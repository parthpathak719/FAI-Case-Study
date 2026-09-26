"""
Represents one snapshot of the game: where everyone is, whose turn it is,
and whether the artifact has been picked up.
"""

THIEF_TURN = "THIEF"
GUARD1_TURN = "GUARD1"
GUARD2_TURN = "GUARD2"

TURN_ORDER = [THIEF_TURN, GUARD1_TURN, GUARD2_TURN]


class GameState:
    def __init__(self, thief_pos, guard1_pos, guard2_pos, artifact_taken, turn, ply_count):
        self.thief_pos = thief_pos
        self.guard1_pos = guard1_pos
        self.guard2_pos = guard2_pos
        self.artifact_taken = artifact_taken
        self.turn = turn
        self.ply_count = ply_count

    def guard_positions(self):
        return [self.guard1_pos, self.guard2_pos]

    def is_capture(self):
        if self.thief_pos == self.guard1_pos:
            return True
        if self.thief_pos == self.guard2_pos:
            return True
        return False

    def is_escape(self, world):
        if self.artifact_taken and self.thief_pos == world.exit_pos:
            return True
        return False

    def next_turn(self):
        current_index = TURN_ORDER.index(self.turn)
        next_index = (current_index + 1) % len(TURN_ORDER)
        return TURN_ORDER[next_index]


def initial_state(world):
    return GameState(
        thief_pos=world.thief_start,
        guard1_pos=world.guard_starts[0],
        guard2_pos=world.guard_starts[1],
        artifact_taken=False,
        turn=THIEF_TURN,
        ply_count=0,
    )


def apply_move(state, world, new_position):
    new_thief_pos = state.thief_pos
    new_guard1_pos = state.guard1_pos
    new_guard2_pos = state.guard2_pos

    if state.turn == THIEF_TURN:
        new_thief_pos = new_position
    if state.turn == GUARD1_TURN:
        new_guard1_pos = new_position
    if state.turn == GUARD2_TURN:
        new_guard2_pos = new_position

    new_artifact_taken = state.artifact_taken
    if new_thief_pos == world.artifact_pos:
        new_artifact_taken = True

    return GameState(
        thief_pos=new_thief_pos,
        guard1_pos=new_guard1_pos,
        guard2_pos=new_guard2_pos,
        artifact_taken=new_artifact_taken,
        turn=state.next_turn(),
        ply_count=state.ply_count + 1,
    )


def legal_moves_for_current_agent(state, world):
    if state.turn == THIEF_TURN:
        current_pos = state.thief_pos
    if state.turn == GUARD1_TURN:
        current_pos = state.guard1_pos
    if state.turn == GUARD2_TURN:
        current_pos = state.guard2_pos

    return world.legal_moves(current_pos)