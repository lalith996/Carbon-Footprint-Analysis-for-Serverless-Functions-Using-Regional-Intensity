"""
analyze_embodied_aware_experiments.py
======================================
Analyze embodied carbon-aware scheduling experiments and generate visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)

def load_data():
    """Load experiment results."""
    file_path = "experiment_results/embodied_aware_experiments.csv"
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    print(f"✅ Loaded {len(df)} experiments")
    return df

def analyze_strategy_comparison(df):
    """Compare strategies across all experiments."""
    print("\n" + "="*70)
    print("STRATEGY COMPARISON")
    print("="*70)
    
    summary = df.groupby("strategy").agg({
        "operational_co2_g": ["mean", "std"],
        "embodied_co2_g": ["mean", "std"],
        "total_co2_g": ["mean", "std"],
        "carbon_debt_ratio": "mean",
        "server_age_years": "mean",
        "power_w": "mean",
        "latency_ms": "mean"
    }).round(6)
    
    print(summary)
    
    # Calculate carbon savings vs baseline (operational_only)
    baseline = df[df["strategy"] == "operational_only"]["total_co2_g"].mean()
    
    print("\n📊 CARBON SAVINGS vs OPERATIONAL_ONLY:")
    for strategy in ["embodied_prioritized", "balanced"]:
        strategy_mean = df[df["strategy"] == strategy]["total_co2_g"].mean()
        savings = ((baseline - strategy_mean) / baseline) * 100
        print(f"  {strategy:25s}: {savings:+.2f}% ({strategy_mean:.6f}g vs {baseline:.6f}g)")
    
    return summary

def analyze_workload_impact(df):
    """Analyze how strategies perform across workload scales."""
    print("\n" + "="*70)
    print("WORKLOAD SCALE IMPACT")
    print("="*70)
    
    summary = df.groupby(["strategy", "workload_scale"]).agg({
        "total_co2_g": ["mean", "std"],
        "operational_co2_g": "mean",
        "embodied_co2_g": "mean"
    }).round(6)
    
    print(summary)
    return summary

def analyze_server_age_distribution(df):
    """Analyze server age selection by strategy."""
    print("\n" + "="*70)
    print("SERVER AGE DISTRIBUTION")
    print("="*70)
    
    age_dist = df.groupby(["strategy", "server_age"]).size().unstack(fill_value=0)
    print(age_dist)
    
    # Show percentages
    age_pct = (age_dist.T / age_dist.sum(axis=1)).T * 100
    print("\nPercentages:")
    print(age_pct.round(1))
    
    return age_dist

def create_visualizations(df):
    """Generate comprehensive visualization."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Total CO2 by Strategy
    ax = axes[0, 0]
    strategy_order = ["embodied_prioritized", "balanced", "operational_only"]
    sns.boxplot(data=df, x="strategy", y="total_co2_g", order=strategy_order, ax=ax, palette="Set2")
    ax.set_title("Total CO₂ Emissions by Strategy", fontsize=14, fontweight='bold')
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Total CO₂ (g)")
    ax.tick_params(axis='x', rotation=15)
    
    # 2. Operational vs Embodied Carbon
    ax = axes[0, 1]
    carbon_data = df.groupby("strategy")[["operational_co2_g", "embodied_co2_g"]].mean()
    carbon_data.plot(kind="bar", stacked=True, ax=ax, color=["#ff7f0e", "#2ca02c"])
    ax.set_title("Operational vs Embodied Carbon", fontsize=14, fontweight='bold')
    ax.set_xlabel("Strategy")
    ax.set_ylabel("CO₂ (g)")
    ax.legend(["Operational", "Embodied"])
    ax.tick_params(axis='x', rotation=15)
    
    # 3. Server Age Selection
    ax = axes[0, 2]
    age_counts = df.groupby(["strategy", "server_age"]).size().unstack(fill_value=0)
    age_counts.plot(kind="bar", ax=ax, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    ax.set_title("Server Age Selection by Strategy", fontsize=14, fontweight='bold')
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Count")
    ax.legend(title="Server Age", labels=["New (0.5y)", "Medium (2.5y)", "Old (4.0y)"])
    ax.tick_params(axis='x', rotation=15)
    
    # 4. Carbon Debt Ratio
    ax = axes[1, 0]
    sns.violinplot(data=df, x="strategy", y="carbon_debt_ratio", order=strategy_order, ax=ax, palette="muted")
    ax.set_title("Carbon Debt Ratio Distribution", fontsize=14, fontweight='bold')
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Carbon Debt Ratio")
    ax.axhline(y=0.5, color='r', linestyle='--', label='50% Threshold')
    ax.legend()
    ax.tick_params(axis='x', rotation=15)
    
    # 5. Workload Scale Impact
    ax = axes[1, 1]
    for strategy in strategy_order:
        strategy_data = df[df["strategy"] == strategy]
        grouped = strategy_data.groupby("workload_scale")["total_co2_g"].mean()
        ax.plot(grouped.index, grouped.values, marker='o', label=strategy, linewidth=2)
    ax.set_title("CO₂ Emissions vs Workload Scale", fontsize=14, fontweight='bold')
    ax.set_xlabel("Workload Scale")
    ax.set_ylabel("Total CO₂ (g)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Power Consumption vs Carbon Debt
    ax = axes[1, 2]
    for strategy in strategy_order:
        strategy_data = df[df["strategy"] == strategy]
        ax.scatter(strategy_data["carbon_debt_ratio"], strategy_data["power_w"], 
                  label=strategy, alpha=0.6, s=50)
    ax.set_title("Power Consumption vs Carbon Debt", fontsize=14, fontweight='bold')
    ax.set_xlabel("Carbon Debt Ratio")
    ax.set_ylabel("Power Consumption (W)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = "experiment_results/embodied_aware_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Visualization saved to: {output_file}")
    plt.close()

def generate_summary_report(df):
    """Generate text summary report."""
    report_file = "experiment_results/embodied_aware_summary.txt"
    
    with open(report_file, "w") as f:
        f.write("="*70 + "\n")
        f.write("EMBODIED CARBON-AWARE SCHEDULING - EXPERIMENT SUMMARY\n")
        f.write("="*70 + "\n\n")
        
        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total experiments: {len(df)}\n")
        f.write(f"Strategies tested: {df['strategy'].nunique()}\n")
        f.write(f"Workload scales: {sorted(df['workload_scale'].unique())}\n")
        f.write(f"Regions covered: {sorted(df['region'].unique())}\n\n")
        
        # Strategy comparison
        f.write("STRATEGY PERFORMANCE\n")
        f.write("-" * 70 + "\n")
        baseline = df[df["strategy"] == "operational_only"]["total_co2_g"].mean()
        
        for strategy in ["embodied_prioritized", "balanced", "operational_only"]:
            strategy_df = df[df["strategy"] == strategy]
            mean_co2 = strategy_df["total_co2_g"].mean()
            std_co2 = strategy_df["total_co2_g"].std()
            mean_age = strategy_df["server_age_years"].mean()
            mean_debt = strategy_df["carbon_debt_ratio"].mean()
            savings = ((baseline - mean_co2) / baseline) * 100
            
            f.write(f"\n{strategy.upper()}:\n")
            f.write(f"  Total CO₂: {mean_co2:.6f} ± {std_co2:.6f} g\n")
            f.write(f"  Avg Server Age: {mean_age:.2f} years\n")
            f.write(f"  Avg Carbon Debt: {mean_debt:.2%}\n")
            f.write(f"  Carbon Savings: {savings:+.2f}% vs baseline\n")
        
        # Key insights
        f.write("\n" + "="*70 + "\n")
        f.write("KEY INSIGHTS\n")
        f.write("="*70 + "\n")
        
        embodied_prio = df[df["strategy"] == "embodied_prioritized"]["total_co2_g"].mean()
        balanced = df[df["strategy"] == "balanced"]["total_co2_g"].mean()
        operational = df[df["strategy"] == "operational_only"]["total_co2_g"].mean()
        
        best_savings = ((operational - embodied_prio) / operational) * 100
        
        f.write(f"\n1. Embodied-prioritized strategy achieves {best_savings:.2f}% carbon reduction\n")
        f.write(f"2. Balanced strategy provides middle ground with {((operational - balanced) / operational) * 100:.2f}% savings\n")
        
        old_server_pct = (df[df["strategy"] == "embodied_prioritized"]["server_age"] == "old").mean() * 100
        f.write(f"3. Embodied-prioritized uses old servers {old_server_pct:.1f}% of the time\n")
        
        avg_embodied = df["embodied_co2_g"].mean()
        avg_operational = df["operational_co2_g"].mean()
        embodied_share = (avg_embodied / (avg_embodied + avg_operational)) * 100
        f.write(f"4. Embodied carbon represents {embodied_share:.1f}% of total emissions\n")
        
        f.write(f"5. Traditional approach (operational_only) ignores {embodied_share:.1f}% of carbon impact\n")
    
    print(f"✅ Summary report saved to: {report_file}")

def main():
    """Main analysis pipeline."""
    print("="*70)
    print("EMBODIED CARBON-AWARE SCHEDULING ANALYSIS")
    print("="*70)
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Run analyses
    analyze_strategy_comparison(df)
    analyze_workload_impact(df)
    analyze_server_age_distribution(df)
    
    # Generate visualizations
    create_visualizations(df)
    
    # Generate summary report
    generate_summary_report(df)
    
    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
