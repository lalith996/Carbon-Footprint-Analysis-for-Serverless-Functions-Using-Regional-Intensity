# 🌍 Carbon Footprint Analysis for Serverless Functions Using Regional Carbon Intensity

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

## 📖 Overview

A comprehensive **carbon-aware cloud workload scheduling system** that optimizes serverless function placement across Indian data center regions to minimize **both operational and embodied carbon emissions** while maintaining SLA requirements.

### Key Innovation
- ⚡ **Real-time carbon intensity tracking** via ElectricityMap API
- 🤖 **ML-based carbon prediction** using Linear Regression and LSTM models
- 🔬 **Embodied carbon calculation** from hardware manufacturing
- 📊 **Complete carbon footprint** analysis (operational + embodied)
- 🌐 **Multi-region scheduling** across Northern, Western, Southern, and Eastern India

---

## 🎯 Features

### Carbon Tracking
- ✅ Real-time operational carbon from electricity consumption
- ✅ Embodied carbon from hardware manufacturing (CPUs, GPUs, RAM, Storage)
- ✅ Total carbon footprint = Operational + Embodied
- ✅ Regional carbon intensity monitoring (5-minute resolution)
- ✅ Hybrid estimation (70% live + 30% historical data)

### Scheduling Strategies
1. **Baseline** - Fixed region scheduling (control group)
2. **Reactive** - Live carbon intensity-based scheduling
3. **Predictive** - ML-based carbon forecasting with scheduling

### Machine Learning Models
- **Linear Regression (Ridge)** - Fast, interpretable CI predictions
- **LSTM Neural Network** - Deep learning for complex patterns
- **Feature Engineering** - 12 lags, rolling windows, cyclical time encoding

### Telemetry & Monitoring
- 🖥️ CPU usage (average, peak, core count)
- 💾 Memory usage (GB, percentage, delta)
- 🎮 GPU metrics (utilization, memory - if available)
- 💿 Disk usage tracking
- ⏱️ Duration and energy consumption

---

## 📁 Project Structure

```
GreenAI_Project/
├── 📊 Data/                          # Carbon intensity datasets
│   ├── IN-NO_2024_5_minute.csv     # Northern region data
│   ├── IN-WE_2024_5_minute.csv     # Western region data
│   ├── IN-SO_2024_5_minute.csv     # Southern region data
│   ├── IN-EA_2024_5_minute.csv     # Eastern region data
│   ├── data_clean/                  # Cleaned datasets
│   │   └── features/                # Engineered features
│   └── results*.csv                 # Experiment results
│
├── 🤖 Models/                        # Trained ML models
│   ├── northern_lr_fixed.joblib     # Linear Regression model
│   ├── northern_lstm.h5             # LSTM model
│   └── northern_scaler.joblib       # Feature scaler
│
├── 📈 experiment_results/            # Analysis outputs
│   ├── experiment_log.csv           # Experiment tracking
│   ├── embodied_carbon_analysis.png # Visualizations
│   └── telemetry_timeline.png       # Telemetry charts
│
├── 🔧 Core Modules
│   ├── estimator.py                 # CO₂ estimation engine
│   ├── embodied_carbon.py           # Embodied carbon calculator ⭐
│   ├── scheduler.py                 # Reactive scheduler
│   ├── scheduler_using_lr.py        # Predictive scheduler
│   ├── features.py                  # Feature engineering
│   ├── predictor_interface.py       # ML model interface
│   ├── lr_model.py                  # Linear Regression trainer
│   └── lstm_model.py                # LSTM trainer
│
├── 🚀 Execution
│   ├── serverless_task.py           # Basic workload simulator
│   ├── serverless_task_enhanced.py  # Enhanced with telemetry ⭐
│   ├── run_experiments.py           # Experiment orchestrator
│   ├── analyze_experiments.py       # Results analyzer
│   ├── analyze_embodied_carbon.py   # Carbon analysis ⭐
│   └── analyze_and_plot.py          # Visualization tool
│
├── 🐳 Deployment
│   ├── Dockerfile                   # Container configuration
│   ├── requirements.txt             # Python dependencies
│   └── .dockerignore                # Docker ignore rules
│
└── 📚 Documentation
    ├── README.md                    # This file
    └── EMBODIED_CARBON_GUIDE.md     # Embodied carbon guide ⭐
```

