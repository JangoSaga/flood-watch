# FloodML - Machine Learning Flood Prediction System

A comprehensive flood prediction and analysis system built with Flask (ML backend) and Next.js (frontend). The system provides real-time flood predictions for 200+ Indian cities using machine learning algorithms and weather data analysis.

## 🌟 Features

### Backend (Flask + ML)
- **Flood Prediction API**: ML-powered flood risk assessment using Random Forest Classifier (98.71% accuracy)
- **Weather Data Integration**: Real-time weather data from Visual Crossing API
- **City Coverage**: Support for 200+ Indian cities with coordinates
- **Data Visualization APIs**: Endpoints for plots, heatmaps, and satellite imagery
- **RESTful API**: Clean API design with CORS support

### Frontend (Next.js)
- **Interactive Plots**: Map visualization of flood predictions across India
- **Heatmaps**: Damage analysis and flood risk intensity visualization
- **Satellite Data**: Precipitation analysis and satellite imagery
- **Real-time Predictions**: City-specific flood predictions with weather data
- **Modern UI**: Beautiful, responsive interface built with Tailwind CSS

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Node.js 16+
- Visual Crossing Weather API key (free)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd FloodML-master
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure API Key
1. Get a free API key from [Visual Crossing Weather API](https://www.visualcrossing.com/weather-api)
2. Run the setup script:
```bash
python setup.py
```
3. Edit the `.env` file and replace `your_api_key_here` with your actual API key

#### Run the Backend
```bash
python app.py
```
The backend will be available at `http://localhost:5000`

### 3. Frontend Setup

#### Install Node.js Dependencies
```bash
cd frontend/floodguard
npm install
```

#### Run the Frontend
```bash
npm run dev
```
The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
FloodML-master/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── setup.py              # Setup script
├── requirements.txt      # Python dependencies
├── model.pickle          # Trained ML model
├── finalfinal.csv        # City data with coordinates
├── training/             # ML training modules
│   ├── prediction.py     # Weather data fetching
│   └── train.py         # Model training
└── processed_satellite_images/  # Satellite imagery

frontend/floodguard/
├── app/                  # Next.js app directory
│   ├── page.tsx         # Homepage
│   ├── predict/         # Prediction page
│   ├── plots/           # Interactive plots
│   ├── heatmaps/        # Heatmap visualizations
│   └── satellite/       # Satellite data
├── components/          # React components
│   ├── ui/             # UI components
│   └── map-component.tsx # Map visualization
└── package.json        # Node.js dependencies
```

## 🔧 API Endpoints

### Backend APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predict` | POST | Get flood prediction for a city |
| `/api/plots` | GET | Get data for interactive plots |
| `/api/heatmaps` | GET | Get data for heatmap visualizations |
| `/api/cities` | GET | Get list of available cities |

### Example API Usage

#### Get Flood Prediction
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"city": "Mumbai"}'
```

#### Get Cities List
```bash
curl http://localhost:5000/api/cities
```

## 🧠 Machine Learning Model

- **Algorithm**: Random Forest Classifier
- **Accuracy**: 98.71%
- **Features**: Temperature, humidity, precipitation, wind speed, cloud cover
- **Data Source**: Historical flood data + weather data from Visual Crossing API
- **Coverage**: 200+ Indian cities

## 🎨 Frontend Features

### Interactive Plots
- Map-based visualization of flood predictions
- Color-coded risk assessment (green = safe, red = high risk)
- Real-time data from backend APIs

### Heatmaps
- Damage analysis visualization
- Flood risk intensity mapping
- Rainfall intensity analysis

### Predictions Page
- City selection from 200+ Indian cities
- Real-time weather data display
- ML-powered flood risk assessment
- Detailed weather parameters

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Visual Crossing Weather API Key
VISUAL_CROSSING_API_KEY=your_api_key_here

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
```

### API Key Setup
1. Visit [Visual Crossing Weather API](https://www.visualcrossing.com/weather-api)
2. Sign up for a free account
3. Get your API key
4. Add it to the `.env` file

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**
   - Ensure you have a valid Visual Crossing API key
   - Check the `.env` file configuration

2. **CORS Issues**
   - The backend includes CORS configuration
   - Ensure both frontend and backend are running

3. **Missing Dependencies**
   - Run `pip install -r requirements.txt` for backend
   - Run `npm install` for frontend

4. **Port Conflicts**
   - Backend runs on port 5000
   - Frontend runs on port 3000
   - Ensure these ports are available

### Debug Mode
Both applications run in debug mode by default:
- Backend: `python app.py`
- Frontend: `npm run dev`

## 📊 Data Sources

- **Weather Data**: Visual Crossing Weather API
- **Flood Data**: Historical flood records from floodlist.com
- **City Data**: 200+ Indian cities with coordinates
- **Satellite Data**: NASA Global Precipitation Measurement Project

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Visual Crossing for weather data API
- NASA for satellite precipitation data
- The open-source community for various libraries and tools

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

---

**Note**: This is a research project for flood prediction and analysis. Always verify predictions with official weather services for critical decisions.
