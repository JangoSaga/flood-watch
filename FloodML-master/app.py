# """Web app."""
import flask
from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS

import pickle
import base64
from training import prediction
import requests
import csv
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

app = flask.Flask(__name__)
CORS(app)

# data = [{'name':'Delhi', "sel": "selected"}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}]
# # data = [{'name':'India', "sel": ""}]
# months = [{"name":"May", "sel": ""}, {"name":"June", "sel": ""}, {"name":"July", "sel": "selected"}]
# cities = [{'name':'Delhi', "sel": "selected"}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}, {'name':'New York', "sel": ""}, {'name':'Los Angeles', "sel": ""}, {'name':'London', "sel": ""}, {'name':'Paris', "sel": ""}, {'name':'Sydney', "sel": ""}, {'name':'Beijing', "sel": ""}]

model = pickle.load(open("model.pickle", 'rb'))

# @app.route("/")
# @app.route('/index.html')
# def index() -> str:
#     """Base page."""
#     return flask.render_template("index.html")

# @app.route('/plots.html')
# def plots():
#     return render_template('plots.html')

# @app.route('/heatmaps.html')
# def heatmaps():
#     return render_template('heatmaps.html')

# @app.route('/satellite.html')
# def satellite():
#     direc = "processed_satellite_images/Delhi_July.png"
#     with open(direc, "rb") as image_file:
#         image = base64.b64encode(image_file.read())
#     image = image.decode('utf-8')
#     return render_template('satellite.html', data=data, image_file=image, months=months, text="Delhi in July 2020")

# @app.route('/satellite.html', methods=['GET', 'POST'])
# def satelliteimages():
#     place = request.form.get('place')
#     date = request.form.get('date')
#     data = [{'name':'Delhi', "sel": ""}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}]
#     months = [{"name":"May", "sel": ""}, {"name":"June", "sel": ""}, {"name":"July", "sel": ""}]
#     for item in data:
#         if item["name"] == place:
#             item["sel"] = "selected"
    
#     for item in months:
#         if item["name"] == date:
#             item["sel"] = "selected"

#     text = place + " in " + date + " 2020"

#     direc = "processed_satellite_images/{}_{}.png".format(place, date)
#     with open(direc, "rb") as image_file:
#         image = base64.b64encode(image_file.read())
#     image = image.decode('utf-8')
#     return render_template('satellite.html', data=data, image_file=image, months=months, text=text)

# @app.route('/predicts.html')
# def predicts():
#     return render_template('predicts.html', cities=cities, cityname="Information about the city")

