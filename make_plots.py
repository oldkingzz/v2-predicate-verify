#!/usr/bin/env python3
"""
V1 vs V2 predicate timeline heatmap.
Left = V1 (annotation-based, per-object binary).
Right = V2 (simulator-based, per-predicate continuous progress).
Shared bottom colorbar (viridis).
"""
import json
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np

V1_DIR = "/vast/projects/kumar/lab/yishao/data/predicate_data/predicate_data"
V2_DIR = "/vast/projects/kumar/lab/yishao/data/predicate_data_v2_kumar_jsonl"
OUT_DIR = "/vast/home/y/yishao/Vincent/v2_predicate_verify/plots"

V2_TASKS = [2, 3, 5, 6, 10, 11, 13, 14, 15, 19, 23, 24, 25, 28, 29, 34, 42, 44, 47, 48]

TASK_NAMES = [
    "turning_on_radio", "picking_up_trash", "putting_away_Halloween_decorations",
    "cleaning_up_plates_and_food", "can_meat", "setting_mousetraps",
    "hiding_Easter_eggs", "picking_up_toys", "rearranging_kitchen_furniture",
    "putting_up_Christmas_decorations_inside", "set_up_a_coffee_station_in_your_kitchen",
    "putting_dishes_away_after_cleaning", "preparing_lunch_box", "loading_the_car",
    "carrying_in_groceries", "bringing_in_wood", "moving_boxes_to_storage",
    "bringing_water", "tidying_bedroom", "outfit_a_basic_toolbox",
    "sorting_vegetables", "collecting_childrens_toys", "putting_shoes_on_rack",
    "boxing_books_up_for_storage", "storing_food", "clearing_food_from_table_into_fridge",
    "assembling_gift_baskets", "sorting_household_items", "getting_organized_for_work",
    "clean_up_your_desk", "setting_the_fire", "clean_boxing_gloves",
    "wash_a_baseball_cap", "wash_dog_toys", "hanging_pictures",
    "attach_a_camera_to_a_tripod", "clean_a_patio", "clean_a_trumpet",
    "spraying_for_bugs", "spraying_fruit_trees", "make_microwave_popcorn",
    "cook_cabbage", "chop_an_onion", "slicing_vegetables", "chopping_wood",
    "cook_hot_dogs", "cook_bacon", "freeze_pies", "canning_food", "make_pizza",
]


def load_v1(task_id, episode_id):
    """Return (states matrix [T, N], item labels [N])."""
    with open(f"{V1_DIR}/task_{task_id:04d}_state_action_vectors.pkl", "rb") as f:
        d = pickle.load(f)
    states = np.asarray(d["demo_vectors"][episode_id]["states"], dtype=np.float32)
    labels = [d["index_to_item"][i] for i in range(d["num_items"])]
    return states, labels


def predicate_value(p):
    """Map a predicate dict to a [0, 1] progress value per spec."""
    t = p.get("type", "")
    if t in ("forall", "forn", "forpairs"):
        c = p.get("count")
        thr = p.get("threshold")
        if c is None or thr is None or thr == 0:
            return 1.0 if p.get("satisfied") else 0.0
        return float(min(max(c / thr, 0.0), 1.0))
    return 1.0 if p.get("satisfied") else 0.0


def load_v2(task_id, episode_id):
    """Return (values [T, N], labels [N], steps [T])."""
    path = f"{V2_DIR}/task-{task_id:04d}/episode_{episode_id}_predicates.jsonl"
    rows = []
    steps = []
    labels = None
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            steps.append(r["step"])
            if labels is None:
                labels = [p["_raw_description"] for p in r["predicates"]]
            rows.append([predicate_value(p) for p in r["predicates"]])
    return np.asarray(rows, dtype=np.float32), labels, np.asarray(steps)


