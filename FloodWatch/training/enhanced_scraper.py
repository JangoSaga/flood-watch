import requests
import datetime
import csv
import pandas as pd
import os
from city_reservoir_mapper import get_district_for_city

def get_weather_data(date, month, year, days, lat, lon, city_name):
    """
    Get historical weather data from Open-Meteo API
    """
    a = datetime.date(year, month, date)
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
        print(f"Fetching weather for {city_name} from {start_date} to {end_date}")
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"Weather API Error: {response.status_code}")
            return [0, 0, 0, 0, 0, 0, 0]
        
        data = response.json()
        if 'daily' not in data:
            return [0, 0, 0, 0, 0, 0, 0]
        
        daily_data = data['daily']
        
        # Calculate weather metrics
        def safe_avg(values):
            clean_values = [v for v in values if v is not None]
            return sum(clean_values) / len(clean_values) if clean_values else 0
        
        def safe_max(values):
            clean_values = [v for v in values if v is not None]
            return max(clean_values) if clean_values else 0
        
        def safe_sum(values):
            clean_values = [v for v in values if v is not None]
            return sum(clean_values) if clean_values else 0
        
        temp = safe_avg(daily_data['temperature_2m_mean'])
        maxt = safe_max(daily_data['temperature_2m_max'])
        wspd = safe_avg(daily_data['wind_speed_10m_max'])
        cloudcover = safe_avg(daily_data['cloud_cover_mean'])
        precip = safe_sum(daily_data['precipitation_sum'])
        humidity = safe_avg(daily_data['relative_humidity_2m_mean'])
        
        # Calculate precipitation cover
        precip_days = sum(1 for p in daily_data['precipitation_sum'] if p is not None and p > 0)
        total_days = len([p for p in daily_data['precipitation_sum'] if p is not None])
        precipcover = (precip_days / total_days * 100) if total_days > 0 else 0
        
        return [temp, maxt, wspd, cloudcover, precip, humidity, precipcover]
        
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return [0, 0, 0, 0, 0, 0, 0]

def get_reservoir_data_for_date(city, target_date, aggregated_reservoir_df):
    """
    Get reservoir data for specific city and date
    """
    target_date = pd.to_datetime(target_date)
    
    # Find exact date match first
    exact_match = aggregated_reservoir_df[
        (aggregated_reservoir_df['City'] == city) & 
        (aggregated_reservoir_df['Date'] == target_date)
    ]
    
    if not exact_match.empty:
        row = exact_match.iloc[0]
        return [
            row['Avg_Reservoir_Fill'], 
            row['Max_Reservoir_Fill'],
            row['Reservoir_Risk_Score'],
            row['Reservoirs_Above_Danger']
        ]
    
    # If no exact match, find closest date within 7 days
    city_data = aggregated_reservoir_df[aggregated_reservoir_df['City'] == city].copy()
    if city_data.empty:
        return [0, 0, 0, 0]
    
    city_data['Date_Diff'] = abs((city_data['Date'] - target_date).dt.days)
    closest = city_data[city_data['Date_Diff'] <= 7].sort_values('Date_Diff')
    
    if not closest.empty:
        row = closest.iloc[0]
        return [
            row['Avg_Reservoir_Fill'], 
            row['Max_Reservoir_Fill'],
            row['Reservoir_Risk_Score'],
            row['Reservoirs_Above_Danger']
        ]
    
    return [0, 0, 0, 0]

