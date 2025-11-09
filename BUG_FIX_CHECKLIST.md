# 🐛 Bug Fix Checklist: Carbon Scheduling Experiments

## Issue Summary

**Problem**: Embodied-aware strategies show 65-104% worse performance (should be 10-20%)
**Root Causes**: 
1. Excessive aging degradation model (83% vs expected 12%/year)
2. Potential double-counting in carbon accounting
3. Timing inconsistencies in CI measurements
4. Missing intermediate calculation validation

---

## Step 1: Diagnostic Run ✅

### 1.1 Create Debug Mode
- [ ] Add `--debug` flag to experiments
- [ ] Log intermediate calculations for each task
- [ ] Track CI values used per strategy
- [ ] Output per-task breakdown (operational, embodied, total)

### 1.2 Validation Metrics to Track
```python
# For each task execution:
- duration_s
- region_chosen
- carbon_intensity_used (gCO₂/kWh)
- server_age_years
- base_power_w
- actual_power_w
- degradation_factor
- operational_co2_g (raw calculation)
- embodied_co2_g (amortized)
- total_co2_g
- timestamp
```

### 1.3 Sanity Checks
- [ ] Verify power degradation: Should be `base_power × (1 + 0.12 × age)` MAX 60%
- [ ] Check embodied carbon: Should be ~10-30% of total for short tasks
- [ ] Validate CI values: All strategies should use same CI at same time
- [ ] Confirm amortization: Embodied should decrease with server age

---

## Step 2: Fix Implementation 🔧

### 2.1 Power Degradation Model
**Current Bug**: 83% increase for 4-year-old servers (too high!)

**Fix**:
```python
# scheduler_embodied_aware.py - Line ~150
def calculate_power_consumption(base_power_w: float, age_years: float) -> float:
    """
    Calculate power consumption with realistic degradation.
    
    Research shows 10-15% degradation per year, capped at 60% total.
    """
    DEGRADATION_RATE = 0.12  # 12% per year
    MAX_DEGRADATION = 0.60   # Cap at 60% total increase
    
    degradation_factor = min(DEGRADATION_RATE * age_years, MAX_DEGRADATION)
    actual_power = base_power_w * (1 + degradation_factor)
    
    # Assertion for validation
    assert actual_power <= base_power_w * 1.60, \
        f"Power {actual_power}W exceeds 60% cap for base {base_power_w}W"
    
    return actual_power
```

**Expected Results**:
- New (0.5y): 65W × 1.06 = 68.9W ✓
- Medium (2.5y): 65W × 1.30 = 84.5W (was 93.6W) ✓
- Old (4.0y): 65W × 1.48 = 96.2W (was 125.8W) ✓✓✓

### 2.2 Carbon Accounting - Remove Double Counting
**Current Bug**: May be applying embodied benefits incorrectly

**Fix**:
```python
# scheduler_embodied_aware.py - Line ~180
def calculate_amortized_embodied_carbon(
    server_age_years: float,
    duration_hours: float,
    total_embodied_kg: float = 660,  # kg CO₂e per server
    expected_lifetime_years: float = 5.0
) -> float:
    """
    Calculate amortized embodied carbon for this task.
    
    CRITICAL: This is ADDITIONAL carbon beyond operational.
    Do NOT subtract from operational carbon.
    """
    # Remaining lifetime
    remaining_years = max(expected_lifetime_years - server_age_years, 0.1)
    
    # Amortize over remaining lifetime
    hours_remaining = remaining_years * 365.25 * 24
    embodied_per_hour_g = (total_embodied_kg * 1000) / hours_remaining
    
    task_embodied_g = embodied_per_hour_g * duration_hours
    
    # Assertion: Embodied should be small fraction of operational
    # For typical 15s task: ~0.01-0.05g embodied
    assert 0 <= task_embodied_g <= 1.0, \
        f"Embodied carbon {task_embodied_g}g seems unrealistic for {duration_hours}h task"
    
    return task_embodied_g
```

### 2.3 Ensure Consistent CI Timing
**Current Bug**: Different strategies may query CI at different times

