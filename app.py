import os
import base64
import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

# Add project modules
from handle_board.extract_slice import extract_and_slice_board
from handle_board.detect_tiles import load_trained_model, predict_tile
from pikachu_solver.correct_solver import solve_backtracking

app = FastAPI(title="Pikachu Board Solver API")

# Ensure directories exist
os.makedirs("temp_uploads", exist_ok=True)

# Load CNN model once at startup
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = 'model/pikachu_model_best.pth'

print(f"Loading Pikachu CNN model on {DEVICE}...")
try:
    BOT_MODEL = load_trained_model(MODEL_PATH, DEVICE)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    BOT_MODEL = None

class SolveGridRequest(BaseModel):
    grid: List[List[int]]  # 9x16 grid with values 0 (empty) or 1..36 (tile types)

@app.post("/api/solve")
async def solve_board_image(file: UploadFile = File(...)):
    if not BOT_MODEL:
        raise HTTPException(status_code=500, detail="CNN Model is not loaded on server.")
        
    # Save the file temporarily
    file_path = os.path.join("temp_uploads", file.filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # Extract and slice board
        # Use gap=2 as per main.py default
        try:
            board_img, tile_list = extract_and_slice_board(file_path, gap=2)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract board from image: {str(e)}")
            
        # Predict labels for all tiles
        labels = []
        for tile in tile_list:
            label = predict_tile(tile, BOT_MODEL, DEVICE)
            labels.append(label)
            
        # Convert predicted class (0..35) to 1-indexed (1..36)
        # Reshape to 9x16 grid
        grid_labels = (np.array(labels) + 1).reshape((9, 16)).tolist()
        
        # Count frequencies
        frequencies = {}
        for row in grid_labels:
            for val in row:
                if val != 0:
                    frequencies[val] = frequencies.get(val, 0) + 1
                    
        # Check if frequencies are valid (each present class must have a count of 4, or at least even)
        warnings = []
        for k, v in frequencies.items():
            if v % 2 != 0:
                warnings.append(f"Tile {k} has odd count ({v}).")
            elif v != 4:
                warnings.append(f"Tile {k} has count {v} instead of 4.")
                
        # Try to solve the grid
        grid_np = np.array(grid_labels)
        solve_success, steps = solve_backtracking(grid_np)
        
        # Convert board_img to Base64 (convert RGB to BGR first for OpenCV)
        board_bgr = cv2.cvtColor(board_img, cv2.COLOR_RGB2BGR)
        _, buffer_img = cv2.imencode(".png", board_bgr)
        board_base64 = base64.b64encode(buffer_img).decode("utf-8")
        
        warning_msg = " ".join(warnings) if warnings else None
        
        return {
            "success": solve_success,
            "grid": grid_labels,
            "steps": steps,
            "board_img": board_base64,
            "error": warning_msg
        }
        
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

@app.post("/api/solve_grid")
async def solve_grid_only(req: SolveGridRequest):
    grid_np = np.array(req.grid)
    if grid_np.shape != (9, 16):
        raise HTTPException(status_code=400, detail="Grid shape must be 9x16.")
        
    solve_success, steps = solve_backtracking(grid_np)
    
    # Count frequencies for warnings
    frequencies = {}
    for val in req.grid:
        for v in val:
            if v != 0:
                frequencies[v] = frequencies.get(v, 0) + 1
                
    warnings = []
    for k, v in frequencies.items():
        if v % 2 != 0:
            warnings.append(f"Tile {k} has odd count ({v}).")
            
    warning_msg = " ".join(warnings) if warnings else None
    
    return {
        "success": solve_success,
        "steps": steps,
        "error": warning_msg
    }

# Serve static files for frontend
# Check if static directory exists, if not create it
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
