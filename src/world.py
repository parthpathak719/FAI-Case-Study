"""
Grid world loader for the Museum Heist simulation.

Map file format (plain text, one row per line):
    #  wall
    .  floor (walkable)
    A  artifact position
    E  exit position
    T  thief start position
    G  guard start position (used twice, once per guard)
"""

MOVES = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
    "WAIT": (0, 0),
}


class GridWorld:
    def __init__(self, grid_rows):
        self.rows = len(grid_rows)
        self.cols = len(grid_rows[0])
        self.grid = grid_rows

        self.artifact_pos = None
        self.exit_pos = None
        self.thief_start = None
        self.guard_starts = []

        self._find_special_cells()

    def _find_special_cells(self):
        row_index = 0
        while row_index < self.rows:
            col_index = 0
            while col_index < self.cols:
                cell = self.grid[row_index][col_index]
                position = (row_index, col_index)

                if cell == "A":
                    self.artifact_pos = position
                if cell == "E":
                    self.exit_pos = position
                if cell == "T":
                    self.thief_start = position
                if cell == "G":
                    self.guard_starts.append(position)

                col_index = col_index + 1
            row_index = row_index + 1

    def in_bounds(self, position):
        row, col = position
        if row < 0:
            return False
        if row >= self.rows:
            return False
        if col < 0:
            return False
        if col >= self.cols:
            return False
        return True

    def is_wall(self, position):
        row, col = position
        return self.grid[row][col] == "#"

    def is_walkable(self, position):
        if not self.in_bounds(position):
            return False
        if self.is_wall(position):
            return False
        return True

    def legal_moves(self, position):
        moves = []
        for move_name in MOVES:
            delta_row, delta_col = MOVES[move_name]
            new_position = (position[0] + delta_row, position[1] + delta_col)
            if self.is_walkable(new_position):
                moves.append((move_name, new_position))
        return moves


def load_map(file_path):
    grid_rows = []
    with open(file_path, "r") as file_handle:
        for line in file_handle:
            clean_line = line.rstrip("\n")
            if len(clean_line) > 0:
                grid_rows.append(clean_line)

    max_len = 0
    for row in grid_rows:
        if len(row) > max_len:
            max_len = len(row)

    padded_rows = []
    for row in grid_rows:
        padded_row = row
        while len(padded_row) < max_len:
            padded_row = padded_row + "#"
        padded_rows.append(padded_row)

    return GridWorld(padded_rows)