import os
from dotenv import load_dotenv
import requests
import time

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")


MAX_RETRIES = 3
WAIT_SECONDS = 2

def get_weather(location):
    # Temperature is in Celsius
    URL = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric&lang=en"
    data = None
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                break
            
        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(WAIT_SECONDS)
            else:
                return None
            
            
    if not data:
        return None
        
    
    temp        = data["main"]["temp"]
    feels_like  = data["main"]["feels_like"]
    humidity    = data["main"]["humidity"]
    description = data["weather"][0]["description"]
    weather_id  = data["weather"][0]["id"]
    city        = data["name"]

    # alerts
    alerts = []
    if weather_id // 100 == 2:
        alerts.append("⚡ Thunderstorm — avoid running outdoors")
    if weather_id // 100 == 3:
        alerts.append("🌦 Drizzle — waterproof jacket recommended")
    if weather_id // 100 == 5:
        alerts.append("🌧 Rain — waterproof jacket recommended")
    if weather_id // 100 == 6:
        alerts.append("❄️ Snow — roads may be slippery, be careful")
    if weather_id // 100 == 7:
        alerts.append("🌫 Extreme conditions — check before going out")
    if temp >= 35:
        alerts.append("🌡 Extreme heat — go out before 8AM or after 7PM")
    if temp >= 28 and humidity >= 70:
        alerts.append("💧 High heat and humidity — carry at least 750ml of water")
    if temp <= 5:
        alerts.append("🥶 Very cold — dress in layers, warm up longer")
    
    
    return {
        "location":    city,
        "temp":        round(temp, 1),
        "feels_like":  round(feels_like, 1),
        "humidity":    humidity,
        "description": description,
        "alerts":      alerts,
    }