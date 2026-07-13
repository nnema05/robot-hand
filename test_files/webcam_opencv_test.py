import cv2

# Open the default camera (0 = your built-in webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open camera.")
    exit()

print("Camera opened! Press 'q' in the video window to quit.")

while True:
    # Grab one frame from the web cam! 
        # the frame is a grid of numbers 
    ok, frame = cap.read()
    if not ok:
        print("ERROR: Couldn't read a frame.")
        break

    # Show it in a window
    cv2.imshow("Webcam Test", frame)

    # Wait 1ms for a keypress, quit if its q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()