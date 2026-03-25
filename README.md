# V1 vs V2 Predicate Verification

Comparison of two predicate evaluation methods for BEHAVIOR-1K task episodes:

- **V1 (Annotation-based)**: Predicates extracted from pre-recorded annotations (`sample_interval=90`)
- **V2 (Simulator-based)**: Predicates re-evaluated by replaying episodes in OmniGibson simulator (`sample_interval=10`)

Videos in `v1/` and `v2/` show side-by-side heatmap timelines of predicate satisfaction over the course of each episode.

---

## Summary

| Task | Overall Diff | Root Cause | Progress Impact |
|------|-------------|------------|-----------------|
| task-0004 (can_meat) | ~23% | V1 wrong on `not open cabinet` | V1: 75% vs V2: 100% |
| task-0027 (sorting_household) | 5-18% | V1 wrong on `ontop(sanitary_napkin, shelf)` and `ontop(cup, sink)` | V1: 86% vs V2: 100% |
| task-0033 (wash_dog_toys) | ~62% | V1 wrong on `covered` states for tennis_ball and softball | V1: 100% vs V2: 100% (same final, different trajectory) |

---

## Task-0004: can_meat

**Predicates (4):**

| # | Predicate | Description |
|---|-----------|-------------|
| 0 | `forall hinged_jar inside cabinet` | All jars placed inside the cabinet |
| 1 | `forall hinged_jar not open` | All jars are closed |
| 2 | `forall hinged_jar forn 2 bratwurst inside` | Each jar contains 2 bratwursts |
| 3 | `not open cabinet` | Cabinet door is closed |

### episode_00040010

| Predicate | Disagreement | First Divergence |
|-----------|-------------|------------------|
| [0] jars inside cabinet | 0% | -- |
| [1] jars closed | 0% | -- |
| [2] bratwurst inside jars | 0% | -- |
| **[3] cabinet closed** | **90.8%** (148/163) | step 1080 (0:36): V1=True, V2=False |

**Final progress: V1=75%, V2=100%**

### episode_00040020

| Predicate | Disagreement | First Divergence |
|-----------|-------------|------------------|
| [0] jars inside cabinet | 0% | -- |
| [1] jars closed | 0% | -- |
| [2] bratwurst inside jars | 0% | -- |
| **[3] cabinet closed** | **90.4%** (142/157) | step 1080 (0:36): V1=True, V2=False |

**Final progress: V1=75%, V2=100%**

### Analysis

The only disagreement is on **`not open cabinet`**. V1 marks the cabinet as closed from the very beginning and never updates it, while V2 correctly detects that the robot opens the cabinet at step 1080 (0:36) and it remains open for most of the episode. The cabinet is eventually closed at the end, so V2 reports 100% task completion. V1 misses the open-then-close transition and incorrectly reports only 75% progress (3/4 predicates satisfied), because it fails to recognize that the cabinet was closed *at the end* after being opened mid-task.

---

## Task-0027: sorting_household_items

**Predicates (7):**

| # | Predicate | Description |
|---|-----------|-------------|
| 0 | `forall detergent under sink` | All detergent bottles under the sink |
| 1 | `nextto(detergent_1, detergent_2)` | Detergent bottles next to each other |
| 2 | `ontop(sanitary_napkin, shelf)` | Sanitary napkin box on the shelf |
| 3 | `ontop(soap_dispenser, sink)` | Soap dispenser on the sink |
| 4 | `ontop(cup, sink)` | Cup on the sink |
| 5 | `nextto(toothpaste, cup)` | Toothpaste next to the cup |
| 6 | `inside(toothbrush, cup)` | Toothbrush inside the cup |

### episode_00270010

| Predicate | Disagreement | First Divergence |
|-----------|-------------|------------------|
| [0] detergent under sink | 0% | -- |
| [1] detergents next to each other | 0% | -- |
| **[2] sanitary napkin on shelf** | **31.3%** (42/134) | step 8280 (4:36): V1=False, V2=True |
| [3] soap dispenser on sink | 0% | -- |
| **[4] cup on sink** | **94.8%** (127/134) | step 0 (0:00): V1=False, V2=True |
| [5] toothpaste next to cup | 0% | -- |
| [6] toothbrush inside cup | 0% | -- |

**Final progress: V1=86% (6/7), V2=100%**

Final state diff: V1 says `sanitary_napkin` is NOT on the shelf; V2 says it IS.

