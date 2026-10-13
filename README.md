# Museum Heist: Thief vs Cooperating Guards using Minimax

A multi-agent AI case study for 23CSE401 Fundamentals of Artificial Intelligence,
Amrita School of Computing, Amrita Vishwa Vidyapeetham, Bengaluru.

A thief must steal an artifact and reach the exit on a grid-based museum map,
while two guards, cooperating as a team, try to catch the thief first. All
agents are utility-based and use depth-limited search over a shared
evaluation function built from shortest-path distances. The project compares
Minimax against Alpha-Beta pruning, Alpha-Beta against a greedy one-step
baseline, and coordinated guards against independent guards.

## Setup

Requires Python 3.10 or higher.

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Mac or Linux)
pip install -r requirements.txt
```

`requirements.txt` lists matplotlib, pillow, and numpy. No other packages are needed.

## How to run

All commands are run from the project root, with the virtual environment active.

**Play one full game and see the turn-by-turn log:**
```
python main.py play --map maps/working_case_1.txt --depth 6
```

**Compare minimax vs alpha-beta node counts on the starting position of a map:**
```
python main.py compare --map maps/working_case_1.txt --depth 6
```

**Export a game as an animated GIF:**
```
python main.py visualize --map maps/working_case_1.txt --depth 6 --output outputs/working_case_1.gif
```

**Regenerate all core experiment data, CSVs and plots used in the report:**
```
python main.py experiments
```

**Run the full alpha-beta vs greedy benchmark suite** (mixed matchups, random
maps, depth sweep, cost-per-decision, and the edge case 2 move trace):
```
python main.py benchmark
```

**Generate a labelled search tree diagram from a real position** (used for the
presentation, draws exactly what the code actually searched, including
pruned branches):
```
python tree_trace.py --map maps/working_case_1.txt --depth 3 --algo alphabeta --output outputs/search_tree.png
```

Optional arguments:

| Command | Option | Meaning | Default |
|---|---|---|---|
| `play`, `compare`, `visualize` | `--map` | path to a map file | `maps/working_case_1.txt` |
| `play`, `compare`, `visualize` | `--depth` | search depth limit for all agents | 6 |
| `play`, `visualize` | `--turn_limit` | maximum turns before a draw is declared | 100 |
| `visualize` | `--output` | path to save the GIF | `outputs/game.gif` |
| `benchmark` | `--maps` | number of random maps to test on | 30 |
| `benchmark` | `--seed` | random seed, for reproducible random maps | 42 |
| `benchmark` | `--depth` | alpha-beta depth used in the random-map matchups | 4 |
| `benchmark` | `--max_depth` | largest depth tested in the depth sweep | 6 |
| `tree_trace.py` | `--map` | path to a map file | `maps/working_case_1.txt` |
| `tree_trace.py` | `--depth` | how many levels deep to draw | 2 |
| `tree_trace.py` | `--algo` | `alphabeta` or `minimax` | `alphabeta` |
| `tree_trace.py` | `--output` | path to save the tree image | `outputs/search_tree.png` |

## Inputs

Maps are plain text files under `maps/`. Each character represents one cell:

| Character | Meaning |
|---|---|
| `#` | Wall |
| `.` | Floor (walkable) |
| `A` | Artifact position |
| `E` | Exit position |
| `T` | Thief starting position |
| `G` | Guard starting position (used twice, once per guard) |

Four maps are included, matching the four required test cases:
- `working_case_1.txt`, thief has a real path to victory
- `working_case_2.txt`, guards intercept the thief before the artifact
- `edge_case_1_trapped.txt`, thief starts with no safe move
- `edge_case_2_horizon.txt`, same map and guard positions, result flips between depth 2 and depth 8 (the horizon effect)

The benchmark suite additionally generates its own random maps at runtime
(not stored as files), using a fixed seed so results are reproducible.

## Outputs

Running `python main.py experiments` regenerates everything below in `outputs/`:

| File | Contents |
|---|---|
| `nodes_vs_depth.csv`, `.png` | Nodes expanded, minimax vs alpha-beta, depths 2 to 7 |
| `runtime_vs_depth.png` | Wall-clock time for the same comparison |
| `all_cases_summary.csv` | Result, turns, and nodes for alpha-beta and greedy on all four required cases |
| `all_cases_nodes_comparison.png`, `all_cases_turns_comparison.png` | Bar charts of the summary above |
| `coordination_comparison.csv` | Coordinated vs independent guard teams at depths 6 and 9 |

Running `python main.py benchmark` regenerates everything below in `outputs/benchmark/`:

