import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from pikachu_solver.correct_solver import solve_backtracking

def test_reconstructed_board_is_solved():
    # Read steps from solution.txt to reconstruct the 9x16 board matrix
    # solution.txt coordinates are padded (1..9, 1..16)
    solution_path = Path(__file__).parent.parent / "solution.txt"
    assert solution_path.exists(), "solution.txt not found!"
    
    steps = []
    with open(solution_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            steps.append(eval(line))
            
    # The active area of Pikachu board is 9x16
    matrix = np.zeros((9, 16), dtype=int)
    for s in steps:
        r1, c1 = s['start']
        r2, c2 = s['end']
        val = s['value']
        
        # Map padded coordinates back to 9x16 active cells
        matrix[r1 - 1, c1 - 1] = val
        matrix[r2 - 1, c2 - 1] = val
        
    # Solve using backtracking
    success, solved_steps = solve_backtracking(matrix, timeout=5.0)
    
    assert success is True, "Failed to solve the board!"
    assert len(solved_steps) == len(steps), f"Expected {len(steps)} steps, but got {len(solved_steps)}"

if __name__ == "__main__":
    test_reconstructed_board_is_solved()
    print("Test passed successfully!")
