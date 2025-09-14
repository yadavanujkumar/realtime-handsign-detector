#!/usr/bin/env python3
"""
Lightweight demo server for the hand sign detector
This version uses minimal dependencies for demonstration
"""

try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

import json
import base64
import os
from test_detector import MockHandDetector

if FLASK_AVAILABLE:
    app = Flask(__name__)
    CORS(app)
    
    # Initialize mock detector
    detector = MockHandDetector()
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/plugin')
    def plugin():
        return render_template('plugin.html')
    
    @app.route('/api/detect', methods=['POST'])
    def detect_hand_signs():
        """REST API endpoint for hand sign detection"""
        try:
            data = request.get_json()
            
            if 'image' not in data:
                return jsonify({'error': 'No image provided'}), 400
            
            # For demo purposes, randomly select a test case
            import random
            test_cases = ['thumbs_up', 'peace', 'fist', 'open_palm', 'none']
            test_case = random.choice(test_cases)
            
            # Simulate detection
            results = detector.simulate_detection(test_case)
            
            return jsonify({
                'success': True,
                'results': results,
                'demo_note': f'Demo mode: simulated {test_case} detection'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status')
    def status():
        return jsonify({
            'status': 'running',
            'mode': 'demo',
            'message': 'Hand sign detector demo server is running'
        })
    
    if __name__ == '__main__':
        print("🤟 Starting Hand Sign Detector Demo Server")
        print("=" * 50)
        print("Demo Mode: Using mock detection for demonstration")
        print("For full functionality, install: pip install -r requirements.txt")
        print("Server will be available at: http://localhost:5000")
        print("=" * 50)
        
        app.run(host='0.0.0.0', port=5000, debug=True)

else:
    print("🤟 Hand Sign Detector - Installation Required")
    print("=" * 50)
    print("Flask is not installed. To run the web server:")
    print("1. Install dependencies: pip install flask flask-cors")
    print("2. Run: python demo_server.py")
    print("")
    print("Or install all dependencies: pip install -r requirements.txt")
    print("=" * 50)
    
    # Show static demo
    print("\n📱 Static Demo:")
    print("-" * 20)
    
    detector = MockHandDetector()
    test_cases = ['thumbs_up', 'peace', 'fist']
    
    for test_case in test_cases:
        result = detector.simulate_detection(test_case)
        if result['hand_signs']:
            sign = result['hand_signs'][0]
            emoji_map = {
                'thumbs_up': '👍',
                'peace': '✌️',
                'fist': '✊'
            }
            emoji = emoji_map.get(sign['sign'], '❓')
            print(f"{emoji} {sign['sign'].replace('_', ' ')} - {sign['confidence']:.0%} confidence")
    
    print(f"\n🔌 Integration ready with SDK at: static/js/handsign-sdk.js")
    print(f"📖 Full documentation in: README.md")