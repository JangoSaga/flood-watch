from flask import Blueprint, jsonify, request, current_app
from data_loader import to_serializable
import pandas as pd

data_bp = Blueprint('data', __name__)

@data_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of all available cities with basic info"""
    try:
        data_loader = current_app.data_loader
        cities = data_loader.get_city_list()
        
        if not cities:
            return jsonify({
                'error': 'No cities data available'
            }), 404
        
        # Get additional info for each city if available
        cities_info = []
        for city in cities:
            lat, lon = data_loader.get_city_coordinates(city)
            city_forecast = data_loader.get_city_forecast(city)
            
            city_info = {
                'name': city,
                'coordinates': {
                    'lat': lat,
                    'lon': lon
                } if lat and lon else None
            }
            
            # Add current risk status if forecast available
            if city_forecast:
                df = pd.DataFrame(city_forecast)
                current_risk = df.iloc[0]['Predicted_Flood_Risk'] if len(df) > 0 else 0
                avg_probability = df['Flood_Probability'].mean()
                
                city_info.update({
                    'current_risk': int(current_risk),
                    'average_probability': round(avg_probability, 3),
                    'forecast_available': True
                })
            else:
                city_info['forecast_available'] = False
            
            cities_info.append(city_info)
        
        return jsonify(to_serializable({
            'cities': cities_info,
            'count': len(cities_info)
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/risk-zones', methods=['GET'])
def get_risk_zones():
    """Get risk zones data with alert levels"""
    try:
        data_loader = current_app.data_loader
        risk_zones = data_loader.load_risk_zones()
        
        if risk_zones is None:
            return jsonify({
                'error': 'No risk zones data available',
                'message': 'Please run enhanced_plotting.py to generate risk zones'
            }), 404
        
        # Optional filters
        risk_level_filter = request.args.get('risk_level')
        alert_level_filter = request.args.get('alert_level')
        date_filter = request.args.get('date')
        # Group by city by default; clients can opt out with group_by_city=false
        group_by_city = request.args.get('group_by_city', 'true').lower() == 'true'
        
        filtered_zones = risk_zones
        
        if risk_level_filter:
            filtered_zones = [
                zone for zone in filtered_zones 
                if zone['Risk_Level'].lower() == risk_level_filter.lower()
            ]
        
        if alert_level_filter:
            filtered_zones = [
                zone for zone in filtered_zones 
                if zone['Alert_Level'].lower() == alert_level_filter.lower()
            ]
        
        if date_filter:
            filtered_zones = [
                zone for zone in filtered_zones 
                if zone['Date'] == date_filter
            ]
        # Build DataFrame for sorting and potential grouping
        df = pd.DataFrame(filtered_zones)
        if len(df) > 0:
            # Ensure Date is treated as datetime for correct ordering
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            # Sort by City then Date (if present)
            sort_cols = ['City'] + (['Date'] if 'Date' in df.columns else [])
            df = df.sort_values(sort_cols).reset_index(drop=True)

            # Prepare summary
            risk_level_counts = df['Risk_Level'].value_counts().to_dict() if 'Risk_Level' in df.columns else {}
            alert_level_counts = df['Alert_Level'].value_counts().to_dict() if 'Alert_Level' in df.columns else {}

            if group_by_city:
                # Group into one record per city with a days array
                grouped_output = []
                for city, g in df.groupby('City', sort=False):
                    g_out = g.copy()
                    if 'Date' in g_out.columns:
                        g_out['Date'] = g_out['Date'].dt.strftime('%Y-%m-%d')
                    days = g_out.to_dict('records')
                    # Use first row for coordinates if present
                    lat = float(g.iloc[0]['Latitude']) if 'Latitude' in g.columns else None
                    lon = float(g.iloc[0]['Longitude']) if 'Longitude' in g.columns else None
                    grouped_output.append({
                        'City': city,
                        'coordinates': {'lat': lat, 'lon': lon} if lat is not None and lon is not None else None,
                        'days': days,
                        'day_count': len(days)
                    })

                response_payload = {
                    'risk_zones': grouped_output,
                    'grouped': True,
                    'city_count': len(grouped_output),
                    'filters_applied': {
                        'risk_level': risk_level_filter,
                        'alert_level': alert_level_filter,
                        'date': date_filter,
                        'group_by_city': group_by_city
                    },
                    'summary': {
                        'risk_level_distribution': risk_level_counts,
                        'alert_level_distribution': alert_level_counts
                    }
                }
            else:
                # Flat list, but sorted and with formatted date
                df_out = df.copy()
                if 'Date' in df_out.columns:
                    df_out['Date'] = df_out['Date'].dt.strftime('%Y-%m-%d')
                flat_sorted = df_out.to_dict('records')

                response_payload = {
                    'risk_zones': flat_sorted,
                    'count': len(flat_sorted),
                    'grouped': False,
                    'filters_applied': {
                        'risk_level': risk_level_filter,
                        'alert_level': alert_level_filter,
                        'date': date_filter,
                        'group_by_city': group_by_city
                    },
                    'summary': {
                        'risk_level_distribution': risk_level_counts,
                        'alert_level_distribution': alert_level_counts
                    }
                }
        else:
            response_payload = {
                'risk_zones': [],
                'count': 0,
                'grouped': group_by_city,
                'filters_applied': {
                    'risk_level': risk_level_filter,
                    'alert_level': alert_level_filter,
                    'date': date_filter,
                    'group_by_city': group_by_city
                },
                'summary': {
                    'risk_level_distribution': {},
                    'alert_level_distribution': {}
                }
            }

        return jsonify(to_serializable(response_payload))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/plotting', methods=['GET'])
def get_plotting_data():
    """Get final plotting data for map visualization"""
    try:
        data_loader = current_app.data_loader
        plotting_data = data_loader.load_plotting_data()
        
        if plotting_data is None:
            return jsonify({
                'error': 'No plotting data available',
                'message': 'Please run enhanced_plotting.py to generate plotting data'
            }), 404
        
        # Optional filters
        city_filter = request.args.get('city')
        date_filter = request.args.get('date')
        risk_threshold = request.args.get('min_probability', type=float)
        # Group by city by default; clients can opt out with group_by_city=false
        group_by_city = request.args.get('group_by_city', 'true').lower() == 'true'
        
        filtered_data = plotting_data
        
        if city_filter:
            filtered_data = [
                item for item in filtered_data 
                if item['City'].lower() == city_filter.lower()
            ]
        
        if date_filter:
            filtered_data = [
                item for item in filtered_data 
                if item['Date'] == date_filter
            ]
        
        if risk_threshold is not None:
            filtered_data = [
                item for item in filtered_data 
                if item['Flood_Probability'] >= risk_threshold
            ]
        # Build DataFrame for sorting and potential grouping
        df = pd.DataFrame(filtered_data)
        if len(df) > 0:
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            sort_cols = ['City'] + (['Date'] if 'Date' in df.columns else [])
            df = df.sort_values(sort_cols).reset_index(drop=True)

            if group_by_city:
                grouped_output = []
                for city, g in df.groupby('City', sort=False):
                    g_out = g.copy()
                    if 'Date' in g_out.columns:
                        g_out['Date'] = g_out['Date'].dt.strftime('%Y-%m-%d')
                    days = g_out.to_dict('records')
                    lat = float(g.iloc[0]['Latitude']) if 'Latitude' in g.columns else None
                    lon = float(g.iloc[0]['Longitude']) if 'Longitude' in g.columns else None
                    grouped_output.append({
                        'City': city,
                        'coordinates': {'lat': lat, 'lon': lon} if lat is not None and lon is not None else None,
                        'days': days,
                        'day_count': len(days)
                    })

                response_payload = {
                    'plotting_data': grouped_output,
                    'grouped': True,
                    'city_count': len(grouped_output),
                    'filters_applied': {
                        'city': city_filter,
                        'date': date_filter,
                        'min_probability': risk_threshold,
                        'group_by_city': group_by_city
                    }
                }
            else:
                df_out = df.copy()
                if 'Date' in df_out.columns:
                    df_out['Date'] = df_out['Date'].dt.strftime('%Y-%m-%d')
                flat_sorted = df_out.to_dict('records')

                response_payload = {
                    'plotting_data': flat_sorted,
                    'count': len(flat_sorted),
                    'grouped': False,
                    'filters_applied': {
                        'city': city_filter,
                        'date': date_filter,
                        'min_probability': risk_threshold,
                        'group_by_city': group_by_city
                    }
                }
        else:
            response_payload = {
                'plotting_data': [],
                'count': 0,
                'grouped': group_by_city,
                'filters_applied': {
                    'city': city_filter,
                    'date': date_filter,
                    'min_probability': risk_threshold,
                    'group_by_city': group_by_city
                }
            }

        return jsonify(to_serializable(response_payload))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/coordinates/<city_name>', methods=['GET'])
def get_city_coordinates(city_name):
    """Get coordinates for a specific city"""
    try:
        data_loader = current_app.data_loader
        lat, lon = data_loader.get_city_coordinates(city_name)
        
        if lat is None or lon is None:
            return jsonify({
                'error': f'Coordinates not found for {city_name}'
            }), 404
        
        return jsonify(to_serializable({
            'city': city_name,
            'coordinates': {
                'latitude': lat,
                'longitude': lon
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/dates', methods=['GET'])
def get_available_dates():
    """Get list of available forecast dates"""
    try:
        data_loader = current_app.data_loader
        predictions = data_loader.load_7day_predictions()
        
        if predictions is None:
            return jsonify({
                'error': 'No predictions available'
            }), 404
        
        # Get unique dates
        dates = sorted(list(set([p['Date'] for p in predictions])))
        
        # Calculate summary for each date
        date_summaries = []
        for date in dates:
            date_predictions = [p for p in predictions if p['Date'] == date]
            df = pd.DataFrame(date_predictions)
            
            date_summaries.append({
                'date': date,
                'total_cities': len(date_predictions),
                'high_risk_cities': len(df[df['Predicted_Flood_Risk'] == 1]),
                'average_probability': round(df['Flood_Probability'].mean(), 3)
            })
        
        return jsonify(to_serializable({
            'available_dates': dates,
            'date_summaries': date_summaries,
            'forecast_period': f"{len(dates)} days"
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/export/<data_type>', methods=['GET'])
def export_data(data_type):
    """Export specific data type as JSON"""
    try:
        data_loader = current_app.data_loader
        
        export_functions = {
            '7day': data_loader.load_7day_predictions,
            'daily': data_loader.load_daily_summary,
            'cities': data_loader.load_city_summary,
            'risk_zones': data_loader.load_risk_zones,
            'plotting': data_loader.load_plotting_data
        }
        
        if data_type not in export_functions:
            return jsonify({
                'error': f'Invalid data type: {data_type}',
                'available_types': list(export_functions.keys())
            }), 400
        
        data = export_functions[data_type]()
        
        if data is None:
            return jsonify({
                'error': f'No data available for type: {data_type}'
            }), 404
        
        return jsonify(to_serializable({
            'data_type': data_type,
            'data': data,
            'count': len(data),
            'exported_at': pd.Timestamp.now().isoformat()
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500