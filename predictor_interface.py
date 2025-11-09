# predictor_interface.py
import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

def load_lr(region):
    return joblib.load(f"models/{region.lower()}_lr_fixed.joblib")

def predict_lr_next(region, features_df):
    """
    features_df: DataFrame with feature columns (lags, roll_*, hour_sin, hour_cos, etc)
    We use the last row's features to predict next 5-min CI.
    """
    model = load_lr(region)
    # Get available feature columns (handle both with and without minute encoding)
    available_cols = [c for c in features_df.columns if c.startswith("lag_") or c.startswith("roll_") or c in ["hour_sin","hour_cos","minute_sin","minute_cos"]]
    X = features_df[available_cols]
    X_last = X.iloc[-1].values.reshape(1, -1)
    pred = model.predict(X_last)[0]
    return float(pred)
