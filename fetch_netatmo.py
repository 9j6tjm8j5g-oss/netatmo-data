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
    "regen": {},
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

        # Zusatzmodule
        for mod in main_dev.get("modules", []):
            m_dash = mod.get("dashboard_data", {})
            name = mod.get("module_name", "").lower()
            mod_type = mod.get("type", "")
            battery = mod.get("battery_percent")
            
            # REGENSENSOR (NAModule3)
            if mod_type == "NAModule3" or "regen" in name or "rain" in name:
                output["regen"] = {
                    "rain": m_dash.get("Rain"),
                    "sum_1h": m_dash.get("sum_rain_1"),
                    "sum_24h": m_dash.get("sum_rain_24"),
                    "battery": battery
                }
            # AUSSENSENSOR (NAModule1)
            elif mod_type == "NAModule1" or any(x in name for x in ["au", "drau", "out"]):
                output["draussen"] = {
                    "temp": m_dash.get("Temperature"),
                    "hum": m_dash.get("Humidity"),
                    "trend": m_dash.get("temp_trend", "stable"),
                    "battery": battery
                }
            # BÜRO
            elif any(x in name for x in ["bür", "buer", "firm"]):
                output["buero"] = {
                    "temp": m_dash.get("Temperature"),
                    "hum": m_dash.get("Humidity"),
                    "co2": m_dash.get("CO2"),
                    "trend": m_dash.get("temp_trend", "stable"),
                    "battery": battery
                }
            # OBERGESCHOSS
            elif any(x in name for x in ["og", "ober"]):
                output["og"] = {
                    "temp": m_dash.get("Temperature"),
                    "hum": m_dash.get("Humidity"),
                    "co2": m_dash.get("CO2"),
                    "trend": m_dash.get("temp_trend", "stable"),
                    "battery": battery
                }

except Exception as e:
    print(f"Fehler bei Netatmo: {e}")

# 2. Open-Meteo Wetterdaten (inkl. stündlicher Daten & Niederschlag)
try:
    om_res = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 49.563,
            "longitude": 7.022,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,sunrise,sunset",
            "hourly": "temperature_2m,weathercode,precipitation_probability,precipitation",
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
