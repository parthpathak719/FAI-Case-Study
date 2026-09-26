"""
Single entry point for the Museum Heist project.
Run with: python main.py <command> [options]

Commands:
    play      Run one full game and print the turn-by-turn log
    compare   Run minimax vs alpha-beta node counts on one position
    experiments   Run all experiments and regenerate CSVs and plots
"""

import argparse

from src.world import load_map
from src.distances import build_distance_table
from src.state import initial_state
from src.search import minimax, alpha_beta, SearchStats
from src.simulation import run_game


def command_play(args):
    world = load_map(args.map)
    table = build_distance_table(world)
    print("Running game on", args.map, "at depth", args.depth)
    history, result, stats = run_game(world, table, depth=args.depth, turn_limit=args.turn_limit, verbose=True)
    print()
    print("Final result:", result)


def command_compare(args):
    world = load_map(args.map)
    table = build_distance_table(world)
    state = initial_state(world)

    stats_mm = SearchStats()
    score_mm, move_mm = minimax(state, world, table, depth=args.depth, stats=stats_mm)
    print("Minimax: move", move_mm, "score", score_mm, "nodes", stats_mm.nodes_expanded)

    stats_ab = SearchStats()
    score_ab, move_ab = alpha_beta(state, world, table, depth=args.depth, stats=stats_ab)
    print("Alpha-beta: move", move_ab, "score", score_ab, "nodes", stats_ab.nodes_expanded, "pruned", stats_ab.nodes_pruned)

def command_visualize(args):
    from src.visualize import save_history_as_gif

    world = load_map(args.map)
    table = build_distance_table(world)
    print("Running game on", args.map, "at depth", args.depth, "for the GIF")
    history, result, stats = run_game(world, table, depth=args.depth, turn_limit=args.turn_limit, verbose=False)
    print("Result:", result, "after", len(history) - 1, "turns")
    save_history_as_gif(history, world, args.output)

def command_experiments(args):
    from src.experiments import (
        experiment_nodes_vs_depth,
        experiment_all_cases,
        plot_all_cases_comparison,
        experiment_coordination_comparison,
    )
    experiment_nodes_vs_depth()
    experiment_all_cases()
    plot_all_cases_comparison()
    experiment_coordination_comparison()
    print("All experiments complete. Check the outputs folder.")


def build_parser():
    parser = argparse.ArgumentParser(description="Museum Heist multi-agent search simulation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    play_parser = subparsers.add_parser("play", help="Run one full game")
    play_parser.add_argument("--map", default="maps/working_case_1.txt")
    play_parser.add_argument("--depth", type=int, default=6)
    play_parser.add_argument("--turn_limit", type=int, default=100)
    play_parser.set_defaults(func=command_play)

    compare_parser = subparsers.add_parser("compare", help="Compare minimax vs alpha-beta on one position")
    compare_parser.add_argument("--map", default="maps/working_case_1.txt")
    compare_parser.add_argument("--depth", type=int, default=6)
    compare_parser.set_defaults(func=command_compare)

    experiments_parser = subparsers.add_parser("experiments", help="Run all experiments and regenerate plots")
    experiments_parser.set_defaults(func=command_experiments)
    
    visualize_parser = subparsers.add_parser("visualize", help="Run a game and export it as a GIF")
    visualize_parser.add_argument("--map", default="maps/working_case_1.txt")
    visualize_parser.add_argument("--depth", type=int, default=6)
    visualize_parser.add_argument("--turn_limit", type=int, default=100)
    visualize_parser.add_argument("--output", default="outputs/game.gif")
    visualize_parser.set_defaults(func=command_visualize)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)