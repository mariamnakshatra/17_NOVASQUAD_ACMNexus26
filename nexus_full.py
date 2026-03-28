"""
NEXUS | Climate Intelligence Twin
----------------------------------
Full app with 4 tabs:
  Tab 1 — Dashboard        (original NEXUS engine)
  Tab 2 — Flood Risk Map   (Leaflet.js via st.components)
  Tab 3 — Indoor Climate   (dew point, condensation, structural risks)
  Tab 4 — 5-Day Forecast   (OpenWeatherMap /forecast endpoint)

Run:
    pip install streamlit pandas requests
    streamlit run nexus_full.py
"""

import streamlit as st
import pandas as pd
import requests
import datetime
import math

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS | Climate Intelligence Twin",
    page_icon="🌍",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #0e1117; }
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
.metric-row {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
}
.mini-metric {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 12px 16px;
    flex: 1;
    text-align: center;
}
.mini-val   { font-size: 1.6rem; font-weight: 700; color: #f1f5f9; }
.mini-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase;
              letter-spacing: .07em; margin-top: 2px; }
section[data-testid="stSidebar"] .stSlider { margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# API KEY
# ─────────────────────────────────────────────────────────────────────────────
WEATHER_API_KEY = "8c1d1f75ee0374a3e1eaa4985e2930ed"

# ─────────────────────────────────────────────────────────────────────────────
# CORE INTELLIGENCE ENGINE  (original — untouched)
# ─────────────────────────────────────────────────────────────────────────────
def nexus_predictive_engine(temp, hum, press, rain, wind_dir, in_temp):
    predictions = []
    alerts = []

    # 1. NATURAL CALAMITY PREDICTIONS
    drain_limit = 20.0
    overflow = max(0, rain - drain_limit)
    if overflow > 10:
        alerts.append({
            "Level": "🚨 CALAMITY",
            "Issue": "Urban Flash Flood",
            "Details": "Perandoor Canal capacity exceeded. Street submergence imminent.",
        })

    if wind_dir in ["W", "WSW", "NW"] and hum > 85:
        alerts.append({
            "Level": "🌊 DISASTER",
            "Issue": "Tidal Incursion",
            "Details": "Sea-level surge predicted in Edakochi/Chellanam regions.",
        })

    # 2. INFRASTRUCTURE & BUILDING HEALTH
    dew_point = temp - ((100 - hum) / 5)
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

    # 3. HUMAN HEALTH & BIOMETEOROLOGY
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

    # 4. LOGISTICS & DAILY LIFE
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
            "Insight": "Fungal growth accelerated. Countertop spoilage risk increased by 2×.",
        })

    return alerts, predictions, overflow


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — heat index
# ─────────────────────────────────────────────────────────────────────────────
def heat_index(t, rh):
    hi = (-8.78 + 1.61*t + 2.34*rh - 0.146*t*rh
          - 0.0123*t**2 - 0.0164*rh**2
          + 0.00222*t**2*rh + 0.000725*t*rh**2
          - 0.00000358*t**2*rh**2)
    return round(hi, 1)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — flood risk
# ─────────────────────────────────────────────────────────────────────────────
def get_risk(rain):
    if rain == 0:      return "Safe",        "#22c55e", 0
    elif rain <= 3:    return "Low Risk",     "#eab308", 1
    elif rain <= 10:   return "Moderate",     "#f97316", 2
    else:              return "Flood Risk",   "#ef4444", 3


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.title("🌍 NEXUS: Localized Climate Intelligence Twin")
st.markdown("#### *Bridges the gap between Atmospheric Data and Human Impact*")
st.info("Target Region: **Thevara-Edakochi Corridor, Kochi** | Model Status: **Active**")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("📡 Live Sensor Feed")
s_temp  = st.sidebar.slider("🌡 Outdoor Temp (°C)",  20.0, 45.0, 31.0)
s_hum   = st.sidebar.slider("💧 Humidity (%)",        40,   100,  85)
s_press = st.sidebar.slider("🔵 Pressure (hPa)",      990,  1020, 1007)
s_rain  = st.sidebar.number_input("🌧 Rainfall (mm/h)", 0.0, 100.0, 25.0)
s_wind  = st.sidebar.selectbox(
    "💨 Wind Direction",
    ["N", "S", "E", "W", "NW", "NE", "SW", "SE"],
    index=3,
)

