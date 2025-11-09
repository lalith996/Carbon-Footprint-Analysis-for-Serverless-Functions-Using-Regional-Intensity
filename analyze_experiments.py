"""
analyze_experiments.py
----------------------
Analyzes performance data across different regions and workload scales.
Auto-detects file location whether running locally or in Docker.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_rel, wilcoxon

# ---------------------------------------------------------------------
# Step 1. Find and load the data file
# ---------------------------------------------------------------------

def find_data_file():
    """Find the data file in various possible locations"""
    possible_locations = [
        "/app/Data/results.csv",         # Docker absolute path
        "./Data/results.csv",            # Local relative path
        "Data/results.csv",              # Alternative relative path
        "../Data/results.csv",           # One level up
        "../../Data/results.csv",        # Two levels up
    ]
    
    # Print current working directory for debugging
    print(f"Current working directory: {os.getcwd()}")
    
    # Try each possible location
    for path in possible_locations:
        if os.path.exists(path):
            print(f"Found data file at: {path}")
            return path
            
    # If we get here, we couldn't find the file
    print("Available files in current directory:", os.listdir("."))
    if os.path.exists("/app"):
        print("Files in /app:", os.listdir("/app"))
    raise FileNotFoundError("Could not find results.csv in any expected location")

# Try to find and load the data file
data_file = find_data_file()
print(f"Loading data from: {data_file}")

# ---------------------------------------------------------------------
# Step 2. Load the experiment data
# ---------------------------------------------------------------------

try:
    df = pd.read_csv(data_file)
except Exception as e:
    print(f"Error reading {data_file}: {str(e)}")
    print("Current directory:", os.getcwd())
    print("Directory contents:", os.listdir("."))
    if os.path.exists("/app"):
        print("/app contents:", os.listdir("/app"))
    raise

expected_cols = ["region", "workload_scale", "duration_s", "cpu_time_s"]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    raise ValueError(f"❌ Missing expected columns in CSV: {missing}")

print(f"✅ Loaded {len(df)} experiment records")

# ---------------------------------------------------------------------
# Step 3. Compute group statistics
# ---------------------------------------------------------------------

# Calculate CPU efficiency
df['cpu_efficiency'] = df['cpu_time_s'] / df['duration_s']

summary = (
    df.groupby("region")
      .agg(mean_duration=("duration_s", "mean"),
           std_duration=("duration_s", "std"),
           mean_cpu_time=("cpu_time_s", "mean"),
           mean_efficiency=("cpu_efficiency", "mean"))
      .reset_index()
)

print("\n📊 Region Performance Summary:")
print(summary)

# ---------------------------------------------------------------------
# Step 4. Statistical tests (compare Northern vs Eastern)
# ---------------------------------------------------------------------

northern = df[df.region == "Northern"]["duration_s"].values
eastern = df[df.region == "Eastern"]["duration_s"].values

n = min(len(northern), len(eastern))
northern, eastern = northern[:n], eastern[:n]

if len(northern) > 2 and len(eastern) > 2:
    t_stat, p_ttest = ttest_rel(northern, eastern)
    _, p_wilcox = wilcoxon(northern, eastern)
    print(f"\n📈 Paired t-test p-value: {p_ttest:.4e}")
    print(f"📉 Wilcoxon signed-rank p-value: {p_wilcox:.4e}")
else:
    print("\n⚠️ Not enough paired samples for statistical tests.")

# ---------------------------------------------------------------------
# Step 5. Compute performance differences
# ---------------------------------------------------------------------

if "Northern" in summary.region.values and "Eastern" in summary.region.values:
    northern_mean = summary.loc[summary.region == "Northern", "mean_duration"].values[0]
    eastern_mean = summary.loc[summary.region == "Eastern", "mean_duration"].values[0]
    diff_percent = (northern_mean - eastern_mean) / eastern_mean * 100
    print(f"\n⚡ Performance difference (Northern vs Eastern): {diff_percent:.2f}%")
else:
    print("\n⚠️ Missing Northern or Eastern region in results.")

# ---------------------------------------------------------------------
# Step 6. Visualization
# ---------------------------------------------------------------------

# Create a scatter plot of duration vs workload scale, colored by region
plt.figure(figsize=(10,6))
for region in df['region'].unique():
    mask = df['region'] == region
    plt.scatter(df[mask]['workload_scale'], 
               df[mask]['duration_s'],
               label=region,
               alpha=0.6)
plt.grid(True, alpha=0.3)
plt.xlabel('Workload Scale')
plt.ylabel('Duration (seconds)')
plt.title('Performance Comparison Across Regions')
plt.legend()

# ---------------------------------------------------------------------
# Step 7. Save results and plot
# ---------------------------------------------------------------------

try:
    # Try to create output directory in multiple possible locations
    output_dirs = [
        os.path.join(os.getcwd(), "experiment_results"),
        os.path.join(os.path.dirname(data_file), "experiment_results"),
        "experiment_results"
    ]
    
    # Try each location until we find one we can write to
    output_dir = None
    for dir_path in output_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            # Test if we can write to this directory
            test_file = os.path.join(dir_path, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            output_dir = dir_path
            print(f"Using output directory: {output_dir}")
            break
        except (OSError, PermissionError):
            continue
    
    if output_dir is None:
        print("Warning: Could not create output directory. Saving files in current directory.")
        output_dir = os.getcwd()
    
    # Save the files
    summary_path = os.path.join(output_dir, "region_summary.csv")
    plot_path = os.path.join(output_dir, "region_performance.png")
    
    summary.to_csv(summary_path, index=False)
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.show()
    
    print(f"\n✅ Analysis complete.")
    print(f"📁 Saved summary CSV: {summary_path}")
    print(f"🖼️ Saved plot: {plot_path}")
except Exception as e:
    print(f"\n⚠️ Warning: Could not save output files: {str(e)}")
    print("Analysis results are still displayed in the console output above.")
    plt.show()

print(f"\n✅ Analysis complete.")
print(f"📁 Saved summary CSV: {summary_path}")
print(f"🖼️ Saved plot: {plot_path}")