def truncate(s, n=60):
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def plot_one(task_id, episode_id, out_path):
    task_name = TASK_NAMES[task_id]
    v1_states, v1_labels = load_v1(task_id, episode_id)  # (T1, N1)
    v2_values, v2_labels, v2_steps = load_v2(task_id, episode_id)  # (T2, N2)

    T1, N1 = v1_states.shape
    T2, N2 = v2_values.shape
    x1 = np.linspace(0.0, 1.0, T1 + 1)
    if v2_steps.max() > 0:
        x2 = np.concatenate([v2_steps, [v2_steps[-1] + 1]]).astype(np.float32)
        x2 = x2 / x2[-1]
    else:
        x2 = np.linspace(0.0, 1.0, T2 + 1)

    fig = plt.figure(figsize=(18, max(5, 0.4 * max(N1, N2) + 4)))
    gs = fig.add_gridspec(
        2, 2, height_ratios=[20, 1], width_ratios=[1, 1],
        hspace=0.18, wspace=0.32, left=0.20, right=0.97, top=0.86, bottom=0.10,
    )
    ax_v1 = fig.add_subplot(gs[0, 0])
    ax_v2 = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[1, :])

    cmap = plt.get_cmap("viridis")
    norm = plt.Normalize(vmin=0.0, vmax=1.0)

    y1 = np.arange(N1 + 1)
    mesh1 = ax_v1.pcolormesh(
        x1, y1, v1_states.T, cmap=cmap, norm=norm,
        edgecolors="white", linewidth=0.4, antialiased=False,
    )
    ax_v1.set_yticks(np.arange(N1) + 0.5)
    ax_v1.set_yticklabels([truncate(l, 38) for l in v1_labels], fontsize=8)
    ax_v1.invert_yaxis()
    ax_v1.set_xlim(0.0, 1.0)
    ax_v1.set_xlabel("Episode Progress (normalized)", fontsize=10)
    ax_v1.set_title(
        f"V1: {N1} per-object binary  ({T1} frames)",
        fontsize=11, color="#0b3d91", fontweight="bold",
    )

    y2 = np.arange(N2 + 1)
    ax_v2.pcolormesh(
        x2, y2, v2_values.T, cmap=cmap, norm=norm,
        edgecolors="white", linewidth=0.4, antialiased=False,
    )
    ax_v2.set_yticks(np.arange(N2) + 0.5)
    ax_v2.set_yticklabels([truncate(l, 60) for l in v2_labels], fontsize=8)
    ax_v2.invert_yaxis()
    ax_v2.set_xlim(0.0, 1.0)
    ax_v2.set_xlabel("Episode Progress (normalized)", fontsize=10)
    ax_v2.set_title(
        f"V2: {N2} per-predicate continuous  ({T2} steps)",
        fontsize=11, color="#0b3d91", fontweight="bold",
    )

    cb = fig.colorbar(mesh1, cax=cax, orientation="horizontal")
    cb.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0])
    cb.set_ticklabels(["0.00", "0.25", "0.50", "0.75", "1.00"])
    cb.set_label(
        "Predicate Value (0 = not satisfied, 1 = fully satisfied)", fontsize=10,
    )

    fig.suptitle(
        f"Episode {episode_id} — {task_name}: V1 vs V2 Predicate Timeline",
        fontsize=14, color="#0b3d91", fontweight="bold", y=0.965,
    )
    fig.text(
        0.5, 0.018,
        "V1 = per-object binary (annotation-based) | V2 = per-predicate "
        "continuous progress (simulator-based, BDDL evaluation)",
        ha="center", color="#666666", fontsize=8, style="italic",
    )

    fig.savefig(out_path, dpi=130, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def common_episodes(task_id, n=2):
    with open(f"{V1_DIR}/task_{task_id:04d}_state_action_vectors.pkl", "rb") as f:
        v1 = pickle.load(f)
    v1_eps = set(v1["demo_vectors"].keys())
    v2_dir = f"{V2_DIR}/task-{task_id:04d}"
    if not os.path.isdir(v2_dir):
        return []
    v2_eps = {
        f.replace("episode_", "").replace("_predicates.jsonl", "")
        for f in os.listdir(v2_dir)
        if f.endswith("_predicates.jsonl")
    }
    return sorted(v1_eps & v2_eps)[:n]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    n_done = 0
    n_failed = 0
    for tid in V2_TASKS:
        eps = common_episodes(tid, n=1)
        for ep in eps:
            out = f"{OUT_DIR}/task{tid:02d}_{TASK_NAMES[tid]}_ep{ep}.png"
            try:
                plot_one(tid, ep, out)
                print(f"  ✓ {os.path.basename(out)}")
                n_done += 1
            except Exception as e:
                print(f"  ✗ {os.path.basename(out)}: {type(e).__name__}: {e}")
                n_failed += 1
    print(f"\nDone. {n_done} plots generated, {n_failed} failed.")


if __name__ == "__main__":
    main()