st.sidebar.divider()
st.sidebar.header("🏠 Indoor Environment")
s_in_temp = st.sidebar.slider("❄️ Indoor AC Temp (°C)", 16, 30, 22)

st.sidebar.divider()
st.sidebar.header("📍 Map Location")
s_lat = st.sidebar.number_input("Latitude",  value=9.9312,  format="%.4f")
s_lon = st.sidebar.number_input("Longitude", value=76.2673, format="%.4f")

# ─────────────────────────────────────────────────────────────────────────────
# RUN ENGINE
# ─────────────────────────────────────────────────────────────────────────────
alerts, predictions, overflow = nexus_predictive_engine(
    s_temp, s_hum, s_press, s_rain, s_wind, s_in_temp
)
dew_pt   = round(s_temp - ((100 - s_hum) / 5), 1)
hi_val   = heat_index(s_temp, s_hum)

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
# TAB 1 — DASHBOARD  (original, untouched)
# ═════════════════════════════════════════════════════════════════════════════
with tab1:

    # Row 1: Vital Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Atmospheric Temp",  f"{s_temp}°C")
    m2.metric("Relative Humidity", f"{s_hum}%")
    m3.metric("Rain Load",         f"{s_rain} mm/h")
    m4.metric("Drainage Overflow", f"{overflow:.1f} mm/h",
              delta=overflow, delta_color="inverse")

    # Row 2: Calamity Alerts
    if alerts:
        st.subheader("⚠️ Critical Calamity Warnings")
        for a in alerts:
            st.error(f"**{a['Level']}**: {a['Issue']} — {a['Details']}")

    st.divider()

    # Row 3: Intelligence Matrix
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
        st.write(f"**Current Indoor Setting:** {s_in_temp}°C")

        if s_in_temp < dew_pt:
            st.progress(100)
            st.error("CONDENSATION ACTIVE: Moisture is currently forming inside walls.")
        else:
            st.progress(30)
            st.success("THERMAL STABILITY: Indoor environment is safe.")

    st.divider()
    expander = st.expander("🛠️ Technical Merit & Logic Framework")
    expander.write("""
- **Rational Method Physics:** We use $Q = C \\times I \\times A$ to map rainfall against the specific drainage capacity of Kochi's canal network.
- **Biometeorology:** The algorithm tracks Barometric Pressure trends to predict joint pain and migraine triggers.
- **BIM Integration:** By comparing Indoor vs. Outdoor temperature gradients, we predict 'Building Sweat' (latent moisture failure).
- **Coastal Specificity:** Includes salinity-driven tech corrosion warnings based on wind-direction and humidity coupling.
""")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — FLOOD RISK MAP
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🗺️ Flood Risk Map")
    st.caption("Marker colour updates live from the Rainfall slider in the sidebar.")

    risk_label, risk_color, risk_score = get_risk(s_rain)

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Rainfall Input",  f"{s_rain} mm/h")
    rc2.metric("Risk Level",       risk_label)
    rc3.metric("Map Centre",       f"{s_lat:.4f}, {s_lon:.4f}")

    # Leaflet map
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
.popup-card {{ padding:14px 18px; min-width:190px; font-family:-apple-system,sans-serif; }}
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
const lat={s_lat}, lon={s_lon}, rain={s_rain};
const riskLabel="{risk_label}", riskColor="{risk_color}";

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
  <div class="popup-title">📍 Flood Risk Assessment</div>
  <div class="popup-row"><span class="popup-label">🌧 Rainfall</span><span class="popup-value">${{rain}} mm/h</span></div>
  <div class="popup-row"><span class="popup-label">📍 Location</span><span class="popup-value">${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}</span></div>
  <div class="popup-row"><span class="popup-label">⚠️ Risk</span><span class="popup-value" style="color:${{riskColor}}">${{riskLabel}}</span></div>
  <div><span class="popup-badge" style="background:${{riskColor}}22;color:${{riskColor}};border:1px solid ${{riskColor}}55;">${{riskLabel.toUpperCase()}}</span></div>
