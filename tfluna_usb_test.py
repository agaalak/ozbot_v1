import serial, time
import numpy as np

# TFLuna Lidar
#ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0)  # USB serial device
ser = serial.Serial("/dev/tfluna_usb", 115200, timeout=0)  # USB serial device

# Read ToF data from TF-Luna
def read_tfluna_data():
    while True:
        counter = ser.in_waiting  # Count the number of bytes of the serial port
        if counter > 8:
            bytes_serial = ser.read(9)  # Read 9 bytes
            ser.reset_input_buffer()  # Reset buffer

            if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:  # Check first two bytes
                distance = bytes_serial[2] + bytes_serial[3] * 256  # Distance in next two bytes
                strength = bytes_serial[4] + bytes_serial[5] * 256  # Signal strength in next two bytes
                temperature = bytes_serial[6] + bytes_serial[7] * 256  # Temp in next two bytes
                temperature = (temperature / 8.0) - 256.0  # Temp scaling and offset

                return distance / 100.0, strength, temperature

if ser.isOpen() == False:
    ser.open()  # Open serial port if not open

try:
    while True:
        distance, strength, temperature = read_tfluna_data()  # Read values
        print('Distance: {0:2.2f} m, Strength: {1:2.0f} / 65535 (16-bit), Chip Temperature: {2:2.1f} C'.\
                  format(distance, strength, temperature))  # Print sample data
        time.sleep(0.1)  # Wait a bit before the next reading
except KeyboardInterrupt:
    ser.close()  # Close serial port when Ctrl+C is pressed
