from flask import Blueprint, jsonify, request, current_app
from data_loader import to_serializable
import pandas as pd
from datetime import datetime

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/overview', methods=['GET'])
def get_analysis_overview():
    """Get comprehensive analysis overview"""
    try:
        data_loader = current_app.data_loader
        summary_stats = data_loader.get_summary_stats()
        
        if summary_stats is None:
            return jsonify({
                'error': 'No prediction data available for analysis'
            }), 404
        
        # Get additional insights
        predictions = data_loader.load_7day_predictions()
        if predictions:
            df = pd.DataFrame(predictions)
            
            # Top risk cities
            city_risk = df.groupby('City').agg({
                'Predicted_Flood_Risk': 'sum',
                'Flood_Probability': 'mean'
            }).sort_values('Flood_Probability', ascending=False).head(5)
            
            # Daily risk progression
            daily_risk = df.groupby('Date')['Predicted_Flood_Risk'].sum().to_dict()
            
            # Weather vs Reservoir risk analysis
            weather_risk = len(df[(df['Weather_Precip'] > 30) & (df['Predicted_Flood_Risk'] == 1)])
            reservoir_risk = len(df[(df['Max_Reservoir_Fill'] > 80) & (df['Predicted_Flood_Risk'] == 1)])
            combined_risk = len(df[(df['Weather_Precip'] > 30) & (df['Max_Reservoir_Fill'] > 80) & (df['Predicted_Flood_Risk'] == 1)])
            
            additional_insights = {
                'top_risk_cities': city_risk.reset_index().to_dict('records'),
                'daily_risk_progression': daily_risk,
                'risk_factor_analysis': {
                    'weather_driven_risks': weather_risk,
                    'reservoir_driven_risks': reservoir_risk,
                    'combined_factor_risks': combined_risk,
                    'total_high_risk': summary_stats['high_risk_predictions']
                }
            }
        else:
            additional_insights = {}
        
        return jsonify(to_serializable({
            'overview': summary_stats,
            'insights': additional_insights
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/risk-distribution', methods=['GET'])
def get_risk_distribution():
    """Get detailed risk distribution analysis"""
    try:
        data_loader = current_app.data_loader
        risk_zones = data_loader.load_risk_zones()
        
        if risk_zones is None:
            return jsonify({
                'error': 'No risk zones data available'
            }), 404
        
        df = pd.DataFrame(risk_zones)
        
        # Risk level distribution
        risk_level_dist = df['Risk_Level'].value_counts().to_dict()
        alert_level_dist = df['Alert_Level'].value_counts().to_dict()
        
        # Primary risk factor distribution
        risk_factor_dist = df['Primary_Risk_Factor'].value_counts().to_dict()
        
        # Geographic distribution (by city)
        city_risk_dist = df.groupby('City').agg({
            'Risk_Level': lambda x: x.mode()[0] if not x.empty else 'Unknown',
            'Flood_Probability': 'mean',
            'Precipitation_mm': 'mean',
            'Max_Reservoir_Fill_Percent': 'mean'
        }).round(3)
        
        # Probability distribution bins
        probability_bins = pd.cut(df['Flood_Probability'], 
                                bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0], 
                                labels=['Very Low', 'Low', 'Medium', 'High', 'Critical'])
        probability_dist = probability_bins.value_counts().to_dict()
        
        return jsonify(to_serializable({
            'risk_distribution': {
                'by_risk_level': risk_level_dist,
                'by_alert_level': alert_level_dist,
                'by_probability_range': {str(k): int(v) for k, v in probability_dist.items() if pd.notna(k)},
                'by_primary_factor': risk_factor_dist
            },
            'geographic_distribution': city_risk_dist.reset_index().to_dict('records'),
            'statistics': {
                'total_zones': len(df),
                'average_probability': round(df['Flood_Probability'].mean(), 3),
                'max_probability': round(df['Flood_Probability'].max(), 3),
                'cities_monitored': df['City'].nunique(),
                'dates_covered': df['Date'].nunique()
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/trends', methods=['GET'])
def get_analysis_trends():
    """Get trend analysis from forecast data"""
    try:
        data_loader = current_app.data_loader
        predictions = data_loader.load_7day_predictions()
        
        if predictions is None:
            return jsonify({
                'error': 'No predictions available for trend analysis'
            }), 404
        
        df = pd.DataFrame(predictions)
        
        # Time series analysis
        daily_trends = df.groupby('Date').agg({
            'Predicted_Flood_Risk': ['sum', 'count'],
            'Flood_Probability': ['mean', 'max'],
            'Weather_Precip': 'mean',
            'Max_Reservoir_Fill': 'mean'
        }).round(3)
        
        # Flatten column names
        daily_trends.columns = [
            'High_Risk_Cities', 'Total_Cities', 'Avg_Probability', 
            'Max_Probability', 'Avg_Precipitation', 'Avg_Reservoir_Fill'
        ]
        
        # City risk trends (showing persistence of risk)
        city_trends = df.groupby('City').agg({
            'Predicted_Flood_Risk': ['sum', 'count'],
            'Flood_Probability': ['mean', 'std', 'max']
        }).round(3)
        
        city_trends.columns = [
            'High_Risk_Days', 'Total_Days', 'Avg_Probability', 
            'Risk_Variability', 'Peak_Probability'
        ]
        
        # Risk progression analysis
        dates = sorted(df['Date'].unique())
        risk_progression = []
        for i, date in enumerate(dates):
            day_data = df[df['Date'] == date]
            risk_progression.append({
                'date': date,
                'day_number': i + 1,
                'high_risk_cities': int(day_data['Predicted_Flood_Risk'].sum()),
                'average_probability': round(day_data['Flood_Probability'].mean(), 3),
                'total_cities': len(day_data)
            })
        
        return jsonify(to_serializable({
            'daily_trends': daily_trends.reset_index().to_dict('records'),
            'city_trends': city_trends.reset_index().to_dict('records'),
            'risk_progression': risk_progression,
            'trend_insights': {
                'forecast_period': f"{len(dates)} days",
                'cities_monitored': df['City'].nunique(),
                'peak_risk_date': max(risk_progression, key=lambda x: x['high_risk_cities'])['date'],
                'most_consistent_high_risk_city': city_trends.idxmax()['High_Risk_Days']
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/city-comparison', methods=['POST'])
def compare_cities():
    """Compare flood risk between multiple cities"""
    try:
        data = request.get_json()
        cities_to_compare = data.get('cities', [])
        
        if not cities_to_compare:
            return jsonify({'error': 'Please provide cities to compare'}), 400
        
        data_loader = current_app.data_loader
        predictions = data_loader.load_7day_predictions()
        
        if predictions is None:
            return jsonify({
                'error': 'No predictions available for comparison'
            }), 404
        
        df = pd.DataFrame(predictions)
        
        # Filter for requested cities
        comparison_data = []
        for city in cities_to_compare:
            city_data = df[df['City'].str.lower() == city.lower()]
            
            if len(city_data) == 0:
                comparison_data.append({
                    'city': city,
                    'data_available': False,
                    'error': 'No data found'
                })
                continue
            
            # Calculate city metrics
            high_risk_days = int(city_data['Predicted_Flood_Risk'].sum())
            avg_probability = city_data['Flood_Probability'].mean()
            peak_probability = city_data['Flood_Probability'].max()
            avg_precipitation = city_data['Weather_Precip'].mean()
            avg_reservoir_fill = city_data['Max_Reservoir_Fill'].mean()
            
            comparison_data.append({
                'city': city,
                'data_available': True,
                'metrics': {
                    'high_risk_days': high_risk_days,
                    'total_forecast_days': len(city_data),
                    'average_probability': round(avg_probability, 3),
                    'peak_probability': round(peak_probability, 3),
                    'average_precipitation': round(avg_precipitation, 1),
                    'average_reservoir_fill': round(avg_reservoir_fill, 1)
                },
                'risk_category': (
                    'Critical' if avg_probability >= 0.8 else
                    'High' if avg_probability >= 0.6 else
                    'Medium' if avg_probability >= 0.4 else
                    'Low'
                )
            })
        
        # Find highest and lowest risk cities
        valid_cities = [c for c in comparison_data if c['data_available']]
        if valid_cities:
            highest_risk = max(valid_cities, key=lambda x: x['metrics']['average_probability'])
            lowest_risk = min(valid_cities, key=lambda x: x['metrics']['average_probability'])
        else:
            highest_risk = lowest_risk = None
        
        return jsonify(to_serializable({
            'comparison': comparison_data,
            'insights': {
                'cities_compared': len(cities_to_compare),
                'cities_with_data': len(valid_cities),
                'highest_risk_city': highest_risk['city'] if highest_risk else None,
                'lowest_risk_city': lowest_risk['city'] if lowest_risk else None
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/risk-factors', methods=['GET'])
def analyze_risk_factors():
    """Analyze primary risk factors across all predictions"""
    try:
        data_loader = current_app.data_loader
        risk_zones = data_loader.load_risk_zones()
        
        if risk_zones is None:
            return jsonify({
                'error': 'No risk zones data available for factor analysis'
            }), 404
        
        df = pd.DataFrame(risk_zones)
        
        # Risk factor distribution
        factor_distribution = df['Primary_Risk_Factor'].value_counts().to_dict()
        
        # Risk factor by risk level
        factor_by_risk = df.groupby(['Primary_Risk_Factor', 'Risk_Level']).size().unstack(fill_value=0)
        
        # Average probability by risk factor
        factor_probability = df.groupby('Primary_Risk_Factor').agg({
            'Flood_Probability': ['mean', 'count', 'std'],
            'Precipitation_mm': 'mean',
            'Max_Reservoir_Fill_Percent': 'mean'
        }).round(3)
        
        factor_probability.columns = [
            'Avg_Probability', 'Count', 'Probability_StdDev',
            'Avg_Precipitation', 'Avg_Reservoir_Fill'
        ]
        
        # Geographic distribution of risk factors
        geographic_factors = df.groupby('City')['Primary_Risk_Factor'].apply(
            lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown'
        ).to_dict()
        
        return jsonify(to_serializable({
            'risk_factor_analysis': {
                'distribution': factor_distribution,
                'by_risk_level': factor_by_risk.to_dict(),
                'statistics': factor_probability.reset_index().to_dict('records'),
                'geographic_distribution': geographic_factors
            },
            'insights': {
                'most_common_factor': max(factor_distribution.items(), key=lambda x: x[1])[0],
                'total_risk_zones': len(df),
                'factors_identified': len(factor_distribution)
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/performance-metrics', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics of the forecasting system"""
    try:
        data_loader = current_app.data_loader
        
        # Get all available data for metrics calculation
        predictions = data_loader.load_7day_predictions()
        daily_summary = data_loader.load_daily_summary()
        city_summary = data_loader.load_city_summary()
        
        if predictions is None:
            return jsonify({
                'error': 'No predictions available for performance analysis'
            }), 404
        
        df = pd.DataFrame(predictions)
        
        # System coverage metrics
        total_city_days = len(df)
        unique_cities = df['City'].nunique()
        unique_dates = df['Date'].nunique()
        
        # Prediction distribution
        high_risk_predictions = len(df[df['Predicted_Flood_Risk'] == 1])
        low_risk_predictions = total_city_days - high_risk_predictions
        
        # Confidence analysis
        avg_confidence = df['Flood_Probability'].mean()
        high_confidence_predictions = len(df[df['Flood_Probability'] >= 0.8])
        
        # Data quality metrics
        complete_records = len(df.dropna())
        data_completeness = (complete_records / total_city_days) * 100
        
        # Risk severity distribution
        critical_risk = len(df[df['Flood_Probability'] >= 0.8])
        high_risk = len(df[(df['Flood_Probability'] >= 0.6) & (df['Flood_Probability'] < 0.8)])
        medium_risk = len(df[(df['Flood_Probability'] >= 0.4) & (df['Flood_Probability'] < 0.6)])
        low_risk = len(df[df['Flood_Probability'] < 0.4])
        
        return jsonify(to_serializable({
            'system_metrics': {
                'coverage': {
                    'total_predictions': total_city_days,
                    'cities_monitored': unique_cities,
                    'forecast_days': unique_dates,
                    'data_completeness_percent': round(data_completeness, 1)
                },
                'prediction_distribution': {
                    'high_risk_predictions': high_risk_predictions,
                    'low_risk_predictions': low_risk_predictions,
                    'high_risk_percentage': round((high_risk_predictions / total_city_days) * 100, 1)
                },
                'confidence_metrics': {
                    'average_confidence': round(avg_confidence, 3),
                    'high_confidence_predictions': high_confidence_predictions,
                    'high_confidence_percentage': round((high_confidence_predictions / total_city_days) * 100, 1)
                },
                'risk_severity_distribution': {
                    'critical': critical_risk,
                    'high': high_risk,
                    'medium': medium_risk,
                    'low': low_risk
                }
            },
            'data_sources': {
                'predictions_available': predictions is not None,
                'daily_summary_available': daily_summary is not None,
                'city_summary_available': city_summary is not None,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/city-rankings', methods=['GET'])
def get_city_rankings():
    """Get cities ranked by various risk metrics"""
    try:
        data_loader = current_app.data_loader
        city_summary = data_loader.load_city_summary()
        
        if city_summary is None:
            return jsonify({
                'error': 'No city summary data available'
            }), 404
        
        df = pd.DataFrame(city_summary)
        
        # Ensure we have the right column names
        required_columns = ['City', 'Avg_Flood_Probability', 'Total_High_Risk_Days', 'Peak_Flood_Probability']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {missing_columns}',
                'available_columns': list(df.columns)
            }), 500
        
        # Create rankings
        rankings = {
            'by_average_probability': df.nlargest(10, 'Avg_Flood_Probability')[
                ['City', 'Avg_Flood_Probability', 'Risk_Category']
            ].to_dict('records'),
            
            'by_high_risk_days': df.nlargest(10, 'Total_High_Risk_Days')[
                ['City', 'Total_High_Risk_Days', 'Avg_Flood_Probability']
            ].to_dict('records'),
            
            'by_peak_risk': df.nlargest(10, 'Peak_Flood_Probability')[
                ['City', 'Peak_Flood_Probability', 'Risk_Category']
            ].to_dict('records')
        }
        
        # Additional metrics
        if 'Risk_Variability' in df.columns:
            rankings['most_variable_risk'] = df.nlargest(5, 'Risk_Variability')[
                ['City', 'Risk_Variability', 'Avg_Flood_Probability']
            ].to_dict('records')
        
        # Risk category distribution
        risk_category_dist = df['Risk_Category'].value_counts().to_dict() if 'Risk_Category' in df.columns else {}
        
        return jsonify(to_serializable({
            'rankings': rankings,
            'summary': {
                'total_cities': len(df),
                'risk_category_distribution': risk_category_dist,
                'highest_risk_city': df.loc[df['Avg_Flood_Probability'].idxmax(), 'City'],
                'lowest_risk_city': df.loc[df['Avg_Flood_Probability'].idxmin(), 'City']
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/weather-impact', methods=['GET'])
def analyze_weather_impact():
    """Analyze the impact of weather conditions on flood predictions"""
    try:
        data_loader = current_app.data_loader
        predictions = data_loader.load_7day_predictions()
        
        if predictions is None:
            return jsonify({
                'error': 'No predictions available for weather impact analysis'
            }), 404
        
        df = pd.DataFrame(predictions)
        
        # Weather condition categories
        df['Precip_Category'] = pd.cut(df['Weather_Precip'], 
                                     bins=[0, 10, 30, 50, 100, float('inf')],
                                     labels=['No Rain', 'Light', 'Moderate', 'Heavy', 'Extreme'])
        
        df['Reservoir_Category'] = pd.cut(df['Max_Reservoir_Fill'],
                                        bins=[0, 40, 60, 80, 95, 100],
                                        labels=['Low', 'Normal', 'High', 'Very High', 'Critical'])
        
        # Weather impact on flood risk
        weather_impact = df.groupby('Precip_Category').agg({
            'Predicted_Flood_Risk': ['sum', 'count', 'mean'],
            'Flood_Probability': 'mean'
        }).round(3)
        
        weather_impact.columns = ['High_Risk_Count', 'Total_Count', 'Risk_Rate', 'Avg_Probability']
        
        # Reservoir impact on flood risk
        reservoir_impact = df.groupby('Reservoir_Category').agg({
            'Predicted_Flood_Risk': ['sum', 'count', 'mean'],
            'Flood_Probability': 'mean'
        }).round(3)
        
        reservoir_impact.columns = ['High_Risk_Count', 'Total_Count', 'Risk_Rate', 'Avg_Probability']
        
        # Combined weather + reservoir analysis
        combined_analysis = df.groupby(['Precip_Category', 'Reservoir_Category']).agg({
            'Predicted_Flood_Risk': 'mean',
            'Flood_Probability': 'mean'
        }).round(3)
        
        # Correlation analysis
        correlations = {
            'precipitation_vs_flood_risk': df['Weather_Precip'].corr(df['Predicted_Flood_Risk']),
            'reservoir_vs_flood_risk': df['Max_Reservoir_Fill'].corr(df['Predicted_Flood_Risk']),
            'precipitation_vs_probability': df['Weather_Precip'].corr(df['Flood_Probability']),
            'reservoir_vs_probability': df['Max_Reservoir_Fill'].corr(df['Flood_Probability'])
        }
        
        return jsonify(to_serializable({
            'weather_impact_analysis': {
                'by_precipitation': weather_impact.reset_index().to_dict('records'),
                'by_reservoir_levels': reservoir_impact.reset_index().to_dict('records'),
                'combined_conditions': combined_analysis.reset_index().to_dict('records')
            },
            'correlations': {k: round(v, 3) for k, v in correlations.items()},
            'insights': {
                'highest_risk_precipitation_category': weather_impact['Risk_Rate'].idxmax(),
                'highest_risk_reservoir_category': reservoir_impact['Risk_Rate'].idxmax(),
                'total_predictions_analyzed': len(df)
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/alert-summary', methods=['GET'])
def get_alert_summary():
    """Get current alert summary based on risk zones"""
    try:
        data_loader = current_app.data_loader
        risk_zones = data_loader.load_risk_zones()
        
        if risk_zones is None:
            return jsonify({
                'error': 'No risk zones data available for alert summary'
            }), 404
        
        df = pd.DataFrame(risk_zones)
        
        # Get latest date data (most recent alerts)
        latest_date = df['Date'].max()
        latest_data = df[df['Date'] == latest_date]
        
        # Alert level summary
        alert_summary = latest_data['Alert_Level'].value_counts().to_dict()
        
        # Cities by alert level
        cities_by_alert = {}
        for alert_level in ['RED', 'ORANGE', 'YELLOW', 'GREEN']:
            cities = latest_data[latest_data['Alert_Level'] == alert_level]['City'].tolist()
            cities_by_alert[alert_level] = cities
        
        # Risk factor breakdown for alerts
        risk_factors_by_alert = latest_data.groupby('Alert_Level')['Primary_Risk_Factor'].value_counts().to_dict()
        
        # Priority cities (RED and ORANGE alerts)
        priority_cities = latest_data[latest_data['Alert_Level'].isin(['RED', 'ORANGE'])].sort_values(
            'Flood_Probability', ascending=False
        )[['City', 'Alert_Level', 'Flood_Probability', 'Primary_Risk_Factor']].to_dict('records')
        
        return jsonify(to_serializable({
            'alert_summary': {
                'alert_date': latest_date,
                'alert_distribution': alert_summary,
                'cities_by_alert_level': cities_by_alert,
                'priority_cities': priority_cities
            },
            'risk_analysis': {
                'risk_factors_by_alert': risk_factors_by_alert,
                'total_cities_monitored': len(latest_data),
                'cities_requiring_immediate_attention': len(priority_cities)
            },
            'recommendations': {
                'immediate_action_required': len(cities_by_alert.get('RED', [])) > 0,
                'monitoring_required': len(cities_by_alert.get('ORANGE', [])) > 0,
                'total_alerts_active': len(latest_data[latest_data['Alert_Level'] != 'GREEN'])
            }
        }))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500