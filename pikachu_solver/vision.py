from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np


@dataclass
class BoardDetection:
    image: np.ndarray
    board_bbox: Tuple[int, int, int, int]
    cell_size: int
    rows: int
    cols: int


class BoardPerceiver:
    def __init__(self, image_path: str | Path, rows: int = 9, cols: int = 16) -> None:
        self.image_path = Path(image_path)
        self.rows = rows
        self.cols = cols
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise FileNotFoundError(f"Unable to read image: {self.image_path}")

    # @staticmethod
    # def _tile_signature(crop: np.ndarray) -> str:
    #     gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    #     gray = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
    #     average = gray.mean()
    #     return "".join("1" if pixel >= average else "0" for pixel in gray.flatten())

    @staticmethod
    def _tile_similarity(img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Return similarity in range [-1, 1].
        """

        # grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # trim edges 10%
        h, w = gray1.shape

        margin_h = int(h * 0.1)
        margin_w = int(w * 0.1)

        gray1 = gray1[
            margin_h:h-margin_h,
            margin_w:w-margin_w
        ]

        gray2 = gray2[
            margin_h:h-margin_h,
            margin_w:w-margin_w
        ]

        # Resize
        gray1 = cv2.resize(gray1, (64, 64))
        gray2 = cv2.resize(gray2, (64, 64))

        # Blur to avoid noise
        gray1 = cv2.GaussianBlur(gray1, (3,3), 0)
        gray2 = cv2.GaussianBlur(gray2, (3,3), 0)

        score = cv2.matchTemplate(
            gray1,
            gray2,
            cv2.TM_CCOEFF_NORMED
        )[0][0]

        return float(score)

    def detect_board(self) -> BoardDetection:
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise ValueError("No board contour detected. Try a clearer screenshot.")

        biggest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(biggest)
        if w < 50 or h < 50:
            raise ValueError("Detected board area is too small.")

        board_bbox = (x, y, x + w, y + h)
        cell_size = min(w // self.cols, h // self.rows)
        if cell_size <= 0:
            raise ValueError("Unable to infer a valid grid size from the detected board.")

        return BoardDetection(
            image=self.image,
            board_bbox=board_bbox,
            cell_size=cell_size,
            rows=self.rows,
            cols=self.cols,
        )

    # def extract_board_matrix(self, detection: BoardDetection) -> np.ndarray:
    #     img = detection.image
    #     x1, y1, x2, y2 = detection.board_bbox
    #     board = img[y1:y2, x1:x2]
    #     h, w = board.shape[:2]
    #     cell_h = h // detection.rows
    #     cell_w = w // detection.cols

    #     matrix = np.zeros((detection.rows + 2, detection.cols + 2), dtype=int)
    #     signatures: dict[str, int] = {}
    #     next_id = 1
    #     for r in range(detection.rows):
    #         for c in range(detection.cols):
    #             crop = board[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
    #             if crop.size == 0:
    #                 continue
    #             gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    #             if gray.mean() > 220 and gray.std() < 25:
    #                 matrix[r + 1, c + 1] = 0
    #                 continue
    #             signature = self._tile_signature(crop)
    #             if signature not in signatures:
    #                 signatures[signature] = next_id
    #                 next_id += 1
    #             matrix[r + 1, c + 1] = signatures[signature]
    #     return matrix

    def extract_board_matrix(self, detection: BoardDetection) -> np.ndarray:

        img = detection.image

        x1, y1, x2, y2 = detection.board_bbox

        board = img[y1:y2, x1:x2]

        h, w = board.shape[:2]

        cell_h = h // detection.rows
        cell_w = w // detection.cols

        matrix = np.zeros(
            (detection.rows + 2, detection.cols + 2),
            dtype=int
        )

        known_tiles = []

        next_id = 1

        for r in range(detection.rows):

            for c in range(detection.cols):

                crop = board[
                    r*cell_h:(r+1)*cell_h,
                    c*cell_w:(c+1)*cell_w
                ]

                if crop.size == 0:
                    continue

                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

                if gray.mean() > 220 and gray.std() < 25:
                    matrix[r+1, c+1] = 0
                    continue

                matched = False

                for tile in known_tiles:
                    score = self._tile_similarity(
                        crop,
                        tile["image"]
                    )

                    if score > 0.45:
                        matrix[r+1, c+1] = tile["id"]
                        matched = True
                        break

                if not matched:
                    known_tiles.append({
                        "image": crop.copy(),
                        "id": next_id
                    })
                    matrix[r+1, c+1] = next_id
                    next_id += 1

        return matrix

    def visualize_steps(self, image_path: str | Path, steps: List[dict], output_path: str | Path) -> None:
        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Unable to read image: {image_path}")
        detection = self.detect_board()
        x1, y1, x2, y2 = detection.board_bbox
        cell_h = (y2 - y1) // detection.rows
        cell_w = (x2 - x1) // detection.cols

        for step in steps:
            start = step["start"]
            end = step["end"]
            start_pt = (
                x1 + (start[1] - 1) * cell_w + cell_w // 2,
                y1 + (start[0] - 1) * cell_h + cell_h // 2,
            )
            end_pt = (
                x1 + (end[1] - 1) * cell_w + cell_w // 2,
                y1 + (end[0] - 1) * cell_h + cell_h // 2,
            )
            cv2.line(image, start_pt, end_pt, (0, 255, 0), 2)
            cv2.circle(image, start_pt, 3, (0, 0, 255), -1)
            cv2.circle(image, end_pt, 3, (255, 0, 0), -1)

        cv2.imwrite(str(output_path), image)
