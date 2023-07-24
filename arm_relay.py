import serial
import time
import numpy as np
import RPi.GPIO as GPIO
import os
import subprocess

# Read levelpoints.txt
with open('levelpoints.txt', 'r') as f:
    level_points = [float(line.strip()) for line in f]
print("Loaded level points: ", level_points)

# Create a new directory with timestamp
timestamp = time.strftime("%Y%m%d-%H%M%S")
os.makedirs('input/' + timestamp, exist_ok=True)

# TFLuna Lidar
ser = serial.Serial("/dev/tfluna_usb", 115200, timeout=0)  # mini UART serial device
print("TFLuna Lidar Serial is setup")

# Close and reopen the serial port
if ser.isOpen():
    print('Closing and reopening serial port.')
    ser.close()
    time.sleep(1)  # Wait a bit to ensure the port has closed

ser.open()
if ser.isOpen():
    print('Serial port is open.')
else:
    print('Failed to open serial port.')
    sys.exit(1)  # Exit the script if the serial port didn't open
    
# Relay pins
relay_pin1 = 21  # Pin 23 is for moving up
relay_pin2 = 20  # Pin 22 is for moving down
flash_pin = 24  # Pin 23 is for flash light

# Setup GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin1, GPIO.OUT)
GPIO.setup(relay_pin2, GPIO.OUT)
GPIO.setup(flash_pin, GPIO.OUT)

GPIO.output(relay_pin1, GPIO.LOW)
GPIO.output(relay_pin2, GPIO.LOW)
GPIO.output(flash_pin, GPIO.LOW)
print("GPIO pins are setup")

# Read ToF data from TF-Luna
def read_tfluna_data():
    while True:
        counter = ser.in_waiting  # Count the number of bytes of the serial port
        if counter > 8:
            bytes_serial = ser.read(9)  # Read 9 bytes
            ser.reset_input_buffer()  # Reset buffer

            if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:  # Check first two bytes
                distance = bytes_serial[2] + bytes_serial[3] * 256  # Distance in next two bytes
                return distance / 100.0  # We're only interested in distance

if ser.isOpen() == False:
    ser.open()  # Open serial port if not open
print("Serial port is open")

try:
    for level in level_points:
        print("Processing level: ", level)
        loop_start_time = time.time()  # start time of the loop
        while True:
            distance = read_tfluna_data()  # Read current distance
            print("Read distance: ", distance)  # print the distance being read
            if abs(distance - level) <= 0.02:  # 0.02m threshold
                GPIO.output(relay_pin1, GPIO.LOW)
                GPIO.output(relay_pin2, GPIO.LOW)
                GPIO.output(flash_pin, GPIO.HIGH)
                print("Reached target distance. Relays are turned off.")
                
                # Run gphoto2 command and wait for it to finish
                subprocess.run(['gphoto2', '--capture-image-and-download', '--filename', 'input/' + timestamp + '/%Y%m%d%H%M%S.jpg'], check=True)
                GPIO.output(flash_pin, GPIO.LOW)
                break
            elif distance < level:  # If current distance is less than target, move up
                GPIO.output(relay_pin1, GPIO.HIGH)
                GPIO.output(relay_pin2, GPIO.LOW)
            else:  # If current distance is more than target, move down
                GPIO.output(relay_pin1, GPIO.LOW)
                GPIO.output(relay_pin2, GPIO.HIGH)
            if time.time() - loop_start_time > 30:  # timeout of 30 seconds
                print("Timeout error: Distance to level not achieved in time.")
                break

            time.sleep(0.1)  # Wait a bit before the next reading

    # After reaching the last level point, move to the first one
    print("Moving to the first level point...")
    while True:
        distance = read_tfluna_data()
        print("Read distance: ", distance)
        if abs(distance - level_points[0]) <= 0.02:
            GPIO.output(relay_pin1, GPIO.LOW)
            GPIO.output(relay_pin2, GPIO.LOW)
            print("Reached first level point. Relays are turned off.")
            break
        elif distance < level_points[0]:  # If current distance is less than first level, move up
            GPIO.output(relay_pin1, GPIO.HIGH)
            GPIO.output(relay_pin2, GPIO.LOW)
        else:  # If current distance is more than first level, move down
            GPIO.output(relay_pin1, GPIO.LOW)
            GPIO.output(relay_pin2, GPIO.HIGH)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Interrupt received. Closing serial port.")
    ser.close()  # Close serial port when Ctrl+C is pressed

finally:
    # Turn off all relays
    GPIO.output(relay_pin1, GPIO.LOW)
    GPIO.output(relay_pin2, GPIO.LOW)
    GPIO.output(flash_pin, GPIO.LOW)
    print("Script terminated. All relays are turned off.")
    
    GPIO.cleanup()  # Clean up GPIO states
    print("GPIO cleanup done.")
