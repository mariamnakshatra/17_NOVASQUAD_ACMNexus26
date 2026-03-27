# ---------------- RISK ENGINE ----------------

def evaluate_risk(data):
    # Handle missing data
    if not data:
        return None

    risks = {}

    # 🌡 Heat Risk
    if data["temp"] > 38:
        risks["heat"] = "High"
    elif data["temp"] > 32:
        risks["heat"] = "Moderate"
    else:
        risks["heat"] = "Low"

    # 🌧 Flood Risk
    if data["rain"] > 10:
        risks["flood"] = "Critical"
    elif data["rain"] > 3:
        risks["flood"] = "Moderate"
    else:
        risks["flood"] = "Low"

    # 🌫 Air Quality Risk
    if data["aqi"] > 150:
        risks["air"] = "Unhealthy"
    elif data["aqi"] > 80:
        risks["air"] = "Moderate"
    else:
        risks["air"] = "Good"

    # 🔥 Optional: Overall Risk
    if risks["heat"] == "High" or risks["flood"] == "Critical" or risks["air"] == "Unhealthy":
        risks["overall"] = "High"
    elif risks["heat"] == "Moderate" or risks["flood"] == "Moderate" or risks["air"] == "Moderate":
        risks["overall"] = "Moderate"
    else:
        risks["overall"] = "Low"

    return risks


# ---------------- TESTING ----------------
from data_fetcher import get_all_data

if __name__ == "__main__":
    city = input("Enter city name: ")

    data = get_all_data(city)

    if data:
        print("\n📊 Data:", data)

        risks = evaluate_risk(data)

        print("\n⚠ Risk Analysis:", risks)
    else:
        print("\n❌ Failed to fetch data")