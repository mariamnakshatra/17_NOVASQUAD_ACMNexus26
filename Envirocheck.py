"""
envirocheck_full.py  —  EnviroCheck + NEXUS  (single unified app)
------------------------------------------------------------------
Tabs:
  📊  Dashboard        — city search, climate cards, risk alerts, actions
  🌊  Flood Risk Map   — Leaflet.js live flood map
  🏢  Indoor Climate   — NEXUS campus sensor fusion + indoor building temp
  📅  5-Day Forecast   — Plotly daily min/max temperature chart

Install:
    pip install streamlit requests python-dotenv plotly

Run:
    streamlit run envirocheck_full.py
"""

import streamlit as st
import streamlit.components.v1 as components
import datetime
import requests
import os
import math
import random

from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────────────────────────────────────────
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "8c1d1f75ee0374a3e1eaa4985e2930ed")
AQI_API_KEY     = os.getenv("AQI_API_KEY",     "f43ff0a9ea330b352bc54aa273f9fda6cee84cd9")

CAMPUS_PROFILE = {
    "name":                "NEXUS Campus",
    "terrain":             "mixed_concrete_vegetation",
    "lat":                 9.9816,
    "lon":                 76.2999,
    "construction_active": False,
    "vegetation_index":    0.4,
    "canyon_factor":       0.6,
}

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EnviroCheck",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS  (merged from both files)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080e1a;
    color: #e2e8f0;
}
section[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2rem 3rem 3rem 3rem; max-width: 1300px; }

/* ── Brand ── */
.brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem; font-weight: 700; letter-spacing: -0.5px;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.subtitle { color: #64748b; font-size: 0.95rem; margin-top: 2px; margin-bottom: 1.5rem; }

/* ── Search input ── */
div[data-testid="stTextInput"] input {
    background: #0f172a !important; border: 1.5px solid #1e293b !important;
    border-radius: 12px !important; color: #f1f5f9 !important;
    font-size: 1rem !important; padding: 0.65rem 1rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.12) !important;
}

