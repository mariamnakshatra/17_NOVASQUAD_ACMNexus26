"""
app.py — EnviroCheck: Climate Risk Monitoring Dashboard
--------------------------------------------------------
Integrates:
  - data_fetcher.py  (real API data)
  - location_ai.py   (AQI adjustment by zone)
  - Flood risk map   (Leaflet.js via st.components.v1.html)

Install:
    pip install streamlit requests python-dotenv

Run:
    streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import math
import os
import datetime
from dotenv import load_dotenv

from data_fetcher import get_all_data
from location_ai import classify_location, adjust_aqi

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="EnviroCheck",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080e1a;
    color: #e2e8f0;
}

section[data-testid="stSidebar"] { display: none; }
.block-container { padding: 2rem 3rem 3rem 3rem; max-width: 1200px; }

.brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.subtitle { color: #64748b; font-size: 0.95rem; margin-top: 2px; margin-bottom: 1.5rem; }

div[data-testid="stTextInput"] input {
    background: #0f172a !important;
    border: 1.5px solid #1e293b !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    font-size: 1rem !important;
    padding: 0.65rem 1rem !important;
    transition: border-color .2s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.12) !important;
}

.env-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    transition: border-color .2s, transform .2s;
    margin-bottom: 0.5rem;
}
.env-card:hover { border-color: #38bdf8; transform: translateY(-2px); }
.card-icon  { font-size: 2rem; margin-bottom: .3rem; }
.card-label { font-size: .75rem; color: #64748b; text-transform: uppercase;
              letter-spacing: .08em; margin-bottom: .3rem; }
.card-value { font-size: 2rem; font-weight: 700; color: #f1f5f9; line-height: 1; }
.card-sub   { font-size: .8rem; color: #94a3b8; margin-top: .3rem; }

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin: 1.8rem 0 .8rem 0;
    padding-bottom: .4rem;
    border-bottom: 1px solid #1e293b;
}

.action-item {
    background: #0f172a;
    border-left: 3px solid #38bdf8;
    border-radius: 0 10px 10px 0;
    padding: .7rem 1rem;
    margin-bottom: .5rem;
    font-size: .93rem;
    color: #cbd5e1;
}

.loc-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 6px 14px;
    font-size: .85rem;
    color: #94a3b8;
    margin-bottom: 1rem;
}

hr { border-color: #1e293b !important; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FLOOD MAP HTML BUILDER
# ─────────────────────────────────────────────
def build_flood_map_html(lat, lon, rain, city, temp, humidity):
    """
    Returns a self-contained HTML string with a Leaflet.js flood risk map.
    Rendered inside Streamlit via st.components.v1.html().
    No extra installs needed — Leaflet loads from CDN.
    """
    if rain == 0:
        level, color = "Safe", "#22c55e"
    elif rain <= 3:
        level, color = "Low risk", "#eab308"
    elif rain <= 10:
        level, color = "Moderate", "#f97316"
    else:
        level, color = "Flood risk", "#ef4444"

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
    .pop {{
      padding:14px 16px; min-width:180px;
      font-family:-apple-system,sans-serif;
    }}
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
      fillColor:"{color}", fillOpacity:0.1,
      weight:1.5, opacity:0.5
    }}).addTo(map);
  </script>
</body>
</html>"""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def compute_heat_index(t, rh):
    hi = (-8.78 + 1.61*t + 2.34*rh - 0.146*t*rh
          - 0.0123*t**2 - 0.0164*rh**2
          + 0.00222*t**2*rh + 0.000725*t*rh**2
          - 0.00000358*t**2*rh**2)
    return round(hi, 1)

def compute_dew_point(t, rh):
    a, b = 17.27, 237.7
    g = (a * t / (b + t)) + math.log(rh / 100.0)
    return round((b * g) / (a - g), 1)

def classify_aqi_level(aqi):
    if aqi <= 50:   return "Good",                  "🟢"
    if aqi <= 100:  return "Moderate",              "🟡"
    if aqi <= 150:  return "Unhealthy (Sensitive)", "🟠"
    if aqi <= 200:  return "Unhealthy",             "🔴"
    return "Very Unhealthy",                         "🟣"

def get_flood_risk(rain):
    if rain == 0:   return "Safe",       "🟢", "#22c55e"
    if rain <= 3:   return "Low risk",   "🟡", "#eab308"
    if rain <= 10:  return "Moderate",  "🟠", "#f97316"
    return "Flood risk",                 "🔴", "#ef4444"


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<p class="brand">🌍 EnviroCheck</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Real-time climate & flood risk monitoring</p>',
    unsafe_allow_html=True,
)

city_input = st.text_input(
    "",
    placeholder="🔍  Search any city — e.g. Kochi, Delhi, Mumbai…",
    label_visibility="collapsed",
)

