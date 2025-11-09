import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
import os, joblib

# === 1️⃣ Load data ===
file_path = os.path.join("data_clean", "features", "Northern_features.csv")
df = pd.read_csv(file_path)
print("✅ Dataset loaded. Shape:", df.shape)

# === 2️⃣ Use only timestamp + carbon_intensity ===
df = df[["timestamp", "carbon_intensity"]]
df["carbon_intensity"] = df["carbon_intensity"].astype(float)

# === 3️⃣ Normalize data ===
scaler = MinMaxScaler()
scaled_ci = scaler.fit_transform(df["carbon_intensity"].values.reshape(-1, 1))

# === 4️⃣ Create time-series sequences ===
SEQ_LEN = 12  # last 1 hour (12 × 5-min intervals)
X, y = [], []
for i in range(SEQ_LEN, len(scaled_ci)):
    X.append(scaled_ci[i-SEQ_LEN:i])
    y.append(scaled_ci[i])
X, y = np.array(X), np.array(y)

# === 5️⃣ Split train/test ===
split_ratio = 0.8
split = int(len(X) * split_ratio)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# === 6️⃣ Define LSTM model ===
model = Sequential([
    LSTM(64, input_shape=(SEQ_LEN, 1), return_sequences=False),
    Dropout(0.2),
    Dense(32, activation="relu"),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")
early_stop = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)

# === 7️⃣ Train model ===
history = model.fit(X_train, y_train,
                    epochs=30,
                    batch_size=64,
                    validation_split=0.1,
                    callbacks=[early_stop],
                    verbose=1)

# === 8️⃣ Evaluate ===
y_pred = model.predict(X_test)
y_pred_inv = scaler.inverse_transform(y_pred)
y_test_inv = scaler.inverse_transform(y_test)

mae = mean_absolute_error(y_test_inv, y_pred_inv)
rmse = np.sqrt(mean_squared_error(y_test_inv, y_pred_inv))
r2 = r2_score(y_test_inv, y_pred_inv)

print("\n📊 LSTM Model Evaluation:")
print(f"MAE: {mae:.3f}")
print(f"RMSE: {rmse:.3f}")
print(f"R² Score: {r2:.3f}")

# === 9️⃣ Save model ===
os.makedirs("models", exist_ok=True)
model.save("models/northern_lstm.h5")
joblib.dump(scaler, "models/northern_scaler.joblib")

# === 🔟 Plot comparison ===
plt.figure(figsize=(10,4))
plt.plot(y_test_inv[:200], label="Actual", linewidth=2)
plt.plot(y_pred_inv[:200], label="Predicted (LSTM)", linestyle="--", linewidth=2)
plt.title("LSTM - Actual vs Predicted (Sample 200 points)")
plt.xlabel("Time Steps")
plt.ylabel("Carbon Intensity (gCO₂/kWh)")
plt.legend()
plt.tight_layout()
plt.savefig("models/lstm_actual_vs_pred.png")
plt.show()
