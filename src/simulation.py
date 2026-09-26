"""
Runs a full game of Museum Heist by repeatedly calling the search function
for whichever agent's turn it is, until someone wins or the turn limit hits.
"""

from src.state import initial_state, apply_move
from src.search import alpha_beta, is_terminal, SearchStats

DEFAULT_TURN_LIMIT = 60
DEFAULT_DEPTH = 4


def run_game(world, distance_table, depth=DEFAULT_DEPTH, turn_limit=DEFAULT_TURN_LIMIT, verbose=True):
    state = initial_state(world)
    stats = SearchStats()
    history = []
    history.append(state)

    turn_number = 0
    while turn_number < turn_limit:
        if is_terminal(state, world):
            break

        score, move_name = alpha_beta(state, world, distance_table, depth, stats)

        moves = None
        chosen_position = None
        for candidate_name, candidate_position in world.legal_moves(current_position(state)):
            if candidate_name == move_name:
                chosen_position = candidate_position

        if chosen_position is None:
            break

        if verbose:
            print("Turn", turn_number, "-", state.turn, "plays", move_name, "score", score)

        state = apply_move(state, world, chosen_position)
        history.append(state)
        turn_number = turn_number + 1

    result = "TURN_LIMIT_REACHED"
    if state.is_capture():
        result = "GUARDS_WIN"
    if state.is_escape(world):
        result = "THIEF_WINS"

    if verbose:
        print("Result:", result, "after", turn_number, "turns")
        print("Total nodes expanded:", stats.nodes_expanded, "pruned:", stats.nodes_pruned)

    return history, result, stats


def current_position(state):
    if state.turn == "THIEF":
        return state.thief_pos
    if state.turn == "GUARD1":
        return state.guard1_pos
    return state.guard2_pos