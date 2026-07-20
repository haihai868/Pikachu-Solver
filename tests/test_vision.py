from pikachu_solver.vision import BoardPerceiver

perceiver = BoardPerceiver("img/image.png", 9, 16)

detected_board = perceiver.detect_board()
extracted_matrix = perceiver.extract_board_matrix(detection=detected_board)

print(extracted_matrix)
