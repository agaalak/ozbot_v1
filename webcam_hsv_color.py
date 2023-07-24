import cv2
import numpy as np

def main():
    cap = cv2.VideoCapture(0)

    # Define the small rectangle in the middle of the frame
    rect_size = 20
    values = []

    while True:
        ret, frame = cap.read()

        # Check if the frame was successfully read
        if not ret:
            print("Failed to grab frame")
            break

        height, width, _ = frame.shape

        # Draw the rectangle
        top_left = (width//2 - rect_size//2, height//2 - rect_size//2)
        bottom_right = (width//2 + rect_size//2, height//2 + rect_size//2)
        cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 1)

        # Convert the frame to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Calculate average HSV values within the rectangle
        rect_hsv = hsv[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        avg_hsv = np.mean(rect_hsv, axis=(0, 1))

        cv2.imshow('frame', frame)

        # Break the loop on 'q' key press
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

        # On any other key press, store the average HSV values
        elif key != -1:
            values.append(avg_hsv)
            print(f"Stored HSV values: {avg_hsv}")

            # After four key presses, calculate and print the lower and upper HSV values
            if len(values) == 4:
                min_hsv = np.min(values, axis=0)
                max_hsv = np.max(values, axis=0)

                print(f"Lower HSV values: {min_hsv}")
                print(f"Upper HSV values: {max_hsv}")

                # Reset the values list for the next batch
                values = []

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()

