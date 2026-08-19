import os
import json
from playwright.sync_api import sync_playwright

def create_epaper_png():
    # 1. Daten direkt in Python aus der data.json lesen
    json_data = {}
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # 2. HTML-Vorlage lokal öffnen
        html_path = os.path.abspath("epaper.html")
        page.goto(f"file://{html_path}")
        
        # 3. Die Daten direkt ins JavaScript injizieren
        # Das umgeht die CORS/fetch-Sperre von Chromium vollständig!
        script = f"""
            if (typeof renderData === 'function') {{
                renderData({json.dumps(json_data)});
            }} else if (typeof updateUI === 'function') {{
                updateUI({json.dumps(json_data)});
            }}
        """
        page.evaluate(script)
        
        # Kurz warten, damit das Wetter fertig gerendert ist
        page.wait_for_timeout(4000)
        
        page.screenshot(path="epaper.png")
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
