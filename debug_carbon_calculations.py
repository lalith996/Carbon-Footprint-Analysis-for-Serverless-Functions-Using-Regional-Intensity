#!/usr/bin/env python3
"""
Debug Carbon Calculations - Diagnose why embodied-aware strategies show constant 11.9% penalty
"""

import sys
from scheduler_embodied_aware import (
    choose_region_embodied_aware,
    calculate_total_carbon,
    calculate_power_consumption,
    calculate_carbon_debt_ratio,
    BASE_POWER_W,
    SERVER_SPECS
)

print("="*80)
print("  CARBON CALCULATION DIAGNOSTIC")
print("="*80)

print("\n" + "="*80)
print("  TEST 1: Power Consumption Verification")
print("="*80)

# Test power calculations
new_age = SERVER_SPECS["new"]["age_years"]
old_age = SERVER_SPECS["old"]["age_years"]

power_new = calculate_power_consumption(BASE_POWER_W, new_age)
power_old = calculate_power_consumption(BASE_POWER_W, old_age)

print(f"\nNew Server:")
print(f"  Age: {new_age:.2f} years")
print(f"  Power: {power_new:.1f}W (expected: ~67W)")

print(f"\nOld Server:")
print(f"  Age: {old_age:.2f} years") 
print(f"  Power: {power_old:.1f}W (expected: ~96W)")

print(f"\nPower Ratio: {power_old/power_new:.2f} (expected: ~1.43)")
print(f"Power Difference: +{power_old - power_new:.1f}W (expected: ~+27W)")

# Validation
if 65 <= power_new <= 70:
    print(f"✅ New server power within expected range")
else:
    print(f"❌ ERROR: New server power {power_new}W outside expected range (65-70W)")

if 90 <= power_old <= 104:
    print(f"✅ Old server power within expected range")
else:
    print(f"❌ ERROR: Old server power {power_old}W outside expected range (90-104W)")

print("\n" + "="*80)
print("  TEST 2: Embodied Carbon Verification (24-hour task)")
print("="*80)

duration_s = 86400  # 24 hours
ci = 535  # gCO2/kWh (Northern region average)

# Calculate for new server
op_new, emb_new, total_new = calculate_total_carbon("new", duration_s, ci)

print(f"\nNew Server ({new_age:.2f}y old):")
print(f"  Operational: {op_new:.2f}g")
print(f"  Embodied: {emb_new:.2f}g ({(emb_new/total_new)*100:.1f}%)")
print(f"  Total: {total_new:.2f}g (expected: ~1370g)")

# Calculate for old server
op_old, emb_old, total_old = calculate_total_carbon("old", duration_s, ci)

print(f"\nOld Server ({old_age:.2f}y old):")
print(f"  Operational: {op_old:.2f}g")
print(f"  Embodied: {emb_old:.2f}g ({(emb_old/total_old)*100:.1f}%)")
print(f"  Total: {total_old:.2f}g")

embodied_savings = emb_new - emb_old
operational_penalty = op_old - op_new

print(f"\nEmbodied Savings: {embodied_savings:.2f}g (expected: ~192g)")
print(f"Operational Penalty: {operational_penalty:.2f}g")

if 180 <= embodied_savings <= 250:
    print(f"✅ Embodied savings within expected range")
else:
    print(f"⚠️  WARNING: Embodied savings {embodied_savings:.2f}g outside expected range (180-250g)")

print("\n" + "="*80)
print("  TEST 3: Total Carbon & Penalty Analysis")
print("="*80)

# Calculate penalty
penalty = ((total_old - total_new) / total_new) * 100
penalty_abs = total_old - total_new

print(f"\nOperational Penalty: {operational_penalty:.2f}g")
print(f"Embodied Savings: {embodied_savings:.2f}g")
print(f"Net Penalty: {penalty_abs:.2f}g")
print(f"Percentage Penalty: {penalty:.1f}%")

print(f"\nExpected Penalty: ~25% (operational penalty > embodied savings)")
print(f"Observed in Tests: 11.9%")

if abs(penalty - 25) < 5:
    print(f"✅ Penalty matches expected calculation (~25%)!")
    print(f"   This suggests calculations are correct but server SELECTION is wrong!")
elif abs(penalty - 11.9) < 2:
    print(f"❌ ERROR: Penalty matches observed 11.9%, not expected 25%")
    print(f"   This suggests a bug in the carbon calculation functions!")
else:
    print(f"⚠️  WARNING: Penalty {penalty:.1f}% doesn't match expected (25%) or observed (11.9%)")

print("\n" + "="*80)
print("  TEST 4: Strategy Selection Verification")
print("="*80)

# Test with 24-hour duration
duration_s = 86400

print(f"\nTesting operational_only strategy:")
result_op = choose_region_embodied_aware(
    duration_s=duration_s,
    strategy="operational_only",
    verbose=False
)

