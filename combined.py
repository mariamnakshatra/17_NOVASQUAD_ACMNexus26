"""
combined_app.py  —  NEXUS Dual-Environment Dashboard
------------------------------------------------------
Shows:
  LEFT  → INSIDE / Campus (NEXUS sensor fusion pipeline)
  RIGHT → OUTSIDE / Any location (user-typed, via simple data_fetcher)

NEW in this version:
  • Indoor Temperature card — shows building interior temp with comfort zone badge
  • 5-Day Forecast tab — bar chart of daily min/max temps using Plotly

Run:
    pip install streamlit requests python-dotenv plotly
    streamlit run combined_app.py
"""

import streamlit as st
import datetime
import requests
import os
import math
import random

# ─────────────────────────────────────────────────────────────────────────────
# ░░  API KEYS  ░░
# ─────────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

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

# ═════════════════════════════════════════════════════════════════════════════
# SECTION A — NEXUS (Campus / Indoor sensor-fusion pipeline)
# ═════════════════════════════════════════════════════════════════════════════

def read_local_sensors() -> dict:
    """Simulate local physical sensor readings (replace with real hardware I/O)."""
    now   = datetime.datetime.now()
    hour  = now.hour
    base  = 28.5 + 2.5 * math.sin((hour - 14) * math.pi / 12)
    noise = random.gauss(0, 0.15)
    return {
        "temperature_c": round(base + noise, 2),
        "humidity_pct":  round(random.gauss(75, 3), 1),
        "aqi_local":     random.randint(55, 110),
        "pm25_local":    round(random.uniform(12, 45), 1),
        "pm10_local":    round(random.uniform(20, 80), 1),
        "co_ppm":        round(random.uniform(0.2, 1.5), 2),
        "timestamp":     now.strftime("%Y-%m-%d %H:%M:%S"),
    }


def simulate_indoor_temperature(outdoor_temp: float) -> dict:
    """
    Estimates the temperature INSIDE a building based on the outdoor temperature.
    
    Logic:
      - Buildings in tropical/hot climates (like Kerala) are typically AC-cooled.
      - AC setpoint is usually 22–24°C.
      - If outdoor temp <= 22°C, the building is naturally cooler than outside.
      - We add a small random variation to simulate sensor noise.
    
    Returns a dict with indoor temp and a comfort classification.
    """
    hour = datetime.datetime.now().hour
    is_office_hours = 8 <= hour <= 18

    # AC is typically ON during office hours; building warms up at night
    if is_office_hours:
        # AC-cooled: clamp between 21 and 25°C with small variation
        ac_setpoint = 23.0
        indoor_temp = round(ac_setpoint + random.gauss(0, 0.4), 1)
    else:
        # AC off at night — indoor temp drifts toward outdoor, slightly cooler
        indoor_temp = round(outdoor_temp - random.uniform(1.5, 3.5), 1)

    # Comfort classification
    if indoor_temp < 18:
        comfort = "Too Cold"
        comfort_color = "#5b9bd5"
        comfort_emoji = "🥶"
    elif indoor_temp <= 24:
        comfort = "Comfortable"
        comfort_color = "#00c853"
        comfort_emoji = "😊"
    elif indoor_temp <= 27:
        comfort = "Slightly Warm"
        comfort_color = "#ffd700"
        comfort_emoji = "😐"
    elif indoor_temp <= 31:
        comfort = "Warm"
        comfort_color = "#ffa500"
        comfort_emoji = "🥵"
    else:
        comfort = "Hot"
        comfort_color = "#ff4b4b"
        comfort_emoji = "🔥"

    return {
        "indoor_temp_c":  indoor_temp,
        "comfort":        comfort,
        "comfort_color":  comfort_color,
        "comfort_emoji":  comfort_emoji,
        "ac_active":      is_office_hours,
    }


