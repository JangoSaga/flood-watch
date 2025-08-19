import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE


def load_enhanced_data(data_path):
    print("Loading training data...")
    data = pd.read_csv(data_path)
    X = data.drop('flood_class', axis=1)
    y = data['flood_class']
    return X, y


def train_best_model(X_train, y_train, X_test, y_test):
    print("\n=== TRAINING BEST MODEL (SMOTE + Optimized RandomForest) ===")

    # Apply SMOTE for balance
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

    # Parameter grid for tuning
    param_distributions = {
        'n_estimators': [100, 150, 200, 250],
        'max_depth': [10, 15, 20, 25],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'criterion': ['gini', 'entropy']
    }

    rf = RandomForestClassifier(random_state=42)
    random_search = RandomizedSearchCV(
        rf, param_distributions,
        n_iter=30, cv=3,
        scoring='recall',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )

    print("Performing hyperparameter tuning...")
    random_search.fit(X_train_balanced, y_train_balanced)

    best_model = random_search.best_estimator_
    preds = best_model.predict(X_test)

    metrics = {
        'accuracy': accuracy_score(y_test, preds),
        'precision': precision_score(y_test, preds),
        'recall': recall_score(y_test, preds),
        'f1': f1_score(y_test, preds)
    }

    print("Best Model Metrics:", metrics)
    print("Best Params:", random_search.best_params_)

    return best_model, metrics


def main():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    data_path = os.path.join(project_root, 'data', 'enhanced_training_data.csv')
    model_path = os.path.join(project_root, 'model.pickle')

    X, y = load_enhanced_data(data_path)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    best_model, metrics = train_best_model(X_train, y_train, X_test, y_test)

    # Save best model
    pickle.dump(best_model, open(model_path, 'wb'))
    print(f"\nBest model saved to: {model_path}")


if __name__ == "__main__":
    main()
