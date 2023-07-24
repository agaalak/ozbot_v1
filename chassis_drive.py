import cv2
import numpy as np
from roboclaw_3 import Roboclaw
import threading
import time
import subprocess

# Initialize Roboclaw
roboclaw_port = "/dev/roboclaw_usb"
print(f'Using Roboclaw at {roboclaw_port}')

rc = Roboclaw(roboclaw_port, 115200)  # Adjust the baud rate as needed
rc.Open()
address = 0x80  # Address for Roboclaw
max_speed = 60

# Variables for motor speeds, shared with the motor thread
right_speed = 0
left_speed = 0

# Flag to indicate if motors should be stopped
stop_motors = False

# Variables to store previous center y of red tag
previous_cY_red = None

def motor_thread():
    global right_speed, left_speed, stop_motors
    while True:
        if stop_motors:
            # Stop the motors
            rc.ForwardM1(address, 0)  # right motor
            rc.ForwardM2(address, 0)  # left motor

            # Run the Python script and wait for it to finish
            subprocess.run(["python3", "arm_relay.py"], check=True)

            stop_motors = False
        else:
            # Drive the motors using Roboclaw
            rc.ForwardM1(address, right_speed)  # right motor
            rc.ForwardM2(address, left_speed)   # left motor

def main():
    global right_speed, left_speed, stop_motors, previous_cY_red

    # Start the motor thread
    threading.Thread(target=motor_thread, daemon=True).start()

    # Open the video device
    cap = cv2.VideoCapture('/dev/arducam_8mp')
    if cap is None or not cap.isOpened():
        print('Unable to open video device /dev/arducam_8mp')
        exit(1)
    else:
        print('Successfully opened video device /dev/arducam_8mp')

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Error: Unable to capture video frame")
                break
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            # Convert the frame to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Define range of blue color in HSV
            lower_blue = np.array([100, 50, 50])    # Lower the hue and higher the saturation and value
            upper_blue = np.array([140, 255, 255])  # Increase the hue and saturation range

            # Threshold the HSV image to get only blue colors
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

            # Find contours for blue
            contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw blue contours
            cv2.drawContours(frame, contours_blue, -1, (255,0,0), 1)

            # Check if any contours were found for blue
            if contours_blue:
                # Find the largest contour
                largest_contour_blue = max(contours_blue, key=cv2.contourArea)

                # Set a minimum contour area threshold
                min_contour_area = 600  # Adjust as needed

                # Calculate the area of the largest contour
                contour_area = cv2.contourArea(largest_contour_blue)

                if contour_area > min_contour_area:
                    # Calculate the center of the contour if M["m00"] is not zero
                    M_blue = cv2.moments(largest_contour_blue)
                    if M_blue["m00"] != 0:
                        cX_blue = int(M_blue["m10"] / M_blue["m00"])
                        cY_blue = int(M_blue["m01"] / M_blue["m00"])

                        # Draw a vector from the bottom center of the image to the center of the blue contour
                        height, width, _ = frame.shape
                        cv2.arrowedLine(frame, (width // 2, height), (cX_blue, cY_blue), (255, 0, 0), 1)

                        # Calculate motor speeds based on the position of the blue object
                        right_speed = int(max_speed * cX_blue / width)
                        left_speed = int(max_speed * (width - cX_blue) / width)

                        # Check if the red tag is inside the blue contour
                        # Define range of red color in HSV
                        #lower_red1 = np.array([0, 70, 50])
                        #upper_red1 = np.array([20, 255, 255])  # Increase the hue range
                        lower_red1 = np.array([0, 100, 100])
                        upper_red1 = np.array([10, 255, 255])

                        #lower_red2 = np.array([160, 70, 50])  # Lower the hue range
                        #upper_red2 = np.array([180, 255, 255])
                        lower_red2 = np.array([170, 100, 100])
                        upper_red2 = np.array([180, 255, 255])


                        # Threshold the HSV image to get only red colors
                        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
                        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)

                        # Combine the two masks
                        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

                        # Find contours for red
                        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                        # Draw red contours
                        cv2.drawContours(frame, contours_red, -1, (0,0,255), 1)

                        # Define the minimum contour area for red tags
                        min_contour_area_red = 500  # Adjust as needed

                        if contours_red:
                            for contour_red in contours_red:
                                # Calculate the contour area
                                contour_area_red = cv2.contourArea(contour_red)

                                # Skip small contours
                                if contour_area_red < min_contour_area_red:
                                    continue

                                # Calculate the center of the red contour if M["m00"] is not zero
                                M_red = cv2.moments(contour_red)
                                if M_red["m00"] != 0:
                                    cX_red = int(M_red["m10"] / M_red["m00"])
                                    cY_red = int(M_red["m01"] / M_red["m00"])
                                    print(f"Center of red contour: ({cX_red}, {cY_red})")

                                    # Draw a vector from the bottom center of the image to the center of the red contour
                                    cv2.arrowedLine(frame, (width // 2, height), (cX_red, cY_red), (0, 0, 255), 1)

                                    # Check if the red tag passes from the upper half to the lower half of the image
                                    if previous_cY_red is not None and previous_cY_red < height // 2 and cY_red >= height // 2:
                                        stop_motors = True
                                        print("Red tag passed from upper half to lower half of the image. Stopping motors for 10 seconds.")

                                    previous_cY_red = cY_red
                                    break

                else:
                    # No valid blue vector detected, stop the motors
                    right_speed = 0
                    left_speed = 0
            else:
                # No blue vector detected, stop the motors
                right_speed = 0
                left_speed = 0

            # Show the image
            cv2.imshow('frame', frame)

            # Break the loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        # Keyboard interrupt detected, stop the motors
        right_speed = 0
        left_speed = 0

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()