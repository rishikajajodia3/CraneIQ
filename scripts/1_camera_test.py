import cv2
from utils.hand_tracker import get_hands_model, get_landmarks, draw_landmarks

# Initialize MediaPipe Hands
hands_model = get_hands_model()

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Starting CraneIQ Hand Tracking...")
print("Press 'q' to quit.\n")

hand_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # Mirror the camera for a natural view
    frame = cv2.flip(frame, 1)

    # Detect hand landmarks
    landmarks, hand_landmarks = get_landmarks(frame, hands_model)

    if landmarks:
        # Draw the hand skeleton
        draw_landmarks(frame, hand_landmarks)

        # Print only when a hand is first detected
        if not hand_detected:
            print(f"Hand detected! Extracting {len(landmarks)} landmark values.")
            hand_detected = True
    else:
        # Print only when the hand disappears
        if hand_detected:
            print("Hand lost.")
            hand_detected = False

        # Display a helpful message on the video
        cv2.putText(
            frame,
            "No hand detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    # Show the camera feed
    cv2.imshow("CraneIQ - Hand Tracking", frame)

    # Quit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()