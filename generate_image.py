import os
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright
from PIL import Image  # Neu hinzugefügt!

PORT = 8080

def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()

def create_epaper_bmp():
    # 1. Lokalen Webserver im Hintergrund starten
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Browser starten
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 800, "height": 480},
            timezone_id="Europe/Berlin",
            extra_http_headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        page = context.new_page()
        
        # Aufrufen der E-Paper HTML Seite
        page.goto(f"http://localhost:{PORT}/epaper.html")
        
        # 3. Warten auf JS 'ready' Signal
        page.wait_for_function("window.status === 'ready'", timeout=10000)
        
        # 4. Screenshot temporär als PNG speichern
        temp_png = "epaper_temp.png"
        page.screenshot(path=temp_png)
        
        browser.close()

    # 5. PNG in 1-Bit Schwarz-Weiß BMP umwandeln (für den ESP32)
    with Image.open(temp_png) as img:
        # '1' steht für 1-Bit Pixel (Monochrom: rein Schwarz/Weiß)
        bmp_img = img.convert("1")
        bmp_img.save("epaper.bmp", "BMP")

    # Temp-Datei aufräumen
    if os.path.exists(temp_png):
        os.remove(temp_png)

    print("Erfolg: epaper.bmp wurde perfekt und ESP32-konform erstellt!")

if __name__ == "__main__":
    create_epaper_bmp()
