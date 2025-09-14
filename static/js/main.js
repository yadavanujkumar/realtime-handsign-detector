class HandSignDetectorApp {
    constructor() {
        this.socket = null;
        this.videoElement = null;
        this.canvas = null;
        this.ctx = null;
        this.isDetecting = false;
        this.detectionInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupSocket();
        this.setupEventListeners();
        this.updateStatus('Connecting...');
    }
    
    setupElements() {
        this.videoElement = document.getElementById('videoElement');
        this.canvas = document.getElementById('overlayCanvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.captureBtn = document.getElementById('captureBtn');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
    }
    
    setupSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateStatus('Connected', 'connected');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateStatus('Disconnected', 'disconnected');
        });
        
        this.socket.on('detection_result', (data) => {
            this.handleDetectionResult(data);
        });
        
        this.socket.on('connected', (data) => {
            console.log('Server confirmed connection:', data);
        });
    }
    
    setupEventListeners() {
        if (this.startBtn) {
            this.startBtn.addEventListener('click', () => this.startDetection());
        }
        
        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => this.stopDetection());
        }
        
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.captureFrame());
        }
    }
    
    async startDetection() {
        try {
            // Get user media
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });
            
            this.videoElement.srcObject = stream;
            
            // Wait for video to load
            await new Promise((resolve) => {
                this.videoElement.onloadedmetadata = resolve;
            });
            
            // Setup canvas
            if (this.canvas) {
                this.canvas.width = this.videoElement.videoWidth;
                this.canvas.height = this.videoElement.videoHeight;
            }
            
            this.isDetecting = true;
            this.updateButtons();
            this.updateStatus('Detecting...', 'connected');
            
            // Start detection loop
            this.detectionInterval = setInterval(() => {
                this.detectFrame();
            }, 100); // 10 FPS
            
            // Notify server
            this.socket.emit('start_detection');
            
        } catch (error) {
            console.error('Error starting detection:', error);
            alert('Error accessing camera: ' + error.message);
        }
    }
    
    stopDetection() {
        this.isDetecting = false;
        this.updateButtons();
        this.updateStatus('Connected', 'connected');
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        
        // Stop video stream
        if (this.videoElement.srcObject) {
            const tracks = this.videoElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }
        
        // Clear canvas
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Clear results
        this.displayResults({ hands_detected: 0, hand_signs: [] });
        
        // Notify server
        this.socket.emit('stop_detection');
    }
    
    detectFrame() {
        if (!this.isDetecting || !this.videoElement.videoWidth) return;
        
        // Create a temporary canvas to capture the frame
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.videoElement.videoWidth;
        tempCanvas.height = this.videoElement.videoHeight;
        
        // Draw video frame to canvas
        tempCtx.drawImage(this.videoElement, 0, 0);
        
        // Convert to base64
        const imageData = tempCanvas.toDataURL('image/jpeg', 0.8);
        
        // Send to server for detection
        this.socket.emit('detect_frame', {
            image: imageData,
            timestamp: Date.now()
        });
    }
    
    captureFrame() {
        if (!this.videoElement.videoWidth) {
            alert('Please start detection first');
            return;
        }
        
        // Create a temporary canvas to capture the frame
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.videoElement.videoWidth;
        tempCanvas.height = this.videoElement.videoHeight;
        
        // Draw video frame to canvas
        tempCtx.drawImage(this.videoElement, 0, 0);
        
        // Convert to base64
        const imageData = tempCanvas.toDataURL('image/jpeg', 0.8);
        
        // Send to server for detection
        fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.handleDetectionResult(data);
            } else {
                console.error('Detection error:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    handleDetectionResult(data) {
        if (data.success && data.results) {
            this.displayResults(data.results);
            this.drawLandmarks(data.results);
        } else {
            console.error('Detection error:', data.error);
        }
    }
    
    displayResults(results) {
        if (!this.resultsContainer) return;
        
        const handsDetected = results.hands_detected || 0;
        const handSigns = results.hand_signs || [];
        
        if (handsDetected === 0) {
            this.resultsContainer.innerHTML = '<p class="no-results">No hands detected</p>';
            return;
        }
        
        let html = '';
        handSigns.forEach((sign, index) => {
            const emoji = this.getSignEmoji(sign.sign);
            html += `
                <div class="detection-item">
                    <div>
                        <span class="hand-sign">${emoji} ${sign.sign.replace('_', ' ')}</span>
                    </div>
                    <div class="confidence">
                        ${Math.round((sign.confidence || 0.8) * 100)}%
                    </div>
                </div>
            `;
        });
        
        this.resultsContainer.innerHTML = html;
    }
    
    drawLandmarks(results) {
        if (!this.ctx || !results.landmarks) return;
        
        // Clear previous drawings
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw landmarks for each hand
        results.landmarks.forEach((landmarks, handIndex) => {
            this.drawHandLandmarks(landmarks, handIndex);
        });
    }
    
    drawHandLandmarks(landmarks, handIndex) {
        const colors = ['#ff0000', '#00ff00']; // Red for first hand, green for second
        const color = colors[handIndex] || '#ff0000';
        
        // Draw connections between landmarks
        const connections = [
            [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
            [0, 5], [5, 6], [6, 7], [7, 8], // Index
            [0, 9], [9, 10], [10, 11], [11, 12], // Middle
            [0, 13], [13, 14], [14, 15], [15, 16], // Ring
            [0, 17], [17, 18], [18, 19], [19, 20], // Pinky
            [5, 9], [9, 13], [13, 17] // Palm
        ];
        
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 2;
        
        connections.forEach(([start, end]) => {
            const startPoint = landmarks[start];
            const endPoint = landmarks[end];
            
            if (startPoint && endPoint) {
                this.ctx.beginPath();
                this.ctx.moveTo(
                    startPoint.x * this.canvas.width,
                    startPoint.y * this.canvas.height
                );
                this.ctx.lineTo(
                    endPoint.x * this.canvas.width,
                    endPoint.y * this.canvas.height
                );
                this.ctx.stroke();
            }
        });
        
        // Draw landmark points
        this.ctx.fillStyle = color;
        landmarks.forEach(landmark => {
            this.ctx.beginPath();
            this.ctx.arc(
                landmark.x * this.canvas.width,
                landmark.y * this.canvas.height,
                3,
                0,
                2 * Math.PI
            );
            this.ctx.fill();
        });
    }
    
    getSignEmoji(sign) {
        const emojiMap = {
            'thumbs_up': '👍',
            'thumbs_down': '👎',
            'peace': '✌️',
            'ok': '👌',
            'fist': '✊',
            'open_palm': '🖐️',
            'pointing': '👉',
            'unknown': '❓'
        };
        return emojiMap[sign] || '❓';
    }
    
    updateButtons() {
        if (this.startBtn) this.startBtn.disabled = this.isDetecting;
        if (this.stopBtn) this.stopBtn.disabled = !this.isDetecting;
    }
    
    updateStatus(text, className = '') {
        if (this.statusText) this.statusText.textContent = text;
        if (this.statusIndicator) {
            this.statusIndicator.className = 'status-indicator ' + className;
        }
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HandSignDetectorApp();
});