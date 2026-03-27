# HOW TO IMPLEMENT THE FLOOD RISK MAP INTO ENVIROCHECK
# ======================================================
# Follow these steps exactly. Takes about 10 minutes.


# ── STEP 1: Install one new library ───────────────────
#
# You only need ONE new install. Leaflet.js loads from
# the internet automatically — no pip install needed for it.
#
#   pip install streamlit requests python-dotenv
#
# (If you already have these, nothing extra to install)


# ── STEP 2: Check your .env file ──────────────────────
#
# Your .env file must have these two lines:
#
#   WEATHER_API_KEY=your_openweathermap_key_here
#   AQI_API_KEY=your_waqi_key_here
#
# If you don't have a .env file yet, create one in the
# same folder as app.py and paste the lines above.


# ── STEP 3: Check your project folder structure ───────
#
# Your folder should look like this:
#
#   your_project_folder/
#   ├── app.py              ← REPLACE with the new app.py
#   ├── data_fetcher.py     ← KEEP AS IS (no changes)
#   ├── location_ai.py      ← KEEP AS IS (no changes)
#   ├── main.py             ← KEEP AS IS (no changes)
#   └── .env                ← your API keys
#
# data_fetcher.py and location_ai.py do NOT change.
# Only app.py is replaced.


# ── STEP 4: Replace app.py ────────────────────────────
#
# Delete your old app.py.
# Copy the new app.py (from outputs/) into your project folder.
#
# The new app.py does everything the old one did, plus:
#   - Uses REAL API data (no more sliders / fake data)
#   - Imports get_all_data()     from data_fetcher.py
#   - Imports classify_location() from location_ai.py
#   - Adds a Flood Risk Map tab with Leaflet.js


# ── STEP 5: Run the app ───────────────────────────────
#
#   streamlit run app.py
#
# Open your browser to http://localhost:8501


# ── STEP 6: Test it ───────────────────────────────────
#
# 1. Type a city name (e.g. "Kochi") and press Enter
# 2. You will see two tabs at the top:
#       📊 Dashboard    ← your original cards + alerts
#       🌊 Flood Risk Map ← the new Leaflet map
# 3. Click the "Flood Risk Map" tab
# 4. You should see a dark map centred on the city
#    with a coloured marker:
#       Green  = Safe (0 mm rain)
#       Yellow = Low risk (1–3 mm)
#       Orange = Moderate (3–10 mm)
#       Red    = Flood risk (10+ mm)
# 5. Click the marker → popup shows Rainfall, Temp,
#    Humidity, and Risk Level


# ── HOW THE MAP WORKS (for your understanding) ────────
#
# The function build_flood_map_html() in app.py:
#   1. Takes lat, lon, rain, city, temp, humidity
#   2. Decides the risk level and marker colour
#   3. Builds a complete HTML page as a Python string
#      containing Leaflet.js map code
#   4. st.components.v1.html() renders that HTML
#      inside an iframe in Streamlit
#
# No server, no extra files — it's all one HTML string
# passed to Streamlit's built-in HTML renderer.


# ── COMMON ERRORS AND FIXES ───────────────────────────

# Error: "ModuleNotFoundError: No module named 'data_fetcher'"
#   Fix: Make sure data_fetcher.py is in the SAME folder as app.py

# Error: "ModuleNotFoundError: No module named 'location_ai'"
#   Fix: Make sure location_ai.py is in the SAME folder as app.py

# Error: "Could not fetch data"
#   Fix: Check your .env file has correct API keys
#        Run: python data_fetcher.py  to test keys separately

# Error: Map shows but is blank / grey tiles
#   Fix: You need an internet connection for the map tiles
#        (CartoDB tiles load from the internet)

# Error: "KeyError: rain" or rain shows 0 always
#   This is normal — OpenWeatherMap only returns rain data
#   when it is actually raining. 0 mm = no rain = Safe. Correct.

# Error: Streamlit shows old version after replacing app.py
#   Fix: Stop the server (Ctrl+C), then run again:
#        streamlit run app.py


# ── WHAT EACH FILE DOES (SUMMARY) ────────────────────
#
#   data_fetcher.py   Gets lat/lon, weather, AQI from APIs
#   location_ai.py    Adjusts AQI based on zone type
#   main.py           Command-line test script (not used by app.py)
#   app.py            The Streamlit dashboard UI
#                     Calls data_fetcher + location_ai
#                     Shows Dashboard tab + Flood Map tab