</div>`;

L.marker([lat,lon],{{icon}}).addTo(map).bindPopup(popup,{{maxWidth:240}}).openPopup();
</script></body></html>
"""
    st.components.v1.html(leaflet_html, height=480, scrolling=False)

    advice_map = {
        0: ("✅ No flood risk. Conditions are normal.", "success"),
        1: ("🟡 Light rain. Watch for waterlogging in low-lying areas.", "warning"),
        2: ("🟠 Moderate rain. Avoid underpasses and low roads. Stay alert.", "warning"),
        3: ("🔴 Heavy rain — flood risk active. Avoid all low-lying areas immediately.", "error"),
    }
    msg, kind = advice_map[risk_score]
    getattr(st, kind)(msg)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — INDOOR CLIMATE  ← THE FULL MODULE
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🏠 Indoor vs Outdoor Climate Analysis")
    st.caption("All values are driven by the sidebar sliders — adjust them to simulate different conditions.")

    # ── Top metric strip ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="metric-row">
      <div class="mini-metric">
        <div class="mini-val">{outdoor}°C</div>
        <div class="mini-label">Outdoor temp</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{indoor}°C</div>
        <div class="mini-label">Indoor AC temp</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{dew}°C</div>
        <div class="mini-label">Dew point</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{hi}°C</div>
        <div class="mini-label">Heat index</div>
      </div>
      <div class="mini-metric">
        <div class="mini-val">{hum}%</div>
        <div class="mini-label">Humidity</div>
      </div>
    </div>
    """.format(
        outdoor=s_temp,
        indoor=s_in_temp,
        dew=dew_pt,
        hi=hi_val,
        hum=s_hum,
    ), unsafe_allow_html=True)

    st.divider()

    # ── Two column layout ─────────────────────────────────────────────────────
    left, right = st.columns(2)

    # ── LEFT: Dew point / condensation ───────────────────────────────────────
    with left:
        st.markdown("#### 🌡 Thermal Boundary Analysis")

        gap = round(s_in_temp - dew_pt, 1)
        condensation_active = s_in_temp < dew_pt

        # Visual comparison bar
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
                {'⚠️ CONDENSATION ACTIVE — gap: ' + str(abs(gap)) + '°C below dew point' if condensation_active
                 else '✅ SAFE — margin: ' + str(gap) + '°C above dew point'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if condensation_active:
            st.progress(100)
            st.error(
                "**Condensation is actively forming inside walls.**\n\n"
                "Moisture accumulates behind surfaces when indoor temp drops below the dew point. "
                "This causes mould growth, paint peeling, and short-circuit risk in embedded wiring. "
                "Raise the AC setpoint above **" + str(dew_pt) + "°C** to stop condensation."
            )
        else:
            fill = max(0, min(100, int((1 - gap / 15) * 100)))
            st.progress(fill)
            st.success(
                f"**Thermal stability confirmed.** "
                f"Indoor temp is {gap}°C above the dew point — no moisture risk."
            )

        # Explanation of dew point
        with st.expander("📖 What is dew point and why does it matter?"):
            st.markdown("""
**Dew point** is the temperature at which air becomes saturated and moisture
begins to condense on surfaces.

**Formula used:**
```
Dew Point = Outdoor Temp − ((100 − Humidity) / 5)
```

**Why it matters indoors:**
- If your **AC is set below the dew point**, cold walls and surfaces attract moisture
- This moisture causes **mould**, **corrosion**, and **electrical short circuits**
- In Kerala's coastal humidity (often 85%+), dew points can be as high as 28–30°C
- Running AC below 22°C during monsoon is therefore high risk

**Safe rule:** Keep indoor AC setpoint **at least 2°C above the calculated dew point**.
""")

    # ── RIGHT: Environmental risk breakdown ──────────────────────────────────
    with right:
        st.markdown("#### ⚡ Environmental Risk Breakdown")

        # 1. Salt mist / hardware corrosion
        salt_risk = "W" in s_wind and s_hum > 75
        st.markdown(f"""
        <div class="indoor-card {'indoor-card-warning' if salt_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                ⚡ Hardware / Electronics
            </div>
            <div style="font-weight:600;color:{'#f97316' if salt_risk else '#22c55e'};margin-bottom:4px;">
                {'Salt-mist infiltration DETECTED' if salt_risk else 'No corrosion risk'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Wind: {s_wind} · Humidity: {s_hum}%<br>
                {'Keep electronics away from sea-facing windows. Use silica gel near devices.' if salt_risk
                 else 'Conditions are safe for electronics.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Laundry / evaporation
        laundry_risk = s_hum > 88
        st.markdown(f"""
        <div class="indoor-card {'indoor-card-warning' if laundry_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                🧺 Laundry & Fabric
            </div>
            <div style="font-weight:600;color:{'#f97316' if laundry_risk else '#22c55e'};margin-bottom:4px;">
                {'Zero evaporation — clothes will NOT dry' if laundry_risk else 'Normal drying conditions'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Humidity: {s_hum}% (threshold: 88%)<br>
                {'High microbial growth risk in wet fabrics. Use dryer or indoor fan.' if laundry_risk
                 else 'Air-drying is effective under current humidity.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. Food spoilage
        food_risk = s_temp > 30 and s_hum > 75
        st.markdown(f"""
        <div class="indoor-card {'indoor-card-warning' if food_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                🍎 Food Safety
            </div>
            <div style="font-weight:600;color:{'#f97316' if food_risk else '#22c55e'};margin-bottom:4px;">
                {'Accelerated spoilage — 2× fungal growth rate' if food_risk else 'Normal food shelf life'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Temp: {s_temp}°C · Humidity: {s_hum}%<br>
                {'Refrigerate all perishables. Do not leave cooked food on counter.' if food_risk
                 else 'Countertop storage is safe under current conditions.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4. Cognitive / productivity
        cog_risk = s_temp > 32 and s_hum > 80
        st.markdown(f"""
        <div class="indoor-card {'indoor-card-warning' if cog_risk else 'indoor-card-safe'}">
            <div style="font-size:.78rem;color:#64748b;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;">
                🧠 Human Productivity
            </div>
            <div style="font-weight:600;color:{'#f97316' if cog_risk else '#22c55e'};margin-bottom:4px;">
                {'Extreme wet-bulb — 40% productivity drop predicted' if cog_risk
                 else 'Comfortable working conditions'}
            </div>
            <div style="font-size:.82rem;color:#94a3b8;">
                Heat index: {hi_val}°C<br>
                {'Ensure AC and ventilation. Avoid cognitively demanding tasks during peak heat.' if cog_risk
                 else 'No heat-related cognitive impairment expected.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Bottom: Barometric pressure ───────────────────────────────────────────
    st.markdown("#### 🔵 Barometric Pressure Analysis")
    p_col1, p_col2 = st.columns([1, 2])

    with p_col1:
        migraine_risk = s_press < 1008
        st.metric("Pressure", f"{s_press} hPa",
                  delta="Below threshold" if migraine_risk else "Normal",
                  delta_color="inverse" if migraine_risk else "normal")

    with p_col2:
        if migraine_risk:
            st.warning(
                f"**Pressure: {s_press} hPa** — below the 1008 hPa threshold.\n\n"
                "Rapid barometric dips are linked to joint pain, sinus pressure, and migraines. "
                "People with pressure sensitivity should reduce physical exertion and stay hydrated."
            )
        else:
            st.success(
                f"**Pressure: {s_press} hPa** — within normal range (≥ 1008 hPa). "
                "No pressure-related health warnings."
            )

    # ── Summary risk table ────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 📋 Indoor Risk Summary")

    summary_data = {
        "Risk Factor":    ["Condensation", "Salt Corrosion", "Laundry Drying", "Food Spoilage", "Cognitive Load", "Pressure Migraine"],
        "Status":         [
            "🔴 ACTIVE"   if s_in_temp < dew_pt          else "🟢 Safe",
            "🟠 WARNING"  if salt_risk                    else "🟢 Safe",
            "🟠 WARNING"  if laundry_risk                 else "🟢 Safe",
            "🟠 WARNING"  if food_risk                    else "🟢 Safe",
            "🟠 WARNING"  if cog_risk                     else "🟢 Safe",
            "🟡 CAUTION"  if migraine_risk                else "🟢 Safe",
        ],
        "Key Value": [
            f"Indoor {s_in_temp}°C vs Dew {dew_pt}°C",
            f"Wind {s_wind}, Hum {s_hum}%",
            f"Humidity {s_hum}%",
            f"Temp {s_temp}°C, Hum {s_hum}%",
            f"Heat index {hi_val}°C",
            f"Pressure {s_press} hPa",
        ],
    }
    st.table(pd.DataFrame(summary_data))


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — 5-DAY FORECAST
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📅 5-Day Temperature Forecast")

    forecast_city = st.text_input(
        "🔍 Enter city for forecast",
        value="Kochi",
        key="forecast_city",
    )

    if not forecast_city.strip():
        st.info("Enter a city name above to load the forecast.")
        st.stop()

    @st.cache_data(ttl=1800)
    def fetch_forecast(city):
        try:
            # Geocode
            geo = requests.get(
                f"http://api.openweathermap.org/geo/1.0/direct"
                f"?q={city}&limit=1&appid={WEATHER_API_KEY}",
                timeout=5,
            ).json()
            if not geo:
                return None, "City not found."
            lat, lon = geo[0]["lat"], geo[0]["lon"]
            name = geo[0].get("name", city)

            # Forecast
            fc = requests.get(
                f"http://api.openweathermap.org/data/2.5/forecast"
                f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric",
                timeout=5,
            ).json()
            if fc.get("cod") != "200":
                return None, f"Forecast error: {fc.get('message','unknown')}"

            return fc, name
        except Exception as e:
            return None, str(e)

    with st.spinner("Fetching forecast…"):
        fc_data, fc_name = fetch_forecast(forecast_city.strip())

    if fc_data is None:
        st.error(f"Could not load forecast: {fc_name}")
    else:
        st.caption(f"Location: **{fc_name}** — daily min/max temperatures and rainfall")

        # ── Group 3-hourly slots by date ──────────────────────────────────────
        try:
            import plotly.graph_objects as go
            has_plotly = True
        except ImportError:
            has_plotly = False
            st.warning("Install plotly: `pip install plotly`")

        from collections import defaultdict
        daily = defaultdict(lambda: {"temps": [], "rain": 0.0, "icons": [], "descs": []})

        for item in fc_data["list"]:
            date = item["dt_txt"][:10]
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["rain"] += item.get("rain", {}).get("3h", 0)
            daily[date]["icons"].append(item["weather"][0]["icon"])
            daily[date]["descs"].append(item["weather"][0]["description"])

        dates      = sorted(daily.keys())[:5]
        mins       = [round(min(daily[d]["temps"]), 1)  for d in dates]
        maxs       = [round(max(daily[d]["temps"]), 1)  for d in dates]
        rains      = [round(daily[d]["rain"], 1)         for d in dates]
        icons      = [daily[d]["icons"][len(daily[d]["icons"])//2] for d in dates]
        descs      = [daily[d]["descs"][len(daily[d]["descs"])//2].capitalize() for d in dates]

        # ── Daily cards ───────────────────────────────────────────────────────
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
                    <div style="margin-top:8px;font-size:.78rem;color:#38bdf8;">
                        🌧 {rains[i]} mm
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # ── Chart ─────────────────────────────────────────────────────────────
        if has_plotly:
            st.markdown("#### 📈 Temperature Range Chart")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=maxs, name="Max temp",
                line=dict(color="#f87171", width=2.5),
                marker=dict(size=7),
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=mins, name="Min temp",
                line=dict(color="#60a5fa", width=2.5),
                marker=dict(size=7),
                fill="tonexty",
                fillcolor="rgba(96,165,250,0.08)",
            ))
            fig.update_layout(
                paper_bgcolor="#0e1117",
                plot_bgcolor="#161b22",
                font=dict(color="#94a3b8"),
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b", title="°C"),
                legend=dict(bgcolor="#0e1117"),
                margin=dict(l=10, r=10, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 🌧 Daily Rainfall")
            fig2 = go.Figure(go.Bar(
                x=dates, y=rains,
                marker_color=["#ef4444" if r > 10 else "#f97316" if r > 3
                               else "#eab308" if r > 0 else "#22c55e" for r in rains],
            ))
            fig2.update_layout(
                paper_bgcolor="#0e1117",
                plot_bgcolor="#161b22",
                font=dict(color="#94a3b8"),
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b", title="mm"),
                margin=dict(l=10, r=10, t=10, b=10),
                height=220,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            # Fallback: matplotlib
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(dates, maxs, "o-", color="#f87171", label="Max")
            ax.plot(dates, mins, "o-", color="#60a5fa", label="Min")
            ax.fill_between(dates, mins, maxs, alpha=0.08, color="#60a5fa")
            ax.set_facecolor("#161b22")
            fig.patch.set_facecolor("#0e1117")
            ax.tick_params(colors="#94a3b8")
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363d")
            ax.legend(facecolor="#161b22", labelcolor="#94a3b8")
            st.pyplot(fig)


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Nexus Engine v2.0 | Last updated: {datetime.datetime.now().strftime('%H:%M:%S')} | "
    "Data: OpenWeatherMap · Leaflet.js · NEXUS Predictive Engine"
)
