/*
 * angle_tester.ino  — Phase 6a range finder
 * -----------------------------------------
 * ONE servo at a time, signal wire on pin 9 (same as Phase 5).
 * Type an angle (0-180) in the Serial Monitor + Enter -> servo goes there.
 *
 * HOW TO USE:
 *   1. Open Serial Monitor, set baud to 9600, line ending to "Newline".
 *   2. It starts at 90 (a safe middle).
 *   3. Type angles in SMALL steps (e.g. 90, 85, 80...) toward OPEN.
 *      Watch the finger. The instant it STOPS moving or the servo
 *      BUZZES / STRAINS / gets warm -> back off ~5 degrees and write
 *      that number down as the safe limit for that direction.
 *   4. Do the same the other direction for CLOSED.
 *   5. Whichever number uncurls the finger is OPEN, the other is CLOSED,
 *      regardless of which is higher. Trust your eyes, not the labels.
 *
 * SAFETY: never leave it sitting on a buzzing angle. A stalled servo
 * pulls max current and heats up. If it buzzes, immediately type a
 * safe angle (like 90) to relieve it.
 */

#include <Servo.h>

Servo myservo;

const int SERVO_PIN = 9;
int currentAngle = 90;   // safe starting middle

void setup() {
  Serial.begin(9600);
  myservo.attach(SERVO_PIN);
  myservo.write(currentAngle);
  Serial.println("=== Phase 6a Angle Tester ===");
  Serial.print("Started at ");
  Serial.print(currentAngle);
  Serial.println(" degrees.");
  Serial.println("Type an angle 0-180 and press Enter.");
  Serial.println("Creep in small steps. Stop the instant it buzzes or stalls.");
}

void loop() {
  if (Serial.available() > 0) {
    int requested = Serial.parseInt();   // reads the number you typed

    // ignore stray parses (parseInt returns 0 on junk/newline-only)
    // if you really want 0 degrees, type it twice or just trust the clamp.
    if (requested >= 0 && requested <= 180) {
      currentAngle = requested;
      myservo.write(currentAngle);

      Serial.print("-> moved to ");
      Serial.print(currentAngle);
      Serial.println(" degrees");
    } else {
      Serial.print("ignored (out of 0-180): ");
      Serial.println(requested);
    }

    // clear any leftover characters in the buffer (e.g. the newline)
    while (Serial.available() > 0) {
      Serial.read();
    }
  }
}
