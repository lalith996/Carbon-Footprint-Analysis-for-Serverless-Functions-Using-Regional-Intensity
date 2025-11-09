#!/bin/bash

# GreenAI Dashboard Setup Script
# Creates all necessary React components and pages

echo "🌱 Setting up GreenAI Dashboard Components..."

cd "$(dirname "$0")"

# Create directories
mkdir -p src/components
mkdir -p src/pages
mkdir -p src/services
mkdir -p src/styles

echo "✅ Directories created"

# Create components files
touch src/components/Navbar.js
touch src/components/StatCard.js
touch src/components/LiveMetrics.js
touch src/components/ExperimentCard.js
touch src/components/ChartContainer.js

# Create pages files
touch src/pages/Dashboard.js
touch src/pages/Experiments.js
touch src/pages/Calculator.js
touch src/pages/RegionalMap.js
touch src/pages/Analytics.js

# Create services files
touch src/services/api.js

echo "✅ Component files created"
echo "🎨 Ready for component implementation"
