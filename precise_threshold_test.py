#!/usr/bin/env python3
"""
Precise CI Threshold Mapping (EXP-001)
======================================
Test fine-grained CI values to precisely identify empirical crossover point.

Target: IEEE Transactions on Sustainable Computing
Deadline: 2025-12-21
Task Deadline: 2025-11-10

Theoretical threshold: 215 gCO₂/kWh
Testing range: 175-350 gCO₂/kWh (8 points)
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
import time

# Import project modules
from scheduler_embodied_aware import (
    choose_region_embodied_aware,
    calculate_power_consumption,
    SERVER_SPECS,
    BASE_POWER_W,
    PUE_DEFAULT as PUE
)

# Embodied carbon constant (not exported from scheduler)
EMBODIED_CARBON_KG = 660  # kg CO2e per server

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


class PreciseThresholdTester:
    """
    Test precise CI thresholds to identify empirical crossover point.
    """
    
    def __init__(self, output_dir: str = "threshold_precise"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = []
        self.start_time = datetime.now()
        
    def test_single_ci(
        self,
        ci_value: float,
        duration_s: float,
        num_tasks: int,
        strategies: List[str]
    ) -> List[Dict]:
        """
        Test a single CI value across multiple strategies.
        
        Args:
            ci_value: Carbon intensity (gCO₂/kWh)
            duration_s: Task duration in seconds
            num_tasks: Number of tasks to simulate
            strategies: List of strategies to test
            
        Returns:
            List of result dictionaries
        """
        task_results = []
        
        print(f"\n{'='*70}")
        print(f"Testing CI = {ci_value} gCO₂/kWh")
        print(f"{'='*70}")
        
        for strategy_name in strategies:
            print(f"\n  Strategy: {strategy_name}")
            strategy_carbon = []
            
            for task_idx in range(num_tasks):
                if (task_idx + 1) % 50 == 0:
                    print(f"    Task {task_idx + 1}/{num_tasks}...")
                
                # Select region based on strategy
                if strategy_name == "operational_only":
                    region = "Northern"  # Fixed region for consistency
                    server_age = "new"
                elif strategy_name == "embodied_prioritized":
                    region = "Northern"
                    server_age = "old"  # Prioritize old servers
                elif strategy_name == "balanced":
                    # Use embodied-aware scheduler
                    region, server_age = choose_region_embodied_aware(
                        workload_scale=400000,
                        duration_s=duration_s,
                        regions=["Northern"]  # Single region test
                    )
                else:
                    raise ValueError(f"Unknown strategy: {strategy_name}")
                
                # Calculate carbon with override CI
                total_carbon = self._calculate_carbon_with_override(
                    ci_value, duration_s, server_age
                )
                
                strategy_carbon.append(total_carbon)
                
                # Store individual task result
                task_results.append({
                    'ci_value': ci_value,
                    'strategy': strategy_name,
                    'task_id': task_idx,
                    'region': region,
                    'server_age': server_age,
                    'duration_s': duration_s,
                    'total_carbon_g': total_carbon,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Summary statistics
            mean_carbon = np.mean(strategy_carbon)
            std_carbon = np.std(strategy_carbon)
            print(f"    Mean carbon: {mean_carbon:.2f}g (±{std_carbon:.2f})")
        
        return task_results
    
    def _calculate_carbon_with_override(
        self,
        ci_override: float,
        duration_s: float,
        server_age: str
    ) -> float:
        """
        Calculate total carbon with overridden CI value.
        
        Args:
            ci_override: Override carbon intensity (gCO₂/kWh)
            duration_s: Duration in seconds
            server_age: Server age category
            
        Returns:
            Total carbon in grams
        """
        age_years = SERVER_SPECS[server_age]["age_years"]
        
        # Operational carbon
        power_w = calculate_power_consumption(BASE_POWER_W, age_years)
        energy_kwh = (power_w * duration_s) / (1000 * 3600)
        operational_g = energy_kwh * ci_override * PUE
        
        # Embodied carbon
        lifetime_hours = 5 * 365.25 * 24
        carbon_per_hour = (EMBODIED_CARBON_KG * 1000) / lifetime_hours
        task_carbon_raw = carbon_per_hour * (duration_s / 3600)
        debt_ratio = (5 - age_years) / 5
        embodied_g = task_carbon_raw * debt_ratio
        
        return operational_g + embodied_g
    
    def run_threshold_mapping(
        self,
        ci_values: List[float],
        duration_s: float,
        num_tasks_per_ci: int,
        strategies: List[str]
    ):
        """
        Run complete threshold mapping across CI values.
        """
        print(f"\n{'='*70}")
        print(f"PRECISE CI THRESHOLD MAPPING (EXP-001)")
        print(f"{'='*70}")
        print(f"CI values: {ci_values}")
        print(f"Duration: {duration_s}s ({duration_s/3600:.1f}hr)")
        print(f"Tasks per CI: {num_tasks_per_ci}")
        print(f"Strategies: {strategies}")
        print(f"Total tasks: {len(ci_values) * num_tasks_per_ci * len(strategies)}")
        print(f"Output directory: {self.output_dir}")
        
        all_results = []
        
        for ci_value in ci_values:
            task_results = self.test_single_ci(
                ci_value, duration_s, num_tasks_per_ci, strategies
            )
            all_results.extend(task_results)
        
        # Convert to DataFrame
        self.results_df = pd.DataFrame(all_results)
        
        # Save raw results
        output_file = self.output_dir / "results_ci_mapping.csv"
        self.results_df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved to: {output_file}")
        
        return self.results_df
    
    def analyze_results(self) -> Dict:
        """
        Analyze results and identify crossover point.
        """
        print(f"\n{'='*70}")
        print(f"ANALYSIS")
        print(f"{'='*70}")
        
        # Calculate strategy comparisons
        summary = []
        
        for ci_value in sorted(self.results_df['ci_value'].unique()):
            ci_data = self.results_df[self.results_df['ci_value'] == ci_value]
            
            # Get baseline (operational_only)
            baseline = ci_data[ci_data['strategy'] == 'operational_only']['total_carbon_g']
            baseline_mean = baseline.mean()
            
            for strategy in ['embodied_prioritized', 'balanced']:
                strategy_data = ci_data[ci_data['strategy'] == strategy]['total_carbon_g']
                strategy_mean = strategy_data.mean()
                
                # Calculate percentage difference
                pct_diff = ((strategy_mean - baseline_mean) / baseline_mean) * 100
                
                # Statistical test
                t_stat, p_value = stats.ttest_ind(baseline, strategy_data)
                
                summary.append({
                    'ci_value': ci_value,
                    'strategy': strategy,
                    'baseline_mean_g': baseline_mean,
                    'strategy_mean_g': strategy_mean,
                    'difference_g': strategy_mean - baseline_mean,
                    'pct_difference': pct_diff,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                })
        
        summary_df = pd.DataFrame(summary)
        
        # Save summary
        summary_file = self.output_dir / "strategy_comparison.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\n✅ Strategy comparison saved to: {summary_file}")
        
        # Identify crossover point
        crossover_analysis = self._identify_crossover(summary_df)
        
        # Generate summary report
        self._generate_summary_report(summary_df, crossover_analysis)
        
        return {
            'summary_df': summary_df,
            'crossover': crossover_analysis
        }
    
    def _identify_crossover(self, summary_df: pd.DataFrame) -> Dict:
        """
        Identify precise CI crossover point.
        """
        print(f"\n{'='*70}")
        print(f"CROSSOVER POINT IDENTIFICATION")
        print(f"{'='*70}")
        
        crossover_results = {}
        
        for strategy in ['embodied_prioritized', 'balanced']:
            strategy_data = summary_df[summary_df['strategy'] == strategy].sort_values('ci_value')
            
            # Find where percentage difference crosses zero
            pct_diffs = strategy_data['pct_difference'].values
            ci_values = strategy_data['ci_value'].values
            
            # Find sign change
            crossover_idx = None
            for i in range(len(pct_diffs) - 1):
                if pct_diffs[i] < 0 and pct_diffs[i+1] > 0:
                    crossover_idx = i
                    break
            
            if crossover_idx is not None:
                # Linear interpolation for precise crossover
                x1, x2 = ci_values[crossover_idx], ci_values[crossover_idx + 1]
                y1, y2 = pct_diffs[crossover_idx], pct_diffs[crossover_idx + 1]
                
                crossover_ci = x1 + (0 - y1) * (x2 - x1) / (y2 - y1)
                
                print(f"\n{strategy}:")
                print(f"  Crossover CI: {crossover_ci:.1f} gCO₂/kWh")
                print(f"  Between: {x1} and {x2} gCO₂/kWh")
                
                crossover_results[strategy] = {
                    'crossover_ci': crossover_ci,
                    'ci_below': x1,
                    'ci_above': x2,
                    'pct_diff_below': y1,
                    'pct_diff_above': y2
                }
            else:
                print(f"\n{strategy}: No crossover found in tested range")
                crossover_results[strategy] = None
        
        return crossover_results
    
    def _generate_summary_report(self, summary_df: pd.DataFrame, crossover: Dict):
        """
        Generate text summary report.
        """
        report_file = self.output_dir / "analysis_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("PRECISE CI THRESHOLD MAPPING - ANALYSIS SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Experiment: EXP-001\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s\n\n")
            
            f.write("-"*70 + "\n")
            f.write("CROSSOVER POINTS\n")
            f.write("-"*70 + "\n\n")
            
            for strategy, result in crossover.items():
                if result:
                    f.write(f"{strategy}:\n")
                    f.write(f"  Empirical crossover: {result['crossover_ci']:.1f} gCO₂/kWh\n")
                    f.write(f"  Theoretical crossover: 215 gCO₂/kWh\n")
                    f.write(f"  Difference: {abs(result['crossover_ci'] - 215):.1f} gCO₂/kWh\n")
                    f.write(f"  Relative error: {abs(result['crossover_ci'] - 215) / 215 * 100:.1f}%\n\n")
                else:
                    f.write(f"{strategy}: No crossover found\n\n")
            
            f.write("-"*70 + "\n")
            f.write("PERFORMANCE BY CI RANGE\n")
            f.write("-"*70 + "\n\n")
            
            for strategy in ['embodied_prioritized', 'balanced']:
                f.write(f"\n{strategy}:\n")
                strategy_data = summary_df[summary_df['strategy'] == strategy].sort_values('ci_value')
                
                for _, row in strategy_data.iterrows():
                    sig = "***" if row['p_value'] < 0.001 else "**" if row['p_value'] < 0.01 else "*" if row['p_value'] < 0.05 else ""
                    f.write(f"  CI={row['ci_value']:3.0f}: {row['pct_difference']:+6.2f}% {sig}\n")
        
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
        for ci_value in sorted(self.results_df['ci_value'].unique()):
            ci_data = self.results_df[self.results_df['ci_value'] == ci_value]
            
            baseline = ci_data[ci_data['strategy'] == 'operational_only']['total_carbon_g'].mean()
            
            for strategy in ['operational_only', 'embodied_prioritized', 'balanced']:
                strategy_mean = ci_data[ci_data['strategy'] == strategy]['total_carbon_g'].mean()
                strategy_std = ci_data[ci_data['strategy'] == strategy]['total_carbon_g'].std()
                
                pct_diff = ((strategy_mean - baseline) / baseline) * 100 if strategy != 'operational_only' else 0
                
                plot_data.append({
                    'ci_value': ci_value,
                    'strategy': strategy,
                    'mean_carbon': strategy_mean,
                    'std_carbon': strategy_std,
                    'pct_difference': pct_diff
                })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Plot 1: Absolute carbon emissions
        for strategy in ['operational_only', 'embodied_prioritized', 'balanced']:
            data = plot_df[plot_df['strategy'] == strategy]
            ax1.errorbar(
                data['ci_value'],
                data['mean_carbon'],
                yerr=data['std_carbon'],
                marker='o',
                linewidth=2,
                capsize=5,
                label=strategy.replace('_', ' ').title()
            )
        
        ax1.set_xlabel('Carbon Intensity (gCO₂/kWh)', fontsize=12)
        ax1.set_ylabel('Total Carbon Emissions (g)', fontsize=12)
        ax1.set_title('Absolute Carbon Emissions vs. CI', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Percentage difference from baseline
        for strategy in ['embodied_prioritized', 'balanced']:
            data = plot_df[plot_df['strategy'] == strategy]
            ax2.plot(
                data['ci_value'],
                data['pct_difference'],
                marker='o',
                linewidth=2,
                label=strategy.replace('_', ' ').title()
            )
        
        ax2.axhline(y=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Breakeven')
        ax2.axvline(x=215, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='Theoretical (215)')
        ax2.set_xlabel('Carbon Intensity (gCO₂/kWh)', fontsize=12)
        ax2.set_ylabel('Difference from Baseline (%)', fontsize=12)
        ax2.set_title('Relative Performance vs. CI', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save figure
        figure_file = self.output_dir / "ci_crossover_precise.png"
        plt.savefig(figure_file, dpi=300, bbox_inches='tight')
        print(f"✅ Figure saved to: {figure_file}")
        
        plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Precise CI Threshold Mapping (EXP-001)"
    )
    parser.add_argument(
        '--ci',
        type=str,
        default='175,200,225,250,275,300,325,350',
        help='Comma-separated CI values to test'
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
        default=300,
        help='Number of tasks per CI value (default: 300)'
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
        default='threshold_precise',
        help='Output directory (default: threshold_precise/)'
    )
    
    args = parser.parse_args()
    
    # Parse inputs
    ci_values = [float(x) for x in args.ci.split(',')]
    strategies = args.strategies.split(',')
    
    # Initialize tester
    tester = PreciseThresholdTester(output_dir=args.output)
    
    # Run threshold mapping
    results_df = tester.run_threshold_mapping(
        ci_values=ci_values,
        duration_s=args.duration,
        num_tasks_per_ci=args.tasks,
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
    print(f"  2. Check: {tester.output_dir}/ci_crossover_precise.png")
    print(f"  3. Data: {tester.output_dir}/results_ci_mapping.csv")


if __name__ == "__main__":
    main()