def compute_urban_factors(sensor: dict, api_temp: float) -> dict:
    now      = datetime.datetime.now()
    hour     = now.hour
    is_rush  = (7 <= hour <= 9) or (17 <= hour <= 19)
    is_night = hour >= 21 or hour <= 5

    terrain_offset      = 1.8
    vegetation_cooling  = round(CAMPUS_PROFILE["vegetation_index"] * 2.5, 1)
    traffic_bump        = 20 if is_rush else 5
    canyon_bump         = round(CAMPUS_PROFILE["canyon_factor"] * 15)
    construction_bump   = 25 if CAMPUS_PROFILE.get("construction_active") else 0
    nocturnal_delta     = 2.0 if is_night else 0.0
    total_temp_offset   = round(terrain_offset - vegetation_cooling + nocturnal_delta, 2)
    corrected_temp      = round(api_temp + total_temp_offset, 2)
    sensor_gap          = round(sensor["temperature_c"] - api_temp, 2)
    total_aqi_offset    = traffic_bump + canyon_bump + construction_bump

    return {
        "terrain_offset_c":       terrain_offset,
        "vegetation_cooling_c":   vegetation_cooling,
        "traffic_aqi_bump":       traffic_bump,
        "canyon_aqi_bump":        canyon_bump,
        "construction_pm10_bump": construction_bump,
        "nocturnal_delta_c":      nocturnal_delta,
        "nocturnal_heat_island":  is_night,
        "total_temp_offset_c":    total_temp_offset,
        "corrected_temp_c":       corrected_temp,
        "sensor_vs_api_gap":      sensor_gap,
        "traffic_label":          "Rush hour" if is_rush else "Normal",
        "total_aqi_offset":       total_aqi_offset,
        "construction_active":    CAMPUS_PROFILE.get("construction_active", False),
    }


def compute_heat_index(t: float, rh: float) -> float:
    hi = (-8.78469475556
          + 1.61139411 * t
          + 2.33854883889 * rh
          - 0.14611605 * t * rh
          - 0.012308094 * t**2
          - 0.0164248277778 * rh**2
          + 0.002211732 * t**2 * rh
          + 0.00072546 * t * rh**2
          - 0.000003582 * t**2 * rh**2)
    return round(hi, 1)


def compute_dew_point(t: float, rh: float) -> float:
    a, b = 17.27, 237.7
    gamma = (a * t / (b + t)) + math.log(rh / 100.0)
    return round((b * gamma) / (a - gamma), 1)


def get_diurnal_phase() -> dict:
    hour = datetime.datetime.now().hour
    if 5  <= hour < 8:  return {"phase": "Early morning",       "hour": hour, "note": "Coolest period; ideal for outdoor exercise."}
    if 8  <= hour < 12: return {"phase": "Morning warm-up",     "hour": hour, "note": "Temperature rising; moderate risk building."}
    if 12 <= hour < 16: return {"phase": "Peak heat",           "hour": hour, "note": "Highest heat index. Avoid prolonged sun exposure."}
    if 16 <= hour < 19: return {"phase": "Afternoon cool-down", "hour": hour, "note": "Temperature easing but humidity still high."}
    if 19 <= hour < 21: return {"phase": "Evening",             "hour": hour, "note": "Comfortable for outdoor activity."}
    return {"phase": "Nocturnal heat island",                    "hour": hour, "note": "Campus stays 2-3°C warmer than city average due to concrete."}


def _get_weather_api(city: str) -> dict:
    try:
        url  = (f"http://api.openweathermap.org/data/2.5/weather"
                f"?q={city}&appid={WEATHER_API_KEY}&units=metric")
        data = requests.get(url, timeout=5).json()
        if data.get("cod") != 200:
            return {}
        return {
            "temp":        data["main"]["temp"],
            "feels_like":  data["main"]["feels_like"],
            "humidity":    data["main"]["humidity"],
            "pressure":    data["main"]["pressure"],
            "wind_speed":  data["wind"]["speed"],
            "wind_deg":    data["wind"].get("deg", 0),
            "description": data["weather"][0]["description"],
            "city":        data["name"],
            "country":     data["sys"]["country"],
            "visibility":  data.get("visibility", 10000),
        }
    except Exception as e:
        st.warning(f"[Campus weather API] {e}")
        return {}


