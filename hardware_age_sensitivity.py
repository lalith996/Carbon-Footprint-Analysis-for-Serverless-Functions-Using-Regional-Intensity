#!/usr/bin/env python3
"""
Hardware Age Sensitivity (EXP-004)
===================================
Test aging rates to validate aging threshold where embodied-aware wins.

Target: IEEE Transactions on Sustainable Computing
Deadline: 2025-11-18
Task: EXP-004 of publication pipeline

Key Question: At what aging rate does embodied-aware become beneficial?
Expected Threshold: ~7%/year (from boundary tests)

Test Range: 5% to 30%/year
- Modern hardware: 5-8%/year (embodied should win)
- Standard hardware: 10-15%/year (operational wins)
- Degraded hardware: 20-30%/year (operational wins strongly)
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
    BASE_POWER_W,
    PUE_DEFAULT as PUE
)

# Constants
EMBODIED_CARBON_KG = 660  # kg CO2e per server
BASELINE_CI = 535  # Northern region CI (gCO₂/kWh)

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


class HardwareAgeTester:
    """
    Test strategy performance across different hardware aging rates.
    """
    
    def __init__(self, output_dir: str = "hardware_age_sensitivity"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = []
        self.start_time = datetime.now()
        
    def calculate_power_with_aging(
        self,
        base_power_w: float,
        age_years: float,
        aging_rate: float
    ) -> float:
        """
        Calculate power consumption with custom aging rate.
        
        Args:
            base_power_w: Base power for new hardware
            age_years: Server age in years
            aging_rate: Efficiency degradation rate (e.g., 0.12 for 12%/year)
            
        Returns:
            Power consumption in watts
        """
        # Power increases linearly with age
        power_w = base_power_w * (1 + aging_rate * age_years)
        
        # Cap at 60% increase (same as original implementation)
        max_power = base_power_w * 1.6
        return min(power_w, max_power)
    
    def calculate_carbon_with_aging(
        self,
        ci_value: float,
        duration_s: float,
        age_years: float,
        aging_rate: float
    ) -> Dict[str, float]:
        """
        Calculate carbon with custom aging rate.
        
        Args:
            ci_value: Carbon intensity (gCO₂/kWh)
            duration_s: Duration in seconds
            age_years: Server age in years
            aging_rate: Efficiency degradation rate
            
        Returns:
            Dictionary with carbon breakdown
        """
        # Operational carbon
        power_w = self.calculate_power_with_aging(BASE_POWER_W, age_years, aging_rate)
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
            'energy_kwh': energy_kwh,
            'aging_rate': aging_rate
        }
    
    def test_aging_rate(
        self,
        aging_rate_pct: float,
        duration_s: float,
        num_tasks: int,
        strategies: List[str]
    ) -> List[Dict]:
        """
        Test a single aging rate across multiple strategies.
        
        Args:
            aging_rate_pct: Aging rate as percentage (e.g., 12 for 12%/year)
            duration_s: Task duration in seconds
            num_tasks: Number of tasks to simulate
            strategies: List of strategies to test
            
        Returns:
            List of result dictionaries
        """
        task_results = []
        aging_rate = aging_rate_pct / 100  # Convert to decimal
        
        print(f"\n{'='*70}")
        print(f"Testing Aging Rate = {aging_rate_pct}%/year")
        print(f"{'='*70}")
        
        # Define ages for each strategy
        strategy_ages = {
            "operational_only": 0.5,   # New hardware
            "embodied_prioritized": 4.0,  # Old hardware
            "balanced": 2.5  # Medium age
        }
        
        for strategy_name in strategies:
            age_years = strategy_ages[strategy_name]
            print(f"\n  Strategy: {strategy_name} (age={age_years}y)")
            strategy_carbon = []
            
            for task_idx in range(num_tasks):
                if (task_idx + 1) % 50 == 0:
                    print(f"    Task {task_idx + 1}/{num_tasks}...")
                
                # Calculate carbon
                carbon_breakdown = self.calculate_carbon_with_aging(
                    BASELINE_CI, duration_s, age_years, aging_rate
                )
                
                strategy_carbon.append(carbon_breakdown['total_g'])
                
                # Store individual task result
                task_results.append({
                    'aging_rate_pct': aging_rate_pct,
                    'strategy': strategy_name,
                    'task_id': task_idx,
                    'server_age_years': age_years,
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
    
    def run_aging_sensitivity(
        self,
        aging_rates: List[float],
        duration_s: float,
        num_tasks_per_rate: int,
        strategies: List[str]
    ):
        """
        Run complete hardware age sensitivity analysis.
        """
        print(f"\n{'='*70}")
        print(f"HARDWARE AGE SENSITIVITY (EXP-004)")
        print(f"{'='*70}")
        print(f"Aging rates: {aging_rates}%/year")
        print(f"Duration: {duration_s}s ({duration_s/3600:.1f}hr)")
        print(f"Tasks per rate: {num_tasks_per_rate}")
        print(f"Strategies: {strategies}")
        print(f"Total tasks: {len(aging_rates) * num_tasks_per_rate * len(strategies)}")
        print(f"Output directory: {self.output_dir}")
        
        all_results = []
        
        for aging_rate in aging_rates:
            task_results = self.test_aging_rate(
                aging_rate, duration_s, num_tasks_per_rate, strategies
            )
            all_results.extend(task_results)
        
        # Convert to DataFrame
        self.results_df = pd.DataFrame(all_results)
        
        # Save raw results
        output_file = self.output_dir / "aging_sensitivity.csv"
        self.results_df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved to: {output_file}")
        
        return self.results_df
    
    def analyze_results(self) -> Dict:
        """
        Analyze results and identify aging threshold.
        """
        print(f"\n{'='*70}")
        print(f"ANALYSIS")
        print(f"{'='*70}")
        
        # Calculate strategy comparisons
        summary = []
        
        for aging_rate in sorted(self.results_df['aging_rate_pct'].unique()):
            rate_data = self.results_df[self.results_df['aging_rate_pct'] == aging_rate]
            
            # Get baseline (operational_only)
            baseline = rate_data[rate_data['strategy'] == 'operational_only']['total_carbon_g']
            baseline_mean = baseline.mean()
            
            for strategy in ['embodied_prioritized', 'balanced']:
                strategy_data = rate_data[rate_data['strategy'] == strategy]['total_carbon_g']
                strategy_mean = strategy_data.mean()
                
                # Calculate percentage difference
                pct_diff = ((strategy_mean - baseline_mean) / baseline_mean) * 100
                
                # Statistical test
                t_stat, p_value = stats.ttest_ind(baseline, strategy_data)
                
                summary.append({
                    'aging_rate_pct': aging_rate,
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
        
        # Identify threshold
        threshold_analysis = self._identify_threshold(summary_df)
        
        # Generate summary report
        self._generate_summary_report(summary_df, threshold_analysis)
        
        return {
            'summary_df': summary_df,
            'threshold': threshold_analysis
        }
    
    def _identify_threshold(self, summary_df: pd.DataFrame) -> Dict:
        """
        Identify aging rate threshold where embodied-aware becomes beneficial.
        """
        print(f"\n{'='*70}")
        print(f"THRESHOLD IDENTIFICATION")
        print(f"{'='*70}")
        
        threshold_results = {}
        
        for strategy in ['embodied_prioritized', 'balanced']:
            strategy_data = summary_df[summary_df['strategy'] == strategy].sort_values('aging_rate_pct')
            
            # Find where percentage difference crosses zero
            pct_diffs = strategy_data['pct_difference'].values
            aging_rates = strategy_data['aging_rate_pct'].values
            
            # Find sign change (from negative to positive)
            crossover_idx = None
            for i in range(len(pct_diffs) - 1):
                if pct_diffs[i] < 0 and pct_diffs[i+1] > 0:
                    crossover_idx = i
                    break
            
            if crossover_idx is not None:
                # Linear interpolation for precise crossover
                x1, x2 = aging_rates[crossover_idx], aging_rates[crossover_idx + 1]
                y1, y2 = pct_diffs[crossover_idx], pct_diffs[crossover_idx + 1]
                
                threshold_rate = x1 + (0 - y1) * (x2 - x1) / (y2 - y1)
                
                print(f"\n{strategy}:")
                print(f"  Threshold: {threshold_rate:.1f}%/year")
                print(f"  Between: {x1}% and {x2}%/year")
                print(f"  Below {threshold_rate:.1f}%: Embodied WINS")
                print(f"  Above {threshold_rate:.1f}%: Operational WINS")
                
                threshold_results[strategy] = {
                    'threshold_pct': threshold_rate,
                    'rate_below': x1,
                    'rate_above': x2,
                    'pct_diff_below': y1,
                    'pct_diff_above': y2
                }
            else:
                # Check if all negative or all positive
                all_negative = all(pct_diffs < 0)
                all_positive = all(pct_diffs > 0)
                
                if all_negative:
                    print(f"\n{strategy}: Embodied ALWAYS wins (threshold > {aging_rates[-1]}%)")
                elif all_positive:
                    print(f"\n{strategy}: Operational ALWAYS wins (threshold < {aging_rates[0]}%)")
                
                threshold_results[strategy] = None
        
        return threshold_results
    
    def _generate_summary_report(self, summary_df: pd.DataFrame, threshold: Dict):
        """
        Generate text summary report.
        """
        report_file = self.output_dir / "analysis_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("HARDWARE AGE SENSITIVITY - ANALYSIS SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Experiment: EXP-004\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s\n\n")
            
            f.write("-"*70 + "\n")
            f.write("AGING RATE THRESHOLDS\n")
            f.write("-"*70 + "\n\n")
            
            for strategy, result in threshold.items():
                if result:
                    f.write(f"{strategy}:\n")
                    f.write(f"  Empirical threshold: {result['threshold_pct']:.1f}%/year\n")
                    f.write(f"  Expected threshold: 7.0%/year\n")
                    f.write(f"  Difference: {abs(result['threshold_pct'] - 7.0):.1f}%/year\n")
                    f.write(f"  Relative error: {abs(result['threshold_pct'] - 7.0) / 7.0 * 100:.1f}%\n\n")
                else:
                    f.write(f"{strategy}: No threshold in tested range\n\n")
            
            f.write("-"*70 + "\n")
            f.write("PERFORMANCE BY AGING RATE\n")
            f.write("-"*70 + "\n\n")
            
            for strategy in ['embodied_prioritized', 'balanced']:
                f.write(f"\n{strategy}:\n")
                strategy_data = summary_df[summary_df['strategy'] == strategy].sort_values('aging_rate_pct')
                
                for _, row in strategy_data.iterrows():
                    sig = "***" if row['p_value'] < 0.001 else "**" if row['p_value'] < 0.01 else "*" if row['p_value'] < 0.05 else ""
                    winner = "EMBODIED" if row['pct_difference'] < 0 else "OPERATIONAL"
                    f.write(f"  {row['aging_rate_pct']:3.0f}%/yr: {row['pct_difference']:+6.2f}% {sig} ({winner})\n")
        
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
        for aging_rate in sorted(self.results_df['aging_rate_pct'].unique()):
            rate_data = self.results_df[self.results_df['aging_rate_pct'] == aging_rate]
            
            baseline = rate_data[rate_data['strategy'] == 'operational_only']['total_carbon_g'].mean()
            
            for strategy in ['operational_only', 'embodied_prioritized', 'balanced']:
                strategy_mean = rate_data[rate_data['strategy'] == strategy]['total_carbon_g'].mean()
                strategy_std = rate_data[rate_data['strategy'] == strategy]['total_carbon_g'].std()
                
                pct_diff = ((strategy_mean - baseline) / baseline) * 100 if strategy != 'operational_only' else 0
                
                plot_data.append({
                    'aging_rate_pct': aging_rate,
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
                data['aging_rate_pct'],
                data['mean_carbon'],
                yerr=data['std_carbon'],
                marker='o',
                linewidth=2,
                capsize=5,
                label=strategy.replace('_', ' ').title()
            )
        
        ax1.set_xlabel('Aging Rate (%/year)', fontsize=12)
        ax1.set_ylabel('Total Carbon Emissions (g)', fontsize=12)
        ax1.set_title('Carbon Emissions vs. Aging Rate', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Percentage difference from baseline
        for strategy in ['embodied_prioritized', 'balanced']:
            data = plot_df[plot_df['strategy'] == strategy]
            ax2.plot(
                data['aging_rate_pct'],
                data['pct_difference'],
                marker='o',
                linewidth=2,
                label=strategy.replace('_', ' ').title()
            )
        
        ax2.axhline(y=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Breakeven')
        ax2.axvline(x=7, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='Expected (7%)')
        ax2.set_xlabel('Aging Rate (%/year)', fontsize=12)
        ax2.set_ylabel('Difference from Baseline (%)', fontsize=12)
        ax2.set_title('Relative Performance vs. Aging Rate', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Highlight regions
        ax2.axvspan(0, 7, alpha=0.1, color='green', label='Embodied Wins')
        ax2.axvspan(7, 30, alpha=0.1, color='red', label='Operational Wins')
        
        plt.tight_layout()
        
        # Save figure
        figure_file = self.output_dir / "aging_sensitivity.png"
        plt.savefig(figure_file, dpi=300, bbox_inches='tight')
        print(f"✅ Figure saved to: {figure_file}")
        
        plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Hardware Age Sensitivity (EXP-004)"
    )
    parser.add_argument(
        '--rates',
        type=str,
        default='5,8,10,12,15,20,25,30',
        help='Comma-separated aging rates (%/year)'
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
        help='Number of tasks per aging rate (default: 200)'
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
        default='hardware_age_sensitivity',
        help='Output directory (default: hardware_age_sensitivity/)'
    )
    
    args = parser.parse_args()
    
    # Parse inputs
    aging_rates = [float(x) for x in args.rates.split(',')]
    strategies = args.strategies.split(',')
    
    # Initialize tester
    tester = HardwareAgeTester(output_dir=args.output)
    
    # Run aging sensitivity
    results_df = tester.run_aging_sensitivity(
        aging_rates=aging_rates,
        duration_s=args.duration,
        num_tasks_per_rate=args.tasks,
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
    print(f"  2. Check: {tester.output_dir}/aging_sensitivity.png")
    print(f"  3. Data: {tester.output_dir}/aging_sensitivity.csv")


if __name__ == "__main__":
    main()
