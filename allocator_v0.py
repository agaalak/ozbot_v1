import csv
import re

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read().splitlines()

def write_csv(data, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

def process_data(lines):
    result = []
    pallet_id = ""
    rack_space_pattern = re.compile(r"\d{2}\.\d{2}\.[A-Z]\.\d{2}")

    for line in lines:
        if "#" in line:
            pallet_id = line
        elif rack_space_pattern.match(line):
            result.append([line, pallet_id])
            pallet_id = ""  # clear pallet_id after associating with a rack_space
    return result

lines = read_file("input/reconciled_v2.txt")
data = process_data(lines)
write_csv(data, "allocated_v0.csv")
