import os
import json
import requests
from datetime import datetime, timezone, timedelta

# Zeitzone definieren (Mitteleuropäische Sommerzeit = UTC+2)
tz_offset = timezone(timedelta(hours=2))

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
        
        # Zeitstempel der letzten Netatmo-Messung
        last_status = main_dev.get("dashboard_data", {}).get("time_utc")
        if last_status:
            output["netatmo_messzeit"] = datetime.fromtimestamp(last_status, tz=tz_offset).strftime("%H:%M")
            
        # Hauptstation (Wohnzimmer)
        dash = main_dev.get("dashboard_data", {})
        output["wohnzimmer"] = {
            "temp": dash.get("Temperature"),
            "hum": dash.get("Humidity"),
            "co2": dash.get("CO2"),
            "trend": dash.get("temp_trend", "stable")
        }
        output["druck"] = {"val": dash.get("Pressure")}

        # Zusatzmodule (Außensensor, Büro, OG)
        for mod in main_dev.get("modules", []):
            m_dash = mod.get("dashboard_data", {})
            name = mod.get("module_name", "").lower()
            mod_type = mod.get("type", "")
            
            mod_data = {
                "temp": m_dash.get("Temperature"),
                "hum": m_dash.get("Humidity"),
                "co2": m_dash.get("CO2"),
                "trend": m_dash.get("temp_trend", "stable")
            }
            
            # Direkter Typ-Check: NAModule1 ist bei Netatmo IMMER der Außensensor
            if mod_type == "NAModule1" or any(x in name for x in ["au", "drau", "out"]):
                output["draussen"] = mod_data
            elif any(x in name for x in ["bür", "buer", "firm"]):
                output["buero"] = mod_data
            elif any(x in name for x in ["og", "ober"]):
                output["og"] = mod_data

except Exception as e:
    print(f"Fehler bei Netatmo: {e}")

# 2. Open-Meteo Wetterdaten (inkl. stündlichem Trend, Wind & Regen)
try:
    om_res = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 49.563,
            "longitude": 7.022,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,sunrise,sunset",
            "hourly": "temperature_2m,weathercode",
            "current": "wind_speed_10m,wind_direction_10m,precipitation",
            "timezone": "Europe/Berlin",
            "forecast_days": 3
        },
        timeout=10
    )
    if om_res.status_code == 200:
        output["vorhersage"] = om_res.json()
except Exception as e:
    print(f"Fehler bei Open-Meteo: {e}")

output["timestamp"] = datetime.now(tz_offset).strftime("%H:%M")

# Speichern der data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("data.json erfolgreich generiert.")
