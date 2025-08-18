import pandas as pd
import os
from typing import Dict, List, Optional, Union

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITY_DISTRICT_CSV = os.path.join(BASE_DIR, 'city_district_mapping.csv')
CITY_RESERVOIR_CSV = os.path.join(BASE_DIR, 'city_reservoir_mapping.csv')

def load_city_district_mapping() -> Dict[str, str]:
    """Load city to district mapping from CSV"""
    try:
        df = pd.read_csv(CITY_DISTRICT_CSV)
        return dict(zip(df['city'], df['district']))
    except Exception as e:
        print(f"Error loading city-district mapping: {e}")
        return {}

def load_reservoir_mapping() -> Dict[str, List[Dict[str, Union[str, float]]]]:
    """Load city to reservoir mapping from CSV"""
    try:
        df = pd.read_csv(CITY_RESERVOIR_CSV)
        mapping = {}
        
        for city, group in df.groupby('city'):
            mapping[city] = []
            for _, row in group.iterrows():
                mapping[city].append({
                    'name': row['reservoir'],
                    'weight': float(row['weight']) if 'weight' in row else 0.0,
                    'flood_relevance': float(row['flood_relevance']) if 'flood_relevance' in row else 0.7
                })
        return mapping
    except Exception as e:
        print(f"Error loading reservoir mapping: {e}")
        return {}

# Load mappings
CITY_DISTRICT_MAPPING = load_city_district_mapping()
RESERVOIR_MAPPING = load_reservoir_mapping()

def get_reservoir_capacities(wris_data_path: str) -> Dict[str, float]:
    """Extract maximum capacity for each reservoir from WRIS data"""
    try:
        df = pd.read_csv(wris_data_path)
        return df.groupby('Reservoir Name')['Live Cap FRL'].max().to_dict()
    except Exception as e:
        print(f"Error reading WRIS data: {e}")
        return {}

def calculate_flood_relevance(reservoir_name: str, wris_data_path: Optional[str] = None) -> float:
    """Calculate flood relevance based on reservoir capacity."""
    fallback_relevance = 0.7  # Default fallback value
    
    if not wris_data_path or not os.path.exists(wris_data_path):
        return fallback_relevance
    
    try:
        capacities = get_reservoir_capacities(wris_data_path)
        if not capacities:
            return fallback_relevance
            
        reservoir_cap = capacities.get(reservoir_name.upper())
        if not reservoir_cap or pd.isna(reservoir_cap):
            return fallback_relevance
            
        valid_capacities = [cap for cap in capacities.values() if cap > 0]
        if not valid_capacities:
            return fallback_revision
            
        min_cap, max_cap = min(valid_capacities), max(valid_capacities)
        if max_cap == min_cap:
            return fallback_revision
            
        return round(0.5 + 0.5 * ((reservoir_cap - min_cap) / (max_cap - min_cap)), 2)
        
    except Exception as e:
        print(f"Error calculating relevance for {reservoir_name}: {e}")
        return fallback_relevance

def get_reservoirs_for_city(city_name: str, wris_data_path: Optional[str] = None) -> List[Dict[str, Union[str, float]]]:
    """Get list of reservoirs serving a city with auto-calculated flood relevance"""
    reservoirs = RESERVOIR_MAPPING.get(city_name, [])
    
    # If no reservoirs found in mapping, return empty list
    if not reservoirs:
        print(f"No reservoirs found for city: {city_name}")
        return []
    
    # Calculate weights if not provided
    total_weight = sum(r.get('weight', 0) for r in reservoirs)
    if total_weight <= 0:
        # Assign equal weights if no weights provided
        weight = 1.0 / len(reservoirs) if reservoirs else 0
        for r in reservoirs:
            r['weight'] = weight
    
    # Calculate flood relevance if not provided
    for reservoir in reservoirs:
        print(f"  - {reservoir['name']} (weight: {reservoir['weight']:.2f}, relevance: {reservoir['flood_relevance']:.2f})")

        if 'flood_relevance' not in reservoir or reservoir['flood_relevance'] <= 0:
            reservoir['flood_relevance'] = calculate_flood_relevance(
                reservoir['name'], wris_data_path
            )
    
    return reservoirs

def get_district_for_city(city_name: str) -> str:
    """Get district for a given city"""
    return CITY_DISTRICT_MAPPING.get(city_name, "")

def calculate_city_weights(city_name: str, wris_data_path: Optional[str] = None) -> Dict[str, float]:
    """Calculate normalized weights for a city's reservoirs"""
    reservoirs = get_reservoirs_for_city(city_name, wris_data_path)
    if not reservoirs:
        return {}
    
    # Combine capacity weight and flood relevance
    weights = {
        r['name']: r['weight'] * r['flood_relevance']
        for r in reservoirs
    }
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v/total_weight for k, v in weights.items()}
    
    return weights

# Flood risk thresholds
FLOOD_THRESHOLDS = {
    'low_risk': 50,      # Fill percentage below this = low risk
    'medium_risk': 70,   # Between low and medium
    'high_risk': 85,     # Between medium and high  
    'critical_risk': 95  # Above this = critical
}