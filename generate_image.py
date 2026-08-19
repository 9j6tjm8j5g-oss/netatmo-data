import os
from playwright.sync_api import sync_playwright

def create_epaper_png():
    with sync_playwright() as p:
        # --allow-file-access-from-files erlaubt fetch('data.json') direkt über file://
        browser = p.chromium.launch(args=["--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # Pfad zur lokalen epaper.html ermitteln
        html_path = os.path.abspath("epaper.html")
        page.goto(f"file://{html_path}")
        
        # Kurz warten, damit JS die data.json liest und das DOM aktualisiert
        page.wait_for_timeout(4000)
        
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
