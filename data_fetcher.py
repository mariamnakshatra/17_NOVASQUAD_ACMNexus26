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
    else:
        print("\n❌ Failed to fetch data. Check location or API keys.")