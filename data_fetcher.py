import requests
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# ---------------- API KEYS (SECURE) ----------------
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
AQI_API_KEY = os.getenv("AQI_API_KEY")

# ---------------- WEATHER FUNCTION ----------------
def get_weather(city):
    try:
        # Check if key exists
        if not WEATHER_API_KEY:
            print("Missing WEATHER_API_KEY")
            return None

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()

        # Check if city is valid
        if data.get("cod") != 200:
            return None

        weather_data = {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rain": data.get("rain", {}).get("1h", 0),
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"]
        }

        return weather_data

    except Exception as e:
        print("Weather API Error:", e)
        return None


# ---------------- AQI FUNCTION ----------------
def get_aqi(lat, lon):
    try:
        # Check if key exists
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


# ---------------- COMBINED FUNCTION ----------------
def get_all_data(city):
    weather = get_weather(city)

    if not weather:
        return None

    aqi = get_aqi(weather["lat"], weather["lon"])

    if aqi is None:
        return None

    weather["aqi"] = aqi

    return weather


# ---------------- TEST RUN ----------------
if __name__ == "__main__":
    city = input("Enter city name: ").strip()

    result = get_all_data(city)

    if result:
        print("\n✅ Data fetched successfully:")
        print(result)
    else:
        print("\n❌ Failed to fetch data. Check city name or API keys.")