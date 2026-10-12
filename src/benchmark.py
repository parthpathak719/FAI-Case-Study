"""
Benchmark: alpha-beta search vs greedy one-step search.

Everything here plays real games, with each role (thief, guards) assigned
its own method, so the two techniques actually face each other.

Experiments (all outputs go to outputs/benchmark/):
  1. Matchup matrix on the four required maps  -> matchups.csv, matchups_turns.png
  2. Win rates over many seeded random maps    -> random_maps_winrates.csv, random_maps_winrates.png
  3. Alpha-beta depth sweep against greedy     -> depth_sweep.csv, depth_sweep_winrate.png
  4. Cost per decision vs depth                -> cost_per_decision.csv, cost_per_decision.png
  5. Edge case 2 divergence trace              -> edge2_trace.txt
"""

import csv
import os
import random
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.world import GridWorld, load_map
from src.distances import build_distance_table
from src.state import initial_state, apply_move, legal_moves_for_current_agent, THIEF_TURN
from src.search import alpha_beta, is_terminal, SearchStats
from src.greedy import greedy_move, GreedyStats

BENCH_DIR = "outputs/benchmark"

AB = "alphabeta"
GREEDY = "greedy"

# Same maps and depths as the report so the numbers line up.
REQUIRED_CASES = [
    ("Working Case 1", "maps/working_case_1.txt", 6, 100),
    ("Working Case 2", "maps/working_case_2.txt", 6, 100),
    ("Edge Case 1 (trapped)", "maps/edge_case_1_trapped.txt", 4, 30),
    ("Edge Case 2 (depth 2)", "maps/edge_case_2_horizon.txt", 2, 150),
    ("Edge Case 2 (depth 8)", "maps/edge_case_2_horizon.txt", 8, 150),
]

MATCHUPS = [
    (AB, AB),
    (AB, GREEDY),
    (GREEDY, AB),
    (GREEDY, GREEDY),
]


def matchup_label(thief_method, guard_method):
    names = {AB: "AB", GREEDY: "Greedy"}
    return "Thief " + names[thief_method] + " vs Guards " + names[guard_method]


def ensure_dir():
    if not os.path.isdir(BENCH_DIR):
        os.makedirs(BENCH_DIR)


# ----------------------------------------------------------------------
# Core: play one game with a method per role
# ----------------------------------------------------------------------

def current_position(state):
    if state.turn == "THIEF":
        return state.thief_pos
    if state.turn == "GUARD1":
        return state.guard1_pos
    return state.guard2_pos


def choose_move(state, world, table, method, depth):
    """Returns (move_name, nodes_used)."""
    if method == AB:
        stats = SearchStats()
        _, move_name = alpha_beta(state, world, table, depth, stats)
        return move_name, stats.nodes_expanded
    stats = GreedyStats()
    _, move_name = greedy_move(state, world, table, stats)
    return move_name, stats.nodes_expanded


def play_game(world, table, thief_method, guard_method, depth, turn_limit=100, record_moves=False):
    state = initial_state(world)
    thief_nodes = 0
    guard_nodes = 0
    thief_decisions = 0
    guard_decisions = 0
    thief_time = 0.0
    guard_time = 0.0
    moves = []

    turn_number = 0
    while turn_number < turn_limit:
        if is_terminal(state, world):
            break

        is_thief = state.turn == THIEF_TURN
        method = thief_method if is_thief else guard_method

        start = time.perf_counter()
        move_name, nodes = choose_move(state, world, table, method, depth)
        elapsed = time.perf_counter() - start

        chosen_position = None
        for candidate_name, candidate_position in world.legal_moves(current_position(state)):
            if candidate_name == move_name:
                chosen_position = candidate_position
        if chosen_position is None:
            break

        if is_thief:
            thief_nodes += nodes
            thief_decisions += 1
            thief_time += elapsed
        else:
            guard_nodes += nodes
            guard_decisions += 1
            guard_time += elapsed

        if record_moves:
            moves.append((turn_number, state.turn, move_name, state.thief_pos, state.guard1_pos, state.guard2_pos))

        state = apply_move(state, world, chosen_position)
        turn_number += 1

    result = "TURN_LIMIT_REACHED"
    if state.is_capture():
        result = "GUARDS_WIN"
    if state.is_escape(world):
        result = "THIEF_WINS"

    return {
        "result": result,
        "turns": turn_number,
        "thief_nodes": thief_nodes,
        "guard_nodes": guard_nodes,
        "thief_decisions": thief_decisions,
        "guard_decisions": guard_decisions,
        "thief_time": thief_time,
        "guard_time": guard_time,
        "moves": moves,
    }


