#!/usr/bin/env python3
"""
Direct CI Test - Bypass scheduler to test CI sensitivity directly
"""

from scheduler_embodied_aware import calculate_total_carbon

print("="*80)
print("DIRECT CI SENSITIVITY TEST")
print("="*80)
print("\nTesting if operational carbon scales with CI (it should!)")
print("Testing embodied carbon independence from CI (it should be!)\n")

ci_values = [50, 100, 200, 535]
duration_s = 14400  # 4 hours

print(f"{'CI':>6s} {'Op New':>10s} {'Emb New':>10s} {'Total New':>12s} {'Op Old':>10s} {'Emb Old':>10s} {'Total Old':>12s} {'Penalty':>10s}")
print("-" * 95)

for ci in ci_values:
    # New server
    op_new, emb_new, total_new = calculate_total_carbon("new", duration_s, ci)
    
    # Old server  
    op_old, emb_old, total_old = calculate_total_carbon("old", duration_s, ci)
    
    penalty_pct = ((total_old - total_new) / total_new) * 100
    
    print(f"{ci:>6d} {op_new:>9.2f}g {emb_new:>9.2f}g {total_new:>11.2f}g "
          f"{op_old:>9.2f}g {emb_old:>9.2f}g {total_old:>11.2f}g {penalty_pct:>9.1f}%")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

# Test at CI = 50
op_new_50, emb_new_50, total_new_50 = calculate_total_carbon("new", duration_s, 50)
op_old_50, emb_old_50, total_old_50 = calculate_total_carbon("old", duration_s, 50)
penalty_50 = ((total_old_50 - total_new_50) / total_new_50) * 100

# Test at CI = 535
op_new_535, emb_new_535, total_new_535 = calculate_total_carbon("new", duration_s, 535)
op_old_535, emb_old_535, total_old_535 = calculate_total_carbon("old", duration_s, 535)
penalty_535 = ((total_old_535 - total_new_535) / total_new_535) * 100

print(f"\nOperational carbon scales with CI:")
print(f"  New server @ CI=50:  {op_new_50:.2f}g")
print(f"  New server @ CI=535: {op_new_535:.2f}g")
print(f"  Ratio: {op_new_535/op_new_50:.1f}x (expected: {535/50:.1f}x) {'✅' if abs(op_new_535/op_new_50 - 535/50) < 0.5 else '❌'}")

print(f"\nEmbodied carbon independent of CI:")
print(f"  New server @ CI=50:  {emb_new_50:.2f}g")
print(f"  New server @ CI=535: {emb_new_535:.2f}g")
print(f"  Difference: {abs(emb_new_535 - emb_new_50):.4f}g (expected: ~0g) {'✅' if abs(emb_new_535 - emb_new_50) < 0.01 else '❌'}")

print(f"\nPenalty at different CI:")
print(f"  CI=50:  {penalty_50:.2f}%")
print(f"  CI=535: {penalty_535:.2f}%")

# Calculate expected penalty at CI=50
op_penalty_50 = op_old_50 - op_new_50
emb_savings = emb_new_50 - emb_old_50
net_penalty_50 = op_penalty_50 - emb_savings

print(f"\nAt CI=50:")
print(f"  Operational penalty: {op_penalty_50:.2f}g")
print(f"  Embodied savings: {emb_savings:.2f}g")
print(f"  Net penalty: {net_penalty_50:.2f}g")

if net_penalty_50 < 0:
    print(f"\n✅ Embodied-aware WINS at CI=50 by {-penalty_50:.1f}%!")
elif penalty_50 < 5:
    print(f"\n🟡 Nearly breaks even at CI=50 (penalty: {penalty_50:.1f}%)")
else:
    print(f"\n❌ Embodied-aware still loses at CI=50 by {penalty_50:.1f}%")
    print(f"   This means embodied savings ({emb_savings:.2f}g) < operational penalty ({op_penalty_50:.2f}g)")
    print(f"   even in cleanest grids!")
