import os
from playwright.sync_api import sync_playwright

def create_epaper_png():
    with sync_playwright() as p:
        # Chromium starten mit Freigabe für lokale Dateien
        browser = p.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security"])
        page = browser.new_page(viewport={"width": 800, "height": 480})
        
        # Lokale epaper.html aufrufen
        file_path = f"file://{os.path.abspath('epaper.html')}"
        page.goto(file_path)
        
        # 6 Sekunden warten, damit JavaScript alle Daten eintragen kann
        page.wait_for_timeout(6000)
        
        # Beide Dateinamen direkt speichern
        page.screenshot(path="epaper.png")
        page.screenshot(path="display.png")
        
        browser.close()

if __name__ == "__main__":
    create_epaper_png()
