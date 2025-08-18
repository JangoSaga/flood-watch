import csv
import os
import pandas as pd

def calculate_damage_estimates():
    """Calculate damage estimates based on enhanced prediction data"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input files
    # predictions CSV is in the sibling 'training' directory (one level up)
    predictions_file = os.path.join(os.path.dirname(script_dir), 'training', 'current_flood_predictions.csv')
    population_file = os.path.join(script_dir, 'population_data.csv')
    
    # Output file
    output_file = os.path.join(script_dir, 'damage_estimates.csv')
    
    if not os.path.exists(predictions_file):
        print(f"Predictions file not found: {predictions_file}")
        print("Please run enhanced_forecast.py first.")
        return
    
    # Load data
    predictions_df = pd.read_csv(predictions_file)
    
    # Load population data if available
    population_data = {}
    if os.path.exists(population_file):
        pop_df = pd.read_csv(population_file)
        population_data = dict(zip(pop_df['City'], pop_df['Population']))
    
    damage_estimates = []
    
    for _, row in predictions_df.iterrows():
        city = row['City']
        precipitation = row['Weather_Precip']
        flood_risk = row['Predicted_Flood_Risk']
        confidence = row['Confidence']
        max_reservoir_fill = row['Max_Reservoir_Fill']
        reservoir_risk_score = row['Reservoir_Risk_Score']
        
        # Get population
        population = population_data.get(city, 100000)  # Default 100k if not found
        
        # Enhanced damage calculation
        # Base damage: population exposure to flooding
        base_damage = (population * precipitation / 10000) if precipitation > 0 else 0
        
        # Apply risk multipliers
        risk_multiplier = 1.0
        
        # Flood prediction multiplier
        if flood_risk == 1:
            risk_multiplier *= (1.2 + confidence * 0.8)  # 1.2 to 2.0x
        else:
            risk_multiplier *= (0.1 + confidence * 0.3)  # 0.1 to 0.4x
        
        # Reservoir risk multiplier
        if max_reservoir_fill > 95:
            risk_multiplier *= 1.5
        elif max_reservoir_fill > 85:
            risk_multiplier *= 1.3
        elif max_reservoir_fill > 70:
            risk_multiplier *= 1.1
        
        # Reservoir risk score multiplier
        risk_multiplier *= (1 + reservoir_risk_score / 20)  # Up to 1.5x additional
        
        # Calculate final damage
        final_damage = base_damage * risk_multiplier
        
        damage_estimates.append([city, round(final_damage, 2)])
    
    # Save damage estimates
    with open(output_file, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['City', 'Estimated_Damage'])
        writer.writerows(damage_estimates)
    
    print(f"Damage estimates saved to: {output_file}")
    
    # Summary
    total_damage = sum(damage[1] for damage in damage_estimates)
    high_damage_cities = [city for city, damage in damage_estimates if damage > 1000]
    
    print(f"\nDAMAGE SUMMARY:")
    print(f"Total estimated damage: {total_damage:,.2f} units")
    print(f"Cities with high damage (>1000 units): {len(high_damage_cities)}")
    
    if high_damage_cities:
        print("High damage cities:")
        for city in high_damage_cities:
            damage = next(d for c, d in damage_estimates if c == city)
            print(f"  - {city}: {damage:,.2f} units")

if __name__ == "__main__":
    calculate_damage_estimates()
