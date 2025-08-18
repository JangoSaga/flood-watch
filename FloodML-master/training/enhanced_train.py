import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score, precision_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

def load_enhanced_data(data_path):
    """
    Load training data with weather + reservoir features
    """
    print("Loading enhanced training data...")
    data = pd.read_csv(data_path)
    
    print(f"Dataset shape: {data.shape}")
    print(f"Features: {list(data.columns[:-1])}")
    print(f"Target column: {data.columns[-1]}")
    
    # Separate features and target
    X = data.drop('flood_class', axis=1)
    y = data['flood_class']
    
    print(f"Class distribution:")
    print(y.value_counts())
    print(f"Flood percentage: {(y.sum() / len(y) * 100):.1f}%")
    
    return X, y

def train_baseline_model(X_train, y_train, X_test, y_test):
    """
    Train baseline model for comparison
    """
    print("\n" + "="*50)
    print("TRAINING BASELINE MODEL")
    print("="*50)
    
    baseline_rf = RandomForestClassifier(
        n_estimators=50,
        max_depth=8,
        random_state=42
    )
    
    baseline_rf.fit(X_train, y_train)
    baseline_pred = baseline_rf.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, baseline_pred),
        'precision': precision_score(y_test, baseline_pred),
        'recall': recall_score(y_test, baseline_pred),
        'f1': f1_score(y_test, baseline_pred)
    }
    
    print(f"Baseline Results:")
    for metric, value in metrics.items():
        print(f"{metric.capitalize()}: {value:.4f}")
    
    return baseline_rf, metrics

def train_smote_model(X_train, y_train, X_test, y_test):
    """
    Train model with SMOTE oversampling
    """
    print("\n" + "="*50)
    print("TRAINING SMOTE ENHANCED MODEL")
    print("="*50)
    
    # Apply SMOTE
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    print("After SMOTE class distribution:")
    print(pd.Series(y_train_balanced).value_counts())
    
    # Train model
    smote_rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=2,
        random_state=42
    )
    
    smote_rf.fit(X_train_balanced, y_train_balanced)
    smote_pred = smote_rf.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, smote_pred),
        'precision': precision_score(y_test, smote_pred),
        'recall': recall_score(y_test, smote_pred),
        'f1': f1_score(y_test, smote_pred)
    }
    
    print(f"SMOTE Enhanced Results:")
    for metric, value in metrics.items():
        print(f"{metric.capitalize()}: {value:.4f}")
    
    return smote_rf, metrics, X_train_balanced, y_train_balanced

def train_optimized_model(X_train_balanced, y_train_balanced, X_test, y_test):
    """
    Train optimized model with hyperparameter tuning
    """
    print("\n" + "="*50)
    print("TRAINING OPTIMIZED MODEL (SMOTE + TUNING)")
    print("="*50)
    
    # Parameter grid for tuning
    param_distributions = {
        'n_estimators': [100, 150, 200, 250],
        'max_depth': [10, 15, 20, 25],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'criterion': ['gini', 'entropy']
    }
    
    # Randomized search for efficiency
    rf = RandomForestClassifier(random_state=42)
    random_search = RandomizedSearchCV(
        rf, param_distributions, 
        n_iter=30, cv=3, 
        scoring='recall',  # Optimize for recall (important for flood prediction)
        random_state=42, 
        n_jobs=-1, 
        verbose=1
    )
    
    print("Performing hyperparameter tuning...")
    random_search.fit(X_train_balanced, y_train_balanced)
    
    # Get best model
    optimized_rf = random_search.best_estimator_
    optimized_pred = optimized_rf.predict(X_test)
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, optimized_pred),
        'precision': precision_score(y_test, optimized_pred),
        'recall': recall_score(y_test, optimized_pred),
        'f1': f1_score(y_test, optimized_pred)
    }
    
    print(f"Optimized Results:")
    for metric, value in metrics.items():
        print(f"{metric.capitalize()}: {value:.4f}")
    
    print(f"Best parameters: {random_search.best_params_}")
    
    return optimized_rf, metrics

def analyze_feature_importance(model, feature_names):
    """
    Analyze which features are most important
    """
    print("\n" + "="*50)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("="*50)
    
    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values('Importance', ascending=False)
    
    print("Top 10 Most Important Features:")
    print(feature_importance_df.head(10))
    
    # Group by feature type
    weather_features = ['temp_avg', 'temp_max', 'wind_speed', 'cloud_cover', 'precipitation', 'humidity', 'precip_cover']
    reservoir_features = ['avg_reservoir_fill', 'max_reservoir_fill', 'reservoir_risk_score', 'reservoirs_above_danger']
    
    weather_importance = feature_importance_df[feature_importance_df['Feature'].isin(weather_features)]['Importance'].sum()
    reservoir_importance = feature_importance_df[feature_importance_df['Feature'].isin(reservoir_features)]['Importance'].sum()
    
    print(f"\nFeature Type Importance:")
    print(f"Weather Features: {weather_importance:.3f} ({weather_importance/(weather_importance+reservoir_importance)*100:.1f}%)")
    print(f"Reservoir Features: {reservoir_importance:.3f} ({reservoir_importance/(weather_importance+reservoir_importance)*100:.1f}%)")
    
    return feature_importance_df

def compare_models(baseline_metrics, smote_metrics, optimized_metrics):
    """
    Compare all model performances
    """
    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)
    
    comparison_df = pd.DataFrame({
        'Baseline': baseline_metrics,
        'SMOTE Enhanced': smote_metrics,
        'Optimized': optimized_metrics
    }).round(4)
    
    print(comparison_df)
    
    # Calculate improvements
    print("\n=== Improvements over Baseline ===")
    for metric in baseline_metrics.keys():
        smote_improvement = ((smote_metrics[metric] - baseline_metrics[metric]) / baseline_metrics[metric]) * 100
        optimized_improvement = ((optimized_metrics[metric] - baseline_metrics[metric]) / baseline_metrics[metric]) * 100
        
        print(f"{metric.capitalize()}:")
        print(f"  SMOTE: {smote_improvement:+.2f}%")
        print(f"  Optimized: {optimized_improvement:+.2f}%")

def main():
    """
    Main training pipeline
    """
    script_dir = os.path.dirname(__file__)
    
    # File paths
    data_path = os.path.join(script_dir, 'enhanced_training_data.csv')
    model_path = os.path.join(script_dir, 'model.pickle')
    
    # Load data
    X, y = load_enhanced_data(data_path)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTraining set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    
    # Train models
    baseline_model, baseline_metrics = train_baseline_model(X_train, y_train, X_test, y_test)
    smote_model, smote_metrics, X_train_balanced, y_train_balanced = train_smote_model(X_train, y_train, X_test, y_test)
    optimized_model, optimized_metrics = train_optimized_model(X_train_balanced, y_train_balanced, X_test, y_test)
    
    # Compare models
    compare_models(baseline_metrics, smote_metrics, optimized_metrics)
    
    # Analyze feature importance
    feature_importance_df = analyze_feature_importance(optimized_model, X.columns.tolist())
    
    # Save best model
    pickle.dump(optimized_model, open(model_path, 'wb'))
    print(f"\nOptimized model saved to: {model_path}")
    
    # Cross-validation score
    cv_scores = cross_val_score(optimized_model, X_train_balanced, y_train_balanced, cv=5, scoring='recall')
    print(f"Cross-validation recall scores: {cv_scores}")
    print(f"Mean CV recall: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

if __name__ == "__main__":
    main()