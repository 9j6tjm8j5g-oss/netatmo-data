import os
import requests
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        token_url = "https://api.netatmo.com/oauth2/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": os.environ.get("NETATMO_CLIENT_ID"),
            "client_secret": os.environ.get("NETATMO_CLIENT_SECRET"),
            "refresh_token": os.environ.get("NETATMO_REFRESH_TOKEN"),
        }
        
        try:
            res = requests.post(token_url, data=payload, timeout=5)
            token_data = res.json()
            access_token = token_data.get("access_token")

            station_url = "https://api.netatmo.com/api/getstationsdata"
            headers = {"Authorization": f"Bearer {access_token}"}
            netatmo_res = requests.get(station_url, headers=headers, timeout=5).json()

            meteo_url = "https://api.open-meteo.com/v1/forecast?latitude=49.5606&longitude=7.0142&hourly=temperature_2m,precipitation_probability,precipitation,weathercode&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Europe%2FBerlin"
            meteo_data = requests.get(meteo_url, timeout=5).json()

            device = netatmo_res.get("body", {}).get("devices", [{}])[0]
            
            output = {
                "timestamp": "Live",
                "wohnzimmer": {},
                "draussen": {},
                "buero": {},
                "og": {},
                "druck": {},
                "regen": {},
                "vorhersage": meteo_data
            }

            if device:
                dash = device.get("dashboard_data", {})
                output["wohnzimmer"] = {"temp": dash.get("Temperature"), "hum": dash.get("Humidity"), "co2": dash.get("CO2"), "trend": dash.get("temp_trend")}
                output["druck"] = {"val": dash.get("Pressure"), "trend": dash.get("pressure_trend")}

                for mod in device.get("modules", []):
                    m_dash = mod.get("dashboard_data", {})
                    m_type = mod.get("type")
                    m_name = mod.get("module_name", "")

                    if m_type == "NAModule1":
                        output["draussen"] = {"temp": m_dash.get("Temperature"), "hum": m_dash.get("Humidity"), "trend": m_dash.get("temp_trend"), "battery": mod.get("battery_percent")}
                    elif m_type == "NAModule4":
                        if "Büro" in m_name or "Firma" in m_name:
                            output["buero"] = {"temp": m_dash.get("Temperature"), "hum": m_dash.get("Humidity"), "co2": m_dash.get("CO2"), "trend": m_dash.get("temp_trend"), "battery": mod.get("battery_percent")}
                        elif "OG" in m_name:
                            output["og"] = {"temp": m_dash.get("Temperature"), "hum": m_dash.get("Humidity"), "co2": m_dash.get("CO2"), "trend": m_dash.get("temp_trend"), "battery": mod.get("battery_percent")}
                    elif m_type == "NAModule3":
                        output["regen"] = {"rain": m_dash.get("Rain"), "sum_1h": m_dash.get("sum_rain_1"), "sum_24h": m_dash.get("sum_rain_24"), "battery": mod.get("battery_percent")}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(output).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
