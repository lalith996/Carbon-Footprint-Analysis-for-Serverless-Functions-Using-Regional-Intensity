import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import joblib, os

# === Load dataset ===
file_path = os.path.join("data_clean", "features", "Northern_features.csv")
df = pd.read_csv(file_path)
df = df.sort_values("timestamp").reset_index(drop=True)

# === Create target for next 5-min prediction ===
df["target"] = df["carbon_intensity"].shift(-1)
df = df.dropna(subset=["target"])

# === Select features ===
feature_cols = [c for c in df.columns if c.startswith("lag_") or c.startswith("roll_") or c in ["hour_sin","hour_cos","minute_sin","minute_cos"]]
X = df[feature_cols]
y = df["target"]

# === Split chronologically ===
split = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# === Train Ridge Regression ===
model = Ridge(alpha=1.0)
model.fit(X_train, y_train)

# === Predict ===
y_pred = model.predict(X_test)

# === Evaluate ===
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n📊 Linear Regression (Ridge) Evaluation:")
print(f"MAE: {mae:.3f}")
print(f"RMSE: {rmse:.3f}")
print(f"R² Score: {r2:.3f}")

# === Save model ===
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/northern_lr_fixed.joblib")

# === Plot Actual vs Predicted ===
plt.figure(figsize=(10,4))
plt.plot(y_test.values[:200], label="Actual", linewidth=2)
plt.plot(y_pred[:200], label="Predicted (LR)", linestyle="--", linewidth=2)
plt.title("Linear Regression - Actual vs Predicted ")
plt.xlabel("Time Steps")
plt.ylabel("Carbon Intensity (gCO₂/kWh)")
plt.legend()
plt.tight_layout()
plt.savefig("models/lr_fixed_actual_vs_pred.png")
plt.show()
