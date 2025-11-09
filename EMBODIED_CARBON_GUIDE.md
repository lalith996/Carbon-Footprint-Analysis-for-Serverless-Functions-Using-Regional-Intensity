# 🌍 Embodied Carbon Tracking Guide

## Overview

This project now includes **comprehensive embodied carbon tracking** alongside operational carbon emissions. Embodied carbon represents the CO₂ emissions from manufacturing, transporting, and disposing of hardware over its lifetime.

## What's New?

### ✨ Features

1. **Embodied Carbon Calculation** - Tracks hardware manufacturing emissions
2. **Comprehensive Telemetry** - CPU, Memory, GPU (if available), and Disk usage
3. **Total Carbon Footprint** - Combines operational + embodied emissions
4. **Instance Type Comparison** - Compare carbon footprint across cloud instances
5. **Real-time Monitoring** - Periodic sampling during workload execution

### 📊 Carbon Components

**Total Carbon Emissions = Operational Carbon + Embodied Carbon**

- **Operational Carbon**: CO₂ from electricity consumption during workload
- **Embodied Carbon**: Amortized CO₂ from hardware manufacturing (CPUs, GPUs, RAM, Storage)

---

## Quick Start

### 1. Run Basic Embodied Carbon Demo

```bash
python embodied_carbon.py
```

This demonstrates:
- Hardware embodied carbon for different instance types
- Real-time telemetry collection
- Complete carbon footprint calculation

### 2. Run Enhanced Serverless Task

```bash
# Simple workload with embodied carbon tracking
python serverless_task_enhanced.py --scale 400000 --enhanced

# Specify instance type and region
python serverless_task_enhanced.py \
  --scale 400000 \
  --region Northern \
  --instance cloud_medium \
  --enhanced

# Adjust telemetry sampling interval
python serverless_task_enhanced.py \
  --scale 800000 \
  --enhanced \
  --telemetry-interval 0.2
```

### 3. Analyze Results

```bash
python analyze_embodied_carbon.py
```

This generates:
- Carbon emissions summary (operational vs embodied)
- Hardware telemetry statistics
- Visualizations (pie charts, timelines, comparisons)
- Instance type comparison

---

## 📁 New Files

| File | Description |
|------|-------------|
| `embodied_carbon.py` | Core module for embodied carbon calculation and telemetry |
| `serverless_task_enhanced.py` | Enhanced task runner with full carbon tracking |
| `analyze_embodied_carbon.py` | Analysis and visualization tool |
| `Data/results_enhanced.csv` | Output file with detailed metrics |

---

## 🔧 Configuration

### Instance Types

The following instance types are pre-configured with hardware specifications:

| Instance Type | CPUs | RAM (GB) | GPU | Storage (GB) | Total Embodied CO₂ |
|--------------|------|----------|-----|--------------|-------------------|
| `cloud_small` | 2 | 8 | 0 | 100 | 252 kg CO₂e |
| `cloud_medium` | 4 | 16 | 0 | 200 | 512 kg CO₂e |
| `cloud_large` | 8 | 32 | 0 | 500 | 1,072 kg CO₂e |
| `gpu_instance` | 8 | 64 | 1 (datacenter) | 1,000 | 1,494 kg CO₂e |
| `local_machine` | Auto-detected | Auto | 0 | 500 | ~660 kg CO₂e |

### Hardware Lifetime Assumptions

- **CPUs**: 5 years
- **GPUs**: 4 years
- **RAM/Storage**: 5 years
- **Servers**: 5 years

These values can be modified in `embodied_carbon.py`.

---

## 📊 Understanding the Output

### Enhanced CSV Output

The `results_enhanced.csv` contains:

**Timing**:
- `duration_s` - Total execution time
- `cpu_time_s` - Actual CPU time used

**CPU Telemetry**:
- `cpu_percent_avg` - Average CPU utilization
- `cpu_percent_max` - Peak CPU utilization
- `cpu_count` - Number of CPU cores

**Memory Telemetry**:
- `memory_used_gb_avg` - Average RAM usage
- `memory_percent_avg` - Average RAM percentage
- `memory_percent_max` - Peak RAM usage
- `memory_delta_mb` - Memory increase during workload

**GPU Telemetry** (if available):
- `gpu_available` - GPU detected (true/false)
- `gpu_count` - Number of GPUs
- `gpu_utilization` - GPU usage percentage
- `gpu_memory_used_gb` - GPU memory usage

**Carbon Emissions**:
- `energy_kwh` - Energy consumed
- `operational_co2_g` - CO₂ from electricity
- `embodied_co2_g` - Amortized hardware CO₂
- `total_co2_g` - Total carbon footprint
- `operational_percent` - Percentage from operations
- `embodied_percent` - Percentage from hardware

**Hardware Info**:
- `instance_type` - Instance configuration
- `ram_gb` - Total RAM
- `storage_gb` - Total storage
- `total_embodied_carbon_kg` - Total hardware manufacturing emissions

---

## 🔬 Example Results

### Sample Output

