"""
NEXUS | Climate Intelligence Twin
----------------------------------
Original NEXUS dashboard preserved exactly.
Added: Leaflet.js Flood Risk Map section (after the Intelligence Matrix).

Run:
    pip install streamlit pandas
    streamlit run nexus_combined.py
"""

import streamlit as st
import pandas as pd
import datetime

# --- SET PAGE CONFIG ---
st.set_page_config(
    page_title="NEXUS | Climate Intelligence Twin",
    page_icon="🌍",
    layout="wide"
)

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- CORE INTELLIGENCE ENGINE ---
def nexus_predictive_engine(temp, hum, press, rain, wind_dir, in_temp):
    predictions = []
    alerts = []
   
    # 1. NATURAL CALAMITY PREDICTIONS
    drain_limit = 20.0
    overflow = max(0, rain - drain_limit)
    if overflow > 10:
        alerts.append({"Level": "🚨 CALAMITY", "Issue": "Urban Flash Flood", "Details": "Perandoor Canal capacity exceeded. Street submergence imminent."})
   
    if wind_dir in ["W", "WSW", "NW"] and hum > 85:
        alerts.append({"Level": "🌊 DISASTER", "Issue": "Tidal Incursion", "Details": "Sea-level surge predicted in Edakochi/Chellanam regions."})

    # 2. INFRASTRUCTURE & BUILDING HEALTH
    dew_point = temp - ((100 - hum) / 5)
    if in_temp < dew_point:
        predictions.append({"Category": "🏗️ Infrastructure", "Impact": "Internal Wall Sweat", "Insight": "Indoor temp is below Dew Point. High mold/short-circuit risk."})
   
    if "W" in wind_dir and hum > 75:
        predictions.append({"Category": "⚡ Tech", "Impact": "Hardware Corrosion", "Insight": "Salt-mist infiltration. Keep electronics away from sea-facing windows."})

    # 3. HUMAN HEALTH & BIOMETEOROLOGY
    if temp > 32 and hum > 80:
        predictions.append({"Category": "🧠 Human", "Impact": "Cognitive Decline", "Insight": "Extreme Wet-Bulb temp. 40% drop in labor productivity predicted."})
   
    if press < 1008:
        predictions.append({"Category": "🩺 Health", "Impact": "Pressure Migraine", "Insight": "Rapid barometric dip. High risk of joint pain and headaches."})

    # 4. LOGISTICS & DAILY LIFE
    if hum > 88:
        predictions.append({"Category": "🧺 Logistics", "Impact": "Zero Evaporation", "Insight": "Clothes will not dry. High risk of microbial growth in fabrics."})
   
    if temp > 30 and hum > 75:
        predictions.append({"Category": "🍎 Food", "Impact": "Shelf-life Decay", "Insight": "Fungal growth accelerated. Countertop spoilage risk increased by 2x."})

    return alerts, predictions, overflow

# --- UI HEADER ---
st.title("🌍 NEXUS: Localized Climate Intelligence Twin")
st.markdown("#### *Bridges the gap between Atmospheric Data and Human Impact*")
st.info("Target Region: **Thevara-Edakochi Corridor, Kochi** | Model Status: **Active**")

# --- SIDEBAR: SENSOR INPUTS ---
st.sidebar.header("📡 Live Sensor Feed")
s_temp  = st.sidebar.slider("Outdoor Temp (°C)", 20.0, 45.0, 31.0)
s_hum   = st.sidebar.slider("Humidity (%)", 40, 100, 85)
s_press = st.sidebar.slider("Pressure (hPa)", 990, 1020, 1007)
s_rain  = st.sidebar.number_input("Rainfall (mm/h)", 0.0, 100.0, 25.0)
s_wind  = st.sidebar.selectbox("Wind Direction", ["N", "S", "E", "W", "NW", "NE", "SW", "SE"], index=3)

st.sidebar.divider()
st.sidebar.header("🏠 Indoor Environment")
s_in_temp = st.sidebar.slider("Indoor AC Temp (°C)", 16, 30, 22)

# --- SIDEBAR: MAP LOCATION ---
st.sidebar.divider()
st.sidebar.header("📍 Map Location")
s_lat = st.sidebar.number_input("Latitude",  value=9.9312,  format="%.4f")
s_lon = st.sidebar.number_input("Longitude", value=76.2673, format="%.4f")

# --- RUN ENGINE ---
alerts, predictions, overflow = nexus_predictive_engine(
    s_temp, s_hum, s_press, s_rain, s_wind, s_in_temp
)

# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL DASHBOARD — untouched
# ─────────────────────────────────────────────────────────────────────────────

# Row 1: Vital Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Atmospheric Temp",  f"{s_temp}°C")
m2.metric("Relative Humidity", f"{s_hum}%")
m3.metric("Rain Load",         f"{s_rain} mm/h")
m4.metric("Drainage Overflow", f"{overflow:.1f} mm/h", delta=overflow, delta_color="inverse")

# Row 2: Calamity Alerts
if alerts:
    st.subheader("⚠️ Critical Calamity Warnings")
    for a in alerts:
        st.error(f"**{a['Level']}**: {a['Issue']} - {a['Details']}")

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
    dew_pt = s_temp - ((100 - s_hum) / 5)
    st.write(f"**Calculated Dew Point:** {dew_pt:.1f}°C")
    st.write(f"**Current Indoor Setting:** {s_in_temp}°C")
   
    if s_in_temp < dew_pt:
        st.progress(100)
        st.error("CONDENSATION ACTIVE: Moisture is currently forming inside walls.")
    else:
        st.progress(30)
        st.success("THERMAL STABILITY: Indoor environment is safe.")

# ─────────────────────────────────────────────────────────────────────────────
# NEW SECTION — Flood Risk Map (Leaflet.js)
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("🗺️ Flood Risk Map")
st.caption("Marker colour updates live based on the Rainfall (mm/h) value set in the sidebar.")

# Derive risk for the info strip
def get_risk_info(rain):
    if rain == 0:       return "Safe",     "#22c55e"
    elif rain <= 3:     return "Low Risk",  "#eab308"
    elif rain <= 10:    return "Moderate",  "#f97316"
    else:               return "Flood Risk","#ef4444"

risk_label, risk_color = get_risk_info(s_rain)

# Quick summary strip above the map
rc1, rc2, rc3 = st.columns(3)
rc1.metric("Rainfall Input",  f"{s_rain} mm/h")
rc2.metric("Risk Level",      risk_label)
rc3.metric("Map Centre",      f"{s_lat:.4f}, {s_lon:.4f}")

