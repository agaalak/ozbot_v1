import os
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar

# Parent directory path
parent_dir_path = 'input/'

# List all subdirectories in the parent directory
subdirs = sorted([os.path.join(parent_dir_path, dir) for dir in os.listdir(parent_dir_path) if os.path.isdir(os.path.join(parent_dir_path, dir))])

# Output file to write the results
output_file = open(os.path.join(parent_dir_path, 'decoded_v4.txt'), 'w')

# Set to store all QR codes across directories
all_codes = set()

# Iterate over each subdirectory
for dir_index, dir_path in enumerate(subdirs):
    # List all files in subdirectory
    files = sorted(os.listdir(dir_path), reverse=True)

    for index, file in enumerate(files):
        if file.endswith('.jpg'):
            # Full file path
            file_path = os.path.join(dir_path, file)

            # Open the image file
            img = cv2.imread(file_path)

            if img is None:
                continue

            # Convert image to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply adaptive threshold to enhance barcode
            thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)

            # Decode any barcodes in the original image
            decoded_objects_original = pyzbar.decode(img)

            # Decode any barcodes in the preprocessed image
            decoded_objects_preprocessed = pyzbar.decode(thresh)

            # Combine the results from original and preprocessed image
            decoded_objects = decoded_objects_original + decoded_objects_preprocessed

            # Rotate the image and try to decode
            img_rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            decoded_objects_rotated = pyzbar.decode(img_rotated)
            
            # Combine all results
            decoded_objects = decoded_objects + decoded_objects_rotated

            if not decoded_objects:
                continue

            for obj in decoded_objects:
                # Get the barcode data, type and position
                code_data = obj.data.decode('utf-8')
                code_type = obj.type
                code_position = obj.rect

                if code_data not in all_codes:
                    all_codes.add(code_data)
                    # Write the results to the output file
                    # Folder index, index, Original left position, Original top position,
                    # Modified left position, Modified top position, Folder name, Directory, Image name, Barcode type, Barcode data
                    output_file.write(f"{dir_index} {index} {code_position.left} {code_position.top} {dir_index*6000+code_position.left} {index*4000+code_position.top} {os.path.basename(parent_dir_path)} {os.path.basename(dir_path)} {file} {code_type} {code_data}\n")

output_file.close()
