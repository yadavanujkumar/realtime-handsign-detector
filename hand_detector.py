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
        
        # Define comprehensive hand signs including ASL alphabet
        self.hand_signs = {
            # Basic gestures (existing)
            'thumbs_up': self._detect_thumbs_up,
            'thumbs_down': self._detect_thumbs_down,
            'peace': self._detect_peace_sign,
            'ok': self._detect_ok_sign,
            'fist': self._detect_fist,
            'open_palm': self._detect_open_palm,
            'pointing': self._detect_pointing,
            
            # ASL Alphabet A-Z
            'A': self._detect_letter_A,
            'B': self._detect_letter_B,
            'C': self._detect_letter_C,
            'D': self._detect_letter_D,
            'E': self._detect_letter_E,
            'F': self._detect_letter_F,
            'G': self._detect_letter_G,
            'H': self._detect_letter_H,
            'I': self._detect_letter_I,
            'J': self._detect_letter_J,
            'K': self._detect_letter_K,
            'L': self._detect_letter_L,
            'M': self._detect_letter_M,
            'N': self._detect_letter_N,
            'O': self._detect_letter_O,
            'P': self._detect_letter_P,
            'Q': self._detect_letter_Q,
            'R': self._detect_letter_R,
            'S': self._detect_letter_S,
            'T': self._detect_letter_T,
            'U': self._detect_letter_U,
            'V': self._detect_letter_V,
            'W': self._detect_letter_W,
            'X': self._detect_letter_X,
            'Y': self._detect_letter_Y,
            'Z': self._detect_letter_Z,
            
            # ASL Numbers 0-9
            '0': self._detect_number_0,
            '1': self._detect_number_1,
            '2': self._detect_number_2,
            '3': self._detect_number_3,
            '4': self._detect_number_4,
            '5': self._detect_number_5,
            '6': self._detect_number_6,
            '7': self._detect_number_7,
            '8': self._detect_number_8,
            '9': self._detect_number_9,
            
            # Common ASL words
            'hello': self._detect_hello,
            'goodbye': self._detect_goodbye,
            'thank_you': self._detect_thank_you,
            'please': self._detect_please,
            'sorry': self._detect_sorry,
            'love': self._detect_love,
            'yes': self._detect_yes,
            'no': self._detect_no
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
                
                # Classify hand sign with confidence
                hand_sign = self._classify_hand_sign(landmarks)
                confidence = self._calculate_confidence(landmarks, hand_sign) if hand_sign != 'unknown' else 0.3
                
                detection_result['hand_signs'].append({
                    'hand_index': idx,
                    'sign': hand_sign,
                    'confidence': confidence
                })
        
        return detection_result
    
    def _classify_hand_sign(self, landmarks: List[Dict]) -> str:
        """
        Classify the hand sign based on landmark positions with improved accuracy
        """
        if len(landmarks) < 21:
            return 'unknown'
        
        # Detection results with confidence scores
        detections = []
        
        # Test all signs and collect those that match
        for sign_name, detector_func in self.hand_signs.items():
            try:
                if detector_func(landmarks):
                    # Calculate basic confidence based on finger positions
                    confidence = self._calculate_confidence(landmarks, sign_name)
                    detections.append((sign_name, confidence))
            except Exception as e:
                # Skip signs that cause errors in detection
                continue
        
        if not detections:
            return 'unknown'
        
        # Sort by confidence and return the best match
        detections.sort(key=lambda x: x[1], reverse=True)
        return detections[0][0]
    
    def _calculate_confidence(self, landmarks: List[Dict], sign_name: str) -> float:
        """
        Calculate confidence score for a detected sign based on hand positioning
        """
        base_confidence = 0.8
        
        # Specific confidence adjustments for certain signs
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # Adjust confidence based on finger clarity
        finger_clarity = sum(1 for curl in curls if curl < 0.2 or curl > 0.8) / 5
        base_confidence += finger_clarity * 0.1
        
        # Specific sign adjustments
        if sign_name in ['A', 'S', 'T', 'E', 'M', 'N']:
            # Fist-based signs - check curl consistency
            if all(curl > 0.6 for curl in curls[1:]):
                base_confidence += 0.1
        elif sign_name in ['1', 'pointing', 'I', 'Z']:
            # Single finger signs - check isolation
            if sum(fingers) == 1:
                base_confidence += 0.15
        elif sign_name in ['V', '2', 'U', 'H', 'R']:
            # Two finger signs - check proper extension
            if sum(fingers) == 2:
                base_confidence += 0.1
        elif sign_name in ['open_palm', '5', 'hello', 'goodbye']:
            # Open hand signs - check all fingers extended
            if all(fingers):
                base_confidence += 0.1
        
        return min(0.95, max(0.6, base_confidence))
    
    def _get_finger_status(self, landmarks: List[Dict]) -> List[bool]:
        """
        Determine which fingers are extended
        Returns list [thumb, index, middle, ring, pinky]
        """
        if len(landmarks) < 21:
            return [False] * 5
            
        # Finger tip and pip landmarks
        tip_ids = [4, 8, 12, 16, 20]
        pip_ids = [3, 6, 10, 14, 18]
        
        fingers = []
        
        # Thumb (special case - check x coordinate relative to hand orientation)
        thumb_tip = landmarks[tip_ids[0]]
        thumb_pip = landmarks[pip_ids[0]]
        thumb_mcp = landmarks[2]  # Thumb MCP joint
        
        # Determine hand orientation (left or right hand)
        wrist = landmarks[0]
        thumb_side = thumb_mcp['x'] - wrist['x']
        
        if thumb_side > 0:  # Right hand
            fingers.append(thumb_tip['x'] > thumb_pip['x'])
        else:  # Left hand
            fingers.append(thumb_tip['x'] < thumb_pip['x'])
        
        # Other fingers (check y coordinate)
        for i in range(1, 5):
            if landmarks[tip_ids[i]]['y'] < landmarks[pip_ids[i]]['y']:
                fingers.append(True)
            else:
                fingers.append(False)
        
        return fingers
    
    def _get_finger_curl(self, landmarks: List[Dict]) -> List[float]:
        """
        Get finger curl levels (0.0 = fully extended, 1.0 = fully curled)
        Returns list [thumb, index, middle, ring, pinky]
        """
        if len(landmarks) < 21:
            return [0.0] * 5
            
        tip_ids = [4, 8, 12, 16, 20]
        pip_ids = [3, 6, 10, 14, 18]
        mcp_ids = [2, 5, 9, 13, 17]
        
        curls = []
        
        for i in range(5):
            tip = landmarks[tip_ids[i]]
            pip = landmarks[pip_ids[i]]
            mcp = landmarks[mcp_ids[i]]
            
            # Calculate distances
            tip_to_mcp = np.sqrt((tip['x'] - mcp['x'])**2 + (tip['y'] - mcp['y'])**2)
            pip_to_mcp = np.sqrt((pip['x'] - mcp['x'])**2 + (pip['y'] - mcp['y'])**2)
            
            # Curl ratio (closer to 0 means more extended)
            if pip_to_mcp > 0:
                curl = 1.0 - (tip_to_mcp / (pip_to_mcp * 2))
                curl = max(0.0, min(1.0, curl))  # Clamp between 0 and 1
            else:
                curl = 0.0
                
            curls.append(curl)
        
        return curls
    
    def _get_finger_angles(self, landmarks: List[Dict]) -> Dict[str, float]:
        """
        Calculate angles between finger segments for more precise detection
        """
        if len(landmarks) < 21:
            return {}
        
        angles = {}
        
        # Thumb angle
        thumb_cmc = landmarks[1]
        thumb_mcp = landmarks[2]
        thumb_ip = landmarks[3]
        thumb_tip = landmarks[4]
        
        # Index finger angle
        index_mcp = landmarks[5]
        index_pip = landmarks[6]
        index_dip = landmarks[7]
        index_tip = landmarks[8]
        
        # Calculate angles using dot product
        def angle_between_points(p1, p2, p3):
            """Calculate angle at p2 formed by p1-p2-p3"""
            v1 = np.array([p1['x'] - p2['x'], p1['y'] - p2['y']])
            v2 = np.array([p3['x'] - p2['x'], p3['y'] - p2['y']])
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.arccos(cos_angle)
            return np.degrees(angle)
        
        try:
            angles['thumb_ip'] = angle_between_points(thumb_mcp, thumb_ip, thumb_tip)
            angles['index_pip'] = angle_between_points(index_mcp, index_pip, index_dip)
            angles['index_dip'] = angle_between_points(index_pip, index_dip, index_tip)
        except:
            pass
            
        return angles
    
    def _distance_between_points(self, p1: Dict, p2: Dict) -> float:
        """Calculate Euclidean distance between two landmark points"""
        return np.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
    
    def _is_finger_touching_thumb(self, landmarks: List[Dict], finger_tip_id: int) -> bool:
        """Check if a finger tip is touching the thumb"""
        if len(landmarks) < 21:
            return False
            
        thumb_tip = landmarks[4]
        finger_tip = landmarks[finger_tip_id]
        
        distance = self._distance_between_points(thumb_tip, finger_tip)
        return distance < 0.05  # Threshold for "touching"
    
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
    
    # ASL Alphabet Detection Methods
    def _detect_letter_A(self, landmarks: List[Dict]) -> bool:
        """ASL Letter A: Fist with thumb extended to the side"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # Thumb extended, other fingers curled
        return (fingers[0] and 
                all(curls[i] > 0.7 for i in range(1, 5)))
    
    def _detect_letter_B(self, landmarks: List[Dict]) -> bool:
        """ASL Letter B: Four fingers extended upward, thumb folded across palm"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # Index through pinky extended, thumb curled
        return (not fingers[0] and curls[0] > 0.7 and
                all(fingers[i] for i in range(1, 5)))
    
    def _detect_letter_C(self, landmarks: List[Dict]) -> bool:
        """ASL Letter C: Hand curved in C shape"""
        if len(landmarks) < 21:
            return False
            
        curls = self._get_finger_curl(landmarks)
        
        # All fingers partially curled in C shape
        return all(0.3 < curl < 0.7 for curl in curls)
    
    def _detect_letter_D(self, landmarks: List[Dict]) -> bool:
        """ASL Letter D: Index finger extended, others curled, thumb touches middle finger"""
        fingers = self._get_finger_status(landmarks)
        
        # Index finger extended, others curled
        return (not fingers[0] and fingers[1] and 
                not any(fingers[i] for i in range(2, 5)) and
                self._is_finger_touching_thumb(landmarks, 12))  # Middle finger tip
    
    def _detect_letter_E(self, landmarks: List[Dict]) -> bool:
        """ASL Letter E: All fingers curled into fist, thumb curled over fingers"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # All fingers fully curled
        return all(not finger for finger in fingers) and all(curl > 0.8 for curl in curls)
    
    def _detect_letter_F(self, landmarks: List[Dict]) -> bool:
        """ASL Letter F: Index finger and thumb form circle, other fingers extended"""
        fingers = self._get_finger_status(landmarks)
        
        # Thumb and index form circle (touching), others extended
        return (self._is_finger_touching_thumb(landmarks, 8) and  # Index tip
                all(fingers[i] for i in range(2, 5)))  # Middle, ring, pinky extended
    
    def _detect_letter_G(self, landmarks: List[Dict]) -> bool:
        """ASL Letter G: Index finger and thumb extended horizontally"""
        fingers = self._get_finger_status(landmarks)
        
        # Thumb and index extended, others curled
        return (fingers[0] and fingers[1] and 
                not any(fingers[i] for i in range(2, 5)))
    
    def _detect_letter_H(self, landmarks: List[Dict]) -> bool:
        """ASL Letter H: Index and middle fingers extended horizontally"""
        fingers = self._get_finger_status(landmarks)
        
        # Index and middle extended, thumb and others curled
        return (not fingers[0] and fingers[1] and fingers[2] and
                not fingers[3] and not fingers[4])
    
    def _detect_letter_I(self, landmarks: List[Dict]) -> bool:
        """ASL Letter I: Pinky finger extended upward"""
        fingers = self._get_finger_status(landmarks)
        
        # Only pinky extended
        return (not any(fingers[i] for i in range(0, 4)) and fingers[4])
    
    def _detect_letter_J(self, landmarks: List[Dict]) -> bool:
        """ASL Letter J: Pinky finger extended and curved (motion letter, hard to detect statically)"""
        # For now, same as I but could be enhanced with motion detection
        return self._detect_letter_I(landmarks)
    
    def _detect_letter_K(self, landmarks: List[Dict]) -> bool:
        """ASL Letter K: Index and middle fingers in V shape, thumb touches middle finger"""
        fingers = self._get_finger_status(landmarks)
        
        # Index and middle extended in V, thumb touches middle finger
        return (fingers[1] and fingers[2] and 
                not fingers[3] and not fingers[4] and
                self._is_finger_touching_thumb(landmarks, 12))
    
    def _detect_letter_L(self, landmarks: List[Dict]) -> bool:
        """ASL Letter L: Thumb and index finger form L shape"""
        fingers = self._get_finger_status(landmarks)
        
        # Thumb and index extended in L shape, others curled
        return (fingers[0] and fingers[1] and 
                not any(fingers[i] for i in range(2, 5)))
    
    def _detect_letter_M(self, landmarks: List[Dict]) -> bool:
        """ASL Letter M: Thumb under first three fingers"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # First three fingers slightly curled over thumb
        return (not fingers[0] and curls[0] > 0.5 and
                all(0.3 < curls[i] < 0.7 for i in range(1, 4)) and
                curls[4] > 0.7)
    
    def _detect_letter_N(self, landmarks: List[Dict]) -> bool:
        """ASL Letter N: Thumb under first two fingers"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # First two fingers over thumb, others curled
        return (not fingers[0] and curls[0] > 0.5 and
                all(0.3 < curls[i] < 0.7 for i in range(1, 3)) and
                all(curls[i] > 0.7 for i in range(3, 5)))
    
    def _detect_letter_O(self, landmarks: List[Dict]) -> bool:
        """ASL Letter O: All fingers and thumb form circle"""
        if len(landmarks) < 21:
            return False
            
        # Check if fingertips are close together in circular formation
        thumb_tip = landmarks[4]
        fingertips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        
        # All fingertips should be close to thumb tip
        distances = [self._distance_between_points(thumb_tip, tip) for tip in fingertips]
        return all(dist < 0.08 for dist in distances)
    
    def _detect_letter_P(self, landmarks: List[Dict]) -> bool:
        """ASL Letter P: Similar to K but pointing downward"""
        fingers = self._get_finger_status(landmarks)
        
        # Index and middle extended downward, thumb touches middle
        return (fingers[1] and fingers[2] and 
                not fingers[3] and not fingers[4] and
                self._is_finger_touching_thumb(landmarks, 12))
    
    def _detect_letter_Q(self, landmarks: List[Dict]) -> bool:
        """ASL Letter Q: Thumb and index finger pointing downward"""
        fingers = self._get_finger_status(landmarks)
        
        # Thumb and index extended downward
        return (fingers[0] and fingers[1] and 
                not any(fingers[i] for i in range(2, 5)))
    
    def _detect_letter_R(self, landmarks: List[Dict]) -> bool:
        """ASL Letter R: Index and middle fingers crossed"""
        fingers = self._get_finger_status(landmarks)
        
        # Index and middle extended (crossed position hard to detect precisely)
        return (not fingers[0] and fingers[1] and fingers[2] and
                not fingers[3] and not fingers[4])
    
    def _detect_letter_S(self, landmarks: List[Dict]) -> bool:
        """ASL Letter S: Fist with thumb over fingers"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # All fingers curled, thumb over fingers
        return (all(not finger for finger in fingers[1:]) and
                all(curl > 0.7 for curl in curls[1:]) and
                curls[0] > 0.5)
    
    def _detect_letter_T(self, landmarks: List[Dict]) -> bool:
        """ASL Letter T: Thumb between index and middle finger"""
        fingers = self._get_finger_status(landmarks)
        
        # Fist with thumb positioned between index and middle
        return (all(not finger for finger in fingers[1:]) and
                self._is_finger_touching_thumb(landmarks, 6))  # Index PIP
    
    def _detect_letter_U(self, landmarks: List[Dict]) -> bool:
        """ASL Letter U: Index and middle fingers extended upward together"""
        fingers = self._get_finger_status(landmarks)
        
        # Index and middle extended, others curled
        return (not fingers[0] and fingers[1] and fingers[2] and
                not fingers[3] and not fingers[4])
    
    def _detect_letter_V(self, landmarks: List[Dict]) -> bool:
        """ASL Letter V: Index and middle fingers in V shape"""
        fingers = self._get_finger_status(landmarks)
        
        # Same as U but fingers separated (hard to distinguish statically)
        return (not fingers[0] and fingers[1] and fingers[2] and
                not fingers[3] and not fingers[4])
    
    def _detect_letter_W(self, landmarks: List[Dict]) -> bool:
        """ASL Letter W: Index, middle, and ring fingers extended"""
        fingers = self._get_finger_status(landmarks)
        
        # First three fingers extended
        return (not fingers[0] and fingers[1] and fingers[2] and 
                fingers[3] and not fingers[4])
    
    def _detect_letter_X(self, landmarks: List[Dict]) -> bool:
        """ASL Letter X: Index finger curved (hook shape)"""
        fingers = self._get_finger_status(landmarks)
        curls = self._get_finger_curl(landmarks)
        
        # Index finger partially curled, others fully curled
        return (not fingers[0] and not fingers[1] and
                0.4 < curls[1] < 0.8 and
                all(curls[i] > 0.7 for i in [0, 2, 3, 4]))
    
    def _detect_letter_Y(self, landmarks: List[Dict]) -> bool:
        """ASL Letter Y: Thumb and pinky extended (shaka sign)"""
        fingers = self._get_finger_status(landmarks)
        
        # Thumb and pinky extended, others curled
        return (fingers[0] and not fingers[1] and not fingers[2] and 
                not fingers[3] and fingers[4])
    
    def _detect_letter_Z(self, landmarks: List[Dict]) -> bool:
        """ASL Letter Z: Index finger traces Z pattern (motion letter, hard to detect statically)"""
        fingers = self._get_finger_status(landmarks)
        
        # For now, just index finger extended
        return (not fingers[0] and fingers[1] and 
                not any(fingers[i] for i in range(2, 5)))
    
    # ASL Numbers 0-9
    def _detect_number_0(self, landmarks: List[Dict]) -> bool:
        """ASL Number 0: Same as letter O"""
        return self._detect_letter_O(landmarks)
    
    def _detect_number_1(self, landmarks: List[Dict]) -> bool:
        """ASL Number 1: Index finger extended upward"""
        fingers = self._get_finger_status(landmarks)
        
        # Only index finger extended
        return (not fingers[0] and fingers[1] and 
                not any(fingers[i] for i in range(2, 5)))
    
    def _detect_number_2(self, landmarks: List[Dict]) -> bool:
        """ASL Number 2: Index and middle fingers extended (V shape)"""
        return self._detect_letter_V(landmarks)
    
    def _detect_number_3(self, landmarks: List[Dict]) -> bool:
        """ASL Number 3: Thumb, index, and middle fingers extended"""
        fingers = self._get_finger_status(landmarks)
        
        # First three fingers extended
        return (fingers[0] and fingers[1] and fingers[2] and
                not fingers[3] and not fingers[4])
    
    def _detect_number_4(self, landmarks: List[Dict]) -> bool:
        """ASL Number 4: Four fingers extended (index through pinky)"""
        fingers = self._get_finger_status(landmarks)
        
        # Four fingers extended, thumb curled
        return (not fingers[0] and all(fingers[i] for i in range(1, 5)))
    
    def _detect_number_5(self, landmarks: List[Dict]) -> bool:
        """ASL Number 5: All five fingers extended"""
        return self._detect_open_palm(landmarks)
    
    def _detect_number_6(self, landmarks: List[Dict]) -> bool:
        """ASL Number 6: Thumb and pinky touch, other fingers extended"""
        fingers = self._get_finger_status(landmarks)
        
        # Index, middle, ring extended; thumb touches pinky
        return (all(fingers[i] for i in range(1, 4)) and
                not fingers[4] and
                self._is_finger_touching_thumb(landmarks, 20))  # Pinky tip
    
    def _detect_number_7(self, landmarks: List[Dict]) -> bool:
        """ASL Number 7: Thumb and ring finger touch, others extended"""
        fingers = self._get_finger_status(landmarks)
        
        # Index, middle, pinky extended; thumb touches ring
        return (fingers[1] and fingers[2] and not fingers[3] and fingers[4] and
                self._is_finger_touching_thumb(landmarks, 16))  # Ring finger tip
    
    def _detect_number_8(self, landmarks: List[Dict]) -> bool:
        """ASL Number 8: Thumb and middle finger touch, others extended"""
        fingers = self._get_finger_status(landmarks)
        
        # Index, ring, pinky extended; thumb touches middle
        return (fingers[1] and not fingers[2] and fingers[3] and fingers[4] and
                self._is_finger_touching_thumb(landmarks, 12))  # Middle finger tip
    
    def _detect_number_9(self, landmarks: List[Dict]) -> bool:
        """ASL Number 9: Thumb and index finger touch, others extended"""
        fingers = self._get_finger_status(landmarks)
        
        # Middle, ring, pinky extended; thumb touches index
        return (not fingers[1] and all(fingers[i] for i in range(2, 5)) and
                self._is_finger_touching_thumb(landmarks, 8))  # Index finger tip
    
    # Common ASL Words
    def _detect_hello(self, landmarks: List[Dict]) -> bool:
        """ASL Hello: Open palm with slight wave motion (simplified to open palm)"""
        return self._detect_open_palm(landmarks)
    
    def _detect_goodbye(self, landmarks: List[Dict]) -> bool:
        """ASL Goodbye: Similar to hello with wave motion (simplified to open palm)"""
        return self._detect_open_palm(landmarks)
    
    def _detect_thank_you(self, landmarks: List[Dict]) -> bool:
        """ASL Thank You: Fingers start at lips and move forward (simplified to open palm)"""
        return self._detect_open_palm(landmarks)
    
    def _detect_please(self, landmarks: List[Dict]) -> bool:
        """ASL Please: Open palm making circular motion on chest (simplified to open palm)"""
        return self._detect_open_palm(landmarks)
    
    def _detect_sorry(self, landmarks: List[Dict]) -> bool:
        """ASL Sorry: Fist making circular motion on chest (simplified to fist)"""
        return self._detect_fist(landmarks)
    
    def _detect_love(self, landmarks: List[Dict]) -> bool:
        """ASL Love: Multiple fingers in specific configuration (simplified to Y sign)"""
        return self._detect_letter_Y(landmarks)
    
    def _detect_yes(self, landmarks: List[Dict]) -> bool:
        """ASL Yes: Fist with nodding motion (simplified to fist)"""
        return self._detect_fist(landmarks)
    
    def _detect_no(self, landmarks: List[Dict]) -> bool:
        """ASL No: Index and middle fingers close together like scissors (simplified to U)"""
        return self._detect_letter_U(landmarks)
    
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