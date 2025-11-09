"""
analyze_embodied_carbon.py
===========================
Analyze and visualize operational vs embodied carbon emissions.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from embodied_carbon import estimate_total_carbon, EmbodiedCarbonTracker

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def analyze_enhanced_results(csv_file="Data/results_enhanced.csv"):
    """
    Analyze results from enhanced serverless task runs.
    """
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        print("Run experiments with --enhanced flag first:")
        print("  python serverless_task_enhanced.py --scale 400000 --enhanced")
        return None
    
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df)} experiment records\n")
    
    # Summary statistics
    print("=" * 70)
    print("📊 CARBON EMISSIONS SUMMARY")
    print("=" * 70)
    
    print(f"\nOperational Carbon (from electricity):")
    print(f"  Mean:   {df['operational_co2_g'].mean():.6f} g CO2e")
    print(f"  Median: {df['operational_co2_g'].median():.6f} g CO2e")
    print(f"  Std:    {df['operational_co2_g'].std():.6f} g CO2e")
    
    print(f"\nEmbodied Carbon (from hardware manufacturing):")
    print(f"  Mean:   {df['embodied_co2_g'].mean():.6f} g CO2e")
    print(f"  Median: {df['embodied_co2_g'].median():.6f} g CO2e")
    print(f"  Std:    {df['embodied_co2_g'].std():.6f} g CO2e")
    
    print(f"\nTotal Carbon:")
    print(f"  Mean:   {df['total_co2_g'].mean():.6f} g CO2e")
    print(f"  Median: {df['total_co2_g'].median():.6f} g CO2e")
    print(f"  Total:  {df['total_co2_g'].sum():.6f} g CO2e")
    
    print(f"\nCarbon Split (Average):")
    print(f"  Operational: {df['operational_percent'].mean():.2f}%")
    print(f"  Embodied:    {df['embodied_percent'].mean():.2f}%")
    
    # Telemetry summary
    print("\n" + "=" * 70)
    print("🖥️  HARDWARE TELEMETRY SUMMARY")
    print("=" * 70)
    
    print(f"\nCPU Usage:")
    print(f"  Average: {df['cpu_percent_avg'].mean():.2f}%")
    print(f"  Peak:    {df['cpu_percent_max'].max():.2f}%")
    
    print(f"\nMemory Usage:")
    print(f"  Average: {df['memory_used_gb_avg'].mean():.2f} GB")
    print(f"  Peak:    {df['memory_percent_max'].max():.2f}%")
    
    if 'gpu_available' in df.columns and df['gpu_available'].any():
        print(f"\nGPU Detected:")
        gpu_data = df[df['gpu_available'] == True]
        if len(gpu_data) > 0 and 'gpu_utilization' in gpu_data.columns:
            print(f"  Average Utilization: {gpu_data['gpu_utilization'].mean():.2f}%")
            print(f"  Memory Used: {gpu_data['gpu_memory_used_gb'].mean():.2f} GB")
    
    return df


def create_visualizations(df, output_dir="experiment_results"):
    """
    Create comprehensive visualizations of carbon and telemetry data.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Operational vs Embodied Carbon (Stacked Bar)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Stacked bar chart by region
    ax1 = axes[0, 0]
    if 'region' in df.columns:
        region_summary = df.groupby('region').agg({
            'operational_co2_g': 'mean',
            'embodied_co2_g': 'mean'
        }).reset_index()
        
        x = range(len(region_summary))
        width = 0.6
        ax1.bar(x, region_summary['operational_co2_g'], width, 
               label='Operational', color='#FF6B6B')
        ax1.bar(x, region_summary['embodied_co2_g'], width,
               bottom=region_summary['operational_co2_g'],
               label='Embodied', color='#4ECDC4')
        ax1.set_xlabel('Region')
        ax1.set_ylabel('CO2 Emissions (g)')
        ax1.set_title('Carbon Emissions by Region\n(Operational + Embodied)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(region_summary['region'], rotation=45)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
    
    # Plot 2: Pie chart of carbon split
    ax2 = axes[0, 1]
    avg_operational = df['operational_co2_g'].mean()
    avg_embodied = df['embodied_co2_g'].mean()
    
    colors = ['#FF6B6B', '#4ECDC4']
    explode = (0.05, 0.05)
    ax2.pie([avg_operational, avg_embodied], 
           labels=['Operational', 'Embodied'],
           autopct='%1.1f%%',
           colors=colors,
           explode=explode,
           startangle=90)
    ax2.set_title('Average Carbon Split\n(Operational vs Embodied)')
    
    # Plot 3: CPU vs Memory Usage
    ax3 = axes[1, 0]
    ax3.scatter(df['cpu_percent_avg'], df['memory_percent_avg'], 
               c=df['total_co2_g'], cmap='YlOrRd', s=100, alpha=0.6)
    ax3.set_xlabel('CPU Usage (%)')
    ax3.set_ylabel('Memory Usage (%)')
    ax3.set_title('CPU vs Memory Usage\n(color = total CO2)')
    cbar = plt.colorbar(ax3.collections[0], ax=ax3)
    cbar.set_label('Total CO2 (g)')
    ax3.grid(alpha=0.3)
    
    # Plot 4: Carbon vs Workload Scale
    ax4 = axes[1, 1]
    if 'workload_scale' in df.columns:
        scale_summary = df.groupby('workload_scale').agg({
            'operational_co2_g': 'mean',
            'embodied_co2_g': 'mean',
            'total_co2_g': 'mean'
        }).reset_index()
        
        ax4.plot(scale_summary['workload_scale'], scale_summary['operational_co2_g'],
                marker='o', label='Operational', linewidth=2, color='#FF6B6B')
        ax4.plot(scale_summary['workload_scale'], scale_summary['embodied_co2_g'],
                marker='s', label='Embodied', linewidth=2, color='#4ECDC4')
        ax4.plot(scale_summary['workload_scale'], scale_summary['total_co2_g'],
                marker='^', label='Total', linewidth=2, color='#95E1D3')
        ax4.set_xlabel('Workload Scale')
        ax4.set_ylabel('CO2 Emissions (g)')
        ax4.set_title('Carbon Emissions vs Workload Scale')
        ax4.legend()
        ax4.grid(alpha=0.3)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, "embodied_carbon_analysis.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n📊 Saved visualization: {output_file}")
    
    # 2. Detailed telemetry over time
    fig2, axes2 = plt.subplots(2, 1, figsize=(14, 8))
    
    # CPU and Memory trends
    ax_cpu = axes2[0]
    ax_cpu.plot(df.index, df['cpu_percent_avg'], label='CPU Avg', 
               color='#3498db', linewidth=2)
    ax_cpu.fill_between(df.index, df['cpu_percent_avg'], alpha=0.3, color='#3498db')
    ax_cpu.set_ylabel('CPU Usage (%)', color='#3498db')
    ax_cpu.tick_params(axis='y', labelcolor='#3498db')
    ax_cpu.set_title('Hardware Telemetry Over Time')
    ax_cpu.grid(alpha=0.3)
    
    ax_mem = ax_cpu.twinx()
    ax_mem.plot(df.index, df['memory_percent_avg'], label='Memory Avg',
               color='#e74c3c', linewidth=2, linestyle='--')
    ax_mem.set_ylabel('Memory Usage (%)', color='#e74c3c')
    ax_mem.tick_params(axis='y', labelcolor='#e74c3c')
    
    # Carbon emissions over time
    ax_carbon = axes2[1]
    ax_carbon.plot(df.index, df['operational_co2_g'], label='Operational',
                  marker='o', linewidth=2, color='#FF6B6B')
    ax_carbon.plot(df.index, df['embodied_co2_g'], label='Embodied',
                  marker='s', linewidth=2, color='#4ECDC4')
    ax_carbon.plot(df.index, df['total_co2_g'], label='Total',
                  marker='^', linewidth=2, color='#95E1D3')
    ax_carbon.set_xlabel('Experiment Run')
    ax_carbon.set_ylabel('CO2 Emissions (g)')
    ax_carbon.set_title('Carbon Emissions Over Time')
    ax_carbon.legend()
    ax_carbon.grid(alpha=0.3)
    
    plt.tight_layout()
    output_file2 = os.path.join(output_dir, "telemetry_timeline.png")
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"📊 Saved visualization: {output_file2}")
    
    plt.show()


