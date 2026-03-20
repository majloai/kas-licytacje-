"""
Scraper licytacji KAS (Krajowa Administracja Skarbowa)
Pobiera obwieszczenia ze wszystkich 16 Izb Administracji Skarbowej w Polsce.
"""
 
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9",
}
 
IAS_OFFICES = [
    {"region": "Dolnośląskie",        "city": "Wrocław",         "url": "https://www.dolnoslaskie.kas.gov.pl/izba-administracji-skarbowej-we-wroclawiu/ogloszenia/obwieszczenia-o-licytacjach",          "base_url": "https://www.dolnoslaskie.kas.gov.pl"},
    {"region": "Kujawsko-Pomorskie",  "city": "Bydgoszcz",       "url": "https://www.kujawsko-pomorskie.kas.gov.pl/izba-administracji-skarbowej-w-bydgoszczy/ogloszenia/obwieszczenia-o-licytacjach",    "base_url": "https://www.kujawsko-pomorskie.kas.gov.pl"},
    {"region": "Lubelskie",           "city": "Lublin",          "url": "https://www.lubelskie.kas.gov.pl/izba-administracji-skarbowej-w-lublinie/ogloszenia/obwieszczenia-o-licytacjach",               "base_url": "https://www.lubelskie.kas.gov.pl"},
    {"region": "Lubuskie",            "city": "Zielona Góra",    "url": "https://www.lubuskie.kas.gov.pl/izba-administracji-skarbowej-w-zielonej-gorze/ogloszenia/obwieszczenia-o-licytacjach",          "base_url": "https://www.lubuskie.kas.gov.pl"},
    {"region": "Łódzkie",             "city": "Łódź",            "url": "https://www.lodzkie.kas.gov.pl/izba-administracji-skarbowej-w-lodzi/ogloszenia/obwieszczenia-o-licytacjach",                    "base_url": "https://www.lodzkie.kas.gov.pl"},
    {"region": "Małopolskie",         "city": "Kraków",          "url": "https://www.malopolskie.kas.gov.pl/izba-administracji-skarbowej-w-krakowie/ogloszenia/obwieszczenia-o-licytacjach",             "base_url": "https://www.malopolskie.kas.gov.pl"},
    {"region": "Mazowieckie",         "city": "Warszawa",        "url": "https://www.mazowieckie.kas.gov.pl/izba-administracji-skarbowej-w-warszawie/ogloszenia/obwieszczenia-o-licytacjach",            "base_url": "https://www.mazowieckie.kas.gov.pl"},
    {"region": "Opolskie",            "city": "Opole",           "url": "https://www.opolskie.kas.gov.pl/izba-administracji-skarbowej-w-opolu/ogloszenia/obwieszczenia-o-licytacjach",                   "base_url": "https://www.opolskie.kas.gov.pl"},
    {"region": "Podkarpackie",        "city": "Rzeszów",         "url": "https://www.podkarpackie.kas.gov.pl/izba-administracji-skarbowej-w-rzeszowie/ogloszenia/obwieszczenia-o-licytacjach",           "base_url": "https://www.podkarpackie.kas.gov.pl"},
    {"region": "Podlaskie",           "city": "Białystok",       "url": "https://www.podlaskie.kas.gov.pl/izba-administracji-skarbowej-w-bialymstoku/ogloszenia/obwieszczenia-o-licytacjach",            "base_url": "https://www.podlaskie.kas.gov.pl"},
    {"region": "Pomorskie",           "city": "Gdańsk",          "url": "https://www.pomorskie.kas.gov.pl/izba-administracji-skarbowej-w-gdansku/ogloszenia/obwieszczenia-o-licytacjach",                "base_url": "https://www.pomorskie.kas.gov.pl"},
    {"region": "Śląskie",             "city": "Katowice",        "url": "https://www.slaskie.kas.gov.pl/izba-administracji-skarbowej-w-katowicach/ogloszenia/obwieszczenia-o-licytacjach",               "base_url": "https://www.slaskie.kas.gov.pl"},
    {"region": "Świętokrzyskie",      "city": "Kielce",          "url": "https://www.swietokrzyskie.kas.gov.pl/izba-administracji-skarbowej-w-kielcach/ogloszenia/obwieszczenia-o-licytacjach",          "base_url": "https://www.swietokrzyskie.kas.gov.pl"},
    {"region": "Warmińsko-Mazurskie", "city": "Olsztyn",         "url": "https://www.warminsko-mazurskie.kas.gov.pl/izba-administracji-skarbowej-w-olsztynie/ogloszenia/obwieszczenia-o-licytacjach",    "base_url": "https://www.warminsko-mazurskie.kas.gov.pl"},
    {"region": "Wielkopolskie",       "city": "Poznań",          "url": "https://www.wielkopolskie.kas.gov.pl/izba-administracji-skarbowej-w-poznaniu/ogloszenia/obwieszczenia-o-licytacjach",           "base_url": "https://www.wielkopolskie.kas.gov.pl"},
    {"region": "Zachodniopomorskie",  "city": "Szczecin",        "url": "https://www.zachodniopomorskie.kas.gov.pl/izba-administracji-skarbowej-w-szczecinie/ogloszenia/obwieszczenia-o-licytacjach",    "base_url": "https://www.zachodniopomorskie.kas.gov.pl"},
]
 
