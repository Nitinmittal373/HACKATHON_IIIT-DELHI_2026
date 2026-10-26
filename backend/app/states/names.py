"""State codes and names. Kept free of imports so the data models can use it."""

STATE_NAMES: dict[str, str] = {
    "UP": "Uttar Pradesh",
    "MH": "Maharashtra",
    "HR": "Haryana",
    "KA": "Karnataka",
    "DL": "Delhi",
    "TG": "Telangana",
    "GJ": "Gujarat",
    "TN": "Tamil Nadu",
    "RJ": "Rajasthan",
    "MP": "Madhya Pradesh",
    "WB": "West Bengal",
    "PB": "Punjab",
    "KL": "Kerala",
    "AP": "Andhra Pradesh",
    "UK": "Uttarakhand",
    "BR": "Bihar",
    "OD": "Odisha",
    "GA": "Goa",
    "CG": "Chhattisgarh",
    "HP": "Himachal Pradesh",
    "JH": "Jharkhand",
    "AS": "Assam",
    "JK": "Jammu and Kashmir",
}

DEFAULT_STATE = "UP"


def state_name(code: str) -> str:
    return STATE_NAMES.get(code, code)
