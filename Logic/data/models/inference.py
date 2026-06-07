import torch
import cv2
import numpy as np
from torchvision import transforms
from PIL import Image
import torch.nn as nn
import torchvision.models as models
from torchvision.models import EfficientNet_B4_Weights

class DeepfakeDetector(nn.Module):
    """Deepfake detection model using EfficientNet-B4"""
    
    def __init__(self, pretrained=True):
        super(DeepfakeDetector, self).__init__()
        
        if pretrained:
            weights = EfficientNet_B4_Weights.DEFAULT
            self.backbone = models.efficientnet_b4(weights=weights)
        else:
            self.backbone = models.efficientnet_b4(weights=None)
        
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Linear(512, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.backbone(x)


class DeepfakeInference:
    """Inference class for deepfake detection"""
    
    def __init__(self, model_path, device='cpu'):
        self.device = torch.device(device)
        
        # Load model
        self.model = DeepfakeDetector(pretrained=False)
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Define transform
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def predict_video(self, video_path, num_frames=10):
        """
        Predict if a video is fake
        
        Returns:
            dict with prediction, confidence, and frame-level results
        """
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            return {"error": "Could not read video"}
        
        # Sample frames evenly
        frame_indices = np.linspace(0, total_frames - 1, min(num_frames, total_frames), dtype=int)
        
        predictions = []
        confidences = []
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Transform and predict
            image_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                output = self.model(image_tensor).squeeze().item()
            
            predictions.append(output)
            confidences.append(output)
        
        cap.release()
        
        # Aggregate predictions
        avg_score = np.mean(predictions)
        final_prediction = "FAKE" if avg_score > 0.5 else "REAL"
        confidence = avg_score if avg_score > 0.5 else 1 - avg_score
        return {
            "prediction": final_prediction,
            "confidence": float(confidence),
            "raw_score": float(avg_score),
            "frames_analyzed": len(predictions),
            "frame_scores": [float(p) for p in predictions]
        }