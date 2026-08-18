import os
from playwright.sync_api import sync_playwright

def create_epaper_png():
    with sync_playwright() as p:
        # Chromium mit Zusatz-Flags starten, damit lokale Dateien (file://) problemlos Daten laden dürfen
        browser = p.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security"])
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # Lokale epaper.html laden
        file_path = f"file://{os.path.abspath('epaper.html')}"
        page.goto(file_path, wait_until="networkidle")
        
        # 8 Sekunden warten, damit alle JavaScript-Funktionen die Werte garantiert eingetragen haben
        page.wait_for_timeout(8000)
        
        # Beide Bildnamen zur Sicherheit aktualisieren
        page.screenshot(path="epaper.png")
        page.screenshot(path="display.png")
        
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
