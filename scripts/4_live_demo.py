import cv2
import joblib
import time
import os
import sys

# Add the project root (CraneIQ/) to Python's module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.hand_tracker import (
    get_hands_model,
    get_landmarks,
    draw_landmarks,
)
from utils.operator_input import OperatorInput
from utils.verification_engine import VerificationEngine
from utils.logger import EventLogger

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "gesture_model.pkl")
CONFIRM_FRAMES = 5  # consecutive matching frames before we "confirm" a gesture


def main():
    model = joblib.load(MODEL_PATH)
    hands_model = get_hands_model()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: could not open camera")
        return

    operator = OperatorInput()
    engine = VerificationEngine()
    logger = EventLogger()

    last_prediction = None
    stable_count = 0
    confirmed_gesture = "IDLE"
    confidence = None
    last_logged_resolution = None

    print("=== CraneIQ Live Demo ===")
    print("Press 'q' in the camera window to quit.")

    while operator.running:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        landmarks, hand_landmarks = get_landmarks(frame, hands_model)

        if landmarks:
            draw_landmarks(frame, hand_landmarks)
            pred = model.predict([landmarks])[0]
            proba = model.predict_proba([landmarks])[0]
            confidence = max(proba)

            if pred == last_prediction:
                stable_count += 1
            else:
                stable_count = 1
                last_prediction = pred

            if stable_count >= CONFIRM_FRAMES and pred != confirmed_gesture:
                confirmed_gesture = pred
                engine.register_gesture(confirmed_gesture, timestamp=time.time())

            cv2.putText(frame, f"Rigger signal: {pred} ({confidence:.2f})", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            if confirmed_gesture != "IDLE":
                confirmed_gesture = "IDLE"
                engine.register_gesture("IDLE")
            last_prediction = None
            stable_count = 0
            confidence = None
            cv2.putText(frame, "No hand detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        action, action_ts = operator.update()
        if action:
            engine.register_action(action, timestamp=action_ts)

        engine.update()
        state = engine.get_state()

        # Log only once per resolved event, not every frame it's held on screen
        if engine.has_result() and engine.resolved_time != last_logged_resolution:
            result = engine.get_result()
            logger.log(
                gesture=result["gesture"],
                confidence=confidence,
                operator_action=result["operator_action"],
                verification_state=result["verification_state"],
            )
            last_logged_resolution = engine.resolved_time

        color = (0, 255, 0) if state == "MATCH" else (0, 0, 255) if state in ("MISMATCH", "NO_ACTION") else (0, 255, 255)
        cv2.putText(frame, f"State: {state}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("CraneIQ - Rigger Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    operator.close()


if __name__ == "__main__":
    main()