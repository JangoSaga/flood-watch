import requests
import pandas as pd
import pickle
import csv
import os
from datetime import datetime, timedelta

def get_current_weather_forecast(lat, lon, city_name):
    """
    Get current 15-day weather forecast
    """
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_mean,temperature_2m_max,wind_speed_10m_max,cloud_cover_mean,precipitation_sum,relative_humidity_2m_mean',
        'forecast_days': 15,
        'timezone': 'auto'
    }
    
    try:
        print(f"Fetching forecast for {city_name}...")
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"Forecast API Error: {response.status_code}")
            return [0, 0, 0, 0, 0, 0, 0]
        
        data = response.json()
        if 'daily' not in data:
            return [0, 0, 0, 0, 0, 0, 0]
        
        daily_data = data['daily']
        
        # Calculate forecast metrics (same as historical)
        def safe_avg(values):
            clean_values = [v for v in values if v is not None]
            return sum(clean_values) / len(clean_values) if clean_values else 0
        
        def safe_max(values):
            clean_values = [v for v in values if v is not None]
            return max(clean_values) if clean_values else 0
        
        def safe_sum(values):
            clean_values = [v for v in values if v is not None]
            return sum(clean_values) if clean_values else 0
        
        temp_avg = safe_avg(daily_data['temperature_2m_mean'])
        temp_max = safe_max(daily_data['temperature_2m_max'])
        wspd_avg = safe_avg(daily_data['wind_speed_10m_max'])
        cloudcover_avg = safe_avg(daily_data['cloud_cover_mean'])
        precip_total = safe_sum(daily_data['precipitation_sum'])
        humidity_avg = safe_avg(daily_data['relative_humidity_2m_mean'])
        
        # Calculate precipitation coverage
        precip_days = sum(1 for p in daily_data['precipitation_sum'] if p is not None and p > 0)
        total_days = len([p for p in daily_data['precipitation_sum'] if p is not None])
        precip_coverage = (precip_days / total_days * 100) if total_days > 0 else 0
        
        return [temp_avg, temp_max, wspd_avg, cloudcover_avg, precip_total, humidity_avg, precip_coverage]
        
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return [0, 0, 0, 0, 0, 0, 0]

def get_current_reservoir_data(city, aggregated_reservoir_path):
    """
    Get most recent reservoir data for a city
    """
    try:
        reservoir_df = pd.read_csv(aggregated_reservoir_path)
        reservoir_df['Date'] = pd.to_datetime(reservoir_df['Date'])
        
        # Filter for the city and get most recent data
        city_data = reservoir_df[reservoir_df['City'] == city]
        if city_data.empty:
            print(f"No reservoir data for {city}")
            return [0, 0, 0, 0]
        
        # Get most recent entry
        latest_data = city_data.sort_values('Date').iloc[-1]
        
        return [
            latest_data['Avg_Reservoir_Fill'],
            latest_data['Max_Reservoir_Fill'], 
            latest_data['Reservoir_Risk_Score'],
            latest_data['Reservoirs_Above_Danger']
        ]
        
    except Exception as e:
        print(f"Error getting reservoir data for {city}: {e}")
        return [0, 0, 0, 0]

def make_flood_prediction(weather_features, reservoir_features, model):
    """
    Make flood prediction using combined features
    """
    try:
        # Combine all features
        combined_features = weather_features + reservoir_features
        
        # Make prediction
        prediction = model.predict([combined_features])[0]
        
        # Get prediction probability if available
        try:
            probability = model.predict_proba([combined_features])[0]
            confidence = max(probability)
        except:
            confidence = 0.8 if prediction == 1 else 0.6
        
        return prediction, confidence
        
    except Exception as e:
        print(f"Error making prediction: {e}")
        return 0, 0.0

def generate_predictions_for_cities(cities_path, reservoir_data_path, model_path):
    """
    Generate flood predictions for all cities
    """
    # Load model
    try:
        model = pickle.load(open(model_path, 'rb'))
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        return []
    
    # Load cities
    cities_coords = {}
    with open(cities_path, 'r', encoding='UTF-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                cities_coords[row[0]] = {'lat': float(row[1]), 'lon': float(row[2])}
    
    predictions = []
    
    for city_name, coords in cities_coords.items():
        print(f"Processing {city_name}...")
        
        # Get weather forecast
        weather_features = get_current_weather_forecast(
            coords['lat'], coords['lon'], city_name
        )
        
        # Get current reservoir data
        reservoir_features = get_current_reservoir_data(city_name, reservoir_data_path)
        
        # Skip if no valid data
        if sum(weather_features) == 0 and sum(reservoir_features) == 0:
            print(f"No data available for {city_name}")
            continue
        
        # Make prediction
        flood_prediction, confidence = make_flood_prediction(
            weather_features, reservoir_features, model
        )
        
        # Store result
        prediction_record = {
            'City': city_name,
            'Latitude': coords['lat'],
            'Longitude': coords['lon'],
            'Predicted_Flood_Risk': flood_prediction,
            'Confidence': round(confidence, 3),
            'Weather_Precip': weather_features[4] if len(weather_features) > 4 else 0,
            'Max_Reservoir_Fill': reservoir_features[1] if len(reservoir_features) > 1 else 0,
            'Reservoir_Risk_Score': reservoir_features[2] if len(reservoir_features) > 2 else 0,
            'Prediction_Date': datetime.now().strftime('%Y-%m-%d')
        }
        
        predictions.append(prediction_record)
        
        # Print summary
        risk_level = "HIGH" if flood_prediction == 1 else "LOW"
        print(f"{city_name}: {risk_level} risk (confidence: {confidence:.2f})")
    
    return predictions

def save_predictions(predictions, output_path):
    """
    Save predictions to CSV file
    """
    if not predictions:
        print("No predictions to save")
        return
    
    df = pd.DataFrame(predictions)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(predictions)} predictions to {output_path}")
    
    # Print summary
    high_risk_cities = df[df['Predicted_Flood_Risk'] == 1]
    print(f"\nSUMMARY:")
    print(f"Total cities analyzed: {len(df)}")
    print(f"High risk cities: {len(high_risk_cities)}")
    
    if not high_risk_cities.empty:
        print("Cities at high flood risk:")
        for _, city in high_risk_cities.iterrows():
            print(f"- {city['City']} (confidence: {city['Confidence']:.2f})")

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    
    # File paths
    cities_path = os.path.join(script_dir, 'cities.csv')
    reservoir_path = os.path.join(script_dir, 'aggregated_reservoir_data.csv')
    model_path = os.path.join(script_dir, 'model.pickle')
    output_path = os.path.join(script_dir, 'current_flood_predictions.csv')
    
    # Generate predictions
    predictions = generate_predictions_for_cities(cities_path, reservoir_path, model_path)
    
    # Save results
    save_predictions(predictions, output_path)