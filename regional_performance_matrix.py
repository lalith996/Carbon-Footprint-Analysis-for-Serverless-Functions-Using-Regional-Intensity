#!/usr/bin/env python3
"""
Regional Performance Matrix (EXP-002)
======================================
Test all 4 Indian regions to validate regional recommendations.

Target: IEEE Transactions on Sustainable Computing
Deadline: 2025-11-15
Task: EXP-002 of publication pipeline

Regions:
- Northern: 535 gCO₂/kWh (moderate)
- Southern: 607 gCO₂/kWh (moderate-high)
- Eastern: 813 gCO₂/kWh (high)
- Western: 712 gCO₂/kWh (high)
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import sys

# Import project modules
from scheduler_embodied_aware import (
    calculate_power_consumption,
    SERVER_SPECS,
    BASE_POWER_W,
    PUE_DEFAULT as PUE
)

# Embodied carbon constant
EMBODIED_CARBON_KG = 660  # kg CO2e per server

# Regional carbon intensities (from Indian grid data)
REGIONAL_CI = {
    "Northern": 535,
    "Southern": 607,
    "Eastern": 813,
    "Western": 712
}

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


class RegionalPerformanceTester:
    """
    Test strategy performance across all Indian regions.
    """
    
    def __init__(self, output_dir: str = "regional_matrix"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = []
        self.start_time = datetime.now()
        
    def calculate_carbon_with_ci(
        self,
        ci_value: float,
        duration_s: float,
        server_age: str
    ) -> Dict[str, float]:
        """
        Calculate operational and embodied carbon separately.
        
        Args:
            ci_value: Carbon intensity (gCO₂/kWh)
            duration_s: Duration in seconds
            server_age: Server age category
            
        Returns:
            Dictionary with carbon breakdown
        """
        age_years = SERVER_SPECS[server_age]["age_years"]
        
        # Operational carbon
        power_w = calculate_power_consumption(BASE_POWER_W, age_years)
        energy_kwh = (power_w * duration_s) / (1000 * 3600)
        operational_g = energy_kwh * ci_value * PUE
        
        # Embodied carbon
        lifetime_hours = 5 * 365.25 * 24
        carbon_per_hour = (EMBODIED_CARBON_KG * 1000) / lifetime_hours
        task_carbon_raw = carbon_per_hour * (duration_s / 3600)
        debt_ratio = (5 - age_years) / 5
        embodied_g = task_carbon_raw * debt_ratio
        
        return {
            'operational_g': operational_g,
            'embodied_g': embodied_g,
            'total_g': operational_g + embodied_g,
            'power_w': power_w,
            'energy_kwh': energy_kwh
        }
    
    def test_region(
        self,
        region: str,
        ci_value: float,
        duration_s: float,
        num_tasks: int,
        strategies: List[str]
    ) -> List[Dict]:
        """
        Test a single region across multiple strategies.
        
        Args:
            region: Region name
            ci_value: Carbon intensity for this region
            duration_s: Task duration in seconds
            num_tasks: Number of tasks to simulate
            strategies: List of strategies to test
            
        Returns:
            List of result dictionaries
        """
        task_results = []
        
        print(f"\n{'='*70}")
        print(f"Testing {region} (CI = {ci_value} gCO₂/kWh)")
        print(f"{'='*70}")
        
        for strategy_name in strategies:
            print(f"\n  Strategy: {strategy_name}")
            strategy_carbon = []
            
            for task_idx in range(num_tasks):
                if (task_idx + 1) % 50 == 0:
                    print(f"    Task {task_idx + 1}/{num_tasks}...")
                
                # Select server age based on strategy
                if strategy_name == "operational_only":
                    server_age = "new"
                elif strategy_name == "embodied_prioritized":
                    server_age = "old"
                elif strategy_name == "balanced":
                    server_age = "medium"
                else:
                    raise ValueError(f"Unknown strategy: {strategy_name}")
                
                # Calculate carbon
                carbon_breakdown = self.calculate_carbon_with_ci(
                    ci_value, duration_s, server_age
                )
                
                strategy_carbon.append(carbon_breakdown['total_g'])
                
                # Store individual task result
                task_results.append({
                    'region': region,
                    'ci_value': ci_value,
                    'strategy': strategy_name,
                    'task_id': task_idx,
                    'server_age': server_age,
                    'duration_s': duration_s,
                    'operational_g': carbon_breakdown['operational_g'],
                    'embodied_g': carbon_breakdown['embodied_g'],
                    'total_carbon_g': carbon_breakdown['total_g'],
                    'power_w': carbon_breakdown['power_w'],
                    'energy_kwh': carbon_breakdown['energy_kwh'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Summary statistics
            mean_carbon = np.mean(strategy_carbon)
            std_carbon = np.std(strategy_carbon)
            print(f"    Mean: {mean_carbon:.2f}g (±{std_carbon:.2f})")
        
        return task_results
    
    def run_regional_matrix(
        self,
        regions: List[str],
        duration_s: float,
        num_tasks_per_region: int,
        strategies: List[str]
    ):
        """
        Run complete regional performance matrix.
        """
        print(f"\n{'='*70}")
        print(f"REGIONAL PERFORMANCE MATRIX (EXP-002)")
        print(f"{'='*70}")
        print(f"Regions: {regions}")
        print(f"Duration: {duration_s}s ({duration_s/3600:.1f}hr)")
        print(f"Tasks per region: {num_tasks_per_region}")
        print(f"Strategies: {strategies}")
        print(f"Total tasks: {len(regions) * num_tasks_per_region * len(strategies)}")
        print(f"Output directory: {self.output_dir}")
        
        all_results = []
        
        for region in regions:
            ci_value = REGIONAL_CI[region]
            task_results = self.test_region(
                region, ci_value, duration_s, num_tasks_per_region, strategies
            )
            all_results.extend(task_results)
        
        # Convert to DataFrame
        self.results_df = pd.DataFrame(all_results)
        
        # Save raw results
        output_file = self.output_dir / "regional_performance.csv"
        self.results_df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved to: {output_file}")
        
        return self.results_df
    
    def analyze_results(self) -> Dict:
        """
        Analyze regional performance and generate recommendations.
        """
        print(f"\n{'='*70}")
        print(f"ANALYSIS")
        print(f"{'='*70}")
        
        # Calculate regional summaries
        summary = []
        
        for region in sorted(self.results_df['region'].unique()):
            region_data = self.results_df[self.results_df['region'] == region]
            ci_value = region_data['ci_value'].iloc[0]
            
            # Get baseline (operational_only)
            baseline = region_data[region_data['strategy'] == 'operational_only']['total_carbon_g']
            baseline_mean = baseline.mean()
            baseline_operational = region_data[region_data['strategy'] == 'operational_only']['operational_g'].mean()
            baseline_embodied = region_data[region_data['strategy'] == 'operational_only']['embodied_g'].mean()
            
            for strategy in ['operational_only', 'embodied_prioritized', 'balanced']:
                strategy_data = region_data[region_data['strategy'] == strategy]
                strategy_mean = strategy_data['total_carbon_g'].mean()
                strategy_operational = strategy_data['operational_g'].mean()
                strategy_embodied = strategy_data['embodied_g'].mean()
                
                # Calculate percentage difference from baseline
                pct_diff = ((strategy_mean - baseline_mean) / baseline_mean) * 100
                
                # Statistical test (if not baseline)
                if strategy != 'operational_only':
                    t_stat, p_value = stats.ttest_ind(baseline, strategy_data['total_carbon_g'])
                else:
                    t_stat, p_value = 0, 1.0
                
                summary.append({
                    'region': region,
                    'ci_value': ci_value,
                    'strategy': strategy,
                    'operational_g': strategy_operational,
                    'embodied_g': strategy_embodied,
                    'total_mean_g': strategy_mean,
                    'pct_vs_baseline': pct_diff,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                })
        
        summary_df = pd.DataFrame(summary)
        
        # Save summary
        summary_file = self.output_dir / "regional_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\n✅ Regional summary saved to: {summary_file}")
        
        # Generate recommendations table
        self._generate_recommendations(summary_df)
        
        # Generate summary report
        self._generate_summary_report(summary_df)
        
        return {
            'summary_df': summary_df
        }
    
    def _generate_recommendations(self, summary_df: pd.DataFrame):
        """
        Generate regional recommendations table.
        """
        print(f"\n{'='*70}")
        print(f"REGIONAL RECOMMENDATIONS")
        print(f"{'='*70}")
        
        recommendations = []
        
        for region in sorted(summary_df['region'].unique()):
            region_data = summary_df[summary_df['region'] == region]
            ci_value = region_data['ci_value'].iloc[0]
            
            # Find best strategy (lowest carbon)
            best_strategy = region_data.loc[region_data['total_mean_g'].idxmin(), 'strategy']
            best_carbon = region_data['total_mean_g'].min()
            
            # Get operational_only for comparison
            operational_carbon = region_data[region_data['strategy'] == 'operational_only']['total_mean_g'].values[0]
            
            # Calculate savings
            savings_g = operational_carbon - best_carbon
            savings_pct = (savings_g / operational_carbon) * 100
            
            print(f"\n{region} (CI={ci_value}):")
            print(f"  Best strategy: {best_strategy}")
            print(f"  Carbon: {best_carbon:.2f}g")
            print(f"  vs Operational: {savings_pct:+.2f}%")
            
            recommendations.append({
                'region': region,
                'ci_gco2_kwh': ci_value,
                'recommended_strategy': best_strategy,
                'carbon_g': best_carbon,
                'baseline_carbon_g': operational_carbon,
                'savings_g': savings_g,
                'savings_pct': savings_pct
            })
        
        # Save recommendations
        recommendations_df = pd.DataFrame(recommendations)
        recommendations_file = self.output_dir / "recommendations_table.csv"
        recommendations_df.to_csv(recommendations_file, index=False)
        print(f"\n✅ Recommendations saved to: {recommendations_file}")
    
    def _generate_summary_report(self, summary_df: pd.DataFrame):
        """
        Generate text summary report.
        """
        report_file = self.output_dir / "analysis_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("REGIONAL PERFORMANCE MATRIX - ANALYSIS SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Experiment: EXP-002\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s\n\n")
            
            f.write("-"*70 + "\n")
            f.write("REGIONAL PERFORMANCE\n")
            f.write("-"*70 + "\n\n")
            
            for region in sorted(summary_df['region'].unique()):
                region_data = summary_df[summary_df['region'] == region]
                ci_value = region_data['ci_value'].iloc[0]
                
                f.write(f"{region} (CI = {ci_value} gCO₂/kWh):\n")
                
                for strategy in ['operational_only', 'embodied_prioritized', 'balanced']:
                    row = region_data[region_data['strategy'] == strategy].iloc[0]
                    sig = "***" if row['p_value'] < 0.001 else "**" if row['p_value'] < 0.01 else "*" if row['p_value'] < 0.05 else ""
                    
                    f.write(f"  {strategy:22s}: ")
                    f.write(f"{row['total_mean_g']:7.2f}g ")
                    f.write(f"({row['pct_vs_baseline']:+6.2f}%) {sig}\n")
                
                f.write("\n")
        
        print(f"\n✅ Summary report saved to: {report_file}")
    
    def plot_results(self):
        """
        Generate publication-quality visualization.
        """
        print(f"\n{'='*70}")
        print(f"GENERATING VISUALIZATIONS")
        print(f"{'='*70}")
        
        # Calculate means for plotting
        plot_data = []
        for region in sorted(self.results_df['region'].unique()):
            region_data = self.results_df[self.results_df['region'] == region]
            ci_value = region_data['ci_value'].iloc[0]
            
            for strategy in ['operational_only', 'embodied_prioritized', 'balanced']:
                strategy_data = region_data[region_data['strategy'] == strategy]
                mean_carbon = strategy_data['total_carbon_g'].mean()
                std_carbon = strategy_data['total_carbon_g'].std()
                mean_operational = strategy_data['operational_g'].mean()
                mean_embodied = strategy_data['embodied_g'].mean()
                
                plot_data.append({
                    'region': region,
                    'ci_value': ci_value,
                    'strategy': strategy,
                    'total_carbon': mean_carbon,
                    'std_carbon': std_carbon,
                    'operational': mean_operational,
                    'embodied': mean_embodied
                })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot 1: Total carbon by region
        regions = sorted(plot_df['region'].unique())
        x = np.arange(len(regions))
        width = 0.25
        
        for idx, strategy in enumerate(['operational_only', 'embodied_prioritized', 'balanced']):
            data = plot_df[plot_df['strategy'] == strategy]
            data = data.sort_values('region')
            
            ax1.bar(x + (idx - 1) * width, data['total_carbon'], width,
                   label=strategy.replace('_', ' ').title(),
                   yerr=data['std_carbon'], capsize=5)
        
        ax1.set_xlabel('Region', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Total Carbon Emissions (g)', fontsize=12, fontweight='bold')
        ax1.set_title('Regional Performance Comparison', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(regions, rotation=0)
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Plot 2: Stacked bar showing operational vs embodied
        for idx, strategy in enumerate(['operational_only', 'embodied_prioritized', 'balanced']):
            ax = plt.subplot(1, 3, idx + 1)
            
            data = plot_df[plot_df['strategy'] == strategy].sort_values('region')
            
            ax.bar(data['region'], data['operational'], label='Operational', color='#d62728')
            ax.bar(data['region'], data['embodied'], bottom=data['operational'], 
                   label='Embodied', color='#2ca02c')
            
            ax.set_title(strategy.replace('_', ' ').title(), fontsize=11, fontweight='bold')
            ax.set_ylabel('Carbon (g)' if idx == 0 else '', fontsize=10)
            ax.set_xticklabels(data['region'], rotation=45, ha='right')
            if idx == 2:
                ax.legend(loc='upper left', fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Save main figure
        figure_file = self.output_dir / "regional_comparison.png"
        plt.savefig(figure_file, dpi=300, bbox_inches='tight')
        print(f"✅ Figure saved to: {figure_file}")
        
        plt.close()
        
        # Create second figure: Percentage difference from baseline
        fig, ax = plt.subplots(figsize=(10, 6))
        
        regions_sorted = sorted(plot_df['region'].unique(), 
                               key=lambda r: REGIONAL_CI[r])
        x = np.arange(len(regions_sorted))
        width = 0.35
        
        for idx, strategy in enumerate(['embodied_prioritized', 'balanced']):
            pct_diffs = []
            for region in regions_sorted:
                baseline = plot_df[(plot_df['region'] == region) & 
                                  (plot_df['strategy'] == 'operational_only')]['total_carbon'].values[0]
                strategy_val = plot_df[(plot_df['region'] == region) & 
                                      (plot_df['strategy'] == strategy)]['total_carbon'].values[0]
                pct_diff = ((strategy_val - baseline) / baseline) * 100
                pct_diffs.append(pct_diff)
            
            ax.bar(x + (idx - 0.5) * width, pct_diffs, width,
                   label=strategy.replace('_', ' ').title())
        
        ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Breakeven')
        ax.set_xlabel('Region (sorted by CI)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Difference from Baseline (%)', fontsize=12, fontweight='bold')
        ax.set_title('Strategy Performance vs. Operational-Only Baseline', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        
        # Add CI values to labels
        labels = [f"{r}\n({REGIONAL_CI[r]} gCO₂/kWh)" for r in regions_sorted]
        ax.set_xticklabels(labels, rotation=0)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Save percentage figure
        pct_figure_file = self.output_dir / "regional_percentage_comparison.png"
        plt.savefig(pct_figure_file, dpi=300, bbox_inches='tight')
        print(f"✅ Percentage figure saved to: {pct_figure_file}")
        
        plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Regional Performance Matrix (EXP-002)"
    )
    parser.add_argument(
        '--regions',
        type=str,
        default='Northern,Southern,Eastern,Western',
        help='Comma-separated regions to test'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=14400,
        help='Task duration in seconds (default: 14400 = 4hr)'
    )
    parser.add_argument(
        '--tasks',
        type=int,
        default=200,
        help='Number of tasks per region (default: 200)'
    )
    parser.add_argument(
        '--strategies',
        type=str,
        default='operational_only,embodied_prioritized,balanced',
        help='Comma-separated strategies to test'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='regional_matrix',
        help='Output directory (default: regional_matrix/)'
    )
    
    args = parser.parse_args()
    
    # Parse inputs
    regions = args.regions.split(',')
    strategies = args.strategies.split(',')
    
    # Initialize tester
    tester = RegionalPerformanceTester(output_dir=args.output)
    
    # Run regional matrix
    results_df = tester.run_regional_matrix(
        regions=regions,
        duration_s=args.duration,
        num_tasks_per_region=args.tasks,
        strategies=strategies
    )
    
    # Analyze results
    analysis = tester.analyze_results()
    
    # Generate visualizations
    tester.plot_results()
    
    print(f"\n{'='*70}")
    print(f"✅ EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Total runtime: {(datetime.now() - tester.start_time).total_seconds():.1f}s")
    print(f"Output directory: {tester.output_dir}")
    print(f"\nNext steps:")
    print(f"  1. Review: {tester.output_dir}/analysis_summary.txt")
    print(f"  2. Check: {tester.output_dir}/regional_comparison.png")
    print(f"  3. Table: {tester.output_dir}/recommendations_table.csv")
    print(f"  4. Data: {tester.output_dir}/regional_performance.csv")


if __name__ == "__main__":
    main()
