# Museum Heist: Thief vs Cooperating Guards using Minimax

A multi-agent AI case study for 23CSE401 Fundamentals of Artificial Intelligence.

A thief must steal an artifact and reach the exit on a grid-based museum map,
while two guards, cooperating as a team, try to catch the thief first. All
agents are utility-based and use depth-limited search over a shared
evaluation function built from shortest-path distances.

## Setup

Requires Python 3.10 or higher.

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Mac or Linux)
pip install -r requirements.txt
```

## How to run

All commands are run from the project root, with the virtual environment active.

**Play one full game and see the turn-by-turn log:**
```
python main.py play --map maps/working_case_1.txt --depth 6
```

**Compare minimax vs alpha-beta on the starting position of a map:**
```
python main.py compare --map maps/working_case_1.txt --depth 6
```

**Export a game as an animated GIF:**
```
python main.py visualize --map maps/working_case_1.txt --depth 6 --output outputs/working_case_1.gif
```

**Regenerate all experiment data, CSVs and plots used in the report:**
```
python main.py experiments
```

Optional arguments for `play` and `visualize`:
- `--map`          path to a map file (default: `maps/working_case_1.txt`)
- `--depth`        search depth limit for the thief and guards (default: 6)
- `--turn_limit`   maximum turns before the game is called a draw (default: 100)

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

Five maps are included:
- `working_case_1.txt`, thief has a real path to victory
- `working_case_2.txt`, guards intercept the thief before the artifact
- `edge_case_1_trapped.txt`, thief starts with no safe move
- `edge_case_2_horizon.txt`, same map and guard positions, result flips between depth 2 and depth 8 (the horizon effect)

## Outputs

Running `python main.py experiments` regenerates everything in `outputs/`:

| File | Contents |
|---|---|
| `nodes_vs_depth.csv`, `.png` | Nodes expanded, minimax vs alpha-beta, depths 2 to 7 |
| `runtime_vs_depth.png` | Wall-clock time for the same comparison |
| `all_cases_summary.csv` | Result, turns, and nodes for alpha-beta and greedy on all four required cases |
| `all_cases_nodes_comparison.png`, `all_cases_turns_comparison.png` | Bar charts of the summary above |
| `coordination_comparison.csv` | Coordinated vs independent guard teams at depths 6 and 9 |

`python main.py visualize` produces an animated GIF of one game, showing
the thief (red), both guards (blue), the artifact (gold, disappears once
collected), and the exit (green).

## File descriptions

```
museum_heist/
  main.py                     command line entry point (play, compare, visualize, experiments)
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
    visualize.py              renders a game's history as an animated GIF
    experiments.py            runs all experiments and saves CSVs and plots to outputs/
  outputs/                    generated CSVs, plots, and GIFs (see Outputs above)
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

## Comparisons included

1. **Minimax vs alpha-beta pruning**: same decisions, fewer nodes expanded
   with alpha-beta (see `nodes_vs_depth.csv`).
2. **Alpha-beta vs greedy one-step search**: greedy has no lookahead and
   performs noticeably worse in most cases (see `all_cases_summary.csv`).
3. **Coordinated vs independent guards**: guards sharing one search tree
   split their effective lookahead across all three agents, so at equal
   nominal depth, independent guards (each with a full depth budget to
   themselves) can outperform a coordinated team. Coordination only
   catches up once given a higher depth limit (see `coordination_comparison.csv`).
