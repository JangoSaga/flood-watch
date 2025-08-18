import requests
import datetime
import os

def get_data(date, month, year, days, lat, lon, city_name):
    a = datetime.date(year, month, date)
    b = a - datetime.timedelta(days)
    
    # Open-Meteo API for historical weather data
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    # Use the provided coordinates directly
    
    # Format dates properly for Open-Meteo API
    start_date = b.strftime('%Y-%m-%d')
    end_date = a.strftime('%Y-%m-%d')
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        'end_date': end_date,
        'daily': 'temperature_2m_mean,temperature_2m_max,wind_speed_10m_max,cloud_cover_mean,precipitation_sum,relative_humidity_2m_mean',
        'timezone': 'auto'
    }
    
    try:
        print(f"Fetching data for {city_name} from {start_date} to {end_date}")
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return [0, 0, 0, 0, 0, 0, 0]
        
        data = response.json()
        
        if 'daily' not in data:
            print(f"No daily data in response: {data}")
            return [0, 0, 0, 0, 0, 0, 0]
        
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
        
        # Calculate weather metrics
        temp = safe_avg(daily_data['temperature_2m_mean'])
        maxt = safe_max(daily_data['temperature_2m_max'])
        wspd = safe_avg(daily_data['wind_speed_10m_max'])
        cloudcover = safe_avg(daily_data['cloud_cover_mean'])
        precip = safe_sum(daily_data['precipitation_sum'])
        humidity = safe_avg(daily_data['relative_humidity_2m_mean'])
        
        # Calculate precipitation cover (days with precipitation / total days)
        precip_days = sum(1 for p in daily_data['precipitation_sum'] if p is not None and p > 0)
        total_days = len([p for p in daily_data['precipitation_sum'] if p is not None])
        precipcover = (precip_days / total_days * 100) if total_days > 0 else 0
        
        final = [temp, maxt, wspd, cloudcover, precip, humidity, precipcover]
        print(f"Success: {final}")
        return final
        
    except requests.exceptions.Timeout:
        print("Request timeout")
        return [0, 0, 0, 0, 0, 0, 0]
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return [0, 0, 0, 0, 0, 0, 0]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return [0, 0, 0, 0, 0, 0, 0]

# Updated Maharashtra cities list
maharashtra_cities = ['Mumbai', 'Pune', 'Kolhapur', 'Nashik', 'Nagpur']
import csv
import random
f = open(os.path.join(os.path.dirname(__file__), 'data1.csv'), mode='w', newline='')
writer = csv.writer(f, delimiter=',')

for i in maharashtra_cities:
    for j in range(1, 31):
        a = random.randint(1, 28)
        b = random.randint(1, 12)
        c = random.randint(2019, 2024)

        # Use hardcoded coordinates for Maharashtra cities in the main loop
        maharashtra_coords = {
            'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
            'Pune': {'lat': 18.5204, 'lon': 73.8567},
            'Kolhapur': {'lat': 16.7050, 'lon': 74.2433},
            'Nashik': {'lat': 19.9975, 'lon': 73.7898},
            'Nagpur': {'lat': 21.1458, 'lon': 79.0882}
        }
        coords = maharashtra_coords[i]
        k = get_data(a, b, c, 15, coords['lat'], coords['lon'], i)

        if k[4] != None:
            if k[4] < 20:
                print(k)
                print(j)
                writer.writerow(k + [0])

def extract_date(x):
    k = x.split(" ")

    a = int(k[0])

    d = {'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6, 'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12}
    b = d[k[1][0:len(k[1]) - 1].lower()]

    c = int(k[2])

    return [a, b, c]

# Load cities from cities.csv for coordinate lookup
cities_coords = {}
with open(os.path.join(os.path.dirname(__file__), 'cities.csv'), 'r', encoding='UTF-8') as cities_file:
    cities_reader = csv.reader(cities_file)
    for row in cities_reader:
        if len(row) >= 3:
            cities_coords[row[0].lower()] = {'lat': float(row[1]), 'lon': float(row[2])}

def process(k):
    x = extract_date(k[1])
    city_name = k[0]
    
    # Find matching city in cities.csv
    city_coords = None
    city_lower = city_name.lower()
    
    # Direct match first
    if city_lower in cities_coords:
        city_coords = cities_coords[city_lower]
    else:
        # Partial match - find city that contains the location name or vice versa
        for city_key, coords in cities_coords.items():
            if city_lower in city_key or city_key in city_lower:
                city_coords = coords
                break
    
    if city_coords:
        print(f"Found coordinates for {city_name}: {city_coords}")
        return get_data(x[0], x[1], x[2], 15, city_coords['lat'], city_coords['lon'], city_name)
    else:
        print(f"No coordinates found for {city_name}, skipping...")
        return [0, 0, 0, 0, 0, 0, 0]

f = open(os.path.join(os.path.dirname(__file__), 'data.csv'), mode='w', newline='')
writer = csv.writer(f, delimiter=',')

with open(os.path.join(os.path.dirname(__file__), 'mined.csv'), mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    
    for row in csv_reader:
        print(f"Processing mined data: {row}")
        processed_data = process(row)
        if processed_data != [0, 0, 0, 0, 0, 0, 0]:  # Only write if we got valid data
            writer.writerow(processed_data + [1])
        else:
            # Still write zeros for consistency but mark as flood data
            writer.writerow(processed_data + [1])