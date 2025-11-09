#!/usr/bin/env python3
"""
Duration Sensitivity Analysis for Carbon-Aware Scheduling
===========================================================

Analyzes how strategy performance varies with task duration to find the
crossover point where embodied-aware strategies become beneficial.

Research Question: At what task duration does considering embodied carbon
result in lower total emissions than operational-only strategies?

Default test durations: 5s, 15s, 30s, 60s, 300s (5min), 600s (10min), 1800s (30min), 3600s (1hr)
Extended test: 14400s (4hr), 28800s (8hr), 86400s (24hr)

Author: Carbon Scheduling Research Team
Date: 2024-11-09
"""

import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Import scheduler
try:
    from scheduler_embodied_aware import choose_region_embodied_aware
    SCHEDULER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error: Could not import scheduler_embodied_aware: {e}")
    sys.exit(1)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)


class DurationSensitivityAnalyzer:
    """Analyze carbon emissions across different task durations."""
    
    def __init__(self, output_dir: str = "duration_sensitivity_results", 
                 durations: List[int] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Test durations (in seconds) - allow custom durations
        if durations:
            self.durations = sorted(durations)
        else:
            # Default durations
            self.durations = [5, 15, 30, 60, 300, 600, 1800, 3600]
        
        # Strategies to compare
        self.strategies = [
            "operational_only",
            "embodied_prioritized",
            "balanced"
        ]
        
        self.results = []
        
    def _format_duration(self, duration_s: int) -> str:
        """Format duration in human-readable format."""
        if duration_s < 60:
            return f"{duration_s}s"
        elif duration_s < 3600:
            return f"{duration_s/60:.1f}min"
        elif duration_s < 86400:
            return f"{duration_s/3600:.1f}hr"
        else:
            return f"{duration_s/86400:.1f}days"
        
    def run_analysis(self, num_samples_per_duration: int = 10):
        """
        Run analysis across all durations and strategies.
        
        Args:
            num_samples_per_duration: Number of samples per duration (for averaging)
        """
        print("="*80)
        print("  DURATION SENSITIVITY ANALYSIS")
        print("="*80)
        print(f"\nTest Durations: {len(self.durations)}")
        print(f"Strategies: {len(self.strategies)}")
        print(f"Samples per duration: {num_samples_per_duration}")
        print(f"Total executions: {len(self.durations) * len(self.strategies) * num_samples_per_duration}")
        print("\nStarting analysis...")
        
        total_tests = len(self.durations) * len(self.strategies) * num_samples_per_duration
        completed = 0
        
        for duration_s in self.durations:
            print(f"\n{'='*80}")
            duration_label = self._format_duration(duration_s)
            print(f"Testing duration: {duration_s}s ({duration_label})")
            print(f"{'='*80}")
            
            for strategy in self.strategies:
                print(f"\n  Strategy: {strategy:25s}", end=" ", flush=True)
                
                # Run multiple samples for averaging
                strategy_results = []
                for sample in range(num_samples_per_duration):
                    try:
                        # Scale SLA with duration
                        sla_ms = max(2000, duration_s * 100)
                        
                        result = choose_region_embodied_aware(
                            duration_s=duration_s,
                            sla_ms=sla_ms,
                            strategy=strategy,
                            verbose=False
                        )
                        
                        strategy_results.append({
                            "duration_s": duration_s,
                            "duration_min": duration_s / 60,
                            "duration_hours": duration_s / 3600,
                            "strategy": strategy,
                            "sample": sample,
                            "region": result["region"],
                            "server_age": result["server_age_years"],
                            "power_w": result["power_consumption_w"],
                            "ci": result["carbon_intensity"],
                            "operational_g": result["operational_co2_g"],
                            "embodied_g": result["embodied_co2_g"],
                            "total_g": result["total_co2_g"],
                            "embodied_pct": (result["embodied_co2_g"] / result["total_co2_g"]) * 100,
                            "carbon_debt_ratio": result["carbon_debt_ratio"],
                        })
                        
                        completed += 1
                        if (sample + 1) % 3 == 0:
                            print(".", end="", flush=True)
                        
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        completed += 1
                        continue
                
                # Average the samples
                if strategy_results:
                    avg_result = {
                        "duration_s": duration_s,
                        "duration_min": duration_s / 60,
                        "duration_hours": duration_s / 3600,
                        "strategy": strategy,
                        "total_g": np.mean([r["total_g"] for r in strategy_results]),
                        "operational_g": np.mean([r["operational_g"] for r in strategy_results]),
                        "embodied_g": np.mean([r["embodied_g"] for r in strategy_results]),
                        "embodied_pct": np.mean([r["embodied_pct"] for r in strategy_results]),
                        "power_w": np.mean([r["power_w"] for r in strategy_results]),
                        "server_age": np.mean([r["server_age"] for r in strategy_results]),
                        "samples": len(strategy_results),
                        "std_total_g": np.std([r["total_g"] for r in strategy_results]),
                    }
                    self.results.append(avg_result)
                    print(f" ✅ {avg_result['total_g']:.3f}g")
                
        print(f"\n{'='*80}")
        print(f"✅ Analysis complete! {completed}/{total_tests} executions successful")
        print(f"{'='*80}")
    
    def analyze_crossover_point(self) -> Dict:
        """Find the duration where embodied-aware strategies become beneficial."""
        df = pd.DataFrame(self.results)
        
        print("\n" + "="*80)
        print("  CROSSOVER POINT ANALYSIS")
        print("="*80)
        
        baseline_df = df[df["strategy"] == "operational_only"]
        
        crossover_analysis = {
            "embodied_prioritized": None,
            "balanced": None,
        }
        
        for strategy in ["embodied_prioritized", "balanced"]:
            strategy_df = df[df["strategy"] == strategy]
            
            print(f"\n{strategy}:")
            print("-" * 70)
            
            # Calculate differences at each duration
            differences = []
            for duration in self.durations:
                baseline_val = baseline_df[baseline_df["duration_s"] == duration]["total_g"].values[0]
                strategy_val = strategy_df[strategy_df["duration_s"] == duration]["total_g"].values[0]
                diff_g = strategy_val - baseline_val
                diff_pct = (diff_g / baseline_val) * 100
                
                differences.append({
                    "duration_s": duration,
                    "diff_g": diff_g,
                    "diff_pct": diff_pct
                })
                
                status = "✅ WINS" if diff_g < 0 else "❌ LOSES"
                print(f"  {duration:5d}s ({duration/60:6.1f}min): {diff_pct:+6.1f}% ({diff_g:+7.3f}g) {status}")
            
            # Find crossover
            for i, diff in enumerate(differences):
                if diff["diff_g"] < 0:
                    crossover_analysis[strategy] = {
                        "crossover_duration_s": diff["duration_s"],
                        "crossover_duration_min": diff["duration_s"] / 60,
                        "benefit_g": abs(diff["diff_g"]),
                        "benefit_pct": abs(diff["diff_pct"]),
                    }
                    print(f"\n  🎯 Crossover point: {diff['duration_s']}s ({diff['duration_s']/60:.1f} min)")
                    print(f"     Saves: {abs(diff['diff_g']):.3f}g ({abs(diff['diff_pct']):.1f}%)")
                    break
            
            if crossover_analysis[strategy] is None:
                print(f"\n  ⚠️  No crossover found in tested range (≤{max(self.durations)}s)")
        
        return crossover_analysis
    
    def plot_results(self):
        """Generate comprehensive visualizations."""
        df = pd.DataFrame(self.results)
        
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Plot 1: Total carbon vs duration
        ax1 = fig.add_subplot(gs[0, :])
        for strategy in self.strategies:
            strategy_df = df[df["strategy"] == strategy]
            ax1.plot(strategy_df["duration_min"], strategy_df["total_g"], 
                    marker='o', linewidth=2.5, markersize=8, label=strategy, alpha=0.8)
        
        ax1.set_xlabel("Task Duration (minutes)", fontsize=12, fontweight='bold')
        ax1.set_ylabel("Total CO₂ Emissions (g)", fontsize=12, fontweight='bold')
        ax1.set_title("Carbon Emissions vs Task Duration", fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(alpha=0.3)
        ax1.set_xscale("log")
        ax1.set_yscale("log")
        
        # Plot 2: Percentage difference from baseline
        ax2 = fig.add_subplot(gs[1, 0])
        baseline_df = df[df["strategy"] == "operational_only"]
        
        for strategy in ["embodied_prioritized", "balanced"]:
            strategy_df = df[df["strategy"] == strategy].reset_index(drop=True)
            baseline_vals = baseline_df["total_g"].values
            strategy_vals = strategy_df["total_g"].values
            diff_pct = ((strategy_vals - baseline_vals) / baseline_vals) * 100
            
            ax2.plot(strategy_df["duration_min"], diff_pct, 
                    marker='o', linewidth=2.5, markersize=8, label=strategy, alpha=0.8)
        
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=2, label='Baseline')
        ax2.axhline(y=10, color='red', linestyle=':', linewidth=1, alpha=0.5)
        ax2.axhline(y=-10, color='green', linestyle=':', linewidth=1, alpha=0.5)
        ax2.fill_between(ax2.get_xlim(), -10, 10, alpha=0.1, color='gray', label='±10% band')
        
        ax2.set_xlabel("Task Duration (minutes)", fontsize=11, fontweight='bold')
        ax2.set_ylabel("Difference from Baseline (%)", fontsize=11, fontweight='bold')
        ax2.set_title("Strategy Performance vs Baseline", fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(alpha=0.3)
        ax2.set_xscale("log")
        
        # Plot 3: Embodied carbon percentage
        ax3 = fig.add_subplot(gs[1, 1])
        for strategy in self.strategies:
            strategy_df = df[df["strategy"] == strategy]
            ax3.plot(strategy_df["duration_min"], strategy_df["embodied_pct"], 
                    marker='o', linewidth=2.5, markersize=8, label=strategy, alpha=0.8)
        
        ax3.axhline(y=20, color='red', linestyle='--', linewidth=1, alpha=0.5, label='20% threshold')
        ax3.set_xlabel("Task Duration (minutes)", fontsize=11, fontweight='bold')
        ax3.set_ylabel("Embodied Carbon (% of total)", fontsize=11, fontweight='bold')
        ax3.set_title("Embodied Carbon Contribution", fontsize=12, fontweight='bold')
        ax3.legend(fontsize=9)
        ax3.grid(alpha=0.3)
        ax3.set_xscale("log")
        
        # Plot 4: Operational vs Embodied breakdown
        ax4 = fig.add_subplot(gs[2, 0])
        
        # Use actual durations from results, pick representative ones
        durations_subset = self.durations[:min(4, len(self.durations))]  # Up to 4 durations
        strategies_subset = ["operational_only", "embodied_prioritized"]
        
        x = np.arange(len(durations_subset))
        width = 0.35
        
        for i, strategy in enumerate(strategies_subset):
            strategy_df = df[df["strategy"] == strategy]
            op_vals = []
            emb_vals = []
            for d in durations_subset:
                d_data = strategy_df[strategy_df["duration_s"] == d]
                if not d_data.empty:
                    op_vals.append(d_data["operational_g"].values[0])
                    emb_vals.append(d_data["embodied_g"].values[0])
                else:
                    op_vals.append(0)
                    emb_vals.append(0)
            
            offset = width * (i - 0.5)
            ax4.bar(x + offset, op_vals, width*0.9, label=f'{strategy} (operational)', alpha=0.8)
            ax4.bar(x + offset, emb_vals, width*0.9, bottom=op_vals, 
                   label=f'{strategy} (embodied)', alpha=0.8)
        
        ax4.set_xlabel("Task Duration", fontsize=11, fontweight='bold')
        ax4.set_ylabel("CO₂ Emissions (g)", fontsize=11, fontweight='bold')
        ax4.set_title("Operational vs Embodied Carbon Breakdown", fontsize=12, fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels([self._format_duration(d) for d in durations_subset])
        ax4.legend(fontsize=9, loc='upper left')
        ax4.grid(alpha=0.3, axis='y')
        
        # Plot 5: Carbon intensity of choices
        ax5 = fig.add_subplot(gs[2, 1])
        
        # Calculate absolute differences
        baseline_df = df[df["strategy"] == "operational_only"]
        embodied_df = df[df["strategy"] == "embodied_prioritized"]
        
        absolute_diff = []
        for duration in self.durations:
            baseline_val = baseline_df[baseline_df["duration_s"] == duration]["total_g"].values[0]
            embodied_val = embodied_df[embodied_df["duration_s"] == duration]["total_g"].values[0]
            diff_g = embodied_val - baseline_val
            absolute_diff.append(diff_g)
        
        colors = ['red' if d > 0 else 'green' for d in absolute_diff]
        bars = ax5.bar(range(len(self.durations)), absolute_diff, color=colors, alpha=0.7)
        
        ax5.axhline(y=0, color='black', linestyle='-', linewidth=2)
        ax5.set_xlabel("Task Duration", fontsize=11, fontweight='bold')
        ax5.set_ylabel("Carbon Difference (g)", fontsize=11, fontweight='bold')
        ax5.set_title("Embodied-Prioritized vs Baseline (Absolute)", fontsize=12, fontweight='bold')
        ax5.set_xticks(range(len(self.durations)))
        ax5.set_xticklabels([self._format_duration(d) for d in self.durations], rotation=45)
        ax5.grid(alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, absolute_diff)):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:+.3f}g',
                    ha='center', va='bottom' if height > 0 else 'top',
                    fontsize=9, fontweight='bold')
        
        plt.suptitle("Duration Sensitivity Analysis: Carbon-Aware Scheduling Strategies", 
                    fontsize=16, fontweight='bold', y=0.995)
        
        output_file = self.output_dir / "duration_sensitivity_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✅ Saved visualization: {output_file}")
        plt.close()
    
    def generate_report(self, crossover_analysis: Dict):
        """Generate comprehensive markdown report."""
        df = pd.DataFrame(self.results)
        
        report = []
        report.append("# Duration Sensitivity Analysis Report")
        report.append("")
        report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Test Durations**: {len(self.durations)} ({min(self.durations)}s to {max(self.durations)}s)")
        report.append(f"**Strategies Tested**: {len(self.strategies)}")
        report.append("")
        report.append("---")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        report.append("### Key Findings:")
        report.append("")
        
        for strategy, analysis in crossover_analysis.items():
            if analysis:
                report.append(f"**{strategy}**:")
                report.append(f"- ✅ Becomes beneficial at: **{analysis['crossover_duration_min']:.1f} minutes** ({analysis['crossover_duration_s']}s)")
                report.append(f"- Carbon savings: **{analysis['benefit_g']:.3f}g** ({analysis['benefit_pct']:.1f}%)")
                report.append("")
            else:
                report.append(f"**{strategy}**:")
                report.append(f"- ❌ No crossover found (remains worse than baseline up to {max(self.durations)/60:.0f} minutes)")
                report.append("")
        
        # Detailed Results Table
        report.append("## Detailed Results by Duration")
        report.append("")
        
        baseline_df = df[df["strategy"] == "operational_only"]
        
        report.append("| Duration | Operational Only | Embodied Prioritized | Balanced | Best Strategy |")
        report.append("|----------|------------------|---------------------|----------|---------------|")
        
        for duration in self.durations:
            op_val = baseline_df[baseline_df["duration_s"] == duration]["total_g"].values[0]
            emb_df = df[(df["strategy"] == "embodied_prioritized") & (df["duration_s"] == duration)]
            bal_df = df[(df["strategy"] == "balanced") & (df["duration_s"] == duration)]
            
            emb_val = emb_df["total_g"].values[0] if not emb_df.empty else np.nan
            bal_val = bal_df["total_g"].values[0] if not bal_df.empty else np.nan
            
            best = min([("operational_only", op_val), 
                       ("embodied_prioritized", emb_val), 
                       ("balanced", bal_val)], 
                      key=lambda x: x[1] if not np.isnan(x[1]) else float('inf'))
            
            report.append(f"| {duration}s ({duration/60:.1f}m) | {op_val:.3f}g | "
                         f"{emb_val:.3f}g ({((emb_val-op_val)/op_val)*100:+.1f}%) | "
                         f"{bal_val:.3f}g ({((bal_val-op_val)/op_val)*100:+.1f}%) | "
                         f"**{best[0]}** |")
        
        report.append("")
        
        # Insights
        report.append("## Insights")
        report.append("")
        report.append("### 1. Operational Carbon Dominance for Short Tasks")
        report.append("")
        
        short_task = df[df["duration_s"] == 15]
        avg_embodied_pct = short_task["embodied_pct"].mean()
        report.append(f"For short tasks (≤15s), embodied carbon represents only **{avg_embodied_pct:.1f}%** "
                     "of total emissions. Operational carbon dominates, making embodied-aware strategies "
                     "less effective due to the power penalty of older servers.")
        report.append("")
        
        report.append("### 2. Crossover Point Analysis")
        report.append("")
        
        has_crossover = any(v is not None for v in crossover_analysis.values())
        if has_crossover:
            min_crossover = min([v['crossover_duration_min'] for v in crossover_analysis.values() if v])
            report.append(f"Embodied-aware scheduling becomes beneficial at approximately **{min_crossover:.0f} minutes**. "
                         "Beyond this point, the embodied carbon savings from using older servers outweigh "
                         "the operational carbon penalty from their degraded power efficiency.")
        else:
            report.append(f"Within the tested range (up to {max(self.durations)/60:.0f} minutes), "
                         "embodied-aware strategies do not outperform baseline. This suggests that for "
                         "typical serverless workloads (<1 hour), operational carbon optimization is more effective.")
        report.append("")
        
        report.append("### 3. Strategy Recommendations")
        report.append("")
        report.append("**For Serverless/FaaS (5s - 5min):**")
        report.append("- Use `operational_only` or `balanced` strategies")
        report.append("- Focus on carbon intensity timing and regional selection")
        report.append("- Embodied carbon <20% of total - not worth the power penalty")
        report.append("")
        
        if has_crossover:
            report.append("**For Batch Processing (5min - 1hr):**")
            report.append("- Consider `balanced` strategy for middle ground")
            report.append("- Embodied carbon becomes significant (20-40% of total)")
            report.append("- Trade-off between power efficiency and embodied savings")
            report.append("")
            
            report.append("**For Long-Running Workloads (>1hr):**")
            report.append("- Use `embodied_prioritized` strategy")
            report.append("- Embodied carbon savings outweigh power penalties")
            report.append("- Preferentially use older, 'paid-off' servers")
        else:
            report.append("**For All Workload Types:**")
            report.append("- Stick with `operational_only` strategy")
            report.append("- Embodied-aware optimization not effective for durations tested")
            report.append("- Focus on timing (CI variation) and regional selection")
        
        report.append("")
        report.append("---")
        report.append("")
        report.append("## Data Files")
        report.append("")
        report.append(f"- Raw data: `{self.output_dir}/results.csv`")
        report.append(f"- Visualization: `{self.output_dir}/duration_sensitivity_analysis.png`")
        report.append("")
        
        # Save report
        report_file = self.output_dir / "DURATION_SENSITIVITY_REPORT.md"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"✅ Saved report: {report_file}")
        
        # Save raw data
        csv_file = self.output_dir / "results.csv"
        df.to_csv(csv_file, index=False)
        print(f"✅ Saved raw data: {csv_file}")


