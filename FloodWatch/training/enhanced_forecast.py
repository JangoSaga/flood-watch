import csv
import os
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import requests
import pickle
def get_daily_weather_forecasts(lat, lon, city_name):
    """
    Get 7-day daily weather forecasts (not averaged)
    """
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_mean,temperature_2m_max,wind_speed_10m_max,cloud_cover_mean,precipitation_sum,relative_humidity_2m_mean',
        'forecast_days': 7,  # Changed to 7 days
        'timezone': 'auto'
    }
    
    try:
        print(f"Fetching 7-day forecast for {city_name}...")
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"Forecast API Error: {response.status_code}")
            return []
        
        data = response.json()
        if 'daily' not in data:
            return []
        
        daily_data = data['daily']
        dates = daily_data['time']
        
        # Extract daily forecasts
        daily_forecasts = []
        for i in range(7):  # 7 days
            try:
                day_forecast = [
                    daily_data['temperature_2m_mean'][i] or 0,
                    daily_data['temperature_2m_max'][i] or 0,
                    daily_data['wind_speed_10m_max'][i] or 0,
                    daily_data['cloud_cover_mean'][i] or 0,
                    daily_data['precipitation_sum'][i] or 0,
                    daily_data['relative_humidity_2m_mean'][i] or 0,
                    1 if (daily_data['precipitation_sum'][i] or 0) > 0 else 0  # precip_cover for day
                ]
                daily_forecasts.append({
                    'date': dates[i],
                    'weather': day_forecast
                })
            except (IndexError, KeyError):
                # If data missing for this day, use zeros
                daily_forecasts.append({
                    'date': dates[i] if i < len(dates) else f"Day_{i+1}",
                    'weather': [0, 0, 0, 0, 0, 0, 0]
                })
        
        return daily_forecasts
        
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return []

def forecast_reservoir_levels(city, aggregated_reservoir_path, days=7):
    """
    Forecast reservoir levels for next 7 days using precomputed CSV if available,
    otherwise a simple heuristic based on recent trend.
    """
    try:
        # First, try to read precomputed forecasts from CSV in the same directory
        data_dir = os.path.dirname(aggregated_reservoir_path)
        precomputed_path = os.path.join(data_dir, 'reservoir_7day_forecasts.csv')
        if os.path.exists(precomputed_path):
            try:
                df_fc = pd.read_csv(precomputed_path)
                df_fc_city = df_fc[df_fc['City'] == city]
                if len(df_fc_city) >= days:
                    df_fc_city = df_fc_city.sort_values('Date').head(days)
                    predictions = []
                    for _, r in df_fc_city.iterrows():
                        predictions.append({
                            'avg_fill': float(r.get('avg_fill', 0)),
                            'max_fill': float(r.get('max_fill', 0)),
                            'risk_score': int(r.get('risk_score', 0)),
                            'above_danger': int(r.get('above_danger', 0))
                        })
                    if len(predictions) == days:
                        return predictions
            except Exception:
                pass  # If precomputed read fails, fall back below

        reservoir_df = pd.read_csv(aggregated_reservoir_path)
        reservoir_df['Date'] = pd.to_datetime(reservoir_df['Date'])
        
        # Get city data
        city_data = reservoir_df[reservoir_df['City'] == city].sort_values('Date')
        if len(city_data) < 14:  # Need minimum data for LSTM
            print(f"Insufficient reservoir data for {city}, using last known values")
            if not city_data.empty:
                last_row = city_data.iloc[-1]
                return [{
                    'avg_fill': last_row['Avg_Reservoir_Fill'],
                    'max_fill': last_row['Max_Reservoir_Fill'],
                    'risk_score': last_row['Reservoir_Risk_Score'],
                    'above_danger': last_row['Reservoirs_Above_Danger']
                }] * 7
            else:
                return [{'avg_fill': 0, 'max_fill': 0, 'risk_score': 0, 'above_danger': 0}] * 7
        
        # Prepare data for LSTM (simplified approach)
        fill_levels = city_data['Avg_Reservoir_Fill'].values[-30:]  # Use last 30 days
        
        # Simple trend-based prediction (since training LSTM needs more data)
        recent_trend = fill_levels[-7:].mean() - fill_levels[-14:-7].mean()
        last_level = fill_levels[-1]
        
        predictions = []
        for day in range(7):
            # Simple linear trend with some random variation
            predicted_level = max(0, min(100, last_level + (recent_trend * (day + 1)) + np.random.normal(0, 2)))
            
            # Calculate derived metrics
            risk_score = 0
            if predicted_level > 90: risk_score = 5
            elif predicted_level > 80: risk_score = 3  
            elif predicted_level > 70: risk_score = 2
            elif predicted_level > 60: risk_score = 1
            
            predictions.append({
                'avg_fill': predicted_level,
                'max_fill': min(100, predicted_level + 5),  # Assume max is slightly higher
                'risk_score': risk_score,
                'above_danger': 1 if predicted_level > 80 else 0
            })
        
        return predictions
        
    except Exception as e:
        print(f"Error forecasting reservoir levels for {city}: {e}")
        return [{'avg_fill': 0, 'max_fill': 0, 'risk_score': 0, 'above_danger': 0}] * 7

