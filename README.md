# V1 vs V2 Predicate Timeline Heatmaps

20 plots, one per V2 task, comparing per-frame predicate values from the V1
(annotation-based, per-object binary) and V2 (simulator-based, per-predicate
continuous progress) extraction pipelines.

Each plot shows:

- **Left** — V1: `(num_objects, num_frames)` binary values from
  `data/predicate_data/predicate_data/task_NNNN_state_action_vectors.pkl`
- **Right** — V2: `(num_predicates, num_steps)` continuous values from
  `data/predicate_data_v2_kumar_jsonl/task-NNNN/episode_*_predicates.jsonl`
- **X axis** — Episode progress, normalized to `[0, 1]`
- **Color** — viridis (`0` = not satisfied, `1` = fully satisfied)

V2 progress rule (from `make_plots.py`): for `forall` / `forn` / `forpairs`
predicates the value is `count / threshold` clamped to `[0, 1]`; otherwise
`1.0` if `satisfied` else `0.0`.

## Files

- `make_plots.py` — generation script
- `plots/task<NN>_<task_name>_ep<NNNNNNNN>.png` — one PNG per task

## Reproducing

```bash
python3 make_plots.py
```

Reads from the absolute paths hard-coded at the top of the script
(`V1_DIR`, `V2_DIR`, `OUT_DIR`).
