# GreenAI MERN Stack Dashboard

A professional, production-ready web application for exploring carbon-aware serverless scheduling research.

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18.0.0
- npm >= 9.0.0

### Installation

1. **Install server dependencies:**
```bash
cd dashboard
npm install
```

2. **Install client dependencies:**
```bash
npm run install-client
```

3. **Start development servers:**
```bash
npm run dev
```

This will start:
- Backend server on `http://localhost:5000`
- React frontend on `http://localhost:3000`

### Production Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
dashboard/
├── server.js           # Express backend
├── package.json        # Server dependencies
├── .env.example        # Environment variables template
└── client/            # React frontend
    ├── src/
    │   ├── components/    # React components
    │   ├── pages/         # Page components
    │   ├── services/      # API services
    │   ├── styles/        # CSS/Sass files
    │   └── App.js         # Main app component
    └── package.json       # Client dependencies
```

## 🎨 Features

### 🏠 Dashboard Home
- Real-time metrics
- Live carbon intensity
- Active task monitoring
- Strategy distribution charts

### 📊 Experiments Viewer
- Interactive data visualizations
- Experiment comparison
- Detailed metrics
- Publication-quality charts

### 🔮 Carbon Calculator
- Real-time emissions calculation
- Multi-strategy comparison
- Smart recommendations
- Interactive parameter adjustment

### 🗺️ Regional Map
- Interactive India map
- Regional carbon intensity
- Performance metrics
- Live updates

### 📈 Analytics
- Historical trends
- Performance tracking
- Statistical analysis
- Export capabilities

## 🛠️ Technology Stack

### Backend
- **Express.js** - Web framework
- **Node.js** - Runtime
- **CSV Parser** - Data processing
- **CORS** - Cross-origin requests

### Frontend
- **React** - UI library
- **Recharts** - Data visualization
- **Leaflet** - Interactive maps
- **Axios** - HTTP client
- **React Router** - Navigation
- **Styled Components** - Styling

## 📡 API Endpoints

### GET /api/status
Get overall project status

### GET /api/experiments/:id
Get experiment data (exp001-exp004)

### POST /api/calculate
Calculate carbon emissions
```json
{
  "duration": 4.0,
  "power": 100,
  "ci": 607,
  "serverAge": 2.0,
  "agingRate": 7.0,
  "strategies": ["operational_only", "embodied_prioritized"]
}
```

### GET /api/regions
Get regional performance data

### GET /api/metrics/live
Get real-time metrics (updates every 5s)

## 🎨 UI Components

### Dashboard Cards
- Status overview
- Key metrics
- Live updates
- Trend indicators

### Interactive Charts
- Line charts (time series)
- Bar charts (comparisons)
- Pie charts (distributions)
- Heatmaps (boundaries)

### Regional Map
- Interactive markers
- Color-coded regions
- Tooltips with details
- Zoom & pan controls

### Calculator Form
- Slider inputs
- Strategy selector
- Real-time results
- Visual feedback

## 🔧 Development

### Running Tests
```bash
cd client
npm test
```

### Building for Production
```bash
npm run build
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
```
NODE_ENV=production
PORT=5000
```

## 📦 Deployment

### Heroku
```bash
heroku create greenai-dashboard
git push heroku master
```

### Docker
```bash
docker build -t greenai-dashboard .
docker run -p 5000:5000 greenai-dashboard
```

### Vercel (Frontend Only)
```bash
cd client
vercel
```

## 🎓 For Researchers

All API endpoints return research data from completed experiments:
- EXP-001: CI Threshold (322 gCO₂/kWh)
- EXP-002: Regional Matrix (4 regions)
- EXP-003: Duration Sensitivity (14.8% penalty)
- EXP-004: Aging Sensitivity (7.2%/year)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - Academic Research Project

## 🙏 Acknowledgments

- React team for amazing framework
- Recharts for visualization library
- Leaflet for mapping capabilities
- Indian Grid for regional data

---

**Built with ❤️ for sustainable computing research**
