"""
Greedy one-step search, used as a comparison baseline against minimax
and alpha-beta. Each agent looks only one move ahead and picks whichever
neighboring state has the best immediate evaluation score for it.
"""

from src.state import apply_move, legal_moves_for_current_agent, THIEF_TURN
from src.evaluation import evaluate


class GreedyStats:
    def __init__(self):
        self.nodes_expanded = 0

    def reset(self):
        self.nodes_expanded = 0


def greedy_move(state, world, distance_table, stats):
    moves = legal_moves_for_current_agent(state, world)
    is_thief = state.turn == THIEF_TURN

    best_move = None
    if is_thief:
        best_score = float("-inf")
    else:
        best_score = float("inf")

    for move_name, new_position in moves:
        stats.nodes_expanded = stats.nodes_expanded + 1
        child_state = apply_move(state, world, new_position)
        child_score = evaluate(child_state, world, distance_table)

        if is_thief:
            if child_score > best_score:
                best_score = child_score
                best_move = move_name
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = move_name

    return best_score, best_move