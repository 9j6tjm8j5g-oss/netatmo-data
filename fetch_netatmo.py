import os
import json
import requests
from datetime import datetime
import pytz

tz = pytz.timezone("Europe/Berlin")

# Output-Struktur
output = {
    "wohnzimmer": {},
    "buero": {},
    "og": {},
    "draussen": {},
    "druck": {},
    "vorhersage": {},
    "netatmo_messzeit": "",
    "timestamp": ""
}

# 1. Netatmo Auth & Daten
client_id = os.environ.get("NETATMO_CLIENT_ID")
client_secret = os.environ.get("NETATMO_CLIENT_SECRET")
refresh_token = os.environ.get("NETATMO_REFRESH_TOKEN")

try:
    auth_res = requests.post("https://api.netatmo.com/oauth2/token", data={
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }, timeout=10)
    
    token = auth_res.json().get("access_token")
    
    dev_res = requests.get("https://api.netatmo.com/api/getstationsdata", headers={
        "Authorization": f"Bearer {token}"
    }, timeout=10)
    
    devices = dev_res.json().get("body", {}).get("devices", [])
    if devices:
        main_dev = devices[0]
        
        # Zeitstempel der Messung
        last_status = main_dev.get("dashboard_data", {}).get("time_utc")
        if last_status:
            output["netatmo_messzeit"] = datetime.fromtimestamp(last_status, tz).strftime("%H:%M")
            
        # Hauptstation (z.B. Wohnzimmer)
        dash = main_dev.get("dashboard_data", {})
        output["wohnzimmer"] = {
            "temp": dash.get("Temperature"),
            "hum": dash.get("Humidity"),
            "co2": dash.get("CO2"),
            "trend": dash.get("temp_trend", "stable")
        }
        output["druck"] = {"val": dash.get("Pressure")}

        # Module (Aussen, Buero, OG)
        for mod in main_dev.get("modules", []):
            m_dash = mod.get("dashboard_data", {})
            name = mod.get("module_name", "").lower()
            
            mod_data = {
                "temp": m_dash.get("Temperature"),
                "hum": m_dash.get("Humidity"),
                "co2": m_dash.get("CO2"),
                "trend": m_dash.get("temp_trend", "stable")
            }
            
            if "außen" in name or "draussen" in name or "outdoor" in name:
                output["draussen"] = mod_data
            elif "büro" in name or "buero" in name or "firma" in name:
                output["buero"] = mod_data
            elif "og" in name or "obergeschoss" in name:
                output["og"] = mod_data

except Exception as e:
    print(f"Fehler bei Netatmo: {e}")

# 2. Open-Meteo Wetterdaten direkt in Python abrufen
try:
    om_res = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 49.563,
            "longitude": 7.022,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,sunrise,sunset",
            "hourly": "temperature_2m,weathercode",
            "timezone": "Europe/Berlin",
            "forecast_days": 3
        },
        timeout=10
    )
    if om_res.status_code == 200:
        output["vorhersage"] = om_res.json()
except Exception as e:
    print(f"Fehler bei Open-Meteo: {e}")

output["timestamp"] = datetime.now(tz).strftime("%H:%M")

# Speichern
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("data.json erfolgreich generiert.")
