"""
Scraper licytacji KAS (Krajowa Administracja Skarbowa)
Pobiera obwieszczenia ze wszystkich 16 Izb Administracji Skarbowej w Polsce.
Strony IAS agregują ogłoszenia ze wszystkich lokalnych Urzędów Skarbowych.
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
    {"region": "Dolnośląskie",        "city": "Wrocław",      "url": "https://www.dolnoslaskie.kas.gov.pl/izba-administracji-skarbowej-we-wroclawiu/ogloszenia/obwieszczenia-o-licytacjach",          "base_url": "https://www.dolnoslaskie.kas.gov.pl"},
    {"region": "Kujawsko-Pomorskie",  "city": "Bydgoszcz",    "url": "https://www.kujawsko-pomorskie.kas.gov.pl/izba-administracji-skarbowej-w-bydgoszczy/ogloszenia/obwieszczenia-o-licytacjach",    "base_url": "https://www.kujawsko-pomorskie.kas.gov.pl"},
    {"region": "Lubelskie",           "city": "Lublin",       "url": "https://www.lubelskie.kas.gov.pl/izba-administracji-skarbowej-w-lublinie/ogloszenia/obwieszczenia-o-licytacjach",               "base_url": "https://www.lubelskie.kas.gov.pl"},
    {"region": "Lubuskie",            "city": "Zielona Góra", "url": "https://www.lubuskie.kas.gov.pl/izba-administracji-skarbowej-w-zielonej-gorze/ogloszenia/obwieszczenia-o-licytacjach",          "base_url": "https://www.lubuskie.kas.gov.pl"},
    {"region": "Łódzkie",             "city": "Łódź",         "url": "https://www.lodzkie.kas.gov.pl/izba-administracji-skarbowej-w-lodzi/ogloszenia/obwieszczenia-o-licytacjach",                    "base_url": "https://www.lodzkie.kas.gov.pl"},
    {"region": "Małopolskie",         "city": "Kraków",       "url": "https://www.malopolskie.kas.gov.pl/izba-administracji-skarbowej-w-krakowie/ogloszenia/obwieszczenia-o-licytacjach",             "base_url": "https://www.malopolskie.kas.gov.pl"},
    {"region": "Mazowieckie",         "city": "Warszawa",     "url": "https://www.mazowieckie.kas.gov.pl/izba-administracji-skarbowej-w-warszawie/ogloszenia/obwieszczenia-o-licytacjach",            "base_url": "https://www.mazowieckie.kas.gov.pl"},
    {"region": "Opolskie",            "city": "Opole",        "url": "https://www.opolskie.kas.gov.pl/izba-administracji-skarbowej-w-opolu/ogloszenia/obwieszczenia-o-licytacjach",                   "base_url": "https://www.opolskie.kas.gov.pl"},
    {"region": "Podkarpackie",        "city": "Rzeszów",      "url": "https://www.podkarpackie.kas.gov.pl/izba-administracji-skarbowej-w-rzeszowie/ogloszenia/obwieszczenia-o-licytacjach",           "base_url": "https://www.podkarpackie.kas.gov.pl"},
    {"region": "Podlaskie",           "city": "Białystok",    "url": "https://www.podlaskie.kas.gov.pl/izba-administracji-skarbowej-w-bialymstoku/ogloszenia/obwieszczenia-o-licytacjach",            "base_url": "https://www.podlaskie.kas.gov.pl"},
    {"region": "Pomorskie",           "city": "Gdańsk",       "url": "https://www.pomorskie.kas.gov.pl/izba-administracji-skarbowej-w-gdansku/ogloszenia/obwieszczenia-o-licytacjach",                "base_url": "https://www.pomorskie.kas.gov.pl"},
    {"region": "Śląskie",             "city": "Katowice",     "url": "https://www.slaskie.kas.gov.pl/izba-administracji-skarbowej-w-katowicach/ogloszenia/obwieszczenia-o-licytacjach",               "base_url": "https://www.slaskie.kas.gov.pl"},
    {"region": "Świętokrzyskie",      "city": "Kielce",       "url": "https://www.swietokrzyskie.kas.gov.pl/izba-administracji-skarbowej-w-kielcach/ogloszenia/obwieszczenia-o-licytacjach",          "base_url": "https://www.swietokrzyskie.kas.gov.pl"},
    {"region": "Warmińsko-Mazurskie", "city": "Olsztyn",      "url": "https://www.warminsko-mazurskie.kas.gov.pl/izba-administracji-skarbowej-w-olsztynie/ogloszenia/obwieszczenia-o-licytacjach",    "base_url": "https://www.warminsko-mazurskie.kas.gov.pl"},
    {"region": "Wielkopolskie",       "city": "Poznań",       "url": "https://www.wielkopolskie.kas.gov.pl/izba-administracji-skarbowej-w-poznaniu/ogloszenia/obwieszczenia-o-licytacjach",           "base_url": "https://www.wielkopolskie.kas.gov.pl"},
    {"region": "Zachodniopomorskie",  "city": "Szczecin",     "url": "https://www.zachodniopomorskie.kas.gov.pl/izba-administracji-skarbowej-w-szczecinie/ogloszenia/obwieszczenia-o-licytacjach",    "base_url": "https://www.zachodniopomorskie.kas.gov.pl"},
]
 
# Linki nawigacyjne do pominięcia
NAV_SKIP = [
    "Przejdź do", "Mapa strony", "Wersja kontrastowa",
    "Izba Administracji", "Urząd Celno", "Wiadomości",
    "Aktualności", "Organizacja", "Kierownictwo", "Regulamin",
    "Zamówienia", "Kariera", "Kontakt", "Dostępność",
    "Bip.gov", "Gov.pl", "YouTube", "Twitter", "RSS",
    "Serwis Służby", "Elektronicz",
]
 
# Słowa kluczowe potwierdzające że to ogłoszenie licytacyjne
CONTENT_KEYWORDS = [
    "licytacj", "sprzedaż", "sprzedaz", "ruchom", "nieruchom",
    "obwieszczen", "zawiadomien", "przetarg", "informacja roczna",
    "samochód", "samochod", "pojazd", "mieszkan", "działk",
    "grunt", "lokal", "maszyn", "naczepa", "przyczepa",
    "motocykl", "ciągnik", "traktor", "autobus", "ciężar",
    "osobowy", "budynek", "dom ", "opel", "ford", "bmw", "audi",
    "toyota", "honda", "fiat", "renault", "peugeot", "skoda",
    "mercedes", "volkswagen", "hyundai", "kia", "mazda",
    "nissan", "volvo", "dacia", "kawasaki", "yamaha", "suzuki",
]
 
 
def clean_title(raw_title):
    """
    Wyciąga prawdziwy tytuł z tekstu linku.
    Obsługuje formaty:
      - "Czytaj więcej o TYTUŁ»"
      - "Czytaj więcej o TYTUŁ »"
      - "Czytaj wiecej o TYTUŁ»"
      - normalny tytuł
    """
    t = raw_title.strip()
 
    # Usuń końcowe "»" i podobne
    t = t.rstrip("»›>").strip()
 
    # Wyciągnij tytuł z "Czytaj więcej o ..."
    prefixes = [
        "Czytaj więcej o ",
        "Czytaj wiecej o ",
        "Czytaj wi",  # skrócone (obcięte)
        "czytaj więcej o ",
    ]
    for prefix in prefixes:
        if t.lower().startswith(prefix.lower()):
            extracted = t[len(prefix):].strip()
            if len(extracted) > 10:
                return extracted
            return None  # za krótki — pomiń
 
    return t
 
 
def detect_category(title):
    tl = title.lower()
    if any(k in tl for k in ["nieruchom", "mieszkan", "lokal", "działk", "grunt",
                              "budynek", "kamienica", "garaż", "dom jedno"]):
        return "Nieruchomości"
    if any(k in tl for k in ["samochód", "samochod", "auto", "pojazd", "motorow",
                              "motocykl", "ciągnik", "bmw", "audi", "ford", "vw",
                              "opel", "mercedes", "toyota", "renault", "peugeot",
                              "skoda", "fiat", "hyundai", "kia", "seat", "honda",
                              "mazda", "nissan", "volvo", "suzuki", "dacia",
                              "sprinter", "transit", "vivaro", "boxer", "ducato",
                              "kangoo", "berlingo", "citroen", "kawasaki", "yamaha",
                              "ciężar", "autobus", "bus ", "van "]):
        return "Pojazdy"
    return "Inne ruchomości"
 
 
def detect_type(title):
    tl = title.lower()
    if ("pierwsz" in tl or "i licytacj" in tl) and "licytacj" in tl:
        return "I licytacja"
    if ("drug" in tl or "ii licytacj" in tl) and "licytacj" in tl:
        return "II licytacja"
    if "trzeci" in tl and "licytacj" in tl:
        return "III licytacja"
    if "wolnej ręki" in tl or "wolna ręka" in tl or "wolnej reki" in tl:
        return "Wolna ręka"
    if "przetarg" in tl:
        return "Przetarg"
    if "odwołan" in tl or "unieważn" in tl:
        return "Odwołanie"
    if "licytacj" in tl:
        return "Licytacja"
    return "Ogłoszenie"
 
 
def extract_date(title):
    months = {
        "stycznia": "01", "lutego": "02", "marca": "03", "kwietnia": "04",
        "maja": "05", "czerwca": "06", "lipca": "07", "sierpnia": "08",
        "wrzesnia": "09", "września": "09",
        "pazdziernika": "10", "października": "10",
        "listopada": "11", "grudnia": "12",
    }
    patterns = [
        r"\b(\d{1,2})[.\-](\d{1,2})[.\-](20\d{2})\b",
        r"\b(\d{1,2})\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|"
        r"lipca|sierpnia|wrze[sś]nia|pa[zź]dziernik\w*|listopada|grudnia)\s+(20\d{2})\b",
    ]
    for pat in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            day, month, year = m.groups()
            if month.isdigit():
                return f"{int(day):02d}.{int(month):02d}.{year}"
            month_num = next(
                (v for k, v in months.items() if month.lower().startswith(k[:4])), "??")
            return f"{int(day):02d}.{month_num}.{year}"
    return ""
 
 
def is_nav_link(title):
    """Sprawdza czy link to nawigacja, nie ogłoszenie."""
    for skip in NAV_SKIP:
        if title.startswith(skip):
            return True
    return False
 
 
def scrape_ias(session, office):
    """Pobiera i parsuje wszystkie strony jednej IAS z obsługą paginacji."""
    all_listings = []
    seen_urls = set()    # deduplication po URL
    seen_titles = set()  # deduplication po tytule
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
            or soup.find(class_=re.compile(
                r"portlet-content|journal-content|asset-publisher"))
            or soup.body
        )
 
        for a_tag in content_area.find_all("a", href=True):
            href = a_tag.get("href", "").strip()
            raw_title = a_tag.get_text(strip=True)
 
            # Pomiń puste i za krótkie
            if not raw_title or len(raw_title) < 10:
                continue
 
            # Pomiń nawigację
            if is_nav_link(raw_title):
                continue
 
            # Wyciągnij prawdziwy tytuł
            title = clean_title(raw_title)
            if not title or len(title) < 10:
                continue
 
            # Sprawdź czy zawiera słowa kluczowe licytacji
            if not any(kw in title.lower() for kw in CONTENT_KEYWORDS):
                continue
 
            # Buduj pełny URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = office["base_url"] + href
            else:
                full_url = office["base_url"] + "/" + href
 
            # Deduplication — sprawdź URL i tytuł
            title_key = re.sub(r"\s+", " ", title.lower().strip())
            if full_url in seen_urls or title_key in seen_titles:
                continue
 
            seen_urls.add(full_url)
            seen_titles.add(title_key)
 
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
 
        # Szukaj linku do następnej strony
        next_url = None
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True).lower().strip()
            href = a_tag.get("href", "")
            if text in ["»", "następna", "next", str(page + 1)]:
                if href.startswith("http"):
                    next_url = href
                elif href.startswith("/"):
                    next_url = office["base_url"] + href
                else:
                    next_url = office["base_url"] + "/" + href
                break
 
        if page >= 20:
            print(f"  ⚠️ Osiągnięto limit 20 stron dla {office['city']}")
            next_url = None
 
        current_url = next_url
        page += 1
        if current_url:
            time.sleep(0.5)
 
    print(f"  ✅ {office['city']} ({office['region']}): "
          f"{len(all_listings)} ogłoszeń ({page-1} stron)")
    return all_listings
 
 
def run_scraper():
    session = requests.Session()
    all_listings = []
 
    print(f"\n🔍 Start scrapowania KAS — "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
 
    for office in IAS_OFFICES:
        print(f"📌 {office['city']} ({office['region']})...")
        listings = scrape_ias(session, office)
        all_listings.extend(listings)
        time.sleep(1)
 
    # Globalna deduplication po tytule (między regionami)
    seen_global = set()
    unique_listings = []
    for item in all_listings:
        key = re.sub(r"\s+", " ", item["title"].lower().strip())
        if key not in seen_global:
            seen_global.add(key)
            unique_listings.append(item)
 
    by_region = {}
    by_category = {}
    for item in unique_listings:
        by_region[item["region"]] = by_region.get(item["region"], 0) + 1
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
 
    result = {
        "scraped_at":  datetime.now().isoformat(),
        "total":       len(unique_listings),
        "listings":    unique_listings,
        "by_region":   by_region,
        "by_category": by_category,
    }
 
    print(f"\n📊 Łącznie znaleziono: {len(unique_listings)} unikalnych ogłoszeń")
    return result
 
 
if __name__ == "__main__":
    data = run_scraper()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 Zapisano do data.json")
