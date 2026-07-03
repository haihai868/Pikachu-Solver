from __future__ import annotations

from collections import deque
from typing import List, Tuple

import numpy as np


Point = Tuple[int, int]


def can_connect(matrix: np.ndarray, point1: Point, point2: Point) -> Tuple[bool, List[Point]]:
    """Return True and a path if two matching tiles can be connected with up to three segments."""
    if matrix.shape[0] < 3 or matrix.shape[1] < 3:
        return False, []

    h, w = matrix.shape
    if not (0 <= point1[0] < h and 0 <= point1[1] < w and 0 <= point2[0] < h and 0 <= point2[1] < w):
        return False, []

    if point1 == point2:
        return False, []

    if matrix[point1] != matrix[point2] or matrix[point1] == 0 or matrix[point2] == 0:
        return False, []

    start = point1
    target = point2
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    q = deque([(start[0], start[1], None, 0, [start])])
    visited = {(start[0], start[1], None, 0)}

    while q:
        r, c, last_dir, turns, path = q.popleft()
        if (r, c) == target:
            return True, path
        if turns >= 2:
            continue

        for direction_idx, (dr, dc) in enumerate(directions):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if matrix[nr, nc] != 0 and (nr, nc) != target:
                continue
            if (nr, nc) in path:
                continue

            if last_dir is None:
                next_turns = 0
            elif direction_idx == last_dir:
                next_turns = turns
            else:
                next_turns = turns + 1
                if next_turns > 2:
                    continue

            next_dir = direction_idx
            state = (nr, nc, next_dir, next_turns)
            if state in visited:
                continue
            visited.add(state)
            q.append((nr, nc, next_dir, next_turns, path + [(nr, nc)]))

    return False, []
