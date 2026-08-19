import os
import json
from playwright.sync_api import sync_playwright

def create_epaper_png():
    # 1. data.json direkt einlesen
    json_data = {}
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # 2. HTML-Datei öffnen
        html_path = os.path.abspath("epaper.html")
        page.goto(f"file://{html_path}")
        
        # 3. JSON direkt in die Seite injizieren und Render-Funktion aufrufen
        page.evaluate(f"if (typeof renderData === 'function') renderData({json.dumps(json_data)});")
        
        # Kurz warten, falls Wetter-API noch rendert
        page.wait_for_timeout(3000)
        
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
