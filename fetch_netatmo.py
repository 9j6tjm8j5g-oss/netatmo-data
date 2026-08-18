import json
import os
import requests
from datetime import datetime
import zoneinfo

TOKEN_FILE = "token.json"

CLIENT_ID = os.environ.get("NETATMO_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("NETATMO_CLIENT_SECRET", "").strip()

# Zeitzone definieren
tz = zoneinfo.ZoneInfo("Europe/Berlin")

# 1. Refresh Token ermitteln
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

# Token sichern
with open(TOKEN_FILE, "w", encoding="utf-8") as f:
    json.dump({"refresh_token": new_refresh_token}, f, indent=2)

# 3. Netatmo Daten abrufen
data_res = requests.get(
    "https://api.netatmo.com/api/getstationsdata",
    params={"no_cache": "true"},
    headers={"Authorization": f"Bearer {access_token}"},
)
raw_data = data_res.json()
devices = raw_data.get("body", {}).get("devices", [])
output = {}

def fmt(val):
    return round(float(val), 1) if val is not None else None

if devices:
    main_mod = devices[0]
    dash = main_mod.get("dashboard_data", {})

    # NEU: Exakten Messzeitpunkt der Netatmo-Station auslesen
    netatmo_ts = dash.get("time_utc")
    if netatmo_ts:
        output["netatmo_messzeit"] = datetime.fromtimestamp(netatmo_ts, tz=tz).strftime("%H:%M")
    else:
        output["netatmo_messzeit"] = "unbekannt"

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

        if "aussen" in name or "draußen" in name or mod_type == "NAModule1":
            output["draussen"] = {
                "temp": mod_data["temp"],
                "hum": mod_data["hum"],
                "trend": mod_data["trend"],
                "battery": battery,
            }
        elif "firma" in name:
            output["firma"] = mod_data
        elif "keller" in name:
            output["keller"] = mod_data
        elif "og" in name or "obergeschoss" in name:
            output["og"] = mod_data

# 4. Open-Meteo Wettervorhersage abrufen (Nohfelden-Eiweiler)
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
    print(f"Fehler beim Laden von Open-Meteo: {e}")

# Uhrzeit des Abrufs (Skript-Laufzeit)
output["timestamp"] = datetime.now(tz).strftime("%H:%M")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
from playwright.sync_api import sync_playwright

def create_epaper_png():
    with sync_playwright() as p:
        # Browser starten
        browser = p.chromium.launch()
        # Bildschirmgröße exakt auf dein E-Paper anpassen (z. B. 800x480)
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # Deine GitHub Pages HTML-Seite aufrufen (oder eine lokale epaper.html)
        page.goto("https://9j6tjm8j5g-oss.github.io/netatmo-data/epaper.html")
        
        # Warten, bis alles geladen ist (z. B. 2 Sekunden)
        page.wait_for_timeout(2000)
        
        # Screenshot als epaper.png speichern
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
