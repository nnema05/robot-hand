"""
finger_angles_test.py
------------------------------------------
Print-only, no servos
Just watch each finger's bend angle live as you move your hand
To confirm the math is sane before wiring it to servo commands.

Straight finger -> angle near 180
Fully curled -> angle small (40-ish)

Press 'q' in the video window to quit.
"""

import cv2
import mediapipe as mp
import numpy as np

# Which landmarks form each finger's angle
# For each finger: (base, joint, tip). We measure the angle AT the
# joint (middle point). Same landmark numbers as the plan.
FINGERS = {
    "thumb":  (1, 2, 4), 
    "index":  (5, 6, 8),
    "middle": (9, 10, 12),
    "ring":   (13, 14, 16),
    "pinky":  (17, 18, 20),
}

def finger_angle(a, b, c):
    """
    Angle (degrees) at point landmark joint (b), formed by vectors b->a and b->c.
        a (base), b (joint), c (tip)
      - abs + fold into 180
      - dot product method to find the angles: cos(angle) = (BA . BC) / (|BA| * |BC|)
    """
    ba = a - b # vector from joint to base
    bc = c - b # vector from joint to tip

    # dot product of the two vectors
    dot = np.dot(ba, bc)

    # magnitudes (lengths) of each vector
    mag_ba = np.linalg.norm(ba)
    mag_bc = np.linalg.norm(bc)

    # guard against divide-by-zero if two landmarks land on top of each other
    if mag_ba == 0 or mag_bc == 0:
        return 180.0

    cosine = dot / (mag_ba * mag_bc)
    # floating point can push this outside [-1, 1] clamp so its safe
    cosine = np.clip(cosine, -1.0, 1.0)

    angle = np.degrees(np.arccos(cosine))
    return angle


def main():
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    cap = cv2.VideoCapture(0)

    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        # mirror so moving your right hand right moves it right on screen
        frame = cv2.flip(frame, 1)

        # MediaPipe wants RGB, OpenCV gives BGR
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            # pull all 21 landmarks into a simple list of (x, y) arrays.
            pts = [np.array([lm.x, lm.y]) for lm in hand.landmark]

            # compute + print each finger's angle
            y = 30
            for name, (base, joint, tip) in FINGERS.items():
                angle = finger_angle(pts[base], pts[joint], pts[tip])

                text = f"{name}: {angle:5.0f}"
                cv2.putText(frame, text, (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y += 30

            # draw the skeleton so you can see tracking
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Finger angles (press q to quit)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()