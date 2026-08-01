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

def update_board(padded_board: np.ndarray, p1: Tuple[int, int], p2: Tuple[int, int], level: int = 1) -> np.ndarray:
    # 1. Clear the matched cells first
    padded_board[p1] = 0
    padded_board[p2] = 0
    
    if level == 1:
        return padded_board

    row1, col1 = p1
    row2, col2 = p2
    row, col = padded_board.shape

    # Column-based shifting (Level 2, 3, 6, 7)
    if level in (2, 3, 6, 7):
        columns_to_update = {col1, col2}
        for c in columns_to_update:
            if c == 0 or c == col - 1:
                continue
            # Extract active rows 1..9 (which has 9 elements)
            active_col = padded_board[1:10, c]
            vals = [v for v in active_col if v != 0]
            
            if level == 2:  # Down
                padded_board[1:10, c] = [0] * (9 - len(vals)) + vals
            elif level == 3:  # Up
                padded_board[1:10, c] = vals + [0] * (9 - len(vals))
            elif level == 6:  # Vertical Center
                # Split: top 5 cells (rows 1..5) shift down, bottom 4 cells (rows 6..9) shift up
                top_vals = [v for v in padded_board[1:6, c] if v != 0]
                padded_board[1:6, c] = [0] * (5 - len(top_vals)) + top_vals
                
                bot_vals = [v for v in padded_board[6:10, c] if v != 0]
                padded_board[6:10, c] = bot_vals + [0] * (4 - len(bot_vals))
            elif level == 7:  # Vertical Sides
                # Split: top 5 cells shift up, bottom 4 cells shift down
                top_vals = [v for v in padded_board[1:6, c] if v != 0]
                padded_board[1:6, c] = top_vals + [0] * (5 - len(top_vals))
                
                bot_vals = [v for v in padded_board[6:10, c] if v != 0]
                padded_board[6:10, c] = [0] * (4 - len(bot_vals)) + bot_vals

    # Row-based shifting (Level 4, 5, 8, 9)
    elif level in (4, 5, 8, 9):
        rows_to_update = {row1, row2}
        for r in rows_to_update:
            if r == 0 or r == row - 1:
                continue
            # Extract active cols 1..16 (which has 16 elements)
            active_row = padded_board[r, 1:17]
            vals = [v for v in active_row if v != 0]
            
            if level == 4:  # Left
                padded_board[r, 1:17] = vals + [0] * (16 - len(vals))
            elif level == 5:  # Right
                padded_board[r, 1:17] = [0] * (16 - len(vals)) + vals
            elif level == 8:  # Horizontal Center
                # Split: left 8 cells (cols 1..8) shift right, right 8 cells (cols 9..16) shift left
                left_vals = [v for v in padded_board[r, 1:9] if v != 0]
                padded_board[r, 1:9] = [0] * (8 - len(left_vals)) + left_vals
                
                right_vals = [v for v in padded_board[r, 9:17] if v != 0]
                padded_board[r, 9:17] = right_vals + [0] * (8 - len(right_vals))
            elif level == 9:  # Horizontal Sides
                # Split: left 8 cells shift left, right 8 cells shift right
                left_vals = [v for v in padded_board[r, 1:9] if v != 0]
                padded_board[r, 1:9] = left_vals + [0] * (8 - len(left_vals))
                
                right_vals = [v for v in padded_board[r, 9:17] if v != 0]
                padded_board[r, 9:17] = [0] * (8 - len(right_vals)) + right_vals

    return padded_board

def count_turns(path: List[Tuple[int, int]]) -> int:
    if len(path) <= 2:
        return 0
    turns = 0
    last_dir = None
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i+1]
        dr, dc = r2 - r1, c2 - c1
        curr_dir = (dr, dc)
        if last_dir is not None and curr_dir != last_dir:
            turns += 1
        last_dir = curr_dir
    return turns

def validate_board(grid: np.ndarray) -> Tuple[bool, str]:
    if grid.shape != (9, 16):
        return False, f"Kích thước bảng không hợp lệ: {grid.shape}. Phải là 9x16."
        
    flat = grid.flatten()
    non_zero_tiles = [v for v in flat if v != 0]
    total_tiles = len(non_zero_tiles)
    if total_tiles % 2 != 0:
        return False, f"Tổng số ô trên bảng là số lẻ ({total_tiles} ô). Không thể ghép cặp!"
        
    counts = {}
    for val in non_zero_tiles:
        counts[val] = counts.get(val, 0) + 1
        
    odd_classes = []
    for val, count in counts.items():
        if count % 2 != 0:
            odd_classes.append(f"Loại {val} ({count} ô)")
            
    if odd_classes:
        return False, "Bảng chứa số lượng ô lẻ: " + ", ".join(odd_classes) + ". Vui lòng dùng Edit Mode để sửa lại!"
        
    return True, ""

def solve_backtracking(matrix: np.ndarray, level: int = 1, timeout: float = 8.0):
    """Pads a 9x16 matrix to 11x18, solves it using backtracking,
    and returns (success, steps) with coordinates mapped back to 9x16.
    """
    is_valid, err_msg = validate_board(matrix)
    if not is_valid:
        return False, err_msg

    rows, cols = matrix.shape
    padded = np.zeros((rows + 2, cols + 2), dtype=int)
    padded[1:-1, 1:-1] = matrix
    
    start_time = time.time()
    steps = []
    
    def backtrack(curr_padded: np.ndarray) -> bool:
        if time.time() - start_time > timeout:
            return False
        if np.all(curr_padded == 0):
            return True
            
        pairs = get_all_connectable_pairs(curr_padded)
        if not pairs:
            return False
            
        # Heuristic: Prioritize pairs with fewer turns to avoid long-range blocking connections
        pairs.sort(key=lambda x: count_turns(x[3]))
            
        # Try matching pairs
        for p1, p2, val, path in pairs:
            next_padded = curr_padded.copy()
            next_padded = update_board(next_padded, p1, p2, level)
            
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
            
            if backtrack(next_padded):
                return True
                
            # Undo
            steps.pop()
            
        return False

    success = backtrack(padded)
    return success, steps
