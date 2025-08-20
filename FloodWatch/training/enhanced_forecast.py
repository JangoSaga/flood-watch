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
    Forecast reservoir levels for next 7 days using deterministic trend analysis
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
        if len(city_data) < 14:  # Need minimum data for trend analysis
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
        
        # Prepare data for deterministic forecasting
        fill_levels = city_data['Avg_Reservoir_Fill'].values[-30:]  # Use last 30 days
        
        # Calculate trend using rolling averages (more stable than random)
        recent_trend = np.mean(fill_levels[-7:]) - np.mean(fill_levels[-14:-7])
        last_level = fill_levels[-1]
        
        # Calculate seasonal adjustment based on historical patterns
        month = datetime.now().month
        seasonal_adjustment = 0
        if 6 <= month <= 9:  # Monsoon season
            seasonal_adjustment = 2  # Slight increase expected
        elif 3 <= month <= 5:  # Pre-monsoon
            seasonal_adjustment = -1  # Slight decrease expected
        
        predictions = []
        for day in range(7):
            # Deterministic prediction with trend and seasonal component
            predicted_level = last_level + (recent_trend * (day + 1)) + (seasonal_adjustment * (day + 1) * 0.1)
            predicted_level = max(0, min(100, predicted_level))  # Clamp to valid range
            
            # Calculate derived metrics
            risk_score = 0
            if predicted_level > 95: risk_score = 5
            elif predicted_level > 85: risk_score = 4
            elif predicted_level > 75: risk_score = 3
            elif predicted_level > 65: risk_score = 2
            elif predicted_level > 55: risk_score = 1
            
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

def determine_forecast_confidence(day):
    """
    Determine confidence level based on forecast horizon
    """
    if day <= 3:
        return "High"
    else:
        return "Low"

def categorize_flood_risk(probability, weather_precip=0, reservoir_risk=0):
    """
    Categorize flood probability into risk levels with rainfall & reservoir overrides
    """
    # Base categorization (even softer)
    if probability >= 0.5:
        category = "Critical"
    elif probability >= 0.35:
        category = "High"
    elif probability >= 0.2:
        category = "Medium"
    else:
        category = "Low"

    # Rainfall override
    if weather_precip > 100:
        category = "Critical"
    elif weather_precip > 80:
        category = "High"
    elif weather_precip > 50 and category == "Low":
        category = "Medium"

    # Reservoir override
    if reservoir_risk >= 4 and category != "Critical":
        category = "High"

    return category


def make_daily_flood_predictions(daily_weather_forecasts, daily_reservoir_forecasts, model):
    """
    Make flood predictions for each of the next 7 days with probability scores and risk categories
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
            
            risk_category = categorize_flood_risk(
                flood_probability,
                weather_features[4],                # precipitation
                daily_reservoir_forecasts[day]['risk_score']  # reservoir
            )   
            if flood_probability > 0.7 or flood_probability < 0.3:
                confidence = "High"
            else:
                confidence = "Medium" if day <= 3 else "Low"    
            # Explainability: why this risk category was assigned
            reason = []
            if weather_features[4] > 80:   # precipitation
                reason.append(f"Heavy rainfall {weather_features[4]:.1f}mm")
            elif weather_features[4] > 40:
                reason.append(f"Moderate rainfall {weather_features[4]:.1f}mm")

            if reservoir_features[1] > 90:  # max reservoir fill
                reason.append(f"Reservoir critical {reservoir_features[1]:.1f}%")
            elif reservoir_features[1] > 75:
                reason.append(f"Reservoir high {reservoir_features[1]:.1f}%")

            if not reason:
                reason = ["Normal conditions"]

            explanation = "; ".join(reason)
    
            daily_predictions.append({
                'date': daily_weather_forecasts[day]['date'],
                'flood_prediction': int(prediction),
                'flood_probability': float(flood_probability),
                'risk_category': risk_category,
                'confidence': confidence,
                'weather_precip': weather_features[4],
                'max_reservoir_fill': reservoir_features[1],
                'explanation': explanation
            })
            
        except Exception as e:
            print(f"Error predicting day {day+1}: {e}")
            daily_predictions.append({
                'date': f"Day_{day+1}",
                'flood_prediction': 0,
                'flood_probability': 0.0,
                'risk_category': 'Low',
                'confidence': 'Low',
                'weather_precip': 0,
                'max_reservoir_fill': 0,
                'explanation': ""
            })
    
    return daily_predictions

def generate_7day_predictions_for_cities(cities_path, reservoir_data_path, model_path):
    """
    Generate 7-day flood predictions for all cities with risk categories and confidence levels
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
                'Risk_Category': day_pred['risk_category'],
                'Confidence': day_pred['confidence'],
                'Weather_Precip': day_pred['weather_precip'],
                'Max_Reservoir_Fill': day_pred['max_reservoir_fill'],
                'Prediction_Generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'explanation': day_pred['explanation'] 
            }
            
            all_predictions.append(prediction_record)
        
        # Print summary for this city
        high_risk_days = sum(1 for p in daily_predictions if p['flood_prediction'] == 1)
        avg_probability = np.mean([p['flood_probability'] for p in daily_predictions])
        critical_days = sum(1 for p in daily_predictions if p['risk_category'] == 'Critical')
        high_confidence_days = sum(1 for p in daily_predictions if p['confidence'] == 'High')
        
        print(f"{city_name}: {high_risk_days}/7 high-risk days, {critical_days}/7 critical days")
        print(f"  Avg probability: {avg_probability:.2f}, High confidence: {high_confidence_days}/7 days")
    
    return all_predictions