def compare_instance_types():
    """
    Compare embodied carbon across different instance types.
    """
    print("\n" + "=" * 70)
    print("🖥️  INSTANCE TYPE COMPARISON")
    print("=" * 70)
    
    instance_types = ["cloud_small", "cloud_medium", "cloud_large", "gpu_instance"]
    duration_hours = 1.0  # 1 hour workload
    
    results = []
    for instance in instance_types:
        tracker = EmbodiedCarbonTracker(instance)
        total_embodied = tracker.calculate_total_embodied_carbon()
        amortized = tracker.calculate_amortized_embodied_carbon(duration_hours)
        
        results.append({
            "instance": instance,
            "total_embodied_kg": total_embodied,
            "amortized_g_per_hour": amortized,
            "specs": tracker.specs
        })
    
    # Print comparison
    print(f"\n{'Instance Type':<20} {'Total Embodied':<20} {'Amortized (1hr)':<20}")
    print("─" * 60)
    for r in results:
        print(f"{r['instance']:<20} {r['total_embodied_kg']:>10.2f} kg CO2e  "
              f"{r['amortized_g_per_hour']:>10.6f} g/hr")
    
    print("\n💡 Tip: Choose smaller instances when possible to reduce embodied carbon!")
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("🌍 EMBODIED CARBON ANALYSIS TOOL")
    print("=" * 70)
    
    # Analyze enhanced results if available
    df = analyze_enhanced_results()
    
    if df is not None and len(df) > 0:
        create_visualizations(df)
    else:
        print("\n⚠️  No enhanced results found. Running demo comparison...\n")
    
    # Compare instance types
    compare_instance_types()
    
    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
