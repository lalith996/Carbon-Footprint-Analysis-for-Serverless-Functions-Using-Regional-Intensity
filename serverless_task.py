# serverless_task.py
import time, psutil, os, csv, json, argparse
from datetime import datetime

def cpu_bound_work(iter_scale=300000):
    s = 0.0
    for i in range(1, iter_scale):
        s += (i ** 0.5)
    return s

def run_once(workload_scale=300000, region="Northern", out_csv="Data/results.csv"):
    proc = psutil.Process()
    start = time.time()
    cpu_before = proc.cpu_times().user + proc.cpu_times().system

    cpu_bound_work(workload_scale)

    end = time.time()
    cpu_after = proc.cpu_times().user + proc.cpu_times().system
    duration_s = end - start
    cpu_time_s = cpu_after - cpu_before

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "region": region,
        "duration_s": round(duration_s, 4),
        "cpu_time_s": round(cpu_time_s, 4),
        "workload_scale": workload_scale
    }

    file_exists = os.path.exists(out_csv)
    with open(out_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(record.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    # Print JSON on single line for parsing
    print(json.dumps(record))
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=300000)
    parser.add_argument("--region", type=str, default="Northern")
    args = parser.parse_args()
    run_once(args.scale, args.region)
