import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# --- AUTOMATIC PATH MANAGEMENT ---
# Finds the directory where this script lives (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Moves one level up to the root project directory
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# Define safe absolute paths to save files
DATA_DIR = os.path.join(ROOT_DIR, 'data')
MODEL_PATH = os.path.join(SCRIPT_DIR, 'credit_rf_model.pkl')

# Create the data directory if it somehow missing
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, 'synthetic_historical_data.csv')
# ---------------------------------

# Step 1: Generate 1,000 fake historical counterparty credit records
np.random.seed(42)
n_records = 1000

z_scores = np.random.uniform(0.5, 4.5, n_records)
leverage = np.random.uniform(0.1, 0.9, n_records)
current_ratio = np.random.uniform(0.5, 3.0, n_records)

# Higher default risk if Z-Score is low and leverage is high
default_prob = 1 / (1 + np.exp(-(-2.5 * z_scores + 4.0 * leverage - 1.5 * current_ratio + np.random.normal(0, 1, n_records))))
default_flag = (default_prob > 0.5).astype(int)

df = pd.DataFrame({
    'altman_z_score': z_scores,
    'leverage_ratio': leverage,
    'current_ratio': current_ratio,
    'defaulted': default_flag
})

# Save to the verified absolute path
df.to_csv(CSV_PATH, index=False)

# Step 2: Train a simple Random Forest Classifier
X = df[['altman_z_score', 'leverage_ratio', 'current_ratio']]
y = df['defaulted']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model artifact to verified absolute path
joblib.dump(model, MODEL_PATH)
print(f"SUCCESS: Synthetic data saved to: {CSV_PATH}")
print(f"SUCCESS: ML Model artifact saved to: {MODEL_PATH}")