def save_7day_predictions(predictions, output_path):
    """
    Save 7-day predictions to CSV file with enhanced metrics
    """
    if not predictions:
        print("No predictions to save")
        return
    
    df = pd.DataFrame(predictions)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(predictions)} daily predictions to {output_path}")
    
    # Print comprehensive summary
    total_city_days = len(df)
    high_risk_predictions = len(df[df['Predicted_Flood_Risk'] == 1])
    unique_cities = df['City'].nunique()
    
    # Risk category breakdown
    critical_predictions = len(df[df['Risk_Category'] == 'Critical'])
    high_predictions = len(df[df['Risk_Category'] == 'High'])
    medium_predictions = len(df[df['Risk_Category'] == 'Medium'])
    low_predictions = len(df[df['Risk_Category'] == 'Low'])
    
    # Confidence breakdown
    high_confidence = len(df[df['Confidence'] == 'High'])
    low_confidence = len(df[df['Confidence'] == 'Low'])
    
    print(f"\n7-DAY FORECAST SUMMARY:")
    print(f"Cities analyzed: {unique_cities}")
    print(f"Total city-day predictions: {total_city_days}")
    print(f"High-risk predictions: {high_risk_predictions} ({high_risk_predictions/total_city_days*100:.1f}%)")
    
    print(f"\nRisk Category Distribution:")
    print(f"Critical: {critical_predictions} ({critical_predictions/total_city_days*100:.1f}%)")
    print(f"High:     {high_predictions} ({high_predictions/total_city_days*100:.1f}%)")
    print(f"Medium:   {medium_predictions} ({medium_predictions/total_city_days*100:.1f}%)")
    print(f"Low:      {low_predictions} ({low_predictions/total_city_days*100:.1f}%)")
    
    print(f"\nForecast Confidence:")
    print(f"High confidence (Days 1-3): {high_confidence} ({high_confidence/total_city_days*100:.1f}%)")
    print(f"Low confidence (Days 4-7):  {low_confidence} ({low_confidence/total_city_days*100:.1f}%)")
    
    # Show cities with highest average flood probability
    city_avg_prob = df.groupby('City')['Flood_Probability'].mean().sort_values(ascending=False)
    city_risk_breakdown = df.groupby(['City', 'Risk_Category']).size().unstack(fill_value=0)
    # Print examples of High/Medium predictions with reasons
    sample_explanations = df[df['Risk_Category'].isin(['High','Medium'])].head(5)
    print("\nSample explanations for High/Medium risk days:")
    for _, row in sample_explanations.iterrows():
        print(f"- {row['City']} on {row['Date']}: {row['Risk_Category']} ({row['explanation']})")

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    # File paths
    cities_path = os.path.join(project_root, 'data', 'cities.csv')
    reservoir_path = os.path.join(project_root, 'data', 'aggregated_reservoir_data.csv')
    model_path = os.path.join(project_root, 'model.pickle')
    output_path = os.path.join(project_root, 'data', '7day_flood_predictions.csv')
    
    # Generate 7-day predictions
    predictions = generate_7day_predictions_for_cities(cities_path, reservoir_path, model_path)
    
    # Save results
    save_7day_predictions(predictions, output_path)