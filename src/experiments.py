"""
Runs all experiments needed for the report:
1. Nodes expanded vs depth, minimax vs alpha-beta (on working_case_1)
2. Runtime vs depth, minimax vs alpha-beta (on working_case_1)
3. Full results for all four required cases (working 1, working 2, edge 1, edge 2)
4. Greedy comparison on the same four cases

Saves CSV files to outputs/ and PNG plots to outputs/.
"""

import csv
import time
import matplotlib.pyplot as plt

from src.world import load_map
from src.distances import build_distance_table
from src.state import initial_state, apply_move
from src.search import minimax, alpha_beta, SearchStats
from src.greedy import greedy_move, GreedyStats
from src.simulation import run_game

OUTPUT_DIR = "outputs"


def get_current_position(state):
    if state.turn == "THIEF":
        return state.thief_pos
    if state.turn == "GUARD1":
        return state.guard1_pos
    return state.guard2_pos


def experiment_nodes_vs_depth():
    world = load_map("maps/working_case_1.txt")
    table = build_distance_table(world)
    state = initial_state(world)

    depths = [2, 3, 4, 5, 6, 7]
    rows = []

    for depth in depths:
        stats_mm = SearchStats()
        start_time = time.time()
        minimax(state, world, table, depth, stats_mm)
        mm_time = time.time() - start_time

        stats_ab = SearchStats()
        start_time = time.time()
        alpha_beta(state, world, table, depth, stats_ab)
        ab_time = time.time() - start_time

        rows.append({
            "depth": depth,
            "minimax_nodes": stats_mm.nodes_expanded,
            "alpha_beta_nodes": stats_ab.nodes_expanded,
            "alpha_beta_pruned": stats_ab.nodes_pruned,
            "minimax_time_seconds": round(mm_time, 4),
            "alpha_beta_time_seconds": round(ab_time, 4),
        })
        print("Depth", depth, "done. Minimax nodes:", stats_mm.nodes_expanded, "Alpha-beta nodes:", stats_ab.nodes_expanded)

    csv_path = OUTPUT_DIR + "/nodes_vs_depth.csv"
    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print("Saved", csv_path)

    depth_values = [row["depth"] for row in rows]
    mm_values = [row["minimax_nodes"] for row in rows]
    ab_values = [row["alpha_beta_nodes"] for row in rows]

    plt.figure()
    plt.plot(depth_values, mm_values, marker="o", label="Minimax")
    plt.plot(depth_values, ab_values, marker="o", label="Alpha-beta")
    plt.xlabel("Search depth")
    plt.ylabel("Nodes expanded")
    plt.title("Nodes expanded vs depth (Working Case 1)")
    plt.legend()
    plt.savefig(OUTPUT_DIR + "/nodes_vs_depth.png")
    plt.close()
    print("Saved", OUTPUT_DIR + "/nodes_vs_depth.png")

    time_mm_values = [row["minimax_time_seconds"] for row in rows]
    time_ab_values = [row["alpha_beta_time_seconds"] for row in rows]

    plt.figure()
    plt.plot(depth_values, time_mm_values, marker="o", label="Minimax")
    plt.plot(depth_values, time_ab_values, marker="o", label="Alpha-beta")
    plt.xlabel("Search depth")
    plt.ylabel("Time (seconds)")
    plt.title("Runtime vs depth (Working Case 1)")
    plt.legend()
    plt.savefig(OUTPUT_DIR + "/runtime_vs_depth.png")
    plt.close()
    print("Saved", OUTPUT_DIR + "/runtime_vs_depth.png")


def run_alpha_beta_case(map_path, depth, turn_limit):
    world = load_map(map_path)
    table = build_distance_table(world)
    history, result, stats = run_game(world, table, depth=depth, turn_limit=turn_limit, verbose=False)
    return {
        "result": result,
        "turns": len(history) - 1,
        "nodes_expanded": stats.nodes_expanded,
        "nodes_pruned": stats.nodes_pruned,
    }


def run_greedy_case(map_path, turn_limit):
    world = load_map(map_path)
    table = build_distance_table(world)
    state = initial_state(world)
    stats = GreedyStats()

    turn_number = 0
    result = "TURN_LIMIT_REACHED"

    while turn_number < turn_limit:
        if state.is_capture():
            result = "GUARDS_WIN"
            break
        if state.is_escape(world):
            result = "THIEF_WINS"
            break

        _, move_name = greedy_move(state, world, table, stats)
        chosen_position = None
        for candidate_name, candidate_position in world.legal_moves(get_current_position(state)):
            if candidate_name == move_name:
                chosen_position = candidate_position

        state = apply_move(state, world, chosen_position)
        turn_number = turn_number + 1

    return {
        "result": result,
        "turns": turn_number,
        "nodes_expanded": stats.nodes_expanded,
        "nodes_pruned": 0,
    }


