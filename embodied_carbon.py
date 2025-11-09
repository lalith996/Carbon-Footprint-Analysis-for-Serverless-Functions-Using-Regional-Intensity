"""
embodied_carbon.py
==================
Module for calculating embodied carbon emissions from hardware manufacturing.
Includes telemetry for CPU, GPU, memory, and storage usage.

Embodied carbon represents the total GHG emissions from manufacturing, 
transporting, and disposing of hardware over its lifetime.
"""

import psutil
import time
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# =============================================================================
# EMBODIED CARBON CONSTANTS (kg CO2e)
# =============================================================================
# Source: "Estimating the Carbon Footprint of ICT" and various LCA studies

# Servers and Computing Hardware (kg CO2e total manufacturing emissions)
EMBODIED_CARBON = {
    # CPUs (per unit)
    "cpu_server": 100.0,      # High-end server CPU (e.g., Intel Xeon, AMD EPYC)
    "cpu_desktop": 50.0,      # Desktop CPU
    "cpu_mobile": 20.0,       # Mobile/laptop CPU
    
    # GPUs (per unit)
    "gpu_datacenter": 150.0,  # NVIDIA A100, H100, etc.
    "gpu_consumer": 75.0,     # Consumer GPU (RTX 3080, etc.)
    "gpu_mobile": 30.0,       # Mobile GPU
    
    # Memory (per GB)
    "ram_ddr4": 5.0,          # DDR4 RAM per GB
    "ram_ddr5": 6.0,          # DDR5 RAM per GB
    
    # Storage (per GB)
    "ssd_nvme": 0.16,         # NVMe SSD per GB
    "ssd_sata": 0.12,         # SATA SSD per GB
    "hdd": 0.04,              # HDD per GB
    
    # Complete Server
    "server_1u": 500.0,       # 1U server (total)
    "server_2u": 800.0,       # 2U server (total)
}

# Expected hardware lifetime (years)
HARDWARE_LIFETIME = {
    "cpu": 5.0,
    "gpu": 4.0,
    "ram": 5.0,
    "storage": 5.0,
    "server": 5.0,
}

# Hardware specifications for different instance types
INSTANCE_SPECS = {
    "cloud_small": {
        "cpu_count": 2,
        "cpu_type": "cpu_server",
        "gpu_count": 0,
        "gpu_type": None,
        "ram_gb": 8,
        "ram_type": "ram_ddr4",
        "storage_gb": 100,
        "storage_type": "ssd_sata",
    },
    "cloud_medium": {
        "cpu_count": 4,
        "cpu_type": "cpu_server",
        "gpu_count": 0,
        "gpu_type": None,
        "ram_gb": 16,
        "ram_type": "ram_ddr4",
        "storage_gb": 200,
        "storage_type": "ssd_nvme",
    },
    "cloud_large": {
        "cpu_count": 8,
        "cpu_type": "cpu_server",
        "gpu_count": 0,
        "gpu_type": None,
        "ram_gb": 32,
        "ram_type": "ram_ddr5",
        "storage_gb": 500,
        "storage_type": "ssd_nvme",
    },
    "gpu_instance": {
        "cpu_count": 8,
        "cpu_type": "cpu_server",
        "gpu_count": 1,
        "gpu_type": "gpu_datacenter",
        "ram_gb": 64,
        "ram_type": "ram_ddr5",
        "storage_gb": 1000,
        "storage_type": "ssd_nvme",
    },
    "local_machine": {
        "cpu_count": psutil.cpu_count(logical=False) or 4,
        "cpu_type": "cpu_desktop",
        "gpu_count": 0,  # Will detect if available
        "gpu_type": "gpu_consumer",
        "ram_gb": round(psutil.virtual_memory().total / (1024**3)),
        "ram_type": "ram_ddr4",
        "storage_gb": 500,
        "storage_type": "ssd_nvme",
    }
}