if not city_input.strip():
    st.markdown(
        '<div style="color:#475569;text-align:center;padding:4rem 0;font-size:1.05rem;">'
        '↑ Enter a city name to get live weather, air quality &amp; flood risk map'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─────────────────────────────────────────────
# FETCH  (your existing data_fetcher + location_ai)
# ─────────────────────────────────────────────
with st.spinner("Fetching live data…"):
    raw = get_all_data(city_input.strip())

if not raw:
    st.error("Could not fetch data. Check city name or API keys in your .env file.")
    st.stop()

loc_type     = classify_location(city_input.strip())
adjusted_aqi = adjust_aqi(raw["aqi"], loc_type)

loc_labels = {
    "industrial": "🏭 Industrial zone — AQI +30",
    "traffic":    "🚗 Traffic corridor — AQI +20",
    "coastal":    "🌊 Coastal zone — AQI −10",
    "urban":      "🏙 Urban area",
}

temp     = round(raw["temp"], 1)
humidity = raw["humidity"]
rain     = round(raw.get("rain", 0), 1)
lat      = raw["lat"]
lon      = raw["lon"]
heat_idx = compute_heat_index(temp, humidity)
dew_pt   = compute_dew_point(temp, humidity)
ts       = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

flood_level, flood_icon, flood_color = get_flood_risk(rain)
aqi_level,   aqi_icon                = classify_aqi_level(adjusted_aqi)

# ─────────────────────────────────────────────
# LOCATION BADGE
# ─────────────────────────────────────────────
st.markdown(
    f'<div class="loc-badge">📍 {city_input.title()} &nbsp;·&nbsp; '
    f'{loc_labels[loc_type]} &nbsp;·&nbsp; 🕐 {ts}</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊  Dashboard", "🌊  Flood Risk Map"])

# ════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════
with tab1:

    st.markdown('<p class="section-title">Current Conditions</p>',
                unsafe_allow_html=True)

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

    st.markdown('<p class="section-title">Risk Alerts</p>',
                unsafe_allow_html=True)

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

    st.markdown('<p class="section-title">Recommended Actions</p>',
                unsafe_allow_html=True)

    actions = []
    if temp > 38:
        actions.append("🔥 Dangerous heat — stay indoors, avoid all outdoor activity.")
    elif temp > 32:
        actions.append("🌡 High temp — limit outdoor time 12pm–4pm, stay hydrated.")
    if rain > 10:
        actions.append("🌊 Heavy rainfall — avoid low-lying areas, follow flood alerts.")
    elif rain > 3:
        actions.append("🌧 Moderate rain — carry umbrella, drive carefully.")
    if adjusted_aqi > 150:
        actions.append("😷 Unhealthy air — wear N95 mask, keep windows closed.")
    elif adjusted_aqi > 100:
        actions.append("🌫 Moderate AQI — sensitive groups limit outdoor time.")
    if dew_pt > 26:
        actions.append("💧 Very humid — risk of heat exhaustion, stay ventilated.")

    if actions:
        for a in actions:
            st.markdown(
                f'<div class="action-item">{a}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="action-item" style="border-left-color:#22c55e;">'
            '✅ All conditions safe. No special precautions needed.'
            '</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════
# TAB 2 — FLOOD RISK MAP
# ════════════════════════════════════════════
with tab2:

    fl1, fl2, fl3 = st.columns(3)
    fl1.metric("Rainfall (1h)",  f"{rain} mm")
    fl2.metric("Flood risk",     f"{flood_icon} {flood_level}")
    fl3.metric("Zone type",      loc_labels[loc_type])

    advice_map = {
        "Safe":       ("✅ No flood risk. Conditions are safe.", "success"),
        "Low risk":   ("🟡 Light rain. Watch for waterlogging in low-lying areas.", "warning"),
        "Moderate":   ("🟠 Moderate rain. Avoid underpasses and low roads.", "warning"),
        "Flood risk": ("🔴 Heavy rain — flood risk active. Avoid low areas now.", "error"),
    }
    msg, kind = advice_map[flood_level]
    getattr(st, kind)(msg)

    # Render the Leaflet map inside Streamlit
    map_html = build_flood_map_html(
        lat=lat, lon=lon, rain=rain,
        city=city_input.title(),
        temp=temp, humidity=humidity,
    )
    components.html(map_html, height=500, scrolling=False)

    st.caption(
        f"Centred on {city_input.title()} ({lat:.4f}, {lon:.4f})  ·  "
        f"Basemap: CartoDB Dark  ·  Risk thresholds: IMD standard"
    )


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<p style="color:#334155;font-size:.8rem;text-align:center;">'
    f'EnviroCheck · Data: OpenWeatherMap + WAQI · {ts}'
    f'</p>',
    unsafe_allow_html=True,
)