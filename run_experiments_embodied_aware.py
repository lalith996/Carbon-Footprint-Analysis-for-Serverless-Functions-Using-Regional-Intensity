"""
run_experiments_embodied_aware.py
==================================
Run comprehensive experiments comparing traditional vs embodied carbon-aware scheduling.

Tests three strategies:
1. embodied_prioritized - Favors older servers with paid-off carbon debt
2. balanced - Balances operational and embodied carbon equally  
3. operational_only - Traditional approach (ignores hardware age)
"""

import subprocess
import csv
import os
import time
import json
import sys
from datetime import datetime
from scheduler_embodied_aware import choose_region_embodied_aware

REGIONS = ["Northern", "Western", "Southern", "Eastern"]
WORKLOAD_SCALES = [200000, 400000, 800000]
STRATEGIES = ["embodied_prioritized", "balanced", "operational_only"]
REPEATS = 3

out_dir = "experiment_results"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "embodied_aware_experiments.csv")

# Initialize CSV
if not os.path.exists(out_file):
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "strategy", "region", "server_age", "server_age_years",
            "workload_scale", "duration_s", "operational_co2_g", "embodied_co2_g",
            "total_co2_g", "carbon_debt_ratio", "power_w", "latency_ms",
            "score", "carbon_intensity", "note"
        ])

def simulate_run(region, server_age, scale):
    """Run workload simulation."""
    cmd = [sys.executable, "serverless_task.py", "--scale", str(scale), "--region", region]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = proc.stdout.strip()
        if not output:
            return None
        lines = [line for line in output.splitlines() if line.startswith("{") and line.endswith("}")]
        if not lines:
            return None
        record = json.loads(lines[-1])
        return record
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

print("="*70)
print("EMBODIED CARBON-AWARE SCHEDULING EXPERIMENTS")
print("="*70)
print(f"Strategies: {len(STRATEGIES)}")
print(f"Workload scales: {WORKLOAD_SCALES}")
print(f"Repeats per configuration: {REPEATS}")
print(f"Total experiments: {len(STRATEGIES) * len(WORKLOAD_SCALES) * REPEATS}")
print("="*70)

experiment_count = 0
total_experiments = len(STRATEGIES) * len(WORKLOAD_SCALES) * REPEATS

for strategy in STRATEGIES:
    print(f"\n{'='*70}")
    print(f"STRATEGY: {strategy.upper()}")
    print(f"{'='*70}")
    
    for scale in WORKLOAD_SCALES:
        print(f"\n  Workload Scale: {scale}")
        
        for rep in range(REPEATS):
            experiment_count += 1
            ts = datetime.utcnow().isoformat()
            
            # Use embodied-aware scheduler to choose region and server age
            result = choose_region_embodied_aware(
                duration_s=scale/50000,  # Estimate duration
                sla_ms=2000,
                strategy=strategy,
                verbose=False
            )
            
            region = result["region"]
            server_age = result["server_age"]
            
            # Run actual workload
            rec = simulate_run(region, server_age, scale)
            
            if rec:
                # Log experiment
                with open(out_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        ts,
                        strategy,
                        region,
                        server_age,
                        result["server_age_years"],
                        scale,
                        rec["duration_s"],
                        result["operational_co2_g"],
                        result["embodied_co2_g"],
                        result["total_co2_g"],
                        result["carbon_debt_ratio"],
                        result["power_consumption_w"],
                        result["latency_ms"],
                        result["score"],
                        result["carbon_intensity"],
                        "ok"
                    ])
                
                progress = (experiment_count / total_experiments) * 100
                print(f"    [{experiment_count}/{total_experiments}] {progress:.1f}% - "
                      f"{region} ({server_age}) - CO₂: {result['total_co2_g']:.6f}g")
            
            time.sleep(0.5)

print(f"\n{'='*70}")
print(f"✅ Experiments Complete!")
print(f"Results saved to: {out_file}")
print(f"{'='*70}")