SKIP_KEYWORDS = [
    "Przejdź do", "Izba Admin", "Urząd Skarbowy",
    "Pierwsz", "Drugi ", "Trzeci ", "Czytaj więcej", "Czytaj wi",
]
 
CONTENT_KEYWORDS = [
    "licytacj", "sprzedaż", "sprzedaz", "ruchom", "nieruchom",
    "obwieszczen", "zawiadomien", "przetarg",
    "samochód", "samochod", "pojazd", "mieszkan", "działk",
    "grunt", "lokal", "maszyn", "sprzęt", "naczepa", "przyczepa",
    "motocykl", "ciągnik", "traktor", "autobus", "ciężar",
    "osobowy", "budynek", "dom ", "opel", "ford", "bmw", "audi",
    "toyota", "honda", "fiat", "renault", "peugeot", "skoda",
    "mercedes", "volkswagen", "hyundai", "kia", "mazda",
]
 
 
def detect_category(title):
    tl = title.lower()
    if any(k in tl for k in ["nieruchom", "mieszkan", "lokal", "dzialka", "działk", "grunt", "budynek", "kamienica", "garaż"]):
        return "Nieruchomości"
    if any(k in tl for k in ["samochód", "samochod", "auto", "pojazd", "motorow", "motocykl", "ciągnik",
                              "bmw", "audi", "ford", "vw", "opel", "mercedes", "toyota", "renault",
                              "peugeot", "skoda", "fiat", "hyundai", "kia", "seat", "honda", "mazda",
                              "nissan", "volvo", "suzuki", "dacia", "sprinter", "transit", "vivaro",
                              "boxer", "ducato", "kangoo", "berlingo", "citroen"]):
        return "Pojazdy"
    return "Inne ruchomości"
 
 
def detect_type(title):
    tl = title.lower()
    if "pierwsz" in tl and "licytacj" in tl:
        return "I licytacja"
    if "drug" in tl and "licytacj" in tl:
        return "II licytacja"
    if "wolnej ręki" in tl or "wolna ręka" in tl:
        return "Wolna ręka"
    if "przetarg" in tl:
        return "Przetarg"
    if "odwołan" in tl or "unieważn" in tl:
        return "Odwołanie"
    if "licytacj" in tl:
        return "Licytacja"
    return "Ogłoszenie"
 
 
