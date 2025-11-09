import pandas as pd, matplotlib.pyplot as plt
from estimator import estimate_co2

# Workload-based emission analysis
df = pd.read_csv("data/results.csv")
df[["energy_kwh","co2_g"]] = df.apply(lambda r: pd.Series(estimate_co2(r["duration_s"], r["region"], "hybrid")), axis=1)
df.to_csv("data/results_with_co2.csv", index=False)
summary = df.groupby("region")["co2_g"].agg(["mean","std"]).reset_index()
summary.to_csv("data/analysis_summary.csv", index=False)
print(summary)

plt.figure(figsize=(6,4))
plt.bar(summary["region"], summary["mean"], yerr=summary["std"], capsize=5)
plt.title("Average CO₂ Emission per Region (Hybrid Model)")
plt.ylabel("CO₂ (grams)")
plt.tight_layout()
plt.savefig("data/co2_bar_chart.png")
plt.show()

# Historical trend plotting
plt.figure(figsize=(7,4))
for region in ["Northern","Western","Southern","Eastern"]:
    df_h = pd.read_csv(f"data/{region}.csv", parse_dates=["timestamp"])
    plt.plot(df_h["timestamp"], df_h["carbon_intensity"], label=region)
plt.legend(); plt.xticks(rotation=30)
plt.title("Historical Carbon Intensity Trends (5-min data)")
plt.ylabel("gCO₂/kWh"); plt.tight_layout()
plt.savefig("data/historical_trends.png")
plt.show()
