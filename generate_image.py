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

    # 2. Browser mit deutscher Zeitzone (Europe/Berlin) starten
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 800, "height": 480},
            timezone_id="Europe/Berlin",  # Zwingt Playwright auf deutsche Zeit
            extra_http_headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        page = context.new_page()
        
        page.goto(f"http://localhost:{PORT}/epaper.html", wait_until="networkidle")
        page.wait_for_timeout(3000)
        
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
