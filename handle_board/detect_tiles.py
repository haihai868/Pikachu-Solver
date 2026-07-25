from handle_board.PikachuCNN import PikachuCNN
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

def load_trained_model(model_path, device):
    model = PikachuCNN(num_classes=36)

    model.load_state_dict(torch.load(model_path, map_location=device))

    model.eval()
    return model.to(device)


VAL_TRANSFORMS = transforms.Compose([
    transforms.ToPILImage(), # Chuyển đổi np.ndarray thành PIL Image
    transforms.Resize((48, 48)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

def predict_tile(image: np.ndarray, model, device) -> int:
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    model.eval() 
    image_tensor = VAL_TRANSFORMS(image)

    image_tensor = image_tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        _, predicted_class = torch.max(outputs, 1)

    return predicted_class.item()

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    MODEL_PATH = 'model/pikachu_model_best.pth'
    bot_model = load_trained_model(MODEL_PATH, device)


    TEST_IMAGE_PATH = 'image1_0.png'
    predicted_label = predict_tile(TEST_IMAGE_PATH, bot_model, device)
    print(f"Class ID: {predicted_label}")