class EmbodiedCarbonTracker:
    """
    Track and calculate embodied carbon emissions for hardware usage.
    """
    
    def __init__(self, instance_type: str = "local_machine", 
                 region: str = "Northern"):
        """
        Initialize embodied carbon tracker.
        
        Args:
            instance_type: Type of compute instance (cloud_small, cloud_medium, etc.)
            region: Data center region
        """
        self.instance_type = instance_type
        self.region = region
        self.specs = INSTANCE_SPECS.get(instance_type, INSTANCE_SPECS["local_machine"])
        self.start_time = None
        self.telemetry_data = []
        
    def calculate_total_embodied_carbon(self) -> float:
        """
        Calculate total embodied carbon for the hardware configuration.
        
        Returns:
            Total embodied carbon in kg CO2e
        """
        total = 0.0
        
        # CPU embodied carbon
        cpu_carbon = (EMBODIED_CARBON[self.specs["cpu_type"]] * 
                      self.specs["cpu_count"])
        total += cpu_carbon
        
        # GPU embodied carbon
        if self.specs["gpu_count"] > 0 and self.specs["gpu_type"]:
            gpu_carbon = (EMBODIED_CARBON[self.specs["gpu_type"]] * 
                         self.specs["gpu_count"])
            total += gpu_carbon
        
        # RAM embodied carbon
        ram_carbon = (EMBODIED_CARBON[self.specs["ram_type"]] * 
                     self.specs["ram_gb"])
        total += ram_carbon
        
        # Storage embodied carbon
        storage_carbon = (EMBODIED_CARBON[self.specs["storage_type"]] * 
                         self.specs["storage_gb"])
        total += storage_carbon
        
        return round(total, 3)
    
    def calculate_amortized_embodied_carbon(self, duration_hours: float) -> float:
        """
        Calculate amortized embodied carbon for a specific workload duration.
        
        Formula: (Total Embodied Carbon / Expected Lifetime Hours) × Duration
        
        Args:
            duration_hours: Workload duration in hours
            
        Returns:
            Amortized embodied carbon in g CO2e
        """
        total_embodied = self.calculate_total_embodied_carbon()
        
        # Average lifetime across all components (weighted by carbon footprint)
        avg_lifetime_years = 5.0  # Conservative estimate
        lifetime_hours = avg_lifetime_years * 365.25 * 24
        
        # Amortized carbon per hour
        carbon_per_hour = (total_embodied * 1000) / lifetime_hours  # Convert to grams
        
        # Carbon for this workload
        workload_carbon = carbon_per_hour * duration_hours
        
        return round(workload_carbon, 6)
    
    def collect_telemetry(self) -> Dict:
        """
        Collect real-time system telemetry (CPU, Memory, Disk, GPU if available).
        
        Returns:
            Dictionary with telemetry metrics
        """
        telemetry = {
            "timestamp": datetime.now().isoformat(),
            
            # CPU metrics
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_freq_current": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            
            # Memory metrics
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            
            # Disk metrics
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "disk_used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
        }
        
        # Try to get GPU info (requires additional libraries like pynvml)
        telemetry["gpu_available"] = False
        telemetry["gpu_count"] = 0
        telemetry["gpu_utilization"] = None
        telemetry["gpu_memory_used_gb"] = None
        
        try:
            import pynvml
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()
            telemetry["gpu_available"] = True
            telemetry["gpu_count"] = gpu_count
            
            if gpu_count > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                telemetry["gpu_utilization"] = gpu_util.gpu
                telemetry["gpu_memory_used_gb"] = round(gpu_mem.used / (1024**3), 2)
                telemetry["gpu_memory_total_gb"] = round(gpu_mem.total / (1024**3), 2)
            
            pynvml.nvmlShutdown()
        except (ImportError, Exception):
            # GPU monitoring not available
            pass
        
        return telemetry
    
    def start_tracking(self):
        """Start tracking a workload."""
        self.start_time = time.time()
        self.telemetry_data = []
        initial_telemetry = self.collect_telemetry()
        self.telemetry_data.append(initial_telemetry)
        return initial_telemetry
    
    def sample_telemetry(self):
        """Collect a telemetry sample during workload execution."""
        if self.start_time is None:
            raise RuntimeError("Tracking not started. Call start_tracking() first.")
        
        telemetry = self.collect_telemetry()
        self.telemetry_data.append(telemetry)
        return telemetry
    
    def stop_tracking(self) -> Dict:
        """
        Stop tracking and calculate final metrics including embodied carbon.
        
        Returns:
            Dictionary with complete metrics
        """
        if self.start_time is None:
            raise RuntimeError("Tracking not started. Call start_tracking() first.")
        
        end_time = time.time()
        duration_s = end_time - self.start_time
        duration_h = duration_s / 3600.0
        
        # Final telemetry
        final_telemetry = self.collect_telemetry()
        self.telemetry_data.append(final_telemetry)
        
        # Calculate embodied carbon
        total_embodied_carbon_kg = self.calculate_total_embodied_carbon()
        amortized_embodied_carbon_g = self.calculate_amortized_embodied_carbon(duration_h)
        
        # Aggregate telemetry statistics
        cpu_usage = [t["cpu_percent"] for t in self.telemetry_data]
        mem_usage = [t["memory_percent"] for t in self.telemetry_data]
        
        result = {
            "timestamp_start": datetime.fromtimestamp(self.start_time).isoformat(),
            "timestamp_end": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": round(duration_s, 4),
            "duration_hours": round(duration_h, 6),
            
            # Instance info
            "instance_type": self.instance_type,
            "region": self.region,
            "specs": self.specs,
            
            # Embodied carbon
            "total_embodied_carbon_kg": total_embodied_carbon_kg,
            "amortized_embodied_carbon_g": amortized_embodied_carbon_g,
            
            # Telemetry statistics
            "cpu_percent_avg": round(sum(cpu_usage) / len(cpu_usage), 2),
            "cpu_percent_max": round(max(cpu_usage), 2),
            "cpu_percent_min": round(min(cpu_usage), 2),
            
            "memory_percent_avg": round(sum(mem_usage) / len(mem_usage), 2),
            "memory_percent_max": round(max(mem_usage), 2),
            "memory_gb_avg": round(sum(t["memory_used_gb"] for t in self.telemetry_data) / len(self.telemetry_data), 2),
            
            "telemetry_samples": len(self.telemetry_data),
            "telemetry_history": self.telemetry_data,
        }
        
        return result


