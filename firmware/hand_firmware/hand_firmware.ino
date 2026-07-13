/*
Serial command listener --> mini Firmata
Read text over serial then arduino acts: 
Protocol: 
  - "3:90" = servo 3, angle 90
  - "90,140,140,50,50"  -> all 5 servos at once (thumb..pinky order)
  - "NEUTRAL"              all servos to a safe neutral
- 0 based 0 = thumb, 4 = pinky
*/

#include <Servo.h>

const int NUM_SERVOS = 5;

// ORDER: thumb, index, middle, ring, pinky
Servo servos[NUM_SERVOS];

const int PINS[NUM_SERVOS] = {2, 3, 4, 5, 6};
// tested and verified
const int OPEN_ANGLE[NUM_SERVOS] = {10, 140, 140, 140, 140};
const int CLOSED_ANGLE[NUM_SERVOS] = {165,  50,  45,  50,  50};

// safe neatural for each one!
const int NEUTRAL_ANGLE[NUM_SERVOS] = { 90,  90,  90,  90,  90};

// helper: 
// bounds check, clamp angle between lower or higher of open or close angle!
      // min max to handle the fact that for thumb is the open angle is low number and close angle is high number (inverted compared to other fingers)
int clampToRange(int servoNum, int angle) {
  int lo = min(OPEN_ANGLE[servoNum], CLOSED_ANGLE[servoNum]);
  int hi = max(OPEN_ANGLE[servoNum], CLOSED_ANGLE[servoNum]);
  // contrain pulls angle up to lo if below, down to hi if above 
  return constrain(angle, lo, hi);
}

// helper : move one servo 
void moveServo(int servoNum, int angle) {
  angle = clampToRange(servoNum, angle);
  servos[servoNum].write(angle);
}

// helper: all servos to neutral 
void goNeutral() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    moveServo(i, NEUTRAL_ANGLE[i]);
  }
  Serial.println("NEUTRAL ANGLE");
}

// helper: handle a single servo command 
void handleSingleServoCommand(String command) {
  int colon = command.indexOf(':');
  int servoNum = command.substring(0, colon).toInt();
  int angle = command.substring(colon + 1).toInt();

  if (servoNum < 0 || servoNum >= NUM_SERVOS) {
    Serial.print("invalid servo: ");
    Serial.println(servoNum);
    return;
  }

  moveServo(servoNum, angle);

  Serial.print("servo ");
  Serial.print(servoNum);
  Serial.print(" -> ");
  Serial.println(clampToRange(servoNum, angle));
}

// helper: handle a servo command for all servos
  // "90,140,140,50,50" --> pulling out comma-separated chunks, one per servo
void handleAllServoCommand(String command) {
  int start = 0; // index of beginning of current number

  // find angle for each servo one by one and move
  for (int i = 0; i < NUM_SERVOS; i++) {
    // find the next comma after start index
      // returns -1 if no more commans
    int comma = command.indexOf(',', start);

    String one_angle;
    if (comma == -1) {
      // last number: take everything from start to the end
      one_angle = command.substring(start);
    } else {
      // take from start up to (not including) the comma
      one_angle = command.substring(start, comma);
    }

    int angle = one_angle.toInt();
    moveServo(i, angle);

    // if out of commas early, stop (short message)
    if (comma == -1) break;
    start = comma + 1;   // next number starts just after this comma
  }

  Serial.print("all servos command -> ");
  Serial.println(command);
}


void setup() {
  // arduino serial at baud rate 9600
    // baud rate is how fast bits travel so speed of serial communication
  Serial.begin(9600);

  // attach each servo to pin on arduino that its plugged into
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(PINS[i]);
  }

  goNeutral(); // start all fingers at neutral state
  Serial.println("Ready. Commands: 'servoNum:angle'  |  'thumb angle,index angle,middle angle,ring angle,pinky angle'  |  'NEUTRAL'");

}

void loop() {
  if (Serial.available() > 0) {
    // read everything up to new line
    String command = Serial.readStringUntil('\n');
    command.trim();

    // blank line
    if (command.length() == 0) {
      return;
    }

    if (command == "NEUTRAL") {
      goNeutral();
    } else if (command.indexOf(':') != -1) {
      handleSingleServoCommand(command);
    } else if (command.indexOf(',') != -1) {
      handleAllServoCommand(command);
    } else {
      Serial.print("unknown command: ");
      Serial.println(command);
    }
  }
}
