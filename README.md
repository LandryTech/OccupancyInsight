# OccupancyInsight
An automated occupancy monitoring and predictive modeling project for the Wentworth Institute of Technology Schumann Gym. This project addresses a real-world problem: determining gym occupancy levels to optimize workout scheduling. The system continuously collects occupancy and environmental data, which is now entering an active analysis phase to identify trends and prepare for predicitve modeling.

## Project Overview
OccupancyInsight monitors and logs occupancy data, weather conditions, and environmental metrics from the Wentworth gym to identify patterns and build predictive models. The system automatically collects data during the gym operating hours and stores it in a local SQLite database for later analysis and model training.

## Motivation
After more than a year of gym attendance, I identified a significant personal problem: the difficulty of determining when the gym would be crowded. This project transforms that observation into a practical machine learning application that can predict occupancy levels based on historical patterns and environmental factors.

## Current Phase: Data Collection & Analysis
🔵 **Status**: Active Data Collection  + Exploratory Analysis (In Progress | 3/17/2026)

This project is currently running on two parallel tracks:

- **Ongoing Collection**: Daily logging continues throughout the spring semester and beyond
- **Exploratory Analysis**: Initial trends and patterns are being identified from the collected dataset

**Collection Parameters**
- **Collecting Period**: Spring semeseter (excluding spring break), with continutation through end of semester and potentially beyond
- **Data Points**: Occupancy count, temperature, and precipitation
- **Frequency**: Every 15 minutes during gym operating hours (XX:00, XX:15, XX:30, XX:45)
- **Storage**: SQLite databse for reliable data persistence

---

## Analysis

The following visualiations represent early exploratory analysis on the collected dataset. Charts are generated from occupancy, temperature, and precipitation data logged since the start of the collection period.

### Occupancy Trends by Day of Week

Hourly occupancy trends broken down across all 7 days of the week. Each subplot represents a single day, plotted in 1-hour increments, allowing for direct day-to-day comparison of traffic patterns throughout the gym's operating hours.

![7-Day Occupancy Analysis](Analysis/7DayAnalysis.png)

---

### Occupancy Heatmap

A heatmap visualization of occupancy intensity across hours of the day and days of the week. Darker cells indicate higher average occupancy, providing an at-a-glance view of the busiest and quietest windows throughout the week.

![Occupancy Heatmap](Analysis/OccupancyHeatMap.png)

---

### Occupancy vs. Temperature vs. Precipitation

A multi-variable chart exploring the relationship between gym occupancy and environmental conditions. This visualization examines whether temperature and precipitations have a measurable influence on attendance behavior.

![Occupancy vs Temperature vs Precipitation](Analysis/OccupancyVsTemperature.png)

---

## Features
- **Automated Monitoring**: Runs continuously in the background during gym operationg hours
- **Environmental Data Integration**: Captures temperature and precipitation data via weather API
- **Persistent Storage**: SQLite database for efficient data management and future querying
- **Minimal Overhead**: Lightweight operation with task scheduling on Windows
- **Automated Scheduling**: Batch script integration with Windows Task Scheduler for hands-off operation

## Technical Stack
- **Primary Language**: Python
- **Data Storage**: SQLite
- **Weather Data**: Weather API (environment variable protected)
- **Planned ML Frameworks**: R, TensorFlow (to be learned and integrated during model development phase)
- **Automation**: Windows batch scripting + Task Scheduler
- **Environment**: Windows

---

## Installation & Setup
*Full setup instructions to be documented.*

### Prerequisites
- Python 3.8 or higher
- Active internet connection (for weather API)
- Weather API key (see Configuration section)

### Configuration
1. **Clone the repository**
   ```
   git clone https://github.com/LandryTech/OccupancyInsight.git
   cd OccupancyInsight
   ```
   
2. **Set up environment variables**
   Create a `.env` file in the project root directory with your weather API credentials
   https://openweathermap.org/api
   ```
   WEATHER_API_KEY = your_api_key_here
   ```
   
3. **Install dependencies**
*To be determined*

### Running the Project
*To be determined*

## Data Collection Process

The monitoring system follows this workflow:

1. **Data Acquisition**: Retrieves current occupancy count and environmental data
2. **Enrichment**: Fetches real-time weather metrics (temperature, precipitation)
3. **Logging**: Records timestamp, occupancy, and weather data to SQLite
4. **Archival**: Stores data for future analysis and model training

**Data Points Collected**
- Timestamp
- Occupancy count
- Temperature
- Precipitation


## Development Notes
**Code Attribution**: Portions of this codebase were engineered with assistance from Claude AI (Anthropic), with comprehensive review, testing, and customization by the project author. All code has been validated and modified to ensure functionality, reliability, and alignment with project objectives.

## Roadmap
### ✅ Phase 1: Data Collection (Active)
- Automated data logging during gym operating hours
- Environmental data integration via weather API
- SQLite storage and schema design

### 🔄 Phase 2: Exploratory Analysis (In Progress)
- Inital trend visualizations (occupancy by day, heatmaps, environmental correlations)
- Feature engineering and data preprocessing
- Dataset evaluation ahead of model training

### Phase 3: Model Development (TBD)
- [ ] Exploratory data analysis on collected dataset
- [ ] Feature engineering and data preprocessing
- [ ] Initial model baseline
- [ ] Model evalutation and parameter tuning

### Phase 4: Advanced Modeling (TBD)
- [ ] Experiment with R-based models
- [ ] Deep learning with Tensorflow
- [ ] Ensemble methods and optimization
- [ ] Production model selection

### Phase 5: Deployment & Release (TBD)
- [ ] Release anonymized/aggregated database
- [ ] Publish trained models
- [ ] API development for predictions
- [ ] Web interface or dashboard

## Learning Objectives
This project is also a personal learning vehicle for:
- Machine learning fundamentals and advanced techniques
- TensorFlow and neural network developement
- Data engineering and database management
- Time series analysis and forecasting
- Real-world application development

## Future Enhancements
As this project evolves, planned improvements include:
- Real-time prediction API
- Web dashboard for visualization
- Mobile application for occupancy queries
- Integration with additional data sources

## License
MIT License - See [License](LICENSE) for details

## Contact & Questions
For questions about this project, please open an issue on the Github repository

---
**Repository**: https://github.com/LandryTech/OccupancyInsight \
**Last Updated**: March 17th, 2026 \
**Project Phase**: Data Collection & Exploratory Analysis
