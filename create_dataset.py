import pandas as pd
import numpy as np

# Make the results reproducible
np.random.seed(42)

# Number of records
rows = 1000

# Generate smart-grid input data
voltage = np.random.uniform(210, 250, rows)
current = np.random.uniform(5, 100, rows)
reactive_power = np.random.uniform(1, 50, rows)
power_factor = np.random.uniform(0.75, 0.99, rows)
solar_power = np.random.uniform(0, 50, rows)
wind_power = np.random.uniform(0, 40, rows)
temperature = np.random.uniform(15, 45, rows)
humidity = np.random.uniform(20, 90, rows)

# Create a realistic load value for training
predicted_load = (
    (voltage * current * power_factor) / 1000
    + reactive_power * 0.10
    - solar_power * 0.20
    - wind_power * 0.15
    + temperature * 0.05
    + np.random.normal(0, 2, rows)
)

# Make sure load values are positive
predicted_load = np.maximum(predicted_load, 0)

# Create DataFrame
data = pd.DataFrame({
    "Voltage (V)": voltage,
    "Current (A)": current,
    "Reactive Power (kVAR)": reactive_power,
    "Power Factor": power_factor,
    "Solar Power (kW)": solar_power,
    "Wind Power (kW)": wind_power,
    "Temperature (°C)": temperature,
    "Humidity (%)": humidity,
    "Predicted Load (kW)": predicted_load
})

# Save dataset
data.to_csv("dataset/smart_grid_data.csv", index=False)

print("Dataset created successfully!")
print(f"Total records: {len(data)}")
print("\nFirst 5 records:")
print(data.head())