from PikachuCNN import PikachuCNN

import torch
import torchvision.transforms as transforms
from PIL import Image

def load_trained_model(model_path, device):
    model = PikachuCNN(num_classes=36)

    model.load_state_dict(torch.load(model_path, map_location=device))

    model.eval()
    return model.to(device)


def predict_tile(image_path, model, device):
    transform = transforms.Compose([
        transforms.Resize((48, 48)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])


    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image)

    # add dim batch_size
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