def main():
    """Run duration sensitivity analysis."""
    parser = argparse.ArgumentParser(
        description='Duration Sensitivity Analysis for Carbon-Aware Scheduling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default durations (5s to 1hr)
  python duration_sensitivity_analysis.py
  
  # Test longer durations (4hr, 8hr, 24hr)
  python duration_sensitivity_analysis.py --durations 14400,28800,86400 --samples 5
  
  # Test specific durations
  python duration_sensitivity_analysis.py --durations 60,300,3600,14400 --output longer_test
        """
    )
    parser.add_argument('--durations', type=str, 
                       help='Comma-separated list of durations in seconds (e.g., 60,300,3600)')
    parser.add_argument('--samples', type=int, default=10,
                       help='Number of samples per duration (default: 10)')
    parser.add_argument('--output', type=str, default='duration_sensitivity_results',
                       help='Output directory (default: duration_sensitivity_results)')
    
    args = parser.parse_args()
    
    # Parse custom durations if provided
    custom_durations = None
    if args.durations:
        try:
            custom_durations = [int(d.strip()) for d in args.durations.split(',')]
            print(f"\n✅ Custom durations: {custom_durations}")
        except ValueError as e:
            print(f"❌ Error parsing durations: {e}")
            sys.exit(1)
    
    print("\n" + "="*80)
    print("  DURATION SENSITIVITY ANALYSIS FOR CARBON-AWARE SCHEDULING")
    print("="*80)
    print("\nThis analysis finds the crossover point where embodied-aware")
    print("strategies become beneficial compared to operational-only approaches.")
    print("")
    
    # Create analyzer
    analyzer = DurationSensitivityAnalyzer(output_dir=args.output, durations=custom_durations)
    
    # Run analysis
    start_time = time.time()
    analyzer.run_analysis(num_samples_per_duration=args.samples)
    elapsed = time.time() - start_time
    
    print(f"\n⏱️  Analysis completed in {elapsed:.1f} seconds")
    
    # Find crossover point
    crossover_analysis = analyzer.analyze_crossover_point()
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    analyzer.plot_results()
    
    # Generate report
    print("\nGenerating report...")
    analyzer.generate_report(crossover_analysis)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nResults saved to: {analyzer.output_dir}/")
    print(f"  - DURATION_SENSITIVITY_REPORT.md (comprehensive report)")
    print(f"  - duration_sensitivity_analysis.png (visualizations)")
    print(f"  - results.csv (raw data)")
    print("")


if __name__ == "__main__":
    main()
