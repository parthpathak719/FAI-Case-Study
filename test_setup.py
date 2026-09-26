from src.world import load_map
from src.distances import build_distance_table
from src.independent_guards import run_independent_game
from src.simulation import run_game

world = load_map("maps/working_case_1.txt")
table = build_distance_table(world)

print("Coordinated guards (existing team minimax):")
_, coordinated_result, coordinated_stats = run_game(world, table, depth=6, turn_limit=100, verbose=False)
print("Result:", coordinated_result)
print("Nodes:", coordinated_stats.nodes_expanded)

print()
print("Independent guards (solo minimax each):")
result, turns, nodes = run_independent_game(world, table, depth=6, turn_limit=100, verbose=True)
print("Result:", result, "after", turns, "turns")
print("Total nodes:", nodes)

print()
print("Coordinated guards at depth 9 (partial equalization):")
_, coordinated_result_9, coordinated_stats_9 = run_game(world, table, depth=9, turn_limit=100, verbose=False)
print("Result:", coordinated_result_9)
print("Nodes:", coordinated_stats_9.nodes_expanded)