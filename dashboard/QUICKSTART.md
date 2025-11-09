# 🚀 Quick Start - GreenAI MERN Dashboard

## One-Command Setup & Launch

```bash
cd dashboard
chmod +x setup-and-launch.sh
./setup-and-launch.sh
```

That's it! The script will:
1. ✅ Check prerequisites (Node.js 18+)
2. ✅ Install server dependencies
3. ✅ Install client dependencies  
4. ✅ Create environment file
5. ✅ Start both servers

## What You Get

### 🖥️ Backend API Server
- **Port**: 5000
- **URL**: http://localhost:5000
- **Endpoints**: `/api/status`, `/api/experiments/:id`, `/api/calculate`, `/api/regions`, `/api/metrics/live`

### 🎨 Frontend React App
- **Port**: 3000
- **URL**: http://localhost:3000
- **Modern UI** with animations, responsive design, dark theme

## Dashboard Features

### 🏠 Home Dashboard (/)
- **Live Metrics**: Real-time carbon intensity, active tasks, carbon saved
- **Status Cards**: 4 experiments, 14,824 tasks, thresholds
- **Quick Stats**: Visual KPIs with trend indicators
- **Recent Activity**: Latest calculations and updates

### 🔬 Experiments (/experiments)
- **EXP-001**: CI Threshold (322 gCO₂/kWh) with interactive charts
- **EXP-002**: Regional Matrix (4 Indian regions) with comparison views
- **EXP-003**: Duration Sensitivity (14.8% constant penalty)
- **EXP-004**: Hardware Age (7.2%/year threshold)
- **Interactive Charts**: Recharts library with zoom, hover, export
- **Data Tables**: Sortable, filterable experiment data

### 🔮 Calculator (/calculator)
- **Real-time Calculations**: Instant carbon emissions
- **Parameters**:
  - Task Duration: 0.001 - 24 hours
  - Power: 10 - 300W
  - Grid CI: 50 - 1000 gCO₂/kWh
  - Server Age: 0.1 - 5 years
  - Aging Rate: 0 - 30%/year
- **Strategy Comparison**: Side-by-side results
- **Smart Recommendations**: Based on CI and aging thresholds
- **Visual Breakdown**: Operational vs embodied carbon

### 🗺️ Regional Map (/regional-map)
- **Interactive India Map**: Leaflet.js powered
- **4 Regions**: Northern, Southern, Eastern, Western
- **Color-coded Markers**: Based on CI intensity
- **Click for Details**: Popup with metrics and recommendations
- **Real-time Updates**: Simulated live data

### 📈 Analytics (/analytics)
- **Historical Trends**: Time-series charts
- **Performance Comparison**: Strategy effectiveness
- **Statistical Analysis**: P-values, confidence intervals
- **Export Options**: CSV, JSON, PDF reports
- **Custom Date Ranges**: Filter by time period

## Tech Stack Highlights

### Backend
- ✅ **Express.js** - Fast, minimalist web framework
- ✅ **CSV Parser** - Direct experimental data access
- ✅ **CORS** - Cross-origin resource sharing
- ✅ **RESTful API** - Clean, semantic endpoints

### Frontend  
- ✅ **React 19** - Latest React features
- ✅ **React Router** - Client-side routing
- ✅ **Styled Components** - CSS-in-JS styling
- ✅ **Recharts** - Beautiful, responsive charts
- ✅ **Leaflet** - Interactive maps
- ✅ **Framer Motion** - Smooth animations
- ✅ **React Icons** - Icon library
- ✅ **Axios** - HTTP client

## Manual Setup (Alternative)

If you prefer step-by-step:

```bash
# 1. Install server dependencies
cd dashboard
npm install

# 2. Install client dependencies
cd client
npm install --legacy-peer-deps

# 3. Create environment file
cd ..
cp .env.example .env

# 4. Start development servers
npm run dev
```

## Available Scripts

### Development
```bash
npm run dev          # Start both servers concurrently
npm start            # Start backend only
npm run client       # Start frontend only
```

### Production
```bash
npm run build        # Build React app for production
npm start            # Serve production build
```

