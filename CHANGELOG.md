# 📄 Changelog

All notable changes to **EnviroCheck – Climate Intelligence System** are documented here.
This project follows semantic versioning.

---

## [1.0.0] – Initial Release

### 🔹 Data Integration

* Integrated real-time environmental data using:

  * OpenWeatherMap API (temperature, humidity, rainfall)
  * WAQI API (Air Quality Index)
* Implemented centralized data pipeline using `data_fetcher.py`

### 🔹 Location Intelligence

* Developed location classification system:

  * Industrial, Traffic, Coastal, Urban zones
* Dynamic AQI adjustment based on environmental context

---

## [1.1.0] – Risk Analysis Engine

### ⚠ Risk Engine (`risk_engine.py`)

* Implemented threshold-based environmental risk detection:

  * Heat Risk:

    * Moderate > 32°C
    * High > 38°C
  * Flood Risk:

    * Moderate > 3 mm rainfall
    * Critical > 10 mm rainfall
  * Air Quality Risk:

    * Moderate > AQI 80
    * Unhealthy > AQI 150

### 🔹 Overall Risk Scoring

* Combined multi-factor risks into a unified severity level:

  * Low / Moderate / High

---

## [1.2.0] – Dashboard & Visualization

### 📊 Dashboard Interface (`app.py`)

* Built modern Streamlit UI with:

  * Climate cards (temperature, AQI, humidity, rainfall)
  * Dark theme with custom CSS
* Integrated real-time updates and responsive layout

### 🌊 Flood Risk Map

* Implemented dynamic **Leaflet.js map**
* Risk levels based on rainfall thresholds:

  * Safe → Low → Moderate → Flood Risk
* Interactive popup with environmental details

---

## [1.3.0] – Indoor Climate & Sensor Simulation

### 🏢 Indoor Climate Module

* Simulated indoor temperature using:

  * AC behavior (office hours logic)
  * Outdoor temperature influence
* Comfort classification:

  * Too Cold / Comfortable / Warm / Hot

### 🔹 Sensor Fusion

* Combined:

  * API data
  * Simulated local sensors
* Generated corrected environmental values using:

  * Vegetation index
  * Urban heat island effect
  * Traffic pollution factors

---

## [1.4.0] – NEXUS Intelligence Engine Integration

### 🧠 Predictive Intelligence (`nexus_full.py`)

* Implemented multi-layer AI reasoning system:

  * **Natural Calamities**

    * Urban flood prediction based on drainage overflow
  * **Infrastructure Risks**

    * Dew point–based condensation detection
  * **Health Risks**

    * Heat index → cognitive decline prediction
    * Pressure drop → migraine prediction
  * **Environmental Effects**

    * Humidity → fabric drying failure
    * Temperature → food spoilage acceleration

### 🌊 Flood Modeling

* Drainage capacity model:

  * Overflow = rainfall – threshold (20 mm)
* Predicts real-world urban flooding scenarios

---

## [1.5.0] – Unified System Integration

### 🔗 Combined Application (`envirocheck_full.py`)

* Merged:

  * EnviroCheck dashboard
  * NEXUS predictive engine
* Introduced multi-tab system:

  * Dashboard
  * Flood Map
  * Indoor Climate
  * 5-Day Forecast

### 📅 Forecast Module

* Integrated 5-day forecast using OpenWeather API
* Daily min/max temperature aggregation

---

## [1.6.0] – Action Plan Module

### 🛠 Smart Action Plan (`action_plan.py`)

* Generated dynamic recommendations based on:

  * Heat risk
  * Flood risk
  * Air quality
* Designed for future integration with NEXUS predictions

### 🔁 Improvement

* Replaced static conditional UI logic with modular AI-driven system

---

## 🔮 Future Enhancements

* Real IoT sensor integration
* Personalized alerts (elderly, children)
* Push notification system
* Advanced geospatial risk mapping
* Full AI prediction + action automation

---

## 👩‍💻 Contributors

* Julia Mary James
* Nakshatra Mariam Manoj
* Nandana Deepak
* Pooja Nair

---
