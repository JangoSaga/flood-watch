
# =====================================
# Updated accent_manipulation.py
# =====================================

import csv
import os

def process_accents(text):
    """Remove accents from text"""
    final = ""
    accent_map = {
        "ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
        "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
        "ã": "a", "ẽ": "e", "ĩ": "i", "õ": "o", "ũ": "u"
    }
    
    for char in text:
        final += accent_map.get(char, char)
    return final

def clean_prediction_file():
    """Clean accents from current flood predictions file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # predictions CSV is in the sibling 'training' directory (one level up)
    input_file = os.path.join(os.path.dirname(script_dir), 'training', 'current_flood_predictions.csv')
    output_file = os.path.join(script_dir, 'cleaned_predictions.csv')
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        print("Please run enhanced_forecast.py first to generate predictions.")
        return
    
    with open(input_file, 'r', encoding='UTF-8') as f_in, \
         open(output_file, 'w', newline='', encoding='UTF-8') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        # Process each row
        for row in reader:
            if row:  # Skip empty rows
                # Clean accents from city name (first column)
                cleaned_row = [process_accents(row[0])] + row[1:]
                writer.writerow(cleaned_row)
    
    print(f"Cleaned predictions saved to: {output_file}")

if __name__ == "__main__":
    clean_prediction_file()