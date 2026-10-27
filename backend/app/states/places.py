"""Cities a buyer may type next to a project name.

A city is not part of a project's name, so it is dropped before names are compared. A city
outside Uttar Pradesh also tells us, without searching, that the project is not one UP-RERA
registers. Only cities that homebuyers search for are listed; an unknown place changes nothing.
"""

import re

UP_PLACES = (
    "noida", "greater noida", "greater noida west", "noida extension", "yamuna expressway",
    "ghaziabad", "indirapuram", "lucknow", "kanpur", "agra", "meerut", "varanasi", "prayagraj",
    "allahabad", "bareilly", "gorakhpur", "mathura", "vrindavan", "aligarh", "moradabad",
)  # fmt: skip

# Cities whose projects other states' RERAs register.
OTHER_PLACES = (
    "mumbai", "navi mumbai", "thane", "pune", "nagpur", "nashik", "panvel", "kalyan", "palava",
    "dombivli", "vasai", "virar", "mira road", "worli", "andheri", "bandra", "powai", "chembur",
    "aurangabad", "kolhapur", "hinjewadi", "wakad", "lower parel", "borivali",
    "gurugram", "gurgaon", "faridabad", "panchkula", "sonipat", "panipat", "ambala", "rohtak",
    "hisar", "karnal", "manesar", "sohna", "bahadurgarh",
    "bengaluru", "bangalore", "mysuru", "mysore", "mangaluru", "hubballi", "whitefield",
    "sarjapur", "yelahanka", "hebbal", "electronic city", "devanahalli", "belagavi",
    "delhi", "new delhi", "dwarka", "rohini", "saket",
    "hyderabad", "secunderabad", "gachibowli", "kokapet", "warangal", "kompally",
    "ahmedabad", "surat", "vadodara", "rajkot", "gandhinagar",
    "chennai", "coimbatore", "madurai", "tiruchirappalli", "tambaram", "porur",
    "jaipur", "jodhpur", "udaipur", "ajmer", "bhopal", "indore", "jabalpur", "gwalior",
    "kolkata", "howrah", "siliguri", "rajarhat", "mohali", "ludhiana", "amritsar", "jalandhar",
    "zirakpur", "patiala", "kochi", "thiruvananthapuram", "trivandrum", "kozhikode", "thrissur",
    "ernakulam", "visakhapatnam", "vizag", "vijayawada", "amaravati", "guntur", "tirupati",
    "dehradun", "haridwar", "haldwani", "rishikesh", "patna", "muzaffarpur",
    "bhubaneswar", "cuttack", "goa", "panaji", "margao", "mapusa", "north goa",
    "raipur", "bhilai", "bilaspur", "shimla", "solan", "manali", "baddi", "ranchi",
    "jamshedpur", "dhanbad", "guwahati", "dibrugarh", "silchar", "srinagar", "jammu",
)  # fmt: skip

_LONGEST_FIRST = sorted((*UP_PLACES, *OTHER_PLACES), key=len, reverse=True)


def place_in(text: str) -> str | None:
    """The longest known place named in the text ("greater noida" before "noida")."""
    lowered = f" {re.sub(r'[^a-z0-9]+', ' ', text.lower())} "
    return next((place for place in _LONGEST_FIRST if f" {place} " in lowered), None)


def names_place_outside_up(text: str) -> bool:
    """Whether the first place the text names is a city whose projects UP-RERA does not register."""
    place = place_in(text)
    return place is not None and place in OTHER_PLACES


def without_places(text: str) -> str:
    """The text with every known place removed, so a city does not count as part of a name."""
    out = f" {re.sub(r'[^A-Za-z0-9]+', ' ', text)} "
    for place in _LONGEST_FIRST:
        out = re.sub(rf"(?i)(?<= ){re.escape(place)}(?= )", " ", out)
    return out.strip()