# ----------------------------------------------------------------------
# Seeded random map generator
# ----------------------------------------------------------------------

def generate_random_world(rng, size=9, wall_prob=0.2):
    """Returns a GridWorld whose thief, artifact, exit and guards are all
    connected, with guards not starting on top of the thief."""
    while True:
        grid = []
        for r in range(size):
            row = []
            for c in range(size):
                border = r == 0 or c == 0 or r == size - 1 or c == size - 1
                if border or rng.random() < wall_prob:
                    row.append("#")
                else:
                    row.append(".")
            grid.append(row)

        floor_cells = []
        for r in range(size):
            for c in range(size):
                if grid[r][c] == ".":
                    floor_cells.append((r, c))
        if len(floor_cells) < 12:
            continue

        picks = rng.sample(floor_cells, 5)
        thief, artifact, exit_cell, g1, g2 = picks
        grid[thief[0]][thief[1]] = "T"
        grid[artifact[0]][artifact[1]] = "A"
        grid[exit_cell[0]][exit_cell[1]] = "E"
        grid[g1[0]][g1[1]] = "G"
        grid[g2[0]][g2[1]] = "G"
        rows = ["".join(row) for row in grid]

        world = GridWorld(rows)
        table = build_distance_table(world)

        if artifact not in table[thief]:
            continue
        if exit_cell not in table[artifact]:
            continue
        if g1 not in table[thief] or g2 not in table[thief]:
            continue
        if table[thief][g1] < 3 or table[thief][g2] < 3:
            continue
        if table[thief][artifact] < 3:
            continue
        return world


def generate_maps(count, seed, size=9):
    rng = random.Random(seed)
    worlds = []
    for _ in range(count):
        worlds.append(generate_random_world(rng, size=size))
    return worlds


# ----------------------------------------------------------------------
# Experiment 1: matchup matrix on the required maps
# ----------------------------------------------------------------------

def experiment_matchups():
    rows = []
    for case_name, map_path, depth, turn_limit in REQUIRED_CASES:
        world = load_map(map_path)
        table = build_distance_table(world)
        for thief_method, guard_method in MATCHUPS:
            game = play_game(world, table, thief_method, guard_method, depth, turn_limit)
            rows.append({
                "case": case_name,
                "depth": depth,
                "matchup": matchup_label(thief_method, guard_method),
                "result": game["result"],
                "turns": game["turns"],
                "thief_nodes": game["thief_nodes"],
                "guard_nodes": game["guard_nodes"],
                "thief_nodes_per_move": round(game["thief_nodes"] / max(1, game["thief_decisions"]), 1),
                "guard_nodes_per_move": round(game["guard_nodes"] / max(1, game["guard_decisions"]), 1),
            })
        print("Matchups done:", case_name)

    path = BENCH_DIR + "/matchups.csv"
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print("Saved", path)

    # Printed table
    print()
    print("Result matrix (T = thief wins, G = guards win, - = turn limit):")
    header = "{:<24}".format("Case")
    for thief_method, guard_method in MATCHUPS:
        header += "{:<26}".format(matchup_label(thief_method, guard_method))
    print(header)
    short = {"THIEF_WINS": "T", "GUARDS_WIN": "G", "TURN_LIMIT_REACHED": "-"}
    index = 0
    for case_name, _, _, _ in REQUIRED_CASES:
        line = "{:<24}".format(case_name)
        for _ in MATCHUPS:
            row = rows[index]
            index += 1
            line += "{:<26}".format(short[row["result"]] + " (" + str(row["turns"]) + " turns)")
        print(line)
    print()

    # Plot: turns per matchup
    case_names = [c[0] for c in REQUIRED_CASES]
    plt.figure(figsize=(10, 5))
    width = 0.2
    for m_index, (thief_method, guard_method) in enumerate(MATCHUPS):
        label = matchup_label(thief_method, guard_method)
        values = []
        for row in rows:
            if row["matchup"] == label:
                values.append(row["turns"])
        positions = [i + (m_index - 1.5) * width for i in range(len(case_names))]
        plt.bar(positions, values, width=width, label=label)
    plt.xticks(range(len(case_names)), case_names, rotation=20, ha="right")
    plt.ylabel("Turns until game ended")
    plt.title("Game length by matchup (outcome letters are in matchups.csv)")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(BENCH_DIR + "/matchups_turns.png")
    plt.close()
    print("Saved", BENCH_DIR + "/matchups_turns.png")
    return rows