def estimate_total_carbon(duration_s: float, region: str = "Northern", 
                         instance_type: str = "local_machine",
                         operational_co2_g: Optional[float] = None) -> Dict:
    """
    Calculate total carbon emissions (operational + embodied).
    
    Args:
        duration_s: Workload duration in seconds
        region: Data center region
        instance_type: Type of compute instance
        operational_co2_g: Operational carbon from electricity (if already calculated)
        
    Returns:
        Dictionary with complete carbon footprint breakdown
    """
    tracker = EmbodiedCarbonTracker(instance_type, region)
    duration_h = duration_s / 3600.0
    
    # Calculate embodied carbon
    amortized_embodied_g = tracker.calculate_amortized_embodied_carbon(duration_h)
    total_embodied_kg = tracker.calculate_total_embodied_carbon()
    
    # If operational carbon not provided, estimate it
    if operational_co2_g is None:
        from estimator import estimate_co2
        _, operational_co2_g = estimate_co2(duration_s, region)
    
    # Total carbon
    total_co2_g = operational_co2_g + amortized_embodied_g
    
    # Calculate percentages
    operational_percent = (operational_co2_g / total_co2_g * 100) if total_co2_g > 0 else 0
    embodied_percent = (amortized_embodied_g / total_co2_g * 100) if total_co2_g > 0 else 0
    
    return {
        "duration_seconds": duration_s,
        "duration_hours": round(duration_h, 6),
        "region": region,
        "instance_type": instance_type,
        
        # Carbon emissions (grams)
        "operational_co2_g": round(operational_co2_g, 6),
        "embodied_co2_g": round(amortized_embodied_g, 6),
        "total_co2_g": round(total_co2_g, 6),
        
        # Percentages
        "operational_percent": round(operational_percent, 2),
        "embodied_percent": round(embodied_percent, 2),
        
        # Hardware info
        "total_embodied_carbon_kg": total_embodied_kg,
        "specs": tracker.specs,
    }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EMBODIED CARBON CALCULATOR - Demo")
    print("=" * 70)
    
    # Example 1: Calculate embodied carbon for different instance types
    print("\n📊 Hardware Embodied Carbon (Total Manufacturing):\n")
    for instance_type in ["cloud_small", "cloud_medium", "cloud_large", "gpu_instance", "local_machine"]:
        tracker = EmbodiedCarbonTracker(instance_type)
        total = tracker.calculate_total_embodied_carbon()
        print(f"  {instance_type:20s}: {total:8.2f} kg CO2e")
    
    # Example 2: Track a workload with telemetry
    print("\n" + "=" * 70)
    print("🔍 Tracking Sample Workload with Telemetry")
    print("=" * 70)
    
    tracker = EmbodiedCarbonTracker("local_machine", "Northern")
    
    # Start tracking
    print("\n⏱️  Starting workload...")
    tracker.start_tracking()
    
    # Simulate workload
    for i in range(3):
        time.sleep(1)
        sample = tracker.sample_telemetry()
        print(f"  Sample {i+1}: CPU {sample['cpu_percent']:.1f}% | RAM {sample['memory_percent']:.1f}%")
    
    # Stop and get results
    result = tracker.stop_tracking()
    
    print(f"\n✅ Workload Complete!")
    print(f"  Duration: {result['duration_seconds']:.2f} seconds")
    print(f"  Amortized Embodied Carbon: {result['amortized_embodied_carbon_g']:.6f} g CO2e")
    print(f"  Total Hardware Embodied: {result['total_embodied_carbon_kg']:.2f} kg CO2e")
    print(f"  CPU Usage (avg/max): {result['cpu_percent_avg']:.1f}% / {result['cpu_percent_max']:.1f}%")
    print(f"  Memory Usage (avg): {result['memory_gb_avg']:.2f} GB")
    
    # Example 3: Complete carbon footprint
    print("\n" + "=" * 70)
    print("🌍 Complete Carbon Footprint (Operational + Embodied)")
    print("=" * 70)
    
    total_carbon = estimate_total_carbon(
        duration_s=result['duration_seconds'],
        region="Northern",
        instance_type="local_machine"
    )
    
    print(f"\n  Operational Carbon: {total_carbon['operational_co2_g']:.6f} g CO2e ({total_carbon['operational_percent']:.1f}%)")
    print(f"  Embodied Carbon:    {total_carbon['embodied_co2_g']:.6f} g CO2e ({total_carbon['embodied_percent']:.1f}%)")
    print(f"  {'─' * 50}")
    print(f"  Total Carbon:       {total_carbon['total_co2_g']:.6f} g CO2e (100%)")
    
    print("\n" + "=" * 70)
