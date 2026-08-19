import os
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright

PORT = 8080

def start_server():
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()

def create_epaper_png():
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
        
        # 3. Perfekte Synchronisation:
        # Wartet exakt darauf, dass das JS in der HTML "window.status = 'ready'" setzt!
        page.wait_for_function("window.status === 'ready'", timeout=10000)
        
        # 4. Screenshot direkt erstellen
        page.screenshot(path="epaper.png")
        print("Erfolg: epaper.png wurde perfekt und vollständig erstellt!")
        
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
