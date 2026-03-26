# Meeting Notes: Predicate Redesign Discussion (2026-03-25)

Participants: Prof. (advisor), Yishao (student)

---

## Context

We have a VLA (Vision-Language-Action) model for BEHAVIOR-1K that takes a **predicate vector** as part of its input. The predicate vector tells the robot "how far along are you in this task." Currently, each predicate is a binary 0/1 extracted from BDDL goal conditions using either V1 (annotation-based) or V2 (simulator-based) methods.

The V1 vs V2 comparison revealed systematic errors in V1, documented in this repo's README. This meeting discussed **how to redesign the predicate representation** for better training signals.

---

## 1. The Core Problem: Current Predicates Are Too Coarse

**Advisor's opening point:**

The current predicates don't distinguish between individual object instances. Take task-0004 (can_meat) as an example:

- BDDL goal: `forall jar: forn 2 bratwurst inside(bratwurst, jar)`
- Current representation: **one binary** — are ALL jars filled with 2 bratwursts? Yes/No.

This means:
- Robot has placed 3 out of 4 bratwursts → predicate = 0 (not done)
- Robot has placed 0 out of 4 bratwursts → predicate = 0 (not done)
- **No difference.** The model gets zero signal about intermediate progress.

Similarly, there's no distinction between "jar_1 is full but jar_2 is empty" vs "both jars have 1 bratwurst each." The `forall` quantifier collapses all instance-level information into a single bit.

**What the advisor wants:** The model should see intermediate progress. Specifically:
- Which jar is full, which isn't (per-instance tracking)
- How many bratwursts are in each jar (count progress, not just binary)

---

## 2. Two Types of Predicates: Binary and Progress

The advisor proposed a unified framework:

- **Binary predicates**: True/False (e.g., `is jar_1 inside cabinet?`, `is cabinet closed?`)
- **Progress predicates**: A scalar value representing partial completion (e.g., `jar_1 bratwurst count = 1/2 = 0.5`)

The network would have **two corresponding loss functions**:
- Binary → BCE (binary cross-entropy)
- Progress → Regression (e.g., MSE)

This applies universally: every predicate in every task falls into one of these two types.

---

## 3. How Many Predicates Per Task? (The Slot Design Debate)

Several options were discussed:

### Option A: Per-instance decomposition (most granular)
Expand every `forall` into individual predicates:
```
forall jar: inside(jar, cabinet)
→ inside(jar_1, cabinet): binary
→ inside(jar_2, cabinet): binary

forall jar: forn 2 bratwurst inside(bratwurst, jar)
→ jar_1 progress: 0, 0.5, 1.0
→ jar_2 progress: 0, 0.5, 1.0
```

**Problem:** Different tasks have different numbers of objects → variable-length vectors. Also, more dimensions = more chances for the network to make errors.

### Option B: Per-goal (no expansion)
Each top-level goal condition in the BDDL `(and ...)` becomes one slot:
```
forall jar: forn 2 bratwurst inside(bratwurst, jar)
→ 1 progress slot: how many jars are fully loaded? (0, 1, or 2)
```

**Advantage:** Number of slots = number of BDDL goals, much fewer.
**Disadvantage:** Still loses some per-instance information.

### Option C: Fixed slots (advisor's preferred direction)
**7 binary slots + 7 progress slots = 14 total**, same for every task.
- Each task fills in however many it needs, rest are masked/padded.
- Network architecture is uniform across all tasks.

The advisor went back and forth between options but converged on the idea that having a fixed, uniform structure is important for the network.

---

## 4. "What Logic to Decompose?" — The Immediate Problem

The advisor emphasized this is an **immediate problem**, not something to defer. The core question: given any BDDL goal structure, what are the rules for converting it into binary + progress slots?

### Simple cases:
- **Atomic predicate** (e.g., `ontop(cup, sink)`) → 1 binary slot
- **`not` predicate** (e.g., `not open(cabinet)`) → 1 binary slot
- **`forall` → atomic** (e.g., `forall jar: inside(jar, cabinet)`) → 1 progress slot (count satisfied / total)
- **`forn(N)`** (e.g., `forn 2 bratwurst inside(bratwurst, jar)`) → 1 progress slot (count / N)

### Hard case — nested quantifiers:
```
forall jar:
    forn 2 bratwurst:
        inside(bratwurst, jar)
```
This is `forall` wrapping `forn`. If we don't expand, we get 1 progress slot (how many jars are fully loaded).

But what about the reverse — `forn` wrapping `forall`? Or `exists` wrapping `forall`? Or three levels deep?

### Proposed simple rule (from discussion):
**Reduce from inside out.** Inner quantifier reduces to a boolean (forall = all satisfied, exists = any satisfied, forn = count >= N). Then the outer quantifier counts how many inner ones are satisfied. Each top-level goal becomes one slot.

