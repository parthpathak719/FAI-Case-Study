"""
Full sweep over guard row positions on both side corridors, tested at a
wider depth gap (depth 2 vs depth 8), to find a genuine horizon effect.
Only divergent results are printed.
"""

from src.world import GridWorld
from src.distances import build_distance_table
from src.simulation import run_game

BASE_ROWS = [
    "#########",
    "#T..#...#",
    "#.#.#.#.#",
    "#.#.#.#.#",
    "#.#A#.#.#",
    "#.#.#.#.#",
    "#.#.#.#.#",
    "#.#.#.#.#",
    "#.#.#.#.#",
    "#.......#",
    "####E####",
]

LEFT_COL = 1
RIGHT_COL = 7
ROW_RANGE = range(1, 9)


def build_world_with_guards(guard_positions):
    row_list = []
    for row in BASE_ROWS:
        row_list.append(list(row))

    for guard_row, guard_col in guard_positions:
        if row_list[guard_row][guard_col] == "#":
            return None
        row_list[guard_row][guard_col] = "G"

    final_rows = []
    for row_chars in row_list:
        final_rows.append("".join(row_chars))

    return GridWorld(final_rows)


found_any = False
tested_count = 0

for guard1_row in ROW_RANGE:
    for guard2_row in ROW_RANGE:
        guard_positions = [(guard1_row, LEFT_COL), (guard2_row, RIGHT_COL)]
        world = build_world_with_guards(guard_positions)
        if world is None:
            continue
        if world.thief_start is None:
            continue
        if len(world.guard_starts) != 2:
            continue

        table = build_distance_table(world)
        tested_count = tested_count + 1

        _, result_shallow, _ = run_game(world, table, depth=2, verbose=False)
        _, result_deep, _ = run_game(world, table, depth=8, verbose=False)

        if result_shallow != result_deep:
            found_any = True
            print("Guards at", guard_positions, "| depth2:", result_shallow, "| depth8:", result_deep, " <-- DIVERGENCE")

print()
print("Tested", tested_count, "combinations.")
if found_any:
    print("Divergent map(s) found above. Use one of those guard placements.")
else:
    print("Still no divergence. We will need a different map shape, not just different positions.")