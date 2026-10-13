"""
Generates a real search tree picture from the actual game code, instead of
a hand-drawn illustration. Mirrors the exact logic in src/search.py
(alpha_beta), but also records every node visited so it can be drawn.

Usage:
    python tree_trace.py --map maps/working_case_1.txt --depth 2
    python tree_trace.py --map maps/working_case_1.txt --depth 3 --algo minimax

Outputs:
    outputs/search_tree.png   a labelled tree diagram
    Also prints an indented text version of the same tree to the terminal.
"""

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.world import load_map
from src.distances import build_distance_table
from src.state import initial_state, apply_move, legal_moves_for_current_agent, THIEF_TURN
from src.evaluation import evaluate
from src.search import is_terminal, order_moves

NODE_COUNTER = [0]
NODES = []


def new_node(parent_id, move_label, is_max, depth_remaining):
    node_id = NODE_COUNTER[0]
    NODE_COUNTER[0] += 1
    node = {
        "id": node_id,
        "parent": parent_id,
        "move": move_label,
        "is_max": is_max,
        "depth_remaining": depth_remaining,
        "score": None,
        "pruned": False,
        "leaf": False,
        "children": [],
    }
    NODES.append(node)
    if parent_id is not None:
        NODES[parent_id]["children"].append(node_id)
    return node


def traced_search(state, world, table, depth, parent_id, move_label, alpha, beta, use_pruning):
    is_max = state.turn == THIEF_TURN
    node = new_node(parent_id, move_label, is_max, depth)

    if is_terminal(state, world) or depth == 0:
        node["score"] = evaluate(state, world, table)
        node["leaf"] = True
        return node["score"]

    moves = legal_moves_for_current_agent(state, world)
    if use_pruning:
        moves = order_moves(state, world, table, moves)

    best_score = float("-inf") if is_max else float("inf")

    for index, (move_name, new_position) in enumerate(moves):
        child_state = apply_move(state, world, new_position)
        child_score = traced_search(
            child_state, world, table, depth - 1, node["id"], move_name, alpha, beta, use_pruning
        )

        if is_max:
            if child_score > best_score:
                best_score = child_score
            if use_pruning and best_score > alpha:
                alpha = best_score
        else:
            if child_score < best_score:
                best_score = child_score
            if use_pruning and best_score < beta:
                beta = best_score

        if use_pruning and beta <= alpha:
            for skipped_name, _ in moves[index + 1:]:
                pruned = new_node(node["id"], skipped_name, not is_max, depth - 1)
                pruned["pruned"] = True
                pruned["leaf"] = True
            break

    node["score"] = best_score
    return best_score


def print_text_tree(node_id, indent=0):
    node = NODES[node_id]
    prefix = "  " * indent
    role = "MAX (Thief)" if node["is_max"] else "MIN (Guard)"
    move_part = ("[" + node["move"] + "] ") if node["move"] else ""
    if node["pruned"]:
        print(prefix + move_part + "PRUNED (not explored)")
        return
    score_part = "score=" + str(node["score"]) if node["score"] is not None else ""
    print(prefix + move_part + role + " " + score_part)
    for child_id in node["children"]:
        print_text_tree(child_id, indent + 1)


def assign_positions():
    """Simple layout: leaves get sequential x positions left to right,
    internal nodes get the average x of their children. Depth = y."""
    positions = {}
    leaf_counter = [0]

    def layout(node_id):
        node = NODES[node_id]
        if not node["children"]:
            x = leaf_counter[0]
            leaf_counter[0] += 1
            positions[node_id] = x
            return x
        child_xs = [layout(c) for c in node["children"]]
        x = sum(child_xs) / len(child_xs)
        positions[node_id] = x
        return x

    layout(0)
    return positions


def max_depth():
    return max(NODES[0]["depth_remaining"] - n["depth_remaining"] for n in NODES)


def draw_tree(output_path, title):
    positions = assign_positions()
    top_depth = NODES[0]["depth_remaining"]

    plt.figure(figsize=(max(8, len(positions) * 0.9), 6))

    for node in NODES:
        x = positions[node["id"]]
        y = top_depth - node["depth_remaining"]
        if node["parent"] is not None:
            parent = NODES[node["parent"]]
            px = positions[parent["id"]]
            py = top_depth - parent["depth_remaining"]
            style = "--" if node["pruned"] else "-"
            color = "lightgray" if node["pruned"] else "black"
            plt.plot([px, x], [py, y], style, color=color, linewidth=1, zorder=1)

        if node["pruned"]:
            face = "whitesmoke"
            edge = "lightgray"
            label = (node["move"] or "") + "\npruned"
        else:
            face = "#cfe8ff" if node["is_max"] else "#ffd9d9"
            edge = "black"
            label = (node["move"] + "\n" if node["move"] else "") + \
                    ("score " + str(node["score"]) if node["score"] is not None else "")

        plt.scatter([x], [y], s=1600, marker="s", color=face, edgecolor=edge, zorder=2)
        plt.text(x, y, label, ha="center", va="center", fontsize=8, zorder=3)

    plt.gca().invert_yaxis()
    plt.axis("off")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print("Saved", output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="maps/working_case_1.txt")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--algo", choices=["alphabeta", "minimax"], default="alphabeta")
    parser.add_argument("--output", default="outputs/search_tree.png")
    args = parser.parse_args()

    world = load_map(args.map)
    table = build_distance_table(world)
    state = initial_state(world)

    use_pruning = args.algo == "alphabeta"
    traced_search(state, world, table, args.depth, None, None, float("-inf"), float("inf"), use_pruning)

    print()
    print("Text tree (" + args.algo + ", depth " + str(args.depth) + "):")
    print_text_tree(0)
    print()
    print("Total nodes recorded (including pruned placeholders):", len(NODES))

    title = args.algo + ", depth " + str(args.depth) + " on " + args.map
    draw_tree(args.output, title)


if __name__ == "__main__":
    main()
