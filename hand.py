import cv2
import mediapipe as mp
import numpy as np
import serial
import time

# the Arduino on this particular USB port, (port on the left side closest to user)
USB_PORT = "/dev/cu.usbmodem11401"
# baud rate is how fast bits travel so speed of serial communication (needs to be set to same speed as Arduino firmware)
BAUD = 9600

# mediapipe landmarks for each finger's 3 points (base, joint, tip)
FINGERS = {
    "thumb":  (1, 2, 4),
    "index":  (5, 6, 8),
    "middle": (9, 10, 12),
    "ring":   (13, 14, 16),
    "pinky":  (17, 18, 20),
}
FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]

# the mapping from webcam hand bend to servo angle
    # the ANGLE your hand produces when open vs closed on webcam
ANGLE_OPEN   = {"thumb": 176, "index": 178, "middle": 179, "ring": 177, "pinky": 177}
ANGLE_CLOSED = {"thumb": 146, "index": 6,   "middle": 11,  "ring": 22,  "pinky": 36}
    # SERVO angle each finger needs for open vs closed
SERVO_OPEN   = {"thumb": 10,  "index": 140, "middle": 140, "ring": 140, "pinky": 140}
SERVO_CLOSED = {"thumb": 165, "index": 50,  "middle": 45,  "ring": 50,  "pinky": 50}

# Thumb uses a distance RATIO, not an angle
    # measure thumb by distance not joit angle to avoid confusion when hyperextending thumb
THUMB_RATIO_OPEN = 2.0 # thumb out/open
THUMB_RATIO_CLOSED = 0.8 # thumb tucked across palm

# Map a finger's measured angle to its servo angle
def map_to_servo(name, angle):
    # np.interp does a linear map from the finger's [open, closed] angle range onto the servo's [open, closed] range.
    servo = np.interp(angle,
        [ANGLE_CLOSED[name], ANGLE_OPEN[name]],
        [SERVO_CLOSED[name], SERVO_OPEN[name]],
    )
    return int(servo)

# geometry --> where landmarks measure the angle
def finger_angle(a, b, c):
    """
    Angle (degrees) at point landmark joint (b), formed by vectors b->a and b->c.
        a (base), b (joint), c (tip)
      - abs + fold into 180
    a, b, c are (x, y) numpy arrays.
    """
    # arctan2 gives each arm's direction as the angle a line points.
    # arm b->c
    angle_bc = np.arctan2(c[1] - b[1], c[0] - b[0])
    # arm b->a
    angle_ba = np.arctan2(a[1] - b[1], a[0] - b[0])

    # to get angle: difference between the two arms of the joint
    radians = angle_bc - angle_ba
    # get the absolute value and convert to degrees
    angle = np.abs(np.degrees(radians))

    # fold anything over 180 back down (an angle and its reflex are the same bend)
    if angle > 180.0:
        angle = 360.0 - angle

    return angle

# geomerty -> thumb tuck
def thumb_openness(points):
    """
    Measure thumb tuck by distance, not joint angle.
    - thumb tip = landmark 4, pinky base = landmark 17
    - when thumb is OUT (open), tip is far from pinky base
    - when thumb TUCKS across the palm (closed), tip moves closer
    Normalized by hand width (landmark 5 to 17) so it doesn't change with how close your hand is to the camera.
    Returns a ratio: bigger = more open, smaller = more closed.
    """
    thumb_tip = points[4]
    pinky_base = points[17]
    index_base = points[5]

    # distance from thumb tip to the pinky side of the palm
    tip_to_pinky = np.linalg.norm(thumb_tip - pinky_base)

    # hand width across the knuckles, used to normalize for scale
    hand_width = np.linalg.norm(index_base - pinky_base)

    if hand_width == 0:
        return 1.0

    return tip_to_pinky / hand_width

