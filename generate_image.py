import os
from playwright.sync_api import sync_playwright

def create_epaper_png():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # Lokale epaper.html aufrufen
        file_path = f"file://{os.path.abspath('epaper.html')}"
        
        # Warten, bis alle Netzwerkanfragen (wie das Laden von data.json) durch sind
        page.goto(file_path, wait_until="networkidle")
        
        # 5 Sekunden Sicherheitspuffer für das JS-Rendering
        page.wait_for_timeout(5000)
        
        # Bild speichern
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