def _get_aqi_owm(lat: float, lon: float) -> dict:
    try:
        url  = (f"http://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}")
        data = requests.get(url, timeout=5).json()
        comp = data["list"][0]["components"]
        idx  = data["list"][0]["main"]["aqi"]
        aqi_map = {1: 25, 2: 60, 3: 100, 4: 150, 5: 220}
        return {"aqi_approx": aqi_map.get(idx, 100),
                "pm25": comp.get("pm2_5", 0), "no2": comp.get("no2", 0)}
    except:
        return {}


def get_fused_micro_climate(city: str = "Kochi") -> dict:
    weather  = _get_weather_api(city)
    aqi_owm  = _get_aqi_owm(CAMPUS_PROFILE["lat"], CAMPUS_PROFILE["lon"])
    api_temp = weather.get("temp", 32.0)
    api_aqi  = aqi_owm.get("aqi_approx", 80)
    sensor   = read_local_sensors()
    urban    = compute_urban_factors(sensor, api_temp)
    local_t  = sensor["temperature_c"]
    local_rh = sensor["humidity_pct"]
    indoor   = simulate_indoor_temperature(local_t)
    return {
        "campus":           CAMPUS_PROFILE["name"],
        "city":             weather.get("city", city),
        "terrain":          CAMPUS_PROFILE["terrain"],
        "api_temp_c":       api_temp,
        "sensor_temp_c":    local_t,
        "corrected_temp_c": urban["corrected_temp_c"],
        "temp_gap_c":       urban["sensor_vs_api_gap"],
        "heat_index_c":     compute_heat_index(local_t, local_rh),
        "dew_point_c":      compute_dew_point(local_t, local_rh),
        "humidity_pct":     local_rh,
        "feels_like_c":     compute_heat_index(local_t, local_rh),
        "aqi_api":          api_aqi,
        "aqi_local":        sensor["aqi_local"],
        "aqi_fused":        round(max(api_aqi + urban["total_aqi_offset"], sensor["aqi_local"])),
        "pm25":             sensor["pm25_local"],
        "pm10":             sensor["pm10_local"],
        "co_ppm":           sensor["co_ppm"],
        "no2_api":          aqi_owm.get("no2", 0),
        "wind_speed_ms":    weather.get("wind_speed", 0),
        "wind_deg":         weather.get("wind_deg", 0),
        "description":      weather.get("description", "N/A"),
        "urban_factors":    urban,
        "diurnal":          get_diurnal_phase(),
        "sensor_raw":       sensor,
        "indoor":           indoor,          # ← NEW: indoor temperature data
    }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION B — Simple outside-location fetcher
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
        st.warning(f"[Outdoor weather] {e}")
        return None


def get_aqi_outside(lat: float, lon: float):
    try:
        url  = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQI_API_KEY}"
        data = requests.get(url, timeout=5).json()
        if data.get("status") != "ok":
            return None
        return data["data"]["aqi"]
    except Exception as e:
        st.warning(f"[Outdoor AQI] {e}")
        return None


def get_5day_forecast(lat: float, lon: float):
    """
    Fetches 5-day forecast from OpenWeatherMap /forecast endpoint (3-hour intervals).
    Groups by day to return daily min/max temperatures and rain totals.
    """
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        )
        data = requests.get(url, timeout=5).json()

        # The API returns cod as string "200" for this endpoint
        if str(data.get("cod")) != "200":
            return None

        # Group 3-hour slots by date
        daily = {}
        for entry in data["list"]:
            date_str = entry["dt_txt"].split(" ")[0]
            temp     = entry["main"]["temp"]
            rain     = entry.get("rain", {}).get("3h", 0)
            desc     = entry["weather"][0]["description"]

            if date_str not in daily:
                daily[date_str] = {
                    "date":        date_str,
                    "temps":       [],
                    "rain":        0.0,
                    "description": desc,
                }
            daily[date_str]["temps"].append(temp)
            daily[date_str]["rain"] += rain

        # Build clean daily list (max 5 days)
        forecast = []
        for date_str, d in sorted(daily.items()):
            forecast.append({
                "date":        d["date"],
                "temp_min":    round(min(d["temps"]), 1),
                "temp_max":    round(max(d["temps"]), 1),
                "description": d["description"].capitalize(),
                "rain":        round(d["rain"], 1),
            })

        return forecast[:5]

    except Exception as e:
        st.warning(f"[Forecast API] {e}")
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


