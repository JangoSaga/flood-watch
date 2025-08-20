import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report
)
from sklearn.ensemble import RandomForestClassifier

def load_enhanced_data(data_path):
    """Load training data with flood event labels"""
    print("Loading training data...")
    data = pd.read_csv(data_path)
    X = data.drop('flood_class', axis=1)
    y = data['flood_class']
    
    print(f"Dataset shape: {X.shape}")
    print(f"Flood events: {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"Non-flood events: {(y == 0).sum()} ({(1-y.mean())*100:.1f}%)")
    
    return X, y

def evaluate_model_comprehensive(model, X_test, y_test):
    """Comprehensive model evaluation with academic metrics"""
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]  # Probability of flood class
    
    # Calculate comprehensive metrics
    metrics = {
        'accuracy': accuracy_score(y_test, predictions),
        'precision': precision_score(y_test, predictions, zero_division=0),
        'recall': recall_score(y_test, predictions, zero_division=0),
        'f1_score': f1_score(y_test, predictions, zero_division=0),
        'roc_auc': roc_auc_score(y_test, probabilities),
        'pr_auc': average_precision_score(y_test, probabilities)
    }
    
    # Confusion matrix
    cm = confusion_matrix(y_test, predictions)
    tn, fp, fn, tp = cm.ravel()
    
    # Additional metrics for imbalanced datasets
    metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
    metrics['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0
    metrics['balanced_accuracy'] = (metrics['sensitivity'] + metrics['specificity']) / 2
    
    return metrics, cm

def train_best_model(X_train, y_train, X_test, y_test):
    """Train optimized RandomForest with class balancing"""
    print("\n=== TRAINING OPTIMIZED MODEL (Class-Balanced RandomForest) ===")
    
    # Parameter grid for hyperparameter tuning
    param_distributions = {
        'n_estimators': [100, 150, 200, 250],
        'max_depth': [10, 15, 20, 25, None],
        'min_samples_split': [2, 5, 10, 15],
        'min_samples_leaf': [1, 2, 4, 8],
        'criterion': ['gini', 'entropy'],
        'max_features': ['sqrt', 'log2', None]
    }
    
    # Use class_weight='balanced' instead of SMOTE
    rf = RandomForestClassifier(
        random_state=42, 
        class_weight='balanced',  # Handles imbalanced data
        n_jobs=-1
    )
    
    # Randomized search for efficiency with large parameter space
    random_search = RandomizedSearchCV(
        rf, param_distributions,
        n_iter=50,  # Increased iterations for better optimization
        cv=5,       # 5-fold cross-validation
        scoring='average_precision',  # PR-AUC is better for imbalanced data
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    print("Performing hyperparameter optimization...")
    print("Using PR-AUC as optimization metric (better for imbalanced flood data)")
    
    random_search.fit(X_train, y_train)
    
    # Get best model
    best_model = random_search.best_estimator_
    
    # Comprehensive evaluation
    metrics, cm = evaluate_model_comprehensive(best_model, X_test, y_test)
    
    # Feature importance analysis
    feature_names = X_train.columns if hasattr(X_train, 'columns') else [f'feature_{i}' for i in range(X_train.shape[1])]
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    # Print results
    print("\n" + "="*60)
    print("MODEL EVALUATION RESULTS")
    print("="*60)
    
    print("\nCore Classification Metrics:")
    print(f"Accuracy:           {metrics['accuracy']:.4f}")
    print(f"Precision:          {metrics['precision']:.4f}")
    print(f"Recall (Sensitivity): {metrics['recall']:.4f}")
    print(f"F1-Score:           {metrics['f1_score']:.4f}")
    print(f"Specificity:        {metrics['specificity']:.4f}")
    print(f"Balanced Accuracy:  {metrics['balanced_accuracy']:.4f}")
    
    print("\nImbalanced Dataset Metrics:")
    print(f"ROC-AUC:            {metrics['roc_auc']:.4f}")
    print(f"PR-AUC:             {metrics['pr_auc']:.4f}")
    
    print("\nConfusion Matrix:")
    print(f"True Negatives:  {cm[0,0]}")
    print(f"False Positives: {cm[0,1]}")
    print(f"False Negatives: {cm[1,0]}")
    print(f"True Positives:  {cm[1,1]}")
    
    print(f"\nBest Hyperparameters:")
    for param, value in random_search.best_params_.items():
        print(f"{param}: {value}")
    
    print(f"\nTop 10 Most Important Features:")
    for i, (feature, importance) in enumerate(feature_importance.head(10).values):
        print(f"{i+1:2d}. {feature:25s}: {importance:.4f}")
    
    # Model interpretation for flood prediction
    print(f"\nModel Interpretation for Flood Prediction:")
    top_weather_features = feature_importance[
        feature_importance['feature'].isin(['precipitation', 'temp_avg', 'humidity', 'precip_cover'])
    ].head(3)
    top_reservoir_features = feature_importance[
        feature_importance['feature'].isin(['max_reservoir_fill', 'avg_reservoir_fill', 'reservoir_risk_score'])
    ].head(3)
    
    print("Top Weather Predictors:")
    for feature, importance in top_weather_features.values:
        print(f"- {feature}: {importance:.4f}")
    
    print("Top Reservoir Predictors:")
    for feature, importance in top_reservoir_features.values:
        print(f"- {feature}: {importance:.4f}")
    
    return best_model, metrics, feature_importance

def main():
    """Main training pipeline"""
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    data_path = os.path.join(project_root, 'data', 'enhanced_training_data.csv')
    model_path = os.path.join(project_root, 'model.pickle')
    metrics_path = os.path.join(project_root, 'data', 'model_metrics.csv')
    feature_importance_path = os.path.join(project_root, 'data', 'feature_importance.csv')
    
    # Load and split data
    X, y = load_enhanced_data(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.3, 
        random_state=42, 
        stratify=y  # Maintain class distribution
    )
    
    print(f"\nTraining set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train and evaluate model
    best_model, metrics, feature_importance = train_best_model(X_train, y_train, X_test, y_test)
    
    # Save model and results
    print(f"\nSaving model and results...")
    
    # Save trained model
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"Model saved to: {model_path}")
    
    # Save metrics for reporting
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(metrics_path, index=False)
    print(f"Metrics saved to: {metrics_path}")
    
    # Save feature importance
    feature_importance.to_csv(feature_importance_path, index=False)
    print(f"Feature importance saved to: {feature_importance_path}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print("Key improvements from academic perspective:")
    print("• Used class_weight='balanced' instead of SMOTE (more robust)")
    print("• Optimized for PR-AUC (better for imbalanced flood detection)")
    print("• Comprehensive evaluation metrics for academic reporting")
    print("• Feature importance analysis for model interpretability")
    print("• Stratified sampling maintains class distribution")

if __name__ == "__main__":
    main()