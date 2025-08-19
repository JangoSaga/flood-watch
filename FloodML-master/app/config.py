import os
from datetime import timedelta

class Config:
    """Configuration settings for the Enhanced FloodML API"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'enhanced-floodml-secret-key'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # API settings
    API_VERSION = '3.0.0'
    API_TITLE = 'Enhanced Maharashtra FloodML API'
    
    # Data file paths (relative to base directory)
    DATA_FILES = {
        '7DAY_PREDICTIONS': 'data/7day_flood_predictions.csv',
        'DAILY_SUMMARY': 'data/daily_summary.csv',
        'CITY_SUMMARY': 'data/city_summary.csv',
        'RISK_ZONES': 'data/risk_zones.csv',
        'FINAL_PLOT': 'data/final_plot.csv',
        'CITIES': 'data/cities.csv'  # Fallback for city coordinates
    }
    
    # Response settings
    MAX_RECORDS_PER_REQUEST = 1000
    DEFAULT_PAGINATION_SIZE = 50
    
    # Cache settings (if implementing caching later)
    CACHE_TIMEOUT = timedelta(minutes=30)
    
    # CORS settings
    CORS_ORIGINS = ['*']  # Configure as needed for production
    
    # Error messages
    ERROR_MESSAGES = {
        'NO_DATA': 'No data available. Please run the forecast generation scripts first.',
        'CITY_NOT_FOUND': 'City not found in available data.',
        'DATE_NOT_FOUND': 'No forecast data available for the specified date.',
        'INVALID_PARAMETERS': 'Invalid request parameters provided.',
        'MISSING_FILES': 'Required data files are missing. Please generate forecasts first.'
    }
    
    # API documentation
    ENDPOINT_DESCRIPTIONS = {
        '/api/forecast/7day': 'Complete 7-day flood predictions for all cities',
        '/api/forecast/city/<city_name>': '7-day forecast for specific city',
        '/api/forecast/date/<date>': 'All city forecasts for specific date',
        '/api/forecast/daily-summary': 'Daily summary statistics',
        '/api/forecast/city-summary': 'City-wise summary statistics',
        '/api/forecast/high-risk': 'Only high-risk predictions',
        '/api/forecast/trends': 'Forecast trend analysis',
        
        '/api/data/cities': 'List of all monitored cities',
        '/api/data/risk-zones': 'Risk zones with alert levels',
        '/api/data/plotting': 'Data formatted for map visualization',
        '/api/data/coordinates/<city_name>': 'Get coordinates for specific city',
        '/api/data/dates': 'Available forecast dates',
        '/api/data/export/<data_type>': 'Export specific data type',
        
        '/api/analysis/overview': 'Comprehensive analysis overview',
        '/api/analysis/risk-distribution': 'Risk level and alert distributions',
        '/api/analysis/trends': 'Trend analysis across forecast period',
        '/api/analysis/city-comparison': 'Compare risk metrics across cities',
        '/api/analysis/risk-factors': 'Primary risk factor analysis',
        '/api/analysis/performance-metrics': 'System coverage and performance metrics',
        '/api/analysis/city-rankings': 'City rankings by risk metrics',
        '/api/analysis/weather-impact': 'Weather and reservoir impact on risk',
        '/api/analysis/alert-summary': 'Current alert summary by city and level',
        '/api/health': 'API health check and data availability status'
    }