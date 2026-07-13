#include <Servo.h>

const int NUM_SERVOS = 5;

// ORDER: thumb, index, middle, ring, pinky
Servo servos[NUM_SERVOS];

// which Arduino pin each servos signal wire is plugged into 
const int PINS[NUM_SERVOS] = {2, 3, 4, 5, 6};

// safe angle limits per finger (how far they can open and close)
const int OPEN_ANGLE[NUM_SERVOS]   = {10, 140, 140, 140, 140};
const int CLOSED_ANGLE[NUM_SERVOS] = { 140,  50,  45,  50,  50};

// test function: openHand: send every finger to its OPEN angle
void openHand() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].write(OPEN_ANGLE[i]);
  }
  Serial.println("openHand");
}

// test function: fist: send every finger to its CLOSED angle
void fist() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].write(CLOSED_ANGLE[i]);
  }
  Serial.println("fist");
}

// Non-blocking sweep state 
// "How far along the open->closed journey are we?" 0.0 = fully open, 1.0 = fully closed
float progress = 0.0;
float direction = 1.0; // +1 closing, -1 opening
const float STEP = 0.02; // how much progress moves each tick
const unsigned long INTERVAL = 20; // ms between ticks 

unsigned long lastMoveTime = 0; // when we last nudged the servos

// Move every finger to a blended angle between OPEN and CLOSED, based on `progress` (0.0=open, 1.0=closed)
void applyProgress() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    int angle = OPEN_ANGLE[i] + (int)(progress * (CLOSED_ANGLE[i] - OPEN_ANGLE[i]));
    servos[i].write(angle);
  }
}

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(PINS[i]);
  }

  progress = 0.0; // start open
  applyProgress();
}

void loop() {
  unsigned long now = millis();

  // Only move the servos every INTERVAL ms 
  if (now - lastMoveTime >= INTERVAL) {
    lastMoveTime = now;

    // advance the sweep
    progress += direction * STEP;

    // bounce at the ends
    if (progress >= 1.0) {
      progress = 1.0;
      direction = -1.0;   // now open back up
    } else if (progress <= 0.0) {
      progress = 0.0;
      direction = 1.0;    // now close again
    }

    applyProgress();
  }
}