### Maintenance
```bash
npm run install-client  # Reinstall client dependencies
npm test               # Run tests (client)
```

## Project Structure

```
dashboard/
├── server.js                 # Express backend
├── package.json              # Server dependencies
├── .env                      # Environment variables
├── setup-and-launch.sh       # Setup script
└── client/                   # React frontend
    ├── public/               # Static assets
    ├── src/
    │   ├── components/       # Reusable components
    │   │   ├── Navbar.js
    │   │   ├── StatCard.js
    │   │   ├── LiveMetrics.js
    │   │   └── ...
    │   ├── pages/            # Route pages
    │   │   ├── Dashboard.js
    │   │   ├── Experiments.js
    │   │   ├── Calculator.js
    │   │   ├── RegionalMap.js
    │   │   └── Analytics.js
    │   ├── services/         # API services
    │   │   └── api.js
    │   ├── App.js            # Main app component
    │   └── index.js          # Entry point
    └── package.json          # Client dependencies
```

## API Examples

### Get Project Status
```bash
curl http://localhost:5000/api/status
```

Response:
```json
{
  "experiments": {
    "total": 4,
    "completed": 4,
    "percentage": 100
  },
  "tasks": {
    "total": 14824,
    "runtime": 2.2
  },
  "thresholds": {
    "ci": 321.9,
    "aging": 7.2
  }
}
```

### Calculate Carbon Emissions
```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 4,
    "power": 100,
    "ci": 607,
    "serverAge": 2,
    "agingRate": 7,
    "strategies": ["operational_only", "embodied_prioritized"]
  }'
```

### Get Regional Data
```bash
curl http://localhost:5000/api/regions
```

### Get Live Metrics
```bash
curl http://localhost:5000/api/metrics/live
```

## UI Design Philosophy

### 🎨 Modern & Professional
- **Gradient Backgrounds**: Purple-blue gradients
- **Glass-morphism**: Frosted glass effects
- **Smooth Animations**: Framer Motion transitions
- **Responsive Design**: Mobile-first approach
- **Dark Theme**: Easy on eyes, professional

### 🚀 Performance
- **Code Splitting**: Lazy-loaded routes
- **Optimized Renders**: React.memo, useMemo
- **Compressed Assets**: Minimized bundle size
- **CDN Ready**: Static asset optimization

### ♿ Accessibility
- **Semantic HTML**: Proper element usage
- **ARIA Labels**: Screen reader support
- **Keyboard Navigation**: Tab-friendly
- **Color Contrast**: WCAG AA compliant

## Troubleshooting

### Port Already in Use
```bash
# Change server port
# Edit .env: PORT=5001

# Change client port
# Edit client/package.json: 
# "start": "PORT=3001 react-scripts start"
```

### Module Not Found
```bash
cd dashboard
rm -rf node_modules package-lock.json
npm install

cd client
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### API Connection Failed
- Check backend is running on port 5000
- Verify proxy in `client/package.json`: `"proxy": "http://localhost:5000"`
- Check CORS settings in `server.js`

### Charts Not Rendering
```bash
cd client
npm install --legacy-peer-deps recharts
```

### Map Not Loading
```bash
cd client  
npm install --legacy-peer-deps leaflet react-leaflet
```

Add to `client/public/index.html`:
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
```

## Next Steps

1. ✅ **Explore the Dashboard**: Open http://localhost:3000
2. ✅ **Try the Calculator**: Calculate your workload's carbon
3. ✅ **View Experiments**: See all research results
4. ✅ **Check Regional Map**: Explore Indian regions
5. ✅ **Analyze Data**: Dive into analytics

## Production Deployment

### Heroku
```bash
git init
heroku create greenai-dashboard
git add .
git commit -m "Initial commit"
git push heroku master
```

### Vercel (Frontend Only)
```bash
cd client
npx vercel
```

### Docker
```bash
# Coming soon - Dockerfile included in repo
docker-compose up
```

## Support

- 📖 Full Documentation: `README.md`
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: [Your Email]

---

**🌱 Built with ❤️ for sustainable computing**

*Ready to explore carbon-aware scheduling!*
