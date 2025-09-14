class HandSignPlugin {
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
    }
    
    setupElements() {
        this.videoElement = document.getElementById('pluginVideo');
        this.canvas = document.getElementById('pluginCanvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        
        this.startBtn = document.getElementById('pluginStartBtn');
        this.stopBtn = document.getElementById('pluginStopBtn');
        this.resultsContainer = document.getElementById('pluginResults');
    }
    
    setupSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Plugin connected to server');
        });
        
        this.socket.on('detection_result', (data) => {
            this.handleDetectionResult(data);
        });
    }
    
    setupEventListeners() {
        if (this.startBtn) {
            this.startBtn.addEventListener('click', () => this.startPlugin());
        }
        
        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => this.stopPlugin());
        }
    }
    
    async startPlugin() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 400, height: 300 }
            });
            
            this.videoElement.srcObject = stream;
            
            await new Promise((resolve) => {
                this.videoElement.onloadedmetadata = resolve;
            });
            
            if (this.canvas) {
                this.canvas.width = this.videoElement.videoWidth;
                this.canvas.height = this.videoElement.videoHeight;
                this.canvas.style.width = this.videoElement.offsetWidth + 'px';
                this.canvas.style.height = this.videoElement.offsetHeight + 'px';
            }
            
            this.isDetecting = true;
            this.updateButtons();
            
            this.detectionInterval = setInterval(() => {
                this.detectFrame();
            }, 200); // 5 FPS for plugin demo
            
        } catch (error) {
            console.error('Error starting plugin:', error);
            alert('Error accessing camera: ' + error.message);
        }
    }
    
    stopPlugin() {
        this.isDetecting = false;
        this.updateButtons();
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        
        if (this.videoElement.srcObject) {
            const tracks = this.videoElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }
        
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        
        this.displayResults({ hands_detected: 0, hand_signs: [] });
    }
    
    detectFrame() {
        if (!this.isDetecting || !this.videoElement.videoWidth) return;
        
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = this.videoElement.videoWidth;
        tempCanvas.height = this.videoElement.videoHeight;
        
        tempCtx.drawImage(this.videoElement, 0, 0);
        
        const imageData = tempCanvas.toDataURL('image/jpeg', 0.8);
        
        this.socket.emit('detect_frame', {
            image: imageData,
            timestamp: Date.now()
        });
    }
    
    handleDetectionResult(data) {
        if (data.success && data.results) {
            this.displayResults(data.results);
            this.drawOverlay(data.results);
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
        
        let html = '<div style="text-align: left;">';
        handSigns.forEach((sign, index) => {
            const emoji = this.getSignEmoji(sign.sign);
            html += `
                <div style="margin: 5px 0; padding: 5px; background: #f0f0f0; border-radius: 4px;">
                    ${emoji} <strong>${sign.sign.replace('_', ' ')}</strong>
                    <span style="float: right; color: #666;">${Math.round((sign.confidence || 0.8) * 100)}%</span>
                </div>
            `;
        });
        html += '</div>';
        
        this.resultsContainer.innerHTML = html;
    }
    
    drawOverlay(results) {
        if (!this.ctx || !results.landmarks) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw simple bounding boxes and labels
        results.hand_signs.forEach((sign, index) => {
            const emoji = this.getSignEmoji(sign.sign);
            const label = `${emoji} ${sign.sign.replace('_', ' ')}`;
            
            // Draw label background
            this.ctx.fillStyle = 'rgba(0, 123, 255, 0.8)';
            this.ctx.fillRect(10, 10 + (index * 30), 200, 25);
            
            // Draw label text
            this.ctx.fillStyle = 'white';
            this.ctx.font = '16px Arial';
            this.ctx.fillText(label, 15, 28 + (index * 30));
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
}

// Initialize the plugin when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HandSignPlugin();
});

// Also create the SDK for external integration
class HandSignDetector {
    constructor(options = {}) {
        this.serverUrl = options.serverUrl || window.location.origin;
        this.onDetection = options.onDetection || (() => {});
        this.socket = null;
        this.eventListeners = {};
        this.isDetecting = false;
        
        this.connect();
    }
    
    connect() {
        this.socket = io(this.serverUrl);
        
        this.socket.on('connect', () => {
            console.log('HandSignDetector connected');
        });
        
        this.socket.on('detection_result', (data) => {
            if (data.success && data.results) {
                this.onDetection(data.results);
                this.emitSignEvents(data.results);
            }
        });
    }
    
    startDetection(videoElement) {
        if (!videoElement) {
            throw new Error('Video element is required');
        }
        
        this.videoElement = videoElement;
        this.isDetecting = true;
        
        this.detectionInterval = setInterval(() => {
            this.captureAndDetect();
        }, 200);
    }
    
    stopDetection() {
        this.isDetecting = false;
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    }
    
    captureAndDetect() {
        if (!this.isDetecting || !this.videoElement) return;
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = this.videoElement.videoWidth || this.videoElement.offsetWidth;
        canvas.height = this.videoElement.videoHeight || this.videoElement.offsetHeight;
        
        ctx.drawImage(this.videoElement, 0, 0, canvas.width, canvas.height);
        
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        this.socket.emit('detect_frame', {
            image: imageData,
            timestamp: Date.now()
        });
    }
    
    on(eventName, callback) {
        if (!this.eventListeners[eventName]) {
            this.eventListeners[eventName] = [];
        }
        this.eventListeners[eventName].push(callback);
    }
    
    emitSignEvents(results) {
        results.hand_signs.forEach(sign => {
            const eventName = sign.sign;
            if (this.eventListeners[eventName]) {
                this.eventListeners[eventName].forEach(callback => {
                    callback(sign);
                });
            }
        });
    }
}

// Make SDK available globally
window.HandSignDetector = HandSignDetector;