```json
{
  "timestamp": "2025-11-09T12:39:06",
  "region": "Northern",
  "instance_type": "cloud_medium",
  "workload_scale": 400000,
  "duration_s": 0.1434,
  "cpu_percent_avg": 12.5,
  "cpu_percent_max": 24.8,
  "memory_used_gb_avg": 5.85,
  "memory_percent_avg": 77.0,
  "operational_co2_g": 0.001626,
  "embodied_co2_g": 0.000466,
  "total_co2_g": 0.002092,
  "operational_percent": 77.72,
  "embodied_percent": 22.28
}
```

### Key Insights

From our experiments:
- **Operational Carbon**: ~75% of total emissions (varies by region)
- **Embodied Carbon**: ~25% of total emissions
- Embodied carbon is **significant** and should not be ignored!
- Larger instances have higher embodied carbon per hour

---

## 💡 Best Practices

### 1. Choose Right-Sized Instances
- Avoid over-provisioning (reduces embodied carbon)
- Use auto-scaling to match actual demand
- Consider spot/preemptible instances (better hardware utilization)

### 2. Optimize for Both Carbon Types
- **Operational**: Choose low-carbon regions, efficient code
- **Embodied**: Maximize hardware utilization, extend lifetimes

### 3. Monitor Continuously
```python
from embodied_carbon import EmbodiedCarbonTracker

tracker = EmbodiedCarbonTracker("cloud_medium", "Northern")
tracker.start_tracking()

# Your workload here
do_work()

# Sample telemetry periodically
tracker.sample_telemetry()

result = tracker.stop_tracking()
print(f"Total CO2: {result['total_co2_g']:.6f} g")
```

### 4. Report Complete Footprint
Always report **both** operational and embodied carbon:
```
Total Carbon: 0.002092 g CO2e
  - Operational: 77.7%
  - Embodied: 22.3%
```

---

## 🔍 Advanced Usage

### Custom Instance Configuration

```python
from embodied_carbon import INSTANCE_SPECS, EmbodiedCarbonTracker

# Add custom instance type
INSTANCE_SPECS["custom_gpu"] = {
    "cpu_count": 16,
    "cpu_type": "cpu_server",
    "gpu_count": 4,
    "gpu_type": "gpu_datacenter",
    "ram_gb": 128,
    "ram_type": "ram_ddr5",
    "storage_gb": 2000,
    "storage_type": "ssd_nvme",
}

tracker = EmbodiedCarbonTracker("custom_gpu")
print(f"Total embodied: {tracker.calculate_total_embodied_carbon()} kg CO2e")
```

### Integrate with Existing Code

```python
from embodied_carbon import estimate_total_carbon

# After your workload
duration_s = 15.5
region = "Northern"
operational_co2_g = 0.05  # from your estimator

total = estimate_total_carbon(
    duration_s=duration_s,
    region=region,
    instance_type="cloud_medium",
    operational_co2_g=operational_co2_g
)

print(f"Operational: {total['operational_co2_g']:.6f} g")
print(f"Embodied: {total['embodied_co2_g']:.6f} g")
print(f"Total: {total['total_co2_g']:.6f} g")
```

---

## 📈 Visualizations

The analysis tool generates two main visualizations:

### 1. `embodied_carbon_analysis.png`
- Stacked bar chart by region
- Pie chart of carbon split
- CPU vs Memory scatter plot
- Carbon vs workload scale

### 2. `telemetry_timeline.png`
- Hardware usage over time
- Carbon emissions timeline
- Trend analysis

---

## 🎓 References

### Embodied Carbon Data Sources
1. "Estimating the Carbon Footprint of ICT" (European Commission)
2. Dell Product Carbon Footprints
3. Apple Environmental Progress Reports
4. Various LCA (Life Cycle Assessment) studies

### Hardware Specifications
- Server CPUs: ~100 kg CO₂e (Intel Xeon, AMD EPYC)
- Datacenter GPUs: ~150 kg CO₂e (NVIDIA A100, H100)
- RAM: ~5-6 kg CO₂e per GB (DDR4/DDR5)
- SSD Storage: ~0.12-0.16 kg CO₂e per GB

---

## ❓ FAQ

**Q: Why is embodied carbon important?**
A: It can represent 20-40% of total data center emissions and is often overlooked.

**Q: How accurate are the embodied carbon values?**
A: Values are based on industry LCA studies and provide reasonable estimates. Actual values vary by manufacturer and model.

**Q: Can I add GPU tracking?**
A: Yes! Install `pynvml`:
```bash
pip install nvidia-ml-py3
```
The module will auto-detect and track GPU metrics.

**Q: How do I integrate this with my scheduler?**
A: Use `estimate_total_carbon()` in your scheduling decisions to optimize for total carbon, not just operational.

**Q: Should I optimize for operational or embodied carbon?**
A: Both! Choose efficient regions (operational) AND right-sized instances (embodied).

---

## 🚀 Next Steps

1. ✅ Run experiments with embodied carbon tracking
2. ✅ Compare different instance types
3. ✅ Integrate into your scheduling algorithm
4. 📊 Generate reports with complete carbon footprint
5. 🎯 Set carbon reduction targets (operational + embodied)

---

## 📝 License & Citation

If you use this embodied carbon tracking in your research, please cite:

```
GreenAI Cloud Project - Embodied Carbon Tracking Module
https://github.com/avinashpala19/GreenAI-Cloud-Project
```

---

**Happy Green Computing! 🌱**
