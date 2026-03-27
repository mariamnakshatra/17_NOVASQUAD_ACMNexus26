import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- API KEYS ----------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
AQI_API_KEY = os.getenv("AQI_API_KEY")


# ---------------- GET COORDINATES ----------------
def get_coordinates(place):
    try:
        if not WEATHER_API_KEY:
            print("Missing WEATHER_API_KEY")
            return None

        url = f"http://api.openweathermap.org/geo/1.0/direct?q={place}&limit=1&appid={WEATHER_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if not data:
            return None

        return data[0]["lat"], data[0]["lon"]

    except Exception as e:
        print("Geocoding Error:", e)
        return None


# ---------------- WEATHER USING COORDINATES ----------------
def get_weather_by_coords(lat, lon):
    try:
        if not WEATHER_API_KEY:
            print("Missing WEATHER_API_KEY")
            return None

        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("cod") != 200:
            return None

        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rain": data.get("rain", {}).get("1h", 0),
            "lat": lat,
            "lon": lon
        }

    except Exception as e:
        print("Weather API Error:", e)
        return None


# ---------------- AQI FUNCTION ----------------
def get_aqi(lat, lon):
    try:
        if not AQI_API_KEY:
            print("Missing AQI_API_KEY")
            return None

        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQI_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("status") != "ok":
            return None

        return data["data"]["aqi"]

    except Exception as e:
        print("AQI API Error:", e)
        return None


# ---------------- 5-DAY FORECAST ----------------
def get_5day_forecast(lat, lon):
    """
    Returns a list of daily forecast dicts for the next 5 days.
    Each dict has: date (str), temp_min, temp_max, description, rain (mm)

    OpenWeatherMap /forecast returns data in 3-hour intervals (40 entries = ~5 days).
    We group them by date and compute daily min/max.
    """
    try:
        if not WEATHER_API_KEY:
            print("Missing WEATHER_API_KEY")
            return None

        url = (
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        )
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("cod") != "200":
            return None

        # Group 3-hour slots by date
        daily = {}
        for entry in data["list"]:
            date_str = entry["dt_txt"].split(" ")[0]        # "YYYY-MM-DD"
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

        # Build clean daily list
        forecast = []
        for date_str, d in sorted(daily.items()):
            forecast.append({
                "date":        d["date"],
                "temp_min":    round(min(d["temps"]), 1),
                "temp_max":    round(max(d["temps"]), 1),
                "description": d["description"].capitalize(),
                "rain":        round(d["rain"], 1),
            })

        return forecast[:5]          # Return max 5 days

    except Exception as e:
        print("Forecast API Error:", e)
        return None


# ---------------- COMBINED FUNCTION ----------------
def get_all_data(place):
    coords = get_coordinates(place)

    if not coords:
        return None

    lat, lon = coords

    weather = get_weather_by_coords(lat, lon)

    if not weather:
        return None

    aqi = get_aqi(lat, lon)

    if aqi is None:
        return None

    weather["aqi"] = aqi

    return weather


# ---------------- TEST RUN ----------------
if __name__ == "__main__":
    place = input("Enter place: ").strip()

    result = get_all_data(place)

    if result:
        print("\n✅ Data fetched successfully:")
        print(result)

        lat, lon = result["lat"], result["lon"]
        forecast = get_5day_forecast(lat, lon)
        if forecast:
            print("\n📅 5-Day Forecast:")
            for day in forecast:
                print(f"  {day['date']}: {day['temp_min']}°C – {day['temp_max']}°C  "
                      f"Rain: {day['rain']} mm  {day['description']}")
    else:
        print("\n❌ Failed to fetch data. Check location or API keys.")