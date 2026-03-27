from data_fetcher import get_all_data
from location_ai import classify_location, adjust_aqi

# ---------------- INPUT ----------------
place = input("Enter place: ").strip()

data = get_all_data(place)

if not data:
    print("❌ Failed to fetch data. Check location or API keys.")
else:
    # AI classification
    location_type = classify_location(place)
    adjusted_aqi = adjust_aqi(data["aqi"], location_type)

    data["location_type"] = location_type
    data["adjusted_aqi"] = adjusted_aqi

    # Explanation (optional but good)
    if location_type == "industrial":
        explanation = "Industrial area → AQI increased"
    elif location_type == "traffic":
        explanation = "Traffic zone → AQI slightly increased"
    elif location_type == "coastal":
        explanation = "Coastal area → AQI slightly reduced"
    else:
        explanation = "Urban area → No major adjustment"

    data["explanation"] = explanation

    # OUTPUT
    print(f"\n📍 Location: {place}")
    print("\n📊 Latest Environmental Data:")
    print(data)