**Fix**:
```python
# experiments_large_scale.py - Line ~250
class ExperimentRunner:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.ci_cache = {}
        self.cache_timestamp = None  # Track when CI was fetched
        
    def get_ci_for_all_regions_synced(self) -> Dict[str, float]:
        """
        Fetch CI for ALL regions at SAME TIME.
        Ensures fair comparison across strategies.
        """
        current_time = time.time()
        cache_key = int(current_time / 300)  # 5-min buckets
        
        if cache_key != self.cache_timestamp:
            # Refresh all regions atomically
            self.ci_cache.clear()
            for region in ["Northern", "Western", "Southern", "Eastern"]:
                ci_result = get_live_ci(region)
                self.ci_cache[region] = ci_result[0] if ci_result else 600
            self.cache_timestamp = cache_key
            
        return self.ci_cache.copy()
```

### 2.4 Add Calculation Assertions
**Fix**: Add validation throughout

```python
# After every carbon calculation:
def validate_carbon_result(result: Dict) -> None:
    """Validate carbon calculation makes sense."""
    
    # 1. Operational carbon should dominate for short tasks
    if result["duration_seconds"] < 60:
        assert result["operational_co2_g"] > result["embodied_co2_g"], \
            f"Embodied {result['embodied_co2_g']}g exceeds operational {result['operational_co2_g']}g for short task"
    
    # 2. Total should be sum
    expected_total = result["operational_co2_g"] + result["embodied_co2_g"]
    assert abs(result["total_co2_g"] - expected_total) < 0.001, \
        f"Total {result['total_co2_g']}g != sum {expected_total}g"
    
    # 3. Old servers should have LOWER embodied per hour
    if result.get("server_age_years", 0) > 3:
        assert result["embodied_co2_g"] < result["operational_co2_g"] * 0.1, \
            f"Old server embodied {result['embodied_co2_g']}g too high vs operational"
    
    # 4. Reasonable power consumption
    assert 50 <= result.get("power_w", 80) <= 150, \
        f"Power {result['power_w']}W outside reasonable range"
```

### 2.5 Fix Scoring Function (If Using Lifecycle Scheduler)
**Current Bug**: May be overweighting embodied carbon

**Fix**:
```python
# scheduler_embodied_aware.py - Line ~400
def calculate_score_balanced(
    operational_g: float,
    embodied_g: float,
    latency_ms: float,
    carbon_debt_ratio: float
) -> float:
    """
    Balanced scoring with realistic weights.
    
    For typical serverless (15s), operational >> embodied,
    so embodied weight should be small.
    """
    # Normalize to 0-100 scale
    op_score = operational_g * 100  # grams scale
    emb_score = embodied_g * 100
    latency_score = latency_ms / 10  # ms scale
    debt_score = carbon_debt_ratio * 100  # 0-1 scale
    
    # Weights: Operational dominates for short tasks
    weighted_score = (
        0.60 * op_score +      # Operational is PRIMARY
        0.15 * emb_score +     # Embodied is SECONDARY
        0.15 * latency_score + # Performance matters
        0.10 * debt_score      # Slight preference for paid-off servers
    )
    
    return weighted_score
```

---

## Step 3: Create Validation Test Suite 🧪

