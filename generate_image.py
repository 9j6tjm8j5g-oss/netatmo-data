import os
from playwright.sync_api import sync_playwright

def create_epaper_png():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        html_path = os.path.abspath("epaper.html")
        page.goto(f"file://{html_path}")
        
        # 1. Erzwinge 5 Sekunden Wartezeit, damit fetch('data.json') sicher durchläuft
        page.wait_for_timeout(5000)
        
        # 2. Bild speichern
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
