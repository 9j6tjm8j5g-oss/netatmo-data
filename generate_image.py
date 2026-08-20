import os
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright
from PIL import Image

PORT = 8080

def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()

def create_epaper_bmp():
    # 1. Server im Hintergrund
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Screenshot in exakt 800x480 erstellen
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 800, "height": 480},
            device_scale_factor=1,
            timezone_id="Europe/Berlin"
        )
        page = context.new_page()
        page.goto(f"http://localhost:{PORT}/epaper.html")
        page.wait_for_function("window.status === 'ready'", timeout=10000)
        
        temp_png = "epaper_temp.png"
        page.screenshot(path=temp_png)
        browser.close()

    # 3. Direkte, saubere 1-Bit Umwandlung
    with Image.open(temp_png) as img:
        # Binarisierung ohne Dithering-Muster
        bmp_img = img.convert("L").point(lambda p: 255 if p > 140 else 0).convert("1")
        bmp_img.save("epaper.bmp", "BMP")

    if os.path.exists(temp_png):
        os.remove(temp_png)

    print("epaper.bmp erfolgreich erstellt!")

if __name__ == "__main__":
    create_epaper_bmp()