⭐ = New embodied carbon features

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip package manager
- Optional: Docker for containerized deployment
- Optional: nvidia-ml-py3 for GPU tracking

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/lalith996/Carbon-Footprint-Analysis-for-Serverless-Functions-Using-Regional-Intensity.git
cd Carbon-Footprint-Analysis-for-Serverless-Functions-Using-Regional-Intensity
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set API key (optional)**
```bash
export ELECTRICITYMAP_API_KEY="your_api_key_here"
```

### Basic Usage

#### 1. Test Embodied Carbon Calculator
```bash
python embodied_carbon.py
```

#### 2. Run Enhanced Workload with Telemetry
```bash
# Simple run
python serverless_task_enhanced.py --scale 400000 --enhanced

# Specify region and instance type
python serverless_task_enhanced.py \
  --scale 800000 \
  --region Northern \
  --instance cloud_medium \
  --enhanced
```

#### 3. Run Full Experiments
```bash
python run_experiments.py
```

#### 4. Analyze Results
```bash
# Analyze enhanced results with embodied carbon
python analyze_embodied_carbon.py

# Analyze experiment strategies
python analyze_experiments.py
```

---

## 📊 Results & Analysis

### Carbon Emissions Breakdown

Our experiments show:
- **Operational Carbon**: ~75% (from electricity consumption)
- **Embodied Carbon**: ~25% (from hardware manufacturing)

**Key Insight**: Embodied carbon represents a significant 25% of total emissions and cannot be ignored in carbon-aware computing!

### Instance Comparison

| Instance Type | Total Embodied | Amortized Cost/Hour |
|--------------|----------------|---------------------|
| cloud_small | 252 kg CO₂e | 5.75 g/hr |
| cloud_medium | 512 kg CO₂e | 11.68 g/hr |
| cloud_large | 1,072 kg CO₂e | 24.46 g/hr |
| gpu_instance | 1,494 kg CO₂e | 34.09 g/hr |

### Sample Output

```json
{
  "region": "Northern",
  "duration_s": 0.1434,
  "operational_co2_g": 0.001626,
  "embodied_co2_g": 0.000466,
  "total_co2_g": 0.002092,
  "operational_percent": 77.7,
  "embodied_percent": 22.3,
  "cpu_percent_avg": 12.5,
  "memory_used_gb_avg": 5.85
}
```

---

## 🧪 Scheduling Strategies

### 1. Baseline Strategy
- Fixed region selection (Northern)
- No carbon awareness
- Control group for comparisons

### 2. Reactive Strategy
- Real-time carbon intensity monitoring
- Dynamic region selection
- SLA-aware (latency constraints)
- Scoring: `0.7×CO₂ + 0.2×latency + 0.1×cost`

### 3. Predictive Strategy (ML-Based)
- Linear Regression for CI forecasting
- Combines live + predicted carbon intensity
- Proactive scheduling decisions
- Better for workloads with flexibility

---

## 📈 Machine Learning Pipeline

### Data Processing
1. **Collection**: Historical 5-minute CI data from ElectricityMap
2. **Cleaning**: Handle missing values, outliers
3. **Feature Engineering**:
   - 12 lag features (past hour)
   - Rolling means (3 and 12 windows)
   - Cyclical time encoding (hour_sin, hour_cos, minute_sin, minute_cos)

### Models

#### Linear Regression (Ridge)
```python
# Train model
python lr_model.py

# Performance: MAE, RMSE, R² score
# Fast inference: <1ms prediction time
```

#### LSTM Neural Network
```python
# Train model
python lstm_model.py

# Architecture: 64 LSTM → Dropout → Dense(32) → Output
# Sequence length: 12 timesteps (1 hour)
```

---

## 🌍 Regional Data

### Indian Grid Regions

| Region | Zone Code | Avg Latency | Cost Factor |
|--------|-----------|-------------|-------------|
| Northern | IN-NO | 70ms | 3.0 |
| Western | IN-WE | 90ms | 2.8 |
| Southern | IN-SO | 80ms | 3.2 |
| Eastern | IN-EA | 120ms | 2.5 |

