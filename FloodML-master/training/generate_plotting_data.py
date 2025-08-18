import csv
import pickle
import os
try:
    import numpy as np
except ImportError:
    print("Installing numpy...")
    import subprocess
    subprocess.check_call(["pip", "install", "numpy==1.19.1"])
    import numpy as np

model = pickle.load(open(os.path.join(os.path.dirname(__file__), '..', 'model.pickle'), 'rb'))
c = open(os.path.join(os.path.dirname(__file__), 'cities.csv'), 'r', encoding='UTF-8')

cr = csv.reader(c)

cities = []

for c_row in cr:
    cities.append(c_row) 

d = open(os.path.join(os.path.dirname(__file__), 'plotting.csv'), 'r', encoding='UTF-8')

dr = csv.reader(d)

forecast = []
for d_row in dr:
    k = list(map(float, d_row))
    forecast.append([k[4], model.predict([k])[0]])

ff = open(os.path.join(os.path.dirname(__file__), 'final_plot.csv'), mode='w', newline='', encoding='UTF-8')
writer = csv.writer(ff, delimiter=',')

for i in range(0, len(forecast)):
    writer.writerow(cities[i] + forecast[i])
print(forecast)


