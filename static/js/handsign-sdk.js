/**
 * Hand Sign Detector SDK
 * Easy integration for video conferencing apps
 * 
 * Usage:
 * const detector = new HandSignDetector({
 *   serverUrl: 'https://your-server.com',
 *   onDetection: (results) => console.log(results)
 * });
 * 
 * detector.startDetection(videoElement);
 */

(function(global) {
    'use strict';
    
    class HandSignDetector {
        constructor(options = {}) {
            this.serverUrl = options.serverUrl || 'http://localhost:5000';
            this.onDetection = options.onDetection || (() => {});
            this.onError = options.onError || console.error;
            this.updateInterval = options.updateInterval || 200; // ms
            this.enableOverlay = options.enableOverlay !== false;
            
            this.socket = null;
            this.eventListeners = {};
            this.isDetecting = false;
            this.videoElement = null;
            this.overlayCanvas = null;
            this.overlayCtx = null;
            
            this.init();
        }
        
        init() {
            // Load Socket.IO if not already loaded
            if (typeof io === 'undefined') {
                this.loadSocketIO().then(() => {
                    this.connect();
                });
            } else {
                this.connect();
            }
        }
        
        loadSocketIO() {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }
        
        connect() {
            try {
                this.socket = io(this.serverUrl);
                
                this.socket.on('connect', () => {
                    console.log('HandSignDetector connected to', this.serverUrl);
                    this.emit('connected');
                });
                
                this.socket.on('disconnect', () => {
                    console.log('HandSignDetector disconnected');
                    this.emit('disconnected');
                });
                
                this.socket.on('detection_result', (data) => {
                    if (data.success && data.results) {
                        this.handleDetectionResult(data.results);
                    } else {
                        this.onError('Detection error: ' + (data.error || 'Unknown error'));
                    }
                });
                
            } catch (error) {
                this.onError('Connection error: ' + error.message);
            }
        }
        
        startDetection(videoElement) {
            if (!videoElement) {
                throw new Error('Video element is required');
            }
            
            this.videoElement = videoElement;
            this.isDetecting = true;
            
            // Create overlay canvas if enabled
            if (this.enableOverlay) {
                this.createOverlay();
            }
            
            // Start detection loop
            this.detectionInterval = setInterval(() => {
                this.captureAndDetect();
            }, this.updateInterval);
            
            this.emit('detection_started');
            console.log('Hand sign detection started');
        }
        
        stopDetection() {
            this.isDetecting = false;
            
            if (this.detectionInterval) {
                clearInterval(this.detectionInterval);
                this.detectionInterval = null;
            }
            
            // Remove overlay
            if (this.overlayCanvas) {
                this.overlayCanvas.remove();
                this.overlayCanvas = null;
                this.overlayCtx = null;
            }
            
            this.emit('detection_stopped');
            console.log('Hand sign detection stopped');
        }
        
        createOverlay() {
            if (!this.videoElement || this.overlayCanvas) return;
            
            // Create canvas overlay
            this.overlayCanvas = document.createElement('canvas');
            this.overlayCanvas.style.position = 'absolute';
            this.overlayCanvas.style.top = '0';
            this.overlayCanvas.style.left = '0';
            this.overlayCanvas.style.pointerEvents = 'none';
            this.overlayCanvas.style.zIndex = '1000';
            
            // Position overlay over video
            const videoRect = this.videoElement.getBoundingClientRect();
            this.overlayCanvas.style.width = videoRect.width + 'px';
            this.overlayCanvas.style.height = videoRect.height + 'px';
            this.overlayCanvas.width = this.videoElement.videoWidth || videoRect.width;
            this.overlayCanvas.height = this.videoElement.videoHeight || videoRect.height;
            
            // Insert overlay
            this.videoElement.parentNode.insertBefore(this.overlayCanvas, this.videoElement.nextSibling);
            this.overlayCtx = this.overlayCanvas.getContext('2d');
        }
        
        captureAndDetect() {
            if (!this.isDetecting || !this.videoElement || !this.socket) return;
            
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                const width = this.videoElement.videoWidth || this.videoElement.offsetWidth;
                const height = this.videoElement.videoHeight || this.videoElement.offsetHeight;
                
                canvas.width = width;
                canvas.height = height;
                
                ctx.drawImage(this.videoElement, 0, 0, width, height);
                
                const imageData = canvas.toDataURL('image/jpeg', 0.7);
                
                this.socket.emit('detect_frame', {
                    image: imageData,
                    timestamp: Date.now()
                });
                
            } catch (error) {
                this.onError('Capture error: ' + error.message);
            }
        }
        
        handleDetectionResult(results) {
            // Call user callback
            this.onDetection(results);
            
            // Emit specific sign events
            if (results.hand_signs) {
                results.hand_signs.forEach(sign => {
                    this.emit(sign.sign, sign);
                });
            }
            
            // Update overlay
            if (this.enableOverlay && this.overlayCtx) {
                this.drawOverlay(results);
            }
        }
        
        drawOverlay(results) {
            if (!this.overlayCtx) return;
            
            // Clear previous drawings
            this.overlayCtx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
            
            if (!results.hand_signs || results.hand_signs.length === 0) return;
            
            // Draw detection results
            results.hand_signs.forEach((sign, index) => {
                const emoji = this.getSignEmoji(sign.sign);
                const label = `${emoji} ${sign.sign.replace('_', ' ')}`;
                const confidence = Math.round((sign.confidence || 0.8) * 100);
                
                const y = 30 + (index * 40);
                
                // Draw background
                this.overlayCtx.fillStyle = 'rgba(0, 123, 255, 0.8)';
                this.overlayCtx.fillRect(10, y - 25, 200, 30);
                
                // Draw text
                this.overlayCtx.fillStyle = 'white';
                this.overlayCtx.font = 'bold 16px Arial';
                this.overlayCtx.fillText(`${label} (${confidence}%)`, 15, y - 5);
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
        
        // Event system
        on(eventName, callback) {
            if (!this.eventListeners[eventName]) {
                this.eventListeners[eventName] = [];
            }
            this.eventListeners[eventName].push(callback);
            return this; // For chaining
        }
        
        off(eventName, callback) {
            if (!this.eventListeners[eventName]) return this;
            
            if (callback) {
                const index = this.eventListeners[eventName].indexOf(callback);
                if (index > -1) {
                    this.eventListeners[eventName].splice(index, 1);
                }
            } else {
                delete this.eventListeners[eventName];
            }
            return this;
        }
        
        emit(eventName, data) {
            if (!this.eventListeners[eventName]) return;
            
            this.eventListeners[eventName].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Event listener error:', error);
                }
            });
        }
        
        // Utility methods
        isConnected() {
            return this.socket && this.socket.connected;
        }
        
        isActive() {
            return this.isDetecting;
        }
        
        getStatus() {
            return {
                connected: this.isConnected(),
                detecting: this.isActive(),
                serverUrl: this.serverUrl
            };
        }
    }
    
    // Helper functions for common video conferencing platforms
    HandSignDetector.utils = {
        // Find video element in common video conferencing apps
        findVideoElement() {
            // Common selectors for video elements
            const selectors = [
                'video[autoplay]', // General
                '[data-testid="participant-video"]', // Zoom
                '[data-tid="videostream"]', // Teams
                '[data-participant-id] video', // Meet
                '.participant-video video', // Generic
                '#localVideo, #remoteVideo' // Generic
            ];
            
            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element && element.videoWidth > 0) {
                    return element;
                }
            }
            
            // Fallback: find any video element with actual video
            const allVideos = document.querySelectorAll('video');
            for (const video of allVideos) {
                if (video.videoWidth > 0 && video.videoHeight > 0) {
                    return video;
                }
            }
            
            return null;
        },
        
        // Auto-detect and start on video conferencing pages
        autoStart(options = {}) {
            const detector = new HandSignDetector(options);
            
            // Try to find video immediately
            let video = this.findVideoElement();
            if (video) {
                detector.startDetection(video);
                return detector;
            }
            
            // If no video found, wait and retry
            const observer = new MutationObserver(() => {
                video = this.findVideoElement();
                if (video) {
                    observer.disconnect();
                    detector.startDetection(video);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Stop observing after 30 seconds
            setTimeout(() => {
                observer.disconnect();
            }, 30000);
            
            return detector;
        }
    };
    
    // Export for different module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = HandSignDetector;
    } else if (typeof define === 'function' && define.amd) {
        define([], function() {
            return HandSignDetector;
        });
    } else {
        global.HandSignDetector = HandSignDetector;
    }
    
})(typeof window !== 'undefined' ? window : this);