# vision set up and arduino connection
def main():
    # open serial connection to the Arduino on port and with baud rate
    print(f"Opening {USB_PORT} at {BAUD} baud...")
    arduino = serial.Serial(USB_PORT, BAUD, timeout=1)
    time.sleep(2) # wait for the board to reboot after the port opens
    print("Arduino ready.\n")

    # Smoothing of hand motion
        # jitter comes from  MediaPipe's per-frame tracking wobbling a few degrees every frame even when your hand is still, plus the occasional glitch frame
        # Each wobble gets sent straight to the servos
        # blend each new reading with the previous sent value using a single weight
    smoothed_servo_angle = {name: None for name in FINGER_NAMES} # smoothed holds each finger's running angle value
    ALPHA = 0.5 # weight we will smooth by 

    # Smoothing of hand motion
        # only send a new angles if a finger moved more than this many degrees
    MOVE_THRESHOLD = 2
    last_sent_frame = None # the list of servo angles we last actually sent

    # hand module
    mp_hands = mp.solutions.hands
    # helper that draws skeleton overlay on hand in webcam
    mp_draw = mp.solutions.drawing_utils
    # hands loads the pretrained neural network
    hands = mp_hands.Hands(max_num_hands=1,
                       model_complexity=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.8)
    # Open the default camera (0 = your built-in webcam)
    cap = cv2.VideoCapture(0)

    while True:
        # Grab one frame from the web cam! 
            # the frame is a grid of numbers 
        ok, frame = cap.read()
        if not ok:
            continue
        
        # OpenCV gives BGR but MediaPipe wants RGB so convert
            # rgb is a frame which is a just grid of numbers
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run the hand model on this frame
            # the hand model is a neural network that has been trained and knows what hands look like and where the 21 landmarks sit
            # .process is looking at your rgb grid/frame and trying to find where the hand is and locate the 21 landmarks!
                # function on the hand model!
            # resulst holds what your model found 
        results = hands.process(rgb_frame)

        # If a hand was found, draw its 21 landmarks
            # multi_hand_landmarks — the list of detected hands (grab first hand), each with its 21 landmark coordinates
            # if no hand in the frame results is empty/none 
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            # builds a list where each landmark is a 2D numpy array of its (x, y) coordinates
                # easier to do math! 
            points = [np.array([lm.x, lm.y]) for lm in hand_landmarks.landmark]

            on_screen_y = 30 # for on screen debugging text display
            # per finger loop!
            for finger in FINGER_NAMES:
                if finger == "thumb":
                    # thumb: distance ratio, mapped to its servo angle range
                    ratio = thumb_openness(points)
                    servo_angle_raw = int(np.interp(
                        ratio,
                        [THUMB_RATIO_CLOSED, THUMB_RATIO_OPEN],
                        [SERVO_CLOSED["thumb"], SERVO_OPEN["thumb"]],
                    ))
                    raw_reading_from_webcam = ratio
                else: 
                    base, joint, tip = FINGERS[finger]
                    # for each finger, get its three landmakrs (joint, base, tip) and compute the angle bend
                    angle = finger_angle(points[base], points[joint], points[tip])
                    # map the finger's measured angle to the servo angle
                    servo_angle_raw = map_to_servo(finger, angle)
                    raw_reading_from_webcam = angle

                # smooth out by blend 50% new angle reading with 50% previous angle reading
                if smoothed_servo_angle[finger] is None:
                    smoothed_servo_angle[finger] = servo_angle_raw
                else:
                    smoothed_servo_angle[finger] = ALPHA * servo_angle_raw + (1 - ALPHA) * smoothed_servo_angle[finger]

                # for on screen webcam display, show mapping from finger angle to servo angle
                text = f"{finger}: angle {raw_reading_from_webcam:2f} -> servo {int(smoothed_servo_angle[finger]):3d}"
                cv2.putText(frame, text, (10, on_screen_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                on_screen_y += 28
            
            # decide whether this frame is different enough to send to arduino
            if last_sent_frame is None:
                frame_changed_by_threshold = True # first frame, always send
            else:
                # True if ANY finger moved more than the threshold (to avoid jittery movement)
                frame_changed_by_threshold = any(
                    abs(smoothed_servo_angle[finger] - last_sent_frame[i]) > MOVE_THRESHOLD
                    for i, finger in enumerate(FINGER_NAMES)
                )
            
            # send command of all angles for each finger that we calculated to Arduino
                # hand_firmware will handle receiving the string of angles and moving the servos
            if frame_changed_by_threshold:
                all_angles = ",".join(str(int(smoothed_servo_angle[finger])) for finger in FINGER_NAMES)
                arduino.write((all_angles + "\n").encode())
                print(all_angles)
                last_sent_frame = [int(smoothed_servo_angle[finger]) for finger in FINGER_NAMES]          # remember what we sent

                cv2.putText(frame, f"send: {all_angles}", (10, on_screen_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
            else:
                cv2.putText(frame, "(holding)", (10, on_screen_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

            # draw the hand skeleton on the webcam frame
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Mirror hand (press q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()
    print("Port closed.")



if __name__ == "__main__":
    main()