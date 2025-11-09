import requests, time, pandas as pd, os
from datetime import datetime

# Secure API key - use environment variable or fallback for testing
API_KEY = os.environ.get("ELECTRICITYMAP_API_KEY", "XbTiaxd1H1KVBI4857Zx")
ZONE_MAP = {"Northern":"IN-NO","Western":"IN-WE","Southern":"IN-SO","Eastern":"IN-EA"}
_ci_cache = {}
CACHE_TTL = 300
PUE_DEFAULT = 1.2
POWER_WATTS = 65

def get_live_ci(region):
    zone = ZONE_MAP.get(region)
    if not zone: return 700
    cached = _ci_cache.get(region)
    if cached and time.time()-cached["ts"]<CACHE_TTL:
        return cached["ci"]
    try:
        headers = {"auth-token":API_KEY}
        url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code==200:
            ci = r.json().get("carbonIntensity")
            _ci_cache[region]={"ci":ci,"ts":time.time()}
            print(f"[{datetime.now()}] {region}: {ci} gCO₂/kWh (live)")
            return ci
    except: pass
    return 700

def get_recent_historical_ci(region):
    """Fetch last recorded historical CI value."""
    # Try both Data and data directories for compatibility
    for base_dir in ["Data", "data"]:
        file = os.path.join(base_dir, f"{region}.csv")
        if os.path.exists(file):
            df = pd.read_csv(file)
            return df["carbon_intensity"].iloc[-1]
    return None

def estimate_co2(duration_s, region="Northern", mode="hybrid"):
    """Compute CO₂ emission for workload."""
    duration_h = duration_s / 3600.0
    energy_kwh = (POWER_WATTS * duration_h) / 1000.0
    ci_live = get_live_ci(region)
    ci_hist = get_recent_historical_ci(region) or ci_live
    ci = (0.7*ci_live + 0.3*ci_hist) if mode=="hybrid" else ci_live
    co2_g = energy_kwh * ci * PUE_DEFAULT
    return round(energy_kwh,8), round(co2_g,6)

if __name__ == "__main__":
    print(estimate_co2(2.5, "Southern"))
