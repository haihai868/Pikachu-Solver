import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from pikachu_solver.correct_solver import solve_backtracking

def test_simple_board_is_solved():
    # Set up a simple 4x4 grid with two matching pairs
    matrix = np.zeros((4, 4), dtype=int)
    matrix[0, 0] = 1
    matrix[0, 1] = 1
    matrix[2, 2] = 2
    matrix[3, 2] = 2
    
    success, solved_steps = solve_backtracking(matrix, timeout=5.0)
    
    assert success is True, "Failed to solve simple board!"
    assert len(solved_steps) == 2, f"Expected 2 steps, but got {len(solved_steps)}"

from pikachu_solver.correct_solver import update_board

def test_update_board_gravity_levels():
    padded = np.zeros((11, 18), dtype=int)
    # Active rows 1..9 in column 4 set to: [1, 2, 5, 3, 5, 4, 0, 0, 0]
    # Coordinates of value 5 are (3, 4) and (5, 4)
    padded[1:10, 4] = [1, 2, 5, 3, 5, 4, 0, 0, 0]
    
    # Test Level 2 (Down)
    # Match (3, 4) and (5, 4) -> remaining [1, 2, 3, 4] fall to bottom (indices 5..8 in active column)
    state = padded.copy()
    res = update_board(state, (3, 4), (5, 4), level=2)
    assert list(res[1:10, 4]) == [0, 0, 0, 0, 0, 1, 2, 3, 4]

    # Test Level 3 (Up)
    # Match (3, 4) and (5, 4) -> remaining [1, 2, 3, 4] rise to top (indices 0..3 in active column)
    state = padded.copy()
    res = update_board(state, (3, 4), (5, 4), level=3)
    assert list(res[1:10, 4]) == [1, 2, 3, 4, 0, 0, 0, 0, 0]

    print("Gravity level tests passed!")

if __name__ == "__main__":
    test_simple_board_is_solved()
    test_update_board_gravity_levels()
    print("All tests passed successfully!")
