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
    # 1. Lokalen Webserver im Hintergrund starten
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Browser starten
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # Exakt 800x480 Viewport erzwingen
        context = browser.new_context(
            viewport={"width": 800, "height": 480},
            device_scale_factor=1,
            timezone_id="Europe/Berlin",
            extra_http_headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        page = context.new_page()
        
        # E-Paper HTML Seite aufrufen
        page.goto(f"http://localhost:{PORT}/epaper.html")
        
        # CSS-Injection: Zwingt Body und HTML auf volle 800x480 ohne Abstände
        page.add_style_tag(content="""
            html, body {
                width: 800px !important;
                height: 480px !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                background-color: #ffffff !important;
            }
        """)
        
        # 3. Warten auf JS 'ready' Signal
        page.wait_for_function("window.status === 'ready'", timeout=10000)
        
        # 4. Screenshot exakt in 800x480 aufnehmen
        temp_png = "epaper_temp.png"
        page.screenshot(path=temp_png, clip={"x": 0, "y": 0, "width": 800, "height": 480})
        
        browser.close()

    # 5. PNG ohne Dithering (messerscharf) in 1-Bit BMP umwandeln
    with Image.open(temp_png) as img:
        # Auf 800x480 absichern
        img = img.resize((800, 480))
        
        # In Graustufen konvertieren
        gray = img.convert("L")
        
        # Schwellenwert: Alles heller als 128 wird Weiß, der Rest Schwarz
        threshold = 128
        bmp_img = gray.point(lambda p: 255 if p > threshold else 0).convert("1", dither=Image.Dither.NONE)
        
        # Als 1-Bit Monochrom BMP speichern
        bmp_img.save("epaper.bmp", "BMP")

    # Temp-Datei aufräumen
    if os.path.exists(temp_png):
        os.remove(temp_png)

    print("Erfolg: epaper.bmp wurde in 800x480 scharf erstellt!")

if __name__ == "__main__":
    create_epaper_bmp()
