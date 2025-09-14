from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import base64
import numpy as np
import json
from hand_detector import HandSignDetector
import io
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'handsign_detector_secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize hand detector
detector = HandSignDetector()

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/plugin')
def plugin():
    """Serve the plugin interface"""
    return render_template('plugin.html')

@app.route('/api/detect', methods=['POST'])
def detect_hand_signs():
    """REST API endpoint for hand sign detection"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_data = data['image'].split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Detect hand signs
        results = detector.detect_hands(image_bgr)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to hand sign detector'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('detect_frame')
def handle_frame_detection(data):
    """Handle real-time frame detection via WebSocket"""
    try:
        # Decode base64 image
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Detect hand signs
        results = detector.detect_hands(image_bgr)
        
        # Emit results back to client
        emit('detection_result', {
            'success': True,
            'results': results,
            'timestamp': data.get('timestamp', 0)
        })
        
    except Exception as e:
        emit('detection_result', {
            'success': False,
            'error': str(e)
        })

@socketio.on('start_detection')
def handle_start_detection():
    """Start continuous detection mode"""
    emit('detection_started', {'status': 'Detection started'})

@socketio.on('stop_detection')
def handle_stop_detection():
    """Stop continuous detection mode"""
    emit('detection_stopped', {'status': 'Detection stopped'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)