def experiment_all_cases():
    cases = [
        ("Working Case 1", "maps/working_case_1.txt", 6, 100),
        ("Working Case 2", "maps/working_case_2.txt", 6, 100),
        ("Edge Case 1 (trapped)", "maps/edge_case_1_trapped.txt", 4, 30),
        ("Edge Case 2 (depth 2)", "maps/edge_case_2_horizon.txt", 2, 150),
        ("Edge Case 2 (depth 8)", "maps/edge_case_2_horizon.txt", 8, 150),
    ]

    rows = []
    for case_name, map_path, depth, turn_limit in cases:
        ab_result = run_alpha_beta_case(map_path, depth, turn_limit)
        greedy_result = run_greedy_case(map_path, turn_limit)

        rows.append({
            "case": case_name,
            "depth": depth,
            "alpha_beta_result": ab_result["result"],
            "alpha_beta_turns": ab_result["turns"],
            "alpha_beta_nodes": ab_result["nodes_expanded"],
            "alpha_beta_pruned": ab_result["nodes_pruned"],
            "greedy_result": greedy_result["result"],
            "greedy_turns": greedy_result["turns"],
            "greedy_nodes": greedy_result["nodes_expanded"],
        })
        print("Finished:", case_name)

    csv_path = OUTPUT_DIR + "/all_cases_summary.csv"
    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print("Saved", csv_path)

def plot_all_cases_comparison():
    case_names = []
    ab_nodes = []
    greedy_nodes = []
    ab_turns = []
    greedy_turns = []

    with open(OUTPUT_DIR + "/all_cases_summary.csv", "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            case_names.append(row["case"])
            ab_nodes.append(int(row["alpha_beta_nodes"]))
            greedy_nodes.append(int(row["greedy_nodes"]))
            ab_turns.append(int(row["alpha_beta_turns"]))
            greedy_turns.append(int(row["greedy_turns"]))

    x_positions = range(len(case_names))
    bar_width = 0.35

    plt.figure(figsize=(9, 5))
    left_positions = [x - bar_width / 2 for x in x_positions]
    right_positions = [x + bar_width / 2 for x in x_positions]
    plt.bar(left_positions, ab_nodes, width=bar_width, label="Alpha-beta")
    plt.bar(right_positions, greedy_nodes, width=bar_width, label="Greedy")
    plt.yscale("log")
    plt.xticks(list(x_positions), case_names, rotation=20, ha="right")
    plt.ylabel("Nodes expanded (log scale)")
    plt.title("Nodes expanded across all cases")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR + "/all_cases_nodes_comparison.png")
    plt.close()
    print("Saved", OUTPUT_DIR + "/all_cases_nodes_comparison.png")

    plt.figure(figsize=(9, 5))
    plt.bar(left_positions, ab_turns, width=bar_width, label="Alpha-beta")
    plt.bar(right_positions, greedy_turns, width=bar_width, label="Greedy")
    plt.xticks(list(x_positions), case_names, rotation=20, ha="right")
    plt.ylabel("Turns taken")
    plt.title("Turns taken across all cases")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR + "/all_cases_turns_comparison.png")
    plt.close()
    print("Saved", OUTPUT_DIR + "/all_cases_turns_comparison.png")

def experiment_coordination_comparison():
    from src.independent_guards import run_independent_game

    world = load_map("maps/working_case_1.txt")
    table = build_distance_table(world)

    rows = []

    _, coordinated_result_6, coordinated_stats_6 = run_game(world, table, depth=6, turn_limit=100, verbose=False)
    rows.append({
        "setup": "Coordinated",
        "depth": 6,
        "result": coordinated_result_6,
        "nodes_expanded": coordinated_stats_6.nodes_expanded,
    })

    independent_result_6, independent_turns_6, independent_nodes_6 = run_independent_game(
        world, table, depth=6, turn_limit=100, verbose=False
    )
    rows.append({
        "setup": "Independent",
        "depth": 6,
        "result": independent_result_6,
        "nodes_expanded": independent_nodes_6,
    })

    _, coordinated_result_9, coordinated_stats_9 = run_game(world, table, depth=9, turn_limit=100, verbose=False)
    rows.append({
        "setup": "Coordinated",
        "depth": 9,
        "result": coordinated_result_9,
        "nodes_expanded": coordinated_stats_9.nodes_expanded,
    })

    csv_path = OUTPUT_DIR + "/coordination_comparison.csv"
    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print("Saved", csv_path)

    for row in rows:
        print(row)

if __name__ == "__main__":
    print("Running nodes vs depth experiment...")
    experiment_nodes_vs_depth()

    print()
    print("Running all-cases summary experiment...")
    experiment_all_cases()

    print()
    print("Plotting all-cases comparison...")
    plot_all_cases_comparison()

    print()
    print("Running coordination comparison experiment...")
    experiment_coordination_comparison()

    print()
    print("All experiments complete. Check the outputs folder.")