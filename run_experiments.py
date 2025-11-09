# run_experiments.py
import subprocess, csv, os, time, json
from datetime import datetime
from scheduler_using_lr import choose_region_with_lr
import json, subprocess
from scheduler import choose_region  # reactive scheduler using live CI
# serverless_task.run_once is available or call script

REGIONS = ["Northern","Western","Southern","Eastern"]
WORKLOAD_SCALES = [200000, 400000, 800000]  # small/medium/large
REPEATS = 5

out_dir = "experiment_results"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "experiment_log.csv")

# header
if not os.path.exists(out_file):
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp","strategy","region","workload_scale","duration_s","co2_g","latency_ms","note"])

def simulate_run(region, scale):
    # Use sys.executable to get the current Python interpreter
    import sys
    cmd = [sys.executable, "serverless_task.py", "--scale", str(scale), "--region", region]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = proc.stdout.strip()
        if not output:
            print(f"⚠️ No output for {region} scale {scale}")
            return None
        # Extract last JSON line
        lines = [line for line in output.splitlines() if line.startswith("{") and line.endswith("}")]
        if not lines:
            print(f"⚠️ No JSON line found in output: {output[-200:]}")
            return None
        record = json.loads(lines[-1])
        return record
    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout while running {region} scale {scale}")
        return None
    except Exception as e:
        print(f"❌ simulate_run() error for {region}: {e}")
        return None

for strategy in ["baseline","reactive","predictive_lr"]:
    for scale in WORKLOAD_SCALES:
        for rep in range(REPEATS):
            ts = datetime.utcnow().isoformat()
            latency = 0
            if strategy == "baseline":
                region = "Northern"  # fixed baseline region, change as required
                latency = 70  # Northern latency
            elif strategy == "reactive":
                res = choose_region(scale, sla_ms=2000)  # reactive uses live only
                region = res.get("region","Northern")
                latency = res.get("latency_ms", 0)
            elif strategy == "predictive_lr":
                res = choose_region_with_lr(scale, sla_ms=2000)
                region = res.get("region","Northern")
                latency = res.get("latency_ms", 0)
            rec = simulate_run(region, scale)
            if rec:
                # compute co2 using estimator (import to compute exactly)
                from estimator import estimate_co2
                _, co2 = estimate_co2(rec["duration_s"], region)
                with open(out_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([ts, strategy, region, scale, rec["duration_s"], co2, latency, "ok"])
            time.sleep(1)  # small gap
print("Done experiments. Log:", out_file)
