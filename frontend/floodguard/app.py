import flask
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS

import pickle
import base64
import requests
import csv
import traceback
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = flask.Flask(__name__)
CORS(app)

# Load model with proper path resolution
model_path = os.path.join(BASE_DIR, "training", "model.pickle")
model = pickle.load(open(model_path, 'rb'))
import numpy as np

def to_serializable(obj):
    """Convert numpy/pandas datatypes into native Python types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.ndarray, list, tuple)):
        return [to_serializable(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    return obj

def get_city_coordinates(city_name):
    """Get coordinates for a city from available data files"""
    # First try cities.csv for Maharashtra cities
    try:
        cities_path = os.path.join(BASE_DIR, 'training', 'cities.csv')
        with open(cities_path, 'r', encoding='UTF-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and row[0].lower() == city_name.lower():
                    return float(row[1]), float(row[2])
    except FileNotFoundError:
        pass
    
    # Fallback to finalfinal.csv if it exists
    try:
        finalfinal_path = os.path.join(BASE_DIR, 'finalfinal.csv')
        with open(finalfinal_path, 'r', encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['city'].lower() == city_name.lower():
                    return float(row['lat']), float(row['lon'])
    except FileNotFoundError:
        pass
    
    return None, None

def get_current_weather_forecast(lat, lon, city_name):
    """Get current 15-day weather forecast using enhanced logic"""
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_mean,temperature_2m_max,wind_speed_10m_max,cloud_cover_mean,precipitation_sum,relative_humidity_2m_mean',
        'forecast_days': 15,
        'timezone': 'auto'
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"Forecast API Error: {response.status_code}")
            return [0, 0, 0, 0, 0, 0, 0]
        
        data = response.json()
        if 'daily' not in data:
            return [0, 0, 0, 0, 0, 0, 0]
        
        daily_data = data['daily']
        
        # Calculate forecast metrics using enhanced logic
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

def get_current_reservoir_data(city):
    """Get most recent reservoir data for a city using enhanced logic"""
    try:
        reservoir_path = os.path.join(BASE_DIR, 'training', 'aggregated_reservoir_data.csv')
        if not os.path.exists(reservoir_path):
            print(f"Reservoir data file not found: {reservoir_path}")
            return [0, 0, 0, 0]
        
        reservoir_df = pd.read_csv(reservoir_path)
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

def make_enhanced_prediction(weather_features, reservoir_features):
    """Make flood prediction using combined weather and reservoir features"""
    try:
        # Combine all features as per enhanced model
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

def calculate_risk_category(prediction, confidence, precipitation, reservoir_fill):
    """Calculate risk category using enhanced logic"""
    if prediction == 1 and confidence > 0.8:
        return "Critical"
    elif prediction == 1 and confidence > 0.6:
        return "High"
    elif precipitation > 30 or reservoir_fill > 70:
        return "Medium"
    else:
        return "Low"

def determine_primary_risk_factor(precipitation, reservoir_fill):
    """Determine primary risk factor using enhanced logic"""
    if precipitation > 50 and reservoir_fill > 80:
        return "Weather + Reservoir"
    elif precipitation > 50:
        return "Heavy Rainfall"
    elif reservoir_fill > 80:
        return "High Reservoir Levels"
    else:
        return "Normal Conditions"

@app.route('/api/plots', methods=['GET'])
def get_plots_data():
    """API endpoint for plots page data using enhanced predictions"""
    try:
        plots_data = []
        
        # Try to read from current_flood_predictions.csv first (enhanced data)
        try:
            predictions_path = os.path.join(BASE_DIR, 'training', 'current_flood_predictions.csv')
            if os.path.exists(predictions_path):
                predictions_df = pd.read_csv(predictions_path)
                for _, row in predictions_df.iterrows():
                    plots_data.append({
                        'city': row['City'],
                        'lat': float(row['Latitude']),
                        'lon': float(row['Longitude']),
                        'precipitation': float(row['Weather_Precip']),
                        'prediction': int(row['Predicted_Flood_Risk']),
                        'confidence': float(row['Confidence']),
                        'reservoir_fill': float(row['Max_Reservoir_Fill']),
                        'risk_category': calculate_risk_category(
                            row['Predicted_Flood_Risk'], 
                            row['Confidence'], 
                            row['Weather_Precip'], 
                            row['Max_Reservoir_Fill']
                        )
                    })
                return jsonify(to_serializable( plots_data))
        except Exception as e:
            print(f"Error reading enhanced predictions: {e}")
        
        # Fallback to finalfinal.csv
        try:
            finalfinal_path = os.path.join(BASE_DIR, 'finalfinal.csv')
            with open(finalfinal_path, 'r', encoding='UTF-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    plots_data.append({
                        'city': row['city'],
                        'lat': float(row['lat']),
                        'lon': float(row['lon']),
                        'precipitation': float(row.get('precip', 0)),
                        'prediction': int(float(row.get('class', 0))),
                        'confidence': 0.7,
                        'reservoir_fill': 0,
                        'risk_category': 'Unknown'
                    })
        except FileNotFoundError:
            # Ultimate fallback to cities.csv
            cities_path = os.path.join(BASE_DIR, 'training', 'cities.csv')
            with open(cities_path, 'r', encoding='UTF-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        plots_data.append({
                            'city': row[0],
                            'lat': float(row[1]),
                            'lon': float(row[2]),
                            'precipitation': 0,
                            'prediction': 0,
                            'confidence': 0.5,
                            'reservoir_fill': 0,
                            'risk_category': 'Low'
                        })
        
        return jsonify(to_serializable(plots_data))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmaps', methods=['GET'])
def get_heatmaps_data():
    """API endpoint for heatmaps page data using enhanced analysis"""
    try:
        heatmap_data = []
        
        # Try comprehensive analysis file first
        try:
            comprehensive_path = os.path.join(BASE_DIR, 'analysis', 'comprehensive_flood_analysis.csv')
            if os.path.exists(comprehensive_path):
                comp_df = pd.read_csv(comprehensive_path)
                for _, row in comp_df.iterrows():
                    heatmap_data.append({
                        'city': row['City'],
                        'lat': float(row['Latitude']),
                        'lon': float(row['Longitude']),
                        'precipitation': float(row['Weather_Precip']),
                        'prediction': int(row['Predicted_Flood_Risk']),
                        'damage': float(row['Estimated_Damage']),
                        'cost': float(row['Estimated_Cost_INR']),
                        'population': int(row['Population']),
                        'risk_category': row['Risk_Category']
                    })
                return jsonify(to_serializable(heatmap_data))
        except Exception as e:
            print(f"Error reading comprehensive analysis: {e}")
        
        # Fallback to current predictions
        try:
            predictions_path = os.path.join(BASE_DIR, 'training', 'current_flood_predictions.csv')
            if os.path.exists(predictions_path):
                predictions_df = pd.read_csv(predictions_path)
                for _, row in predictions_df.iterrows():
                    # Calculate basic damage estimate
                    precipitation = row['Weather_Precip']
                    population = 100000  # Default population
                    damage = (population * precipitation / 10000) if precipitation > 0 else 0
                    
                    heatmap_data.append({
                        'city': row['City'],
                        'lat': float(row['Latitude']),
                        'lon': float(row['Longitude']),
                        'precipitation': float(row['Weather_Precip']),
                        'prediction': int(row['Predicted_Flood_Risk']),
                        'damage': damage,
                        'cost': damage * 750,  # Cost per damage unit
                        'population': population,
                        'risk_category': calculate_risk_category(
                            row['Predicted_Flood_Risk'],
                            row['Confidence'],
                            row['Weather_Precip'],
                            row['Max_Reservoir_Fill']
                        )
                    })
                return jsonify(to_serializable(heatmap_data))
        except Exception as e:
            print(f"Error reading predictions: {e}")
        
        # Ultimate fallback to finalfinal.csv
        finalfinal_path = os.path.join(BASE_DIR, 'finalfinal.csv')
        with open(finalfinal_path, 'r', encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                heatmap_data.append({
                    'city': row['city'],
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'precipitation': float(row.get('precip', 0)),
                    'prediction': int(float(row.get('class', 0))),
                    'damage': float(row.get('damage', 0)) * 1000,
                    'cost': float(row.get('damage', 0)) * 750000,
                    'population': 100000,
                    'risk_category': 'Unknown'
                })
        
        return jsonify(to_serializable(heatmap_data))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Enhanced API endpoint for predictions using weather + reservoir data"""
    try:
        data = request.get_json()
        city_name = data.get('city')
        
        if not city_name:
            return jsonify({'error': 'City name is required'}), 400
        
        # Get city coordinates
        latitude, longitude = get_city_coordinates(city_name)
        if latitude is None:
            return jsonify({'error': 'City not found in database'}), 404
        
        # Get enhanced weather data
        weather_data = get_current_weather_forecast(latitude, longitude, city_name)
        
        # Get current reservoir data
        reservoir_data = get_current_reservoir_data(city_name)
        
        # Make enhanced prediction
        prediction_result, confidence = make_enhanced_prediction(weather_data, reservoir_data)
        
        # Calculate risk metrics
        risk_category = calculate_risk_category(
            prediction_result, confidence, weather_data[4], reservoir_data[1]
        )
        
        primary_risk_factor = determine_primary_risk_factor(
            weather_data[4], reservoir_data[1]
        )
        
        # Prepare response with enhanced data
        response_data = {
            'city': city_name,
            'prediction': "Unsafe" if prediction_result == 1 else "Safe",
            'confidence': round(confidence, 3),
            'risk_category': risk_category,
            'primary_risk_factor': primary_risk_factor,
            
            # Weather data
            'weather': {
                'temp_avg': round(weather_data[0], 2),
                'temp_max': round(weather_data[1], 2),
                'wind_speed': round(weather_data[2], 2),
                'cloud_cover': round(weather_data[3], 2),
                'precipitation': round(weather_data[4], 2),
                'humidity': round(weather_data[5], 2),
                'precip_coverage': round(weather_data[6], 2)
            },
            
            # Reservoir data
            'reservoir': {
                'avg_fill': round(reservoir_data[0], 2),
                'max_fill': round(reservoir_data[1], 2),
                'risk_score': round(reservoir_data[2], 2),
                'above_danger': int(reservoir_data[3])
            },
            
            'coordinates': {
                'lat': latitude,
                'lon': longitude
            }
        }
        
        return jsonify(to_serializable(response_data))
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """API endpoint to get list of available cities"""
    try:
        cities = []
        # Try cities.csv first for Maharashtra cities
        try:
            cities_path = os.path.join(BASE_DIR, 'training', 'cities.csv')
            with open(cities_path, 'r', encoding='UTF-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 1:
                        cities.append(row[0])
        except FileNotFoundError:
            # Fall back to finalfinal.csv
            finalfinal_path = os.path.join(BASE_DIR, 'finalfinal.csv')
            with open(finalfinal_path, 'r', encoding='UTF-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cities.append(row['city'])
        
        return jsonify(to_serializable(sorted(cities)))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/satellite', methods=['POST'])
def api_satellite():
    """Enhanced API endpoint for satellite data with reservoir information"""
    try:
        data = request.get_json()
        city_name = data.get('city', 'Mumbai')
        month = data.get('month', 'July')
        
        # Get city coordinates
        latitude, longitude = get_city_coordinates(city_name)
        if latitude is None:
            return jsonify({'error': 'City not found in database'}), 404
        
        # Get enhanced weather data
        weather_data = get_current_weather_forecast(latitude, longitude, city_name)
        
        # Get reservoir data
        reservoir_data = get_current_reservoir_data(city_name)
        
        # Make prediction
        prediction, confidence = make_enhanced_prediction(weather_data, reservoir_data)
        
        # Calculate enhanced risk metrics
        precipitation = weather_data[4]
        cloud_cover = weather_data[3]
        reservoir_fill = reservoir_data[1]
        
        risk_category = calculate_risk_category(prediction, confidence, precipitation, reservoir_fill)
        risk_factor = determine_primary_risk_factor(precipitation, reservoir_fill)
        
        # Try to get satellite image if available
        satellite_image = None
        try:
            image_path = os.path.join(BASE_DIR, "processed_satellite_images", f"{city_name}_{month}.png")
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    satellite_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Could not load satellite image: {e}")
        
        return jsonify(to_serializable({
            'city': city_name,
            'month': month,
            'prediction': prediction,
            'confidence': round(confidence, 3),
            'risk_category': risk_category,
            'primary_risk_factor': risk_factor,
            
            # Weather metrics
            'precipitation': round(precipitation, 1),
            'cloudCover': round(cloud_cover, 1),
            'temperature': round(weather_data[0], 1),
            'humidity': round(weather_data[5], 1),
            
            # Reservoir metrics
            'reservoir_fill': round(reservoir_fill, 1),
            'reservoir_risk_score': round(reservoir_data[2], 2),
            'reservoirs_above_danger': int(reservoir_data[3]),
            
            'satelliteImage': satellite_image,
            'coordinates': {
                'lat': latitude,
                'lon': longitude
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis', methods=['GET'])
def get_comprehensive_analysis():
    """API endpoint for comprehensive flood analysis data"""
    try:
        analysis_path = os.path.join(BASE_DIR, 'analysis', 'comprehensive_flood_analysis.csv')
        
        if os.path.exists(analysis_path):
            analysis_df = pd.read_csv(analysis_path)
            
            # Convert to JSON-friendly format with explicit type conversion
            analysis_data = []
            for _, row in analysis_df.iterrows():
                analysis_data.append({
                    'city': str(row['City']),
                    'latitude': float(row['Latitude']),
                    'longitude': float(row['Longitude']),
                    'flood_risk': int(row['Predicted_Flood_Risk']),
                    'confidence': float(row['Confidence']),
                    'precipitation': float(row['Weather_Precip']),
                    'reservoir_fill': float(row['Max_Reservoir_Fill']),
                    'reservoir_risk_score': float(row['Reservoir_Risk_Score']),
                    'population': int(row['Population']),
                    'estimated_damage': float(row['Estimated_Damage']),
                    'estimated_cost': int(row['Estimated_Cost_INR']),
                    'risk_category': str(row['Risk_Category']),
                    'primary_risk_factor': str(row['Primary_Risk_Factor']),
                    'prediction_date': str(row['Prediction_Date'])
                })
            return jsonify(to_serializable({
                'cities': analysis_data,
                'summary': {
                    'total_cities': int(total_cities),
                    'high_risk_count': int(high_risk_count),
                    'total_cost': int(total_cost),
                    'total_population': int(total_population)
                }
            }))    
            # Generate summary statistics with explicit type conversion
            total_cities = len(analysis_data)
            high_risk_count = len([c for c in analysis_data if c['risk_category'] in ['Critical', 'High']])
            total_cost = int(sum(c['estimated_cost'] for c in analysis_data))
            total_population = int(sum(c['population'] for c in analysis_data))
            
            return jsonify(to_serializable({
                'cities': analysis_data,
                'summary': {
                    'total_cities': int(total_cities),
                    'high_risk_cities': int(high_risk_count),
                    'high_risk_percentage': float(round((high_risk_count / total_cities) * 100, 1)),
                    'total_estimated_cost': int(total_cost),
                    'total_population_at_risk': int(total_population),
                    'average_confidence': float(round(sum(c['confidence'] for c in analysis_data) / total_cities, 3))
                }
            }))
        else:
            return jsonify({'error': 'Comprehensive analysis not available. Run merge_data.py first.'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-zones', methods=['GET'])
def get_risk_zones():
    """API endpoint for risk zones data"""
    try:
        risk_zones_path = os.path.join(BASE_DIR, 'training', 'risk_zones.csv')
        
        if os.path.exists(risk_zones_path):
            risk_df = pd.read_csv(risk_zones_path)
            
            risk_zones_data = []
            for _, row in risk_df.iterrows():
                risk_zones_data.append({
                    'city': str(row['City']),
                    'latitude': float(row['Latitude']),
                    'longitude': float(row['Longitude']),
                    'risk_level': str(row['Risk_Level']),
                    'primary_risk_factor': str(row['Primary_Risk_Factor']),
                    'precipitation': float(row['Precipitation_mm']),
                    'reservoir_fill': float(row['Max_Reservoir_Fill_Percent']),
                    'confidence': float(row['Confidence'])
                })
            
            return jsonify(to_serializable(risk_zones_data))
        else:
            return jsonify({'error': 'Risk zones data not available. Run enhanced_plotting.py first.'}), 404
            
    except Exception as e:
        return jsonify(to_serializable({'error': str(e)})), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check if model is loaded
        model_status = "loaded" if model else "error"
        
        # Check data file availability
        data_files = {
            'cities': os.path.exists(os.path.join(BASE_DIR, 'training', 'cities.csv')),
            'predictions': os.path.exists(os.path.join(BASE_DIR, 'training', 'current_flood_predictions.csv')),
            'reservoir_data': os.path.exists(os.path.join(BASE_DIR, 'training', 'aggregated_reservoir_data.csv')),
            'comprehensive_analysis': os.path.exists(os.path.join(BASE_DIR, 'analysis', 'comprehensive_flood_analysis.csv'))
        }
        
        return jsonify(to_serializable({
            'status': 'healthy',
            'message': 'Enhanced Maharashtra FloodML API is running',
            'version': '2.0.0',
            'model_status': model_status,
            'data_files': data_files,
            'enhancement_features': [
                'Weather + Reservoir predictions',
                'Risk categorization',
                'Comprehensive damage analysis',
                'Population-based cost estimates',
                'Multi-factor risk assessment'
            ]
        }))
    except Exception as e:
        return jsonify(to_serializable({
            'status': 'error',
            'message': str(e)
        })), 500

# Maharashtra-specific enhanced endpoints
@app.route('/api/maharashtra/cities', methods=['GET'])
def get_maharashtra_cities():
    """Get enhanced list of Maharashtra cities with current risk status"""
    try:
        maharashtra_cities = []
        
        # Try to get current prediction data for enhanced city info
        try:
            predictions_path = os.path.join(BASE_DIR, 'training', 'current_flood_predictions.csv')
            if os.path.exists(predictions_path):
                predictions_df = pd.read_csv(predictions_path)
                city_risk_map = dict(zip(predictions_df['City'], predictions_df['Predicted_Flood_Risk']))
                city_confidence_map = dict(zip(predictions_df['City'], predictions_df['Confidence']))
            else:
                city_risk_map = {}
                city_confidence_map = {}
        except:
            city_risk_map = {}
            city_confidence_map = {}
        
        cities_path = os.path.join(BASE_DIR, 'training', 'cities.csv')
        with open(cities_path, 'r', encoding='UTF-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    city_name = row[0]
                    flood_risk = city_risk_map.get(city_name, 0)
                    confidence = city_confidence_map.get(city_name, 0.5)
                    
                    # Determine if flood prone based on enhanced criteria
                    flood_prone_cities = ['Mumbai', 'Pune', 'Kolhapur', 'Sangli', 'Nashik', 'Nagpur', 
                                        'Aurangabad', 'Thane', 'Satara', 'Raigad', 'Ratnagiri']
                    is_historically_flood_prone = city_name in flood_prone_cities
                    is_currently_at_risk = flood_risk == 1
                    
                    maharashtra_cities.append({
                        'name': city_name,
                        'lat': float(row[1]),
                        'lon': float(row[2]),
                        'flood_prone': is_historically_flood_prone,
                        'current_risk': is_currently_at_risk,
                        'confidence': round(confidence, 3),
                        'risk_category': calculate_risk_category(flood_risk, confidence, 0, 0)
                    })
        
        return jsonify(to_serializable(maharashtra_cities))
    except Exception as e:
        return jsonify(to_serializable({'error': str(e)})), 500

@app.route('/api/maharashtra/flood-history', methods=['GET'])
def get_flood_history():
    """Get historical flood data for Maharashtra"""
    try:
        flood_history = []
        mined_path = os.path.join(BASE_DIR, 'training', 'mined.csv')
        
        if os.path.exists(mined_path):
            with open(mined_path, 'r', encoding='UTF-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        flood_history.append({
                            'city': row[0],
                            'date': row[1]
                        })
        
        return jsonify(to_serializable(flood_history))
    except Exception as e:
        return jsonify(to_serializable({'error': str(e)})), 500

@app.route('/api/maharashtra/summary', methods=['GET'])
def get_maharashtra_summary():
    """Get comprehensive summary of Maharashtra flood risk"""
    try:
        summary_data = {
            'total_cities_monitored': 0,
            'cities_at_high_risk': 0,
            'total_estimated_cost': 0,
            'total_population_at_risk': 0,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'high_risk_cities': [],
            'risk_factors': {}
        }
        
        # Try to get comprehensive analysis data
        try:
            analysis_path = os.path.join(BASE_DIR, 'analysis', 'comprehensive_flood_analysis.csv')
            if os.path.exists(analysis_path):
                analysis_df = pd.read_csv(analysis_path)
                
                summary_data['total_cities_monitored'] = int(len(analysis_df))
                summary_data['cities_at_high_risk'] = int(len(analysis_df[analysis_df['Risk_Category'].isin(['Critical', 'High'])]))
                summary_data['total_estimated_cost'] = int(analysis_df['Estimated_Cost_INR'].sum())
                summary_data['total_population_at_risk'] = int(analysis_df['Population'].sum())
                
                # Get high risk cities
                high_risk_df = analysis_df[analysis_df['Risk_Category'].isin(['Critical', 'High'])]
                for _, city in high_risk_df.iterrows():
                    summary_data['high_risk_cities'].append({
                        'name': str(city['City']),
                        'risk_category': str(city['Risk_Category']),
                        'confidence': float(city['Confidence']),
                        'estimated_cost': int(city['Estimated_Cost_INR']),
                        'primary_risk_factor': str(city['Primary_Risk_Factor'])
                    })
                
                # Risk factors distribution with explicit conversion
                risk_factors = analysis_df['Primary_Risk_Factor'].value_counts().to_dict()
                summary_data['risk_factors'] = {str(k): int(v) for k, v in risk_factors.items()}
                
        except Exception as e:
            print(f"Error reading comprehensive analysis: {e}")
            # Fallback to basic predictions data
            try:
                predictions_path = os.path.join(BASE_DIR, 'training', 'current_flood_predictions.csv')
                if os.path.exists(predictions_path):
                    predictions_df = pd.read_csv(predictions_path)
                    summary_data['total_cities_monitored'] = int(len(predictions_df))
                    summary_data['cities_at_high_risk'] = int(len(predictions_df[predictions_df['Predicted_Flood_Risk'] == 1]))
            except:
                pass
        
        return jsonify(to_serializable(summary_data))
        
    except Exception as e:
        return jsonify(to_serializable({'error': str(e)})), 500

@app.route('/api/enhanced-prediction', methods=['POST'])
def enhanced_prediction():
    """New endpoint specifically for enhanced predictions with full feature set"""
    try:
        data = request.get_json()
        city_name = data.get('city')
        
        if not city_name:
            return jsonify({'error': 'City name is required'}), 400
        
        # Get city coordinates
        latitude, longitude = get_city_coordinates(city_name)
        if latitude is None:
            return jsonify({'error': 'City not found in database'}), 404
        
        # Get enhanced weather and reservoir data
        weather_features = get_current_weather_forecast(latitude, longitude, city_name)
        reservoir_features = get_current_reservoir_data(city_name)
        
        # Make enhanced prediction
        prediction, confidence = make_enhanced_prediction(weather_features, reservoir_features)
        
        # Calculate comprehensive risk assessment
        risk_category = calculate_risk_category(
            prediction, confidence, weather_features[4], reservoir_features[1]
        )
        
        primary_risk_factor = determine_primary_risk_factor(
            weather_features[4], reservoir_features[1]
        )
        
        # Calculate damage and cost estimates
        population = get_city_population(city_name)
        damage_estimate = calculate_damage_estimate(weather_features, reservoir_features, population, prediction, confidence)
        cost_estimate = int(damage_estimate * 750)  # Cost per damage unit
        
        # Prepare comprehensive response
        response_data = {
            'city': city_name,
            'coordinates': {'lat': latitude, 'lon': longitude},
            'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Core prediction
            'flood_prediction': {
                'risk': prediction,
                'confidence': round(confidence, 3),
                'category': risk_category,
                'primary_factor': primary_risk_factor
            },
            
            # Weather analysis
            'weather_analysis': {
                'temperature_avg': round(weather_features[0], 2),
                'temperature_max': round(weather_features[1], 2),
                'wind_speed': round(weather_features[2], 2),
                'cloud_cover': round(weather_features[3], 2),
                'precipitation_total': round(weather_features[4], 2),
                'humidity': round(weather_features[5], 2),
                'precipitation_coverage': round(weather_features[6], 2)
            },
            
            # Reservoir analysis
            'reservoir_analysis': {
                'avg_fill_percentage': round(reservoir_features[0], 2),
                'max_fill_percentage': round(reservoir_features[1], 2),
                'risk_score': round(reservoir_features[2], 2),
                'reservoirs_above_danger': int(reservoir_features[3])
            },
            
            # Impact assessment
            'impact_assessment': {
                'population': population,
                'estimated_damage': round(damage_estimate, 2),
                'estimated_cost_inr': cost_estimate,
                'damage_per_person': round(damage_estimate / population, 4) if population > 0 else 0
            },
            
            # Risk indicators
            'risk_indicators': {
                'heavy_rainfall': weather_features[4] > 50,
                'high_reservoir_levels': reservoir_features[1] > 80,
                'multiple_risk_factors': (weather_features[4] > 30 and reservoir_features[1] > 70),
                'critical_reservoir_risk': reservoir_features[2] > 8,
                'multiple_dangerous_reservoirs': reservoir_features[3] > 1
            }
        }
        
        return jsonify(to_serializable(response_data))
        
    except Exception as e:
        print(f"Enhanced prediction error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def get_city_population(city_name):
    """Get population for a city from population data or estimates"""
    try:
        population_path = os.path.join(BASE_DIR, 'analysis', 'population_data.csv')
        if os.path.exists(population_path):
            pop_df = pd.read_csv(population_path)
            population_data = dict(zip(pop_df['City'], pop_df['Population']))
            return population_data.get(city_name, estimate_population(city_name))
    except:
        pass
    
    return estimate_population(city_name)

def estimate_population(city_name):
    """Estimate population for cities without data"""
    population_estimates = {
        'mumbai': 12442373, 'pune': 3124458, 'kolhapur': 549236, 'nashik': 1486973,
        'nagpur': 2405421, 'aurangabad': 1175116, 'solapur': 951118, 'thane': 1841488,
        'sangli': 502697, 'satara': 120000, 'raigad': 85000, 'ratnagiri': 76000,
        'sindhudurg': 45000, 'palghar': 350000, 'ahmednagar': 350821, 'nanded': 550564,
        'jalgaon': 460228, 'dhule': 341473, 'malegaon': 471312, 'bhiwandi': 709665,
        'panvel': 180413, 'kalyan': 1246381, 'dombivli': 1193000, 'vasai': 1221233,
        'virar': 518922, 'ulhasnagar': 506098, 'chiplun': 70000, 'mahad': 25000,
        'ichalkaranji': 287570, 'karad': 54000, 'miraj': 300000
    }
    
    return population_estimates.get(city_name.lower(), 100000)

def calculate_damage_estimate(weather_features, reservoir_features, population, prediction, confidence):
    """Calculate damage estimate using enhanced logic"""
    precipitation = weather_features[4]
    max_reservoir_fill = reservoir_features[1]
    reservoir_risk_score = reservoir_features[2]
    
    # Base damage calculation
    base_damage = (population * precipitation / 10000) if precipitation > 0 else 0
    
    # Apply risk multipliers
    risk_multiplier = 1.0
    
    # Flood prediction multiplier
    if prediction == 1:
        risk_multiplier *= (1.2 + confidence * 0.8)  # 1.2 to 2.0x
    else:
        risk_multiplier *= (0.1 + confidence * 0.3)  # 0.1 to 0.4x
    
    # Reservoir risk multiplier
    if max_reservoir_fill > 95:
        risk_multiplier *= 1.5
    elif max_reservoir_fill > 85:
        risk_multiplier *= 1.3
    elif max_reservoir_fill > 70:
        risk_multiplier *= 1.1
    
    # Reservoir risk score multiplier
    risk_multiplier *= (1 + reservoir_risk_score / 20)
    
    return base_damage * risk_multiplier

# Add error handlers for better API responses
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': 'Bad request'}), 400

# Add CORS support for development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Route for serving the main application (if you have templates)
@app.route('/')
def index():
    """Main application route"""
    try:
        return render_template('index.html')
    except:
        return jsonify(to_serializable({
            'message': 'Enhanced Maharashtra FloodML API',
            'version': '2.0.0',
            'endpoints': [
                '/api/health',
                '/api/predict',
                '/api/enhanced-prediction',
                '/api/plots',
                '/api/heatmaps',
                '/api/analysis',
                '/api/risk-zones',
                '/api/cities',
                '/api/satellite',
                '/api/maharashtra/cities',
                '/api/maharashtra/flood-history',
                '/api/maharashtra/summary'
            ]
        }))

if __name__ == "__main__":
    print("Starting Enhanced Maharashtra FloodML API...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Model path: {model_path}")
    
    # Check if model exists
    if os.path.exists(model_path):
        print("✓ Model loaded successfully")
    else:
        print("✗ Warning: Model file not found")
    
    # Check data files
    data_files = [
        'training/cities.csv',
        'training/current_flood_predictions.csv',
        'training/aggregated_reservoir_data.csv'
    ]
    
    for file_path in data_files:
        full_path = os.path.join(BASE_DIR, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path} found")
        else:
            print(f"✗ Warning: {file_path} not found")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