def get_outside_data(place: str):
    coords = get_coordinates(place)
    if not coords:
        return None
    lat, lon = coords
    weather = get_weather_by_coords(lat, lon)
    if not weather:
        return None
    raw_aqi = get_aqi_outside(lat, lon)
    if raw_aqi is None:
        return None
    loc_type = classify_location(place)
    adj_aqi  = adjust_aqi(int(raw_aqi), loc_type)
    explanation_map = {
        "industrial": "Industrial area → AQI +30 (heavy particulates)",
        "traffic":    "Traffic zone → AQI +20 (vehicle emissions)",
        "coastal":    "Coastal area → AQI −10 (sea breeze dispersal)",
        "urban":      "Urban area — no major adjustment",
    }
    weather.update({
        "aqi_raw":       int(raw_aqi),
        "aqi_adjusted":  adj_aqi,
        "location_type": loc_type,
        "explanation":   explanation_map[loc_type],
    })
    return weather


# ═════════════════════════════════════════════════════════════════════════════
# SECTION C — Risk helpers (shared)
# ═════════════════════════════════════════════════════════════════════════════

def classify_aqi_level(aqi: float) -> tuple:
    if aqi <= 50:   return "Good", "🟢"
    if aqi <= 100:  return "Moderate", "🟡"
    if aqi <= 150:  return "Unhealthy (Sensitive)", "🟠"
    if aqi <= 200:  return "Unhealthy", "🔴"
    if aqi <= 300:  return "Very Unhealthy", "🟣"
    return "Hazardous", "⛔"


def classify_heat_level(hi: float) -> tuple:
    if hi < 27:  return "Comfortable", "🟢"
    if hi < 32:  return "Moderate", "🟡"
    if hi < 40:  return "High", "🟠"
    if hi < 46:  return "Extreme", "🔴"
    return "Critical", "⛔"


