"""
Renders a game's turn history as a GIF using Pillow. No external windowing
library needed, works headless, and produces a file directly usable in the
presentation.
"""

from PIL import Image, ImageDraw

CELL_SIZE = 60

WALL_COLOR = (40, 40, 40)
FLOOR_COLOR = (235, 235, 235)
ARTIFACT_COLOR = (218, 165, 32)
EXIT_COLOR = (100, 200, 100)
THIEF_COLOR = (200, 40, 40)
GUARD_COLOR = (40, 40, 200)


def draw_frame(world, state):
    width = world.cols * CELL_SIZE
    height = world.rows * CELL_SIZE
    image = Image.new("RGB", (width, height), FLOOR_COLOR)
    draw = ImageDraw.Draw(image)

    row_index = 0
    while row_index < world.rows:
        col_index = 0
        while col_index < world.cols:
            x0 = col_index * CELL_SIZE
            y0 = row_index * CELL_SIZE
            x1 = x0 + CELL_SIZE
            y1 = y0 + CELL_SIZE

            if world.is_wall((row_index, col_index)):
                draw.rectangle([x0, y0, x1, y1], fill=WALL_COLOR)

            col_index = col_index + 1
        row_index = row_index + 1

    if not state.artifact_taken:
        if world.artifact_pos is not None:
            draw_marker(draw, world.artifact_pos, ARTIFACT_COLOR)

    if world.exit_pos is not None:
        draw_marker(draw, world.exit_pos, EXIT_COLOR)
    draw_marker(draw, state.guard1_pos, GUARD_COLOR)
    draw_marker(draw, state.guard2_pos, GUARD_COLOR)
    draw_marker(draw, state.thief_pos, THIEF_COLOR)

    return image


def draw_marker(draw, position, color):
    row, col = position
    x0 = col * CELL_SIZE + 8
    y0 = row * CELL_SIZE + 8
    x1 = x0 + CELL_SIZE - 16
    y1 = y0 + CELL_SIZE - 16
    draw.ellipse([x0, y0, x1, y1], fill=color)


def save_history_as_gif(history, world, output_path, frame_duration_ms=400):
    frames = []
    for state in history:
        frame = draw_frame(world, state)
        frames.append(frame)

    first_frame = frames[0]
    remaining_frames = frames[1:]
    first_frame.save(
        output_path,
        save_all=True,
        append_images=remaining_frames,
        duration=frame_duration_ms,
        loop=0,
    )
    print("Saved GIF to", output_path, "with", len(frames), "frames")