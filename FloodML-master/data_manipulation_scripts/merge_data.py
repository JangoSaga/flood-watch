import csv
import os
import pandas as pd

def merge_all_enhanced_data():
    """Merge all enhanced prediction data into comprehensive dataset"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input files
    # predictions CSV is in the sibling 'training' directory (one level up)
    predictions_file = os.path.join(os.path.dirname(script_dir), 'training', 'current_flood_predictions.csv')
    population_file = os.path.join(script_dir, 'population_data.csv')
    damage_file = os.path.join(script_dir, 'damage_estimates.csv')
    cost_file = os.path.join(script_dir, 'cost_estimates.csv')
    
    # Output file
    output_file = os.path.join(script_dir, 'comprehensive_flood_analysis.csv')
    
    # Check if main predictions file exists
    if not os.path.exists(predictions_file):
        print(f"Predictions file not found: {predictions_file}")
        print("Please run enhanced_forecast.py first.")
        return
    
    # Load main predictions data
    main_df = pd.read_csv(predictions_file)
    
    # Load additional data files
    additional_data = {}
    
    # Population data
    if os.path.exists(population_file):
        pop_df = pd.read_csv(population_file)
        additional_data['population'] = dict(zip(pop_df['City'], pop_df['Population']))
    
    # Damage data
    if os.path.exists(damage_file):
        damage_df = pd.read_csv(damage_file)
        additional_data['damage'] = dict(zip(damage_df['City'], damage_df['Estimated_Damage']))
    
    # Cost data
    if os.path.exists(cost_file):
        cost_df = pd.read_csv(cost_file)
        additional_data['cost'] = dict(zip(cost_df['City'], cost_df['Estimated_Cost_INR']))
    
    # Merge data
    merged_records = []
    
    for _, row in main_df.iterrows():
        city = row['City']
        
        # Create comprehensive record
        merged_record = {
            'City': city,
            'Latitude': row['Latitude'],
            'Longitude': row['Longitude'],
            'Predicted_Flood_Risk': row['Predicted_Flood_Risk'],
            'Confidence': row['Confidence'],
            'Weather_Precip': row['Weather_Precip'],
            'Max_Reservoir_Fill': row['Max_Reservoir_Fill'],
            'Reservoir_Risk_Score': row['Reservoir_Risk_Score'],
            'Prediction_Date': row['Prediction_Date'],
            'Population': additional_data.get('population', {}).get(city, 100000),
            'Estimated_Damage': additional_data.get('damage', {}).get(city, 0),
            'Estimated_Cost_INR': additional_data.get('cost', {}).get(city, 0)
        }
        
        # Add risk category
        if row['Predicted_Flood_Risk'] == 1 and row['Confidence'] > 0.8:
            risk_category = "Critical"
        elif row['Predicted_Flood_Risk'] == 1:
            risk_category = "High"
        elif row['Weather_Precip'] > 30 or row['Max_Reservoir_Fill'] > 70:
            risk_category = "Medium"
        else:
            risk_category = "Low"
        
        merged_record['Risk_Category'] = risk_category
        
        # Add primary risk factor
        if row['Weather_Precip'] > 50 and row['Max_Reservoir_Fill'] > 80:
            risk_factor = "Weather + Reservoir"
        elif row['Weather_Precip'] > 50:
            risk_factor = "Heavy Rainfall"
        elif row['Max_Reservoir_Fill'] > 80:
            risk_factor = "High Reservoir Levels"
        else:
            risk_factor = "Normal Conditions"
        
        merged_record['Primary_Risk_Factor'] = risk_factor
        
        merged_records.append(merged_record)
    
    # Create DataFrame and save
    result_df = pd.DataFrame(merged_records)
    result_df.to_csv(output_file, index=False)
    
    print(f"Comprehensive analysis saved to: {output_file}")
    print(f"Total records: {len(result_df)}")
    print(f"Columns: {list(result_df.columns)}")
    
    # Generate summary statistics
    generate_comprehensive_summary(result_df)
    
    return result_df

def generate_comprehensive_summary(df):
    """Generate comprehensive summary of merged data"""
    print("\n" + "="*60)
    print("COMPREHENSIVE FLOOD ANALYSIS SUMMARY")
    print("="*60)
    
    total_cities = len(df)
    
    # Risk category breakdown
    risk_counts = df['Risk_Category'].value_counts()
    print(f"Risk Category Distribution:")
    for category, count in risk_counts.items():
        percentage = (count / total_cities) * 100
        print(f"  {category}: {count} cities ({percentage:.1f}%)")
    
    # Financial impact
    total_cost = df['Estimated_Cost_INR'].sum()
    total_damage = df['Estimated_Damage'].sum()
    total_population = df['Population'].sum()
    
    print(f"\nFinancial Impact:")
    print(f"  Total estimated cost: ₹{total_cost:,}")
    print(f"  Total estimated damage: {total_damage:,.2f} units")
    print(f"  Total population at risk: {total_population:,}")
    
    # High-risk cities
    high_risk_cities = df[df['Risk_Category'].isin(['Critical', 'High'])]
    if not high_risk_cities.empty:
        print(f"\nHigh-Risk Cities ({len(high_risk_cities)}):")
        for _, city in high_risk_cities.iterrows():
            print(f"  - {city['City']}: {city['Risk_Category']} "
                  f"(₹{city['Estimated_Cost_INR']:,}, {city['Primary_Risk_Factor']})")
    
    # Risk factor analysis
    risk_factors = df['Primary_Risk_Factor'].value_counts()
    print(f"\nPrimary Risk Factor Distribution:")
    for factor, count in risk_factors.items():
        percentage = (count / total_cities) * 100
        print(f"  {factor}: {count} cities ({percentage:.1f}%)")

if __name__ == "__main__":
    merge_all_enhanced_data()
