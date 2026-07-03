"""
2_collect_data.py

Records labeled hand-landmark training data for the CraneIQ gesture classifier.

For each gesture in GESTURES, this script:
  1. Shows a countdown so you can get your hand in position
  2. Records landmark frames for RECORD_SECONDS
  3. Writes each frame as a row [63 landmark values, label] to gesture_data.csv

Run this once per "session" (e.g. once per teammate / once per angle) and it
will APPEND to the same CSV, so you can build up a bigger dataset across
multiple people and multiple recording sessions.
"""

import cv2
import csv
import os
import time
import sys

# Make sure we can import utils/ regardless of where this is run from
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.hand_tracker import get_hands_model, get_landmarks, draw_landmarks

# ---- CONFIG ----
GESTURES = ["STOP", "BOOM_UP", "BOOM_DOWN", "SWING_LEFT", "SWING_RIGHT", "HOIST"]
RECORD_SECONDS = 15          # how long to record each gesture per session
COUNTDOWN_SECONDS = 3        # prep time before each gesture starts recording
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "gesture_data.csv")

NUM_LANDMARKS = 21
# session_id groups all rows from one run of this script together, so training
# can split by session instead of by row (prevents near-duplicate frames from
# the same recording leaking into both train and test sets)
HEADER = [f"lm{i}_{axis}" for i in range(NUM_LANDMARKS) for axis in ("x", "y", "z")] + ["label", "session_id"]


def ensure_csv_header(path):
    """Create the CSV with a header row if it doesn't exist yet."""
    file_exists = os.path.isfile(path)
    if not file_exists:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)


def countdown_on_frame(cap, hands_model, seconds, message):
    """Show a countdown overlay on the live camera feed before recording."""
    start = time.time()
    while time.time() - start < seconds:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)

        remaining = int(seconds - (time.time() - start)) + 1
        cv2.putText(frame, message, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"Starting in {remaining}...", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("CraneIQ - Data Collection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False
    return True


def record_gesture(cap, hands_model, label, seconds, csv_writer, session_id):
    """Record landmark frames for one gesture and write them to the CSV."""
    start = time.time()
    frames_written = 0
    frames_skipped = 0

    while time.time() - start < seconds:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)

        landmarks, hand_landmarks = get_landmarks(frame, hands_model)

        if landmarks:
            draw_landmarks(frame, hand_landmarks)
            csv_writer.writerow(landmarks + [label, session_id])
            frames_written += 1
        else:
            frames_skipped += 1
            cv2.putText(frame, "No hand detected - skipping frame", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        remaining = int(seconds - (time.time() - start)) + 1
        cv2.putText(frame, f"Recording: {label}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Time left: {remaining}s", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("CraneIQ - Data Collection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"  {label}: wrote {frames_written} frames, skipped {frames_skipped} (no hand detected)")


def main():
    ensure_csv_header(CSV_PATH)

    # Each run of this script = one "session". Tagging rows with a session_id
    # lets training keep whole sessions together in either train or test,
    # instead of randomly splitting near-identical consecutive frames.
    person = input("Who's recording right now? (e.g. your name, used to tag this session): ").strip() or "unknown"
    session_id = f"{person}_{int(time.time())}"

    hands_model = get_hands_model()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("CraneIQ Data Collection")
    print(f"Session ID: {session_id}")
    print(f"Gestures to record: {GESTURES}")
    print(f"Each gesture records for {RECORD_SECONDS}s after a {COUNTDOWN_SECONDS}s countdown.")
    print("Press 'q' at any point to stop early.\n")

    with open(CSV_PATH, "a", newline="") as f:
        csv_writer = csv.writer(f)

        for gesture in GESTURES:
            proceed = countdown_on_frame(cap, hands_model, COUNTDOWN_SECONDS, f"Get ready: {gesture}")
            if not proceed:
                break
            record_gesture(cap, hands_model, gesture, RECORD_SECONDS, csv_writer, session_id)

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone. Data saved to {os.path.abspath(CSV_PATH)}")


if __name__ == "__main__":
    main()