#!/usr/bin/env python3
"""
Setup script for FloodML project
This script helps configure the project and get the required API key.
"""

import os
import sys
import requests
from pathlib import Path

def create_env_file():
    """Create .env file with API key configuration"""
    env_content = """# Visual Crossing Weather API Key
# Get your free API key from: https://www.visualcrossing.com/weather-api
# Sign up for free at: https://www.visualcrossing.com/weather-api
VISUAL_CROSSING_API_KEY=your_api_key_here

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
"""
    
    env_path = Path('.env')
    if env_path.exists():
        print("✅ .env file already exists")
        return
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("📝 Please edit .env file and add your Visual Crossing API key")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('flask', 'flask'),
        ('flask_cors', 'flask-cors'),
        ('requests', 'requests'),
        ('sklearn', 'scikit-learn'),
        ('numpy', 'numpy'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing_packages = []
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} is missing")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required packages are installed")
        return True

def test_api_key(api_key):
    """Test if the API key works"""
    if api_key == 'your_api_key_here' or not api_key:
        return False
    
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/forecast?locations=28.6139,77.2090&aggregateHours=24&unitGroup=us&shortColumnNames=false&contentType=json&key={api_key}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 FloodML Setup Script")
    print("=" * 50)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    if not check_dependencies():
        return
    
    # Create .env file
    print("\n2. Setting up environment...")
    create_env_file()
    
    # Check if API key is configured
    print("\n3. Checking API key...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('VISUAL_CROSSING_API_KEY')
        
        if test_api_key(api_key):
            print("✅ API key is working correctly")
        else:
            print("❌ API key is not configured or invalid")
            print("📝 Please:")
            print("   1. Sign up at: https://www.visualcrossing.com/weather-api")
            print("   2. Get your free API key")
            print("   3. Edit .env file and replace 'your_api_key_here' with your actual key")
    except ImportError:
        print("❌ python-dotenv not installed")
        print("📦 Run: pip install python-dotenv")
        return
    
    print("\n4. Checking data files...")
    required_files = ['model.pickle', 'finalfinal.csv']
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
    
    print("\n🎉 Setup complete!")
    print("\nTo run the project:")
    print("1. Backend: python app.py")
    print("2. Frontend: cd ../frontend/floodguard && npm run dev")
    print("\nThe backend will be available at: http://localhost:5000")
    print("The frontend will be available at: http://localhost:3000")

if __name__ == "__main__":
    main()
