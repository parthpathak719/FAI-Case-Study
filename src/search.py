"""
Depth-limited Minimax and Alpha-Beta search for the Museum Heist game.

Turn order per full round: THIEF (MAX), GUARD1 (MIN), GUARD2 (MIN).
The thief tries to maximize the evaluation score, both guards try to minimize it.
"""

from src.state import apply_move, legal_moves_for_current_agent, THIEF_TURN
from src.evaluation import evaluate, WIN_SCORE, LOSS_SCORE

MAX_TURN_TYPES = [THIEF_TURN]


class SearchStats:
    def __init__(self):
        self.nodes_expanded = 0
        self.nodes_pruned = 0

    def reset(self):
        self.nodes_expanded = 0
        self.nodes_pruned = 0


def is_terminal(state, world):
    if state.is_capture():
        return True
    if state.is_escape(world):
        return True
    return False


def minimax(state, world, distance_table, depth, stats):
    stats.nodes_expanded = stats.nodes_expanded + 1

    if is_terminal(state, world):
        return evaluate(state, world, distance_table), None

    if depth == 0:
        return evaluate(state, world, distance_table), None

    moves = legal_moves_for_current_agent(state, world)
    is_maximizing = state.turn in MAX_TURN_TYPES

    best_move = None
    if is_maximizing:
        best_score = float("-inf")
    else:
        best_score = float("inf")

    for move_name, new_position in moves:
        child_state = apply_move(state, world, new_position)
        child_score, _ = minimax(child_state, world, distance_table, depth - 1, stats)

        if is_maximizing:
            if child_score > best_score:
                best_score = child_score
                best_move = move_name
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = move_name

    return best_score, best_move


def alpha_beta(state, world, distance_table, depth, stats, alpha=float("-inf"), beta=float("inf")):
    stats.nodes_expanded = stats.nodes_expanded + 1

    if is_terminal(state, world):
        return evaluate(state, world, distance_table), None

    if depth == 0:
        return evaluate(state, world, distance_table), None

    moves = legal_moves_for_current_agent(state, world)
    moves = order_moves(state, world, distance_table, moves)
    is_maximizing = state.turn in MAX_TURN_TYPES

    best_move = None
    if is_maximizing:
        best_score = float("-inf")
    else:
        best_score = float("inf")

    for move_name, new_position in moves:
        child_state = apply_move(state, world, new_position)
        child_score, _ = alpha_beta(child_state, world, distance_table, depth - 1, stats, alpha, beta)

        if is_maximizing:
            if child_score > best_score:
                best_score = child_score
                best_move = move_name
            if best_score > alpha:
                alpha = best_score
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = move_name
            if best_score < beta:
                beta = best_score

        if beta <= alpha:
            stats.nodes_pruned = stats.nodes_pruned + 1
            break

    return best_score, best_move


def order_moves(state, world, distance_table, moves):
    from src.distances import get_distance

    if state.turn == THIEF_TURN:
        if state.artifact_taken:
            goal = world.exit_pos
        else:
            goal = world.artifact_pos

        def sort_key(move_item):
            _, new_position = move_item
            distance = get_distance(distance_table, new_position, goal)
            if distance is None:
                return 999
            return distance

        return sorted(moves, key=sort_key)

    def sort_key_guard(move_item):
        _, new_position = move_item
        distance = get_distance(distance_table, new_position, state.thief_pos)
        if distance is None:
            return 999
        return distance

    return sorted(moves, key=sort_key_guard)