def determine_flood_label(weather_data, reservoir_data):
    """
    Enhanced flood labeling using both weather and reservoir data
    """
    precip = weather_data[4]  # Total precipitation
    max_reservoir_fill = reservoir_data[1]
    reservoir_risk_score = reservoir_data[2]
    reservoirs_above_danger = reservoir_data[3]
    
    flood_score = 0
    
    # Weather contribution
    if precip > 75:  # Very heavy rainfall
        flood_score += 3
    elif precip > 50:
        flood_score += 2
    elif precip > 25:
        flood_score += 1
    
    # Reservoir contribution  
    if max_reservoir_fill > 90:  # Critical level
        flood_score += 4
    elif max_reservoir_fill > 80:
        flood_score += 2
    elif max_reservoir_fill > 70:
        flood_score += 1
    
    # Additional reservoir risk
    flood_score += min(reservoir_risk_score, 3)  # Cap at 3
    
    # Multiple dangerous reservoirs
    if reservoirs_above_danger > 1:
        flood_score += 1
    
    # Decision threshold
    return 1 if flood_score >= 6 else 0

def create_enhanced_training_data(cities_coords_path, aggregated_reservoir_path):
    """
    Create training data combining weather and reservoir data
    """
    # Load aggregated reservoir data
    print("Loading aggregated reservoir data...")
    reservoir_df = pd.read_csv(aggregated_reservoir_path)
    reservoir_df['Date'] = pd.to_datetime(reservoir_df['Date'])
    
    # Load cities coordinates
    cities_coords = {}
    with open(cities_coords_path, 'r', encoding='UTF-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                city = row['city']
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                cities_coords[city] = {'lat': lat, 'lon': lon}
            except (KeyError, ValueError, TypeError):
                # Skip malformed rows
                continue
    
    training_data = []
    
    # Read all cities from cities.csv instead of hardcoded list
    all_cities = list(cities_coords.keys())
    print(f"Found {len(all_cities)} cities in cities.csv")
    
    # Reduce samples per city to manage dataset size
    if len(all_cities) > 50:
        samples_per_city = 20  # For large number of cities
    elif len(all_cities) > 20:
        samples_per_city = 30  # For medium number of cities  
    else:
        samples_per_city = 50  # For small number of cities
    
    print(f"Generating {samples_per_city} samples per city")
    
    for city in all_cities:
        coords = cities_coords[city]
        print(f"Generating training data for {city}...")
        
        # Generate samples for this city
        for _ in range(samples_per_city):
            year = np.random.randint(2019, 2025)
            month = np.random.randint(1, 13)
            day = np.random.randint(1, 29)  # Safe day range
            year = np.random.randint(2019, 2025)
            month = np.random.randint(1, 13)
            day = np.random.randint(1, 29)  # Safe day range
            
            try:
                target_date = datetime.date(year, month, day)
                
                # Get weather data
                weather_data = get_weather_data(
                    day, month, year, 15, 
                    coords['lat'], coords['lon'], city
                )
                
                # Get reservoir data
                reservoir_data = get_reservoir_data_for_date(
                    city, target_date, reservoir_df
                )
                
                # Skip if no valid data
                if sum(weather_data) == 0 or sum(reservoir_data) == 0:
                    continue
                
                # Determine flood label
                flood_label = determine_flood_label(weather_data, reservoir_data)
                
                # Combine features
                combined_features = weather_data + reservoir_data + [flood_label]
                training_data.append(combined_features)
                
            except Exception as e:
                print(f"Error processing {city} {year}-{month}-{day}: {e}")
                continue
    
    return training_data

if __name__ == "__main__":
    import numpy as np
    
    script_dir = os.path.dirname(__file__)
    cities_path = os.path.join(script_dir,'data', 'cities.csv')
    reservoir_path = os.path.join(script_dir, 'data', 'aggregated_reservoir_data.csv')
    output_path = os.path.join(script_dir, 'data', 'enhanced_training_data.csv')
    
    # Create training data
    training_data = create_enhanced_training_data(cities_path, reservoir_path)
    
    # Save to CSV
    headers = [
        'temp_avg', 'temp_max', 'wind_speed', 'cloud_cover', 'precipitation', 
        'humidity', 'precip_cover', 'avg_reservoir_fill', 'max_reservoir_fill', 
        'reservoir_risk_score', 'reservoirs_above_danger', 'flood_class'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(training_data)
    
    print(f"Created {len(training_data)} training samples")
    print(f"Saved to {output_path}")