def make_daily_flood_predictions(daily_weather_forecasts, daily_reservoir_forecasts, model):
    """
    Make flood predictions for each of the next 7 days with probability scores
    """
    daily_predictions = []
    
    for day in range(7):
        try:
            weather_features = daily_weather_forecasts[day]['weather']
            reservoir_features = [
                daily_reservoir_forecasts[day]['avg_fill'],
                daily_reservoir_forecasts[day]['max_fill'], 
                daily_reservoir_forecasts[day]['risk_score'],
                daily_reservoir_forecasts[day]['above_danger']
            ]
            
            # Combine features and ensure valid feature names
            combined_features = weather_features + reservoir_features

            # Determine expected feature columns
            if hasattr(model, 'feature_names_in_'):
                expected_cols = list(model.feature_names_in_)
            else:
                # Fallback to the training feature order used in enhanced_scraper.py
                expected_cols = [
                    'temp_avg', 'temp_max', 'wind_speed', 'cloud_cover', 'precipitation',
                    'humidity', 'precip_cover', 'avg_reservoir_fill', 'max_reservoir_fill',
                    'reservoir_risk_score', 'reservoirs_above_danger'
                ]

            # Create a single-row DataFrame with proper column names
            X_infer = pd.DataFrame([combined_features], columns=expected_cols)

            # Get prediction and probability
            prediction = model.predict(X_infer)[0]

            try:
                # Get probability scores
                probabilities = model.predict_proba(X_infer)[0]
                flood_probability = probabilities[1]  # Probability of flood (class 1)
            except Exception:
                # If model doesn't support predict_proba, use decision function or default
                flood_probability = 0.8 if prediction == 1 else 0.2
            
            daily_predictions.append({
                'date': daily_weather_forecasts[day]['date'],
                'flood_prediction': int(prediction),
                'flood_probability': float(flood_probability),
                'weather_precip': weather_features[4],
                'max_reservoir_fill': reservoir_features[1]
            })
            
        except Exception as e:
            print(f"Error predicting day {day+1}: {e}")
            daily_predictions.append({
                'date': f"Day_{day+1}",
                'flood_prediction': 0,
                'flood_probability': 0.0,
                'weather_precip': 0,
                'max_reservoir_fill': 0
            })
    
    return daily_predictions

def generate_7day_predictions_for_cities(cities_path, reservoir_data_path, model_path):
    """
    Generate 7-day flood predictions for all cities
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
        reader = csv.DictReader(f)
        for row in reader:
            try:
                city = row['city']
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                cities_coords[city] = {'lat': lat, 'lon': lon}
            except (KeyError, ValueError, TypeError):
                continue
    
    all_predictions = []
    
    for city_name, coords in cities_coords.items():
        print(f"Processing 7-day forecast for {city_name}...")
        
        # Get 7-day weather forecasts
        daily_weather_forecasts = get_daily_weather_forecasts(
            coords['lat'], coords['lon'], city_name
        )
        
        if not daily_weather_forecasts:
            print(f"No weather data available for {city_name}")
            continue
        
        # Get 7-day reservoir forecasts
        daily_reservoir_forecasts = forecast_reservoir_levels(city_name, reservoir_data_path)
        
        # Make daily predictions
        daily_predictions = make_daily_flood_predictions(
            daily_weather_forecasts, daily_reservoir_forecasts, model
        )
        
        # Store results for each day
        for day_pred in daily_predictions:
            prediction_record = {
                'City': city_name,
                'Latitude': coords['lat'],
                'Longitude': coords['lon'],
                'Date': day_pred['date'],
                'Predicted_Flood_Risk': day_pred['flood_prediction'],
                'Flood_Probability': day_pred['flood_probability'],
                'Weather_Precip': day_pred['weather_precip'],
                'Max_Reservoir_Fill': day_pred['max_reservoir_fill'],
                'Prediction_Generated': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            all_predictions.append(prediction_record)
        
        # Print summary for this city
        high_risk_days = sum(1 for p in daily_predictions if p['flood_prediction'] == 1)
        avg_probability = np.mean([p['flood_probability'] for p in daily_predictions])
        print(f"{city_name}: {high_risk_days}/7 high-risk days, avg probability: {avg_probability:.2f}")
    
    return all_predictions

def save_7day_predictions(predictions, output_path):
    """
    Save 7-day predictions to CSV file
    """
    if not predictions:
        print("No predictions to save")
        return
    
    df = pd.DataFrame(predictions)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(predictions)} daily predictions to {output_path}")
    
    # Print summary
    total_city_days = len(df)
    high_risk_predictions = len(df[df['Predicted_Flood_Risk'] == 1])
    unique_cities = df['City'].nunique()
    
    print(f"\n7-DAY FORECAST SUMMARY:")
    print(f"Cities analyzed: {unique_cities}")
    print(f"Total city-day predictions: {total_city_days}")
    print(f"High-risk predictions: {high_risk_predictions} ({high_risk_predictions/total_city_days*100:.1f}%)")
    
    # Show cities with highest average flood probability
    city_avg_prob = df.groupby('City')['Flood_Probability'].mean().sort_values(ascending=False)
    print(f"\nTop 5 cities by average flood probability:")
    for city, prob in city_avg_prob.head().items():
        high_risk_days = len(df[(df['City'] == city) & (df['Predicted_Flood_Risk'] == 1)])
        print(f"- {city}: {prob:.3f} ({high_risk_days}/7 high-risk days)")

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    
    # File paths
    cities_path = os.path.join(script_dir, 'data', 'cities.csv')
    reservoir_path = os.path.join(script_dir, 'data', 'aggregated_reservoir_data.csv')
    model_path = os.path.join(script_dir, 'model.pickle')
    output_path = os.path.join(script_dir, 'data', '7day_flood_predictions.csv')
    
    # Generate 7-day predictions
    predictions = generate_7day_predictions_for_cities(cities_path, reservoir_path, model_path)
    
    # Save results
    save_7day_predictions(predictions, output_path)