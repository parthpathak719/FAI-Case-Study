"""
Independent guard search. Each guard runs its own depth-limited minimax
against the thief, using the same depth as the coordinated version, but
treats the other guard as a static obstacle rather than a planning agent.
This isolates the effect of coordination while keeping search depth equal,
so the comparison against src/search.py is fair.
"""

from src.state import apply_move
from src.evaluation import get_distance
from src.distances import get_distance as table_get_distance


class IndependentStats:
    def __init__(self):
        self.nodes_expanded = 0

    def reset(self):
        self.nodes_expanded = 0


def evaluate_solo(thief_pos, guard_pos, frozen_other_guard_pos, world, distance_table, artifact_taken):
    if thief_pos == guard_pos:
        return -1000
    if thief_pos == frozen_other_guard_pos:
        return -1000
    if artifact_taken and thief_pos == world.exit_pos:
        return 1000

    if artifact_taken:
        thief_goal_distance = table_get_distance(distance_table, thief_pos, world.exit_pos)
    else:
        thief_goal_distance = table_get_distance(distance_table, thief_pos, world.artifact_pos)
    if thief_goal_distance is None:
        thief_goal_distance = 0

    guard_distance = table_get_distance(distance_table, thief_pos, guard_pos)
    if guard_distance is None:
        guard_distance = 0

    score = guard_distance - thief_goal_distance
    if artifact_taken:
        score = score + 5

    return score


def solo_minimax(thief_pos, guard_pos, frozen_other_guard_pos, artifact_taken, world,
                  distance_table, depth, is_thief_turn, stats):
    stats.nodes_expanded = stats.nodes_expanded + 1

    if thief_pos == guard_pos or thief_pos == frozen_other_guard_pos:
        return -1000, None
    if artifact_taken and thief_pos == world.exit_pos:
        return 1000, None
    if depth == 0:
        return evaluate_solo(thief_pos, guard_pos, frozen_other_guard_pos, world, distance_table, artifact_taken), None

    if is_thief_turn:
        current_pos = thief_pos
    else:
        current_pos = guard_pos

    best_move = None
    if is_thief_turn:
        best_score = float("-inf")
    else:
        best_score = float("inf")

    for move_name, new_position in world.legal_moves(current_pos):
        new_thief_pos = thief_pos
        new_guard_pos = guard_pos
        new_artifact_taken = artifact_taken

        if is_thief_turn:
            new_thief_pos = new_position
            if new_thief_pos == world.artifact_pos:
                new_artifact_taken = True
        else:
            new_guard_pos = new_position

        child_score, _ = solo_minimax(
            new_thief_pos, new_guard_pos, frozen_other_guard_pos, new_artifact_taken,
            world, distance_table, depth - 1, not is_thief_turn, stats
        )

        if is_thief_turn:
            if child_score > best_score:
                best_score = child_score
                best_move = move_name
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = move_name

    return best_score, best_move


def independent_guard_move(state, world, distance_table, guard_number, depth, stats):
    if guard_number == 1:
        guard_pos = state.guard1_pos
        frozen_other_guard_pos = state.guard2_pos
    else:
        guard_pos = state.guard2_pos
        frozen_other_guard_pos = state.guard1_pos

    _, move_name = solo_minimax(
        state.thief_pos, guard_pos, frozen_other_guard_pos, state.artifact_taken,
        world, distance_table, depth, is_thief_turn=False, stats=stats
    )
    return move_name

def run_independent_game(world, distance_table, depth, turn_limit=100, verbose=False):
    from src.state import initial_state, THIEF_TURN, GUARD1_TURN, GUARD2_TURN
    from src.search import alpha_beta, SearchStats

    state = initial_state(world)
    thief_stats = SearchStats()
    guard_stats = IndependentStats()

    turn_number = 0
    while turn_number < turn_limit:
        if state.is_capture():
            break
        if state.is_escape(world):
            break

        if state.turn == THIEF_TURN:
            _, move_name = alpha_beta(state, world, distance_table, depth, thief_stats)
            current_pos = state.thief_pos
        elif state.turn == GUARD1_TURN:
            move_name = independent_guard_move(state, world, distance_table, 1, depth, guard_stats)
            current_pos = state.guard1_pos
        else:
            move_name = independent_guard_move(state, world, distance_table, 2, depth, guard_stats)
            current_pos = state.guard2_pos

        chosen_position = None
        for candidate_name, candidate_position in world.legal_moves(current_pos):
            if candidate_name == move_name:
                chosen_position = candidate_position

        if verbose:
            print("Turn", turn_number, "-", state.turn, "plays", move_name)

        state = apply_move(state, world, chosen_position)
        turn_number = turn_number + 1

    result = "TURN_LIMIT_REACHED"
    if state.is_capture():
        result = "GUARDS_WIN"
    if state.is_escape(world):
        result = "THIEF_WINS"

    total_nodes = thief_stats.nodes_expanded + guard_stats.nodes_expanded
    return result, turn_number, total_nodes