### Carbon Intensity Sources
- **Live**: ElectricityMap API (5-min updates)
- **Historical**: Stored CSV datasets
- **Hybrid**: 70% live + 30% historical

---

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t greenai-carbon-scheduler .
```

### Run Container
```bash
docker run -p 5000:5000 \
  -e ELECTRICITYMAP_API_KEY="your_key" \
  greenai-carbon-scheduler
```

### Environment Variables
- `ELECTRICITYMAP_API_KEY` - API key for carbon intensity data
- `MODEL_PATH` - Path to trained models (default: /app/models)
- `DATA_PATH` - Path to data files (default: /app/data_clean)

---

## 📚 API Reference

### Embodied Carbon Tracker

```python
from embodied_carbon import EmbodiedCarbonTracker

# Initialize tracker
tracker = EmbodiedCarbonTracker("cloud_medium", "Northern")

# Start tracking
tracker.start_tracking()

# Run workload
do_work()

# Sample telemetry periodically
tracker.sample_telemetry()

# Stop and get results
result = tracker.stop_tracking()
print(f"Total CO₂: {result['total_co2_g']:.6f} g")
```

### Total Carbon Estimation

```python
from embodied_carbon import estimate_total_carbon

total = estimate_total_carbon(
    duration_s=15.5,
    region="Northern",
    instance_type="cloud_medium",
    operational_co2_g=0.05  # Optional
)

print(f"Operational: {total['operational_percent']:.1f}%")
print(f"Embodied: {total['embodied_percent']:.1f}%")
```

---

## 🔬 Research Applications

### Use Cases
1. **Carbon-Aware Scheduling** - Optimize workload placement
2. **Sustainability Research** - Measure and reduce cloud carbon footprint
3. **Green Computing** - Educational tool for sustainable computing
4. **Policy Making** - Data-driven decisions for data center locations
5. **Cost Optimization** - Balance carbon, latency, and cost

### Publications
This project supports research in:
- Sustainable Cloud Computing
- Green AI and ML
- Carbon-Aware Systems
- Edge and Fog Computing
- Serverless Architectures

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
# Fork the repository
git clone https://github.com/YOUR_USERNAME/Carbon-Footprint-Analysis-for-Serverless-Functions-Using-Regional-Intensity.git

# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and commit
git commit -m "Add amazing feature"

# Push to your fork
git push origin feature/amazing-feature

# Open a Pull Request
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Lalith Machavarapu** - [GitHub](https://github.com/lalith996)
- **Avinash Pala** - [GitHub](https://github.com/avinashpala19)

---

## 🙏 Acknowledgments

- **ElectricityMap** for real-time carbon intensity data
- **TensorFlow** and **scikit-learn** for ML frameworks
- **psutil** for system telemetry
- Various LCA studies for embodied carbon data
- Open source community

---

## 📧 Contact

For questions or collaboration:
- Create an issue on GitHub
- Email: [Your email if you want to add]

---

## 🔗 Related Projects

- [CodeCarbon](https://github.com/mlco2/codecarbon) - Track and reduce CO₂ emissions of ML
- [Green Algorithms](http://www.green-algorithms.org/) - Carbon footprint of computational work
- [Cloud Carbon Footprint](https://www.cloudcarbonfootprint.org/) - Cloud emissions tracking

---

## 📖 Citation

If you use this project in your research, please cite:

```bibtex
@software{greenai_carbon_scheduler,
  author = {Machavarapu, Lalith and Pala, Avinash},
  title = {Carbon Footprint Analysis for Serverless Functions Using Regional Carbon Intensity},
  year = {2025},
  url = {https://github.com/lalith996/Carbon-Footprint-Analysis-for-Serverless-Functions-Using-Regional-Intensity}
}
```

---

## 🎯 Roadmap

- [ ] Add support for more global regions
- [ ] Real-time dashboard for carbon monitoring
- [ ] Integration with major cloud providers (AWS, Azure, GCP)
- [ ] Automated model retraining pipeline
- [ ] REST API for carbon estimation
- [ ] Mobile app for carbon tracking
- [ ] Support for more hardware types
- [ ] Cost vs Carbon trade-off analysis

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with 💚 for a sustainable future**
