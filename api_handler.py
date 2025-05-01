import requests

def get_today_data():
    """Získává data o dnešním dni z API svátků"""
    response = requests.get("https://svatkyapi.cz/api/day")
    return response.json()