def get_city_coordinates(city_name):
    with open('finalfinal.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['city'].lower() == city_name.lower():
                return float(row['lat']), float(row['lon'])
    return None, None

# @app.route('/predicts.html', methods=["GET", "POST"])
# def get_predicts():
#     try:
#         cityname = request.form["city"]
#         cities = [{'name':'Delhi', "sel": ""}, {'name':'Mumbai', "sel": ""}, {'name':'Kolkata', "sel": ""}, {'name':'Bangalore', "sel": ""}, {'name':'Chennai', "sel": ""}, {'name':'New York', "sel": ""}, {'name':'Los Angeles', "sel": ""}, {'name':'London', "sel": ""}, {'name':'Paris', "sel": ""}, {'name':'Sydney', "sel": ""}, {'name':'Beijing', "sel": ""}]
#         for item in cities:
#             if item['name'] == cityname:
#                 item['sel'] = 'selected'
#         print(cityname)

#         latitude, longitude = get_city_coordinates(cityname)
#         if latitude is None:
#             return render_template('predicts.html', cities=cities, cityname="City not found in our database.")

#         final = prediction.get_data(latitude, longitude)
#         final[4] *= 15
#         if str(model.predict([final])[0]) == "0":
#             pred = "Safe"
#         else:
#             pred = "Unsafe"
        
#         return render_template('predicts.html', cityname="Information about " + cityname, cities=cities, temp=round(final[0], 2), maxt=round(final[1], 2), wspd=round(final[2], 2), cloudcover=round(final[3], 2), percip=round(final[4], 2), humidity=round(final[5], 2), pred = pred)
#     except:
#         error_message = traceback.format_exc()  
#         print(error_message)
#         return render_template('predicts.html', cities=cities, cityname=f"Error: {error_message}")

# if __name__ == "__main__":
#     app.run(debug=True)
# Add these routes to your existing Flask app.py file

from flask import jsonify
import json

@app.route('/api/plots', methods=['GET'])
def get_plots_data():
    """API endpoint for plots page data"""
    try:
        # Read data from your CSV files
        plots_data = []
        
        # Read from finalfinal.csv or your plotting data
        with open('finalfinal.csv', 'r', encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                plots_data.append({
                    'city': row['city'],
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'precipitation': float(row.get('precip', 0)),
                    'prediction': int(float(row.get('class', 0)))
                })
        
        return jsonify(plots_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmaps', methods=['GET'])
def get_heatmaps_data():
    """API endpoint for heatmaps page data"""
    try:
        heatmap_data = []
        
        # Combine data from multiple CSV files
        cities_data = {}
        
        # Read city coordinates
        with open('finalfinal.csv', 'r', encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cities_data[row['city']] = {
                    'city': row['city'],
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'precipitation': float(row.get('precip', 0)),
                    'prediction': int(float(row.get('class', 0))),
                    'damage': float(row.get('damage', 0)) * 1000  # Convert to USD
                }
        
        heatmap_data = list(cities_data.values())
        return jsonify(heatmap_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for predictions"""
    try:
        data = request.get_json()
        city_name = data.get('city')
        
        if not city_name:
            return jsonify({'error': 'City name is required'}), 400
        
        # Get city coordinates
        latitude, longitude = get_city_coordinates(city_name)
        if latitude is None:
            return jsonify({'error': 'City not found in database'}), 404
        
        # Get weather data and prediction
        weather_data = prediction.get_data(latitude, longitude)
        weather_data[4] *= 15  # Adjust precipitation as in original code
        
        prediction_result = model.predict([weather_data])[0]
        
        return jsonify({
            'city': city_name,
            'prediction': "Safe" if str(prediction_result) == "0" else "Unsafe",
            'temp': round(weather_data[0], 2),
            'maxt': round(weather_data[1], 2),
            'wspd': round(weather_data[2], 2),
            'cloudcover': round(weather_data[3], 2),
            'percip': round(weather_data[4], 2),
            'humidity': round(weather_data[5], 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """API endpoint to get list of available cities"""
    try:
        cities = []
        with open('finalfinal.csv', 'r', encoding='UTF-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cities.append(row['city'])
        return jsonify(cities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/satellite', methods=['POST'])
def api_satellite():
    """API endpoint for satellite data"""
    try:
        data = request.get_json()
        city_name = data.get('city', 'Delhi')
        month = data.get('month', 'July')
        
        # Get city coordinates
        latitude, longitude = get_city_coordinates(city_name)
        if latitude is None:
            return jsonify({'error': 'City not found in database'}), 404
        
        # Get weather data for the city
        weather_data = prediction.get_data(latitude, longitude)
        
        # Calculate risk level based on precipitation
        precipitation = weather_data[4] * 15
        cloud_cover = weather_data[3]
        
        if precipitation > 30:
            risk_level = 'High'
        elif precipitation > 15:
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        
        # Try to get satellite image if available
        satellite_image = None
        try:
            image_path = f"processed_satellite_images/{city_name}_{month}.png"
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    satellite_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Could not load satellite image: {e}")
        
        return jsonify({
            'city': city_name,
            'month': month,
            'precipitation': round(precipitation, 1),
            'cloudCover': round(cloud_cover, 1),
            'riskLevel': risk_level,
            'satelliteImage': satellite_image,
            'coordinates': {
                'lat': latitude,
                'lon': longitude
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'FloodML API is running',
        'version': '1.0.0'
    })

# Add CORS support for development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)