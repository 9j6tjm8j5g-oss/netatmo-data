import os
import http.server
import socketserver
import threading
from playwright.sync_api import sync_playwright

PORT = 8000

def start_server():
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

def create_epaper_png():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        page.goto(f"http://localhost:{PORT}/epaper.html")
        page.wait_for_timeout(6000)
        
        # Erzeugt nur noch epaper.png
        page.screenshot(path="epaper.png")
        
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
