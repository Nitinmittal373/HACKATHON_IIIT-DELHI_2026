"""Which state a city or district is in, so a buyer who types a place needs no state picker.

Only cities that homebuyers search for are listed, each in the state whose RERA registers its
projects. A place that is not here simply gives no state, and every portal is searched.
"""

import re

# fmt: off
PLACES: dict[str, str] = {
    # Uttar Pradesh (the Delhi-NCR towns on this side of the river register with UP-RERA)
    "noida": "UP", "greater noida": "UP", "yamuna expressway": "UP", "ghaziabad": "UP",
    "lucknow": "UP", "kanpur": "UP", "agra": "UP", "meerut": "UP", "varanasi": "UP",
    "prayagraj": "UP", "allahabad": "UP", "bareilly": "UP", "gorakhpur": "UP",
    "mathura": "UP", "vrindavan": "UP", "aligarh": "UP", "moradabad": "UP",
    "greater noida west": "UP", "noida extension": "UP", "indirapuram": "UP",
    # Maharashtra
    "mumbai": "MH", "navi mumbai": "MH", "thane": "MH", "pune": "MH", "nagpur": "MH",
    "nashik": "MH", "panvel": "MH", "kalyan": "MH", "palava": "MH", "dombivli": "MH",
    "vasai": "MH", "virar": "MH", "mira road": "MH", "worli": "MH", "andheri": "MH",
    "bandra": "MH", "powai": "MH", "chembur": "MH", "aurangabad": "MH", "kolhapur": "MH",
    "hinjewadi": "MH", "wakad": "MH", "lower parel": "MH", "borivali": "MH",
    # Haryana
    "gurugram": "HR", "gurgaon": "HR", "faridabad": "HR", "panchkula": "HR", "sonipat": "HR",
    "panipat": "HR", "ambala": "HR", "rohtak": "HR", "hisar": "HR", "karnal": "HR",
    "manesar": "HR", "sohna": "HR", "bahadurgarh": "HR",
    # Karnataka
    "bengaluru": "KA", "bangalore": "KA", "mysuru": "KA", "mysore": "KA", "mangaluru": "KA",
    "hubballi": "KA", "whitefield": "KA", "sarjapur": "KA", "yelahanka": "KA",
    "hebbal": "KA", "electronic city": "KA", "devanahalli": "KA", "belagavi": "KA",
    # Delhi
    "delhi": "DL", "new delhi": "DL", "dwarka": "DL", "rohini": "DL", "saket": "DL",
    # Telangana
    "hyderabad": "TG", "secunderabad": "TG", "gachibowli": "TG", "kokapet": "TG",
    "warangal": "TG", "kompally": "TG", "financial district": "TG",
    # Gujarat
    "ahmedabad": "GJ", "surat": "GJ", "vadodara": "GJ", "rajkot": "GJ", "gandhinagar": "GJ",
    # Tamil Nadu
    "chennai": "TN", "coimbatore": "TN", "madurai": "TN", "tiruchirappalli": "TN",
    "omr": "TN", "tambaram": "TN", "porur": "TN",
    # Rajasthan
    "jaipur": "RJ", "jodhpur": "RJ", "udaipur": "RJ", "kota": "RJ", "ajmer": "RJ",
    # Madhya Pradesh
    "bhopal": "MP", "indore": "MP", "jabalpur": "MP", "gwalior": "MP",
    # West Bengal
    "kolkata": "WB", "howrah": "WB", "siliguri": "WB", "rajarhat": "WB", "new town": "WB",
    # Punjab
    "mohali": "PB", "ludhiana": "PB", "amritsar": "PB", "jalandhar": "PB", "zirakpur": "PB",
    "patiala": "PB",
    # Kerala
    "kochi": "KL", "thiruvananthapuram": "KL", "trivandrum": "KL", "kozhikode": "KL",
    "thrissur": "KL", "ernakulam": "KL",
    # Andhra Pradesh
    "visakhapatnam": "AP", "vizag": "AP", "vijayawada": "AP", "amaravati": "AP",
    "guntur": "AP", "tirupati": "AP",
    # Uttarakhand
    "dehradun": "UK", "haridwar": "UK", "haldwani": "UK", "rishikesh": "UK",
    # Bihar
    "patna": "BR", "gaya": "BR", "muzaffarpur": "BR",
    # Odisha
    "bhubaneswar": "OD", "cuttack": "OD", "puri": "OD",
    # Goa
    "goa": "GA", "panaji": "GA", "margao": "GA", "mapusa": "GA", "north goa": "GA",
    # Chhattisgarh
    "raipur": "CG", "bhilai": "CG", "bilaspur": "CG",
    # Himachal Pradesh
    "shimla": "HP", "solan": "HP", "manali": "HP", "baddi": "HP",
    # Jharkhand
    "ranchi": "JH", "jamshedpur": "JH", "dhanbad": "JH",
    # Assam
    "guwahati": "AS", "dibrugarh": "AS", "silchar": "AS",
    # Jammu and Kashmir
    "srinagar": "JK", "jammu": "JK",
}
# fmt: on

_LONGEST_FIRST = sorted(PLACES, key=len, reverse=True)


def place_in(text: str) -> str | None:
    """The longest known place named in the text ("greater noida" before "noida")."""
    lowered = f" {re.sub(r'[^a-z0-9]+', ' ', text.lower())} "
    return next((place for place in _LONGEST_FIRST if f" {place} " in lowered), None)


def state_of_place(text: str) -> str | None:
    """The state code of the first place the text names, or None when no known place is named."""
    place = place_in(text)
    return PLACES[place] if place else None


def without_places(text: str) -> str:
    """The text with every known place removed, so a city does not count as part of a name."""
    out = f" {re.sub(r'[^A-Za-z0-9]+', ' ', text)} "
    for place in _LONGEST_FIRST:
        out = re.sub(rf"(?i)(?<= ){re.escape(place)}(?= )", " ", out)
    return out.strip()
