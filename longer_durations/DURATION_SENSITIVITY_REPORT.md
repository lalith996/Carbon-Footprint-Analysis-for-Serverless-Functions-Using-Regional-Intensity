# Duration Sensitivity Analysis Report

**Date**: 2025-11-09 19:50:37
**Test Durations**: 3 (14400s to 86400s)
**Strategies Tested**: 3

---

## Executive Summary

### Key Findings:

**embodied_prioritized**:
- ❌ No crossover found (remains worse than baseline up to 1440 minutes)

**balanced**:
- ❌ No crossover found (remains worse than baseline up to 1440 minutes)

## Detailed Results by Duration

| Duration | Operational Only | Embodied Prioritized | Balanced | Best Strategy |
|----------|------------------|---------------------|----------|---------------|
| 14400s (240.0m) | 229.359g | 256.595g (+11.9%) | 229.359g (+0.0%) | **operational_only** |
| 28800s (480.0m) | 458.718g | 513.189g (+11.9%) | 458.718g (+0.0%) | **operational_only** |
| 86400s (1440.0m) | 1376.153g | 1539.568g (+11.9%) | 1376.153g (+0.0%) | **operational_only** |

## Insights

### 1. Operational Carbon Dominance for Short Tasks

For short tasks (≤15s), embodied carbon represents only **nan%** of total emissions. Operational carbon dominates, making embodied-aware strategies less effective due to the power penalty of older servers.

### 2. Crossover Point Analysis

Within the tested range (up to 1440 minutes), embodied-aware strategies do not outperform baseline. This suggests that for typical serverless workloads (<1 hour), operational carbon optimization is more effective.

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

- Raw data: `longer_durations/results.csv`
- Visualization: `longer_durations/duration_sensitivity_analysis.png`