The type of the slot (binary vs progress) is determined by:
- If the top-level goal can only be 0 or 1 → binary
- If the top-level goal has intermediate values (forall over multiple objects, forn) → progress

---

## 5. "Every Position Means Something Different Per Task"

The advisor pointed out a fundamental issue: position 0 in task-0004's predicate vector means "jars inside cabinet", but position 0 in task-0027 means "detergent under sink." The network has to learn what each position means implicitly through the task embedding.

With per-instance expansion, this problem gets worse — more positions, all task-specific.

The fixed 7+7 slot design partially addresses this: the network doesn't need to know the semantics of each position, only whether it's binary or progress. The task embedding provides the semantic context.

---

## 6. BDDL as a Language — The Long-Term Vision

The advisor noted that BDDL is a formal language for task specification. The **most generalizable** version of the system would:
- Take any BDDL specification as input
- Understand the goal conditions directly
- Execute the task in any environment

This is the long-term north star: the model reads the BDDL "recipe" instead of relying on a fixed set of task embeddings. The current predicate vector work is an intermediate step toward that vision.

---

## 7. OOD Risk from Predicate Errors

The advisor raised a critical concern about inference time:

- Training demos only visit a small subset of the 2^n possible predicate states (e.g., for 6 predicates, there are 64 possible states, but a demo might only visit 5-6 of them in a sequential path like `[0,0,0,0] → [1,0,0,0] → [1,1,0,0] → ...`)
- If the network **predicts one predicate wrong** during inference, the resulting state vector might be one that was **never seen in training** → out-of-distribution (OOD)
- More predicates = more dimensions that can be wrong = higher OOD risk

