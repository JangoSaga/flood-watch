from flask import Flask
from flask_cors import CORS
from datetime import datetime
import os

# Import route blueprints
from forecast_routes import forecast_bp
from data_routes import data_bp
from analysis_routes import analysis_bp
from data_loader import DataLoader

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Initialize data loader
    app.data_loader = DataLoader(BASE_DIR)
    
    # Register blueprints
    app.register_blueprint(forecast_bp, url_prefix='/api/forecast')
    app.register_blueprint(data_bp, url_prefix='/api/data')
    
    @app.route('/')
    def index():
        """Main application route"""
        return {
            'message': 'Enhanced Maharashtra FloodML API',
            'version': '3.0.0',
            'description': 'Real-time 7-day flood prediction system',
            'endpoints': {
                'forecast': [
                    '/api/forecast/7day',
                    '/api/forecast/daily-summary',
                    '/api/forecast/city-summary'
                ],
                'data': [
                    '/api/data/cities',
                    '/api/data/risk-zones',
                    '/api/data/plotting'
                ],
            },
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        data_status = app.data_loader.check_data_availability()
        
        return {
            'status': 'healthy',
            'message': 'Enhanced Maharashtra FloodML API is running',
            'version': '3.0.0',
            'data_files': data_status,
            'features': [
                '7-day flood forecasting',
                'Real-time risk assessment',
                'City-wise and daily summaries',
                'Risk zone classification',
                'No prediction logic in API (uses pre-generated forecasts)'
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Endpoint not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(400)
    def bad_request_error(error):
        return {'error': 'Bad request'}, 400
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    print("="*60)
    print("ENHANCED MAHARASHTRA FLOODML API v3.0")
    print("="*60)
    print(f"Base directory: {BASE_DIR}")
    
    # Check data availability
    data_status = app.data_loader.check_data_availability()
    print("\nData File Status:")
    for file_name, status in data_status.items():
        status_icon = "✓" if status else "✗"
        print(f"{status_icon} {file_name}")
    
    print(f"\nStarting server at http://localhost:5000")
    print("Available endpoints:")
    print("- /api/health - Health check")
    print("- /api/forecast/* - 7-day forecast data")
    print("- /api/data/* - Cities and risk zones")
    print("- /api/analysis/* - Analysis and trends")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)