# ----------------------------------------------------------------------
# Experiment 2: win rates over many random maps
# ----------------------------------------------------------------------

def experiment_random_maps(num_maps, seed, depth, turn_limit=60):
    worlds = generate_maps(num_maps, seed)
    tables = [build_distance_table(w) for w in worlds]

    rows = []
    for thief_method, guard_method in MATCHUPS:
        thief_wins = 0
        guard_wins = 0
        timeouts = 0
        total_turns = 0
        for world, table in zip(worlds, tables):
            game = play_game(world, table, thief_method, guard_method, depth, turn_limit)
            total_turns += game["turns"]
            if game["result"] == "THIEF_WINS":
                thief_wins += 1
            elif game["result"] == "GUARDS_WIN":
                guard_wins += 1
            else:
                timeouts += 1
        rows.append({
            "matchup": matchup_label(thief_method, guard_method),
            "depth": depth,
            "maps": num_maps,
            "thief_win_pct": round(100.0 * thief_wins / num_maps, 1),
            "guard_win_pct": round(100.0 * guard_wins / num_maps, 1),
            "timeout_pct": round(100.0 * timeouts / num_maps, 1),
            "avg_turns": round(total_turns / num_maps, 1),
        })
        print("Random maps done:", matchup_label(thief_method, guard_method))

    path = BENCH_DIR + "/random_maps_winrates.csv"
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print("Saved", path)

    labels = [r["matchup"] for r in rows]
    thief = [r["thief_win_pct"] for r in rows]
    guard = [r["guard_win_pct"] for r in rows]
    timeout = [r["timeout_pct"] for r in rows]
    plt.figure(figsize=(10, 5))
    positions = list(range(len(labels)))
    plt.bar(positions, thief, label="Thief wins")
    plt.bar(positions, guard, bottom=thief, label="Guards win")
    bottoms = [thief[i] + guard[i] for i in positions]
    plt.bar(positions, timeout, bottom=bottoms, label="Turn limit")
    plt.xticks(positions, labels, rotation=15, ha="right")
    plt.ylabel("% of games")
    plt.title("Outcomes over " + str(num_maps) + " random maps (depth " + str(depth) + ", seed " + str(seed) + ")")
    plt.legend()
    plt.tight_layout()
    plt.savefig(BENCH_DIR + "/random_maps_winrates.png")
    plt.close()
    print("Saved", BENCH_DIR + "/random_maps_winrates.png")
    return rows


# ----------------------------------------------------------------------
# Experiments 3 and 4: depth sweep (win rate and cost per decision)
# ----------------------------------------------------------------------

