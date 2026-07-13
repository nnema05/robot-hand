# See if Python can talk to Arduino firmware over serial

import serial
import time

# the Arduino on this particular USB port, (port on the left side closest to user)
USB_PORT = "/dev/cu.usbmodem11401"
# baud rate is how fast bits travel so speed of serial communication (needs to be set to same speed as Arduino firmware)
BAUD = 9600

def main(): 
    # open up serial port
    print(f"Opening {USB_PORT} at {BAUD} baud...")
    arduino = serial.Serial(USB_PORT, BAUD, timeout=1)

    # opening the port resets the Arduio, so wait for it to finish booting up
    time.sleep(2)

    print("Arduino ready.\n")

    # read and print arduino ouput during set up so we can check if alive
    while arduino.in_waiting > 0:
        print("  arduino:", arduino.readline().decode().strip())

    # send some commands to the Arduino firmware
    commands = ["0:90", "0:10", "0:140", "10,10,10,10,10", "NEUTRAL"]

    for cmd in commands:
        print(f"sending: {cmd}")
        # .encode sends as bytes!
            # add /n bc thats what firmware reads till
        arduino.write((cmd + "\n").encode()) 
        time.sleep(1)  

        # read back whatever the firmware echoed
        while arduino.in_waiting > 0:
            print("  arduino:", arduino.readline().decode().strip())
        print()

    arduino.close()
    print("Done. Port closed.")

if __name__ == "__main__":
    main()                   
