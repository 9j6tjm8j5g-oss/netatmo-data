import os
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright

PORT = 8000

def create_epaper_png():
    # 1. Lokalen Webserver im Hintergrund aufsetzen
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    try:
        # 2. Playwright starten und Bild erzeugen
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 800, "height": 480})
            
            page.goto(f"http://localhost:{PORT}/epaper.html")
            page.wait_for_timeout(6000)
            
            page.screenshot(path="epaper.png")
            browser.close()
    finally:
        # 3. Server sauber beenden, damit das Skript nicht hängen bleibt!
        httpd.shutdown()
        httpd.server_close()

if __name__ == "__main__":
    create_epaper_png()
