def run_all_calculations():
    """Run all data manipulation calculations in correct order"""
    print("Starting comprehensive data calculation pipeline...")
    
    try:
        # Step 1: Generate population data
        print("\n1. Generating population data...")
        generate_population_data()
        
        # Step 2: Calculate damage estimates
        print("\n2. Calculating damage estimates...")
        calculate_damage_estimates()
        
        # Step 3: Calculate cost estimates
        print("\n3. Calculating cost estimates...")
        calculate_cost_estimates()
        
        # Step 4: Clean accents from data
        print("\n4. Cleaning accents...")
        clean_prediction_file()
        
        # Step 5: Merge all data
        print("\n5. Merging all data...")
        merge_all_enhanced_data()
        
        print("\n" + "="*60)
        print("ALL CALCULATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Generated files:")
        print("- population_data.csv")
        print("- damage_estimates.csv") 
        print("- cost_estimates.csv")
        print("- cleaned_predictions.csv")
        print("- comprehensive_flood_analysis.csv")
        
    except Exception as e:
        print(f"Error in calculation pipeline: {e}")

if __name__ == "__main__":
    # Can run individual functions or the complete pipeline
    run_all_calculations()