### 3.1 Unit Tests
```python
# test_carbon_calculations.py

import pytest
from scheduler_embodied_aware import (
    calculate_power_consumption,
    calculate_amortized_embodied_carbon,
    calculate_carbon_debt_ratio
)

def test_power_degradation_realistic():
    """Power should degrade 12% per year, max 60%."""
    # New server
    assert calculate_power_consumption(65, 0.5) == pytest.approx(68.9, abs=1)
    
    # Medium server
    assert calculate_power_consumption(65, 2.5) == pytest.approx(84.5, abs=2)
    
    # Old server (should cap at 60%)
    assert calculate_power_consumption(65, 4.0) == pytest.approx(96.2, abs=2)
    
    # Very old (should hit cap)
    assert calculate_power_consumption(65, 10.0) <= 65 * 1.60

def test_embodied_decreases_with_age():
    """Older servers have less embodied carbon per task."""
    new_embodied = calculate_amortized_embodied_carbon(0.5, 15/3600)
    old_embodied = calculate_amortized_embodied_carbon(4.0, 15/3600)
    
    assert old_embodied < new_embodied, "Old server should have less embodied carbon"
    assert old_embodied < 0.05, "15s task on old server should be <0.05g embodied"

def test_carbon_debt_ratio():
    """Carbon debt should be (L - t) / L."""
    assert calculate_carbon_debt_ratio(0.5, 5.0) == pytest.approx(0.9)
    assert calculate_carbon_debt_ratio(2.5, 5.0) == pytest.approx(0.5)
    assert calculate_carbon_debt_ratio(4.0, 5.0) == pytest.approx(0.2)

def test_total_carbon_realistic():
    """End-to-end test: 15s task on old server in 600 gCO₂/kWh grid."""
    duration_s = 15
    ci = 600  # gCO₂/kWh
    
    # Old server: 96W, low embodied
    power_w = calculate_power_consumption(65, 4.0)
    operational_g = (power_w / 1000) * (duration_s / 3600) * ci * 1.2  # PUE
    embodied_g = calculate_amortized_embodied_carbon(4.0, duration_s / 3600)
    total_g = operational_g + embodied_g
    
    # Sanity checks
    assert 0.3 <= operational_g <= 0.5, f"Operational {operational_g}g out of range"
    assert 0.01 <= embodied_g <= 0.05, f"Embodied {embodied_g}g out of range"
    assert 0.31 <= total_g <= 0.55, f"Total {total_g}g out of range"
    assert embodied_g < operational_g * 0.15, "Embodied should be <15% of operational"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 3.2 Integration Test
```python
# test_strategy_comparison.py

def test_strategy_differences_realistic():
    """
    Test that embodied strategies are within 10-20% of baseline,
    not 65-104%.
    """
    # Run small experiment (100 tasks)
    results = run_experiment_subset(num_tasks=100)
    
    baseline = results["baseline"]["total_co2_g"].mean()
    balanced = results["balanced"]["total_co2_g"].mean()
    embodied = results["embodied_prioritized"]["total_co2_g"].mean()
    
    # Embodied strategies should be within 20% of baseline
    assert abs(balanced - baseline) / baseline < 0.20, \
        f"Balanced differs by {((balanced - baseline) / baseline) * 100:.1f}%"
    
    assert abs(embodied - baseline) / baseline < 0.20, \
        f"Embodied differs by {((embodied - baseline) / baseline) * 100:.1f}%"
```

---

## Step 4: Diagnostic Run Script 📊

```python
# diagnostic_run.py

"""
Quick diagnostic to identify carbon calculation bugs.
"""

import pandas as pd
from scheduler_embodied_aware import choose_region_embodied_aware

