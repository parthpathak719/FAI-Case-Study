"""
Heuristic evaluation function for a GameState, used at the search depth limit.
Positive scores favor the thief. Negative scores favor the guards.
"""

from src.distances import get_distance

WIN_SCORE = 1000
LOSS_SCORE = -1000


def evaluate(state, world, distance_table):
    if state.is_capture():
        return LOSS_SCORE

    if state.is_escape(world):
        return WIN_SCORE

    if state.artifact_taken:
        thief_goal_distance = get_distance(distance_table, state.thief_pos, world.exit_pos)
    else:
        thief_goal_distance = get_distance(distance_table, state.thief_pos, world.artifact_pos)

    if thief_goal_distance is None:
        thief_goal_distance = 0

    guard_distances = []
    for guard_pos in state.guard_positions():
        distance = get_distance(distance_table, state.thief_pos, guard_pos)
        if distance is not None:
            guard_distances.append(distance)

    if len(guard_distances) > 0:
        nearest_guard_distance = min(guard_distances)
    else:
        nearest_guard_distance = 0

    score = nearest_guard_distance - thief_goal_distance

    if state.artifact_taken:
        score = score + 5

    return score