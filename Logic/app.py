from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import sys
import logging
from datetime import datetime
import cv2
from live_analysis import live_analysis_bp
from data.models.inference import DeepfakeInference
import json
import subprocess

# Add models directory to path
sys.path.append('models')

# Load model once when app starts
MODEL_PATH = 'data/models/ff_efficientnet_b4_FINAL.pth'
detector = DeepfakeInference(MODEL_PATH, device='cpu')
print("✓ Model loaded successfully!")
logging.info("API started - Model loaded successfully")

# Flask app with React build folder
app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['DETECTOR'] = detector
app.config['MODEL'] = detector.model
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Register live analysis blueprint
app.register_blueprint(live_analysis_bp)

# Setup logging
logging.basicConfig(
    filename='api_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force = True
)

# Statistics tracking
prediction_stats = {
    "total_predictions": 0,
    "real_count": 0,
    "fake_count": 0,
    "total_videos_analyzed": 0,
    "average_confidence": 0.0,
    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_stats(prediction, confidence):
    """Update prediction statistics"""
    prediction_stats["total_predictions"] += 1
    prediction_stats["total_videos_analyzed"] += 1
    
    if prediction == "REAL":
        prediction_stats["real_count"] += 1
    else:
        prediction_stats["fake_count"] += 1
    
    # Update average confidence
    total = prediction_stats["total_predictions"]
    current_avg = prediction_stats["average_confidence"]
    prediction_stats["average_confidence"] = ((current_avg * (total - 1)) + confidence) / total


# ============================================================================
# REACT FRONTEND ROUTES
# ============================================================================

@app.route('/')
def serve_react():
    """Serve React app"""
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    """Let React handle all non-API routes"""
    # If it's an API call, return 404 JSON
    if request.path.startswith('/predict') or request.path.startswith('/analyze') or \
       request.path.startswith('/api') or request.path.startswith('/health') or \
       request.path.startswith('/model-info') or request.path.startswith('/stats') or \
       request.path.startswith('/logs') or request.path.startswith('/video-info'):
        return jsonify({'error': 'Not found'}), 404
    # Otherwise serve React (for client-side routing)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/serve-video/<filename>')
def serve_video(filename):
    """Serve uploaded video with range request support"""
    upload_folder = app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    file_size = os.path.getsize(filepath)
    range_header = request.headers.get('Range', None)

    if range_header:
        match = range_header.replace('bytes=', '').split('-')
        byte_start = int(match[0])
        byte_end = int(match[1]) if match[1] else file_size - 1
        length = byte_end - byte_start + 1

        with open(filepath, 'rb') as f:
            f.seek(byte_start)
            data = f.read(length)

        return Response(data, 206, headers={
            'Content-Range': f'bytes {byte_start}-{byte_end}/{file_size}',
            'Accept-Ranges': 'bytes',
            'Content-Length': length,
            'Content-Type': 'video/mp4',
        })

    with open(filepath, 'rb') as f:
        data = f.read()

    return Response(data, 200, headers={
        'Accept-Ranges': 'bytes',
        'Content-Length': file_size,
        'Content-Type': 'video/mp4',
    })


# ============================================================================
# API ROUTES (BACKEND)
# ============================================================================

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        "message": "Deepfake Detection API",
        "version": "1.0",
        "model": "EfficientNet-B4",
        "endpoints": {
            "/": "GET - React web interface",
            "/api": "GET - API information",
            "/health": "GET - Check API health",
            "/predict": "POST - Upload single video for detection",
            "/predict-batch": "POST - Upload multiple videos",
            "/predict-custom": "POST - Predict with custom parameters",
            "/video-info": "POST - Get video metadata",
            "/model-info": "GET - Get model information",
            "/stats": "GET - Get API usage statistics",
            "/logs": "GET - View recent logs",
            "/analyze-live": "POST - Frame-by-frame analysis with heatmaps"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "model_loaded": True,
        "uptime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Standard prediction endpoint"""
    if 'video' not in request.files:
        logging.warning("Prediction failed - No video file provided")
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        logging.warning("Prediction failed - No file selected")
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        logging.warning(f"Prediction failed - Invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file type. Allowed: mp4, avi, mov, mkv"}), 400
    
    filepath = None
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logging.info(f"Processing video: {filename}")
        
        # Run inference
        result = detector.predict_video(filepath, num_frames=10)
        
        # Update statistics
        update_stats(result["prediction"], result["confidence"])
        
        # Log result
        logging.info(f"Prediction: {filename} -> {result['prediction']} (Confidence: {result['confidence']:.2%})")
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "result": result
        })
    
    except Exception as e:
        logging.error(f"Error processing {file.filename}: {str(e)}")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/predict-batch', methods=['POST'])
def predict_batch():
    """Process multiple videos at once"""
    if 'videos' not in request.files:
        return jsonify({"error": "No videos provided"}), 400
    
    files = request.files.getlist('videos')
    
    if len(files) == 0:
        return jsonify({"error": "No files selected"}), 400
    
    if len(files) > 10:
        return jsonify({"error": "Maximum 10 videos allowed per batch"}), 400
    
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            filepath = None
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                result = detector.predict_video(filepath, num_frames=10)
                
                # Update statistics
                update_stats(result["prediction"], result["confidence"])
                
                results.append({
                    "filename": filename,
                    "success": True,
                    "result": result
                })
                
                successful += 1
                os.remove(filepath)
                
                logging.info(f"Batch prediction: {filename} -> {result['prediction']}")
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
                
                logging.error(f"Batch prediction failed: {file.filename} - {str(e)}")
        else:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": "Invalid file type"
            })
            failed += 1
    
    return jsonify({
        "success": True,
        "total": len(files),
        "successful": successful,
        "failed": failed,
        "results": results
    })