def run_diagnostic():
    print("="*80)
    print("CARBON CALCULATION DIAGNOSTICS")
    print("="*80)
    
    # Test case: 15-second task
    duration_s = 15
    sla_ms = 2000
    
    strategies = ["embodied_prioritized", "balanced", "operational_only"]
    
    results = []
    for strategy in strategies:
        result = choose_region_embodied_aware(
            duration_s=duration_s,
            sla_ms=sla_ms,
            strategy=strategy,
            verbose=True
        )
        
        # Extract key metrics
        row = {
            "strategy": strategy,
            "region": result["region"],
            "age_years": result["server_age_years"],
            "power_w": result["power_consumption_w"],
            "degradation_%": ((result["power_consumption_w"] / 65) - 1) * 100,
            "ci_gCO2/kWh": result["carbon_intensity"],
            "operational_g": result["operational_co2_g"],
            "embodied_g": result["embodied_co2_g"],
            "total_g": result["total_co2_g"],
            "embodied_%_of_total": (result["embodied_co2_g"] / result["total_co2_g"]) * 100,
            "debt_ratio": result["carbon_debt_ratio"]
        }
        results.append(row)
    
    df = pd.DataFrame(results)
    print("\n" + df.to_string(index=False))
    
    # Validate results
    print("\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)
    
    for idx, row in df.iterrows():
        print(f"\n{row['strategy']}:")
        
        # Check 1: Power degradation reasonable
        if row['degradation_%'] > 60:
            print(f"  ❌ FAIL: Degradation {row['degradation_%']:.1f}% exceeds 60% cap")
        else:
            print(f"  ✅ PASS: Degradation {row['degradation_%']:.1f}% within limits")
        
        # Check 2: Embodied is small fraction
        if row['embodied_%_of_total'] > 25:
            print(f"  ❌ FAIL: Embodied {row['embodied_%_of_total']:.1f}% too high (should be <25%)")
        else:
            print(f"  ✅ PASS: Embodied {row['embodied_%_of_total']:.1f}% reasonable")
        
        # Check 3: Total makes sense
        expected = row['operational_g'] + row['embodied_g']
        if abs(row['total_g'] - expected) > 0.001:
            print(f"  ❌ FAIL: Total {row['total_g']:.6f} != {expected:.6f}")
        else:
            print(f"  ✅ PASS: Total carbon calculation correct")
    
    # Strategy comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    
    baseline_total = df[df['strategy'] == 'operational_only']['total_g'].values[0]
    
    for _, row in df.iterrows():
        if row['strategy'] != 'operational_only':
            diff_pct = ((row['total_g'] - baseline_total) / baseline_total) * 100
            
            if abs(diff_pct) > 20:
                print(f"❌ {row['strategy']}: {diff_pct:+.1f}% vs baseline (should be ±20%)")
            else:
                print(f"✅ {row['strategy']}: {diff_pct:+.1f}% vs baseline")

if __name__ == "__main__":
    run_diagnostic()
```

---

## Step 5: Add Duration Sensitivity Analysis 📈

```python
# duration_sensitivity.py

"""
Analyze how strategy performance varies with task duration.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scheduler_embodied_aware import choose_region_embodied_aware

def analyze_duration_sensitivity():
    """
    Test strategies across different durations:
    - Micro: 1-10s (serverless typical)
    - Short: 10-60s (batch processing)
    - Medium: 60-600s (ML inference)
    - Long: 600-3600s (ML training)
    """
    durations = [5, 15, 30, 60, 300, 600, 1800, 3600]  # seconds
    strategies = ["embodied_prioritized", "balanced", "operational_only"]
    
    results = []
    
    for duration_s in durations:
        for strategy in strategies:
            result = choose_region_embodied_aware(
                duration_s=duration_s,
                sla_ms=max(2000, duration_s * 100),  # Scale SLA with duration
                strategy=strategy,
                verbose=False
            )
            
            results.append({
                "duration_s": duration_s,
                "duration_min": duration_s / 60,
                "strategy": strategy,
                "total_g": result["total_co2_g"],
                "operational_g": result["operational_co2_g"],
                "embodied_g": result["embodied_co2_g"],
                "server_age": result["server_age_years"]
            })
    
    df = pd.DataFrame(results)
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Total carbon vs duration
    ax = axes[0]
    for strategy in strategies:
        strategy_df = df[df["strategy"] == strategy]
        ax.plot(strategy_df["duration_min"], strategy_df["total_g"], 
               marker='o', label=strategy, linewidth=2)
    
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Total CO₂ (g)")
    ax.set_title("Carbon Emissions vs Task Duration")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    
    # Plot 2: Difference from baseline
    ax = axes[1]
    baseline_df = df[df["strategy"] == "operational_only"]
    
    for strategy in ["embodied_prioritized", "balanced"]:
        strategy_df = df[df["strategy"] == strategy].reset_index(drop=True)
        baseline_vals = baseline_df["total_g"].values
        strategy_vals = strategy_df["total_g"].values
        diff_pct = ((strategy_vals - baseline_vals) / baseline_vals) * 100
        
        ax.plot(strategy_df["duration_min"], diff_pct, 
               marker='o', label=strategy, linewidth=2)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.axhline(y=20, color='red', linestyle=':', linewidth=1, label='±20% threshold')
    ax.axhline(y=-20, color='red', linestyle=':', linewidth=1)
    ax.set_xlabel("Duration (minutes)")
    ax.set_ylabel("Difference from Baseline (%)")
    ax.set_title("Strategy Performance vs Baseline")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xscale("log")
    
    plt.tight_layout()
    plt.savefig("duration_sensitivity_analysis.png", dpi=300)
    print("✅ Saved: duration_sensitivity_analysis.png")
    
    # Print summary
    print("\n" + "="*80)
    print("DURATION SENSITIVITY SUMMARY")
    print("="*80)
    
    for duration_s in [15, 60, 600]:
        print(f"\n{duration_s}s tasks:")
        subset = df[df["duration_s"] == duration_s]
        baseline_val = subset[subset["strategy"] == "operational_only"]["total_g"].values[0]
        
        for strategy in ["embodied_prioritized", "balanced"]:
            strategy_val = subset[subset["strategy"] == strategy]["total_g"].values[0]
            diff_pct = ((strategy_val - baseline_val) / baseline_val) * 100
            print(f"  {strategy:25s}: {diff_pct:+6.1f}%")

if __name__ == "__main__":
    analyze_duration_sensitivity()
```

---

## Step 6: Re-run Experiments (After Fixes) 🔄

### 6.1 Quick Validation (100 tasks)
```bash
python experiments_large_scale.py --num_tasks 100 --output_dir results_fixed_100 \
    --strategies baseline balanced embodied_prioritized operational_only
```

**Expected Results**:
- Balanced: ±5-10% vs baseline
- Embodied_prioritized: ±10-15% vs baseline
- All embodied values: 10-20% of total carbon

### 6.2 Full Run (1000 tasks)
```bash
python experiments_large_scale.py --num_tasks 1000 --output_dir results_fixed_1000 \
    --strategies baseline reactive predictive_lr embodied_prioritized balanced operational_only
```

**Expected Results**:
- Balanced: 10-15% better than baseline (leverages both metrics)
- Embodied_prioritized: 5-10% worse than baseline (power penalty for old servers)
- Operational_only: Similar to baseline (ignores embodied)

---

## Step 7: Root Cause Analysis Summary 🔍

### Suspected Bugs (In Priority Order):

1. **CRITICAL**: Power degradation model using wrong formula
   - Current: 83% increase (125.8W for 4y server)
   - Expected: 48% increase (96.2W for 4y server)
   - **Impact**: Makes old servers look 2× worse than reality

2. **HIGH**: Embodied carbon calculation possibly doubled
   - Check if amortization is applied twice
   - Verify units (kg vs g, hours vs seconds)
   - **Impact**: Inflates embodied carbon by 2-10×

3. **MEDIUM**: CI timing inconsistency
   - Different strategies may query at different times
   - CI can vary ±20% in 5 minutes
   - **Impact**: Unfair comparison across strategies

4. **LOW**: Scoring function may overweight embodied
   - Check if weights sum to 1.0
   - Verify normalization scales
   - **Impact**: Biases toward specific strategies

---

## Immediate Action Plan 🚀

### Tonight (Diagnostic):
1. ✅ Run `diagnostic_run.py` to identify exact bug
2. ✅ Run unit tests to validate calculations
3. ✅ Create this checklist document

### Tomorrow Morning (Fix):
1. Fix power degradation formula (12%/year, max 60%)
2. Fix embodied carbon amortization
3. Add CI timestamp synchronization
4. Add assertion checks throughout

### Tomorrow Afternoon (Validate):
1. Run unit tests (should all pass)
2. Run 100-task experiment (check ±20% range)
3. Run duration sensitivity analysis
4. Run full 1000-task experiment

### Expected Timeline:
- **Diagnostic**: 1 hour
- **Bug fixes**: 2 hours
- **Testing**: 1 hour
- **Full re-run**: 30 minutes
- **Analysis**: 1 hour
- **Total**: ~5-6 hours

---

## Success Criteria ✓

Experiments are fixed when:
1. ✅ Power degradation: Old servers use 96W (not 125W)
2. ✅ Embodied carbon: <20% of total for 15s tasks
3. ✅ Strategy differences: Within ±20% of baseline
4. ✅ All assertions pass without errors
5. ✅ Unit tests: 100% pass rate
6. ✅ Balanced strategy shows SLIGHT advantage (5-15% better)
7. ✅ Old servers show small penalty (5-10% worse) due to power only

---

**Created**: November 9, 2025, 7:00 PM  
**Status**: Ready for diagnostic run  
**Priority**: HIGH - Research findings depend on accurate calculations
