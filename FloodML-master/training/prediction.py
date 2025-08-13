import csv
import datetime
import pickle
import requests
import os
import sys
sys.path.append('..')
from config import VISUAL_CROSSING_API_KEY

def get_data(lat, lon):
    try:
        k = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/forecast?locations=" + str(lat) + "%2C%20" + str(lon) + "&aggregateHours=24&unitGroup=us&shortColumnNames=false&contentType=json&key="+VISUAL_CROSSING_API_KEY
        x = requests.get(k).json()['locations']
        for i in x:
            y = x[i]['values']

        final = [0, 0, 0, 0, 0, 0]

        for j in y:
            final[0] += j['temp']
            if j['maxt'] > final[1]:
                final[1] = j['maxt']
            final[2] += j['wspd']
            final[3] += j['cloudcover']
            final[4] += j['precip']
            final[5] += j['humidity']
        final[0] /= 15
        final[2] /= 15
        final[3] /= 15
        final[5] /= 15

        return final
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        # Return default values if API fails
        return [75.0, 85.0, 10.0, 50.0, 5.0, 70.0]

def testConnection():
    return "yo"