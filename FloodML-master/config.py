import os
from dotenv import load_dotenv

load_dotenv()

# Visual Crossing Weather API Key
# Get your free API key from: https://www.visualcrossing.com/weather-api
VISUAL_CROSSING_API_KEY = os.getenv('VISUAL_CROSSING_API_KEY', 'demo_key')

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