/* ── Climate cards (app.py style) ── */
.env-card {
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 16px; padding: 1.4rem 1.6rem;
    text-align: center; transition: border-color .2s, transform .2s;
    margin-bottom: 0.5rem;
}
.env-card:hover { border-color: #38bdf8; transform: translateY(-2px); }
.card-icon  { font-size: 2rem; margin-bottom: .3rem; }
.card-label { font-size: .75rem; color: #64748b; text-transform: uppercase;
              letter-spacing: .08em; margin-bottom: .3rem; }
.card-value { font-size: 2rem; font-weight: 700; color: #f1f5f9; line-height: 1; }
.card-sub   { font-size: .8rem; color: #94a3b8; margin-top: .3rem; }

/* ── Section titles ── */
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem; font-weight: 600; color: #94a3b8;
    text-transform: uppercase; letter-spacing: .1em;
    margin: 1.8rem 0 .8rem 0; padding-bottom: .4rem;
    border-bottom: 1px solid #1e293b;
}

/* ── Action items ── */
.action-item {
    background: #0f172a; border-left: 3px solid #38bdf8;
    border-radius: 0 10px 10px 0; padding: .7rem 1rem;
    margin-bottom: .5rem; font-size: .93rem; color: #cbd5e1;
}

/* ── Location badge ── */
.loc-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 10px; padding: 6px 14px;
    font-size: .85rem; color: #94a3b8; margin-bottom: 1rem;
}

/* ── NEXUS panel headers ── */
.inside-header {
    background: linear-gradient(135deg,#1a1a2e,#16213e);
    border-radius: 12px; padding: 1rem 1.4rem; margin-bottom: .5rem;
}
.outside-header {
    background: linear-gradient(135deg,#0d2137,#0a3d2b);
    border-radius: 12px; padding: 1rem 1.4rem; margin-bottom: .5rem;
}

/* ── Indoor temperature card ── */
.indoor-card {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    border-radius: 14px; padding: 1.2rem 1.5rem; margin: 0.8rem 0;
    border: 1px solid #2a4a5a; display: flex; align-items: center; gap: 1.2rem;
}
.indoor-temp-big { font-size: 2.8rem; font-weight: 800; color: #e0f7fa; line-height: 1; }
.indoor-badge {
    display: inline-block; border-radius: 20px; padding: 4px 14px;
    font-size: 0.82rem; font-weight: 700; margin-top: 6px;
}
.indoor-label { font-size: 0.75rem; color: #90a4ae; text-transform: uppercase; letter-spacing: 0.1em; }

hr { border-color: #1e293b !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION A — NEXUS helpers  (campus / indoor)
# ═════════════════════════════════════════════════════════════════════════════

def read_local_sensors() -> dict:
    """Simulated campus sensor readings — replace with real hardware I/O."""
    now  = datetime.datetime.now()
    hour = now.hour
    base = 28.5 + 2.5 * math.sin((hour - 14) * math.pi / 12)
    return {
        "temperature_c": round(base + random.gauss(0, 0.15), 2),
        "humidity_pct":  round(random.gauss(75, 3), 1),
        "aqi_local":     random.randint(55, 110),
        "pm25_local":    round(random.uniform(12, 45), 1),
        "pm10_local":    round(random.uniform(20, 80), 1),
        "co_ppm":        round(random.uniform(0.2, 1.5), 2),
        "timestamp":     now.strftime("%Y-%m-%d %H:%M:%S"),
    }


def simulate_indoor_temperature(outdoor_temp: float) -> dict:
    """Estimates building interior temperature from outdoor sensor reading."""
    hour = datetime.datetime.now().hour
    is_office = 8 <= hour <= 18
    if is_office:
        indoor_temp = round(23.0 + random.gauss(0, 0.4), 1)
    else:
        indoor_temp = round(outdoor_temp - random.uniform(1.5, 3.5), 1)

    if indoor_temp < 18:
        comfort, color, emoji = "Too Cold",      "#5b9bd5", "🥶"
    elif indoor_temp <= 24:
        comfort, color, emoji = "Comfortable",   "#00c853", "😊"
    elif indoor_temp <= 27:
        comfort, color, emoji = "Slightly Warm", "#ffd700", "😐"
    elif indoor_temp <= 31:
        comfort, color, emoji = "Warm",          "#ffa500", "🥵"
    else:
        comfort, color, emoji = "Hot",           "#ff4b4b", "🔥"

    return {
        "indoor_temp_c": indoor_temp,
        "comfort":       comfort,
        "comfort_color": color,
        "comfort_emoji": emoji,
        "ac_active":     is_office,
    }


def compute_urban_factors(sensor: dict, api_temp: float) -> dict:
    hour = datetime.datetime.now().hour
    is_rush  = (7 <= hour <= 9) or (17 <= hour <= 19)
    is_night = hour >= 21 or hour <= 5
    veg_cool = round(CAMPUS_PROFILE["vegetation_index"] * 2.5, 1)
    terrain  = 1.8
    traffic  = 20 if is_rush else 5
    canyon   = round(CAMPUS_PROFILE["canyon_factor"] * 15)
    constr   = 25 if CAMPUS_PROFILE.get("construction_active") else 0
    noc      = 2.0 if is_night else 0.0
    return {
        "terrain_offset_c":       terrain,
        "vegetation_cooling_c":   veg_cool,
        "traffic_aqi_bump":       traffic,
        "canyon_aqi_bump":        canyon,
        "construction_pm10_bump": constr,
        "nocturnal_delta_c":      noc,
        "nocturnal_heat_island":  is_night,
        "total_temp_offset_c":    round(terrain - veg_cool + noc, 2),
        "corrected_temp_c":       round(api_temp + terrain - veg_cool + noc, 2),
        "sensor_vs_api_gap":      round(sensor["temperature_c"] - api_temp, 2),
        "traffic_label":          "Rush hour" if is_rush else "Normal",
        "total_aqi_offset":       traffic + canyon + constr,
        "construction_active":    CAMPUS_PROFILE.get("construction_active", False),
    }


def get_diurnal_phase() -> dict:
    hour = datetime.datetime.now().hour
    if 5  <= hour < 8:  return {"phase": "Early morning",       "hour": hour, "note": "Coolest period; ideal for outdoor exercise."}
    if 8  <= hour < 12: return {"phase": "Morning warm-up",     "hour": hour, "note": "Temperature rising; moderate risk building."}
    if 12 <= hour < 16: return {"phase": "Peak heat",           "hour": hour, "note": "Highest heat index. Avoid prolonged sun exposure."}
    if 16 <= hour < 19: return {"phase": "Afternoon cool-down", "hour": hour, "note": "Temperature easing but humidity still high."}
    if 19 <= hour < 21: return {"phase": "Evening",             "hour": hour, "note": "Comfortable for outdoor activity."}
    return {"phase": "Nocturnal heat island", "hour": hour,
            "note": "Campus stays 2-3°C warmer than city average due to concrete."}


def _campus_weather_api(city: str) -> dict:
    try:
        url  = (f"http://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={WEATHER_API_KEY}&units=metric")
        data = requests.get(url, timeout=5).json()
        if data.get("cod") != 200:
            return {}
        return {
            "temp":        data["main"]["temp"],
            "humidity":    data["main"]["humidity"],
            "wind_speed":  data["wind"]["speed"],
            "description": data["weather"][0]["description"],
            "city":        data["name"],
        }
    except Exception as e:
        st.warning(f"[Campus weather] {e}")
        return {}


def _campus_aqi_api(lat: float, lon: float) -> dict:
    try:
        url  = (f"http://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}")
        data = requests.get(url, timeout=5).json()
        idx  = data["list"][0]["main"]["aqi"]
        comp = data["list"][0]["components"]
        aqi_map = {1: 25, 2: 60, 3: 100, 4: 150, 5: 220}
        return {"aqi_approx": aqi_map.get(idx, 100),
                "pm25": comp.get("pm2_5", 0), "no2": comp.get("no2", 0)}
    except:
        return {}


def get_fused_micro_climate(city: str = "Kochi") -> dict:
    weather = _campus_weather_api(city)
    aqi_owm = _campus_aqi_api(CAMPUS_PROFILE["lat"], CAMPUS_PROFILE["lon"])
    api_temp = weather.get("temp", 32.0)
    api_aqi  = aqi_owm.get("aqi_approx", 80)
    sensor   = read_local_sensors()
    urban    = compute_urban_factors(sensor, api_temp)
    lt, lrh  = sensor["temperature_c"], sensor["humidity_pct"]
    indoor   = simulate_indoor_temperature(lt)
    return {
        "campus":           CAMPUS_PROFILE["name"],
        "city":             weather.get("city", city),
        "api_temp_c":       api_temp,
        "sensor_temp_c":    lt,
        "corrected_temp_c": urban["corrected_temp_c"],
        "temp_gap_c":       urban["sensor_vs_api_gap"],
        "heat_index_c":     compute_heat_index(lt, lrh),
        "dew_point_c":      compute_dew_point(lt, lrh),
        "humidity_pct":     lrh,
        "aqi_api":          api_aqi,
        "aqi_local":        sensor["aqi_local"],
        "aqi_fused":        round(max(api_aqi + urban["total_aqi_offset"], sensor["aqi_local"])),
        "pm25":             sensor["pm25_local"],
        "pm10":             sensor["pm10_local"],
        "co_ppm":           sensor["co_ppm"],
        "wind_speed_ms":    weather.get("wind_speed", 0),
        "description":      weather.get("description", "N/A"),
        "urban_factors":    urban,
        "diurnal":          get_diurnal_phase(),
        "sensor_raw":       sensor,
        "indoor":           indoor,
    }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION B — Outside location fetcher  (from app.py / data_fetcher)
# ═════════════════════════════════════════════════════════════════════════════

def get_coordinates(place: str):
    try:
        url  = (f"http://api.openweathermap.org/geo/1.0/direct"
                f"?q={place}&limit=1&appid={WEATHER_API_KEY}")
        data = requests.get(url, timeout=5).json()
        if not data:
            return None
        return data[0]["lat"], data[0]["lon"]
    except Exception as e:
        st.warning(f"[Geocoding] {e}")
        return None


def get_weather_by_coords(lat: float, lon: float):
    try:
        url  = (f"http://api.openweathermap.org/data/2.5/weather"
                f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric")
        data = requests.get(url, timeout=5).json()
        if data.get("cod") != 200:
            return None
        return {
            "temp":        data["main"]["temp"],
            "feels_like":  data["main"]["feels_like"],
            "humidity":    data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed":  data["wind"]["speed"],
            "rain":        data.get("rain", {}).get("1h", 0),
            "city":        data["name"],
            "lat":         lat,
            "lon":         lon,
        }
    except Exception as e:
        st.warning(f"[Weather] {e}")
        return None


def get_aqi_outside(lat: float, lon: float):
    try:
        url  = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQI_API_KEY}"
        data = requests.get(url, timeout=5).json()
        if data.get("status") != "ok":
            return None
        return data["data"]["aqi"]
    except Exception as e:
        st.warning(f"[AQI] {e}")
        return None


def get_5day_forecast(lat: float, lon: float):
    """Calls /forecast endpoint and groups 3-hour slots into daily min/max."""
    try:
        url  = (f"http://api.openweathermap.org/data/2.5/forecast"
                f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric")
        data = requests.get(url, timeout=5).json()
        if str(data.get("cod")) != "200":
            return None
        daily = {}
        for entry in data["list"]:
            date_str = entry["dt_txt"].split(" ")[0]
            temp     = entry["main"]["temp"]
            rain     = entry.get("rain", {}).get("3h", 0)
            desc     = entry["weather"][0]["description"]
            if date_str not in daily:
                daily[date_str] = {"date": date_str, "temps": [], "rain": 0.0, "description": desc}
            daily[date_str]["temps"].append(temp)
            daily[date_str]["rain"] += rain
        forecast = []
        for ds, d in sorted(daily.items()):
            forecast.append({
                "date":        d["date"],
                "temp_min":    round(min(d["temps"]), 1),
                "temp_max":    round(max(d["temps"]), 1),
                "description": d["description"].capitalize(),
                "rain":        round(d["rain"], 1),
            })
        return forecast[:5]
    except Exception as e:
        st.warning(f"[Forecast] {e}")
        return None


def classify_location(place: str) -> str:
    p = place.lower()
    if any(k in p for k in ["eloor", "ambalamugal"]):           return "industrial"
    if any(k in p for k in ["mg road", "highway", "junction"]): return "traffic"
    if any(k in p for k in ["fort kochi", "beach", "coast"]):   return "coastal"
    return "urban"


def adjust_aqi(aqi: int, location_type: str) -> int:
    if location_type == "industrial": return aqi + 30
    if location_type == "traffic":    return aqi + 20
    if location_type == "coastal":    return max(aqi - 10, 0)
    return aqi


def get_all_data(place: str):
    coords = get_coordinates(place)
    if not coords:
        return None
    lat, lon = coords
    weather  = get_weather_by_coords(lat, lon)
    if not weather:
        return None
    raw_aqi = get_aqi_outside(lat, lon)
    if raw_aqi is None:
        return None
    weather["aqi"] = raw_aqi
    return weather


# ═════════════════════════════════════════════════════════════════════════════
# SECTION C — Shared helpers
# ═════════════════════════════════════════════════════════════════════════════

def compute_heat_index(t: float, rh: float) -> float:
    hi = (-8.78469475556
          + 1.61139411 * t + 2.33854883889 * rh
          - 0.14611605 * t * rh - 0.012308094 * t**2
          - 0.0164248277778 * rh**2 + 0.002211732 * t**2 * rh
          + 0.00072546 * t * rh**2 - 0.000003582 * t**2 * rh**2)
    return round(hi, 1)


def compute_dew_point(t: float, rh: float) -> float:
    a, b  = 17.27, 237.7
    gamma = (a * t / (b + t)) + math.log(rh / 100.0)
    return round((b * gamma) / (a - gamma), 1)


def classify_aqi_level(aqi: float) -> tuple:
    if aqi <= 50:  return "Good",                  "🟢"
    if aqi <= 100: return "Moderate",              "🟡"
    if aqi <= 150: return "Unhealthy (Sensitive)", "🟠"
    if aqi <= 200: return "Unhealthy",             "🔴"
    if aqi <= 300: return "Very Unhealthy",        "🟣"
    return "Hazardous", "⛔"


def classify_heat_level(hi: float) -> tuple:
    if hi < 27: return "Comfortable", "🟢"
    if hi < 32: return "Moderate",    "🟡"
    if hi < 40: return "High",        "🟠"
    if hi < 46: return "Extreme",     "🔴"
    return "Critical", "⛔"


def get_flood_risk(rain: float) -> tuple:
    if rain == 0:  return "Safe",      "🟢", "#22c55e"
    if rain <= 3:  return "Low risk",  "🟡", "#eab308"
    if rain <= 10: return "Moderate",  "🟠", "#f97316"
    return "Flood risk",               "🔴", "#ef4444"


# ═════════════════════════════════════════════════════════════════════════════
# SECTION D — Flood map builder  (from app.py, unchanged)
# ═════════════════════════════════════════════════════════════════════════════

def build_flood_map_html(lat, lon, rain, city, temp, humidity):
    if rain == 0:    level, color = "Safe",      "#22c55e"
    elif rain <= 3:  level, color = "Low risk",  "#eab308"
    elif rain <= 10: level, color = "Moderate",  "#f97316"
    else:            level, color = "Flood risk","#ef4444"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#080e1a; }}
    #map {{ width:100%; height:460px; border-radius:12px; }}
    .risk-marker {{
      width:38px; height:38px; border-radius:50%;
      background:{color}; border:3px solid rgba(255,255,255,0.45);
      display:flex; align-items:center; justify-content:center;
      box-shadow:0 0 0 8px {color}33;
    }}
    .risk-marker svg {{ width:18px; height:18px; }}
    .leaflet-popup-content-wrapper {{
      background:#0f172a !important; border:1px solid #334155 !important;
      border-radius:12px !important; box-shadow:0 8px 24px rgba(0,0,0,.6) !important;
      padding:0 !important;
    }}
    .leaflet-popup-content {{ margin:0 !important; }}
    .leaflet-popup-tip {{ background:#0f172a !important; }}
    .pop {{ padding:14px 16px; min-width:180px; font-family:-apple-system,sans-serif; }}
    .pop-title {{ font-size:14px; font-weight:700; color:#f1f5f9; margin-bottom:10px; }}
    .pop-row {{ display:flex; justify-content:space-between; font-size:12px;
               color:#64748b; margin-bottom:5px; }}
    .pop-row b {{ color:#e2e8f0; }}
    .pop-badge {{
      margin-top:10px; padding:5px 0; text-align:center;
      border-radius:6px; font-size:12px; font-weight:700;
      background:{color}22; color:{color}; border:1px solid {color}55;
    }}
    .legend {{
      position:absolute; bottom:24px; right:12px; z-index:999;
      background:rgba(9,15,28,.92); border:1px solid #1e293b;
      border-radius:10px; padding:10px 14px;
      font-family:-apple-system,sans-serif; font-size:11px; color:#94a3b8;
    }}
    .leg-ttl {{ font-weight:700; color:#cbd5e1; text-transform:uppercase;
               letter-spacing:.06em; margin-bottom:8px; font-size:10px; }}
    .leg-row {{ display:flex; align-items:center; gap:8px; margin-bottom:4px; }}
    .leg-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="legend">
    <div class="leg-ttl">Flood risk</div>
    <div class="leg-row"><div class="leg-dot" style="background:#22c55e"></div>Safe — 0 mm</div>
    <div class="leg-row"><div class="leg-dot" style="background:#eab308"></div>Low — 1–3 mm</div>
    <div class="leg-row"><div class="leg-dot" style="background:#f97316"></div>Moderate — 3–10 mm</div>
    <div class="leg-row"><div class="leg-dot" style="background:#ef4444"></div>Flood — 10+ mm</div>
  </div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map("map").setView([{lat}, {lon}], 12);
    L.tileLayer("https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png",
      {{ attribution:"&copy; OSM &copy; CARTO", maxZoom:19 }}).addTo(map);
    const icon = L.divIcon({{
      className:"",
      html:`<div class="risk-marker">
              <svg viewBox="0 0 24 24" fill="none"
                   stroke="white" stroke-width="2.5" stroke-linecap="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>`,
      iconSize:[38,38], iconAnchor:[19,19], popupAnchor:[0,-24]
    }});
    L.marker([{lat},{lon}],{{icon}}).addTo(map)
      .bindPopup(`
        <div class="pop">
          <div class="pop-title">📍 {city}</div>
          <div class="pop-row"><span>Rainfall</span><b>{rain} mm/h</b></div>
          <div class="pop-row"><span>Temperature</span><b>{temp}°C</b></div>
          <div class="pop-row"><span>Humidity</span><b>{humidity}%</b></div>
          <div class="pop-badge">Risk level: {level}</div>
        </div>`, {{maxWidth:220}})
      .openPopup();
    L.circle([{lat},{lon}],{{
      radius:12000, color:"{color}",
      fillColor:"{color}", fillOpacity:0.1, weight:1.5, opacity:0.5
    }}).addTo(map);
  </script>
</body>
</html>"""


# ═════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═════════════════════════════════════════════════════════════════════════════

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="brand">🌍 EnviroCheck</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Real-time climate, flood risk & indoor monitoring</p>',
    unsafe_allow_html=True,
)

# ── Search bar + sidebar settings in one row ──────────────────────────────────
search_col, settings_col = st.columns([3, 1])
with search_col:
    city_input = st.text_input(
        "",
        placeholder="🔍  Search any city — e.g. Kochi, Delhi, Mumbai…",
        label_visibility="collapsed",
    )
with settings_col:
    campus_city  = st.text_input("Campus city", value="Kochi", label_visibility="visible")
    construction = st.toggle("Active construction", value=False)

CAMPUS_PROFILE["construction_active"] = construction

if not city_input.strip():
    st.markdown(
        '<div style="color:#475569;text-align:center;padding:4rem 0;font-size:1.05rem;">'
        '↑ Enter a city name to load all four dashboards'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Fetch all data ─────────────────────────────────────────────────────────────
with st.spinner("Fetching live data from all sources…"):
    raw          = get_all_data(city_input.strip())
    fused        = get_fused_micro_climate(campus_city)
    forecast_data = None
    if raw:
        forecast_data = get_5day_forecast(raw["lat"], raw["lon"])

if not raw:
    st.error("Could not fetch data. Check city name or API keys in your .env file.")
    st.stop()

# ── Derived values ────────────────────────────────────────────────────────────
loc_type     = classify_location(city_input.strip())
adjusted_aqi = adjust_aqi(int(raw["aqi"]), loc_type)
temp         = round(raw["temp"], 1)
humidity     = raw["humidity"]
rain         = round(raw.get("rain", 0), 1)
lat          = raw["lat"]
lon          = raw["lon"]
heat_idx     = compute_heat_index(temp, humidity)
dew_pt       = compute_dew_point(temp, humidity)
ts           = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

flood_level, flood_icon, flood_color = get_flood_risk(rain)
aqi_level,   aqi_icon                = classify_aqi_level(adjusted_aqi)

loc_labels = {
    "industrial": "🏭 Industrial zone — AQI +30",
    "traffic":    "🚗 Traffic corridor — AQI +20",
    "coastal":    "🌊 Coastal zone — AQI −10",
    "urban":      "🏙 Urban area",
}

# ── Location badge ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="loc-badge">📍 {city_input.title()} &nbsp;·&nbsp; '
    f'{loc_labels[loc_type]} &nbsp;·&nbsp; 🕐 {ts}</div>',
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════════════════════
# FOUR TABS
# ═════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Dashboard",
    "🌊  Flood Risk Map",
    "🏢  Indoor Climate",
    "📅  5-Day Forecast",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — DASHBOARD  (from app.py, unchanged)
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<p class="section-title">Current Conditions</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="env-card">
            <div class="card-icon">🌡</div>
            <div class="card-label">Temperature</div>
            <div class="card-value">{temp}°C</div>
            <div class="card-sub">Heat index {heat_idx}°C</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="env-card">
            <div class="card-icon">💧</div>
            <div class="card-label">Humidity</div>
            <div class="card-value">{humidity}%</div>
            <div class="card-sub">Dew point {dew_pt}°C</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="env-card">
            <div class="card-icon">🌫</div>
            <div class="card-label">Air Quality Index</div>
            <div class="card-value">{adjusted_aqi}</div>
            <div class="card-sub">{aqi_icon} {aqi_level}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="env-card">
            <div class="card-icon">🌧</div>
            <div class="card-label">Rainfall (1h)</div>
            <div class="card-value">{rain} mm</div>
            <div class="card-sub">{flood_icon} {flood_level}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<p class="section-title">Risk Alerts</p>', unsafe_allow_html=True)
    colA, colB, colC = st.columns(3)
    with colA:
        if temp > 38:   st.error(f"🔥 Heatwave — {temp}°C")
        elif temp > 32: st.warning(f"🌡 Warm — {temp}°C")
        else:           st.success(f"🟢 Normal temp — {temp}°C")
    with colB:
        if rain > 10:   st.error(f"🌊 Flood risk — {rain} mm/h")
        elif rain > 3:  st.warning(f"🌧 Rain — {rain} mm/h")
        else:           st.success(f"🟢 No flood risk — {rain} mm/h")
    with colC:
        if adjusted_aqi > 150:  st.error(f"🌫 Unhealthy AQI — {adjusted_aqi}")
        elif adjusted_aqi > 80: st.warning(f"🌫 Moderate AQI — {adjusted_aqi}")
        else:                   st.success(f"🟢 Good AQI — {adjusted_aqi}")

    st.markdown('<p class="section-title">Recommended Actions</p>', unsafe_allow_html=True)
    actions = []
    if temp > 38:          actions.append("🔥 Dangerous heat — stay indoors, avoid all outdoor activity.")
    elif temp > 32:        actions.append("🌡 High temp — limit outdoor time 12pm–4pm, stay hydrated.")
    if rain > 10:          actions.append("🌊 Heavy rainfall — avoid low-lying areas, follow flood alerts.")
    elif rain > 3:         actions.append("🌧 Moderate rain — carry umbrella, drive carefully.")
    if adjusted_aqi > 150: actions.append("😷 Unhealthy air — wear N95 mask, keep windows closed.")
    elif adjusted_aqi > 100: actions.append("🌫 Moderate AQI — sensitive groups limit outdoor time.")
    if dew_pt > 26:        actions.append("💧 Very humid — risk of heat exhaustion, stay ventilated.")

    if actions:
        for a in actions:
            st.markdown(f'<div class="action-item">{a}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="action-item" style="border-left-color:#22c55e;">'
            '✅ All conditions safe. No special precautions needed.'
            '</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — FLOOD RISK MAP  (from app.py, unchanged)
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    fl1, fl2, fl3 = st.columns(3)
    fl1.metric("Rainfall (1h)", f"{rain} mm")
    fl2.metric("Flood risk",    f"{flood_icon} {flood_level}")
    fl3.metric("Zone type",     loc_labels[loc_type])

    advice_map = {
        "Safe":       ("✅ No flood risk. Conditions are safe.", "success"),
        "Low risk":   ("🟡 Light rain. Watch for waterlogging in low-lying areas.", "warning"),
        "Moderate":   ("🟠 Moderate rain. Avoid underpasses and low roads.", "warning"),
        "Flood risk": ("🔴 Heavy rain — flood risk active. Avoid low areas now.", "error"),
    }
    msg, kind = advice_map[flood_level]
    getattr(st, kind)(msg)

    map_html = build_flood_map_html(
        lat=lat, lon=lon, rain=rain,
        city=city_input.title(), temp=temp, humidity=humidity,
    )
    components.html(map_html, height=500, scrolling=False)
    st.caption(
        f"Centred on {city_input.title()} ({lat:.4f}, {lon:.4f})  ·  "
        f"Basemap: CartoDB Dark  ·  Risk thresholds: IMD standard"
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — INDOOR CLIMATE  (from combined.py)
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    indoor = fused["indoor"]
    urban  = fused["urban_factors"]
    d      = fused["diurnal"]
    hi_level,  hi_icon  = classify_heat_level(fused["heat_index_c"])
    aqi_level2, aqi_icon2 = classify_aqi_level(fused["aqi_fused"])

    st.markdown('<p class="section-title">Campus Indoor Temperature</p>', unsafe_allow_html=True)

    # Indoor card
    ac_label = "🌀 AC Active" if indoor["ac_active"] else "🌙 AC Off (night)"
    st.markdown(f"""
        <div class="indoor-card">
          <div style="font-size:2.4rem;">🏠</div>
          <div>
            <div class="indoor-label">Indoor Building Temperature</div>
            <div class="indoor-temp-big">{indoor['indoor_temp_c']}°C</div>
            <span class="indoor-badge" style="background:{indoor['comfort_color']}33;
                  color:{indoor['comfort_color']}">
              {indoor['comfort_emoji']} {indoor['comfort']}
            </span>
            &nbsp;
            <span style="font-size:0.78rem;color:#78909c;">{ac_label}</span>
          </div>
          <div style="margin-left:auto;text-align:right;">
            <div class="indoor-label">Campus Outdoor</div>
            <div style="font-size:1.4rem;font-weight:700;color:#b0bec5;">{fused['sensor_temp_c']}°C</div>
            <div style="font-size:0.78rem;color:#78909c;">sensor reading</div>
          </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-title">Campus Sensor Metrics</p>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Campus Temp",  f"{fused['sensor_temp_c']}°C",
              delta=f"{fused['temp_gap_c']:+}°C vs API", delta_color="inverse")
    m2.metric("Heat Index",   f"{fused['heat_index_c']}°C")
    m3.metric("Fused AQI",    fused["aqi_fused"],
              delta=f"{fused['aqi_fused'] - fused['aqi_api']:+} vs API", delta_color="inverse")
    m4.metric("Humidity",     f"{fused['humidity_pct']}%")
    m5.metric("Dew Point",    f"{fused['dew_point_c']}°C")
    m6.metric("PM 2.5",       f"{fused['pm25']} µg/m³")

    st.markdown(
        f"**Heat risk:** {hi_icon} {hi_level} &nbsp;&nbsp; "
        f"**Air quality:** {aqi_icon2} {aqi_level2}",
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-title">Urban Factor Corrections</p>', unsafe_allow_html=True)
    factors = []
    if urban.get("terrain_offset_c"):    factors.append(f"🏗 Terrain +{urban['terrain_offset_c']}°C")
    if urban.get("vegetation_cooling_c"): factors.append(f"🌿 Vegetation −{urban['vegetation_cooling_c']}°C")
    if urban.get("traffic_aqi_bump"):    factors.append(f"🚗 Traffic AQI +{urban['traffic_aqi_bump']} ({urban['traffic_label']})")
    if urban.get("canyon_aqi_bump"):     factors.append(f"🏙 Building canyon AQI +{urban['canyon_aqi_bump']}")
    if urban.get("nocturnal_heat_island"): factors.append(f"🌙 Nocturnal heat island +{urban['nocturnal_delta_c']}°C")
    if urban.get("construction_active"): factors.append(f"🚧 Construction PM10 +{urban['construction_pm10_bump']}")
    for f_item in factors:
        st.markdown(f"- {f_item}")

    st.markdown(f"**Diurnal phase:** {d['phase']} (hour {d['hour']:02d}:00)")
    st.caption(d["note"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — 5-DAY FORECAST  (from combined.py)
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(f"### 📅 5-Day Temperature Forecast")
    st.caption(f"Location: **{raw['city']}** — daily min/max temperatures and rainfall")

    if not forecast_data:
        st.warning("Could not load forecast data. Check API keys or location name.")
    else:
        try:
            import plotly.graph_objects as go

            dates    = [d["date"] for d in forecast_data]
            temp_min = [d["temp_min"] for d in forecast_data]
            temp_max = [d["temp_max"] for d in forecast_data]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Min Temp (°C)", x=dates, y=temp_min,
                marker_color="#5b9bd5",
                text=[f"{v}°C" for v in temp_min], textposition="outside",
            ))
            fig.add_trace(go.Bar(
                name="Max Temp (°C)", x=dates, y=temp_max,
                marker_color="#ff6b6b",
                text=[f"{v}°C" for v in temp_max], textposition="outside",
            ))
            fig.update_layout(
                title=dict(text="5-Day Min / Max Temperature", font=dict(size=18, color="#e0e0e0")),
                barmode="group",
                xaxis=dict(title=dict(text="Date",            font=dict(color="#b0bec5")), tickfont=dict(color="#b0bec5")),
                yaxis=dict(title=dict(text="Temperature (°C)", font=dict(color="#b0bec5")),
                           tickfont=dict(color="#b0bec5"),
                           range=[min(temp_min) - 3, max(temp_max) + 5]),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,20,30,0.6)",
                legend=dict(font=dict(color="#e0e0e0"), bgcolor="rgba(0,0,0,0.3)"),
                font=dict(color="#e0e0e0"), height=420,
                margin=dict(t=60, b=40, l=50, r=20),
            )
            fig.update_yaxes(gridcolor="#1e2a36", zerolinecolor="#1e2a36")
            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            st.warning("Install plotly: `pip install plotly`")

        # Daily cards
        st.markdown("#### 📋 Daily Breakdown")
        cols = st.columns(len(forecast_data))
        for i, day in enumerate(forecast_data):
            with cols[i]:
                desc_lower = day["description"].lower()
                if "rain" in desc_lower or "drizzle" in desc_lower: icon = "🌧"
                elif "cloud" in desc_lower:  icon = "☁️"
                elif "clear" in desc_lower:  icon = "☀️"
                elif "storm" in desc_lower or "thunder" in desc_lower: icon = "⛈"
                elif "snow" in desc_lower:   icon = "❄️"
                elif "mist" in desc_lower or "fog" in desc_lower: icon = "🌫"
                else:                        icon = "🌤"
                try:
                    dt = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
                    day_label  = dt.strftime("%a")
                    date_label = dt.strftime("%-d %b")
                except Exception:
                    day_label, date_label = day["date"], ""

                st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#0f2027,#1c3a4a);
                                border-radius:12px;padding:1rem;text-align:center;
                                border:1px solid #1e3a4a;">
                      <div style="font-size:0.7rem;color:#90a4ae;text-transform:uppercase;
                                  letter-spacing:0.1em;">{day_label}</div>
                      <div style="font-size:0.85rem;color:#b0bec5;margin-bottom:6px;">{date_label}</div>
                      <div style="font-size:2rem;">{icon}</div>
                      <div style="font-size:0.72rem;color:#78909c;margin:4px 0;">{day['description']}</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#ff6b6b;">↑ {day['temp_max']}°C</div>
                      <div style="font-size:1rem;color:#5b9bd5;">↓ {day['temp_min']}°C</div>
                      <div style="font-size:0.78rem;color:#64b5f6;margin-top:6px;">💧 {day['rain']} mm</div>
                    </div>
                """, unsafe_allow_html=True)

        st.caption("Rain values are cumulative totals for the day across all 3-hour forecast slots.")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<p style="color:#334155;font-size:.8rem;text-align:center;">'
    f'EnviroCheck · OpenWeatherMap + WAQI + NEXUS Local Sensor · {ts}'
    f'</p>',
    unsafe_allow_html=True,
)