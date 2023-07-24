import csv
import re
import os

# Parent directory path
parent_dir_path = 'input/'

# Input file
input_file_path = os.path.join(parent_dir_path, 'decoded_v4.txt')
# Output file
output_file_path = os.path.join(parent_dir_path, 'reconciled_v2.txt')

# Regular expressions
six_digit_num_pattern = re.compile(r'^\d{6}$')
custom_format_pattern = re.compile(r'^\d{2}\.\d{2}\.A\.\d{2}$')

filtered_rows = []

with open(input_file_path, 'r') as input_file:
    reader = csv.reader(input_file, delimiter=' ')

    for row in reader:
        code_type = row[9]    # assuming code_type is the 10th field in each row
        code_data = row[10]   # assuming code_data is the 11th field in each row

        # Delete row if code_type is not QRCODE or I25
        if code_type not in ['QRCODE', 'I25']:
            continue

        # Delete row if code_type is I25 and code_data is not a six digit number
        if code_type == 'I25' and not six_digit_num_pattern.match(code_data):
            continue

        # Convert "Modified left position" and "Modified top position" to integers for proper sorting
        row[4] = int(row[4])
        row[5] = int(row[5])
        filtered_rows.append(row)

# Sort the rows by "Modified left position" in ascending order
filtered_rows = sorted(filtered_rows, key=lambda row: row[4])

groups = []
group = []
# Split the rows into groups based on the presence of six digit pattern
for row in filtered_rows:
    code_data = row[10]   # assuming code_data is the 11th field in each row
    if six_digit_num_pattern.match(code_data):
        groups.append(group)
        group = []
    group.append(row)
groups.append(group)

# In each group, if there's a row with Barcode data in custom format, move that row to the end of that group
# Then sort the rows with barcode type QRCODE in each group by "Modified top position"
for group in groups:
    group_with_custom_format = [row for row in group if custom_format_pattern.match(row[10])]
    group_without_custom_format = [row for row in group if not custom_format_pattern.match(row[10])]
    group_without_custom_format.sort(key=lambda row: (row[9] == 'QRCODE', row[5]))
    group_with_custom_format.sort(key=lambda row: row[5])
    group.clear()
    group.extend(group_without_custom_format)
    group.extend(group_with_custom_format)

# Write the sorted groups to the output file, only writing the last column (Barcode data)
with open(output_file_path, 'w', newline='') as output_file:
    writer = csv.writer(output_file, delimiter=' ')
    for group in groups:
        for row in group:
            writer.writerow([row[10]])  # Only write Barcode data
        writer.writerow([])  # Empty row to separate groups
