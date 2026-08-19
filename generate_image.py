import os
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright

PORT = 8080

def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()

def create_epaper_png():
    # 1. Lokalen Webserver im Hintergrund starten
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Mit Playwright die HTML über http://localhost aufrufen
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # Ruft die Datei wie eine echte Webseite auf (CORS-Sperre ist damit aufgehoben)
        page.goto(f"http://localhost:{PORT}/epaper.html")
        
        # 3. Kurz warten, bis fetch('data.json') & Open-Meteo fertig sind
        page.wait_for_timeout(4000)
        
        # Screenshot erstellen
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
