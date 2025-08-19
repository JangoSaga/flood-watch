import pandas as pd
import numpy as np
import os
from city_reservoir_mapper import get_district_for_city, get_reservoirs_for_city, calculate_city_weights, FLOOD_THRESHOLDS

def aggregate_reservoirs_by_city(processed_wris_path, cities_list):
    """
    Combine multiple reservoir data per city into single records
    """
    print("Loading processed WRIS data...")
    df = pd.read_csv(processed_wris_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    aggregated_data = []
    
    for city in cities_list:
        print(f"Processing {city}...")
        district = get_district_for_city(city)
        reservoirs = get_reservoirs_for_city(city)
        
        if not reservoirs:
            print(f"No reservoirs mapped for {city}, skipping...")
            continue
            
        weights = calculate_city_weights(city)
        reservoir_names = [r['name'] for r in reservoirs]
        
        # Filter data for this city's reservoirs
        city_data = df[
            (df['District'] == district) & 
            (df['Reservoir Name'].isin(reservoir_names))
        ].copy()
        
        if city_data.empty:
            print(f"No data found for {city} reservoirs")
            continue
            
        # Group by date and aggregate
        for date, date_group in city_data.groupby('Date'):
            city_record = aggregate_single_date(city, date, date_group, weights)
            if city_record:
                aggregated_data.append(city_record)
    
    result_df = pd.DataFrame(aggregated_data)
    print(f"Created {len(result_df)} aggregated city-date records")
    return result_df

def aggregate_single_date(city, date, date_group, weights):
    """
    Aggregate reservoir data for a single city-date combination
    """
    if date_group.empty:
        return None
    
    # Calculate weighted averages
    weighted_fill = 0
    total_weight = 0
    max_fill = 0
    reservoirs_above_danger = 0
    total_storage = 0
    
    for _, reservoir_row in date_group.iterrows():
        reservoir_name = reservoir_row['Reservoir Name']
        fill_pct = reservoir_row['Fill_Percentage']
        storage = reservoir_row['Current Live Storage']
        
        weight = weights.get(reservoir_name, 0)
        
        # Weighted fill percentage
        weighted_fill += fill_pct * weight
        total_weight += weight
        
        # Maximum fill percentage
        max_fill = max(max_fill, fill_pct)
        
        # Count reservoirs above danger level
        if fill_pct > FLOOD_THRESHOLDS['high_risk']:
            reservoirs_above_danger += 1
            
        # Total storage
        total_storage += storage
    
    # Normalize weighted fill if we have weights
    if total_weight > 0:
        avg_fill = weighted_fill / total_weight
    else:
        avg_fill = date_group['Fill_Percentage'].mean()
    
    # Calculate risk score
    risk_score = calculate_flood_risk_score(avg_fill, max_fill, reservoirs_above_danger)
    
    return {
        'City': city,
        'Date': date,
        'Avg_Reservoir_Fill': round(avg_fill, 2),
        'Max_Reservoir_Fill': round(max_fill, 2),
        'Total_Storage': round(total_storage, 3),
        'Reservoirs_Above_Danger': reservoirs_above_danger,
        'Reservoir_Risk_Score': risk_score
    }

def calculate_flood_risk_score(avg_fill, max_fill, reservoirs_above_danger):
    """
    Calculate overall flood risk score based on reservoir data
    """
    risk_score = 0
    
    # Average fill contribution
    if avg_fill > FLOOD_THRESHOLDS['critical_risk']:
        risk_score += 3
    elif avg_fill > FLOOD_THRESHOLDS['high_risk']:
        risk_score += 2
    elif avg_fill > FLOOD_THRESHOLDS['medium_risk']:
        risk_score += 1
        
    # Max fill contribution (most critical reservoir)
    if max_fill > FLOOD_THRESHOLDS['critical_risk']:
        risk_score += 2
    elif max_fill > FLOOD_THRESHOLDS['high_risk']:
        risk_score += 1
        
    # Number of dangerous reservoirs
    risk_score += reservoirs_above_danger
    
    return min(risk_score, 10)  # Cap at 10

def add_temporal_features(df):
    """
    Add trend analysis over time windows
    """
    df = df.sort_values(['City', 'Date']).copy()
    df['Reservoir_Trend_7d'] = 0
    df['Reservoir_Trend_15d'] = 0
    
    for city in df['City'].unique():
        city_mask = df['City'] == city
        city_data = df[city_mask].copy()
        
        # 7-day trend
        city_data['Reservoir_Trend_7d'] = city_data['Avg_Reservoir_Fill'].rolling(
            window=7, min_periods=2
        ).apply(lambda x: x.iloc[-1] - x.iloc[0] if len(x) >= 2 else 0)
        
        # 15-day trend  
        city_data['Reservoir_Trend_15d'] = city_data['Avg_Reservoir_Fill'].rolling(
            window=15, min_periods=2
        ).apply(lambda x: x.iloc[-1] - x.iloc[0] if len(x) >= 2 else 0)
        
        df.loc[city_mask, 'Reservoir_Trend_7d'] = city_data['Reservoir_Trend_7d']
        df.loc[city_mask, 'Reservoir_Trend_15d'] = city_data['Reservoir_Trend_15d']
    
    return df

if __name__ == "__main__":
    import csv
    
    script_dir = os.path.dirname(__file__)
    processed_data_path = os.path.join(script_dir, 'data', 'processed_wris_data.csv')
    output_path = os.path.join(script_dir, 'data', 'aggregated_reservoir_data.csv')
    cities_path = os.path.join(script_dir,'data', 'cities.csv')
    
    # Read all cities from cities.csv
    cities_list = []
    try:
        with open(cities_path, 'r', encoding='UTF-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 1:
                    cities_list.append(row[0])
        print(f"Found {len(cities_list)} cities in cities.csv")
    except FileNotFoundError:
        print("cities.csv not found, using default Maharashtra cities")
        cities_list = ['Mumbai', 'Pune', 'Nashik', 'Nagpur', 'Kolhapur']
    
    # Aggregate reservoir data
    aggregated_df = aggregate_reservoirs_by_city(processed_data_path, cities_list)
    
    # Add temporal features
    aggregated_df = add_temporal_features(aggregated_df)
    
    # Save results
    aggregated_df.to_csv(output_path, index=False)
    print(f"Saved aggregated data to {output_path}")
    print(f"Sample data:\n{aggregated_df.head()}")