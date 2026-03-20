"""
Główny skrypt agenta — uruchamia scraper i generuje raport HTML.
"""

import json
import os
from scraper import run_scraper
from generate_report import generate_html

def main():
    # 1. Scrapuj dane
    data = run_scraper()

    # 2. Zapisz dane JSON (dla archiwum / debugowania)
    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 Dane JSON zapisane: docs/data.json")

    # 3. Wygeneruj raport HTML
    html = generate_html(data)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("📄 Raport HTML zapisany: docs/index.html")
    print(f"\n✅ GOTOWE — {data['total']} ogłoszeń, raport dostępny na GitHub Pages")

if __name__ == "__main__":
    main()
