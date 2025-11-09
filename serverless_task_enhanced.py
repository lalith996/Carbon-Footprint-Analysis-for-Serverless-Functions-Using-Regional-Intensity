# serverless_task_enhanced.py
"""
Enhanced serverless task with embodied carbon tracking and detailed telemetry.
Tracks CPU, GPU, memory usage and calculates both operational and embodied carbon.
"""

import time, psutil, os, csv, json, argparse
from datetime import datetime
from embodied_carbon import EmbodiedCarbonTracker, estimate_total_carbon

def cpu_bound_work(iter_scale=300000):
    """Simulated CPU-intensive workload."""
    s = 0.0
    for i in range(1, iter_scale):
        s += (i ** 0.5)
    return s

def run_once_enhanced(workload_scale=300000, region="Northern", 
                     instance_type="local_machine",
                     out_csv="Data/results_enhanced.csv",
                     telemetry_interval=0.5):
    """
    Run workload with comprehensive telemetry and carbon tracking.
    
    Args:
        workload_scale: Size of the workload
        region: Data center region
        instance_type: Type of compute instance
        out_csv: Output CSV file path
        telemetry_interval: Seconds between telemetry samples
    
    Returns:
        Dictionary with complete metrics
    """
    # Initialize embodied carbon tracker
    tracker = EmbodiedCarbonTracker(instance_type, region)
    
    # Start tracking
    tracker.start_tracking()
    
    # Get process handle for detailed CPU tracking
    proc = psutil.Process()
    cpu_before = proc.cpu_times().user + proc.cpu_times().system
    mem_before = proc.memory_info().rss / (1024**2)  # MB
    
    # Run workload with periodic telemetry sampling
    start_time = time.time()
    
    # Sample telemetry during execution
    def run_with_sampling():
        result = None
        last_sample = time.time()
        
        # Start the work
        for i in range(1, workload_scale):
            s = (i ** 0.5) if result is None else result + (i ** 0.5)
            
            # Sample telemetry periodically
            if time.time() - last_sample >= telemetry_interval:
                tracker.sample_telemetry()
                last_sample = time.time()
        
        return s
    
    workload_result = run_with_sampling()
    
    # Stop tracking
    tracking_result = tracker.stop_tracking()
    
    end_time = time.time()
    duration_s = end_time - start_time
    
    # Get final process stats
    cpu_after = proc.cpu_times().user + proc.cpu_times().system
    cpu_time_s = cpu_after - cpu_before
    mem_after = proc.memory_info().rss / (1024**2)  # MB
    mem_delta = mem_after - mem_before
    
    # Calculate operational carbon (from electricity)
    from estimator import estimate_co2
    energy_kwh, operational_co2_g = estimate_co2(duration_s, region)
    
    # Get embodied carbon from tracking result
    embodied_co2_g = tracking_result["amortized_embodied_carbon_g"]
    total_co2_g = operational_co2_g + embodied_co2_g
    
    # Prepare comprehensive record
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "region": region,
        "instance_type": instance_type,
        "workload_scale": workload_scale,
        
        # Timing
        "duration_s": round(duration_s, 4),
        "cpu_time_s": round(cpu_time_s, 4),
        
        # CPU telemetry
        "cpu_percent_avg": tracking_result["cpu_percent_avg"],
        "cpu_percent_max": tracking_result["cpu_percent_max"],
        "cpu_count": tracking_result["specs"]["cpu_count"],
        
        # Memory telemetry
        "memory_used_gb_avg": tracking_result["memory_gb_avg"],
        "memory_percent_avg": tracking_result["memory_percent_avg"],
        "memory_percent_max": tracking_result["memory_percent_max"],
        "memory_delta_mb": round(mem_delta, 2),
        
        # GPU telemetry (if available)
        "gpu_available": tracking_result["telemetry_history"][-1].get("gpu_available", False),
        "gpu_count": tracking_result["telemetry_history"][-1].get("gpu_count", 0),
        "gpu_utilization": tracking_result["telemetry_history"][-1].get("gpu_utilization"),
        "gpu_memory_used_gb": tracking_result["telemetry_history"][-1].get("gpu_memory_used_gb"),
        
        # Energy and Carbon
        "energy_kwh": energy_kwh,
        "operational_co2_g": round(operational_co2_g, 6),
        "embodied_co2_g": round(embodied_co2_g, 6),
        "total_co2_g": round(total_co2_g, 6),
        "operational_percent": round((operational_co2_g / total_co2_g * 100) if total_co2_g > 0 else 0, 2),
        "embodied_percent": round((embodied_co2_g / total_co2_g * 100) if total_co2_g > 0 else 0, 2),
        
        # Hardware specs
        "ram_gb": tracking_result["specs"]["ram_gb"],
        "storage_gb": tracking_result["specs"]["storage_gb"],
        "total_embodied_carbon_kg": tracking_result["total_embodied_carbon_kg"],
        
        # Sampling info
        "telemetry_samples": tracking_result["telemetry_samples"],
    }
    
    # Save to CSV
    os.makedirs(os.path.dirname(out_csv) if os.path.dirname(out_csv) else ".", exist_ok=True)
    file_exists = os.path.exists(out_csv)
    
    with open(out_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(record.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)
    
    # Print JSON summary (single line for parsing)
    print(json.dumps(record))
    
    return record


def run_once_simple(workload_scale=300000, region="Northern", out_csv="Data/results.csv"):
    """
    Simple version for backward compatibility.
    """
    proc = psutil.Process()
    start = time.time()
    cpu_before = proc.cpu_times().user + proc.cpu_times().system

    # Do work
    s = 0.0
    for i in range(1, workload_scale):
        s += (i ** 0.5)

    end = time.time()
    cpu_after = proc.cpu_times().user + proc.cpu_times().system
    duration_s = end - start
    cpu_time_s = cpu_after - cpu_before

    os.makedirs(os.path.dirname(out_csv) if os.path.dirname(out_csv) else ".", exist_ok=True)
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

    print(json.dumps(record))
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run serverless task with optional embodied carbon tracking"
    )
    parser.add_argument("--scale", type=int, default=300000, 
                       help="Workload scale (iterations)")
    parser.add_argument("--region", type=str, default="Northern",
                       help="Data center region")
    parser.add_argument("--instance", type=str, default="local_machine",
                       choices=["cloud_small", "cloud_medium", "cloud_large", 
                               "gpu_instance", "local_machine"],
                       help="Instance type for embodied carbon calculation")
    parser.add_argument("--enhanced", action="store_true",
                       help="Use enhanced mode with embodied carbon tracking")
    parser.add_argument("--telemetry-interval", type=float, default=0.5,
                       help="Seconds between telemetry samples (enhanced mode)")
    
    args = parser.parse_args()
    
    if args.enhanced:
        print(f"🔬 Running ENHANCED mode with embodied carbon tracking...")
        result = run_once_enhanced(
            workload_scale=args.scale,
            region=args.region,
            instance_type=args.instance,
            telemetry_interval=args.telemetry_interval
        )
        print(f"\n✅ Complete! Total CO2: {result['total_co2_g']:.6f} g " +
              f"(Operational: {result['operational_percent']:.1f}%, " +
              f"Embodied: {result['embodied_percent']:.1f}%)")
    else:
        print(f"⚡ Running SIMPLE mode (backward compatible)...")
        run_once_simple(args.scale, args.region)