**Proposed mitigation:** Add a module that **restricts predicate modifications**:
- Don't allow arbitrary flips
- Require high confidence before changing a predicate state
- Possibly enforce monotonicity (once a predicate becomes true, it can't go back to false, for predicates where this makes sense)

This connects to the existing consensus voting mechanism (slide [12]) but may need to be stronger.

---

## 8. Visibility-Based Predicate Updates

The advisor also considered: **only allow updating predicates for objects the robot can currently see.**

Example: If the robot's camera is pointed at the table and can see jar_1, it can update `inside(jar_1, cabinet)`. But if jar_2 is behind the robot and not in the camera frame, the predicate for jar_2 should remain unchanged (carry forward the previous value).

Rationale: Updating predicates for objects you can't see is pure guessing → likely to be wrong → OOD risk.

This introduces a coupling between the **vision module** (what's visible in the current frame) and the **predicate update module** (which slots can change).

---

## 9. V1 Reinterpretation

The advisor offered a different interpretation of V1's "errors":

V1 (annotation-based) predicates don't actually represent physical state. What V1 tracks is: **"was this object the target of the last manipulation action?"** In other words, V1 answers "did the robot last interact with this object?" rather than "is this object in the goal state?"

Examples:
- V1 says cabinet is closed → it really means "the robot hasn't touched the cabinet recently"
- V1 says napkin is not on shelf → it really means "the robot's last place action wasn't putting the napkin on the shelf"

So V1 vs V2 isn't "wrong vs right" — they're answering **different questions**. V1 is a proxy for manipulation history; V2 is ground-truth physical state. For training, V2 is what we want if the goal is to track actual task progress.

---

## 10. BDDL Keyword Statistics for 50 Challenge Tasks

Full scan of all 50 tasks' BDDL goal conditions:

### Quantifier usage:
| Quantifier | Count | Notes |
|---|---|---|
| `forall` | 57 | Most common, present in ~30 tasks |
| `not` | 36 | |
| `exists` | 32 | |
| `forpairs` | 6 | Only 3 tasks (task-0003, task-0026, task-0047) |
| `forn` | 4 | Only 2 tasks (task-0004, task-0009) |
| `or` | 3 | |

### Predicate types:
| Predicate | Count | Notes |
|---|---|---|
| `inside` | 60 | Most common |
| `ontop` | 31 | |
| `open` | 19 | Always with `not` (close something) |
| `nextto` | 17 | |
| `covered` | 11 | Cleaning tasks |
| `contains` | 6 | Cooking tasks |
| `touching` | 5 | |
| `under` | 4 | |
| `toggled_on` | 2 | |
| `attached` | 2 | |
| `cooked` | 2 | |
| `filled` | 2 | |
| `frozen` | 1 | |

### Per-task breakdown:

| Task | Activity | Quantifiers | Predicates |
|---|---|---|---|
| task-0000 | turning_on_radio | — | toggled_on |
| task-0001 | picking_up_trash | forall | inside |
| task-0002 | putting_away_Halloween_decorations | forall, exists, not | inside, nextto, open |
| task-0003 | cleaning_up_plates_and_food | forall, forpairs, exists, not | inside, ontop, open |
| task-0004 | can_meat | forall, forn, not | inside, open |
| task-0005 | setting_mousetraps | forall, forn, exists, or | ontop, under, nextto |
| task-0006 | hiding_Easter_eggs | forall, exists, not | inside, ontop, nextto |
| task-0007 | picking_up_toys | forall, exists | inside |
| task-0008 | rearranging_kitchen_furniture | exists, not | inside, open |
| task-0009 | putting_up_Christmas_decorations_inside | forall, forn, exists, or | ontop, under, nextto, touching |
| task-0010 | set_up_a_coffee_station | — | ontop, nextto |
| task-0011 | putting_dishes_away_after_cleaning | forall, exists, not | inside, open |
| task-0012 | preparing_lunch_box | forall, not | inside, open |
| task-0013 | loading_the_car | not | inside, open |
| task-0014 | carrying_in_groceries | exists, not | inside, open |
| task-0015 | bringing_in_wood | forall | ontop |
| task-0016 | moving_boxes_to_storage | or | ontop |
| task-0017 | bringing_water | forall, not | ontop, open |
| task-0018 | tidying_bedroom | exists | ontop, nextto |
| task-0019 | outfit_a_basic_toolbox | not | inside, ontop, open |
| task-0020 | sorting_vegetables | forall, exists | inside |
| task-0021 | collecting_childrens_toys | forall, exists | inside |
| task-0022 | putting_shoes_on_rack | forall, not | nextto, touching |
| task-0023 | boxing_books_up_for_storage | forall | inside |
| task-0024 | storing_food | forall, exists | inside |
| task-0025 | clearing_food_from_table_into_fridge | forall, exists, not | inside, open |
| task-0026 | assembling_gift_baskets | forpairs | inside |
| task-0027 | sorting_household_items | forall | inside, ontop, under, nextto |
| task-0028 | getting_organized_for_work | — | ontop, under, nextto |
| task-0029 | clean_up_your_desk | forall, not | inside, ontop, open |
| task-0030 | setting_the_fire | forall, not | inside, ontop, toggled_on |
| task-0031 | clean_boxing_gloves | forall, not | covered |
| task-0032 | wash_a_baseball_cap | forall, not | covered |
| task-0033 | wash_dog_toys | forall, not | covered |
| task-0034 | hanging_pictures | exists | attached |
| task-0035 | attach_a_camera_to_a_tripod | — | attached |
| task-0036 | clean_a_patio | not | covered |
| task-0037 | clean_a_trumpet | not | covered |
| task-0038 | spraying_for_bugs | forall | covered |
| task-0039 | spraying_fruit_trees | — | covered |
| task-0040 | make_microwave_popcorn | — | contains |
| task-0041 | cook_cabbage | — | contains |
| task-0042 | chop_an_onion | — | inside, contains |
| task-0043 | slicing_vegetables | forall, not | open |
| task-0044 | chopping_wood | — | — |
| task-0045 | cook_hot_dogs | forall | cooked |
| task-0046 | cook_bacon | forall, not | open, cooked |
| task-0047 | freeze_pies | forall, forpairs, not | inside, open, frozen |
| task-0048 | canning_food | forall, exists, not | inside, filled, open, contains |
| task-0049 | make_pizza | — | ontop |

### Key observations:
1. **`forn` is rare** — only 2 tasks use it (task-0004, task-0009). So progress-type predicates from `forn` are uncommon.
2. **`forall` is the main thing to handle** — 57 occurrences across ~30 tasks. Each `forall` is a candidate for progress representation (count satisfied / total).
3. **Most tasks are structurally simple** — many have no quantifiers at all (just atomic predicates).
4. **`exists` is common (32)** — but `exists` is inherently binary (does ANY instance satisfy?), so it maps cleanly to a binary slot.
5. **`forpairs` is niche** — 3 tasks, bijective matching (e.g., each cork matches to a wine bottle).
6. **13 different predicate types** — but `inside`, `ontop`, `open`, `nextto`, `covered` cover ~90% of cases.

---

## Open Questions / Next Steps

1. **Slot design**: Fixed 7+7 or variable per task? Advisor leaning toward fixed.
2. **Decomposition logic**: Need to finalize the rules for converting BDDL goals → binary/progress slots. Proposed: inner-to-outer reduction, top-level goals map to slots.
3. **Visibility gating**: How to determine which objects are visible in the current camera frame? Needs integration with the vision pipeline.
4. **OOD protection module**: Design a gating mechanism that prevents low-confidence or invisible predicate updates.
5. **V2 extraction for all 50 tasks**: With sample_interval=10 and 4 L40S GPUs, estimated ~10-12 days. With interval=30, ~3.5 days.
6. **The existing V2 predicate tree already contains per-instance data** — the `instances` field in each quantifier node has individual object satisfaction states. Decomposition can be done as post-processing on existing JSONL files without re-running the simulator.
