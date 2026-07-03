import numpy as np

from pikachu_solver.pathfinding import can_connect
from pikachu_solver.solver import apply_gravity, solve


def test_can_connect_with_l_shape_path():
    matrix = np.zeros((6, 6), dtype=int)
    matrix[1, 1] = 1
    matrix[3, 3] = 1

    ok, path = can_connect(matrix, (1, 1), (3, 3))

    assert ok is True
    assert path[0] == (1, 1)
    assert path[-1] == (3, 3)
    assert len(path) >= 3


def test_solver_removes_pairs_and_supports_gravity():
    matrix = np.zeros((6, 6), dtype=int)
    matrix[1, 1] = 1
    matrix[1, 2] = 1
    matrix[3, 3] = 2
    matrix[3, 4] = 2

    steps = solve(matrix)

    assert len(steps) == 2
    assert steps[0]["value"] == 1
    assert steps[1]["value"] == 2


def test_apply_gravity_squeezes_tiles_downward():
    matrix = np.zeros((5, 5), dtype=int)
    matrix[1, 1] = 3
    matrix[3, 1] = 4

    collapsed = apply_gravity(matrix, direction="down")

    assert collapsed[3, 1] == 3
    assert collapsed[4, 1] == 4
