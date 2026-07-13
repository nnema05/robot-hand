import cv2
import mediapipe as mp

# MediaPipe's hand model + drawing helpers
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,           # track one hand
    min_detection_confidence=0.7
)

cap = cv2.VideoCapture(0)
print("Show your hand! Press 'q' to quit.")

while True:
    # Grab one frame from the web cam! 
        # the frame is a grid of numbers 
    ok, frame = cap.read()
    if not ok:
        break

    # OpenCV gives BGR; MediaPipe wants RGB (remember this!)
        # rgb is a frame 0 that grid of numbers, now in RGB order!
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run the hand model on this frame
        # the hand model is a neural network that has been trained and knows what hands look like and where the 21 landmarks sit
        # .process is looking at your rgb grid/frame and trying to find where the hand is and locate the 21 landmarks!
            # function on the hand model!
        # resulst holds what your model found 
    results = hands.process(rgb)

    # If a hand was found, draw its 21 landmarks
        # multi_hand_landmarks — the list of detected hands, each with its 21 landmark coordinates
        # if no hand in the frame this is empty/none! 
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 0, 255), thickness=4, circle_radius=6),   # the dots
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=3)                     # the connecting lines
            )

    cv2.imshow("Hand Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()