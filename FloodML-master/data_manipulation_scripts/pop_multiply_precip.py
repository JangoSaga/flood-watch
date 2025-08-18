import requests
import json
import csv

damage = []

import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root, then into training directory
training_dir = os.path.join(os.path.dirname(script_dir), 'training')
csv_file = os.path.join(training_dir, 'final_plot.csv')

with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if row[0] != "city":
            dam = round(float(row[3]) * float(row[5])/10000, 2)
            damage.append(dam)

with open('damage.csv', 'w') as f:
    writer = csv.writer(f)
    for val in damage:
        writer.writerow([val])