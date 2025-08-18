import csv
import datetime
import pickle
import requests
import os

def get_data(lat, lon):
    # Open-Meteo API for forecast data
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_mean,temperature_2m_max,wind_speed_10m_max,cloud_cover_mean,precipitation_sum,relative_humidity_2m_mean',
        'forecast_days': 15,
        'timezone': 'auto'
    }
    
    try:
        print(f"Fetching forecast for lat: {lat}, lon: {lon}")
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return [0, 0, 0, 0, 0, 0]
        
        data = response.json()
        
        if 'daily' not in data:
            print(f"No daily data in response: {data}")
            return [0, 0, 0, 0, 0, 0]
        
        daily_data = data['daily']
        
        # Handle None values and calculate averages
        def safe_avg(values):
            clean_values = [v for v in values if v is not None]
            return sum(clean_values) / len(clean_values) if clean_values else 0
        
        def safe_max(values):
            clean_values = [v for v in values if v is not None]
            return max(clean_values) if clean_values else 0
        
        def safe_sum(values):
            clean_values = [v for v in values if v is not None]
            return sum(clean_values) if clean_values else 0
        
        # Calculate averages and totals over 15 days
        temp_avg = safe_avg(daily_data['temperature_2m_mean'])
        temp_max = safe_max(daily_data['temperature_2m_max'])
        wspd_avg = safe_avg(daily_data['wind_speed_10m_max'])
        cloudcover_avg = safe_avg(daily_data['cloud_cover_mean'])
        precip_total = safe_sum(daily_data['precipitation_sum'])
        humidity_avg = safe_avg(daily_data['relative_humidity_2m_mean'])
        
        final = [temp_avg, temp_max, wspd_avg, cloudcover_avg, precip_total, humidity_avg]
        print(f"Success: {final}")
        return final
        
    except requests.exceptions.Timeout:
        print("Request timeout")
        return [0, 0, 0, 0, 0, 0]
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return [0, 0, 0, 0, 0, 0]
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return [0, 0, 0, 0, 0, 0]

def testConnection():
    return "yo"



f = open(os.path.join(os.path.dirname(__file__), 'cities.csv'), 'r', encoding='UTF-8')
ff = open(os.path.join(os.path.dirname(__file__), 'plotting.csv'), mode='w', newline='')
writer = csv.writer(ff, delimiter=',')

r = csv.reader(f)

for row in r:
    print(row)
    writer.writerow(get_data(row[1], row[2]))