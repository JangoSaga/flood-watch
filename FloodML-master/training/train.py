import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
import pickle
from pathlib import Path

# Load labeled, augmented dataset
data = pd.read_csv("final_data.csv")

# Basic sanity checks
assert 'class' in data.columns, "final_data.csv must include a 'class' column"

y = data['class']
X = data.drop('class', axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

classifier = RandomForestClassifier(n_estimators=50, criterion='entropy', random_state=0)
classifier.fit(X_train, y_train)

pred = classifier.predict(X_test)
accuracy = accuracy_score(y_test, pred)

print("accuracy: " + str(round(accuracy * 100, 2)) + "%")
print("\nClassification report:\n")
print(classification_report(y_test, pred, digits=4))

# Save model in training dir and project root
training_model_path = Path('model.pickle')
root_model_path = Path('..') / 'model.pickle'

with open(training_model_path, 'wb') as f:
    pickle.dump(classifier, f)

with open(root_model_path, 'wb') as f:
    pickle.dump(classifier, f)

print(f"Saved model to {training_model_path.resolve()} and {root_model_path.resolve()}")