import cv2
import mediapipe as mp
import numpy as np
import json
from typing import Dict, List, Tuple, Optional

class HandSignDetector:
    """
    Real-time hand sign detector using MediaPipe
    """
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Define common hand signs
        self.hand_signs = {
            'thumbs_up': self._detect_thumbs_up,
            'thumbs_down': self._detect_thumbs_down,
            'peace': self._detect_peace_sign,
            'ok': self._detect_ok_sign,
            'fist': self._detect_fist,
            'open_palm': self._detect_open_palm,
            'pointing': self._detect_pointing
        }
    
    def detect_hands(self, image: np.ndarray) -> Dict:
        """
        Detect hands and classify hand signs in the given image
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary containing detection results
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_image)
        
        detection_result = {
            'hands_detected': 0,
            'hand_signs': [],
            'landmarks': []
        }
        
        if results.multi_hand_landmarks:
            detection_result['hands_detected'] = len(results.multi_hand_landmarks)
            
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Extract landmark coordinates
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z
                    })
                
                detection_result['landmarks'].append(landmarks)
                
                # Classify hand sign
                hand_sign = self._classify_hand_sign(landmarks)
                detection_result['hand_signs'].append({
                    'hand_index': idx,
                    'sign': hand_sign,
                    'confidence': 0.8  # Placeholder confidence
                })
        
        return detection_result
    
    def _classify_hand_sign(self, landmarks: List[Dict]) -> str:
        """
        Classify the hand sign based on landmark positions
        """
        for sign_name, detector_func in self.hand_signs.items():
            if detector_func(landmarks):
                return sign_name
        return 'unknown'
    
    def _get_finger_status(self, landmarks: List[Dict]) -> List[bool]:
        """
        Determine which fingers are extended
        Returns list [thumb, index, middle, ring, pinky]
        """
        # Finger tip and pip landmarks
        tip_ids = [4, 8, 12, 16, 20]
        pip_ids = [3, 6, 10, 14, 18]
        
        fingers = []
        
        # Thumb (special case - check x coordinate)
        if landmarks[tip_ids[0]]['x'] > landmarks[pip_ids[0]]['x']:
            fingers.append(True)
        else:
            fingers.append(False)
        
        # Other fingers (check y coordinate)
        for i in range(1, 5):
            if landmarks[tip_ids[i]]['y'] < landmarks[pip_ids[i]]['y']:
                fingers.append(True)
            else:
                fingers.append(False)
        
        return fingers
    
    def _detect_thumbs_up(self, landmarks: List[Dict]) -> bool:
        fingers = self._get_finger_status(landmarks)
        return fingers[0] and not any(fingers[1:])
    
    def _detect_thumbs_down(self, landmarks: List[Dict]) -> bool:
        # Inverted thumb logic
        fingers = self._get_finger_status(landmarks)
        return not fingers[0] and not any(fingers[1:])
    
    def _detect_peace_sign(self, landmarks: List[Dict]) -> bool:
        fingers = self._get_finger_status(landmarks)
        return not fingers[0] and fingers[1] and fingers[2] and not fingers[3] and not fingers[4]
    
    def _detect_ok_sign(self, landmarks: List[Dict]) -> bool:
        # Simplified OK detection - thumb and index finger close together
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        distance = np.sqrt((thumb_tip['x'] - index_tip['x'])**2 + (thumb_tip['y'] - index_tip['y'])**2)
        return distance < 0.05
    
    def _detect_fist(self, landmarks: List[Dict]) -> bool:
        fingers = self._get_finger_status(landmarks)
        return not any(fingers)
    
    def _detect_open_palm(self, landmarks: List[Dict]) -> bool:
        fingers = self._get_finger_status(landmarks)
        return all(fingers)
    
    def _detect_pointing(self, landmarks: List[Dict]) -> bool:
        fingers = self._get_finger_status(landmarks)
        return not fingers[0] and fingers[1] and not any(fingers[2:])
    
    def draw_landmarks(self, image: np.ndarray, detection_result: Dict) -> np.ndarray:
        """
        Draw hand landmarks on the image
        """
        if detection_result['hands_detected'] > 0:
            # Convert landmarks back to MediaPipe format for drawing
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_image)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        return image