import csv
import random 

def augment(k):
    final = []
    # k indices: 0..5 are features
    for i in range(0, 6):
        final.append(round(random.uniform(0.8, 1.2) * float(k[i]), 2))

    return final + [int(k[6])]

with open('data.csv', mode='r') as data1, open('data1.csv', mode='r') as data0:
    reader1 = csv.reader(data1)
    reader0 = csv.reader(data0)

    with open('final_data.csv', mode='w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        # Read and write header once
        header1 = next(reader1, None)
        header0 = next(reader0, None)
        writer.writerow(['temp','max_temp','wind_speed','cloudcover','precip','humidity','class'])

        for row1 in reader1:
            writer.writerow(row1)
            for _ in range(0, 19):
                writer.writerow(augment(row1))

        for row0 in reader0:
            writer.writerow(row0)
            for _ in range(0, 19):
                writer.writerow(augment(row0))