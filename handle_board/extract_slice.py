import cv2
import numpy as np
import torch
from detect_tiles import load_trained_model, predict_tile
from typing import Tuple, List

def extract_and_slice_board(image_path, rows=9, cols=16, model_input_size=(48, 48), gap=1)-> Tuple[np.ndarray, List[np.ndarray]]:
    # load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    original_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Find small tiles to determine the main board
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    img_h, img_w, _ = img.shape
    estimated_tile_w = img_w // cols
    estimated_tile_h = img_h // rows
    estimated_tile_area = estimated_tile_w * estimated_tile_h

    min_area = estimated_tile_area * 0.1
    max_area = estimated_tile_area * 3.0

    tile_contours = []
    for c in contours:
        x_c, y_c, w_c, h_c = cv2.boundingRect(c)
        area_c = w_c * h_c
        if area_c < min_area or area_c > max_area:
            continue

        aspect_ratio = w_c / h_c if w_c > h_c else h_c / w_c
        if aspect_ratio > 1.5:
            continue

        tile_contours.append(c)

    if len(tile_contours) < 50:
        raise ValueError("Not enough tiles found to identify the board.")

    # Create bounding box for the entire board (tight fit - padding = 0)
    x_min, y_min = img_w, img_h
    x_max, y_max = 0, 0

    for c in tile_contours:
        x_c, y_c, w_c, h_c = cv2.boundingRect(c)
        if x_c < x_min: x_min = x_c
        if y_c < y_min: y_min = y_c
        if (x_c + w_c) > x_max: x_max = (x_c + w_c)
        if (y_c + h_c) > y_max: y_max = (y_c + h_c)

    # Set padding to 0 as requested
    padding = 0
    x_final = max(0, x_min - padding)
    y_final = max(0, y_min - padding)
    w_final = min(img_w - x_final, (x_max - x_min) + padding * 2)
    h_final = min(img_h - y_final, (y_max - y_min) + padding * 2)

    board_img = original_img[y_final:y_final+h_final, x_final:x_final+w_final]

    # SLICE BOARD ACCURATELY WITH GAP BETWEEN TILES
    # Calculate standard tile size (float) minus the gaps
    tile_w_float = (w_final - (cols - 1) * gap) / cols
    tile_h_float = (h_final - (rows - 1) * gap) / rows

    tiles = []

    for r in range(rows):
        for c in range(cols):
            # Start coordinates: accumulate width of previous tiles and previous gaps
            start_x = int(round(c * (tile_w_float + gap)))
            start_y = int(round(r * (tile_h_float + gap)))

            # End coordinates
            end_x = int(round(start_x + tile_w_float))
            end_y = int(round(start_y + tile_h_float))

            # Crop tile
            tile = board_img[start_y:end_y, start_x:end_x]

            if tile.shape[0] > 0 and tile.shape[1] > 0:
                tile_resized = cv2.resize(tile, model_input_size)
                tiles.append(tile_resized)
            else:
                print(f"warning: row {r}, col {c} empty, skip.")
    return board_img, tiles

def encode_board(tiles, rows=9, cols=16) -> np.ndarray:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    MODEL_PATH = 'model/pikachu_model_best.pth'
    bot_model = load_trained_model(MODEL_PATH, device)

    # Predict
    labels = []
    for tile in tile_list:
        label = predict_tile(tile, bot_model, device)
        labels.append(label)

    #reshape 9x16
    board_labels = np.array(labels).reshape((rows, cols))
    return board_labels

if __name__ == "__main__":
    try:
        IMAGE_PATH = "../board_img/image1.png"
        board, tile_list = extract_and_slice_board(IMAGE_PATH, gap=2)

        matrix = encode_board(tile_list)
        print(matrix)

        # cv2.imwrite("../cropped_board/image1.png", board)
        # if len(tile_list) >= 144:
        #     cv2.imwrite("../tile_img/image1_0.png", tile_list[0])
        #     cv2.imwrite("../tile_img/image1_19.png", tile_list[19])

    except Exception as e:
        print(f"Err: {e}")