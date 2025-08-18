import csv
import pickle
import pandas as pd
import os

def load_model_and_data():
    """
    Load trained model and necessary data files
    """
    script_dir = os.path.dirname(__file__)
    
    # Load model
    model_path = os.path.join(script_dir, 'model.pickle')
    model = pickle.load(open(model_path, 'rb'))
    
    # Load cities coordinates
    cities_path = os.path.join(script_dir, 'cities.csv')
    cities = []
    with open(cities_path, 'r', encoding='UTF-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                cities.append([row[0], float(row[1]), float(row[2])])  # [city, lat, lon]
    
    return model, cities

def get_prediction_data():
    """
    Load current predictions or generate plotting data
    """
    script_dir = os.path.dirname(__file__)
    predictions_path = os.path.join(script_dir, 'current_flood_predictions.csv')
    
    try:
        # Try to load existing predictions
        predictions_df = pd.read_csv(predictions_path)
        print(f"Loaded {len(predictions_df)} existing predictions")
        
        plotting_data = []
        for _, row in predictions_df.iterrows():
            plotting_data.append([
                row['City'],
                row['Latitude'], 
                row['Longitude'],
                row['Weather_Precip'],
                row['Max_Reservoir_Fill'],
                row['Predicted_Flood_Risk'],
                row['Confidence']
            ])
        
        return plotting_data
        
    except FileNotFoundError:
        print("No existing predictions found. Run enhanced_forecast.py first.")
        return []

def create_plotting_csv(plotting_data):
    """
    Create CSV file for map visualization
    """
    script_dir = os.path.dirname(__file__)
    output_path = os.path.join(script_dir, 'final_plot.csv')
    
    headers = [
        'City', 'Latitude', 'Longitude', 'Precipitation', 
        'Max_Reservoir_Fill', 'Flood_Risk', 'Confidence'
    ]
    
    with open(output_path, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(plotting_data)
    
    print(f"Created plotting data with {len(plotting_data)} cities")
    print(f"Saved to: {output_path}")

def generate_risk_summary(plotting_data):
    """
    Generate summary of flood risk predictions
    """
    if not plotting_data:
        print("No data to summarize")
        return
    
    total_cities = len(plotting_data)
    high_risk_cities = [city for city in plotting_data if city[5] == 1]  # flood_risk = 1
    low_risk_cities = [city for city in plotting_data if city[5] == 0]
    
    print("\n" + "="*50)
    print("FLOOD RISK SUMMARY")
    print("="*50)
    print(f"Total cities analyzed: {total_cities}")
    print(f"High risk cities: {len(high_risk_cities)} ({len(high_risk_cities)/total_cities*100:.1f}%)")
    print(f"Low risk cities: {len(low_risk_cities)} ({len(low_risk_cities)/total_cities*100:.1f}%)")
    
    if high_risk_cities:
        print("\nHIGH RISK CITIES:")
        for city_data in high_risk_cities:
            city_name = city_data[0]
            precipitation = city_data[3]
            reservoir_fill = city_data[4]
            confidence = city_data[6]
            
            print(f"- {city_name}:")
            print(f"  Precipitation: {precipitation:.1f}mm")
            print(f"  Max Reservoir Fill: {reservoir_fill:.1f}%")
            print(f"  Confidence: {confidence:.2f}")
    
    # Risk level distribution
    high_precip_cities = [c for c in plotting_data if c[3] > 50]  # >50mm precipitation
    high_reservoir_cities = [c for c in plotting_data if c[4] > 80]  # >80% reservoir fill
    
    print(f"\nRISK FACTORS:")
    print(f"Cities with heavy precipitation (>50mm): {len(high_precip_cities)}")
    print(f"Cities with high reservoir levels (>80%): {len(high_reservoir_cities)}")

def create_risk_zones_data(plotting_data):
    """
    Create additional data file with risk zone classifications
    """
    script_dir = os.path.dirname(__file__)
    output_path = os.path.join(script_dir, 'risk_zones.csv')
    
    risk_zones = []
    for city_data in plotting_data:
        city_name = city_data[0]
        lat = city_data[1]
        lon = city_data[2]
        precipitation = city_data[3]
        reservoir_fill = city_data[4]
        flood_risk = city_data[5]
        confidence = city_data[6]
        
        # Determine risk level
        if flood_risk == 1 and confidence > 0.8:
            risk_level = "Critical"
        elif flood_risk == 1 and confidence > 0.6:
            risk_level = "High"
        elif precipitation > 30 or reservoir_fill > 70:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Determine primary risk factor
        if precipitation > 50 and reservoir_fill > 80:
            risk_factor = "Weather + Reservoir"
        elif precipitation > 50:
            risk_factor = "Heavy Rainfall"
        elif reservoir_fill > 80:
            risk_factor = "High Reservoir Levels"
        else:
            risk_factor = "Normal Conditions"
        
        risk_zones.append([
            city_name, lat, lon, risk_level, risk_factor, 
            round(precipitation, 1), round(reservoir_fill, 1), round(confidence, 2)
        ])
    
    # Save risk zones data
    headers = [
        'City', 'Latitude', 'Longitude', 'Risk_Level', 'Primary_Risk_Factor',
        'Precipitation_mm', 'Max_Reservoir_Fill_Percent', 'Confidence'
    ]
    
    with open(output_path, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(risk_zones)
    
    print(f"Created risk zones data: {output_path}")

def main():
    """
    Main function to generate plotting data
    """
    print("Generating enhanced plotting data...")
    
    # Load model and cities (for future use if needed)
    model, cities = load_model_and_data()
    
    # Get prediction data
    plotting_data = get_prediction_data()
    
    if not plotting_data:
        print("No prediction data available. Please run enhanced_forecast.py first.")
        return
    
    # Create plotting CSV for map visualization
    create_plotting_csv(plotting_data)
    
    # Generate summary
    generate_risk_summary(plotting_data)
    
    # Create additional risk zones data
    create_risk_zones_data(plotting_data)
    
    print("\nPlotting data generation complete!")
    print("Files created:")
    print("- final_plot.csv (for map visualization)")
    print("- risk_zones.csv (detailed risk analysis)")

if __name__ == "__main__":
    main()