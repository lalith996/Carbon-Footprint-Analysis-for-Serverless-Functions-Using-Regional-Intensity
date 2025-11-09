const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs-extra');
const csv = require('csv-parser');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Helper function to read CSV files
const readCSV = (filePath) => {
  return new Promise((resolve, reject) => {
    const results = [];
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (data) => results.push(data))
      .on('end', () => resolve(results))
      .on('error', (error) => reject(error));
  });
};

// API Routes

// Get project status
app.get('/api/status', (req, res) => {
  res.json({
    experiments: {
      total: 4,
      completed: 4,
      percentage: 100
    },
    tasks: {
      total: 14824,
      runtime: 2.2
    },
    thresholds: {
      ci: 321.9,
      aging: 7.2
    },
    status: 'ready_for_publication'
  });
});

// Get experiment data
app.get('/api/experiments/:id', async (req, res) => {
  const { id } = req.params;
  
  try {
    let data = {};
    
    switch(id) {
      case 'exp001':
        const ciData = await readCSV(path.join(__dirname, '../threshold_precise/precise_results.csv'));
        data = {
          id: 'exp001',
          name: 'CI Threshold Mapping',
          status: 'complete',
          threshold: 321.9,
          tasks: 7200,
          runtime: 0.5,
          data: ciData
        };
        break;
        
      case 'exp002':
        const regionalData = await readCSV(path.join(__dirname, '../regional_matrix/regional_matrix.csv'));
        data = {
          id: 'exp002',
          name: 'Regional Performance Matrix',
          status: 'complete',
          regions: 4,
          tasks: 2400,
          runtime: 0.7,
          data: regionalData
        };
        break;
        
      case 'exp003':
        const durationData = await readCSV(path.join(__dirname, '../duration_sensitivity_publication/duration_summary.csv'));
        data = {
          id: 'exp003',
          name: 'Duration Sensitivity',
          status: 'complete',
          penalty: 14.8,
          tasks: 24,
          runtime: 0.5,
          data: durationData
        };
        break;
        
      case 'exp004':
        const agingData = await readCSV(path.join(__dirname, '../hardware_age_sensitivity/aging_sensitivity.csv'));
        data = {
          id: 'exp004',
          name: 'Hardware Age Sensitivity',
          status: 'complete',
          threshold: 7.2,
          tasks: 4800,
          runtime: 0.5,
          data: agingData
        };
        break;
        
      default:
        return res.status(404).json({ error: 'Experiment not found' });
    }
    
    res.json(data);
  } catch (error) {
    console.error('Error reading experiment data:', error);
    res.status(500).json({ error: 'Failed to load experiment data' });
  }
});

// Carbon calculator API
app.post('/api/calculate', (req, res) => {
  const { duration, power, ci, serverAge, agingRate, strategies } = req.body;
  
  const PUE = 1.58;
  const EMBODIED_CARBON_KG = 1200.0;
  
  const results = strategies.map(strategy => {
    // Determine server age based on strategy
    let age = serverAge;
    if (strategy === 'operational_only') age = 0.5;
    if (strategy === 'embodied_prioritized') age = 4.0;
    if (strategy === 'balanced') age = 2.5;
    
    // Calculate aging factor
    const ageFactor = 1.0 + (agingRate / 100) * age;
    const adjustedPower = power * ageFactor;
    
    // Operational carbon
    const energyKwh = (adjustedPower * duration) / 1000.0;
    const operationalG = energyKwh * ci * PUE;
    
    // Embodied carbon (linear amortization over 5 years)
    const embodiedG = (EMBODIED_CARBON_KG * 1000.0 / (5 * 365 * 24)) * duration;
    
    const totalG = operationalG + embodiedG;
    const embodiedPct = (embodiedG / totalG) * 100;
    
    return {
      strategy,
      total_g: parseFloat(totalG.toFixed(2)),
      operational_g: parseFloat(operationalG.toFixed(2)),
      embodied_g: parseFloat(embodiedG.toFixed(2)),
      embodied_pct: parseFloat(embodiedPct.toFixed(2)),
      adjusted_power: parseFloat(adjustedPower.toFixed(2))
    };
  });
  
  // Determine recommendation
  const bestStrategy = results.reduce((min, curr) => 
    curr.total_g < min.total_g ? curr : min
  );
  
  const recommendation = {
    strategy: bestStrategy.strategy,
    reason: ci < 322 
      ? 'Clean grid detected. Embodied-aware strategies may be beneficial.'
      : 'Dirty grid detected. Operational-only strategy recommended.'
  };
  
  res.json({
    results,
    recommendation,
    metadata: {
      ci_threshold: 322,
      aging_threshold: 7.2,
      your_ci: ci,
      your_aging: agingRate
    }
  });
});

// Get regional data
app.get('/api/regions', (req, res) => {
  res.json({
    regions: [
      {
        name: 'Northern',
        ci: 535,
        penalty: 12.1,
        recommendation: 'operational_only',
        coordinates: { lat: 28.7041, lng: 77.1025 }
      },
      {
        name: 'Southern',
        ci: 607,
        penalty: 14.7,
        recommendation: 'operational_only',
        coordinates: { lat: 13.0827, lng: 80.2707 }
      },
      {
        name: 'Western',
        ci: 712,
        penalty: 17.7,
        recommendation: 'operational_only',
        coordinates: { lat: 19.0760, lng: 72.8777 }
      },
      {
        name: 'Eastern',
        ci: 813,
        penalty: 19.9,
        recommendation: 'operational_only',
        coordinates: { lat: 22.5726, lng: 88.3639 }
      }
    ]
  });
});

// Get live metrics (simulated real-time data)
app.get('/api/metrics/live', (req, res) => {
  const now = Date.now();
  const metrics = {
    timestamp: now,
    current_ci: 607 + Math.sin(now / 10000) * 50, // Simulated fluctuation
    active_tasks: Math.floor(Math.random() * 1000) + 500,
    carbon_saved: Math.floor(Math.random() * 10000) + 50000,
    efficiency: 85 + Math.random() * 10,
    regions_active: 4,
    strategy_distribution: {
      operational_only: 75,
      embodied_prioritized: 15,
      balanced: 10
    }
  };
  
  res.json(metrics);
});

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
  });
}

app.listen(PORT, () => {
  console.log(`🚀 GreenAI Server running on port ${PORT}`);
  console.log(`📊 API available at http://localhost:${PORT}/api`);
});
