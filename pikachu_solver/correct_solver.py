import numpy as np
import time
from typing import List, Tuple

def is_clear_line(matrix: np.ndarray, p1: Tuple[int, int], p2: Tuple[int, int]) -> bool:
    """Check if the line between p1 and p2 (exclusive) is entirely empty (0)."""
    r1, c1 = p1
    r2, c2 = p2
    if r1 == r2:
        step = 1 if c2 > c1 else -1
        for c in range(c1 + step, c2, step):
            if matrix[r1, c] != 0:
                return False
        return True
    elif c1 == c2:
        step = 1 if r2 > r1 else -1
        for r in range(r1 + step, r2, step):
            if matrix[r, c1] != 0:
                return False
        return True
    return False

def can_connect_correct(matrix: np.ndarray, p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[bool, List[Tuple[int, int]]]:
    """Check if two matching tiles can connect with at most 2 turns.
    Returns (True, path) or (False, []).
    """
    if matrix[p1] != matrix[p2] or matrix[p1] == 0 or matrix[p2] == 0:
        return False, []
    if p1 == p2:
        return False, []
        
    r1, c1 = p1
    r2, c2 = p2
    
    # 0 turns (straight line)
    if r1 == r2 or c1 == c2:
        if is_clear_line(matrix, p1, p2):
            path = []
            if r1 == r2:
                step = 1 if c2 > c1 else -1
                for c in range(c1, c2 + step, step):
                    path.append((r1, c))
            else:
                step = 1 if r2 > r1 else -1
                for r in range(r1, r2 + step, step):
                    path.append((r, c1))
            return True, path
            
    # 1 turn (L-shape)
    corner1 = (r1, c2)
    if matrix[corner1] == 0:
        if is_clear_line(matrix, p1, corner1) and is_clear_line(matrix, corner1, p2):
            path = []
            step_c = 1 if c2 > c1 else -1
            for c in range(c1, c2, step_c):
                path.append((r1, c))
            step_r = 1 if r2 > r1 else -1
            for r in range(r1, r2 + step_r, step_r):
                path.append((r, c2))
            return True, path
            
    corner2 = (r2, c1)
    if matrix[corner2] == 0:
        if is_clear_line(matrix, p1, corner2) and is_clear_line(matrix, corner2, p2):
            path = []
            step_r = 1 if r2 > r1 else -1
            for r in range(r1, r2, step_r):
                path.append((r, c1))
            step_c = 1 if c2 > c1 else -1
            for c in range(c1, c2 + step_c, step_c):
                path.append((r2, c))
            return True, path

    # 2 turns (Z-shape or U-shape)
    h, w = matrix.shape
    # Horizontal projection from p1
    for col in range(w):
        C1 = (r1, col)
        if col == c1:
            continue
        if matrix[C1] != 0:
            continue
        if not is_clear_line(matrix, p1, C1):
            continue
            
        C2 = (r2, col)
        if matrix[C2] != 0:
            continue
        if not is_clear_line(matrix, C1, C2):
            continue
        if not is_clear_line(matrix, C2, p2):
            continue
            
        path = []
        step_c1 = 1 if col > c1 else -1
        for c in range(c1, col, step_c1):
            path.append((r1, c))
        step_r = 1 if r2 > r1 else -1
        for r in range(r1, r2, step_r):
            path.append((r, col))
        step_c2 = 1 if c2 > col else -1
        for c in range(col, c2 + step_c2, step_c2):
            path.append((r2, c))
        return True, path
        
    # Vertical projection from p1
    for row in range(h):
        C1 = (row, c1)
        if row == r1:
            continue
        if matrix[C1] != 0:
            continue
        if not is_clear_line(matrix, p1, C1):
            continue
            
        C2 = (row, c2)
        if matrix[C2] != 0:
            continue
        if not is_clear_line(matrix, C1, C2):
            continue
        if not is_clear_line(matrix, C2, p2):
            continue
            
        path = []
        step_r1 = 1 if row > r1 else -1
        for r in range(r1, row, step_r1):
            path.append((r, c1))
        step_c = 1 if c2 > c1 else -1
        for c in range(c1, c2, step_c):
            path.append((row, c))
        step_r2 = 1 if r2 > row else -1
        for r in range(row, r2 + step_r2, step_r2):
            path.append((r, c2))
        return True, path

    return False, []

def get_all_connectable_pairs(state: np.ndarray):
    """Find all matchable pairs in the current board state."""
    pairs = []
    h, w = state.shape
    val_coords = {}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            val = state[r, c]
            if val != 0:
                if val not in val_coords:
                    val_coords[val] = []
                val_coords[val].append((r, c))
                
    for val, coords in val_coords.items():
        n = len(coords)
        for i in range(n):
            for j in range(i + 1, n):
                p1 = coords[i]
                p2 = coords[j]
                ok, path = can_connect_correct(state, p1, p2)
                if ok:
                    pairs.append((p1, p2, val, path))
    return pairs

def update_board(padded_board, p1: Tuple[int, int], p2: Tuple[int, int], level: int=1):
    row, col = padded_board.shape
    row1, col1 = p1
    row2, col2 = p2
    

    # remember to check edge cases
    if level == 1:
        padded_board[p1] = 0
        padded_board[p2] = 0
    elif level == 2:
        above1 = padded_board[row1 + 1:, col1]
        padded_board[row1:row - 1, col1] = above1

        above2 = padded_board[row2 + 1:, col2]
        padded_board[row2:row - 1, col2] = above2

    elif level == 3:
        under1 = padded_board[:row1, col1]
        padded_board[1:row1+1, col1] = under1

        under2 = padded_board[:row2, col2]
        padded_board[1:row2+1, col2] = under2

    elif level == 4:
        right1 = padded_board[row1, col1 + 1:]
        padded_board[row1, col1:col - 1] = right1

        right2 = padded_board[row2, col2 + 1:]
        padded_board[row2, col2:col - 1] = right2

    elif level == 5:
        left1 = padded_board[row1, :col1]
        padded_board[row1, 1:col1+1] = left1

        left2 = padded_board[row2, :col2]
        padded_board[row2, 1:col2+1] = left2

    elif level == 6:
        pass
    elif level == 7:
        pass
    elif level == 8:
        pass
    elif level == 9:
        pass
    elif level == 10:
        pass
    
    return padded_board

def solve_backtracking(matrix: np.ndarray, timeout: float = 8.0, level: int = 1):
    """Pads a 9x16 matrix to 11x18, solves it using backtracking,
    and returns (success, steps) with coordinates mapped back to 9x16.
    """
    rows, cols = matrix.shape
    padded = np.zeros((rows + 2, cols + 2), dtype=int)
    padded[1:-1, 1:-1] = matrix
    
    start_time = time.time()
    steps = []
    
    def backtrack():
        if time.time() - start_time > timeout:
            return False
        if np.all(padded == 0):
            return True
            
        pairs = get_all_connectable_pairs(padded)
        if not pairs:
            return False
            
        # Try matching pairs
        for p1, p2, val, path in pairs:
            old_padded = padded.copy()

            # update board base on level
            padded = update_board(padded, p1, p2, level)
            
            # Map path back to 9x16 space (subtract 1 from all row & col coordinates)
            mapped_path = [(r - 1, c - 1) for r, c in path]
            mapped_start = (p1[0] - 1, p1[1] - 1)
            mapped_end = (p2[0] - 1, p2[1] - 1)
            
            steps.append({
                "start": mapped_start,
                "end": mapped_end,
                "value": int(val),
                "path": mapped_path
            })
            
            if backtrack():
                return True
                
            # Undo
            padded = old_padded
            steps.pop()
            
        return False

    success = backtrack()
    return success, steps
