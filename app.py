import streamlit as st
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="EnviroCheck", layout="wide")

# ---------------- CUSTOM CSS (MODERN UI) ----------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: rgba(255,255,255,0.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    text-align: center;
}

.metric {
    font-size: 28px;
    font-weight: bold;
}

.title {
    font-size: 18px;
    color: #94a3b8;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
# 🌍 EnviroCheck  
### Climate Risk Monitoring Dashboard
""")

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙ Control Panel")

sim_temp = st.sidebar.slider("🌡 Temperature", 0, 50, 30)
sim_aqi = st.sidebar.slider("🌫 AQI", 0, 300, 100)
sim_rain = st.sidebar.slider("🌧 Rainfall", 0, 20, 5)

# ---------------- INPUT ----------------
city = st.text_input("📍 Enter City Name", key="city_input")

# ---------------- MAIN ----------------
if city.strip() != "":

    data = {
        "temp": sim_temp,
        "humidity": 75,
        "aqi": sim_aqi,
        "rain": sim_rain,
        "lat": 9.93,
        "lon": 76.26
    }

    # ---------------- CARDS ----------------
    st.markdown("### 🌡 Environmental Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="title">Temperature</div>
            <div class="metric">🌡 {data['temp']}°C</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="title">Humidity</div>
            <div class="metric">💧 {data['humidity']}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="title">AQI</div>
            <div class="metric">🌫 {data['aqi']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- MAP ----------------
    st.markdown("### 📍 Location Overview")
    st.map([{"lat": data["lat"], "lon": data["lon"]}])

    # ---------------- ALERTS ----------------
    st.markdown("### ⚠ Risk Alerts")

    colA, colB, colC = st.columns(3)

    # Heat
    with colA:
        if data["temp"] > 38:
            st.error("🔥 Heatwave")
        elif data["temp"] > 32:
            st.warning("🌡 Warm")
        else:
            st.success("🟢 Normal")

    # Rain
    with colB:
        if data["rain"] > 10:
            st.error("🌊 Flood Risk")
        elif data["rain"] > 3:
            st.warning("🌧 Rain")
        else:
            st.success("🟢 Safe")

    # AQI
    with colC:
        if data["aqi"] > 150:
            st.error("🌫 Unhealthy")
        elif data["aqi"] > 80:
            st.warning("🌫 Moderate")
        else:
            st.success("🟢 Good")

    # ---------------- CHART ----------------
    st.markdown("### 📊 Temperature Trend")

    temps = [28, 30, 32, 31, 33, 34, data["temp"]]

    fig, ax = plt.subplots()
    ax.plot(temps, marker='o', color="#38bdf8")
    ax.set_facecolor("#0f172a")
    fig.patch.set_facecolor('#0f172a')
    ax.tick_params(colors='white')

    st.pyplot(fig)

    # ---------------- ACTION PLAN ----------------
    st.markdown("### 📋 Suggested Actions")

    actions = []

    if data["temp"] > 38:
        actions.append("🔥 Stay hydrated & avoid sun")

    if data["rain"] > 10:
        actions.append("🌊 Avoid low areas")

    if data["aqi"] > 150:
        actions.append("🌫 Wear mask")

    if actions:
        for act in actions:
            st.write("•", act)
    else:
        st.success("✅ No major risks")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Modern Climate Dashboard • Built with Streamlit")