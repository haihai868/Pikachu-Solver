# Pikachu Solver

This project detects a Classic Pikachu board in an image, extracts the tile layout, finds matching pairs with a pathfinding check, and saves a visualization of the solved moves.

## Quick start

```bash
python main.py path/to/board.png --rows 9 --cols 16 --output-dir output
```

## Notes

- The board detector is intentionally lightweight and may need a clearer screenshot for best results.
- The solver uses a path search that allows direct, L-shaped, and U/Z-shaped routes with up to two turns.
- Use the optional `--gravity` flag if your board version shifts tiles after matches.
