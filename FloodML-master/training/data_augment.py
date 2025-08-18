import csv
import random
import os 

def augment(k):
    final = []
    for i in range(0, 7):
        final.append(round(random.uniform(33.33, 66.66), 2) + float(k[i]))

    return final + [int(k[7])]

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Open files relative to script location
data1 = open(os.path.join(script_dir, 'data.csv'), mode='r')
data0 = open(os.path.join(script_dir, 'data1.csv'), mode='r')

reader1 = csv.reader(data1)

reader0 = csv.reader(data0)

f = open(os.path.join(script_dir, 'final_data.csv'), mode='w', newline = '')
writer = csv.writer(f, delimiter=',')

for row1 in reader1:
    writer.writerow(row1)
    for i in range(0, 19):
        writer.writerow(augment(row1))

for row0 in reader0:
    writer.writerow(row0)
    for i in range(0, 19):
        writer.writerow(augment(row0))