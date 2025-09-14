# Realtime Hand Sign Detector

A powerful, real-time hand sign detection system that can be integrated into video conferencing applications like Zoom, Microsoft Teams, Google Meet, and more.

## 🌟 Features

- **Real-time Detection**: Detect hand signs in real-time using MediaPipe and OpenCV
- **Multiple Hand Signs**: Supports thumbs up/down, peace sign, OK sign, fist, open palm, and pointing
- **Plugin Integration**: Easy-to-use SDK for integrating into existing video conferencing apps
- **WebSocket Support**: Low-latency real-time communication
- **REST API**: Simple HTTP API for one-off detections
- **Web Interface**: Complete web-based demo application
- **Cross-platform**: Works in any modern web browser

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Modern web browser with camera access
- Internet connection for initial setup

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yadavanujkumar/realtime-handsign-detector.git
cd realtime-handsign-detector
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and go to:
```
http://localhost:5000
```

## 🔌 Plugin Integration

### Quick Integration

Include the SDK in your web application:

```html
<script src="https://yourserver.com/static/js/handsign-sdk.js"></script>
```

Initialize and start detection:

```javascript
const detector = new HandSignDetector({
    serverUrl: 'https://yourserver.com',
    onDetection: (results) => {
        console.log('Hand signs detected:', results);
    }
});

// Start detection with your video element
const videoElement = document.getElementById('yourVideo');
detector.startDetection(videoElement);

// Listen for specific gestures
detector.on('thumbs_up', () => {
    console.log('User gave thumbs up!');
    // Add reaction, send emoji, etc.
});

detector.on('peace', () => {
    console.log('Peace sign detected!');
    // Show peace emoji
});
```

### Platform-Specific Integration

#### Zoom Apps SDK
```javascript
import zoomSdk from '@zoom/appssdk';
import { HandSignDetector } from './handsign-sdk.js';

const detector = new HandSignDetector({
    serverUrl: 'your-server-url'
});

zoomSdk.getVideoStream().then(stream => {
    detector.startDetection(stream);
});
```

#### Microsoft Teams
```javascript
import * as microsoftTeams from "@microsoft/teams-js";
import { HandSignDetector } from './handsign-sdk.js';

microsoftTeams.initialize(() => {
    const detector = new HandSignDetector({
        serverUrl: 'your-server-url'
    });
    
    detector.startDetection(videoElement);
});
```

#### Chrome Extension for Google Meet
```javascript
chrome.tabs.executeScript({
    code: `
        const detector = new HandSignDetector({
            serverUrl: 'your-server-url'
        });
        
        const videoElement = document.querySelector('video[autoplay]');
        if (videoElement) {
            detector.startDetection(videoElement);
        }
    `
});
```

## 📖 API Documentation

### REST API

#### Detect Hand Signs
```http
POST /api/detect
Content-Type: application/json

{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

**Response:**
```json
{
    "success": true,
    "results": {
        "hands_detected": 1,
        "hand_signs": [
            {
                "hand_index": 0,
                "sign": "thumbs_up",
                "confidence": 0.95
            }
        ],
        "landmarks": [...]
    }
}
```

### WebSocket API

#### Connect
```javascript
const socket = io('https://yourserver.com');
```

#### Send Frame for Detection
```javascript
socket.emit('detect_frame', {
    image: 'data:image/jpeg;base64,...',
    timestamp: Date.now()
});
```

#### Receive Results
```javascript
socket.on('detection_result', (data) => {
    if (data.success) {
        console.log('Detection results:', data.results);
    }
});
```

## 🤟 Supported Hand Signs

| Sign | Emoji | Description |
|------|-------|-------------|
| Thumbs Up | 👍 | Thumb extended upward |
| Thumbs Down | 👎 | Thumb extended downward |
| Peace | ✌️ | Index and middle fingers extended |
| OK | 👌 | Thumb and index finger touching |
| Fist | ✊ | All fingers closed |
| Open Palm | 🖐️ | All fingers extended |
| Pointing | 👉 | Index finger extended |

## ⚙️ Configuration

### SDK Options

```javascript
const detector = new HandSignDetector({
    serverUrl: 'https://yourserver.com',     // Server URL
    updateInterval: 200,                      // Detection interval (ms)
    enableOverlay: true,                      // Show overlay on video
    onDetection: (results) => {},             // Detection callback
    onError: (error) => {}                    // Error callback
});
```

### Server Configuration

Edit `app.py` to configure:

- **Host/Port**: Change `host='0.0.0.0', port=5000`
- **Detection Confidence**: Modify `min_detection_confidence` in `hand_detector.py`
- **CORS Settings**: Update `cors_allowed_origins` in Flask-SocketIO setup

## 🔧 Development

### Project Structure
```
realtime-handsign-detector/
├── app.py                 # Flask server
├── hand_detector.py       # Hand detection logic
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       ├── main.js       # Main web app
│       ├── plugin.js     # Plugin demo
│       └── handsign-sdk.js # SDK for integration
├── templates/
│   ├── index.html        # Main interface
│   └── plugin.html       # Plugin demo
└── README.md
```

### Adding New Hand Signs

1. Add detection logic in `hand_detector.py`:
```python
def _detect_new_sign(self, landmarks: List[Dict]) -> bool:
    # Your detection logic here
    return True  # or False
```

2. Register the sign:
```python
self.hand_signs['new_sign'] = self._detect_new_sign
```

3. Add emoji mapping in JavaScript files:
```javascript
const emojiMap = {
    'new_sign': '🆕',
    // ... existing mappings
};
```

## 🚀 Deployment

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
```

### Using Heroku

1. Create `Procfile`:
```
web: python app.py
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

### Using AWS/GCP/Azure

The application can be deployed to any cloud platform that supports Python web applications. Make sure to:

1. Install system dependencies for OpenCV
2. Configure environment variables
3. Set up HTTPS for WebSocket connections
4. Configure CORS for your domains

## 📱 Browser Support

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

**Required Permissions:**
- Camera access for video capture
- Network access for API communication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) for hand detection
- [OpenCV](https://opencv.org/) for computer vision
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Socket.IO](https://socket.io/) for real-time communication

## 📞 Support

For support, please open an issue on GitHub or contact the maintainers.

---

Made with ❤️ for better communication in the digital world!