# ═════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NEXUS — Inside vs Outside",
    page_icon="🌡️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .big-val    { font-size:2.6rem; font-weight:700; line-height:1.1; }
  .label      { font-size:0.78rem; color:#aaa; text-transform:uppercase; letter-spacing:.08em; }
  .tag        { display:inline-block; border-radius:4px; padding:2px 8px;
                font-size:0.75rem; font-weight:600; }
  .tag-red    { background:#ff4b4b22; color:#ff4b4b; }
  .tag-orange { background:#ffa50022; color:#ffa500; }
  .tag-yellow { background:#ffd70022; color:#ffd700; }
  .tag-green  { background:#00c85322; color:#00c853; }
  .divider-v  { border-left: 2px solid #333; height: 100%; }
  .inside-header  { background:linear-gradient(135deg,#1a1a2e,#16213e);
                    border-radius:12px; padding:1rem 1.4rem; margin-bottom:.5rem; }
  .outside-header { background:linear-gradient(135deg,#0d2137,#0a3d2b);
                    border-radius:12px; padding:1rem 1.4rem; margin-bottom:.5rem; }

  /* Indoor temperature card */
  .indoor-card {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0;
    border: 1px solid #2a4a5a;
    display: flex;
    align-items: center;
    gap: 1.2rem;
  }
  .indoor-temp-big {
    font-size: 2.8rem;
    font-weight: 800;
    color: #e0f7fa;
    line-height: 1;
  }
  .indoor-badge {
    display: inline-block;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.82rem;
    font-weight: 700;
    margin-top: 6px;
  }
  .indoor-label {
    font-size: 0.75rem;
    color: #90a4ae;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
</style>
""", unsafe_allow_html=True)

# ── TITLE ─────────────────────────────────────────────────────────────────────
st.markdown("## 🌡️ NEXUS — Campus Inside vs Outside")
st.caption("Left: Campus micro-climate (sensor fusion) · Right: Your chosen outside location (live API)")
st.divider()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Settings")
    campus_city   = st.text_input("Campus city (API baseline)", value="Kochi")
    outside_place = st.text_input("Outside location to compare", value="Ernakulam")
    st.markdown("---")
    construction  = st.toggle("Active construction nearby", value=False)
    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()
    st.info(
        "**Inside** = NEXUS sensor fusion\n\n"
        "API baseline + physical sensors + urban factor corrections\n\n"
        "**Outside** = Simple live fetch\n\n"
        "Geocode → Weather → AQI → Location-type adjustment"
    )

CAMPUS_PROFILE["construction_active"] = construction

# ── FETCH ─────────────────────────────────────────────────────────────────────
with st.spinner("Fetching data from both environments…"):
    fused   = get_fused_micro_climate(campus_city)
    outside = get_outside_data(outside_place)

    # Fetch 5-day forecast for OUTSIDE location
    forecast_data = None
    if outside:
        forecast_data = get_5day_forecast(outside["lat"], outside["lon"])

# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📊 Dashboard", "📅 5-Day Forecast"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — DASHBOARD (original dual panel + indoor temp card)
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    inside_col, sep_col, outside_col = st.columns([1, 0.03, 1])

    # ──────────────── LEFT: INSIDE (NEXUS) ────────────────────────────────────
    with inside_col:
        hi_level, hi_icon   = classify_heat_level(fused["heat_index_c"])
        aqi_level, aqi_icon = classify_aqi_level(fused["aqi_fused"])
        indoor              = fused["indoor"]

        st.markdown(
            f'<div class="inside-header">'
            f'<span style="font-size:1.1rem;font-weight:700;">🏢 INSIDE — {fused["campus"]}</span><br>'
            f'<span style="color:#aaa;font-size:.8rem;">Sensor fusion · {fused["city"]} API baseline</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── INDOOR TEMPERATURE CARD (NEW) ──────────────────────────────────
        ac_label = "🌀 AC Active" if indoor["ac_active"] else "🌙 AC Off (night)"
        st.markdown(
            f"""
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
                <div class="indoor-label">vs Outdoor</div>
                <div style="font-size:1.4rem;font-weight:700;color:#b0bec5;">
                  {fused['sensor_temp_c']}°C
                </div>
                <div style="font-size:0.78rem;color:#78909c;">campus sensor</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Key metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Campus Temp",     f"{fused['sensor_temp_c']}°C",
                  delta=f"+{fused['temp_gap_c']}°C vs city API", delta_color="inverse")
        m2.metric("Heat Index",      f"{fused['heat_index_c']}°C")
        m3.metric("Fused AQI",       fused["aqi_fused"],
                  delta=f"+{fused['aqi_fused'] - fused['aqi_api']} vs API", delta_color="inverse")

        m4, m5, m6 = st.columns(3)
        m4.metric("Humidity",        f"{fused['humidity_pct']}%")
        m5.metric("Dew Point",       f"{fused['dew_point_c']}°C")
        m6.metric("PM 2.5",          f"{fused['pm25']} µg/m³")

        st.divider()

        # Risk tags
        st.markdown(
            f"**Heat risk:** {hi_icon} {hi_level} &nbsp;&nbsp; "
            f"**Air quality:** {aqi_icon} {aqi_level}",
            unsafe_allow_html=True,
        )

        st.divider()

        # Urban corrections
        urban = fused["urban_factors"]
        st.markdown("**Urban factor corrections applied:**")
        factors = []
        if urban.get("terrain_offset_c"):
            factors.append(f"🏗 Terrain +{urban['terrain_offset_c']}°C")
        if urban.get("vegetation_cooling_c"):
            factors.append(f"🌿 Vegetation −{urban['vegetation_cooling_c']}°C")
        if urban.get("traffic_aqi_bump"):
            factors.append(f"🚗 Traffic AQI +{urban['traffic_aqi_bump']} ({urban['traffic_label']})")
        if urban.get("canyon_aqi_bump"):
            factors.append(f"🏙 Building canyon AQI +{urban['canyon_aqi_bump']}")
        if urban.get("nocturnal_heat_island"):
            factors.append(f"🌙 Nocturnal heat island +{urban['nocturnal_delta_c']}°C")
        if urban.get("construction_active"):
            factors.append(f"🚧 Construction PM10 +{urban['construction_pm10_bump']}")
        for f_item in factors:
            st.markdown(f"- {f_item}")

        st.divider()

        d = fused["diurnal"]
        st.markdown(f"**Diurnal phase:** {d['phase']} (hour {d['hour']:02d}:00)")
        st.caption(d["note"])

    # ──────────────── SEPARATOR ───────────────────────────────────────────────
    with sep_col:
        st.markdown(
            '<div style="border-left:2px solid #333;height:700px;margin-top:60px"></div>',
            unsafe_allow_html=True,
        )

    # ──────────────── RIGHT: OUTSIDE ──────────────────────────────────────────
    with outside_col:
        if not outside:
            st.error("Could not fetch outside data. Check location name or API keys.")
        else:
            o_aqi_level, o_aqi_icon = classify_aqi_level(outside["aqi_adjusted"])
            o_hi                     = compute_heat_index(outside["temp"], outside["humidity"])
            o_hi_level, o_hi_icon    = classify_heat_level(o_hi)

            st.markdown(
                f'<div class="outside-header">'
                f'<span style="font-size:1.1rem;font-weight:700;">🌍 OUTSIDE — {outside["city"]}</span><br>'
                f'<span style="color:#aaa;font-size:.8rem;">'
                f'{outside["location_type"].title()} zone · live API fetch'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            n1, n2, n3 = st.columns(3)
            n1.metric("Temperature",  f"{outside['temp']}°C")
            n2.metric("Feels Like",   f"{outside['feels_like']}°C")
            n3.metric("Adjusted AQI", outside["aqi_adjusted"],
                      delta=f"{outside['aqi_adjusted'] - outside['aqi_raw']:+d} vs raw",
                      delta_color="inverse")

            n4, n5, n6 = st.columns(3)
            n4.metric("Humidity",     f"{outside['humidity']}%")
            n5.metric("Wind",         f"{outside['wind_speed']} m/s")
            n6.metric("Rain (1h)",    f"{outside['rain']} mm")

            st.divider()

            st.markdown(
                f"**Heat risk:** {o_hi_icon} {o_hi_level} &nbsp;&nbsp; "
                f"**Air quality:** {o_aqi_icon} {o_aqi_level}",
                unsafe_allow_html=True,
            )

            st.divider()

            st.markdown("**Location-type AQI adjustment:**")
            st.info(outside["explanation"])

            st.markdown("**Condition:**")
            st.markdown(f"🌤 {outside['description'].capitalize()}")

            st.divider()
            st.markdown(f"**Heat index (calc):** {o_hi}°C")
            st.markdown(f"**Dew point:** {compute_dew_point(outside['temp'], outside['humidity'])}°C")



# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — 5-DAY FORECAST (NEW)
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"### 📅 5-Day Temperature Forecast")

    if outside:
        st.caption(f"Location: **{outside['city']}** — daily min/max temperatures and rainfall")
    else:
        st.caption("Forecast for the outside location you selected.")

    if not forecast_data:
        st.warning("Could not load forecast data. Check API keys or location name.")
    else:
        # ── Plotly bar chart: min/max temps ───────────────────────────────────
        try:
            import plotly.graph_objects as go

            dates    = [d["date"] for d in forecast_data]
            temp_min = [d["temp_min"] for d in forecast_data]
            temp_max = [d["temp_max"] for d in forecast_data]
            rain     = [d["rain"] for d in forecast_data]

            fig = go.Figure()

            # Min temperature bars
            fig.add_trace(go.Bar(
                name="Min Temp (°C)",
                x=dates,
                y=temp_min,
                marker_color="#5b9bd5",
                text=[f"{v}°C" for v in temp_min],
                textposition="outside",
            ))

            # Max temperature bars
            fig.add_trace(go.Bar(
                name="Max Temp (°C)",
                x=dates,
                y=temp_max,
                marker_color="#ff6b6b",
                text=[f"{v}°C" for v in temp_max],
                textposition="outside",
            ))

            fig.update_layout(
                title=dict(
                    text="5-Day Min / Max Temperature",
                    font=dict(size=18, color="#e0e0e0"),
                ),
                barmode="group",
                xaxis=dict(
                    title=dict(text="Date", font=dict(color="#b0bec5")),
                    tickfont=dict(color="#b0bec5"),
                ),
                yaxis=dict(
                    title=dict(text="Temperature (°C)", font=dict(color="#b0bec5")),
                    tickfont=dict(color="#b0bec5"),
                    range=[min(temp_min) - 3, max(temp_max) + 5],
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,20,30,0.6)",
                legend=dict(
                    font=dict(color="#e0e0e0"),
                    bgcolor="rgba(0,0,0,0.3)",
                ),
                font=dict(color="#e0e0e0"),
                height=420,
                margin=dict(t=60, b=40, l=50, r=20),
            )

            fig.update_yaxes(gridcolor="#1e2a36", zerolinecolor="#1e2a36")

            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            # Fallback if plotly is not installed: show a simple bar using st.bar_chart
            import pandas as pd
            df = {
                "Date":     dates,
                "Min °C":   temp_min,
                "Max °C":   temp_max,
            }
            st.bar_chart(data=df, x="Date", y=["Min °C", "Max °C"], height=380)

        # ── Forecast detail table ─────────────────────────────────────────────
        st.markdown("#### 📋 Daily Breakdown")
        cols = st.columns(len(forecast_data))
        for i, day in enumerate(forecast_data):
            with cols[i]:
                # Pick weather icon based on description
                desc_lower = day["description"].lower()
                if "rain" in desc_lower or "drizzle" in desc_lower:
                    icon = "🌧"
                elif "cloud" in desc_lower:
                    icon = "☁️"
                elif "clear" in desc_lower:
                    icon = "☀️"
                elif "storm" in desc_lower or "thunder" in desc_lower:
                    icon = "⛈"
                elif "snow" in desc_lower:
                    icon = "❄️"
                elif "mist" in desc_lower or "fog" in desc_lower:
                    icon = "🌫"
                else:
                    icon = "🌤"

                # Format date nicely (e.g. "Mon\n28 Mar")
                try:
                    dt = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
                    day_label = dt.strftime("%a")
                    date_label = dt.strftime("%-d %b")
                except Exception:
                    day_label = day["date"]
                    date_label = ""

                st.markdown(
                    f"""
                    <div style="background:linear-gradient(135deg,#0f2027,#1c3a4a);
                                border-radius:12px;padding:1rem;text-align:center;
                                border:1px solid #1e3a4a;">
                      <div style="font-size:0.7rem;color:#90a4ae;text-transform:uppercase;
                                  letter-spacing:0.1em;">{day_label}</div>
                      <div style="font-size:0.85rem;color:#b0bec5;margin-bottom:6px;">{date_label}</div>
                      <div style="font-size:2rem;">{icon}</div>
                      <div style="font-size:0.72rem;color:#78909c;margin:4px 0;">{day['description']}</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#ff6b6b;">
                        ↑ {day['temp_max']}°C
                      </div>
                      <div style="font-size:1rem;color:#5b9bd5;">
                        ↓ {day['temp_min']}°C
                      </div>
                      <div style="font-size:0.78rem;color:#64b5f6;margin-top:6px;">
                        💧 {day['rain']} mm
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.caption("Rain values are cumulative totals for the day across all 3-hour forecast slots.")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
ts = fused.get("sensor_raw", {}).get("timestamp", str(datetime.datetime.now()))
st.caption(
    f"Last updated: {ts}  ·  "
    f"Inside: OpenWeatherMap + WAQI + NEXUS Local Sensor + Urban Factor Engine  ·  "
    f"Outside: OpenWeatherMap + WAQI (location-type adjusted)  ·  "
    f"Forecast: OpenWeatherMap /forecast (3-hour intervals, grouped daily)"
)