| File | Contents |
|---|---|
| `matchups.csv`, `matchups_turns.png` | Every alpha-beta vs greedy role combination (e.g. alpha-beta thief vs greedy guards, and the reverse) on the four required maps |
| `random_maps_winrates.csv`, `random_maps_winrates.png` | Win rates over many randomly generated maps, not just the four hand-built ones |
| `depth_sweep.csv`, `depth_sweep_winrate.png` | How the alpha-beta win rate changes as its search depth increases |
| `cost_per_decision.csv`, `cost_per_decision.png` | Nodes expanded and time taken per decision, at each depth |
| `edge2_trace.txt` | A move-by-move log comparing alpha-beta and greedy on edge case 2, showing exactly where and why their decisions first diverge |

`python main.py visualize` produces an animated GIF of one game, showing
the thief (red), both guards (blue), the artifact (gold, disappears once
collected), and the exit (green).

`python tree_trace.py` produces a labelled search tree image (blue boxes for
the thief's turns, pink boxes for a guard's turn, grey dashed boxes for
branches Alpha-Beta skipped), plus a text version of the same tree printed
to the terminal.

## File descriptions

```
museum_heist/
  main.py                     command line entry point (play, compare, visualize, experiments, benchmark)
  tree_trace.py                generates a labelled search tree image from a real position, by
                               re-running the actual search code and recording every node visited
  requirements.txt            Python package dependencies (matplotlib, pillow, numpy)
  test_setup.py                scratch workbench used during development to try things out
                               quickly before they were moved into src/. Not required to run
                               the project, kept only as a development record.
  find_horizon_map.py          one-off utility script used to search for guard start positions
                               that produce a genuine horizon effect (a result that flips between
                               a shallow and a deep search on the same map). Used to design
                               edge_case_2_horizon.txt and is not needed to run the project.
  maps/                       text map files, see Inputs above
  src/
    world.py                  loads a map file into a GridWorld, tracks walls and legal moves
    distances.py              precomputes all-pairs shortest-path distances with BFS
    state.py                  represents one game state: positions, turn, artifact status
    evaluation.py             heuristic scoring function used at the search depth limit
    search.py                 minimax and alpha-beta pruning, with move ordering and node counters
    greedy.py                 one-step greedy search, used as a comparison baseline
    independent_guards.py     guards searching alone rather than as a coordinated team
    simulation.py             runs one full game turn by turn until a result is reached
    visualize.py               renders a game's history as an animated GIF
    experiments.py            runs the core experiments and saves CSVs and plots to outputs/
    benchmark.py               runs the statistical alpha-beta vs greedy benchmark suite
                               (mixed matchups, random maps, depth sweep, cost per decision,
                               and the edge case 2 divergence trace), saves to outputs/benchmark/
  outputs/                    generated CSVs, plots, GIFs, and search tree images
  outputs/benchmark/          generated CSVs and plots from the benchmark suite
  report/                     LaTeX report source
```

## Notes on agent design

- The thief is a MAX agent trying to maximize the evaluation score.
- Both guards are MIN agents inside a single shared search tree, which is
  what makes them a cooperative team rather than two agents acting alone.
- The evaluation function combines the thief's distance to its current goal
  (the artifact, then the exit) against the nearest guard's distance to the
  thief, plus large terminal bonuses or penalties for a win or a capture.
- A depth limit is required because the full game tree is too large to
  search exhaustively. This introduces the horizon effect, demonstrated in
  `edge_case_2_horizon.txt`, where the same map produces opposite results
  at different search depths.
- Move ordering (trying the most promising move first, based on shortest-path
  distance to the current goal) is what lets Alpha-Beta prune so effectively
  without changing the final decision.

## Comparisons included

1. **Minimax vs alpha-beta pruning**: same decisions, fewer nodes expanded
   with alpha-beta (see `nodes_vs_depth.csv`).
2. **Alpha-beta vs greedy one-step search**: a full statistical comparison,
   not a single anecdote. Covers every role matchup (alpha-beta as thief vs
   greedy as guards, and the reverse) on the four required maps, win rates
   across 30 randomly generated maps, how the win rate changes as search
   depth increases, and the cost in nodes and time per decision at each
   depth (see `outputs/benchmark/`).
3. **Coordinated vs independent guards**: guards sharing one search tree
   split their effective lookahead across all three agents, so at equal
   nominal depth, independent guards (each with a full depth budget to
   themselves) can outperform a coordinated team. Coordination only
   catches up once given a higher depth limit (see `coordination_comparison.csv`).
