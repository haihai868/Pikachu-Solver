from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from pikachu_solver.solver import solve
from handle_board.extract_slice import extract_and_slice_board, encode_board


def main() -> None:
    # parser = argparse.ArgumentParser(description="Solve a Classic Pikachu board from an image")
    # parser.add_argument("image", type=str, help="Path to an input image")
    # parser.add_argument("--rows", type=int, default=9)
    # parser.add_argument("--cols", type=int, default=16)
    # parser.add_argument("--output-dir", type=str, default="output")
    # parser.add_argument("--gravity", action="store_true", help="Apply gravity after each match")
    # args = parser.parse_args()

    # output_dir = Path(args.output_dir)
    # output_dir.mkdir(exist_ok=True)

    # perceiver = BoardPerceiver(args.image, rows=args.rows, cols=args.cols)
    # try:
    #     detection = perceiver.detect_board()
    # except ValueError as exc:
    #     print(f"Board detection failed: {exc}")
    #     return

    # matrix = perceiver.extract_board_matrix(detection)
    # print("Detected board matrix:")
    # print(matrix)

    
    
    IMAGE_PATH = "../board_img/image1.png"
    board, tile_list = extract_and_slice_board(IMAGE_PATH, gap=2)
    matrix = encode_board(tile_list)


    steps = solve(matrix)
    print(f"Found {len(steps)} steps")
    for step in steps:
        print(step)

    # output_image = output_dir / "solved_board.png"
    # perceiver.visualize_steps(args.image, steps, output_image)
    # print(f"Saved visualization to {output_image}")


if __name__ == "__main__":
    main()
