import requests
import json
import csv
import os
import pandas as pd

def get_city_population_api(city, country='in'):
    """Get city population from OpenDataSoft API"""
    try:
        base_url = 'https://public.opendatasoft.com/api/records/1.0/search/'
        params = {
            'dataset': 'worldcitiespop',
            'q': city,
            'sort': 'population',
            'facet': 'country',
            'refine.country': country
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['records']:
                return data['records'][0]['fields'].get('population', 0)
    except Exception as e:
        print(f"API error for {city}: {e}")
    
    return None

def generate_population_data():
    """Generate population data for cities in current predictions"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    predictions_file = os.path.join(os.path.dirname(script_dir), 'training', 'current_flood_predictions.csv')
    output_file = os.path.join(script_dir, 'population_data.csv')
    
    if not os.path.exists(predictions_file):
        print(f"Predictions file not found: {predictions_file}")
        print("Please run enhanced_forecast.py first.")
        return
    
    # Load predictions to get city list
    predictions_df = pd.read_csv(predictions_file)
    cities = predictions_df['City'].tolist()
    
    # Maharashtra population data (backup)
    maharashtra_populations = {
        'mumbai': 12442373, 'pune': 3124458, 'kolhapur': 549236, 'nashik': 1486973,
        'nagpur': 2405421, 'aurangabad': 1175116, 'solapur': 951118, 'thane': 1841488,
        'sangli': 502697, 'satara': 120000, 'raigad': 85000, 'ratnagiri': 76000,
        'sindhudurg': 45000, 'palghar': 350000, 'ahmednagar': 350821, 'chiplun': 70000,
        'mahad': 25000, 'ichalkaranji': 287570, 'karad': 54000, 'miraj': 300000,
        'nanded': 550564, 'jalgaon': 460228, 'dhule': 341473, 'malegaon': 471312,
        'bhiwandi': 709665, 'panvel': 180413, 'kalyan': 1246381, 'dombivli': 1193000,
        'vasai': 1221233, 'virar': 518922, 'ulhasnagar': 506098, 'sangamner': 55000,
        'baramati': 102762, 'osmanabad': 116509, 'beed': 142197, 'hingoli': 129318,
        'parbhani': 307191, 'latur': 382940, 'yavatmal': 128697, 'washim': 74350,
        'buldhana': 114054, 'wardha': 125455, 'chandrapur': 320379, 'gadchiroli': 89396,
        'gondia': 132821, 'bhandara': 93017, 'akola': 563814, 'amravati': 647057
    }
    
    population_data = []
    
    for city in cities:
        print(f"Getting population for {city}...")
        
        # Try API first
        population = get_city_population_api(city)
        
        # If API fails, use backup data
        if population is None or population == 0:
            population = maharashtra_populations.get(city.lower(), 100000)
            print(f"Used backup data for {city}: {population}")
        else:
            print(f"API data for {city}: {population}")
        
        population_data.append([city, population])
    
    # Save population data
    with open(output_file, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['City', 'Population'])
        writer.writerows(population_data)
    
    print(f"Population data saved to: {output_file}")
    return population_data

if __name__ == "__main__":
    generate_population_data()
