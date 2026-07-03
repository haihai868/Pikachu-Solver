from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .pathfinding import can_connect


def apply_gravity(matrix: np.ndarray, direction: str = "down") -> np.ndarray:
    matrix = np.array(matrix, copy=True)
    if direction == "down":
        for c in range(matrix.shape[1]):
            column = matrix[:, c]
            non_zero = column[column != 0]
            if len(non_zero) == 0:
                continue
            if len(non_zero) < len(column):
                column[:] = 0
                column[-len(non_zero):] = non_zero
                matrix[:, c] = column
    elif direction == "up":
        for c in range(matrix.shape[1]):
            column = matrix[:, c]
            non_zero = column[column != 0]
            if len(non_zero) == 0:
                continue
            if len(non_zero) < len(column):
                column[:] = 0
                column[: len(non_zero)] = non_zero
                matrix[:, c] = column
    elif direction == "left":
        for r in range(matrix.shape[0]):
            row = matrix[r, :]
            non_zero = row[row != 0]
            if len(non_zero) == 0:
                continue
            if len(non_zero) < len(row):
                row[:] = 0
                row[: len(non_zero)] = non_zero
                matrix[r, :] = row
    elif direction == "right":
        for r in range(matrix.shape[0]):
            row = matrix[r, :]
            non_zero = row[row != 0]
            if len(non_zero) == 0:
                continue
            if len(non_zero) < len(row):
                row[:] = 0
                row[-len(non_zero):] = non_zero
                matrix[r, :] = row
    return matrix


def solve(matrix: np.ndarray, apply_gravity_rule: bool = False) -> List[dict]:
    state = np.array(matrix, copy=True)
    steps: List[dict] = []
    while np.any(state != 0):
        found = False
        for r in range(1, state.shape[0] - 1):
            for c in range(1, state.shape[1] - 1):
                if state[r, c] == 0:
                    continue
                for rr in range(1, state.shape[0] - 1):
                    for cc in range(1, state.shape[1] - 1):
                        if rr == r and cc == c:
                            continue
                        if state[rr, cc] != state[r, c]:
                            continue
                        ok, path = can_connect(state, (r, c), (rr, cc))
                        if ok:
                            steps.append({"start": (r, c), "end": (rr, cc), "value": int(state[r, c]), "path": path})
                            state[r, c] = 0
                            state[rr, cc] = 0
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if not found:
            break
        if apply_gravity_rule:
            state = apply_gravity(state)
    return steps
