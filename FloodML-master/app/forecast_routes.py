from flask import Blueprint, jsonify, request, current_app
from data_loader import to_serializable
import pandas as pd

forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/7day', methods=['GET'])
def get_7day_forecast():
    """Get complete 7-day flood predictions for all cities"""
    try:
        data_loader = current_app.data_loader
        predictions = data_loader.load_7day_predictions()
        
        if predictions is None:
            return jsonify({
                'error': 'No 7-day predictions available',
                'message': 'Please run enhanced_forecast.py to generate predictions'
            }), 404
        
        # Optional city filter
        city_filter = request.args.get('city')
        if city_filter:
            predictions = [
                p for p in predictions 
                if p['City'].lower() == city_filter.lower()
            ]
        
        # Optional date filter
        date_filter = request.args.get('date')
        if date_filter:
            predictions = [
                p for p in predictions 
                if p['Date'] == date_filter
            ]
        
        return jsonify(to_serializable({
            'predictions': predictions,
            'count': len(predictions),
            'filters_applied': {
                'city': city_filter,
                'date': date_filter
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/city/<city_name>', methods=['GET'])
def get_city_forecast(city_name):
    """Get 7-day forecast for a specific city"""
    try:
        data_loader = current_app.data_loader
        city_forecast = data_loader.get_city_forecast(city_name)
        
        if city_forecast is None:
            return jsonify({
                'error': f'No forecast data available for {city_name}'
            }), 404
        
        # Calculate city-specific summary
        df = pd.DataFrame(city_forecast)
        high_risk_days = len(df[df['Predicted_Flood_Risk'] == 1])
        avg_probability = df['Flood_Probability'].mean()
        max_probability = df['Flood_Probability'].max()
        
        return jsonify(to_serializable({
            'city': city_name,
            'forecast_period': '7 days',
            'daily_forecasts': city_forecast,
            'summary': {
                'high_risk_days': high_risk_days,
                'total_days': len(city_forecast),
                'average_probability': round(avg_probability, 3),
                'peak_probability': round(max_probability, 3),
                'risk_trend': 'increasing' if city_forecast[-1]['Flood_Probability'] > city_forecast[0]['Flood_Probability'] else 'decreasing'
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/date/<target_date>', methods=['GET'])
def get_date_forecast(target_date):
    """Get all city forecasts for a specific date"""
    try:
        data_loader = current_app.data_loader
        date_forecast = data_loader.get_date_forecast(target_date)
        
        if date_forecast is None:
            return jsonify({
                'error': f'No forecast data available for {target_date}'
            }), 404
        
        # Calculate date-specific summary
        df = pd.DataFrame(date_forecast)
        high_risk_cities = len(df[df['Predicted_Flood_Risk'] == 1])
        avg_probability = df['Flood_Probability'].mean()
        
        return jsonify(to_serializable({
            'date': target_date,
            'city_forecasts': date_forecast,
            'summary': {
                'total_cities': len(date_forecast),
                'high_risk_cities': high_risk_cities,
                'high_risk_percentage': round((high_risk_cities / len(date_forecast)) * 100, 1),
                'average_probability': round(avg_probability, 3)
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/daily-summary', methods=['GET'])
def get_daily_summary():
    """Get daily summary statistics across all cities"""
    try:
        data_loader = current_app.data_loader
        daily_summary = data_loader.load_daily_summary()
        
        if daily_summary is None:
            return jsonify({
                'error': 'No daily summary available',
                'message': 'Please run enhanced_plotting.py to generate summaries'
            }), 404
        
        return jsonify(to_serializable({
            'daily_summary': daily_summary,
            'period': f"{len(daily_summary)} days",
            'description': 'Day-wise flood risk statistics across all monitored cities'
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/city-summary', methods=['GET'])
def get_city_summary():
    """Get city-wise summary statistics across the 7-day period"""
    try:
        data_loader = current_app.data_loader
        city_summary = data_loader.load_city_summary()
        
        if city_summary is None:
            return jsonify({
                'error': 'No city summary available',
                'message': 'Please run enhanced_plotting.py to generate summaries'
            }), 404
        
        # Sort by risk level
        sorted_summary = sorted(
            city_summary, 
            key=lambda x: x.get('Avg_Flood_Probability', 0), 
            reverse=True
        )
        
        return jsonify(to_serializable({
            'city_summary': sorted_summary,
            'cities_count': len(city_summary),
            'description': 'City-wise risk analysis over 7-day forecast period'
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/high-risk', methods=['GET'])
def get_high_risk_forecast():
    """Get only high-risk flood predictions"""
    try:
        data_loader = current_app.data_loader
        
        # Optional date filter
        date_filter = request.args.get('date')
        
        if date_filter:
            high_risk_cities = data_loader.get_high_risk_cities(date_filter)
        else:
            high_risk_cities = data_loader.get_high_risk_cities()
        
        if not high_risk_cities:
            return jsonify({
                'message': 'No high-risk cities found',
                'high_risk_predictions': [],
                'count': 0
            })
        
        # Calculate summary
        df = pd.DataFrame(high_risk_cities)
        avg_probability = df['Flood_Probability'].mean()
        max_precipitation = df['Weather_Precip'].max()
        max_reservoir_fill = df['Max_Reservoir_Fill'].max()
        
        return jsonify(to_serializable({
            'high_risk_predictions': high_risk_cities,
            'count': len(high_risk_cities),
            'date_filter': date_filter,
            'summary': {
                'average_probability': round(avg_probability, 3),
                'max_precipitation': round(max_precipitation, 1),
                'max_reservoir_fill': round(max_reservoir_fill, 1),
                'unique_cities': df['City'].nunique() if len(df) > 0 else 0
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/trends', methods=['GET'])
def get_forecast_trends():
    """Get forecast trends analysis"""
    try:
        data_loader = current_app.data_loader
        predictions = data_loader.load_7day_predictions()
        
        if predictions is None:
            return jsonify({
                'error': 'No predictions available for trend analysis'
            }), 404
        
        df = pd.DataFrame(predictions)
        
        # Daily trends
        daily_trends = df.groupby('Date').agg({
            'Predicted_Flood_Risk': 'sum',
            'Flood_Probability': 'mean',
            'Weather_Precip': 'mean',
            'Max_Reservoir_Fill': 'mean'
        }).round(3)
        
        # City trends (cities with most risk days)
        city_trends = df.groupby('City').agg({
            'Predicted_Flood_Risk': 'sum',
            'Flood_Probability': 'mean'
        }).sort_values('Flood_Probability', ascending=False).head(10)
        
        # Risk distribution
        risk_distribution = df['Flood_Probability'].describe()
        
        return jsonify(to_serializable({
            'daily_trends': daily_trends.reset_index().to_dict('records'),
            'top_risk_cities': city_trends.reset_index().to_dict('records'),
            'risk_distribution': {
                'count': int(risk_distribution['count']),
                'mean': round(risk_distribution['mean'], 3),
                'std': round(risk_distribution['std'], 3),
                'min': round(risk_distribution['min'], 3),
                'max': round(risk_distribution['max'], 3),
                'median': round(risk_distribution['50%'], 3)
            },
            'forecast_period': f"{df['Date'].nunique()} days",
            'cities_monitored': df['City'].nunique()
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500