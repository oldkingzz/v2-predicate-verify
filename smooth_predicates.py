#!/usr/bin/env python3
"""
Post-process V2 predicate JSONL to remove physics-simulation jitter.

Pipeline per-episode:
  1. Extract per-predicate time series (forall/forn/forpairs → count/threshold, else → satisfied)
  2. Median filter (kernel_size=5)
  3. Monotonic hold: short dips below 0.5 (< min_hold steps) are filled back
  4. Write smoothed JSONL preserving original format
"""
import argparse
import copy
import json
import os
from pathlib import Path

import numpy as np
from scipy.signal import medfilt

V2_TASKS = [2, 3, 5, 6, 10, 11, 13, 14, 15, 19, 23, 24, 25, 28, 29, 34, 42, 44, 47, 48]

# ---------------------------------------------------------------------------
# Value extraction / injection
# ---------------------------------------------------------------------------

def pred_value(p):
    """Extract a [0,1] progress float from a predicate dict."""
    t = p.get("type", "")
    if t in ("forall", "forn", "forpairs"):
        c, thr = p.get("count"), p.get("threshold")
        if c is not None and thr and thr > 0:
            return float(np.clip(c / thr, 0.0, 1.0))
    # For exists / atomic / not — also check for nested quantifier progress
    if "instances" in p:
        for inst in p["instances"].values():
            nested = inst.get("nested")
            if nested and nested.get("type") in ("forall", "forn", "forpairs"):
                c, thr = nested.get("count"), nested.get("threshold")
                if c is not None and thr and thr > 0:
                    return float(np.clip(c / thr, 0.0, 1.0))
    return 1.0 if p.get("satisfied") else 0.0


def inject_value(p, val):
    """Write smoothed value back into predicate dict (in-place)."""
    p["satisfied"] = bool(val >= 0.5)
    t = p.get("type", "")
    if t in ("forall", "forn", "forpairs") and "threshold" in p:
        p["count"] = float(val * p["threshold"])
    if "instances" in p:
        for inst in p["instances"].values():
            nested = inst.get("nested")
            if nested and nested.get("type") in ("forall", "forn", "forpairs") and "threshold" in nested:
                nested["count"] = float(val * nested["threshold"])
                nested["satisfied"] = bool(val >= 0.5)

# ---------------------------------------------------------------------------
# Smoothing
# ---------------------------------------------------------------------------

def smooth_series(vals: np.ndarray, kernel: int = 5, min_hold: int = 10) -> np.ndarray:
    """Median filter + monotonic hold."""
    # Step 1: median filter
    v = medfilt(vals, kernel_size=kernel).astype(np.float64)

    # Step 2: monotonic hold — fill short dips below 0.5
    out = v.copy()
    i = 0
    n = len(out)
    while i < n:
        if out[i] >= 0.5:
            high_val = out[i]
            i += 1
            continue
        # out[i] < 0.5 — start of a dip
        if i == 0:
            i += 1
            continue
        high_val = out[i - 1]
        if high_val < 0.5:
            i += 1
            continue
        dip_start = i
        while i < n and out[i] < 0.5:
            i += 1
        dip_len = i - dip_start
        if dip_len < min_hold:
            out[dip_start:i] = high_val
    return out

# ---------------------------------------------------------------------------
# Per-episode processing
# ---------------------------------------------------------------------------

def process_episode(in_path: str, out_path: str, kernel: int, min_hold: int):
    """Return (flips_before, flips_after) for this episode."""
    with open(in_path) as f:
        records = [json.loads(line) for line in f]
    if not records:
        return 0, 0

    n_preds = len(records[0]["predicates"])
    n_steps = len(records)

    # Build raw matrix [n_steps, n_preds]
    raw = np.zeros((n_steps, n_preds), dtype=np.float64)
    for t, rec in enumerate(records):
        for j, p in enumerate(rec["predicates"]):
            raw[t, j] = pred_value(p)

    # Smooth each predicate column
    smoothed = np.zeros_like(raw)
    for j in range(n_preds):
        smoothed[:, j] = smooth_series(raw[:, j], kernel=kernel, min_hold=min_hold)

    # Count flips (transitions across 0.5) before and after
    def count_flips(mat):
        binary = (mat >= 0.5).astype(int)
        return int(np.sum(np.abs(np.diff(binary, axis=0))))

    fb = count_flips(raw)
    fa = count_flips(smoothed)

    # Write output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out_records = []
    for t, rec in enumerate(records):
        rec2 = copy.deepcopy(rec)
        for j, p in enumerate(rec2["predicates"]):
            inject_value(p, smoothed[t, j])
        # Recompute top-level progress
        sat = sum(1 for p in rec2["predicates"] if p.get("satisfied"))
        total = len(rec2["predicates"])
        rec2["satisfied_count"] = sat
        rec2["total_count"] = total
        rec2["progress"] = sat / total if total else 0.0
        rec2["done"] = sat == total
        out_records.append(json.dumps(rec2, ensure_ascii=False))

    with open(out_path, "w") as f:
        f.write("\n".join(out_records) + "\n")

    return fb, fa

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2_dir", default="/vast/projects/kumar/lab/yishao/data/predicate_data_v2_kumar_jsonl")
    parser.add_argument("--out_dir", default="/vast/home/y/yishao/Vincent/v2_predicate_verify/predicates_smoothed")
    parser.add_argument("--kernel", type=int, default=5)
    parser.add_argument("--min_hold", type=int, default=10)
    parser.add_argument("--tasks", type=int, nargs="+", default=V2_TASKS)
    args = parser.parse_args()

    print(f"Smoothing V2 predicates: kernel={args.kernel}, min_hold={args.min_hold}")
    print(f"Input:  {args.v2_dir}")
    print(f"Output: {args.out_dir}")
    print()

    total_before, total_after = 0, 0
    for tid in args.tasks:
        in_dir = f"{args.v2_dir}/task-{tid:04d}"
        out_task_dir = f"{args.out_dir}/task-{tid:04d}"
        if not os.path.isdir(in_dir):
            print(f"  task {tid:2d}: SKIP (no input dir)")
            continue
        files = sorted(f for f in os.listdir(in_dir) if f.endswith("_predicates.jsonl"))
        task_fb, task_fa = 0, 0
        for fn in files:
            fb, fa = process_episode(
                os.path.join(in_dir, fn),
                os.path.join(out_task_dir, fn),
                args.kernel, args.min_hold,
            )
            task_fb += fb
            task_fa += fa
        total_before += task_fb
        total_after += task_fa
        pct = ((task_fb - task_fa) / task_fb * 100) if task_fb else 0
        print(f"  task {tid:2d}: {len(files):3d} eps | flips {task_fb:6d} -> {task_fa:6d}  (-{pct:.0f}%)")

    pct = ((total_before - total_after) / total_before * 100) if total_before else 0
    print(f"\nTotal: flips {total_before} -> {total_after}  (-{pct:.0f}%)")


if __name__ == "__main__":
    main()
