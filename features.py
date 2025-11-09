# features.py
import pandas as pd
import numpy as np
import os

def make_features(df, lags=12, rolling_windows=[3,12]):
    # df must have timestamp (datetime) and ci
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["hour"] = df["timestamp"].dt.hour
    df["minute"] = df["timestamp"].dt.minute
    # cyclical encoding
    df["hour_sin"] = np.sin(2*np.pi*df["hour"]/24.0)
    df["hour_cos"] = np.cos(2*np.pi*df["hour"]/24.0)
    df["minute_sin"] = np.sin(2*np.pi*df["minute"]/60.0)
    df["minute_cos"] = np.cos(2*np.pi*df["minute"]/60.0)
    # lags (use past lags at 5-min intervals)
    for lag in range(1, lags+1):
        df[f"lag_{lag}"] = df["carbon_intensity"].shift(lag)
    # rolling means
    for w in rolling_windows:
        df[f"roll_{w}"] = df["carbon_intensity"].rolling(window=w, min_periods=1).mean()
    df = df.dropna().reset_index(drop=True)
    return df

# Example usage:
if __name__=="__main__":
    # Try both Data and data directories
    for base_dir in ["Data", "data"]:
        input_file = os.path.join(base_dir, "Northern.csv")
        if os.path.exists(input_file):
            df = pd.read_csv(input_file, parse_dates=["timestamp"])
            f = make_features(df, lags=12, rolling_windows=[3,12])
            output_file = os.path.join(base_dir, "Northern_features.csv")
            f.to_csv(output_file, index=False)
            print(f"Features for Northern saved to {output_file}")
            break

