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
    # 1. Lokalen Webserver starten
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Browser starten
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # device_scale_factor=2 sorgt für Gestochen scharfe Schrift (Retina/HD)
        context = browser.new_context(
            viewport={"width": 800, "height": 480},
            device_scale_factor=2,
            timezone_id="Europe/Berlin",
            extra_http_headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        page = context.new_page()
        page.goto(f"http://localhost:{PORT}/epaper.html")
        
        # CSS Injection für knallharte Schwarz-Weiß-Ränder ohne Grauschleier
        page.add_style_tag(content="""
            html, body {
                width: 800px !important;
                height: 480px !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                background-color: #ffffff !important;
                -webkit-font-smoothing: none !important;
            }
            * {
                box-sizing: border-box !important;
            }
        """)
        
        page.wait_for_function("window.status === 'ready'", timeout=10000)
        
        temp_png = "epaper_temp.png"
        page.screenshot(path=temp_png)
        browser.close()

    # 3. Bildverarbeitung: Scharfes Binarisieren
    with Image.open(temp_png) as img:
        # Exakt auf 800x480 mit hochwertigem Resampling bringen
        img = img.resize((800, 480), Image.Resampling.LANCZOS)
        
        # In Graustufen umwandeln
        gray = img.convert("L")
        
        # Dithering (Floyd-Steinberg) verhindert klumpige Treppenstufen
        bmp_img = gray.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        
        bmp_img.save("epaper.bmp", "BMP")

    if os.path.exists(temp_png):
        os.remove(temp_png)

    print("Erfolg: epaper.bmp messerscharf generiert!")

if __name__ == "__main__":
    create_epaper_bmp()
