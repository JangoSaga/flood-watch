import pandas as pd
import os
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score, precision_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
import pickle
import numpy as np

# Load data with proper file path
data_path = os.path.join(os.path.dirname(__file__), "final_data.csv")
data = pd.read_csv(data_path)

y = data['class']
X = data.drop('class', axis=1)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Original class distribution:")
print(y_train.value_counts())

# Store results for comparison
results = []

# 1. BASELINE MODEL - Basic RandomForest with weak parameters
print("\n" + "="*50)
print("TRAINING BASELINE MODEL")
print("="*50)

baseline_rf = RandomForestClassifier(
    n_estimators=10,  # Very few trees
    max_depth=3,      # Shallow trees
    min_samples_split=10,  # Conservative splitting
    random_state=42
)
baseline_rf.fit(X_train, y_train)
baseline_pred = baseline_rf.predict(X_test)

baseline_accuracy = accuracy_score(y_test, baseline_pred)
baseline_precision = precision_score(y_test, baseline_pred)
baseline_recall = recall_score(y_test, baseline_pred)
baseline_f1 = f1_score(y_test, baseline_pred)

results.append({
    'Model': 'Baseline',
    'Accuracy': baseline_accuracy,
    'Precision': baseline_precision,
    'Recall': baseline_recall,
    'F1-Score': baseline_f1
})

print(f"Baseline - Accuracy: {baseline_accuracy:.4f}, Recall: {baseline_recall:.4f}, F1: {baseline_f1:.4f}")

# 2. SMOTE ENHANCED MODEL - Add SMOTE but keep basic parameters
print("\n" + "="*50)
print("TRAINING SMOTE ENHANCED MODEL")
print("="*50)

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print("After SMOTE class distribution:")
print(pd.Series(y_train_balanced).value_counts())

smote_rf = RandomForestClassifier(
    n_estimators=50,  # Better than baseline
    max_depth=8,      # Deeper than baseline
    min_samples_split=5,  # Less conservative
    random_state=42
)
smote_rf.fit(X_train_balanced, y_train_balanced)
smote_pred = smote_rf.predict(X_test)

smote_accuracy = accuracy_score(y_test, smote_pred)
smote_precision = precision_score(y_test, smote_pred)
smote_recall = recall_score(y_test, smote_pred)
smote_f1 = f1_score(y_test, smote_pred)

results.append({
    'Model': 'SMOTE Enhanced',
    'Accuracy': smote_accuracy,
    'Precision': smote_precision,
    'Recall': smote_recall,
    'F1-Score': smote_f1
})

print(f"SMOTE Enhanced - Accuracy: {smote_accuracy:.4f}, Recall: {smote_recall:.4f}, F1: {smote_f1:.4f}")

# 3. OPTIMIZED MODEL - SMOTE + Hyperparameter tuning
print("\n" + "="*50)
print("TRAINING OPTIMIZED MODEL (SMOTE + TUNING)")
print("="*50)

param_distributions = {
    'n_estimators': [100, 150, 200],
    'max_depth': [10, 15, 20],
    'min_samples_split': [2, 5],
    'min_samples_leaf': [1, 2],
    'criterion': ['gini', 'entropy']
}

rf = RandomForestClassifier(random_state=42)
random_search = RandomizedSearchCV(rf, param_distributions, n_iter=20, cv=3, scoring='recall', 
                                 random_state=42, n_jobs=1, verbose=0)
random_search.fit(X_train_balanced, y_train_balanced)

optimized_rf = random_search.best_estimator_
optimized_pred = optimized_rf.predict(X_test)

optimized_accuracy = accuracy_score(y_test, optimized_pred)
optimized_precision = precision_score(y_test, optimized_pred)
optimized_recall = recall_score(y_test, optimized_pred)
optimized_f1 = f1_score(y_test, optimized_pred)

results.append({
    'Model': 'Optimized (SMOTE + Tuning)',
    'Accuracy': optimized_accuracy,
    'Precision': optimized_precision,
    'Recall': optimized_recall,
    'F1-Score': optimized_f1
})

print(f"Optimized - Accuracy: {optimized_accuracy:.4f}, Recall: {optimized_recall:.4f}, F1: {optimized_f1:.4f}")

# COMPARISON SUMMARY
print("\n" + "="*60)
print("MODEL COMPARISON SUMMARY")
print("="*60)

results_df = pd.DataFrame(results)
print(results_df.round(4))

print("\n=== Improvements over Baseline ===")
smote_recall_improvement = ((smote_recall - baseline_recall) / baseline_recall) * 100
optimized_recall_improvement = ((optimized_recall - baseline_recall) / baseline_recall) * 100
smote_f1_improvement = ((smote_f1 - baseline_f1) / baseline_f1) * 100
optimized_f1_improvement = ((optimized_f1 - baseline_f1) / baseline_f1) * 100

print(f"SMOTE Recall Improvement: {smote_recall_improvement:.2f}%")
print(f"Optimized Recall Improvement: {optimized_recall_improvement:.2f}%")
print(f"SMOTE F1 Improvement: {smote_f1_improvement:.2f}%")
print(f"Optimized F1 Improvement: {optimized_f1_improvement:.2f}%")

print(f"\nBest parameters: {random_search.best_params_}")

# Save the best model
model_path = os.path.join(os.path.dirname(__file__), '..', 'model.pickle')
pickle.dump(optimized_rf, open(model_path, 'wb'))
print(f"\nOptimized model saved to: {model_path}")