# ── Leaflet map rendered as an HTML component ─────────────────────────────────
leaflet_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

  <!-- Leaflet CSS & JS -->
  <link  rel="stylesheet"
         href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      background: #0e1117;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

    #map {{
      width:  100%;
      height: 480px;
      border-radius: 12px;
      border: 1px solid #30363d;
    }}

    /* ── Custom marker dot ── */
    .risk-dot {{
      width:  22px;
      height: 22px;
      border-radius: 50%;
      border: 3px solid rgba(255,255,255,0.35);
      box-shadow: 0 0 12px 4px var(--glow);
      animation: pulse 2s ease-in-out infinite;
    }}

    @keyframes pulse {{
      0%,100% {{ box-shadow: 0 0 10px 3px var(--glow); transform: scale(1);   }}
      50%      {{ box-shadow: 0 0 20px 8px var(--glow); transform: scale(1.1); }}
    }}

    /* ── Popup card ── */
    .leaflet-popup-content-wrapper {{
      background: #161b22 !important;
      border: 1px solid #30363d !important;
      border-radius: 12px !important;
      padding: 0 !important;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
    }}
    .leaflet-popup-tip {{ background: #161b22 !important; }}
    .leaflet-popup-content {{ margin: 0 !important; }}

    .popup-card {{
      padding: 14px 18px;
      min-width: 190px;
    }}
    .popup-title {{
      font-size: 13px;
      font-weight: 700;
      color: #e2e8f0;
      margin-bottom: 10px;
      letter-spacing: 0.03em;
    }}
    .popup-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
      font-size: 12px;
    }}
    .popup-label {{ color: #64748b; }}
    .popup-value {{ color: #e2e8f0; font-weight: 600; }}
    .popup-badge {{
      display: inline-block;
      margin-top: 10px;
      padding: 3px 12px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.06em;
    }}

    /* ── Legend ── */
    .legend {{
      position: absolute;
      bottom: 28px;
      left: 12px;
      z-index: 1000;
      background: rgba(22,27,34,0.95);
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 11px;
      color: #94a3b8;
      line-height: 1.9;
      backdrop-filter: blur(4px);
    }}
    .legend-title {{
      font-size: 10px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
    }}
    .dot {{
      display: inline-block;
      width: 10px; height: 10px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: middle;
    }}
  </style>
</head>
<body>

<div style="position:relative;">
  <div id="map"></div>

  <!-- Legend overlay -->
  <div class="legend">
    <div class="legend-title">Flood Risk</div>
    <div><span class="dot" style="background:#22c55e;"></span>Safe — 0 mm</div>
    <div><span class="dot" style="background:#eab308;"></span>Low — 1–3 mm</div>
    <div><span class="dot" style="background:#f97316;"></span>Moderate — 3–10 mm</div>
    <div><span class="dot" style="background:#ef4444;"></span>Flood risk — 10+ mm</div>
  </div>
</div>

<script>
  // ── 1. Data from Python (injected by Streamlit) ─────────────────────────
  const lat      = {s_lat};
  const lon      = {s_lon};
  const rain     = {s_rain};
  const riskLabel = "{risk_label}";
  const riskColor = "{risk_color}";

  // ── 2. Initialise map ───────────────────────────────────────────────────
  const map = L.map('map', {{
    center: [lat, lon],
    zoom: 12,
    zoomControl: true,
  }});

  // Dark tile layer (CartoDB Dark Matter — no API key needed)
  L.tileLayer(
    'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
    {{
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19
    }}
  ).addTo(map);

  // ── 3. Risk zone circle (semi-transparent) ──────────────────────────────
  L.circle([lat, lon], {{
    radius:      10000,          // 10 km
    color:       riskColor,
    fillColor:   riskColor,
    fillOpacity: 0.10,
    weight:      1.5,
    opacity:     0.45,
  }}).addTo(map);

  // ── 4. Custom divIcon marker ────────────────────────────────────────────
  const markerIcon = L.divIcon({{
    className: '',              // clear Leaflet's default white box
    html: `<div class="risk-dot"
                style="background:${{riskColor}};
                       --glow:${{riskColor}}80;">
           </div>`,
    iconSize:   [22, 22],
    iconAnchor: [11, 11],       // centre of the dot
    popupAnchor:[0, -14],       // popup appears just above
  }});

  // ── 5. Popup content ────────────────────────────────────────────────────
  const popupHTML = `
    <div class="popup-card">
      <div class="popup-title">📍 Flood Risk Assessment</div>
      <div class="popup-row">
        <span class="popup-label">🌧 Rainfall</span>
        <span class="popup-value">${{rain}} mm/h</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">📍 Coordinates</span>
        <span class="popup-value">${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">⚠️ Risk Level</span>
        <span class="popup-value" style="color:${{riskColor}}">${{riskLabel}}</span>
      </div>
      <div>
        <span class="popup-badge"
              style="background:${{riskColor}}22;
                     color:${{riskColor}};
                     border:1px solid ${{riskColor}}55;">
          ${{riskLabel.toUpperCase()}}
        </span>
      </div>
    </div>
  `;

  // ── 6. Add marker & open popup ──────────────────────────────────────────
  L.marker([lat, lon], {{ icon: markerIcon }})
   .addTo(map)
   .bindPopup(popupHTML, {{ maxWidth: 240 }})
   .openPopup();

</script>
</body>
</html>
"""

st.components.v1.html(leaflet_html, height=500, scrolling=False)

# Advice strip below the map
advice_map = {
    "Safe":      ("✅ No flood risk. Conditions are normal.",                        "success"),
    "Low Risk":  ("🟡 Light rain. Watch for waterlogging in low-lying areas.",        "warning"),
    "Moderate":  ("🟠 Moderate rain. Avoid underpasses and low roads. Stay alert.",   "warning"),
    "Flood Risk":("🔴 Heavy rain — flood risk active. Avoid low areas immediately.",  "error"),
}
msg, kind = advice_map[risk_label]
getattr(st, kind)(msg)

# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL FOOTER — untouched
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
expander = st.expander("🛠️ Technical Merit & Logic Framework")
expander.write("""
- **Rational Method Physics:** We use $Q = C \\times I \\times A$ to map rainfall against the specific drainage capacity of Kochi's canal network.
- **Biometeorology:** The algorithm tracks Barometric Pressure trends to predict joint pain and migraine triggers.
- **BIM Integration:** By comparing Indoor vs. Outdoor temperature gradients, we predict 'Building Sweat' (latent moisture failure).
- **Coastal Specificity:** Includes salinity-driven tech corrosion warnings based on wind-direction and humidity coupling.
""")

st.caption(f"Nexus Engine v1.0 | Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")