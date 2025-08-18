import pandas as pd
import os
from datetime import datetime

def preprocess_wris_data(input_file_path):
    """
    Clean and preprocess raw WRIS dataset
    """
    print("Loading WRIS dataset...")
    df = pd.read_csv(input_file_path)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Convert date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Handle missing values
    numeric_cols = ['FRL', 'Live Cap FRL', 'Level', 'Current Live Storage']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col].fillna(0, inplace=True)
    
    # Remove rows with invalid data
    df = df[df['Current Live Storage'] >= 0]
    df = df[df['Live Cap FRL'] > 0]
    
    # Calculate fill percentage
    df['Fill_Percentage'] = (df['Current Live Storage'] / df['Live Cap FRL']) * 100
    df['Fill_Percentage'] = df['Fill_Percentage'].clip(0, 100)
    
    # Sort by date for trend calculations
    df = df.sort_values(['State', 'District', 'Reservoir Name', 'Date'])
    
    print(f"Processed {len(df)} records")
    return df

def save_processed_data(df, output_path):
    """Save cleaned data"""
    df.to_csv(output_path, index=False)
    print(f"Saved processed data to {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    input_path = os.path.join(script_dir,'wris-data.csv')
    output_path = os.path.join(script_dir,'processed_wris_data.csv')
    
    # Process the data
    processed_df = preprocess_wris_data(input_path)
    save_processed_data(processed_df, output_path)