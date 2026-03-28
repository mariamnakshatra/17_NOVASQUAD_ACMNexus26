"""
NEXUS | Climate Intelligence Twin
----------------------------------
Full app with 4 tabs:
  Tab 1 — Dashboard
  Tab 2 — Flood Risk Map
  Tab 3 — Indoor Climate
  Tab 4 — 5-Day Forecast

FIX: City search now drives ALL tabs — weather, flood map, indoor analysis, forecast.
Sidebar sliders become manual override mode (toggle on/off).

Run:
    pip install streamlit pandas requests plotly
    streamlit run nexus_full.py
"""

import streamlit as st
import pandas as pd
import requests
import datetime
import math
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS | Climate Intelligence Twin",
    page_icon="🌍",
    layout="wide",
)

st.markdown("""
<style>
.stMetric {
    background-color: #161b22;
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #30363d;
}
.indoor-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.indoor-card-danger  { border-left: 4px solid #ef4444; }
.indoor-card-warning { border-left: 4px solid #f97316; }
.indoor-card-safe    { border-left: 4px solid #22c55e; }
.metric-row { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.mini-metric {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px 16px;
    flex: 1;
    text-align: center;
    min-width: 100px;
}
.mini-val   { font-size: 1.6rem; font-weight: 700; color: #f1f5f9; }
.mini-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase;
              letter-spacing: .07em; margin-top: 2px; }
.city-badge {
    display: inline-block;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# API KEY
# ─────────────────────────────────────────────────────────────────────────────
WEATHER_API_KEY = "8c1d1f75ee0374a3e1eaa4985e2930ed"

# ─────────────────────────────────────────────────────────────────────────────
# LIVE WEATHER FETCH  — drives all tabs
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_live_weather(city: str) -> dict | None:
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
        )
        r = requests.get(url, timeout=6)
        d = r.json()
        if d.get("cod") != 200:
            return None

        wind_deg = d["wind"].get("deg", 0)
        dirs = ["N","NE","E","SE","S","SW","W","NW"]
        wind_dir = dirs[round(wind_deg / 45) % 8]

        return {
            "city":        d["name"],
            "country":     d["sys"]["country"],
            "temp":        round(d["main"]["temp"], 1),
            "feels_like":  round(d["main"]["feels_like"], 1),
            "humidity":    d["main"]["humidity"],
            "pressure":    d["main"]["pressure"],
            "wind_speed":  d["wind"]["speed"],
            "wind_dir":    wind_dir,
            "wind_deg":    wind_deg,
            "description": d["weather"][0]["description"].capitalize(),
            "icon":        d["weather"][0]["icon"],
            "rain_1h":     d.get("rain", {}).get("1h", 0.0),
            "lat":         d["coord"]["lat"],
            "lon":         d["coord"]["lon"],
            "visibility":  d.get("visibility", 10000),
        }
    except Exception as e:
        return None


@st.cache_data(ttl=1800)
def fetch_forecast(city: str):
    try:
        geo = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct"
            f"?q={city}&limit=1&appid={WEATHER_API_KEY}",
            timeout=5,
        ).json()
        if not geo:
            return None, "City not found."
        lat, lon = geo[0]["lat"], geo[0]["lon"]
        name = geo[0].get("name", city)
        fc = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric",
            timeout=5,
        ).json()
        if fc.get("cod") != "200":
            return None, fc.get("message", "unknown error")
        return fc, name
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# FORMULAS
# ─────────────────────────────────────────────────────────────────────────────
def calc_dew_point(temp: float, humidity: float) -> float:
    return round(temp - ((100 - humidity) / 5), 1)

def calc_heat_index(t: float, rh: float) -> float:
    hi = (-8.78 + 1.61*t + 2.34*rh - 0.146*t*rh
          - 0.0123*t**2 - 0.0164*rh**2
          + 0.00222*t**2*rh + 0.000725*t*rh**2
          - 0.00000358*t**2*rh**2)
    return round(hi, 1)

def get_flood_risk(rain: float):
    if rain == 0:     return "Safe",        "#22c55e", 0
    elif rain <= 3:   return "Low Risk",     "#eab308", 1
    elif rain <= 10:  return "Moderate",     "#f97316", 2
    else:             return "Flood Risk",   "#ef4444", 3


# ─────────────────────────────────────────────────────────────────────────────
# NEXUS PREDICTIVE ENGINE  (original logic, now takes computed values)
# ─────────────────────────────────────────────────────────────────────────────
def nexus_predictive_engine(temp, hum, press, rain, wind_dir, in_temp):
    predictions, alerts = [], []
    drain_limit = 20.0
    overflow = max(0, rain - drain_limit)

    if overflow > 10:
        alerts.append({
            "Level": "🚨 CALAMITY",
            "Issue": "Urban Flash Flood",
            "Details": "Drainage capacity exceeded. Street submergence imminent.",
        })
    if wind_dir in ["W", "WSW", "NW"] and hum > 85:
        alerts.append({
            "Level": "🌊 DISASTER",
            "Issue": "Tidal Incursion",
            "Details": "Sea-level surge predicted in coastal low-lying areas.",
        })

    dew_point = calc_dew_point(temp, hum)
    if in_temp < dew_point:
        predictions.append({
            "Category": "🏗️ Infrastructure",
            "Impact": "Internal Wall Sweat",
            "Insight": "Indoor temp is below Dew Point. High mold/short-circuit risk.",
        })
    if "W" in wind_dir and hum > 75:
        predictions.append({
            "Category": "⚡ Tech",
            "Impact": "Hardware Corrosion",
            "Insight": "Salt-mist infiltration. Keep electronics away from sea-facing windows.",
        })
    if temp > 32 and hum > 80:
        predictions.append({
            "Category": "🧠 Human",
            "Impact": "Cognitive Decline",
            "Insight": "Extreme Wet-Bulb temp. 40% drop in labor productivity predicted.",
        })
    if press < 1008:
        predictions.append({
            "Category": "🩺 Health",
            "Impact": "Pressure Migraine",
            "Insight": "Rapid barometric dip. High risk of joint pain and headaches.",
        })
    if hum > 88:
        predictions.append({
            "Category": "🧺 Logistics",
            "Impact": "Zero Evaporation",
            "Insight": "Clothes will not dry. High risk of microbial growth in fabrics.",
        })
    if temp > 30 and hum > 75:
        predictions.append({
            "Category": "🍎 Food",
            "Impact": "Shelf-life Decay",
            "Insight": "Fungal growth accelerated. Countertop spoilage risk 2×.",
        })

    return alerts, predictions, overflow


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.title("🌍 NEXUS: Localized Climate Intelligence Twin")
st.markdown("#### *Bridges the gap between Atmospheric Data and Human Impact*")

# ─────────────────────────────────────────────────────────────────────────────
# CITY SEARCH  — top of page, drives everything
# ─────────────────────────────────────────────────────────────────────────────
search_col, btn_col = st.columns([4, 1])
with search_col:
    city_input = st.text_input(
        "🔍 Search any city",
        value=st.session_state.get("active_city", "Kochi"),
        placeholder="e.g. Mumbai, Dubai, London, Tokyo...",
        label_visibility="collapsed",
    )
with btn_col:
    search_btn = st.button("Search", use_container_width=True, type="primary")

if search_btn and city_input.strip():
    st.session_state["active_city"] = city_input.strip()

active_city = st.session_state.get("active_city", "Kochi")

# ─────────────────────────────────────────────────────────────────────────────
# FETCH LIVE DATA
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner(f"Fetching live data for {active_city}..."):
    live = fetch_live_weather(active_city)

if live is None:
    st.error(f"Could not find weather data for **{active_city}**. Check the city name and try again.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — manual override
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 📍 {live['city']}, {live['country']}")
    st.caption(f"Live: {live['description']} · {live['temp']}°C")
    st.divider()

    st.markdown("### 🔧 Manual Override")
    use_override = st.toggle("Enable manual sliders", value=False)
    st.caption("Override live API data with custom values for simulation/demo.")

    s_temp  = st.slider("🌡 Outdoor Temp (°C)",  -10.0, 50.0, float(live["temp"]),   disabled=not use_override)
    s_hum   = st.slider("💧 Humidity (%)",          0,   100,  live["humidity"],       disabled=not use_override)
    s_press = st.slider("🔵 Pressure (hPa)",       950,  1040, live["pressure"],       disabled=not use_override)
    s_rain  = st.number_input("🌧 Rainfall (mm/h)",  0.0, 200.0, float(live["rain_1h"]), disabled=not use_override)
    s_wind  = st.selectbox(
        "💨 Wind Direction",
        ["N","S","E","W","NW","NE","SW","SE"],
        index=["N","S","E","W","NW","NE","SW","SE"].index(live["wind_dir"]) if live["wind_dir"] in ["N","S","E","W","NW","NE","SW","SE"] else 0,
        disabled=not use_override,
    )
    st.divider()
    st.markdown("### 🏠 Indoor AC Setting")
    s_in_temp = st.slider("❄️ Indoor AC Temp (°C)", 16, 30, 22)

# Use live or override values
if use_override:
    t, h, p, r, wd = s_temp, s_hum, s_press, s_rain, s_wind
else:
    t   = live["temp"]
    h   = live["humidity"]
    p   = live["pressure"]
    r   = live["rain_1h"]
    wd  = live["wind_dir"]

lat = live["lat"]
lon = live["lon"]

# Derived
dew_pt = calc_dew_point(t, h)
hi_val = calc_heat_index(t, h)
risk_label, risk_color, risk_score = get_flood_risk(r)
alerts, predictions, overflow = nexus_predictive_engine(t, h, p, r, wd, s_in_temp)

# ─────────────────────────────────────────────────────────────────────────────
# STATUS BAR
# ─────────────────────────────────────────────────────────────────────────────
st.info(
    f"📍 **{live['city']}, {live['country']}** · "
    f"{live['description']} · "
    f"Wind: {wd} at {live['wind_speed']} m/s · "
    f"{'🔧 Manual override active' if use_override else '🛰️ Live API data'}"
)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "🌊 Flood Risk Map",
    "🏠 Indoor Climate",
    "📅 5-Day Forecast",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🌡 Temperature",    f"{t}°C",   delta=f"Feels {hi_val}°C")
    m2.metric("💧 Humidity",       f"{h}%")
    m3.metric("🔵 Pressure",       f"{p} hPa", delta="Low" if p < 1008 else "Normal",
              delta_color="inverse" if p < 1008 else "normal")
    m4.metric("🌧 Rainfall",       f"{r} mm/h")
    m5.metric("⚡ Drainage load",  f"{overflow:.1f} mm/h",
              delta=overflow, delta_color="inverse")

    if alerts:
        st.subheader("⚠️ Critical Calamity Warnings")
        for a in alerts:
            st.error(f"**{a['Level']}**: {a['Issue']} — {a['Details']}")

    st.divider()
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🧠 Multi-Layer Predictive Intelligence")
        df = pd.DataFrame(predictions)
        if not df.empty:
            st.table(df)
        else:
            st.success("All systems stable. No micro-risks detected.")

    with col_right:
        st.subheader("🏗️ Structural Risk Visualization")
        st.write(f"**Calculated Dew Point:** {dew_pt}°C")
        st.write(f"**Indoor AC Setting:** {s_in_temp}°C")
        if s_in_temp < dew_pt:
            st.progress(100)
            st.error("CONDENSATION ACTIVE: Moisture is forming inside walls.")
        else:
            st.progress(30)
            st.success("THERMAL STABILITY: Indoor environment is safe.")

    st.divider()
    with st.expander("🛠️ Technical Merit & Logic Framework"):
        st.markdown("""
- **Rational Method Physics:** Q = C × I × A maps rainfall against local drainage capacity.
- **Biometeorology:** Barometric pressure trends predict joint pain and migraine triggers.
- **BIM Integration:** Indoor vs outdoor temperature gradients predict 'Building Sweat'.
- **Coastal Specificity:** Salinity-driven tech corrosion warnings from wind + humidity coupling.
""")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — FLOOD RISK MAP
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🗺️ Flood Risk Map")
    st.caption(f"Showing live conditions for **{live['city']}** — rainfall {r} mm/h")

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Rainfall",   f"{r} mm/h")
    rc2.metric("Risk Level",  risk_label)
    rc3.metric("Coordinates", f"{lat:.4f}, {lon:.4f}")

    leaflet_html = f"""
<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0e1117; }}
#map {{ width:100%; height:460px; border-radius:12px; border:1px solid #30363d; }}
.risk-dot {{
    width:22px; height:22px; border-radius:50%;
    border:3px solid rgba(255,255,255,0.3);
    animation: pulse 2s ease-in-out infinite;
}}
@keyframes pulse {{
    0%,100% {{ box-shadow:0 0 10px 3px var(--glow); transform:scale(1); }}
    50%      {{ box-shadow:0 0 20px 8px var(--glow); transform:scale(1.12); }}
}}
.leaflet-popup-content-wrapper {{
    background:#161b22 !important; border:1px solid #30363d !important;
    border-radius:12px !important; padding:0 !important;
    box-shadow:0 8px 24px rgba(0,0,0,0.5) !important;
}}
.leaflet-popup-tip {{ background:#161b22 !important; }}
.leaflet-popup-content {{ margin:0 !important; }}
.popup-card {{ padding:14px 18px; min-width:210px; font-family:-apple-system,sans-serif; }}
.popup-title {{ font-size:13px; font-weight:700; color:#e2e8f0; margin-bottom:10px; }}
.popup-row {{ display:flex; justify-content:space-between; margin-bottom:6px; font-size:12px; }}
.popup-label {{ color:#64748b; }}
.popup-value {{ color:#e2e8f0; font-weight:600; }}
.popup-badge {{
    display:inline-block; margin-top:10px; padding:3px 12px;
    border-radius:999px; font-size:11px; font-weight:700; letter-spacing:.06em;
}}
.legend {{
    position:absolute; bottom:24px; left:12px; z-index:1000;
    background:rgba(22,27,34,0.95); border:1px solid #30363d;
    border-radius:10px; padding:10px 14px;
    font-family:-apple-system,sans-serif; font-size:11px; color:#94a3b8; line-height:2;
}}
.legend b {{ color:#64748b; font-size:10px; text-transform:uppercase; letter-spacing:.08em; }}
.dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; }}
</style>
</head><body>
<div style="position:relative;">
  <div id="map"></div>
  <div class="legend">
    <b>Flood Risk</b><br>
    <span class="dot" style="background:#22c55e"></span>Safe — 0 mm<br>
    <span class="dot" style="background:#eab308"></span>Low — 1–3 mm<br>
    <span class="dot" style="background:#f97316"></span>Moderate — 3–10 mm<br>
    <span class="dot" style="background:#ef4444"></span>Flood risk — 10+ mm
  </div>
</div>
<script>
const lat={lat}, lon={lon}, rain={r};
const riskLabel="{risk_label}", riskColor="{risk_color}";
const cityName="{live['city']}";

const map = L.map('map', {{center:[lat,lon], zoom:12}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
  {{attribution:'&copy; CARTO', subdomains:'abcd', maxZoom:19}}).addTo(map);

L.circle([lat,lon], {{
  radius:10000, color:riskColor, fillColor:riskColor,
  fillOpacity:0.1, weight:1.5, opacity:0.45
}}).addTo(map);

const icon = L.divIcon({{
  className:'',
  html:`<div class="risk-dot" style="background:${{riskColor}};--glow:${{riskColor}}80;"></div>`,
  iconSize:[22,22], iconAnchor:[11,11], popupAnchor:[0,-14]
}});

const popup = `
<div class="popup-card">
  <div class="popup-title">📍 ${{cityName}} — Flood Risk</div>
  <div class="popup-row"><span class="popup-label">🌧 Rainfall</span><span class="popup-value">${{rain}} mm/h</span></div>
  <div class="popup-row"><span class="popup-label">📍 Coordinates</span><span class="popup-value">${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}</span></div>
  <div class="popup-row"><span class="popup-label">⚠️ Risk</span><span class="popup-value" style="color:${{riskColor}}">${{riskLabel}}</span></div>
  <div><span class="popup-badge" style="background:${{riskColor}}22;color:${{riskColor}};border:1px solid ${{riskColor}}55;">${{riskLabel.toUpperCase()}}</span></div>
</div>`;

L.marker([lat,lon],{{icon}}).addTo(map).bindPopup(popup,{{maxWidth:260}}).openPopup();
</script></body></html>
"""
    st.components.v1.html(leaflet_html, height=480, scrolling=False)

    advice_map = {
        0: ("✅ No flood risk. Conditions are normal.", "success"),
        1: ("🟡 Light rain. Watch for waterlogging in low-lying areas.", "warning"),
        2: ("🟠 Moderate rain. Avoid underpasses and low roads.", "warning"),
        3: ("🔴 Heavy rain — flood risk active. Avoid all low-lying areas.", "error"),
    }
    msg, kind = advice_map[risk_score]
    getattr(st, kind)(msg)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — INDOOR CLIMATE
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader(f"🏠 Indoor vs Outdoor Climate — {live['city']}")
    st.caption("Outdoor values from live API · Indoor AC temp from sidebar slider")

    st.markdown(f"""
    <div class="metric-row">
      <div class="mini-metric">
        <div class="mini-val">{t}°C</div>
        <div class="mini-label">Outdoor temp</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{s_in_temp}°C</div>
        <div class="mini-label">Indoor AC temp</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{dew_pt}°C</div>
        <div class="mini-label">Dew point</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{hi_val}°C</div>
        <div class="mini-label">Heat index</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{h}%</div>
        <div class="mini-label">Humidity</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    left, right = st.columns(2)

    with left:
        st.markdown("#### 🌡 Thermal Boundary Analysis")
        gap = round(s_in_temp - dew_pt, 1)
        condensation_active = s_in_temp < dew_pt

        st.markdown(f"""
        <div class="indoor-card {'indoor-card-danger' if condensation_active else 'indoor-card-safe'}">
            <div style="font-size:.8rem;color:#64748b;margin-bottom:10px;text-transform:uppercase;letter-spacing:.07em;">
                Dew point vs Indoor temp
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
                <div style="text-align:center;">
                    <div style="font-size:1.8rem;font-weight:700;color:#38bdf8;">{s_in_temp}°C</div>
                    <div style="font-size:.75rem;color:#64748b;">Indoor AC</div>
                </div>
                <div style="font-size:1.4rem;color:#475569;align-self:center;">{'&lt;' if condensation_active else '&gt;'}</div>
                <div style="text-align:center;">
                    <div style="font-size:1.8rem;font-weight:700;color:{'#ef4444' if condensation_active else '#22c55e'};">{dew_pt}°C</div>
                    <div style="font-size:.75rem;color:#64748b;">Dew point</div>
                </div>
            </div>
            <div style="font-size:.85rem;color:{'#ef4444' if condensation_active else '#22c55e'};font-weight:600;">
                {'⚠️ CONDENSATION ACTIVE — ' + str(abs(gap)) + '°C below dew point' if condensation_active
                 else '✅ SAFE — margin: ' + str(gap) + '°C above dew point'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if condensation_active:
            st.progress(100)
            st.error(
                f"**Condensation is actively forming inside walls.**\n\n"
                f"Raise AC setpoint above **{dew_pt}°C** to stop condensation. "
                f"Current humidity in {live['city']}: {h}% — dew point is high."
            )
        else:
            fill = max(0, min(100, int((1 - gap / 15) * 100)))
            st.progress(fill)
            st.success(
                f"**Thermal stability confirmed.** "
                f"Indoor temp is {gap}°C above the dew point — no moisture risk."
            )

        with st.expander("📖 What is dew point and why does it matter?"):
            st.markdown(f"""
**Dew point** is the temperature at which air becomes saturated and moisture condenses on surfaces.

**Formula used:**
```
Dew Point = Outdoor Temp − ((100 − Humidity) / 5)
         = {t} − ((100 − {h}) / 5) = {dew_pt}°C
```

**Current situation in {live['city']}:**
- Outdoor temp: **{t}°C**, Humidity: **{h}%**
- Dew point: **{dew_pt}°C**
- Your AC at **{s_in_temp}°C** is {'⚠️ **below** the dew point — condensation risk!' if condensation_active else '✅ **above** the dew point — safe.'}

**Safe rule:** Keep indoor AC at least 2°C above the dew point.
""")

    with right:
        st.markdown("#### ⚡ Environmental Risk Breakdown")

        salt_risk    = "W" in wd and h > 75
        laundry_risk = h > 88
        food_risk    = t > 30 and h > 75
        cog_risk     = t > 32 and h > 80

        st.markdown(f"""
        <div class="indoor-card {'indoor-card-warning' if salt_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                ⚡ Hardware / Electronics
            </div>
            <div style="font-weight:600;color:{'#f97316' if salt_risk else '#22c55e'};margin-bottom:4px;">
                {'Salt-mist infiltration DETECTED' if salt_risk else 'No corrosion risk'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Wind: {wd} · Humidity: {h}%<br>
                {'Keep electronics away from sea-facing windows.' if salt_risk else 'Conditions are safe for electronics.'}
            </div>
        </div>
        <div class="indoor-card {'indoor-card-warning' if laundry_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                🧺 Laundry & Fabric
            </div>
            <div style="font-weight:600;color:{'#f97316' if laundry_risk else '#22c55e'};margin-bottom:4px;">
                {'Zero evaporation — clothes will NOT dry' if laundry_risk else 'Normal drying conditions'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Humidity: {h}% (threshold: 88%)<br>
                {'High microbial risk in wet fabrics. Use dryer or fan.' if laundry_risk else 'Air-drying is effective.'}
            </div>
        </div>
        <div class="indoor-card {'indoor-card-warning' if food_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                🍎 Food Safety
            </div>
            <div style="font-weight:600;color:{'#f97316' if food_risk else '#22c55e'};margin-bottom:4px;">
                {'Accelerated spoilage — 2× fungal growth rate' if food_risk else 'Normal food shelf life'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Temp: {t}°C · Humidity: {h}%<br>
                {'Refrigerate all perishables.' if food_risk else 'Countertop storage is safe.'}
            </div>
        </div>
        <div class="indoor-card {'indoor-card-warning' if cog_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                🧠 Human Productivity
            </div>
            <div style="font-weight:600;color:{'#f97316' if cog_risk else '#22c55e'};margin-bottom:4px;">
                {'Extreme wet-bulb — 40% productivity drop predicted' if cog_risk else 'Comfortable working conditions'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Heat index: {hi_val}°C<br>
                {'Ensure AC and ventilation in {city}.' .format(city=live['city']) if cog_risk else 'No heat-related impairment expected.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🔵 Barometric Pressure Analysis")
    p_col1, p_col2 = st.columns([1, 2])
    with p_col1:
        migraine_risk = p < 1008
        st.metric("Pressure", f"{p} hPa",
                  delta="Below threshold" if migraine_risk else "Normal",
                  delta_color="inverse" if migraine_risk else "normal")
    with p_col2:
        if migraine_risk:
            st.warning(f"**{p} hPa** — below 1008 hPa. Barometric dip linked to joint pain and migraines.")
        else:
            st.success(f"**{p} hPa** — within normal range. No pressure-related warnings.")

    st.divider()
    st.markdown("#### 📋 Indoor Risk Summary")
    condensation_active = s_in_temp < dew_pt
    migraine_risk = p < 1008
    st.table(pd.DataFrame({
        "Risk Factor": ["Condensation", "Salt Corrosion", "Laundry Drying",
                        "Food Spoilage", "Cognitive Load", "Pressure Migraine"],
        "Status": [
            "🔴 ACTIVE"   if condensation_active else "🟢 Safe",
            "🟠 WARNING"  if salt_risk           else "🟢 Safe",
            "🟠 WARNING"  if laundry_risk        else "🟢 Safe",
            "🟠 WARNING"  if food_risk           else "🟢 Safe",
            "🟠 WARNING"  if cog_risk            else "🟢 Safe",
            "🟡 CAUTION"  if migraine_risk       else "🟢 Safe",
        ],
        "Key Value": [
            f"Indoor {s_in_temp}°C vs Dew {dew_pt}°C",
            f"Wind {wd}, Hum {h}%",
            f"Humidity {h}%",
            f"Temp {t}°C, Hum {h}%",
            f"Heat index {hi_val}°C",
            f"Pressure {p} hPa",
        ],
    }))


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — 5-DAY FORECAST
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader(f"📅 5-Day Forecast — {live['city']}")

    with st.spinner("Fetching forecast..."):
        fc_data, fc_name = fetch_forecast(active_city)

    if fc_data is None:
        st.error(f"Could not load forecast: {fc_name}")
    else:
        st.caption(f"Location resolved: **{fc_name}**")

        daily = defaultdict(lambda: {"temps": [], "rain": 0.0, "icons": [], "descs": []})
        for item in fc_data["list"]:
            date = item["dt_txt"][:10]
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["rain"] += item.get("rain", {}).get("3h", 0)
            daily[date]["icons"].append(item["weather"][0]["icon"])
            daily[date]["descs"].append(item["weather"][0]["description"])

        dates = sorted(daily.keys())[:5]
        mins  = [round(min(daily[d]["temps"]), 1) for d in dates]
        maxs  = [round(max(daily[d]["temps"]), 1) for d in dates]
        rains = [round(daily[d]["rain"], 1)        for d in dates]
        icons = [daily[d]["icons"][len(daily[d]["icons"])//2] for d in dates]
        descs = [daily[d]["descs"][len(daily[d]["descs"])//2].capitalize() for d in dates]

        st.markdown("#### 📆 Daily Breakdown")
        cols = st.columns(len(dates))
        for i, d in enumerate(dates):
            with cols[i]:
                icon_url = f"https://openweathermap.org/img/wn/{icons[i]}@2x.png"
                st.markdown(f"""
                <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;
                            padding:14px;text-align:center;">
                    <div style="font-size:.78rem;color:#64748b;">{d}</div>
                    <img src="{icon_url}" width="52" style="margin:6px 0;"/>
                    <div style="font-size:.78rem;color:#94a3b8;margin-bottom:8px;">{descs[i]}</div>
                    <div style="display:flex;justify-content:space-around;">
                        <div>
                            <div style="font-size:1.1rem;font-weight:700;color:#f87171;">{maxs[i]}°</div>
                            <div style="font-size:.7rem;color:#64748b;">High</div>
                        </div>
                        <div>
                            <div style="font-size:1.1rem;font-weight:700;color:#60a5fa;">{mins[i]}°</div>
                            <div style="font-size:.7rem;color:#64748b;">Low</div>
                        </div>
                    </div>
                    <div style="margin-top:8px;font-size:.78rem;color:#38bdf8;">🌧 {rains[i]} mm</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        try:
            import plotly.graph_objects as go

            st.markdown("#### 📈 Temperature Range")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=maxs, name="Max",
                line=dict(color="#f87171", width=2.5), marker=dict(size=7)))
            fig.add_trace(go.Scatter(x=dates, y=mins, name="Min",
                line=dict(color="#60a5fa", width=2.5), marker=dict(size=7),
                fill="tonexty", fillcolor="rgba(96,165,250,0.08)"))
            fig.update_layout(
                paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
                font=dict(color="#94a3b8"),
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b", title="°C"),
                legend=dict(bgcolor="#0e1117"),
                margin=dict(l=10, r=10, t=10, b=10), height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 🌧 Daily Rainfall")
            fig2 = go.Figure(go.Bar(
                x=dates, y=rains,
                marker_color=["#ef4444" if r > 10 else "#f97316" if r > 3
                               else "#eab308" if r > 0 else "#22c55e" for r in rains],
            ))
            fig2.update_layout(
                paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
                font=dict(color="#94a3b8"),
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b", title="mm"),
                margin=dict(l=10, r=10, t=10, b=10), height=220,
            )
            st.plotly_chart(fig2, use_container_width=True)

        except ImportError:
            st.warning("Install plotly for charts: `pip install plotly`")
            st.table(pd.DataFrame({"Date": dates, "Min °C": mins, "Max °C": maxs, "Rain mm": rains}))


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"NEXUS Engine v3.0 | {live['city']}, {live['country']} | "
    f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')} | "
    "Data: OpenWeatherMap · Leaflet.js · NEXUS Predictive Engine"
)

