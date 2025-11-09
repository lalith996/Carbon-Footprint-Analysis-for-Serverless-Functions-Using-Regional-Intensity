# Duration Sensitivity Analysis Report

**Date**: 2025-11-09 19:37:36
**Test Durations**: 8 (5s to 3600s)
**Strategies Tested**: 3

---

## Executive Summary

### Key Findings:

**embodied_prioritized**:
- ❌ No crossover found (remains worse than baseline up to 60 minutes)

**balanced**:
- ❌ No crossover found (remains worse than baseline up to 60 minutes)

## Detailed Results by Duration

| Duration | Operational Only | Embodied Prioritized | Balanced | Best Strategy |
|----------|------------------|---------------------|----------|---------------|
| 5s (0.1m) | 0.090g | 0.103g (+14.9%) | 0.090g (+0.0%) | **operational_only** |
| 15s (0.2m) | 0.269g | 0.309g (+14.9%) | 0.269g (+0.0%) | **operational_only** |
| 30s (0.5m) | 0.478g | 0.617g (+29.2%) | 0.537g (+12.4%) | **operational_only** |
| 60s (1.0m) | 0.956g | 1.069g (+11.9%) | 0.956g (+0.0%) | **operational_only** |
| 300s (5.0m) | 4.778g | 5.346g (+11.9%) | 4.778g (+0.0%) | **operational_only** |
| 600s (10.0m) | 9.557g | 10.691g (+11.9%) | 9.557g (+0.0%) | **operational_only** |
| 1800s (30.0m) | 28.670g | 32.074g (+11.9%) | 28.670g (+0.0%) | **operational_only** |
| 3600s (60.0m) | 57.340g | 64.149g (+11.9%) | 57.340g (+0.0%) | **operational_only** |

## Insights

### 1. Operational Carbon Dominance for Short Tasks

For short tasks (≤15s), embodied carbon represents only **15.4%** of total emissions. Operational carbon dominates, making embodied-aware strategies less effective due to the power penalty of older servers.

### 2. Crossover Point Analysis

Within the tested range (up to 60 minutes), embodied-aware strategies do not outperform baseline. This suggests that for typical serverless workloads (<1 hour), operational carbon optimization is more effective.

### 3. Strategy Recommendations

**For Serverless/FaaS (5s - 5min):**
- Use `operational_only` or `balanced` strategies
- Focus on carbon intensity timing and regional selection
- Embodied carbon <20% of total - not worth the power penalty

**For All Workload Types:**
- Stick with `operational_only` strategy
- Embodied-aware optimization not effective for durations tested
- Focus on timing (CI variation) and regional selection

---

## Data Files

- Raw data: `duration_sensitivity_results/results.csv`
- Visualization: `duration_sensitivity_results/duration_sensitivity_analysis.png`
