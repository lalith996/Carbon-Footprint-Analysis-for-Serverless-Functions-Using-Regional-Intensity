# scheduler_using_lr.py
from estimator import get_live_ci  # still used for live fallback
from predictor_interface import predict_lr_next
import pandas as pd
import os

REGION_LATENCY = {"Northern":70,"Western":90,"Southern":80,"Eastern":120}
REGION_COST = {"Northern":3.0,"Western":2.8,"Southern":3.2,"Eastern":2.5}
REGIONS = list(REGION_LATENCY.keys())
POWER_W = 65
PUE_DEFAULT = 1.2

def get_latest_features(region):
    fpath = f"data_clean/features/{region}_features.csv"
    if not os.path.exists(fpath):
        # fallback: build minimal features from last few raw rows
        raw = pd.read_csv(f"data_clean/{region}_clean.csv", parse_dates=["timestamp"])
        from features import make_features
        feat = make_features(raw)
        feat.to_csv(fpath, index=False)
    return pd.read_csv(fpath, parse_dates=["timestamp"])

def choose_region_with_lr(duration_s, sla_ms=2000):
    best, best_score = None, float("inf")
    for r in REGIONS:
        lat = REGION_LATENCY[r]
        if lat > sla_ms:
            continue
        # get predictive CI using LR (features must be up to date)
        feats = get_latest_features(r)
        try:
            ci_pred = predict_lr_next(r, feats)
        except Exception:
            ci_pred = get_live_ci(r)
        # combine: 0.7 live + 0.3 lr_pred (or choose 1.0*ci_pred if you prefer)
        ci_live = get_live_ci(r)
        ci_eff = 0.7*ci_live + 0.3*ci_pred
        energy_kwh = (POWER_W * (duration_s/3600.0)) / 1000.0
        co2_g = energy_kwh * ci_eff * PUE_DEFAULT
        score = 0.7*co2_g + 0.2*(lat/1000.0) + 0.1*REGION_COST[r]
        if score < best_score:
            best_score = score
            best = {"region": r, "co2_g": round(co2_g,6), "latency_ms": lat, "score": round(score,6)}
    return best

if __name__=="__main__":
    print(choose_region_with_lr(2.5, 2000))
