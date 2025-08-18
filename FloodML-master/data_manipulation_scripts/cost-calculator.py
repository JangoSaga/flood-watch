import csv
import os
import pandas as pd

def calculate_cost_estimates():
    """Calculate cost estimates based on damage estimates and flood risk"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input files
    # predictions CSV is in the sibling 'training' directory (one level up)
    predictions_file = os.path.join(os.path.dirname(script_dir), 'training', 'current_flood_predictions.csv')
    damage_file = os.path.join(script_dir, 'damage_estimates.csv')
    
    # Output file
    output_file = os.path.join(script_dir, 'cost_estimates.csv')
    
    if not os.path.exists(predictions_file):
        print(f"Predictions file not found: {predictions_file}")
        print("Please run enhanced_forecast.py first.")
        return
    
    # Load predictions
    predictions_df = pd.read_csv(predictions_file)
    
    # Load damage estimates if available
    damage_data = {}
    if os.path.exists(damage_file):
        damage_df = pd.read_csv(damage_file)
        damage_data = dict(zip(damage_df['City'], damage_df['Estimated_Damage']))
    
    cost_estimates = []
    
    for _, row in predictions_df.iterrows():
        city = row['City']
        flood_risk = row['Predicted_Flood_Risk']
        confidence = row['Confidence']
        precipitation = row['Weather_Precip']
        max_reservoir_fill = row['Max_Reservoir_Fill']
        
        # Get damage estimate
        if city in damage_data:
            damage_units = damage_data[city]
        else:
            # Calculate basic damage if not available
            damage_units = precipitation * 10 if precipitation > 0 else 0
        
        # Cost calculation factors
        base_cost_per_unit = 750  # INR per damage unit
        
        # Apply multipliers based on risk factors
        cost_multiplier = 1.0
        
        # Flood risk multiplier
        if flood_risk == 1:
            cost_multiplier *= (1.3 + confidence * 0.7)  # 1.3 to 2.0x
        
        # Reservoir risk multiplier
        if max_reservoir_fill > 90:
            cost_multiplier *= 1.4
        elif max_reservoir_fill > 80:
            cost_multiplier *= 1.2
        
        # Precipitation impact multiplier
        if precipitation > 75:
            cost_multiplier *= 1.3
        elif precipitation > 50:
            cost_multiplier *= 1.1
        
        # Calculate final cost
        total_cost = int(damage_units * base_cost_per_unit * cost_multiplier)
        
        cost_estimates.append([city, total_cost])
    
    # Save cost estimates
    with open(output_file, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['City', 'Estimated_Cost_INR'])
        writer.writerows(cost_estimates)
    
    print(f"Cost estimates saved to: {output_file}")
    
    # Summary
    total_cost = sum(cost[1] for cost in cost_estimates)
    high_cost_cities = [city for city, cost in cost_estimates if cost > 1000000]  # > 10 lakh
    
    print(f"\nCOST SUMMARY:")
    print(f"Total estimated cost: ₹{total_cost:,}")
    print(f"Cities with high cost (>₹10 lakh): {len(high_cost_cities)}")
    
    if high_cost_cities:
        print("High cost cities:")
        for city in high_cost_cities:
            cost = next(c for ct, c in cost_estimates if ct == city)
            print(f"  - {city}: ₹{cost:,}")

if __name__ == "__main__":
    calculate_cost_estimates()