@app.route('/predict-custom', methods=['POST'])
def predict_custom():
    """Predict with custom parameters"""
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or no file selected"}), 400
    
    # Get custom parameters
    threshold = float(request.form.get('threshold', 0.5))
    num_frames = int(request.form.get('num_frames', 10))
    
    # Validate parameters
    if not 0.0 <= threshold <= 1.0:
        return jsonify({"error": "Threshold must be between 0 and 1"}), 400
    
    if not 1 <= num_frames <= 30:
        return jsonify({"error": "Number of frames must be between 1 and 30"}), 400
    
    filepath = None
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Run inference with custom frame count
        result = detector.predict_video(filepath, num_frames=num_frames)
        
        # Apply custom threshold
        raw_score = result["raw_score"]
        custom_prediction = "FAKE" if raw_score > threshold else "REAL"
        custom_confidence = raw_score if raw_score > threshold else 1 - raw_score
        
        result["custom_prediction"] = custom_prediction
        result["custom_confidence"] = custom_confidence
        result["threshold_used"] = threshold
        
        # Update statistics
        update_stats(custom_prediction, custom_confidence)
        
        os.remove(filepath)
        
        logging.info(f"Custom prediction: {filename} -> {custom_prediction} (threshold={threshold}, frames={num_frames})")
        
        return jsonify({
            "success": True,
            "filename": filename,
            "result": result
        })
    
    except Exception as e:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        logging.error(f"Custom prediction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/video-info', methods=['POST'])
def video_info():
    """Extract metadata from video without prediction"""
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    filepath = None
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Convert to H264 for browser compatibility
        converted_filename = filename.rsplit('.', 1)[0] + '_h264.mp4'
        converted_path = os.path.join(app.config['UPLOAD_FOLDER'], converted_filename)
        subprocess.run([
            'ffmpeg', '-i', filepath,
            '-vcodec', 'libx264', '-acodec', 'aac',
            '-y', converted_path
        ], capture_output=True)
        os.remove(filepath)
        filepath = converted_path
        filename = converted_filename
        
        cap = cv2.VideoCapture(filepath)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        info = {
            "filename": filename,
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_seconds": round(duration, 2),
            "file_size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2)
        }
        
        cap.release()
        
        return jsonify({
            "success": True,
            "info": info
        })
    
    except Exception as e:
        if filepath and os.path.exists(filepath):
            pass
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/model-info', methods=['GET'])
def model_info():
    """Get detailed information about the model"""
    try:
        # Try to load metadata file
        metadata_path = MODEL_PATH.replace('.pth', '.json')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"✓ Loaded metadata from {metadata_path}")
        else:
            print(f"⚠ Metadata file not found at {metadata_path}, using defaults")
            metadata = {
                "model_name": "Deepfake Detector v1.0",
                "architecture": "EfficientNet-B4",
                "performance_metrics": {
                    "validation_accuracy": "99.03%",
                    "auc_score": "99.95%",
                    "precision": "98.92%",
                    "recall": "99.22%",
                    "f1_score": "99.07%"
                },
                "training_details": {
                "dataset": "FaceForensics++ c40",
                "total_videos": 2000,
                "total_frames": 39697,
                "epochs": 20,
                "batch_size": 32
                 },
                "inference_settings": {
                "default_frames_analyzed": 10,
                "frame_sampling": "evenly distributed",
                "input_size": "224x224",
                "prediction_threshold": 0.5
                }
            }
        
        # Add runtime info
        metadata["model_file"] = os.path.basename(MODEL_PATH)
        metadata["device"] = "CPU"
        
        return jsonify(metadata)
        
    except Exception as e:
        print(f"Error loading model info: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get API usage statistics"""
    stats_copy = prediction_stats.copy()
    stats_copy["average_confidence"] = f"{stats_copy['average_confidence']:.2%}"
    
    if stats_copy["total_predictions"] > 0:
        stats_copy["real_percentage"] = f"{(stats_copy['real_count'] / stats_copy['total_predictions'] * 100):.2f}%"
        stats_copy["fake_percentage"] = f"{(stats_copy['fake_count'] / stats_copy['total_predictions'] * 100):.2f}%"
    else:
        stats_copy["real_percentage"] = "0%"
        stats_copy["fake_percentage"] = "0%"
    
    return jsonify(stats_copy)

@app.route('/logs', methods=['GET'])
def logs():
    """View recent API logs"""
    try:
        with open('api_logs.txt', 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-50:]  # Last 50 lines
        
        return jsonify({
            "success": True,
            "total_lines": len(lines),
            "showing": len(recent_logs),
            "logs": [line.strip() for line in recent_logs]
        })
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "No logs found yet"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print(f"✓ DeepfakeShield starting...")
    print(f"Model    : {MODEL_PATH}")
    print(f"Uploads  : {UPLOAD_FOLDER}")
    print(f"Max size : {MAX_FILE_SIZE / (1024*1024):.0f} MB")
    print(f"Logs     : api_logs.txt")
    print(f"Server   : http://127.0.0.1:5000")

    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)