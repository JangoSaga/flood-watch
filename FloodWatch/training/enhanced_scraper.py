import requests
import datetime
import csv
import pandas as pd
import os
import numpy as np
from city_reservoir_mapper import get_district_for_city

def load_flood_events(flood_events_path):
    """Load real flood events from CSV for accurate labeling."""
    flood_events = []
    try:
        df = pd.read_csv(flood_events_path)
        df['date'] = pd.to_datetime(df['date'])
        for _, row in df.iterrows():
            flood_events.append((row['city'], row['date'].date()))
        print(f"Loaded {len(flood_events)} real flood events")
    except Exception as e:
        print(f"Warning: Could not load flood events from {flood_events_path}: {e}")
        flood_events = []
    return flood_events


def get_weather_data(day, month, year, days, lat, lon, city_name):
    """Fetch historical weather data from Open-Meteo API."""
    a = datetime.date(year, month, day)
    b = a - datetime.timedelta(days)

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
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
        response = requests.get(BASE_URL, params=params, timeout=10)
        if response.status_code != 200:
            return [0, 0, 0, 0, 0, 0, 0]

        data = response.json()
        if 'daily' not in data:
            return [0, 0, 0, 0, 0, 0, 0]

        daily_data = data['daily']

        def safe_avg(values): return sum([v for v in values if v is not None]) / len([v for v in values if v is not None]) if any(values) else 0
        def safe_max(values): return max([v for v in values if v is not None]) if any(values) else 0
        def safe_sum(values): return sum([v for v in values if v is not None]) if any(values) else 0

        temp = safe_avg(daily_data['temperature_2m_mean'])
        maxt = safe_max(daily_data['temperature_2m_max'])
        wspd = safe_avg(daily_data['wind_speed_10m_max'])
        cloudcover = safe_avg(daily_data['cloud_cover_mean'])
        precip = safe_sum(daily_data['precipitation_sum'])
        humidity = safe_avg(daily_data['relative_humidity_2m_mean'])

        precip_days = sum(1 for p in daily_data['precipitation_sum'] if p and p > 0)
        total_days = len([p for p in daily_data['precipitation_sum'] if p is not None])
        precipcover = (precip_days / total_days * 100) if total_days > 0 else 0

        return [temp, maxt, wspd, cloudcover, precip, humidity, precipcover]

    except Exception:
        return [0, 0, 0, 0, 0, 0, 0]


def get_reservoir_data_for_date(city, target_date, aggregated_reservoir_df):
    """Get reservoir data for city-date, fallback ±7 days."""
    target_date = pd.to_datetime(target_date)

    exact = aggregated_reservoir_df[(aggregated_reservoir_df['City'] == city) &
                                    (aggregated_reservoir_df['Date'] == target_date)]
    if not exact.empty:
        r = exact.iloc[0]
        return [r['Avg_Reservoir_Fill'], r['Max_Reservoir_Fill'], r['Reservoir_Risk_Score'], r['Reservoirs_Above_Danger']]

    city_data = aggregated_reservoir_df[aggregated_reservoir_df['City'] == city].copy()
    if city_data.empty:
        return [0, 0, 0, 0]

    city_data['Date_Diff'] = abs((city_data['Date'] - target_date).dt.days)
    closest = city_data[city_data['Date_Diff'] <= 7].sort_values('Date_Diff')
    if not closest.empty:
        r = closest.iloc[0]
        return [r['Avg_Reservoir_Fill'], r['Max_Reservoir_Fill'], r['Reservoir_Risk_Score'], r['Reservoirs_Above_Danger']]

    return [0, 0, 0, 0]


def create_enhanced_training_data(cities_coords_path, aggregated_reservoir_path, flood_events_path=None):
    """Create training data using real flood events + heuristic fallback."""
    flood_events = load_flood_events(flood_events_path) if (flood_events_path and os.path.exists(flood_events_path)) else []

    reservoir_df = pd.read_csv(aggregated_reservoir_path)
    reservoir_df['Date'] = pd.to_datetime(reservoir_df['Date'])

    cities_coords = {}
    with open(cities_coords_path, 'r', encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cities_coords[row['city']] = {'lat': float(row['latitude']), 'lon': float(row['longitude'])}
            except Exception:
                continue

    training_data = []
    real_event_labels = 0
    heuristic_labels = 0

    # --- 1. Add samples from real flood events ---
    for city, event_date in flood_events:
        if city not in cities_coords:
            continue
        coords = cities_coords[city]
        print(f"Generating training data for {city}...")
        weather_data = get_weather_data(event_date.day, event_date.month, event_date.year, 15, coords['lat'], coords['lon'], city)
        reservoir_data = get_reservoir_data_for_date(city, event_date, reservoir_df)

        if sum(weather_data) == 0 or sum(reservoir_data) == 0:
            continue

        combined_features = weather_data + reservoir_data + [1]
        training_data.append(combined_features)
        real_event_labels += 1

    # --- 2. Add heuristic/random samples for negatives + balance ---
    all_cities = list(cities_coords.keys())
    samples_per_city = 20 if len(all_cities) > 50 else 30
    for city in all_cities:
        coords = cities_coords[city]
        for _ in range(samples_per_city):
            year = np.random.randint(2019, 2025)
            month = np.random.randint(1, 13)
            day = np.random.randint(1, 29)
            target_date = datetime.date(year, month, day)

            weather_data = get_weather_data(day, month, year, 15, coords['lat'], coords['lon'], city)
            reservoir_data = get_reservoir_data_for_date(city, target_date, reservoir_df)

            if sum(weather_data) == 0 or sum(reservoir_data) == 0:
                continue

            # Label = 1 if near a real event, else 0
            label = 0
            for event_city, event_date in flood_events:
                if event_city == city and abs((target_date - event_date).days) <= 7:
                    label = 1
                    break

            combined_features = weather_data + reservoir_data + [label]
            training_data.append(combined_features)
            if label == 1:
                real_event_labels += 1
            else:
                heuristic_labels += 1

    print(f"\nLabeling Stats → Real events: {real_event_labels}, Heuristic: {heuristic_labels}, Total samples: {len(training_data)}")
    return training_data


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    cities_path = os.path.join(project_root, 'data', 'cities.csv')
    reservoir_path = os.path.join(project_root, 'data', 'aggregated_reservoir_data.csv')
    flood_events_path = os.path.join(project_root, 'data', 'flood_events_clean.csv')
    output_path = os.path.join(project_root, 'data', 'enhanced_training_data.csv')

    training_data = create_enhanced_training_data(cities_path, reservoir_path, flood_events_path)

    headers = ['temp_avg', 'temp_max', 'wind_speed', 'cloud_cover', 'precipitation', 'humidity',
               'precip_cover', 'avg_reservoir_fill', 'max_reservoir_fill',
               'reservoir_risk_score', 'reservoirs_above_danger', 'flood_class']

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(training_data)

    print(f"✅ Created {len(training_data)} samples → saved to {output_path}")
