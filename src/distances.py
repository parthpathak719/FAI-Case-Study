"""
Precomputes shortest path distances between every pair of walkable cells.
This avoids running BFS again and again inside minimax.
"""

from collections import deque


def bfs_from_source(world, source):
    distances = {}
    distances[source] = 0

    queue = deque()
    queue.append(source)

    while len(queue) > 0:
        current = queue.popleft()
        current_distance = distances[current]

        for move_name, next_position in world.legal_moves(current):
            if move_name == "WAIT":
                continue
            if next_position not in distances:
                distances[next_position] = current_distance + 1
                queue.append(next_position)

    return distances


def build_distance_table(world):
    table = {}

    row_index = 0
    while row_index < world.rows:
        col_index = 0
        while col_index < world.cols:
            position = (row_index, col_index)
            if world.is_walkable(position):
                table[position] = bfs_from_source(world, position)
            col_index = col_index + 1
        row_index = row_index + 1

    return table


def get_distance(table, source, target):
    if source not in table:
        return None
    if target not in table[source]:
        return None
    return table[source][target]