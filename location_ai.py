# location_ai.py

def classify_location(place):
    place = place.lower()

    industrial = ["eloor", "ambalamugal"]
    traffic = ["mg road", "highway", "junction"]
    coastal = ["fort kochi", "beach", "coast"]

    if place in industrial:
        return "industrial"
    elif place in traffic:
        return "traffic"
    elif place in coastal:
        return "coastal"
    else:
        return "urban"


def adjust_aqi(aqi, location_type):
    if location_type == "industrial":
        return aqi + 30
    elif location_type == "traffic":
        return aqi + 20
    elif location_type == "coastal":
        return max(aqi - 10, 0)
    return aqi