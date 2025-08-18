import csv
import os
import pandas as pd

def calculate_cost_and_damage():
    """Calculate cost and damage based on enhanced prediction data"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input files
    predictions_file = os.path.join(script_dir, 'current_flood_predictions.csv')
    population_file = os.path.join(script_dir, 'population_data.csv')
    
    # Output files
    cost_file = os.path.join(script_dir, 'cost_estimates.csv')
    damage_file = os.path.join(script_dir, 'damage_estimates.csv')
    
    if not os.path.exists(predictions_file):
        print(f"Predictions file not found: {predictions_file}")
        print("Please run enhanced_forecast.py first.")
        return
    
    # Load predictions
    predictions_df = pd.read_csv(predictions_file)
    
    # Load population data if available
    population_data = {}
    if os.path.exists(population_file):
        pop_df = pd.read_csv(population_file)
        population_data = dict(zip(pop_df['City'], pop_df['Population']))
    
    cost_estimates = []
    damage_estimates = []
    
    for _, row in predictions_df.iterrows():
        city = row['City']
        precipitation = row['Weather_Precip']
        flood_risk = row['Predicted_Flood_Risk']
        confidence = row['Confidence']
        max_reservoir_fill = row['Max_Reservoir_Fill']
        
        # Get population (default to estimated values if not available)
        population = population_data.get(city, estimate_population(city))
        
        # Calculate damage estimate
        # Base damage calculation: population * precipitation impact * flood multiplier
        base_damage = (population * precipitation / 10000) if precipitation > 0 else 0
        
        # Apply flood risk multiplier
        if flood_risk == 1:  # High flood risk
            damage_multiplier = 1.5 + (confidence * 0.5)  # 1.5 to 2.0 multiplier
        else:
            damage_multiplier = 0.3 + (confidence * 0.2)  # 0.3 to 0.5 multiplier
        
        # Apply reservoir fill multiplier
        if max_reservoir_fill > 90:
            reservoir_multiplier = 1.3
        elif max_reservoir_fill > 80:
            reservoir_multiplier = 1.1
        else:
            reservoir_multiplier = 1.0
        
        final_damage = base_damage * damage_multiplier * reservoir_multiplier
        
        # Calculate cost estimate (damage * economic factor)
        cost_per_damage_unit = 750  # Updated cost factor
        total_cost = int(final_damage * cost_per_damage_unit)
        
        cost_estimates.append([city, total_cost])
        damage_estimates.append([city, round(final_damage, 2)])
    
    # Save cost estimates
    with open(cost_file, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['City', 'Estimated_Cost_INR'])
        writer.writerows(cost_estimates)
    
    # Save damage estimates
    with open(damage_file, 'w', newline='', encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['City', 'Estimated_Damage'])
        writer.writerows(damage_estimates)
    
    print(f"Cost estimates saved to: {cost_file}")
    print(f"Damage estimates saved to: {damage_file}")
    
    # Print summary
    total_cost = sum(cost[1] for cost in cost_estimates)
    total_damage = sum(damage[1] for damage in damage_estimates)
    high_risk_cities = [city for city, _ in cost_estimates if predictions_df[predictions_df['City'] == city]['Predicted_Flood_Risk'].iloc[0] == 1]
    
    print(f"\nSUMMARY:")
    print(f"Total estimated cost: ₹{total_cost:,}")
    print(f"Total estimated damage: {total_damage:,.2f} units")
    print(f"High risk cities: {len(high_risk_cities)}")

def estimate_population(city_name):
    """Estimate population for cities without data"""
    # Default population estimates for Maharashtra cities
    population_estimates = {
        'mumbai': 12442373, 'pune': 3124458, 'kolhapur': 549236, 'nashik': 1486973,
        'nagpur': 2405421, 'aurangabad': 1175116, 'solapur': 951118, 'thane': 1841488,
        'sangli': 502697, 'satara': 120000, 'raigad': 85000, 'ratnagiri': 76000,
        'sindhudurg': 45000, 'palghar': 350000, 'ahmednagar': 350821, 'nanded': 550564,
        'jalgaon': 460228, 'dhule': 341473, 'malegaon': 471312, 'bhiwandi': 709665
    }
    
    return population_estimates.get(city_name.lower(), 100000)  # Default 100k if not found

if __name__ == "__main__":
    calculate_cost_and_damage()
