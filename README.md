# Webcam-Controlled Robotic Hand

A robotic hand that mirrors your real hand's finger bend movements in real-time through a webcam. 

**Demo:** 

https://github.com/user-attachments/assets/15c34cb0-4124-4804-8bd9-6a9c450d029c





## What it does

- Tracks your hand through a webcam and locates 21 hand landmarks per frame.
- Computes each finger's bend angle/thumbs distance ratio from pinky from the landmarks
- Maps each finger's bend onto its servo's calibrated range and drives five servos so the robot hand mirrors yours — proportionally, not just open/closed.
- Smooths the motion (exponential smoother + send-i4f-changed guard) for stable, responsive control at ~20–30 FPS.

## Tech stack

- **Python** — vision, geometry, and control (`hand.py`)
- **MediaPipe** — hand landmark detection
- **OpenCV** — webcam capture and display
- **NumPy** — vector math and finger-servo range mapping
- **pyserial** — sends servo commands to the Arduino
- **Arduino (C++)** — custom `hand_firmware.ino` with a serial command protocol that recieves comma-separated of angles per frame, does safety climping and writes the angles to servos
- **Hardware** — ELEGOO Uno R3, 5× micro servos in LewanSoul/Hiwonder uHand, external 5V supply, breadboard

## Per frame Pipeline 

```
webcam → MediaPipe (21 landmarks) → per-finger bend angle → map to servo range
       → smooth → command over serial → Arduino firmware → servos → hand
```

## Running it

```bash
python mirror_hand.py
```

(Requires the Arduino connected with `hand_firmware.ino` loaded, servos powered externally, and the webcam available)
