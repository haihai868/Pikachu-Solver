from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from pikachu_solver.solver import solve
from pikachu_solver.vision import BoardPerceiver


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


    matrix = np.array([
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [ 0,  1,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10,  2,  2, 11, 12, 13,  0],
        [ 0,  1, 14, 15, 16, 17, 12,  7, 11, 11, 18, 14, 19, 20,  5,  9, 11,  0],
        [ 0, 19, 21, 22,  8,  9, 16, 16,  6, 11, 20, 12,  4, 23, 23, 24, 25,  0],
        [ 0, 26, 27, 25, 11, 11, 17, 27, 14, 12, 28, 12, 10, 29, 30, 31,  9,  0],
        [ 0, 32, 30, 30, 32, 33, 21, 17, 24, 31,  3, 31, 30, 28, 34, 10, 12,  0],
        [ 0, 33, 18, 21, 26,  7,  8, 27, 22, 17,  4, 18, 35, 22, 12, 11, 19,  0],
        [ 0, 15,  5, 20, 28, 13, 27,  6, 25, 24,  7,  4, 25, 14, 34, 19, 36,  0],
        [ 0, 31,  3, 13, 15, 12,  6,  2, 34,  5, 20, 29, 10, 22, 36, 26, 33,  0],
        [ 0, 24, 23, 21, 15, 26, 34, 23, 36, 28,  8, 18,  3, 34, 36, 33, 13,  0],
        [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
    ])
    steps = solve(matrix)
    print(f"Found {len(steps)} steps")
    for step in steps:
        print(step)

    # output_image = output_dir / "solved_board.png"
    # perceiver.visualize_steps(args.image, steps, output_image)
    # print(f"Saved visualization to {output_image}")


if __name__ == "__main__":
    main()
