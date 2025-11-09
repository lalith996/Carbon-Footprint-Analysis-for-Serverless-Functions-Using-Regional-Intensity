"""
experiments_large_scale.py
==========================
Comprehensive large-scale experiment framework for carbon scheduling validation.
Generates 1000+ realistic serverless workloads and compares scheduling strategies.

Based on research patterns from:
- Azure Functions traces (Shahrad et al., 2020)
- Google Cloud Functions traces (Wang et al., 2021)
- Serverless workload characterization (Eismann et al., 2020)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import os
import sys
import time
import argparse
from scipy import stats
from scipy.stats import ttest_ind, mannwhitneyu

# Your existing modules
from estimator import estimate_co2, get_live_ci
from scheduler import choose_region
from scheduler_using_lr import choose_region_with_lr
from scheduler_embodied_aware import choose_region_embodied_aware

# Progress bar
try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm for progress bars...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm


# =============================================================================
# WORKLOAD GENERATION
# =============================================================================

class WorkloadGenerator:
    """
    Generate realistic serverless workloads based on research patterns.
    """
    
    # Workload pattern distributions from research
    PATTERNS = {
        "constant": 0.15,      # 15% steady load
        "sinusoidal": 0.25,    # 25% daily cycles
        "bursty": 0.20,        # 20% spike patterns
        "mean_adjacent": 0.30, # 30% gradual variations
        "idle_pulse": 0.10,    # 10% idle with bursts
    }
    
    # Duration distribution (seconds)
    DURATION_RANGES = {
        "micro": (0.1, 1.0, 0.80),      # 80% < 1 second
        "short": (1.0, 60.0, 0.15),     # 15% 1-60 seconds
        "long": (60.0, 600.0, 0.05),    # 5% > 1 minute (capped at 10 min)
    }
    
    # Workload types with carbon characteristics
    WORKLOAD_TYPES = {
        "api_request": {
            "duration_range": "micro",
            "cpu_intensity": 0.3,  # Low CPU
            "memory_gb": 0.5,
            "sla_latency_ms": 500,
            "frequency": 0.40,  # 40% of workloads
        },
        "data_processing": {
            "duration_range": "short",
            "cpu_intensity": 0.8,  # High CPU
            "memory_gb": 2.0,
            "sla_latency_ms": 5000,
            "frequency": 0.30,
        },
        "ml_inference": {
            "duration_range": "short",
            "cpu_intensity": 0.9,
            "memory_gb": 4.0,
            "sla_latency_ms": 2000,
            "frequency": 0.15,
        },
        "scheduled_job": {
            "duration_range": "long",
            "cpu_intensity": 0.5,
            "memory_gb": 1.0,
            "sla_latency_ms": 30000,  # More flexible
            "frequency": 0.10,
        },
        "batch_analytics": {
            "duration_range": "long",
            "cpu_intensity": 0.7,
            "memory_gb": 3.0,
            "sla_latency_ms": 60000,  # Very flexible
            "frequency": 0.05,
        },
    }
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility."""
        np.random.seed(seed)
        self.seed = seed
    
    def generate_duration(self, workload_type: str) -> float:
        """Generate realistic duration based on workload type."""
        duration_range = self.WORKLOAD_TYPES[workload_type]["duration_range"]
        min_dur, max_dur, _ = self.DURATION_RANGES[duration_range]
        
        # Log-normal distribution (more realistic than uniform)
        # Most tasks short, few tasks long
        mu = np.log(min_dur + (max_dur - min_dur) * 0.3)
        sigma = 0.8
        duration = np.random.lognormal(mu, sigma)
        
        # Clip to range
        return np.clip(duration, min_dur, max_dur)
    
    def generate_workload_type(self) -> str:
        """Select workload type based on frequency distribution."""
        types = list(self.WORKLOAD_TYPES.keys())
        frequencies = [self.WORKLOAD_TYPES[t]["frequency"] for t in types]
        return np.random.choice(types, p=frequencies)
    
    def generate_arrival_pattern(self, 
                                  num_tasks: int,
                                  duration_hours: float = 24) -> np.ndarray:
        """
        Generate realistic arrival times over a period.
        
        Args:
            num_tasks: Total number of tasks to generate
            duration_hours: Time period (default: 24 hours)
            
        Returns:
            Array of arrival times (hours from start)
        """
        # Select pattern
        pattern = np.random.choice(
            list(self.PATTERNS.keys()),
            p=list(self.PATTERNS.values())
        )
        
        if pattern == "constant":
            # Uniform distribution with slight noise
            arrivals = np.linspace(0, duration_hours, num_tasks)
            arrivals += np.random.normal(0, 0.1, num_tasks)
            
        elif pattern == "sinusoidal":
            # Daily cycle: low at night, peak during day
            base_times = np.linspace(0, duration_hours, num_tasks)
            # Peak at 12 hours (noon), low at 0/24 (midnight)
            intensity = 0.5 + 0.5 * np.sin(2 * np.pi * base_times / 24 - np.pi/2)
            # Non-homogeneous Poisson process
            arrivals = []
            for i, t in enumerate(base_times):
                if np.random.random() < intensity[i]:
                    arrivals.append(t + np.random.uniform(-0.5, 0.5))
            arrivals = np.array(arrivals) if arrivals else base_times[:num_tasks]
            
        elif pattern == "bursty":
            # Multiple bursts throughout the period
            num_bursts = max(3, num_tasks // 100)
            burst_times = np.random.uniform(0, duration_hours, num_bursts)
            
            arrivals = []
            tasks_per_burst = num_tasks // num_bursts
            for burst_time in burst_times:
                # Exponential inter-arrival within burst
                burst_arrivals = burst_time + np.random.exponential(0.01, tasks_per_burst)
                arrivals.extend(burst_arrivals)
            arrivals = np.array(arrivals[:num_tasks])
            
        elif pattern == "mean_adjacent":
            # Clustered around mean with gradual drift
            mean_time = duration_hours / 2
            arrivals = np.random.normal(mean_time, duration_hours/6, num_tasks)
            
        else:  # idle_pulse
            # Long idle periods with occasional pulses
            idle_fraction = 0.7
            active_hours = duration_hours * (1 - idle_fraction)
            arrivals = np.random.uniform(0, active_hours, num_tasks)
            # Shift to distributed idle periods
            arrivals = np.sort(arrivals)
            arrivals = arrivals * (duration_hours / active_hours)
        
        # Ensure within bounds and sort
        arrivals = np.clip(arrivals, 0, duration_hours)
        arrivals = np.sort(arrivals)
        
        # Ensure we have correct number
        if len(arrivals) < num_tasks:
            # Pad with uniform distribution
            extra = num_tasks - len(arrivals)
            extra_arrivals = np.random.uniform(0, duration_hours, extra)
            arrivals = np.concatenate([arrivals, extra_arrivals])
            arrivals = np.sort(arrivals)
        
        return arrivals[:num_tasks]
    
    def generate_task_batch(self, 
                            num_tasks: int,
                            start_time: datetime,
                            duration_hours: float = 24) -> pd.DataFrame:
        """
        Generate a batch of realistic tasks.
        
        Args:
            num_tasks: Number of tasks to generate
            start_time: Experiment start time
            duration_hours: Time period
            
        Returns:
            DataFrame with task specifications
        """
        # Generate arrival times
        arrival_hours = self.generate_arrival_pattern(num_tasks, duration_hours)
        
        tasks = []
        for i, arrival_hour in enumerate(arrival_hours):
            # Select workload type
            workload_type = self.generate_workload_type()
            workload_spec = self.WORKLOAD_TYPES[workload_type]
            
            # Generate task
            task = {
                "task_id": f"task_{i:06d}",
                "arrival_time": start_time + timedelta(hours=float(arrival_hour)),
                "workload_type": workload_type,
                "duration_seconds": self.generate_duration(workload_type),
                "cpu_intensity": workload_spec["cpu_intensity"],
                "memory_gb": workload_spec["memory_gb"],
                "sla_latency_ms": workload_spec["sla_latency_ms"],
            }
            
            tasks.append(task)
        
        return pd.DataFrame(tasks)


# =============================================================================
# EXPERIMENT EXECUTION ENGINE
# =============================================================================

class ExperimentRunner:
    """
    Execute experiments comparing different scheduling strategies.
    """
    
    STRATEGIES = {
        "baseline": "Fixed region (Northern), no carbon awareness",
        "reactive": "Live carbon intensity-based scheduling",
        "predictive_lr": "ML-predicted carbon intensity scheduling",
        "embodied_prioritized": "Aggressive old-server prioritization",
        "balanced": "Balanced operational + embodied optimization",
        "operational_only": "New servers, ignores embodied carbon",
    }
    
    def __init__(self, output_dir: str = "experiment_results_large"):
        """
        Initialize experiment runner.
        
        Args:
            output_dir: Directory for saving results
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # CI cache to reduce API calls
        self.ci_cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_cached_ci(self, region: str) -> float:
        """Get carbon intensity with caching."""
        cache_key = f"{region}_{int(time.time() / self.cache_duration)}"
        
        if cache_key not in self.ci_cache:
            try:
                ci_result = get_live_ci(region)
                if ci_result:
                    self.ci_cache[cache_key] = ci_result[0]
                else:
                    # Fallback to reasonable defaults
                    defaults = {"Northern": 533, "Western": 677, "Southern": 547, "Eastern": 748}
                    self.ci_cache[cache_key] = defaults.get(region, 600)
            except Exception:
                defaults = {"Northern": 533, "Western": 677, "Southern": 547, "Eastern": 748}
                self.ci_cache[cache_key] = defaults.get(region, 600)
        
        return self.ci_cache[cache_key]
    
    def execute_single_task(self,
                            task: Dict,
                            strategy: str,
                            current_time: datetime) -> Dict:
        """
        Execute a single task using specified strategy.
        
        Args:
            task: Task specification dictionary
            strategy: Scheduling strategy name
            current_time: Current simulation time
            
        Returns:
            Dictionary with execution results
        """
        duration_s = task["duration_seconds"]
        sla_latency = task["sla_latency_ms"]
        
        # Execute based on strategy
        if strategy == "baseline":
            # Fixed Northern region
            region = "Northern"
            _, co2_g = estimate_co2(duration_s, region)
            ci = self.get_cached_ci(region)
            
            result = {
                "region": region,
                "server_age": "medium",
                "server_age_years": 2.0,
                "operational_co2_g": co2_g,
                "embodied_co2_g": 0.0,  # Not tracked in baseline
                "total_co2_g": co2_g,
                "latency_ms": 70,
                "sla_met": True,
                "carbon_intensity": ci,
                "carbon_debt_ratio": 0.5,
                "power_w": 93.6,
            }
            
        elif strategy == "reactive":
            # Use existing reactive scheduler
            try:
                reactive_result = choose_region(duration_s, sla_latency)
                region = reactive_result["region"]
                ci = self.get_cached_ci(region)
                
                result = {
                    "region": region,
                    "server_age": "medium",
                    "server_age_years": 2.0,
                    "operational_co2_g": reactive_result["co2_g"],
                    "embodied_co2_g": 0.0,  # Not tracked
                    "total_co2_g": reactive_result["co2_g"],
                    "latency_ms": reactive_result["latency_ms"],
                    "sla_met": reactive_result["latency_ms"] <= sla_latency,
                    "carbon_intensity": ci,
                    "carbon_debt_ratio": 0.5,
                    "power_w": 93.6,
                }
            except Exception as e:
                # Fallback to baseline
                return self.execute_single_task(task, "baseline", current_time)
            
        elif strategy == "predictive_lr":
            # Use ML-based predictive scheduler
            try:
                pred_result = choose_region_with_lr(duration_s, sla_latency)
                region = pred_result["region"]
                ci = self.get_cached_ci(region)
                
                result = {
                    "region": region,
                    "server_age": "medium",
                    "server_age_years": 2.0,
                    "operational_co2_g": pred_result["co2_g"],
                    "embodied_co2_g": 0.0,
                    "total_co2_g": pred_result["co2_g"],
                    "latency_ms": pred_result["latency_ms"],
                    "sla_met": pred_result["latency_ms"] <= sla_latency,
                    "carbon_intensity": ci,
                    "carbon_debt_ratio": 0.5,
                    "power_w": 93.6,
                }
            except Exception as e:
                # Fallback to reactive
                return self.execute_single_task(task, "reactive", current_time)
        
        elif strategy in ["embodied_prioritized", "balanced", "operational_only"]:
            # Use embodied-aware scheduler
            try:
                lc_result = choose_region_embodied_aware(
                    duration_s=duration_s,
                    sla_ms=sla_latency,
                    strategy=strategy,
                    verbose=False
                )
                
                result = {
                    "region": lc_result["region"],
                    "server_age": lc_result["server_age"],
                    "server_age_years": lc_result["server_age_years"],
                    "operational_co2_g": lc_result["operational_co2_g"],
                    "embodied_co2_g": lc_result["embodied_co2_g"],
                    "total_co2_g": lc_result["total_co2_g"],
                    "latency_ms": lc_result["latency_ms"],
                    "sla_met": lc_result["latency_ms"] <= sla_latency,
                    "carbon_intensity": lc_result["carbon_intensity"],
                    "carbon_debt_ratio": lc_result["carbon_debt_ratio"],
                    "power_w": lc_result["power_consumption_w"],
                }
            except Exception as e:
                print(f"⚠️  Lifecycle scheduler failed: {e}, using baseline")
                return self.execute_single_task(task, "baseline", current_time)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Add common fields
        result.update({
            "task_id": task["task_id"],
            "strategy": strategy,
            "workload_type": task["workload_type"],
            "duration_seconds": duration_s,
            "execution_time": current_time.isoformat(),
        })
        
        return result
    
    def run_experiment(self,
                       tasks_df: pd.DataFrame,
                       strategies: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Run complete experiment with all tasks and strategies.
        
        Args:
            tasks_df: DataFrame with task specifications
            strategies: List of strategies to test (None = all)
            
        Returns:
            DataFrame with all results
        """
        if strategies is None:
            strategies = list(self.STRATEGIES.keys())
        
        print(f"\n{'='*80}")
        print(f"RUNNING EXPERIMENT: {len(tasks_df)} tasks × {len(strategies)} strategies")
        print(f"Total executions: {len(tasks_df) * len(strategies)}")
        print(f"{'='*80}\n")
        
        all_results = []
        
        for strategy in strategies:
            print(f"\n📊 Strategy: {strategy}")
            print(f"   Description: {self.STRATEGIES[strategy]}")
            
            # Execute all tasks for this strategy
            strategy_results = []
            
            # Use tqdm for progress bar
            for idx, task in tqdm(tasks_df.iterrows(), 
                                   total=len(tasks_df),
                                   desc=f"   {strategy:20s}",
                                   ncols=100):
                try:
                    result = self.execute_single_task(
                        task.to_dict(),
                        strategy,
                        task["arrival_time"]
                    )
                    strategy_results.append(result)
                    
                except Exception as e:
                    print(f"\n   ⚠️  Error on task {task['task_id']}: {e}")
                    continue
            
            all_results.extend(strategy_results)
            
            # Save intermediate results
            if strategy_results:
                temp_df = pd.DataFrame(strategy_results)
                temp_file = os.path.join(self.output_dir, f"results_{strategy}.csv")
                temp_df.to_csv(temp_file, index=False)
                
                # Print quick stats
                avg_co2 = temp_df["total_co2_g"].mean()
                sla_rate = temp_df["sla_met"].mean() * 100
                print(f"   ✅ Avg CO₂: {avg_co2:.6f}g | SLA: {sla_rate:.1f}% | Saved: {temp_file}")
        
        # Combine all results
        results_df = pd.DataFrame(all_results)
        
        # Save complete results
        output_file = os.path.join(self.output_dir, "results_complete.csv")
        results_df.to_csv(output_file, index=False)
        print(f"\n✅ Complete results saved: {output_file}")
        
        return results_df


# =============================================================================
# STATISTICAL ANALYSIS
# =============================================================================

class StatisticalValidator:
    """Perform statistical tests on experiment results."""
    
    @staticmethod
    def compare_strategies(results_df: pd.DataFrame, 
                          strategy1: str, 
                          strategy2: str,
                          metric: str = "total_co2_g") -> Dict:
        """
        Compare two strategies statistically.
        
        Returns:
            Dictionary with test results and interpretation
        """
        data1 = results_df[results_df["strategy"] == strategy1][metric].dropna()
        data2 = results_df[results_df["strategy"] == strategy2][metric].dropna()
        
        if len(data1) == 0 or len(data2) == 0:
            return {"error": "Insufficient data"}
        
        # T-test (parametric)
        t_stat, t_pval = ttest_ind(data1, data2)
        
        # Mann-Whitney U (non-parametric)
        u_stat, u_pval = mannwhitneyu(data1, data2, alternative='two-sided')
        
        # Effect size (Cohen's d)
        mean1, mean2 = data1.mean(), data2.mean()
        std1, std2 = data1.std(), data2.std()
        pooled_std = np.sqrt((std1**2 + std2**2) / 2)
        cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        
        # Interpretation
        significant = t_pval < 0.05
        effect_size_interpretation = (
            "large" if abs(cohens_d) > 0.8 else
            "medium" if abs(cohens_d) > 0.5 else
            "small"
        )
        
        return {
            "strategy1": strategy1,
            "strategy2": strategy2,
            "metric": metric,
            "mean1": mean1,
            "mean2": mean2,
            "std1": std1,
            "std2": std2,
            "difference": mean1 - mean2,
            "difference_pct": ((mean1 - mean2) / mean1 * 100) if mean1 != 0 else 0,
            "t_statistic": t_stat,
            "t_pvalue": t_pval,
            "mannwhitney_u": u_stat,
            "mannwhitney_pvalue": u_pval,
            "cohens_d": cohens_d,
            "effect_size": effect_size_interpretation,
            "statistically_significant": significant,
            "interpretation": (
                f"{strategy1} vs {strategy2}: "
                f"{'SIGNIFICANT' if significant else 'NOT SIGNIFICANT'} difference "
                f"({effect_size_interpretation} effect size, p={t_pval:.4f})"
            )
        }
    
    @staticmethod
    def generate_pairwise_comparison(results_df: pd.DataFrame,
                                      strategies: List[str],
                                      metric: str = "total_co2_g") -> pd.DataFrame:
        """Generate pairwise comparison matrix."""
        comparisons = []
        
        for i, s1 in enumerate(strategies):
            for s2 in strategies[i+1:]:
                comp = StatisticalValidator.compare_strategies(results_df, s1, s2, metric)
                if "error" not in comp:
                    comparisons.append(comp)
        
        return pd.DataFrame(comparisons)


# =============================================================================
# ANALYSIS & VISUALIZATION
# =============================================================================

class ExperimentAnalyzer:
    """
    Analyze and visualize experiment results.
    """
    
    def __init__(self, results_df: pd.DataFrame, output_dir: str):
        self.results_df = results_df
        self.output_dir = output_dir
        sns.set_style("whitegrid")
        
    def generate_summary_statistics(self) -> pd.DataFrame:
        """Generate comprehensive summary statistics."""
        summary = self.results_df.groupby("strategy").agg({
            "operational_co2_g": ["sum", "mean", "std"],
            "embodied_co2_g": ["sum", "mean", "std"],
            "total_co2_g": ["sum", "mean", "std"],
            "latency_ms": ["mean", "std"],
            "sla_met": ["sum", "mean"],  # Count and percentage
            "server_age_years": ["mean", "std"],
        }).round(6)
        
        # Flatten column names
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        
        # Calculate additional metrics
        baseline_total = summary.loc["baseline", "total_co2_g_sum"]
        summary["carbon_reduction_vs_baseline_g"] = baseline_total - summary["total_co2_g_sum"]
        summary["carbon_reduction_vs_baseline_pct"] = (
            (baseline_total - summary["total_co2_g_sum"]) / baseline_total * 100
        )
        
        # SLA compliance rate
        summary["sla_compliance_rate"] = summary["sla_met_mean"] * 100
        
        return summary
    
    def plot_comprehensive_analysis(self):
        """Generate comprehensive visualization."""
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Total carbon by strategy (stacked bar)
        ax1 = fig.add_subplot(gs[0, 0])
        summary = self.results_df.groupby("strategy")[["operational_co2_g", "embodied_co2_g"]].sum()
        summary.plot(kind="bar", stacked=True, ax=ax1, color=["#ff6b6b", "#4ecdc4"])
        ax1.set_title("Total Carbon Emissions", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Carbon (g CO₂)", fontsize=10)
        ax1.set_xlabel("")
        ax1.legend(["Operational", "Embodied"], fontsize=9)
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Carbon reduction vs baseline
        ax2 = fig.add_subplot(gs[0, 1])
        baseline_total = self.results_df[self.results_df["strategy"] == "baseline"]["total_co2_g"].sum()
        reductions = []
        strategies = []
        for strategy in self.results_df["strategy"].unique():
            if strategy != "baseline":
                strategy_total = self.results_df[self.results_df["strategy"] == strategy]["total_co2_g"].sum()
                reduction_pct = (baseline_total - strategy_total) / baseline_total * 100
                reductions.append(reduction_pct)
                strategies.append(strategy)
        
        colors = ['#95e1d3' if r > 0 else '#f38181' for r in reductions]
        ax2.bar(range(len(strategies)), reductions, color=colors)
        ax2.set_xticks(range(len(strategies)))
        ax2.set_xticklabels(strategies, rotation=45, ha='right')
        ax2.set_title("Carbon Reduction vs Baseline", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Reduction (%)", fontsize=10)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.grid(axis='y', alpha=0.3)
        
        # Plot 3: SLA compliance
        ax3 = fig.add_subplot(gs[0, 2])
        sla_data = self.results_df.groupby("strategy")["sla_met"].mean() * 100
        sla_data.plot(kind="bar", ax=ax3, color="#aa96da")
        ax3.set_title("SLA Compliance Rate", fontsize=12, fontweight="bold")
        ax3.set_ylabel("Compliance (%)", fontsize=10)
        ax3.set_xlabel("")
        ax3.axhline(y=95, color='r', linestyle='--', label="95% Target", linewidth=2)
        ax3.legend(fontsize=9)
        ax3.tick_params(axis='x', rotation=45)
        ax3.set_ylim([0, 105])
        
        # Plot 4: Carbon distribution (violin)
        ax4 = fig.add_subplot(gs[1, 0])
        strategies_list = self.results_df["strategy"].unique()
        data_for_violin = [self.results_df[self.results_df["strategy"] == s]["total_co2_g"] 
                          for s in strategies_list]
        parts = ax4.violinplot(data_for_violin, positions=range(len(strategies_list)), 
                               showmeans=True, showmedians=True)
        ax4.set_xticks(range(len(strategies_list)))
        ax4.set_xticklabels(strategies_list, rotation=45, ha='right')
        ax4.set_title("Carbon per Task Distribution", fontsize=12, fontweight="bold")
        ax4.set_ylabel("Total Carbon (g CO₂)", fontsize=10)
        ax4.grid(axis='y', alpha=0.3)
        
        # Plot 5: Workload type analysis
        ax5 = fig.add_subplot(gs[1, 1])
        workload_summary = self.results_df.groupby(["workload_type", "strategy"])["total_co2_g"].mean().unstack()
        workload_summary.plot(kind="bar", ax=ax5)
        ax5.set_title("Carbon by Workload Type", fontsize=12, fontweight="bold")
        ax5.set_ylabel("Avg Carbon (g CO₂)", fontsize=10)
        ax5.set_xlabel("")
        ax5.legend(title="Strategy", fontsize=8, loc='upper left')
        ax5.tick_params(axis='x', rotation=45)
        
        # Plot 6: Server age distribution
        ax6 = fig.add_subplot(gs[1, 2])
        if "server_age" in self.results_df.columns:
            age_counts = self.results_df.groupby(["strategy", "server_age"]).size().unstack(fill_value=0)
            age_counts.plot(kind="bar", stacked=True, ax=ax6, 
                           color=["#74b9ff", "#fdcb6e", "#e17055"])
            ax6.set_title("Server Age Selection", fontsize=12, fontweight="bold")
            ax6.set_ylabel("Count", fontsize=10)
            ax6.set_xlabel("")
            ax6.legend(title="Server Age", fontsize=8)
            ax6.tick_params(axis='x', rotation=45)
        
        # Plot 7: Duration vs Carbon scatter
        ax7 = fig.add_subplot(gs[2, 0])
        for strategy in self.results_df["strategy"].unique():
            strategy_data = self.results_df[self.results_df["strategy"] == strategy]
            ax7.scatter(strategy_data["duration_seconds"], strategy_data["total_co2_g"],
                       alpha=0.3, s=5, label=strategy)
        ax7.set_title("Duration vs Carbon", fontsize=12, fontweight="bold")
        ax7.set_xlabel("Duration (seconds)", fontsize=10)
        ax7.set_ylabel("Total Carbon (g CO₂)", fontsize=10)
        ax7.set_xscale("log")
        ax7.legend(fontsize=8)
        ax7.grid(alpha=0.3)
        
        # Plot 8: Operational vs Embodied percentage
        ax8 = fig.add_subplot(gs[2, 1])
        carbon_breakdown = self.results_df.groupby("strategy")[["operational_co2_g", "embodied_co2_g"]].sum()
        carbon_breakdown_pct = carbon_breakdown.div(carbon_breakdown.sum(axis=1), axis=0) * 100
        carbon_breakdown_pct.plot(kind="bar", stacked=True, ax=ax8, 
                                  color=["#ff6b6b", "#4ecdc4"])
        ax8.set_title("Carbon Breakdown (%)", fontsize=12, fontweight="bold")
        ax8.set_ylabel("Percentage", fontsize=10)
        ax8.set_xlabel("")
        ax8.legend(["Operational", "Embodied"], fontsize=9)
        ax8.tick_params(axis='x', rotation=45)
        
        # Plot 9: Average latency
        ax9 = fig.add_subplot(gs[2, 2])
        latency_data = self.results_df.groupby("strategy")["latency_ms"].mean()
        latency_data.plot(kind="bar", ax=ax9, color="#6c5ce7")
        ax9.set_title("Average Latency", fontsize=12, fontweight="bold")
        ax9.set_ylabel("Latency (ms)", fontsize=10)
        ax9.set_xlabel("")
        ax9.tick_params(axis='x', rotation=45)
        ax9.grid(axis='y', alpha=0.3)
        
        plt.savefig(os.path.join(self.output_dir, "comprehensive_analysis.png"), 
                   dpi=300, bbox_inches='tight')
        print(f"✅ Saved: comprehensive_analysis.png")
        plt.close()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution: Generate workloads and run experiments.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description="Large-scale carbon scheduling experiments")
    parser.add_argument("--num_tasks", type=int, default=1000, help="Number of tasks to generate")
    parser.add_argument("--duration_hours", type=float, default=24, help="Experiment duration in hours")
    parser.add_argument("--output_dir", type=str, default="experiment_results_large", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--strategies", nargs='+', default=None, help="Strategies to test")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("LARGE-SCALE CARBON SCHEDULING EXPERIMENT")
    print("="*80)
    print(f"Tasks: {args.num_tasks}")
    print(f"Duration: {args.duration_hours} hours")
    print(f"Output: {args.output_dir}")
    print(f"Seed: {args.seed}")
    
    # Step 1: Generate workloads
    print(f"\n📋 STEP 1: Generating {args.num_tasks} realistic tasks...")
    generator = WorkloadGenerator(seed=args.seed)
    tasks_df = generator.generate_task_batch(
        num_tasks=args.num_tasks,
        start_time=datetime(2025, 11, 9, 9, 0, 0),
        duration_hours=args.duration_hours
    )
    
    print(f"   ✅ Generated {len(tasks_df)} tasks")
    print(f"   Workload types: {tasks_df['workload_type'].value_counts().to_dict()}")
    
    # Save tasks
    os.makedirs(args.output_dir, exist_ok=True)
    tasks_file = os.path.join(args.output_dir, "tasks_generated.csv")
    tasks_df.to_csv(tasks_file, index=False)
    print(f"   ✅ Saved: {tasks_file}")
    
    # Step 2: Run experiments
    print(f"\n🚀 STEP 2: Running experiments...")
    runner = ExperimentRunner(args.output_dir)
    
    strategies = args.strategies if args.strategies else [
        "baseline", "reactive", "predictive_lr", 
        "embodied_prioritized", "balanced", "operational_only"
    ]
    
    results_df = runner.run_experiment(tasks_df, strategies=strategies)
    
    # Step 3: Summary statistics
    print(f"\n📊 STEP 3: Analyzing results...")
    analyzer = ExperimentAnalyzer(results_df, args.output_dir)
    
    summary = analyzer.generate_summary_statistics()
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(summary.to_string())
    
    summary_file = os.path.join(args.output_dir, "summary_statistics.csv")
    summary.to_csv(summary_file)
    print(f"\n✅ Saved: {summary_file}")
    
    # Step 4: Statistical tests
    print(f"\n🔬 STEP 4: Statistical validation...")
    validator = StatisticalValidator()
    
    comparisons = validator.generate_pairwise_comparison(
        results_df, 
        strategies,
        metric="total_co2_g"
    )
    
    print("\n" + "="*80)
    print("PAIRWISE STATISTICAL COMPARISONS")
    print("="*80)
    for _, row in comparisons.iterrows():
        print(f"\n{row['interpretation']}")
        print(f"  Mean difference: {row['difference']:.6f}g ({row['difference_pct']:.2f}%)")
        print(f"  Cohen's d: {row['cohens_d']:.3f} ({row['effect_size']} effect)")
        print(f"  p-value: {row['t_pvalue']:.6f}")
    
    comparisons_file = os.path.join(args.output_dir, "statistical_comparisons.csv")
    comparisons.to_csv(comparisons_file, index=False)
    print(f"\n✅ Saved: {comparisons_file}")
    
    # Step 5: Visualizations
    print(f"\n📈 STEP 5: Generating visualizations...")
    analyzer.plot_comprehensive_analysis()
    
    print("\n" + "="*80)
    print("✅ EXPERIMENT COMPLETE!")
    print("="*80)
    print(f"\nResults saved in: {args.output_dir}/")
    print(f"  - results_complete.csv: All execution data ({len(results_df)} records)")
    print(f"  - summary_statistics.csv: Aggregated metrics")
    print(f"  - statistical_comparisons.csv: Pairwise t-tests")
    print(f"  - comprehensive_analysis.png: 9-panel visualization")
    

if __name__ == "__main__":
    main()
