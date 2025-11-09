#!/usr/bin/env python3
"""
Boundary Condition Tests for Impossibility Theorem
===================================================

Tests Corollary 1: Embodied-aware strategies can win in clean grids (CI < 200 gCO₂/kWh)
and with reduced hardware aging (degradation < 25%/year).

This validates that the impossibility theorem has correct scope - it applies to
typical cloud conditions but not to all possible scenarios.

Author: Carbon Scheduling Research Team
Date: 2024-11-09
"""

import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Import scheduler with temporary overrides
from scheduler_embodied_aware import (
    choose_region_embodied_aware,
    calculate_total_carbon,
    calculate_power_consumption,
    calculate_carbon_debt_ratio,
    BASE_POWER_W,
    SERVER_SPECS,
    EFFICIENCY_DEGRADATION_RATE
)
import estimator

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)


class BoundaryTester:
    """Test boundary conditions where embodied-aware strategies might win."""
    
    def __init__(self, output_dir: str = "boundary_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def test_clean_grid(self, carbon_intensities: List[int], 
                       num_tasks: int = 500,
                       durations: List[int] = None) -> pd.DataFrame:
        """
        Test if embodied-aware wins in clean grids (low carbon intensity).
        
        Hypothesis: In regions with CI < 200 gCO₂/kWh (Norway, Iceland, Quebec),
        the operational penalty is smaller, allowing embodied savings to dominate.
        
        Args:
            carbon_intensities: List of CI values to test (e.g., [50, 100, 200, 535])
            num_tasks: Number of tasks per CI value
            durations: Task durations in seconds (default: [3600, 14400])
            
        Returns:
            DataFrame with results showing where embodied-aware wins
        """
        if durations is None:
            durations = [3600, 14400]  # 1hr, 4hr
            
        print("\n" + "="*80)
        print("  TEST 1: CLEAN GRID SCENARIO")
        print("="*80)
        print(f"\nHypothesis: Embodied-aware wins when CI < 200 gCO₂/kWh")
        print(f"Testing CI values: {carbon_intensities}")
        print(f"Tasks per CI: {num_tasks}")
        print(f"Durations: {durations}s")
        
        # Store original CI function
        original_get_ci = estimator.get_live_ci
        
        results = []
        
        for ci in carbon_intensities:
            print(f"\n{'='*80}")
            print(f"Testing CI = {ci} gCO₂/kWh")
            print(f"{'='*80}")
            
            # Override CI function to return fixed value
            def mock_ci(region):
                return ci
            
            estimator.get_live_ci = mock_ci
            
            for duration_s in durations:
                print(f"\n  Duration: {duration_s}s ({duration_s/3600:.1f}hr)")
                
                # Test both strategies
                for strategy in ["operational_only", "embodied_prioritized"]:
                    strategy_results = []
                    
                    for i in range(num_tasks):
                        try:
                            result = choose_region_embodied_aware(
                                duration_s=duration_s,
                                sla_ms=max(2000, duration_s * 100),
                                strategy=strategy,
                                verbose=False
                            )
                            
                            strategy_results.append({
                                "ci": ci,
                                "duration_s": duration_s,
                                "duration_hr": duration_s / 3600,
                                "strategy": strategy,
                                "task_id": i,
                                "total_g": result["total_co2_g"],
                                "operational_g": result["operational_co2_g"],
                                "embodied_g": result["embodied_co2_g"],
                                "power_w": result["power_consumption_w"],
                                "server_age": result["server_age_years"],
                            })
                            
                        except Exception as e:
                            print(f"    ❌ Error task {i}: {e}")
                            continue
                    
                    # Calculate statistics
                    if strategy_results:
                        avg_total = np.mean([r["total_g"] for r in strategy_results])
                        std_total = np.std([r["total_g"] for r in strategy_results])
                        
                        print(f"    {strategy:25s}: {avg_total:.3f}g ± {std_total:.3f}g")
                        
                        results.extend(strategy_results)
                
                # Calculate and display penalty
                df_temp = pd.DataFrame(results)
                if len(df_temp) > 0:
                    df_ci_dur = df_temp[(df_temp["ci"] == ci) & (df_temp["duration_s"] == duration_s)]
                    
                    if len(df_ci_dur) > 0:
                        op_only = df_ci_dur[df_ci_dur["strategy"] == "operational_only"]["total_g"].mean()
                        emb_prio = df_ci_dur[df_ci_dur["strategy"] == "embodied_prioritized"]["total_g"].mean()
                        
                        if op_only > 0:
                            penalty_pct = ((emb_prio - op_only) / op_only) * 100
                            
                            if penalty_pct < 0:
                                print(f"    ✅ Embodied-aware WINS by {-penalty_pct:.1f}%!")
                            else:
                                print(f"    ❌ Embodied-aware loses by {penalty_pct:.1f}%")
        
        # Restore original function
        estimator.get_live_ci = original_get_ci
        
        df = pd.DataFrame(results)
        
        # Save results
        output_file = self.output_dir / "clean_grid_results.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved: {output_file}")
        
        # Generate summary
        self._summarize_clean_grid(df, carbon_intensities)
        
        return df
    
    def test_reduced_aging(self, degradation_rates: List[float],
                          num_tasks: int = 500,
                          duration_s: int = 14400) -> pd.DataFrame:
        """
        Test if embodied-aware wins with reduced hardware aging.
        
        Hypothesis: If servers age more slowly (degradation < 25%/year),
        the operational penalty is smaller, potentially allowing embodied-aware to win.
        
        Args:
            degradation_rates: Aging rates to test (e.g., [0.05, 0.10, 0.15, 0.20, 0.25])
            num_tasks: Number of tasks per rate
            duration_s: Task duration in seconds
            
        Returns:
            DataFrame showing aging threshold where embodied-aware wins
        """
        print("\n" + "="*80)
        print("  TEST 2: REDUCED AGING SCENARIO")
        print("="*80)
        print(f"\nHypothesis: Embodied-aware wins when aging < 25%/year")
        print(f"Testing degradation rates: {[f'{r*100:.0f}%' for r in degradation_rates]}")
        print(f"Tasks per rate: {num_tasks}")
        print(f"Duration: {duration_s}s ({duration_s/3600:.1f}hr)")
        
        results = []
        
        for rate in degradation_rates:
            print(f"\n{'='*80}")
            print(f"Testing degradation = {rate*100:.0f}%/year")
            print(f"{'='*80}")
            
            # Calculate expected power for old servers with this rate
            new_power = calculate_power_consumption(BASE_POWER_W, 0.5, alpha=rate)
            old_power = calculate_power_consumption(BASE_POWER_W, 4.0, alpha=rate)
            power_penalty = old_power - new_power
            
            print(f"  New server power: {new_power:.1f}W")
            print(f"  Old server power: {old_power:.1f}W")
            print(f"  Power penalty: +{power_penalty:.1f}W (+{(power_penalty/new_power)*100:.1f}%)")
            
            # Calculate carbon manually with this degradation rate
            ci = 535  # Use typical CI
            
            # New server
            op_new, emb_new, total_new = calculate_total_carbon("new", duration_s, ci)
            # Recalculate operational with custom rate
            energy_new = (new_power * duration_s / 3600) / 1000  # kWh
            op_new_custom = energy_new * ci * 1.2  # PUE
            total_new_custom = op_new_custom + emb_new
            
            # Old server
            op_old, emb_old, total_old = calculate_total_carbon("old", duration_s, ci)
            # Recalculate operational with custom rate
            energy_old = (old_power * duration_s / 3600) / 1000  # kWh
            op_old_custom = energy_old * ci * 1.2  # PUE
            total_old_custom = op_old_custom + emb_old
            
            # Calculate penalty
            penalty_g = total_old_custom - total_new_custom
            penalty_pct = (penalty_g / total_new_custom) * 100
            
            # Operational penalty and embodied savings
            op_penalty = op_old_custom - op_new_custom
            emb_savings = emb_new - emb_old
            
            print(f"\n  Operational penalty: {op_penalty:.2f}g")
            print(f"  Embodied savings: {emb_savings:.2f}g")
            print(f"  Net penalty: {penalty_g:.2f}g ({penalty_pct:+.1f}%)")
            
            if penalty_pct < 0:
                print(f"  ✅ Embodied-aware WINS by {-penalty_pct:.1f}%!")
            else:
                print(f"  ❌ Embodied-aware loses by {penalty_pct:.1f}%")
            
            results.append({
                "degradation_rate": rate,
                "degradation_pct": rate * 100,
                "new_power_w": new_power,
                "old_power_w": old_power,
                "power_penalty_w": power_penalty,
                "power_penalty_pct": (power_penalty / new_power) * 100,
                "operational_penalty_g": op_penalty,
                "embodied_savings_g": emb_savings,
                "net_penalty_g": penalty_g,
                "penalty_pct": penalty_pct,
                "embodied_wins": penalty_pct < 0,
                "duration_s": duration_s,
                "ci": ci,
                "total_new_g": total_new_custom,
                "total_old_g": total_old_custom,
            })
        
        df = pd.DataFrame(results)
        
        # Save results
        output_file = self.output_dir / "reduced_aging_results.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved: {output_file}")
        
        # Find threshold
        self._summarize_reduced_aging(df)
        
        return df
    
    def test_combined_boundaries(self, 
                                ci_range: List[int],
                                aging_range: List[float],
                                duration_s: int = 14400) -> pd.DataFrame:
        """
        Test combined effect of CI and aging to create boundary heatmap.
        
        Args:
            ci_range: Carbon intensity values to test
            aging_range: Degradation rates to test
            duration_s: Task duration
            
        Returns:
            DataFrame suitable for heatmap visualization
        """
        print("\n" + "="*80)
        print("  TEST 3: COMBINED BOUNDARY ANALYSIS")
        print("="*80)
        print(f"\nTesting {len(ci_range)} CI values × {len(aging_range)} aging rates")
        print(f"Total: {len(ci_range) * len(aging_range)} combinations")
        
        results = []
        
        for ci in ci_range:
            for rate in aging_range:
                # Calculate with this CI and aging rate
                new_power = calculate_power_consumption(BASE_POWER_W, 0.5, alpha=rate)
                old_power = calculate_power_consumption(BASE_POWER_W, 4.0, alpha=rate)
                
                # Operational carbon
                energy_new = (new_power * duration_s / 3600) / 1000
                energy_old = (old_power * duration_s / 3600) / 1000
                op_new = energy_new * ci * 1.2
                op_old = energy_old * ci * 1.2
                
                # Embodied carbon (unchanged by CI or aging)
                _, emb_new, _ = calculate_total_carbon("new", duration_s, 535)
                _, emb_old, _ = calculate_total_carbon("old", duration_s, 535)
                
                total_new = op_new + emb_new
                total_old = op_old + emb_old
                
                penalty_pct = ((total_old - total_new) / total_new) * 100
                
                results.append({
                    "ci": ci,
                    "degradation_rate": rate,
                    "degradation_pct": rate * 100,
                    "penalty_pct": penalty_pct,
                    "embodied_wins": penalty_pct < 0,
                    "total_new_g": total_new,
                    "total_old_g": total_old,
                })
        
        df = pd.DataFrame(results)
        
        # Save results
        output_file = self.output_dir / "combined_boundary_results.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Results saved: {output_file}")
        
        # Generate heatmap
        self._plot_boundary_heatmap(df, ci_range, aging_range)
        
        return df
    
    def _summarize_clean_grid(self, df: pd.DataFrame, ci_values: List[int]):
        """Generate summary analysis for clean grid tests."""
        print("\n" + "="*80)
        print("  CLEAN GRID TEST SUMMARY")
        print("="*80)
        
        summary = []
        
        for ci in ci_values:
            df_ci = df[df["ci"] == ci]
            
            for duration_s in df_ci["duration_s"].unique():
                df_ci_dur = df_ci[df_ci["duration_s"] == duration_s]
                
                op_only = df_ci_dur[df_ci_dur["strategy"] == "operational_only"]["total_g"].mean()
                emb_prio = df_ci_dur[df_ci_dur["strategy"] == "embodied_prioritized"]["total_g"].mean()
                
                penalty_pct = ((emb_prio - op_only) / op_only) * 100
                
                summary.append({
                    "ci": ci,
                    "duration_hr": duration_s / 3600,
                    "operational_only_g": op_only,
                    "embodied_prioritized_g": emb_prio,
                    "penalty_pct": penalty_pct,
                    "embodied_wins": penalty_pct < 0,
                })
        
        summary_df = pd.DataFrame(summary)
        
        # Display table
        print(f"\n{'CI':>6s} {'Duration':>10s} {'Op-Only':>12s} {'Emb-Prio':>12s} {'Penalty':>10s} {'Winner':>15s}")
        print("-" * 70)
        
        for _, row in summary_df.iterrows():
            winner = "Embodied ✅" if row["embodied_wins"] else "Operational ✅"
            print(f"{row['ci']:>6.0f} {row['duration_hr']:>10.1f}hr {row['operational_only_g']:>12.2f}g "
                  f"{row['embodied_prioritized_g']:>12.2f}g {row['penalty_pct']:>9.1f}% {winner:>15s}")
        
        # Find threshold
        winning_scenarios = summary_df[summary_df["embodied_wins"]]
        
        if len(winning_scenarios) > 0:
            max_ci_win = winning_scenarios["ci"].max()
            print(f"\n🎯 BOUNDARY FOUND: Embodied-aware wins when CI ≤ {max_ci_win} gCO₂/kWh")
        else:
            print(f"\n⚠️  Embodied-aware never wins in tested CI range ({min(ci_values)}-{max(ci_values)})")
            print(f"   Need to test lower CI values (e.g., <{min(ci_values)})")
        
        # Save summary
        summary_df.to_csv(self.output_dir / "clean_grid_summary.csv", index=False)
    
    def _summarize_reduced_aging(self, df: pd.DataFrame):
        """Generate summary for reduced aging tests."""
        print("\n" + "="*80)
        print("  REDUCED AGING TEST SUMMARY")
        print("="*80)
        
        print(f"\n{'Aging':>10s} {'Power Δ':>10s} {'Op Penalty':>12s} {'Emb Savings':>12s} {'Net':>10s} {'Winner':>15s}")
        print("-" * 75)
        
        for _, row in df.iterrows():
            winner = "Embodied ✅" if row["embodied_wins"] else "Operational ✅"
            print(f"{row['degradation_pct']:>9.0f}% {row['power_penalty_w']:>9.1f}W "
                  f"{row['operational_penalty_g']:>11.2f}g {row['embodied_savings_g']:>11.2f}g "
                  f"{row['penalty_pct']:>9.1f}% {winner:>15s}")
        
        # Find threshold
        winning = df[df["embodied_wins"]]
        
        if len(winning) > 0:
            max_rate = winning["degradation_pct"].max()
            print(f"\n🎯 BOUNDARY FOUND: Embodied-aware wins when aging ≤ {max_rate:.0f}%/year")
        else:
            min_tested = df["degradation_pct"].min()
            print(f"\n⚠️  Embodied-aware never wins even at {min_tested:.0f}%/year aging")
            print(f"   Current model: operational penalty always exceeds embodied savings")
    
    def _plot_boundary_heatmap(self, df: pd.DataFrame, ci_range: List[int], aging_range: List[float]):
        """Create heatmap showing where embodied-aware wins."""
        # Pivot for heatmap
        heatmap_data = df.pivot(index="degradation_pct", columns="ci", values="penalty_pct")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create heatmap
        sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdYlGn_r", 
                   center=0, vmin=-20, vmax=20, cbar_kws={"label": "Penalty %"},
                   ax=ax)
        
        ax.set_title("Embodied-Aware Strategy Performance\nBoundary Conditions Heatmap", 
                    fontsize=14, fontweight="bold")
        ax.set_xlabel("Carbon Intensity (gCO₂/kWh)", fontsize=12)
        ax.set_ylabel("Hardware Aging Rate (%/year)", fontsize=12)
        
        # Add legend
        ax.text(0.02, 0.98, "Green = Embodied-aware wins\nRed = Operational-only wins",
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        output_file = self.output_dir / "boundary_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✅ Heatmap saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Boundary condition tests for impossibility theorem")
    parser.add_argument("--scenario", choices=["clean_grid", "reduced_aging", "combined", "all"],
                       default="all", help="Which boundary test to run")
    parser.add_argument("--ci", type=str, default="50,100,200,535",
                       help="Comma-separated carbon intensities for clean grid test")
    parser.add_argument("--degradation", type=str, default="0.05,0.10,0.15,0.20,0.25,0.30",
                       help="Comma-separated degradation rates for aging test")
    parser.add_argument("--tasks", type=int, default=500,
                       help="Number of tasks per test")
    parser.add_argument("--duration", type=int, default=14400,
                       help="Task duration in seconds (default: 4hr)")
    parser.add_argument("--output", type=str, default="boundary_tests",
                       help="Output directory")
    
    args = parser.parse_args()
    
    # Parse lists
    ci_values = [int(x) for x in args.ci.split(",")]
    aging_rates = [float(x) for x in args.degradation.split(",")]
    
    tester = BoundaryTester(output_dir=args.output)
    
    if args.scenario in ["clean_grid", "all"]:
        print("\n" + "🔬" * 40)
        print("STARTING CLEAN GRID BOUNDARY TEST")
        print("🔬" * 40)
        tester.test_clean_grid(ci_values, num_tasks=args.tasks, durations=[3600, args.duration])
    
    if args.scenario in ["reduced_aging", "all"]:
        print("\n" + "🔬" * 40)
        print("STARTING REDUCED AGING BOUNDARY TEST")
        print("🔬" * 40)
        tester.test_reduced_aging(aging_rates, num_tasks=args.tasks, duration_s=args.duration)
    
    if args.scenario in ["combined", "all"]:
        print("\n" + "🔬" * 40)
        print("STARTING COMBINED BOUNDARY ANALYSIS")
        print("🔬" * 40)
        tester.test_combined_boundaries(ci_values, aging_rates, duration_s=args.duration)
    
    print("\n" + "="*80)
    print("  ✅ ALL BOUNDARY TESTS COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {args.output}/")


if __name__ == "__main__":
    main()
