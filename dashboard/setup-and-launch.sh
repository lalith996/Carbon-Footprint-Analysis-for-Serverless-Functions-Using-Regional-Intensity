#!/bin/bash

# GreenAI MERN Dashboard - Complete Setup and Launch Script
# ===========================================================

set -e  # Exit on error

echo "🌱 GreenAI MERN Dashboard Setup"
echo "================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo "✅ npm found: $(npm --version)"
echo ""

# Navigate to dashboard directory
cd "$(dirname "$0")"

echo "📦 Installing server dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install server dependencies"
    exit 1
fi

echo "✅ Server dependencies installed"
echo ""

echo "📦 Installing client dependencies..."
cd client
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo "❌ Failed to install client dependencies"
    exit 1
fi

echo "✅ Client dependencies installed"
echo ""

cd ..

echo "🎨 Creating environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🚀 To start the dashboard:"
echo "   npm run dev"
echo ""
echo "   This will start:"
echo "   - Backend API: http://localhost:5000"
echo "   - Frontend UI: http://localhost:3000"
echo ""
echo "📚 For more information, see:"
echo "   - README.md"
echo "   - API documentation at /api/status"
echo ""
echo "Do you want to start the dashboard now? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "🚀 Starting GreenAI Dashboard..."
    echo ""
    npm run dev
else
    echo ""
    echo "👋 Run 'npm run dev' when you're ready to start!"
fi