print(f"  Selected Region: {result_op['region']}")
print(f"  Server Age Group: {result_op['server_age']}")
print(f"  Server Age Years: {result_op['server_age_years']:.2f}y")
print(f"  Power: {result_op['power_consumption_w']:.1f}W")
print(f"  Operational CO2: {result_op['operational_co2_g']:.2f}g")
print(f"  Embodied CO2: {result_op['embodied_co2_g']:.2f}g")
print(f"  Total CO2: {result_op['total_co2_g']:.2f}g")

print(f"\nTesting embodied_prioritized strategy:")
result_emb = choose_region_embodied_aware(
    duration_s=duration_s,
    strategy="embodied_prioritized",
    verbose=False
)

print(f"  Selected Region: {result_emb['region']}")
print(f"  Server Age Group: {result_emb['server_age']}")
print(f"  Server Age Years: {result_emb['server_age_years']:.2f}y")
print(f"  Power: {result_emb['power_consumption_w']:.1f}W")
print(f"  Operational CO2: {result_emb['operational_co2_g']:.2f}g")
print(f"  Embodied CO2: {result_emb['embodied_co2_g']:.2f}g")
print(f"  Total CO2: {result_emb['total_co2_g']:.2f}g")

# Compare
diff_total = result_emb['total_co2_g'] - result_op['total_co2_g']
diff_pct = (diff_total / result_op['total_co2_g']) * 100
age_diff = result_emb['server_age_years'] - result_op['server_age_years']

print(f"\n" + "="*80)
print(f"  STRATEGY COMPARISON")
print(f"="*80)
print(f"\nTotal Carbon Difference: {diff_total:+.2f}g ({diff_pct:+.1f}%)")
print(f"Age Difference: {age_diff:+.2f} years")

# CRITICAL BUG DETECTION
if abs(age_diff) < 0.5:
    print(f"\n❌ CRITICAL BUG FOUND: Both strategies selecting servers of similar age!")
    print(f"   Expected: embodied_prioritized should select servers 3-4 years OLDER")
    print(f"   This explains the wrong penalty - wrong servers are being chosen!")
    print(f"\n   Root cause: Check the scoring function in choose_region_embodied_aware()")
    print(f"   The 'embodied_prioritized' strategy scoring may be broken.")
elif result_emb['server_age_years'] > result_op['server_age_years'] + 2:
    print(f"\n✅ Server selection working correctly (age difference: {age_diff:.2f}y)")
    if abs(diff_pct - 11.9) < 2:
        print(f"   ⚠️  But penalty matches observed 11.9% instead of expected 25%")
        print(f"   Mismatch suggests carbon calculations may be inconsistent")
    elif abs(diff_pct - 25) < 5:
        print(f"   ✅ Penalty matches expected ~25%!")
        print(f"   This means the bug is elsewhere (maybe in duration_sensitivity_analysis.py)")
else:
    print(f"\n⚠️  Server selection partially working, but age difference too small")

print("\n" + "="*80)
print("  TEST 5: Scoring Function Analysis")
print("="*80)

# Show top 3 alternatives for each strategy
print(f"\nOperational-only top 3 choices:")
for i, alt in enumerate(result_op['top_3_alternatives'][:3], 1):
    print(f"  {i}. {alt['region']:10s} {alt['server_age']:6s} "
          f"{alt['server_age_years']:.1f}y  Score: {alt['score']:8.2f}  "
          f"Total: {alt['total_co2_g']:.2f}g")

print(f"\nEmbodied-prioritized top 3 choices:")
for i, alt in enumerate(result_emb['top_3_alternatives'][:3], 1):
    print(f"  {i}. {alt['region']:10s} {alt['server_age']:6s} "
          f"{alt['server_age_years']:.1f}y  Score: {alt['score']:8.2f}  "
          f"Total: {alt['total_co2_g']:.2f}g")

print("\n" + "="*80)
print("  DIAGNOSTIC SUMMARY")
print("="*80)

print(f"\n1. Power Consumption: {'✅ CORRECT' if 90 <= power_old <= 104 else '❌ ERROR'}")
print(f"2. Embodied Carbon: {'✅ CORRECT' if 180 <= embodied_savings <= 250 else '⚠️  CHECK'}")
print(f"3. Total Carbon Calc: {'✅ Expected ~25%' if abs(penalty - 25) < 5 else f'⚠️  Got {penalty:.1f}%'}")
print(f"4. Server Selection: {'❌ BROKEN' if abs(age_diff) < 0.5 else '✅ WORKING'}")
print(f"5. Observed Penalty: {diff_pct:.1f}% (expected: ~25%, observed in tests: 11.9%)")

if abs(diff_pct - 11.9) < 2:
    print(f"\n🔍 MATCHES OBSERVED 11.9% - This is the bug source!")
elif abs(diff_pct - 25) < 5:
    print(f"\n✅ Calculations are correct. Bug must be in duration_sensitivity_analysis.py aggregation!")

print("\n" + "="*80)
