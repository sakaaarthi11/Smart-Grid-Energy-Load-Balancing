import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# 1. Load the dataset
data = pd.read_csv("dataset/smart_grid_data.csv")

# 2. Separate input features and target
features = [
    "Voltage (V)",
    "Current (A)",
    "Reactive Power (kVAR)",
    "Power Factor",
    "Solar Power (kW)",
    "Wind Power (kW)",
    "Temperature (°C)",
    "Humidity (%)"
]

target = "Predicted Load (kW)"

X = data[features]
y = data[target]

# 3. Split the dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

# 4. Create the Random Forest model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

# 5. Train the model
model.fit(X_train, y_train)

# 6. Make predictions
predictions = model.predict(X_test)

# 7. Calculate performance
mae = mean_absolute_error(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("Model training completed successfully!")
print("--------------------------------------")
print(f"Training records: {len(X_train)}")
print(f"Testing records: {len(X_test)}")
print(f"Mean Absolute Error: {mae:.2f}")
print(f"Mean Squared Error: {mse:.2f}")
print(f"R2 Score: {r2:.4f}")

# 8. Create models folder if it doesn't exist
os.makedirs("models", exist_ok=True)

# 9. Save the trained model
model_path = "models/model.pkl"
joblib.dump(model, model_path)

print("--------------------------------------")
print(f"Model saved successfully: {model_path}")