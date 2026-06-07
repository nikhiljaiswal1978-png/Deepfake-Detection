from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import torch
import base64
import os
from torchvision import transforms

live_analysis_bp = Blueprint('live_analysis', __name__)

# Preprocessing function (adjust based on your model)
def preprocess_frame(frame):
    """Preprocess frame for EfficientNet-B4 - MUST match DeepfakeInference"""
    from PIL import Image
    
    # Convert numpy array to PIL Image
    pil_image = Image.fromarray(frame)
    
    # Same transform as DeepfakeInference
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # B4 uses 224, not 380!
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    return transform(pil_image).unsqueeze(0)

def generate_gradcam_heatmap(model, frame_tensor, target_layers):
    """Generate Grad-CAM heatmap"""
    try:
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        
        cam = GradCAM(model=model, target_layers=target_layers)
        grayscale_cam = cam(input_tensor=frame_tensor, targets=None)
        return grayscale_cam[0, :]
    except ImportError:
        # Fallback if pytorch_grad_cam not installed
        return None

@live_analysis_bp.route('/analyze-live', methods=['POST'])
def analyze_live():
    """
    Analyze video frame-by-frame with predictions and heatmaps
    """
    from flask import current_app
    
    print("\n" + "="*60)
    print("LIVE ANALYSIS REQUEST RECEIVED")
    print("="*60)
    
    try:
        if 'video' not in request.files:
            print("❌ No video file in request")
            return jsonify({'error': 'No video file provided', 'success': False}), 400
        
        video = request.files['video']
        if video.filename == '':
            print("❌ Empty filename")
            return jsonify({'error': 'Empty filename', 'success': False}), 400
        
        print(f"✓ Video received: {video.filename}")
        
        # Get model from app config
        model = current_app.config.get('MODEL')
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        print(f"✓ Model loaded: {model is not None}")
        print(f"✓ Upload folder: {upload_folder}")
        
        if model is None:
            print("❌ Model not in app.config")
            return jsonify({'error': 'Model not loaded in app config', 'success': False}), 500
        
        # Save video temporarily
        os.makedirs(upload_folder, exist_ok=True)
        video_path = os.path.join(upload_folder, video.filename)
        video.save(video_path)
        print(f"✓ Video saved to: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Could not open video")
            return jsonify({'error': 'Could not open video file', 'success': False}), 400
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"✓ Video info: {total_frames} frames @ {fps} fps")
        
        # Analyze 10 frames to match the main prediction endpoint
        frame_indices = np.linspace(0, total_frames - 1, 10, dtype=int)
        
        results = []
        model.eval()
        
        # Setup Grad-CAM if possible
        use_gradcam = False
        cam = None
        try:
            # Check if model has backbone (your custom wrapper)
            if hasattr(model, 'backbone'):
                # Your model structure: model.backbone.features[-1]
                target_layers = [model.backbone.features[-1]]
                print("✓ Using model.backbone.features[-1] for Grad-CAM")
            elif hasattr(model, 'features'):
                # Standard EfficientNet
                target_layers = [model.features[-1]]
                print("✓ Using model.features[-1] for Grad-CAM")
            else:
                # Fallback: find last conv layer
                conv_layers = [m for m in model.modules() if isinstance(m, torch.nn.Conv2d)]
                if conv_layers:
                    target_layers = [conv_layers[-1]]
                    print("✓ Using last Conv2d layer for Grad-CAM")
                else:
                    raise Exception("No conv layers found")
            
            from pytorch_grad_cam import GradCAM
            cam = GradCAM(model=model, target_layers=target_layers)
            use_gradcam = True
            print("✓ Grad-CAM initialized successfully!")
        except Exception as e:
            print(f"⚠ Grad-CAM not available: {e}")
            use_gradcam = False
        
        print(f"\nProcessing {len(frame_indices)} frames...")
        
        for frame_num, idx in enumerate(frame_indices):
            print(f"  Processing frame {frame_num+1}/{len(frame_indices)} (index {idx})...")
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if not ret:
                print(f"  ⚠ Could not read frame {idx}")
                continue
            
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_tensor = preprocess_frame(frame_rgb)
            
            # Get prediction - model already has Sigmoid in it!
            with torch.no_grad():
                output = model(frame_tensor).squeeze().item()
                prob = output  # Don't apply sigmoid again!
            
            print(f"  ✓ Prediction: {prob:.4f}")
            
            # Generate heatmap if available
            heatmap_image = None
            if use_gradcam and cam is not None:
                try:
                    from pytorch_grad_cam.utils.image import show_cam_on_image
                    
                    # Generate heatmap
                    grayscale_cam = cam(input_tensor=frame_tensor, targets=None)
                    grayscale_cam = grayscale_cam[0, :]
                    
                    # IMPORTANT: Enhance the heatmap contrast
                    # Normalize to 0-1 range more aggressively
                    cam_min = grayscale_cam.min()
                    cam_max = grayscale_cam.max()
                    if cam_max > cam_min:
                        grayscale_cam = (grayscale_cam - cam_min) / (cam_max - cam_min)
                    
                    # Apply power transform to make colors more vivid
                    grayscale_cam = np.power(grayscale_cam, 0.7)  # Increase contrast
                    
                    # Resize frame to match and normalize (224x224 for B4)
                    frame_for_overlay = cv2.resize(frame_rgb, (224, 224))
                    frame_normalized = frame_for_overlay.astype(np.float32) / 255.0
                    
                    # Create heatmap overlay with higher opacity
                    visualization = show_cam_on_image(frame_normalized, grayscale_cam, use_rgb=True, image_weight=0.5)
                    
                    # Encode heatmap with reduced quality
                    vis_resized = cv2.resize(visualization, (480, 270))
                    _, heatmap_buffer = cv2.imencode('.jpg', cv2.cvtColor(vis_resized, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 70])
                    heatmap_base64 = base64.b64encode(heatmap_buffer).decode('utf-8')
                    heatmap_image = f'data:image/jpeg;base64,{heatmap_base64}'
                    print(f"  ✓ Heatmap generated (min: {cam_min:.3f}, max: {cam_max:.3f})")
                    
                except Exception as e:
                    print(f"  ⚠ Grad-CAM generation failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Encode original frame (reduce quality to save bandwidth)
            frame_resized = cv2.resize(frame, (480, 270))  # Smaller size
            _, frame_buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_base64 = base64.b64encode(frame_buffer).decode('utf-8')
            
            results.append({
                'frame_number': int(idx),
                'timestamp': float(idx / fps),
                'fake_probability': float(prob),
                'prediction': 'FAKE' if prob > 0.5 else 'REAL',
                'confidence': float(abs(prob - 0.5) * 2),  # 0 to 1 scale
                'frame_image': f'data:image/jpeg;base64,{frame_base64}',
                'heatmap_image': heatmap_image
            })
        
        cap.release()
        print(f"\n✓ Analysis complete! Processed {len(results)} frames")
        
        # Calculate overall prediction
        avg_prob = sum(r['fake_probability'] for r in results) / len(results) if results else 0
        
        response_data = {
            'success': True,
            'total_frames': total_frames,
            'fps': float(fps),
            'duration': float(total_frames / fps),
            'frames_analyzed': len(results),
            'frame_predictions': results,
            'overall_prediction': 'FAKE' if avg_prob > 0.5 else 'REAL',
            'overall_confidence': float(abs(avg_prob - 0.5) * 2)
        }
        
        # Cleanup - Make sure cap is fully released before deleting
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"✓ Cleaned up: {video_path}")
        except PermissionError:
            print(f"⚠ Could not delete {video_path}, file still in use")
        
        print("="*60)
        print("RETURNING RESPONSE")
        print("="*60 + "\n")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\n❌ ERROR in analyze_live: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to cleanup on error
        try:
            if 'cap' in locals():
                cap.release()
            if 'video_path' in locals() and os.path.exists(video_path):
                os.remove(video_path)
        except:
            pass
        
        return jsonify({'error': str(e), 'success': False}), 500

