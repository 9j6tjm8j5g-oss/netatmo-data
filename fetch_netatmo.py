import json
import os
import requests
import time
from datetime import datetime
import zoneinfo

TOKEN_FILE = "token.json"

CLIENT_ID = os.environ.get("NETATMO_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("NETATMO_CLIENT_SECRET", "").strip()

tz = zoneinfo.ZoneInfo("Europe/Berlin")

# 1. Refresh Token
refresh_token = None
if os.path.exists(TOKEN_FILE):
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            refresh_token = json.load(f).get("refresh_token")
    except Exception as e:
        print(f"Hinweis: {e}")

if not refresh_token:
    refresh_token = os.environ.get("NETATMO_REFRESH_TOKEN", "").strip()

if not refresh_token:
    raise SystemExit("FEHLER: Kein Refresh Token gefunden!")

# 2. Token erneuern
auth_res = requests.post(
    "https://api.netatmo.com/oauth2/token",
    data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
)

auth_data = auth_res.json()
access_token = auth_data.get("access_token")
new_refresh_token = auth_data.get("refresh_token")

if not access_token or not new_refresh_token:
    print("FEHLER beim Refresh:", auth_data)
    raise SystemExit("Token ungültig.")

with open(TOKEN_FILE, "w", encoding="utf-8") as f:
    json.dump({"refresh_token": new_refresh_token}, f, indent=2)

# 3. Netatmo Daten abrufen
MAX_VERSUCHE = 6
WAIT_SECONDS = 20

raw_data = {}
for versuch in range(1, MAX_VERSUCHE + 1):
    data_res = requests.get(
        "https://api.netatmo.com/api/getstationsdata",
        params={"no_cache": "true"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    raw_data = data_res.json()
    devices = raw_data.get("body", {}).get("devices", [])

    if devices:
        main_mod = devices[0]
        dash = main_mod.get("dashboard_data", {})
        netatmo_ts = dash.get("time_utc")

        if netatmo_ts:
            alter_in_sekunden = datetime.now(tz).timestamp() - netatmo_ts
            if alter_in_sekunden < 480:
                print(f"Frische Daten erhalten! (Alter: {int(alter_in_sekunden)}s)")
                break
            else:
                if versuch < MAX_VERSUCHE:
                    time.sleep(WAIT_SECONDS)

devices = raw_data.get("body", {}).get("devices", [])
output = {}

def fmt(val):
    return round(float(val), 1) if val is not None else None

if devices:
    main_mod = devices[0]
    dash = main_mod.get("dashboard_data", {})

    netatmo_ts = dash.get("time_utc")
    if netatmo_ts:
        output["netatmo_messzeit"] = datetime.fromtimestamp(netatmo_ts, tz=tz).strftime("%H:%M")
    else:
        output["netatmo_messzeit"] = "unbekannt"

    # Hauptmodul -> Immer Wohnzimmer
    output["wohnzimmer"] = {
        "temp": fmt(dash.get("Temperature")),
        "hum": dash.get("Humidity"),
        "co2": dash.get("CO2"),
        "trend": dash.get("temp_trend", "stable"),
    }
    output["druck"] = {
        "val": fmt(dash.get("Pressure")),
        "trend": dash.get("pressure_trend", "stable"),
    }

    # Zusatzmodule durchlaufen
    for mod in main_mod.get("modules", []):
        mod_type = mod.get("type")
        name = mod.get("module_name", "").lower()
        m_dash = mod.get("dashboard_data", {})
        battery = mod.get("battery_percent")

        if not m_dash:
            continue

        if mod_type == "NAModule3":  # Regen
            output["regen"] = {
                "rain": m_dash.get("Rain", 0),
                "sum_1h": m_dash.get("sum_rain_1", 0),
                "sum_24h": m_dash.get("sum_rain_24", 0),
                "battery": battery,
            }
            continue

        if mod_type == "NAModule2":  # Wind
            output["wind"] = {
                "speed": m_dash.get("WindStrength"),
                "gust": m_dash.get("GustStrength"),
                "angle": m_dash.get("WindAngle"),
                "battery": battery,
            }
            continue

        mod_data = {
            "temp": fmt(m_dash.get("Temperature")),
            "hum": m_dash.get("Humidity"),
            "co2": m_dash.get("CO2"),
            "trend": m_dash.get("temp_trend", "stable"),
            "battery": battery,
        }

        # Eindeutige und feste Zuordnung nach Modultyp und Name:
        if mod_type == "NAModule1" or "aussen" in name or "draußen" in name:
            output["draussen"] = mod_data
        elif "og" in name or "obergeschoss" in name:
            output["og"] = mod_data
        elif "büro" in name or "buero" in name or "office" in name or "firma" in name:
            output["buero"] = mod_data
        elif "keller" in name:
            output["keller"] = mod_data

# 4. Open-Meteo
try:
    om_res = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 49.5694,
            "longitude": 7.0097,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode",
            "hourly": "temperature_2m,precipitation_probability,precipitation,weathercode",
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

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
