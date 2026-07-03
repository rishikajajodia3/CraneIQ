import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

def get_hands_model():
    """Creates and returns a MediaPipe Hands model instance."""
    return mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

def get_landmarks(frame, hands_model):
    """
    Takes a video frame and a hands model.
    Returns (landmarks_list, hand_landmarks_object) or (None, None) if no hand detected.
    landmarks_list is a flat list of 63 values: [x1,y1,z1, x2,y2,z2, ... x21,y21,z21]
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands_model.process(rgb)

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.extend([lm.x, lm.y, lm.z])
        return landmarks, hand_landmarks

    return None, None

def draw_landmarks(frame, hand_landmarks):
    """Draws the hand skeleton overlay on the frame."""
    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)