def experiment_depth_sweep(num_maps, seed, max_depth, turn_limit=60):
    worlds = generate_maps(num_maps, seed)
    tables = [build_distance_table(w) for w in worlds]

    sweep_rows = []
    cost_rows = []

    # Greedy baseline cost (independent of depth), measured once.
    greedy_nodes = 0
    greedy_decisions = 0
    greedy_time = 0.0
    for world, table in zip(worlds, tables):
        game = play_game(world, table, GREEDY, GREEDY, 1, turn_limit)
        greedy_nodes += game["thief_nodes"] + game["guard_nodes"]
        greedy_decisions += game["thief_decisions"] + game["guard_decisions"]
        greedy_time += game["thief_time"] + game["guard_time"]
    greedy_nodes_per_move = greedy_nodes / max(1, greedy_decisions)
    greedy_ms_per_move = 1000.0 * greedy_time / max(1, greedy_decisions)

    for depth in range(1, max_depth + 1):
        # AB thief vs greedy guards: measure thief win rate
        thief_wins = 0
        thief_captured = 0
        ab_nodes = 0
        ab_decisions = 0
        ab_time = 0.0
        # AB guards vs greedy thief: measure guard win rate
        guard_wins = 0

        for world, table in zip(worlds, tables):
            game = play_game(world, table, AB, GREEDY, depth, turn_limit)
            if game["result"] == "THIEF_WINS":
                thief_wins += 1
            if game["result"] == "GUARDS_WIN":
                thief_captured += 1
            ab_nodes += game["thief_nodes"]
            ab_decisions += game["thief_decisions"]
            ab_time += game["thief_time"]

            game = play_game(world, table, GREEDY, AB, depth, turn_limit)
            if game["result"] == "GUARDS_WIN":
                guard_wins += 1
            ab_nodes += game["guard_nodes"]
            ab_decisions += game["guard_decisions"]
            ab_time += game["guard_time"]

        sweep_rows.append({
            "depth": depth,
            "maps": num_maps,
            "ab_thief_vs_greedy_guards_thief_win_pct": round(100.0 * thief_wins / num_maps, 1),
            "ab_thief_vs_greedy_guards_not_captured_pct": round(100.0 * (num_maps - thief_captured) / num_maps, 1),
            "ab_guards_vs_greedy_thief_guard_win_pct": round(100.0 * guard_wins / num_maps, 1),
        })
        cost_rows.append({
            "depth": depth,
            "ab_nodes_per_move": round(ab_nodes / max(1, ab_decisions), 1),
            "ab_ms_per_move": round(1000.0 * ab_time / max(1, ab_decisions), 3),
            "greedy_nodes_per_move": round(greedy_nodes_per_move, 1),
            "greedy_ms_per_move": round(greedy_ms_per_move, 3),
        })
        print("Depth", depth, "done.")

    with open(BENCH_DIR + "/depth_sweep.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sweep_rows[0].keys()))
        writer.writeheader()
        for row in sweep_rows:
            writer.writerow(row)
    print("Saved", BENCH_DIR + "/depth_sweep.csv")

    with open(BENCH_DIR + "/cost_per_decision.csv", "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cost_rows[0].keys()))
        writer.writeheader()
        for row in cost_rows:
            writer.writerow(row)
    print("Saved", BENCH_DIR + "/cost_per_decision.csv")

    depths = [r["depth"] for r in sweep_rows]

    plt.figure(figsize=(8, 5))
    plt.plot(depths, [r["ab_thief_vs_greedy_guards_thief_win_pct"] for r in sweep_rows],
             marker="o", label="Alpha-beta thief vs greedy guards (thief win %)")
    plt.plot(depths, [r["ab_thief_vs_greedy_guards_not_captured_pct"] for r in sweep_rows],
             marker="s", label="Alpha-beta thief vs greedy guards (thief not captured %)")
    plt.plot(depths, [r["ab_guards_vs_greedy_thief_guard_win_pct"] for r in sweep_rows],
             marker="o", label="Alpha-beta guards vs greedy thief (guard win %)")
    plt.xlabel("Alpha-beta search depth (plies)")
    plt.ylabel("Win rate of the alpha-beta side (%)")
    plt.title("Does lookahead beat greedy? (" + str(num_maps) + " random maps)")
    plt.ylim(0, 105)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(BENCH_DIR + "/depth_sweep_winrate.png")
    plt.close()
    print("Saved", BENCH_DIR + "/depth_sweep_winrate.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(depths, [r["ab_nodes_per_move"] for r in cost_rows], marker="o", label="Alpha-beta")
    axes[0].plot(depths, [r["greedy_nodes_per_move"] for r in cost_rows], marker="o", label="Greedy")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Search depth (plies)")
    axes[0].set_ylabel("Nodes per decision (log)")
    axes[0].set_title("Nodes per decision")
    axes[0].legend()
    axes[1].plot(depths, [r["ab_ms_per_move"] for r in cost_rows], marker="o", label="Alpha-beta")
    axes[1].plot(depths, [r["greedy_ms_per_move"] for r in cost_rows], marker="o", label="Greedy")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Search depth (plies)")
    axes[1].set_ylabel("Milliseconds per decision (log)")
    axes[1].set_title("Time per decision")
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(BENCH_DIR + "/cost_per_decision.png")
    plt.close()
    print("Saved", BENCH_DIR + "/cost_per_decision.png")

    return sweep_rows, cost_rows


# ----------------------------------------------------------------------
# Experiment 5: where does alpha-beta (depth 2) diverge from greedy?
# ----------------------------------------------------------------------

def experiment_edge2_trace(depth=2, turn_limit=150):
    world = load_map("maps/edge_case_2_horizon.txt")
    table = build_distance_table(world)

    ab_game = play_game(world, table, AB, AB, depth, turn_limit, record_moves=True)
    gr_game = play_game(world, table, GREEDY, GREEDY, depth, turn_limit, record_moves=True)

    lines = []
    lines.append("Edge case 2 trace, alpha-beta depth " + str(depth) + " vs greedy (same map, same start)")
    lines.append("Alpha-beta result: " + ab_game["result"] + " after " + str(ab_game["turns"]) + " turns")
    lines.append("Greedy result:     " + gr_game["result"] + " after " + str(gr_game["turns"]) + " turns")
    lines.append("")

    first_divergence = None
    limit = min(len(ab_game["moves"]), len(gr_game["moves"]))
    for i in range(limit):
        if ab_game["moves"][i][2] != gr_game["moves"][i][2]:
            first_divergence = i
            break

    if first_divergence is None:
        lines.append("The two games chose identical moves for the whole shared length.")
    else:
        a = ab_game["moves"][first_divergence]
        g = gr_game["moves"][first_divergence]
        lines.append("First divergence at turn " + str(a[0]) + " (" + a[1] + " to move).")
        lines.append("Positions before the move: thief " + str(a[3]) + ", guard1 " + str(a[4]) + ", guard2 " + str(a[5]))
        lines.append("Alpha-beta plays " + a[2] + ", greedy plays " + g[2] + ".")
    differ_thief = 0
    differ_guard = 0
    thief_turns = 0
    guard_turns = 0
    for i in range(limit):
        is_thief_move = ab_game["moves"][i][1] == "THIEF"
        if is_thief_move:
            thief_turns += 1
        else:
            guard_turns += 1
        if ab_game["moves"][i][2] != gr_game["moves"][i][2]:
            if is_thief_move:
                differ_thief += 1
            else:
                differ_guard += 1
    lines.append("Over the first " + str(limit) + " turns the two games differ on " + str(differ_thief) + " of "
                 + str(thief_turns) + " thief moves and " + str(differ_guard) + " of " + str(guard_turns) + " guard moves.")
    lines.append("")

    lines.append("Move-by-move (turn, agent, alpha-beta move | greedy move, thief position before move)")
    for i in range(limit):
        a = ab_game["moves"][i]
        g = gr_game["moves"][i]
        flag = ""
        if a[2] != g[2]:
            flag = "   <-- differs"
        lines.append(str(a[0]).rjust(3) + "  " + a[1].ljust(7) + a[2].ljust(7) + "| " + g[2].ljust(7) + str(a[3]) + flag)

    path = BENCH_DIR + "/edge2_trace.txt"
    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print("Saved", path)
    if first_divergence is not None:
        print("Edge case 2 first divergence at turn", ab_game["moves"][first_divergence][0])


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def run_all(num_maps=30, seed=42, depth=4, max_depth=6):
    ensure_dir()
    start = time.time()

    print("=== 1/4 Matchups on the required maps ===")
    experiment_matchups()

    print("=== 2/4 Random maps, depth", depth, "===")
    experiment_random_maps(num_maps, seed, depth)

    print("=== 3/4 Depth sweep and cost per decision, depths 1 to", max_depth, "===")
    experiment_depth_sweep(num_maps, seed, max_depth)

    print("=== 4/4 Edge case 2 divergence trace ===")
    experiment_edge2_trace()

    print()
    print("Benchmark finished in", round(time.time() - start, 1), "seconds.")
    print("Results are in", BENCH_DIR)