### episode_00270030

| Predicate | Disagreement | First Divergence |
|-----------|-------------|------------------|
| [0] detergent under sink | 0% | -- |
| [1] detergents next to each other | 0% | -- |
| **[2] sanitary napkin on shelf** | **34.0%** (81/238) | step 14040 (7:48): V1=False, V2=True |
| [3] soap dispenser on sink | 0% | -- |
| [4] cup on sink | 0.8% (2/238) | step 0 (0:00): V1=False, V2=True |
| [5] toothpaste next to cup | 0% | -- |
| [6] toothbrush inside cup | 0% | -- |

**Final progress: V1=86% (6/7), V2=100%**

Final state diff: V1 says `sanitary_napkin` is NOT on the shelf; V2 says it IS.

### Analysis

Two predicates show disagreement:

1. **`ontop(cup, sink)`**: V2 detects the cup is already on the sink from step 0, while V1 initially marks it as False. This is a **V1 initialization error** — the cup starts on the sink but V1 doesn't recognize it.

2. **`ontop(sanitary_napkin, shelf)`**: V1 never recognizes this predicate as satisfied, even at the final step. V2 correctly detects the napkin box is placed on the shelf partway through the episode. This is the predicate that causes the final progress difference (86% vs 100%). **V1 misses task completion.**

---

## Task-0033: wash_dog_toys

**Predicates (3):**

| # | Predicate | Description |
|---|-----------|-------------|
| 0 | `forall teddy: not covered(dirt) and not covered(dust)` | All teddy bears are clean |
| 1 | `not covered(tennis_ball, debris)` | Tennis ball is clean |
| 2 | `not covered(softball, dirt)` | Softball is clean |

### episode_00330010

| Predicate | Disagreement | First Divergence |
|-----------|-------------|------------------|
| [0] teddies clean | 0% | -- |
| **[1] tennis ball clean** | **93.6%** (117/125) | step 0 (0:00): V1=True, V2=False |
| **[2] softball clean** | **93.6%** (117/125) | step 0 (0:00): V1=True, V2=False |

**Final progress: V1=100%, V2=100%**

### episode_00330020

| Predicate | Disagreement | First Divergence |
|-----------|-------------|------------------|
| [0] teddies clean | 0% | -- |
| **[1] tennis ball clean** | **94.1%** (127/135) | step 0 (0:00): V1=True, V2=False |
| **[2] softball clean** | **94.1%** (127/135) | step 0 (0:00): V1=True, V2=False |

**Final progress: V1=100%, V2=100%**

### Analysis

The highest overall disagreement rate (~62%) across all tasks, yet **both V1 and V2 agree on the final progress (100%)**. The disagreement is entirely about the **trajectory**, not the outcome.

- **V1** marks the tennis ball and softball as clean (`not covered`) from the very start (step 0). This means V1's annotations assume they begin clean and stay clean throughout.
- **V2** correctly detects that both objects **start dirty** (covered in debris/dirt at step 0) and are only cleaned toward the end of the episode.

V1 is wrong about the initial state — the whole point of the task is to *wash* dirty toys, so they should start dirty. V1's annotation misses the `covered` state entirely, making it appear as if there was nothing to wash. The final states agree because the robot successfully completes the washing, but **V1 gives a misleading picture of the task progression** (always 100% vs. a gradual climb from 33% to 100%).

---

## Methodology

- **V1**: Predicates from annotation files in the original BEHAVIOR-1K dataset, sampled every 90 simulator steps
- **V2**: Predicates re-extracted by replaying episodes in OmniGibson simulator, sampled every 10 simulator steps
- Comparison is performed at aligned time steps (V1's coarser 90-step grid)
- Videos rendered with predicate satisfaction heatmap timeline overlay at 10 fps (frame_skip=3)

## Conclusion

V1 (annotation-based) predicates contain systematic errors:

1. **Missed state transitions** (task-0004): V1 doesn't track open/close transitions of the cabinet
2. **Incorrect initial state** (task-0027, task-0033): V1 assumes wrong starting conditions (cup not on sink, toys already clean)
3. **Missed final satisfaction** (task-0027): V1 fails to detect that `sanitary_napkin` reaches the shelf

These errors directly impact progress scoring: tasks that the robot actually completes (100% in V2) are underscored by V1 (75% for task-0004, 86% for task-0027). V2 simulator-based evaluation is more reliable for ground-truth predicate assessment.
