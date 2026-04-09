# V1 vs V2 Predicate Timeline — Smoothed Comparison (20 Tasks)

Each plot shows a single episode. Left = V1 (annotation-based, per-object binary), Right = V2 (simulator-based, per-predicate continuous, smoothed with median filter k=5 + relative monotonic hold=20).

V2 progress rule: `forall`/`forn`/`forpairs` → `count / threshold` (clamped [0,1]); nested quantifiers are recursively extracted; everything else → `1.0` if satisfied else `0.0`.

---

## Task 02 — putting_away_Halloween_decorations

**Demo**: Robot puts 2 pumpkins and 3 candles into a cabinet, places a cauldron next to a table, then closes the cabinet.

**V1** (6 objects, 13921 frames): tracks each object independently — `pillar_candle × 3`, `cauldron`, `pumpkin × 2`. Candles show "1" for >50% of frames (noisy — V1's "at final location" heuristic triggers whenever the candle is near cabinet, even before final placement).

**V2** (4 predicates, 698 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forall pumpkin exists cabinet inside pumpkin cabinet` | All pumpkins inside some cabinet | 0 → 0.5 → 1.0 (one by one) |
| 1 | `forall candle exists cabinet inside candle cabinet` | All candles inside some cabinet | 0 → 0.33 → 0.67 → 1.0 (three steps) |
| 2 | `exists table nextto cauldron table` | Cauldron next to a table | 0 → 1.0 (single flip) |
| 3 | `forall cabinet not open cabinet` | All cabinets closed | Flickers 0↔1 — robot opens/closes cabinet multiple times during placement |

**Why it looks this way**: V2 pred 0 & 1 show clean staircase progress. Pred 3 flickers because the robot must open the cabinet to insert each item and close it afterward, so `not open` toggles each time.

---

## Task 03 — cleaning_up_plates_and_food

**Demo**: Robot puts 2 pizzas on plates, puts them in the fridge, puts 2 bowls in the sink, then closes the fridge.

**V1** (4 objects, 7945 frames): `plate × 2`, `bowl × 2`. Plates show high "1" counts (~70% and ~34%) — the V1 heuristic fires whenever a plate is near its final location.

**V2** (4 predicates, 399 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forpairs pizza plate ontop pizza plate` | Each pizza on its plate (2 pairs) | Starts at 0.5 → 1.0 (one pizza was already on plate) |
| 1 | `exists fridge forall pizza inside pizza fridge` | All pizzas in fridge | 0 → 0.5 → 1.0 |
| 2 | `exists sink forall bowl inside bowl sink` | All bowls in sink | 0 → 0.5 → 1.0 |
| 3 | `forall fridge not open fridge` | Fridge closed | 0↔1 toggle (opened for pizza, closed after) |

---

## Task 05 — setting_mousetraps

**Demo**: Robot places 4 mousetraps — some on the floor, some under/next to the sink.

**V1** (4 objects, 12850 frames): `mousetrap × 4`. Two show ~46% "1", two show ~7% "1". V1 tracks per-object "at final location", which fires too eagerly for the first two mousetraps.

**V2** (2 predicates, 644 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `exists floor forall mousetrap ontop mousetrap floor` | All 4 mousetraps on floor | 0 → 0.25 → 0.50 → 0.75 (3 of 4 placed; 4th never reaches floor). **Final = 0.75 (not satisfied)** |
| 1 | `exists sink forn 2 mousetrap (under OR nextto sink)` | ≥2 mousetraps near sink | 0 → 0.5 (median lag) → 1.0 (locked) |

**Why it looks this way**: Pred 0 has clean staircase. Pred 1 had massive 1.0↔0.5 flickering in the raw data (15 transitions) because mousetraps slide near the geometric threshold of `nextto`/`under` during placement. Smoothing collapses this to 0 → 1.0. The brief 0.5 at step 4660 is median filter lag (first appearance of 1.0 gets averaged with surrounding 0s).

**Note**: Final `done=False` because pred 0 is only 3/4 (0.75), not all mousetraps reached the floor.

---

## Task 06 — hiding_Easter_eggs

**Demo**: Robot takes 3 Easter eggs from a basket and places them next to trees on the lawn.

**V1** (4 objects, 8935 frames): `wicker_basket`, `easter_egg × 3`. Basket shows 70% "1" (it stays on the lawn, close to "final" by V1 heuristic). Eggs show decreasing "1" counts (first egg placed early, last egg late).

**V2** (2 predicates, 448 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `exists tree forall easter_egg (nextto egg tree)` | All 3 eggs next to some tree | **Stays 0.00 for entire episode** — demo puts eggs near different trees, but `exists` requires ONE tree that all eggs are next to. Demo satisfies per-egg `nextto` but not the `forall` within a single tree. |
| 1 | `forall egg (not inside basket AND ontop lawn)` | All eggs out of basket and on lawn | 0 → 0.33 → 0.67 → 1.0 |

**Why it looks this way**: Pred 0 is permanently 0 — this looks like a **BDDL evaluation bug or overly strict quantifier**. The demo clearly hides eggs near trees, but the `exists tree forall egg nextto egg tree` requires a single tree node that all 3 eggs are simultaneously next to, which never happens. Pred 1 shows clean staircase progress.

---

## Task 10 — set_up_a_coffee_station_in_your_kitchen

**Demo**: Robot arranges coffee station — coffee maker on counter, coffee bottle next to it, filter on it, saucer + cup, kettle next to it.

**V1** (5 objects, 3598 frames): `paper_coffee_filter`, `bottle_of_coffee`, `saucer` (100% "1"!), `electric_kettle`, `coffee_cup`. Saucer is 100% because it starts at its final location.

**V2** (6 predicates, 181 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `ontop(coffee_maker, countertop)` | Coffee maker on counter | **1.0 entire episode** (already there) |
| 1 | `nextto(bottle_of_coffee, coffee_maker)` | Coffee bottle near maker | 0↔1 flickers (robot moves bottle, `nextto` threshold sensitive) |
| 2 | `ontop(paper_coffee_filter, coffee_maker)` | Filter on maker | 0 → 1.0 |
| 3 | `nextto(saucer, coffee_maker)` | Saucer near maker | **1.0 entire episode** (already placed) |
| 4 | `ontop(coffee_cup, saucer)` | Cup on saucer | 0 → 1.0 |
| 5 | `nextto(electric_kettle, coffee_maker)` | Kettle near maker | 0 → 1.0 |

**Why it looks this way**: Pred 0 and 3 are pre-satisfied (items already in place). Pred 1 has `nextto` jitter because the bottle is placed near the edge of the geometric threshold.

---

## Task 11 — putting_dishes_away_after_cleaning

**Demo**: Robot puts 8 plates into a cabinet and closes it.

**V1** (8 objects, 11165 frames): `plate × 8`. They show decreasing "1" — first plates placed early, last plates late.

**V2** (2 predicates, 560 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `exists cabinet forall plate inside plate cabinet` | All 8 plates in some cabinet | **Stays 0.00 entire episode** — the demo fails to get all 8 plates into the cabinet |
| 1 | `forall cabinet not open cabinet` | All cabinets closed | Stays near 1.0 (0.83 → 1.0) — most cabinets were already closed |

**Why it looks this way**: Pred 0 is 0 throughout — the threshold is 8 and none of the plates register as `inside` the cabinet in the V2 BDDL evaluation. This could be a **V2 extraction issue** (plates are inside but the geometric `inside` check fails), or the demo genuinely doesn't complete.

---

## Task 13 — loading_the_car

**Demo**: Robot puts a container, camera, and tennis racket into a car.

**V1** (3 objects, 13720 frames): `toy_box`, `tennis_racket`, `digital_camera`.

**V2** (3 predicates, 687 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `inside(container, car)` | Container in car | 0 → 1.0 |
| 1 | `inside(digital_camera, container)` | Camera in container | 0 → 1.0 |
| 2 | `inside(tennis_racket, car)` | Racket in car | 0 → 1.0 |

**Why it looks this way**: Very clean — all three are single-flip atomic predicates. No quantifiers, no jitter. This is a "gold standard" looking V2 task.

---

## Task 14 — carrying_in_groceries

**Demo**: Robot carries tomato and milk from car to fridge, then closes car and fridge.

**V1** (3 objects, 14627 frames): `paper_bag`, `beefsteak_tomato`, `carton_of_milk`.

**V2** (3 predicates, 733 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `exists fridge (inside tomato fridge AND inside milk fridge)` | Both groceries in fridge | 0 → 1.0 |
| 1 | `not open car` | Car door closed | 0 → 1.0 |
| 2 | `not open fridge` | Fridge closed | 0↔1 toggle (opened to put items in, closed after) |

---

## Task 15 — bringing_in_wood

**Demo**: Robot carries 3 plywood boards inside.

**V1** (3 objects, 11444 frames): `plywood × 3`.

**V2** (1 predicate, 574 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forall plywood ontop plywood floor_2` | All 3 boards on indoor floor | 0 → 0.33 → 0.67 (2 of 3 placed). **Final = 0.67 (not satisfied)** |

**Why it looks this way**: Clean staircase but incomplete — only 2 of 3 boards placed. The `done=False` confirms the demo didn't fully complete this goal.

---

## Task 19 — outfit_a_basic_toolbox

**Demo**: Robot puts 5 tools (drill, pliers, flashlight, allen wrench, screwdriver) into a toolbox on a table, then closes it.

**V1** (5 objects, 10178 frames): each tool tracked separately.

**V2** (7 predicates, 510 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `inside(drill, toolbox)` | Drill in toolbox | 0 → 1.0 |
| 1 | `inside(pliers, toolbox)` | Pliers in toolbox | 0 → 1.0 |
| 2 | `inside(flashlight, toolbox)` | Flashlight in toolbox | 0 → 1.0 |
| 3 | `inside(allen_wrench, toolbox)` | Wrench in toolbox | 0 → 1.0 |
| 4 | `inside(screwdriver, toolbox)` | Screwdriver in toolbox | 0 → 1.0 |
| 5 | `ontop(toolbox, tabletop)` | Toolbox on table | **1.0 always** (already there) |
| 6 | `not open toolbox` | Toolbox closed | 0↔1 toggle |

**Why it looks this way**: Pred 0–4 are clean sequential flips (one tool at a time). Pred 6 flickers because toolbox is opened/closed for each tool.

---

## Task 23 — boxing_books_up_for_storage

**Demo**: Robot puts 6 books into a storage box.

**V1** (7 objects, 26007 frames): `storage_box` + `hardback × 6`.

**V2** (1 predicate, 1302 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forall book inside book box` | All 6 books in box | 0 → 0.17 → 0.33 → 0.50 → 0.67 → 0.83 → 1.0 |

**Why it looks this way**: Perfect 6-step staircase. Each book adds +0.17. One of the cleanest V2 tasks.

---

## Task 24 — storing_food

**Demo**: Robot stores 4 food categories (oatmeal × 2, chips × 2, olive oil × 2, sugar × 2) into cabinets.

**V1** (8 objects, 22550 frames): tracks each item.

**V2** (4 predicates, 1129 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forall box_of_oatmeal exists cabinet inside oatmeal cabinet` | Both oatmeal boxes stored | 0 → 0.5 → 1.0 |
| 1 | `forall bag_of_chips exists cabinet inside chips cabinet` | Both chip bags stored | 0 → 0.5 → 1.0 |
| 2 | `forall bottle_of_olive_oil exists cabinet inside oil cabinet` | Both olive oil bottles stored | 0 → 0.5 → 1.0 |
| 3 | `forall jar_of_sugar exists cabinet inside sugar cabinet` | Both sugar jars stored | 0 → 0.5 → 1.0 |

**Why it looks this way**: Four parallel 2-step staircases. Each category has 2 items, so 0 → 0.5 → 1.0.

---

## Task 25 — clearing_food_from_table_into_fridge

**Demo**: Robot puts apple pie and chicken into separate tupperware containers, puts both in fridge, closes fridge.

**V1** (4 objects, 13708 frames): `tupperware × 2`, `half_chicken`, `half_apple_pie`.

**V2** (4 predicates, 687 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `exists tupperware inside apple_pie tupperware` | Apple pie in some tupperware | 0 → 1.0 |
| 1 | `exists tupperware inside chicken tupperware` | Chicken in some tupperware | 0 → 1.0 |
| 2 | `forall tupperware inside tupperware fridge` | Both tupperwares in fridge | 0 → 0.5 → 1.0 |
| 3 | `not open fridge` | Fridge closed | 0↔1 toggle |

---

## Task 28 — getting_organized_for_work

**Demo**: Robot arranges desk — keyboard next to monitor, mouse next to keyboard, folder next to mouse, notebook on folder, pen on notebook, computer under desk, chair next to desk.

**V1** (6 objects, 18158 frames): `mouse`, `keyboard`, `notebook`, `monitor`, `pen`, `folder`.

**V2** (10 predicates, 909 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `nextto(keyboard, monitor)` | Keyboard near monitor | Flickers — keyboard gets bumped during demo |
| 1 | `ontop(keyboard, desk)` | Keyboard on desk | Flickers — same reason |
| 2 | `under(computer, desk)` | Computer under desk | **1.0 always** |
| 3 | `ontop(monitor, desk)` | Monitor on desk | **1.0 always** |
| 4 | `nextto(mouse, keyboard)` | Mouse near keyboard | 0↔1 flicker. **Final = 0.0** (mouse not next to keyboard at episode end!) |
| 5 | `ontop(mouse, desk)` | Mouse on desk | Flickers, settles 1.0 |
| 6 | `nextto(folder, mouse)` | Folder near mouse | 0 → 1.0 |
| 7 | `ontop(notebook, folder)` | Notebook on folder | 0 → 1.0 |
| 8 | `ontop(pen, notebook)` | Pen on notebook | **0.0 always** (never placed!) |
| 9 | `nextto(swivel_chair, desk)` | Chair near desk | **1.0 always** |

**Why it looks this way**: This task has the most atomic `nextto`/`ontop` predicates, which are the most jitter-prone. Smoothing reduced flips by 56% but some `nextto` noise survives (geometric threshold is tight). **Pred 4 and 8 are never satisfied** — the demo either doesn't place the pen on the notebook, or the mouse drifts away from the keyboard at the end. `done=False`.

---

## Task 29 — clean_up_your_desk

**Demo**: Robot organizes desk — folders and books into bookcase, pens and pencil into pencil box, stapler and laptop on desk, close laptop.

**V1** (10 objects, 19489 frames): `folder × 2`, `paperback_book × 2`, `pencil_case`, `laptop`, `stapler`, `pen × 2`, `pencil`.

**V2** (8 predicates, 976 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forall folder inside folder bookcase` | Both folders in bookcase | 0 → 0.5 → 1.0 |
| 1 | `forall pen inside pen pencil_box` | Both pens in pencil box | 0 → 0.5 → 1.0 |
| 2 | `forall paperback inside paperback bookcase` | Both books in bookcase | 0 → 0.5 → 1.0 |
| 3 | `inside(pencil, pencil_box)` | Pencil in pencil box | 0 → 1.0 |
| 4 | `ontop(stapler, desk)` | Stapler on desk | 0 → 1.0 |
| 5 | `ontop(pencil_box, desk)` | Pencil box on desk | Flickers (moved during organization) |
| 6 | `ontop(laptop, desk)` | Laptop on desk | Flickers (moved during organization) |
| 7 | `not open laptop` | Laptop closed | **0.0 always** (never closed). `done=False` |

---

## Task 34 — hanging_pictures

**Demo**: Robot hangs a poster on a wall nail.

**V1** (1 object, 1544 frames): `poster` — only 1 frame shows "1" (poster at final location for 1 single frame in V1).

**V2** (1 predicate, 130 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `exists wall_nail attached poster wall_nail` | Poster attached to some nail | 0 → 1.0 |

**Why it looks this way**: Simplest task — one object, one predicate, one transition. Clean.

---

## Task 42 — chop_an_onion

**Demo**: Robot uses a parer to dice an onion on a cutting board, puts the diced onion into a bowl, then puts parer and cutting board into the sink.

**V1** (3 objects, 6583 frames): `cutting_board` (0.3% "1"), `vidalia_onion` (50% "1"), `parer` (26% "1"). V1's per-object binary is clearly wrong here — the onion shows "1" for half the episode even though it's not at its final state.

**V2** (4 predicates, 331 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `real(diced_vidalia_onion)` | Diced onion exists (onion has been chopped) | 0 → 1.0 (~halfway through) |
| 1 | `inside(parer, sink)` | Parer in sink | 0 → 1.0 (late in episode) |
| 2 | `inside(chopping_board, sink)` | Board in sink | 0 → 1.0 (late in episode) |
| 3 | `contains(bowl, diced_onion)` | Bowl has diced onion | 0↔1 flicker (onion pieces may bounce out briefly), settles to 1.0 |

**Why it looks this way**: Pred 0 is a `real()` state change (irreversible once chopped) — clean single flip. Pred 1-2 are simple placement. Pred 3 has some jitter because `contains` is sensitive to physics (onion pieces bouncing inside the bowl).

**Known bug**: V1 config gives task 42 only 3 embedding slots but V2 has 4 predicates → collision bug (pred 3's embedding overlaps with task 43's pred 0).

---

## Task 44 — chopping_wood

**Demo**: Robot chops 4 logs into 8 half-logs using an axe.

**V1** (5 objects, 13446 frames): `log × 4`, `axe`.

**V2** (8 predicates, 674 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0–7 | `real(half_log_N)` for N=1..8 | Each half-log exists (log has been chopped) | 0 → 1.0 (sequential, 2 per log) |

**Why it looks this way**: All 8 predicates are `real()` — irreversible state changes. Each log produces 2 half-logs, so you see pairs of flips at each chopping action. Very clean staircase pattern. No jitter because `real()` is permanent.

**Known bug**: V1 config gives task 44 only 5 slots but V2 has 8 predicates → 3 embeddings collide with task 45.

---

## Task 47 — freeze_pies

**Demo**: Robot puts 2 apple pies into 2 tupperwares, puts both in the freezer section of the fridge.

**V1** (4 objects, 13943 frames): `tupperware × 2`, `apple_pie × 2`.

**V2** (4 predicates, 699 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `forpairs apple_pie tupperware inside pie tupperware` | Each pie in its tupperware (2 pairs) | 0 → 0.5 → 1.0 |
| 1 | `forall tupperware inside tupperware fridge` | Both tupperwares in fridge | 0 → 0.5 → 1.0 |
| 2 | `forall apple_pie frozen apple_pie` | Both pies are frozen | **0.0 always** (pies never reach "frozen" state). BDDL `frozen` may require more sim time. |
| 3 | `not open fridge` | Fridge closed | 0↔1 toggle |

**Why it looks this way**: `done=False` because pred 2 stays 0 — the simulator doesn't mark the pies as "frozen" even though they're in the fridge. This is likely a V2 BDDL evaluation limitation (the `frozen` state transition takes longer than the demo, or requires a specific temperature check not triggered in replay).

---

## Task 48 — canning_food

**Demo**: Robot dices steak and pineapple, puts them into separate bowls, puts bowls into a cabinet, closes fridge and cabinet.

**V1** (7 objects, 16767 frames): `cutting_board`, `carving_knife`, `steak`, `pineapple`, `bowl × 2`, `half_pineapple`.

**V2** (7 predicates, 840 steps):
| # | Predicate | What it means | Timeline |
|---|---|---|---|
| 0 | `real(diced_steak)` | Steak has been diced | 0 → 1.0 |
| 1 | `real(diced_pineapple)` | Pineapple has been diced | 0 → 1.0 |
| 2 | `exists bowl (filled bowl diced_steak AND not contains bowl diced_pineapple)` | Some bowl has only steak | 0 → 1.0 |
| 3 | `exists bowl (filled bowl diced_pineapple AND not contains bowl diced_steak)` | Some bowl has only pineapple | 0 → 1.0 |
| 4 | `forall bowl inside bowl cabinet` | Both bowls in cabinet | 0 → 0.5 → 1.0 |
| 5 | `not open fridge` | Fridge closed | 0↔1 toggle |
| 6 | `not open cabinet` | Cabinet closed | 0↔1 toggle (multiple open/close cycles) |

**Why it looks this way**: Pred 0-1 are irreversible `real()` flips. Pred 2-3 are clean existential checks. Pred 4 is a 2-step staircase. Pred 5-6 flicker due to repeated open/close.

---

## Common Patterns Across Tasks

| Pattern | Why | Examples |
|---|---|---|
| **Clean staircase** (0→0.25→0.5→...) | `forall` with N items, each item flips once | Task 23 (books), 44 (logs), 24 (food) |
| **Single flip** (0→1.0) | Atomic predicate, item placed once | Task 13 (loading car), 34 (hanging picture) |
| **Always 1.0** | Item starts at final location | Task 10 pred 0 (coffee maker), 28 pred 2 (computer) |
| **Always 0.0** | Goal never achieved in this demo | Task 6 pred 0 (eggs near trees), 47 pred 2 (frozen pies) |
| **0↔1 toggle** | `not open X` — container opened/closed repeatedly | Task 2 pred 3, 19 pred 6, 48 pred 6 |
| **`nextto` jitter** | Geometric distance threshold is tight, object drifts | Task 10 pred 1 (coffee bottle), 28 pred 0/1 (keyboard) |
| **Median filter lag** | First frame of a transition averaged with surrounding 0s | Task 5 pred 1 (0.5 blip at step 4660) |

## V1 vs V2 Key Differences

| Aspect | V1 | V2 |
|---|---|---|
| Granularity | Per-object binary | Per-predicate continuous |
| What it tracks | "Object at final location" (heuristic) | BDDL goal predicate evaluation (ground truth) |
| Progress info | None (just 0 or 1 per object) | `count/threshold` for quantifiers |
| Noise pattern | Objects flicker "1" whenever near final pose | `nextto`/`ontop` flicker due to physics |
| Known issues | V1 heuristic is too loose (onion shows 50% "1") | `exists` quantifier can be overly strict; `frozen` state doesn't trigger |
