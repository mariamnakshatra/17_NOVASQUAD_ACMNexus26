#  EnviroCheck

EnviroCheck is an intelligent **climate risk monitoring and analysis system** that transforms real-time environmental data into meaningful insights and actionable recommendations.

---

##  Problem Statement

Environmental data is often fragmented and difficult to interpret.
Users lack a unified system that connects **weather data, pollution levels, and real-world risks** to support quick and informed decision-making.

---

##  Solution

EnviroCheck provides a **unified platform** that:

* Collects real-time environmental data from APIs
* Analyzes risks using threshold-based and predictive models
* Generates **actionable recommendations**
* Visualizes insights through an interactive dashboard

---

##  System Overview

### Frontend

* Built using Streamlit
* Interactive dashboard with multiple tabs:

  *  Dashboard (climate metrics + risk alerts)
  *  Flood Risk Map (interactive visualization)
  *  Indoor Climate (comfort + simulation)
  *  Forecast (5-day prediction)

###  Backend

* Python-based modular architecture
* Real-time data fetching using APIs
* Risk evaluation engine
* AI-based recommendation system (Action Plan)
* NEXUS predictive intelligence module

---

##  Key Features

###  Real-time Monitoring

* Temperature, Humidity, Rainfall, AQI
* Location-based AQI adjustment

###  Risk Analysis

* Heat Risk (temperature thresholds)
* Flood Risk (rainfall-based modeling)
* Air Quality Risk (AQI-based classification)

###  Flood Risk Mapping

* Interactive Leaflet.js map
* Risk levels based on rainfall intensity

###  Indoor Climate Simulation

* Simulates indoor temperature based on:

  * Outdoor conditions
  * AC usage patterns
* Comfort classification system

###  NEXUS Intelligence Engine

* Predictive insights including:

  * Urban flood alerts (drainage overflow)
  * Structural risks (dew point & condensation)
  * Health risks (heat index, pressure changes)
  * Environmental impacts (humidity, spoilage)

###  Smart Action Plan

* Generates user-specific safety recommendations
* Based on real-time risk conditions

---

##  Technologies Used

* Python 3.x
* Streamlit
* Requests
* python-dotenv
* Plotly (for forecast visualization)
* Git & GitHub

---

##  Project Structure

* `Envirocheck.py` — Main application
* `action_plan.py` — Smart recommendation module
* `risk_engine.py` — Risk evaluation logic
* `data_fetcher.py` — API integration
* `location_ai.py` — Location-based AQI adjustment
* `nexus_full.py` — NEXUS predictive engine
* `CHANGELOG.md` — Development history
* `.env` — API configuration

---

##  Team

**Team NOVASQUAD**

* Julia Mary James
* Nakshatra Mariam Manoj
* Nandana Deepak
* Pooja Nair

---

##  How to Run

```bash
pip install streamlit requests python-dotenv
streamlit run Envirocheck.py
```

---

##  Future Scope

* Real sensor integration (IoT)
* Personalized alerts (elderly / children)
* Advanced AI prediction models
* Notification system
* Enhanced geospatial analytics

---