def extract_date(title):
    patterns = [
        r"\b(\d{1,2})[.\-](\d{1,2})[.\-](20\d{2})\b",
        r"\b(\d{1,2})\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|"
        r"lipca|sierpnia|wrze[sś]nia|pa[zź]dziernik\w*|listopada|grudnia)\s+(20\d{2})\b",
    ]
    months = {
        "stycznia": "01", "lutego": "02", "marca": "03", "kwietnia": "04",
        "maja": "05", "czerwca": "06", "lipca": "07", "sierpnia": "08",
        "wrzesnia": "09", "września": "09", "pazdziernika": "10", "października": "10",
        "listopada": "11", "grudnia": "12",
    }
    for pat in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            groups = m.groups()
            if len(groups) == 3:
                day, month, year = groups
                if month.isdigit():
                    return f"{int(day):02d}.{int(month):02d}.{year}"
                else:
                    month_num = next(
                        (v for k, v in months.items() if month.lower().startswith(k[:4])),
                        "??"
                    )
                    return f"{int(day):02d}.{month_num}.{year}"
    return ""
 
 
def scrape_ias(session, office):
    """Pobiera i parsuje wszystkie strony jednej IAS z obsługą paginacji."""
    all_listings = []
    seen_titles = set()
    current_url = office["url"]
    page = 1
 
    while current_url:
        print(f"    📄 Strona {page}: {current_url}")
        try:
            resp = session.get(current_url, headers=HEADERS, timeout=25)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
        except requests.RequestException as e:
            print(f"  ❌ Błąd {office['city']} strona {page}: {e}")
            break
 
        soup = BeautifulSoup(resp.text, "html.parser")
 
        content_area = (
            soup.find(id="main-content")
            or soup.find(class_=re.compile(r"portlet-content|journal-content|asset-publisher"))
            or soup.body
        )
 
        found_on_page = 0
        for a_tag in content_area.find_all("a", href=True):
            href = a_tag.get("href", "")
            title = a_tag.get_text(strip=True)
 
            if not title or len(title) < 15:
                continue
 
            if any(title.startswith(sk) for sk in SKIP_KEYWORDS):
                continue
 
            if not any(kw in title.lower() for kw in CONTENT_KEYWORDS):
                continue
 
            if title in seen_titles:
                continue
 
            seen_titles.add(title)
 
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = office["base_url"] + href
            else:
                full_url = office["base_url"] + "/" + href
 
            all_listings.append({
                "region":     office["region"],
                "city":       office["city"],
                "title":      title,
                "url":        full_url,
                "category":   detect_category(title),
                "type":       detect_type(title),
                "date":       extract_date(title),
                "source_url": current_url,
            })
            found_on_page += 1
 
        # Szukaj linku do następnej strony
        next_url = None
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True).lower()
            href = a_tag.get("href", "")
            if text in ["»", "następna", "next", str(page + 1)]:
                if href.startswith("http"):
                    next_url = href
                elif href.startswith("/"):
                    next_url = office["base_url"] + href
                else:
                    next_url = office["base_url"] + "/" + href
                break
 
        if page >= 15:
            print(f"  ⚠️ Osiągnięto limit 15 stron dla {office['city']}")
            next_url = None
 
        current_url = next_url
        page += 1
        if current_url:
            time.sleep(0.5)
 
    print(f"  ✅ {office['city']} ({office['region']}): {len(all_listings)} ogłoszeń ({page-1} stron)")
    return all_listings
 
 
def run_scraper():
    session = requests.Session()
    all_listings = []
 
    print(f"\n🔍 Start scrapowania KAS — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
 
    for office in IAS_OFFICES:
        print(f"📌 {office['city']} ({office['region']})...")
        listings = scrape_ias(session, office)
        all_listings.extend(listings)
        time.sleep(1)
 
    by_region = {}
    by_category = {}
    for item in all_listings:
        by_region[item["region"]] = by_region.get(item["region"], 0) + 1
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
 
    result = {
        "scraped_at":   datetime.now().isoformat(),
        "total":        len(all_listings),
        "listings":     all_listings,
        "by_region":    by_region,
        "by_category":  by_category,
    }
 
    print(f"\n📊 Łącznie znaleziono: {len(all_listings)} ogłoszeń")
    return result
 
 
if __name__ == "__main__":
    data = run_scraper()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 Zapisano do data.json")
