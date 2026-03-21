"""
Scraper licytacji KAS v5
- Obsługuje dwa systemy: gov.pl i kas.gov.pl
- Dla kas.gov.pl: automatycznie odkrywa wszystkie Urzędy Skarbowe w regionie
  i scrapuje każdy z nich osobno
- Pełna paginacja + globalna deduplication
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
 
# Dla kas.gov.pl scraper sam odkrywa wszystkie US z menu
# Dla gov.pl strona IAS już agreguje wszystko
IAS_OFFICES = [
    {
        "region": "Dolnośląskie", "city": "Wrocław",
        "url": "https://www.gov.pl/web/ias-wroclaw/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
    },
    {
        "region": "Kujawsko-Pomorskie", "city": "Bydgoszcz",
        "url": "https://www.kujawsko-pomorskie.kas.gov.pl/izba-administracji-skarbowej-w-bydgoszczy/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.kujawsko-pomorskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Lubelskie", "city": "Lublin",
        "url": "https://www.lubelskie.kas.gov.pl/izba-administracji-skarbowej-w-lublinie/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.lubelskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Lubuskie", "city": "Zielona Góra",
        "url": "https://www.lubuskie.kas.gov.pl/izba-administracji-skarbowej-w-zielonej-gorze/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.lubuskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Łódzkie", "city": "Łódź",
        "url": "https://www.gov.pl/web/ias-lodz/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
    },
    {
        "region": "Małopolskie", "city": "Kraków",
        "url": "https://www.malopolskie.kas.gov.pl/izba-administracji-skarbowej-w-krakowie/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.malopolskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Mazowieckie", "city": "Warszawa",
        "url": "https://www.mazowieckie.kas.gov.pl/izba-administracji-skarbowej-w-warszawie/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.mazowieckie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Opolskie", "city": "Opole",
        "url": "https://www.opolskie.kas.gov.pl/izba-administracji-skarbowej-w-opolu/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.opolskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Podkarpackie", "city": "Rzeszów",
        "url": "https://www.gov.pl/web/ias-rzeszow/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
    },
    {
        "region": "Podlaskie", "city": "Białystok",
        "url": "https://www.gov.pl/web/ias-bialystok/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
    },
    {
        "region": "Pomorskie", "city": "Gdańsk",
        "url": "https://www.pomorskie.kas.gov.pl/izba-administracji-skarbowej-w-gdansku/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.pomorskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Śląskie", "city": "Katowice",
        "url": "https://www.gov.pl/web/ias-katowice/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
    },
    {
        "region": "Świętokrzyskie", "city": "Kielce",
        "url": "https://www.gov.pl/web/ias-kielce/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
    },
    {
        "region": "Warmińsko-Mazurskie", "city": "Olsztyn",
        "url": "https://www.warminsko-mazurskie.kas.gov.pl/izba-administracji-skarbowej-w-olsztynie/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.warminsko-mazurskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Wielkopolskie", "city": "Poznań",
        "url": "https://www.wielkopolskie.kas.gov.pl/izba-administracji-skarbowej-w-poznaniu/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.wielkopolskie.kas.gov.pl", "system": "kaspl",
    },
    {
        "region": "Zachodniopomorskie", "city": "Szczecin",
        "url": "https://www.zachodniopomorskie.kas.gov.pl/izba-administracji-skarbowej-w-szczecinie/ogloszenia/obwieszczenia-o-licytacjach",
        "base_url": "https://www.zachodniopomorskie.kas.gov.pl", "system": "kaspl",
    },
]
 
CONTENT_KEYWORDS = [
    "licytacj", "sprzedaż", "sprzedaz", "ruchom", "nieruchom",
    "obwieszczen", "zawiadomien", "przetarg",
    "samochód", "samochod", "pojazd", "mieszkan", "działk",
    "grunt", "lokal", "maszyn", "naczepa", "przyczepa",
    "motocykl", "ciągnik", "traktor", "autobus", "ciężar",
    "osobowy", "budynek", "dom ", "opel", "ford", "bmw", "audi",
    "toyota", "honda", "fiat", "renault", "peugeot", "skoda",
    "mercedes", "volkswagen", "hyundai", "kia", "mazda",
    "nissan", "volvo", "dacia", "kawasaki", "yamaha", "suzuki",
]
 
NAV_SKIP = [
    "Przejdź do", "Mapa strony", "Wersja kontrastowa",
    "Izba Administracji", "Urząd Celno", "Wiadomości",
    "Aktualności", "Organizacja", "Kierownictwo", "Regulamin",
    "Zamówienia", "Kariera", "Kontakt", "Dostępność",
    "Bip.gov", "Gov.pl", "YouTube", "Twitter", "RSS",
    "Serwis Służby", "Elektronicz", "Strona główna",
    "Rada Ministrów", "Ministerst", "Kancelaria",
    "Załatwianie", "Informacje podatkowe", "Działalność",
    "Ogłoszenia", "Redakcja", "Depozyty", "Nabór",
    "Zbędne", "Szkolenia", "Oferty likwidacyjne",
]
 
 
def is_content(title):
    return any(kw in title.lower() for kw in CONTENT_KEYWORDS)
 
 
def is_nav(title):
    return any(title.startswith(s) for s in NAV_SKIP)
 
 
def clean_title(raw):
    t = raw.strip().rstrip("»›> ").strip()
    for prefix in ["Czytaj więcej o ", "Czytaj wiecej o ", "czytaj więcej o "]:
        if t.lower().startswith(prefix.lower()):
            extracted = t[len(prefix):].strip()
            return extracted if len(extracted) > 10 else None
    return t if len(t) > 10 else None
 
 
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
    if "wolnej ręki" in tl or "wolnej reki" in tl:
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
 
 
def discover_us_urls(session, office):
    """
    Dla kas.gov.pl: pobiera stronę IAS i wyciąga linki do wszystkich
    Urzędów Skarbowych z menu nawigacyjnego.
    Zwraca listę URLi stron licytacji każdego US.
    """
    try:
        resp = session.get(office["url"], headers=HEADERS, timeout=25)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
    except Exception as e:
        print(f"  ❌ Błąd odkrywania US dla {office['city']}: {e}")
        return []
 
    soup = BeautifulSoup(resp.text, "html.parser")
    base = office["base_url"]
    us_urls = []
    seen = set()
 
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        text = a_tag.get_text(strip=True)
 
        # Szukamy linków do urzędów skarbowych w menu
        # Typowy pattern: /urzad-skarbowy-X lub /pierwszy-urzad-skarbowy-X
        if not re.search(r"urzad-skarbowy|urzad skarbowy", href, re.IGNORECASE):
            continue
 
        # Pomiń linki do urzędów celno-skarbowych
        if "celno" in href.lower():
            continue
 
        # Zbuduj URL do strony licytacji tego US
        if href.startswith("http"):
            us_base = href.rstrip("/")
        elif href.startswith("/"):
            us_base = base + href.rstrip("/")
        else:
            continue
 
        # Usuń zagnieżdżone ścieżki — chcemy tylko korzeń US
        # np. /urzad-skarbowy-w-kaliszu (nie /urzad-skarbowy-w-kaliszu/kontakt)
        parts = us_base.replace(base, "").split("/")
        parts = [p for p in parts if p]
        if len(parts) > 1:
            us_base = base + "/" + parts[0]
 
        licytacje_url = us_base + "/ogloszenia/obwieszczenia-o-licytacjach"
 
        if licytacje_url not in seen:
            seen.add(licytacje_url)
            us_name = text.strip() if text else parts[0] if parts else "?"
            us_urls.append({
                "url":  licytacje_url,
                "name": us_name,
            })
 
    print(f"  🗺️  Odkryto {len(us_urls)} Urzędów Skarbowych w {office['region']}")
    return us_urls
 
 
def fetch_page(session, url):
    try:
        resp = session.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception:
        return None
 
 
def parse_kaspl_page(html, base_url):
    """Parsuje jedną stronę kas.gov.pl — zwraca listę (title, url)."""
    soup = BeautifulSoup(html, "html.parser")
    content = (
        soup.find(id="main-content")
        or soup.find(class_=re.compile(r"portlet-content|journal-content|asset-publisher"))
        or soup.body
    )
    results = []
    for a_tag in content.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        raw = a_tag.get_text(strip=True)
        if not raw or len(raw) < 10:
            continue
        if is_nav(raw):
            continue
        title = clean_title(raw)
        if not title or not is_content(title):
            continue
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            full_url = base_url + href
        else:
            continue
        results.append((title, full_url))
    return results, soup
 
 
def parse_govpl_page(html, base_url):
    """Parsuje jedną stronę gov.pl — zwraca listę (title, url)."""
    soup = BeautifulSoup(html, "html.parser")
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"main|content"))
        or soup.body
    )
    results = []
    for a_tag in main.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        title = a_tag.get_text(strip=True).rstrip("»›> ").strip()
        if not title or len(title) < 10:
            continue
        if is_nav(title):
            continue
        if not is_content(title):
            continue
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            full_url = base_url + href
        else:
            continue
        results.append((title, full_url))
    return results, soup
 
 
def get_next_page_kaspl(soup, base_url, page):
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True).lower().strip()
        href = a_tag.get("href", "")
        if text in ["»", "następna", "next", str(page + 1)]:
            if href.startswith("http"):
                return href
            elif href.startswith("/"):
                return base_url + href
    return None
 
 
def get_next_page_govpl(soup, base_url, current_url, page):
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True).lower()
        href = a_tag.get("href", "")
        if text in ["następna", "next", "›", "»"]:
            if href.startswith("http"):
                return href
            return base_url + href
    return None
 
 
def scrape_url(session, url, base_url, system, region, city, seen_urls, seen_titles):
    """
    Scrapuje jeden URL (IAS lub US) ze wszystkimi stronami.
    Zwraca listę nowych ogłoszeń.
    """
    listings = []
    current_url = url
    page = 1
    empty_streak = 0
 
    while current_url and page <= 30:
        html = fetch_page(session, current_url)
        if not html:
            break
 
        if system == "govpl":
            raw, soup = parse_govpl_page(html, base_url)
        else:
            raw, soup = parse_kaspl_page(html, base_url)
 
        found = 0
        for title, full_url in raw:
            title_key = re.sub(r"\s+", " ", title.lower().strip())
            if full_url in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(full_url)
            seen_titles.add(title_key)
            listings.append({
                "region":     region,
                "city":       city,
                "title":      title,
                "url":        full_url,
                "category":   detect_category(title),
                "type":       detect_type(title),
                "date":       extract_date(title),
                "source_url": current_url,
            })
            found += 1
 
        if found == 0:
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0
 
        if system == "govpl":
            next_url = get_next_page_govpl(soup, base_url, current_url, page)
            if next_url == current_url:
                break
        else:
            next_url = get_next_page_kaspl(soup, base_url, page)
 
        current_url = next_url
        page += 1
        if current_url:
            time.sleep(0.4)
 
    return listings
 
 
def scrape_ias(session, office, seen_urls, seen_titles):
    """Scrapuje IAS i wszystkie US w regionie."""
    all_listings = []
 
    if office["system"] == "govpl":
        # gov.pl już agreguje wszystkie US — scrapujemy tylko IAS
        print(f"  📥 Scrapuję IAS ({office['system']})...")
        listings = scrape_url(
            session, office["url"], office["base_url"],
            office["system"], office["region"], office["city"],
            seen_urls, seen_titles
        )
        all_listings.extend(listings)
        print(f"  ✅ IAS: {len(listings)} nowych ogłoszeń")
 
    else:
        # kas.gov.pl: scrapuj IAS + odkryj i scrapuj każdy US osobno
        print(f"  📥 Scrapuję IAS ({office['system']})...")
        ias_listings = scrape_url(
            session, office["url"], office["base_url"],
            office["system"], office["region"], office["city"],
            seen_urls, seen_titles
        )
        all_listings.extend(ias_listings)
        print(f"  ✅ IAS: {len(ias_listings)} nowych ogłoszeń")
 
        # Odkryj wszystkie US
        us_list = discover_us_urls(session, office)
        time.sleep(0.5)
 
        for i, us in enumerate(us_list, 1):
            print(f"  📋 US {i}/{len(us_list)}: {us['name']}")
            us_listings = scrape_url(
                session, us["url"], office["base_url"],
                office["system"], office["region"], us["name"],
                seen_urls, seen_titles
            )
            all_listings.extend(us_listings)
            if us_listings:
                print(f"     → {len(us_listings)} nowych ogłoszeń")
            time.sleep(0.5)
 
    return all_listings
 
 
def run_scraper():
    session = requests.Session()
    all_listings = []
    # Globalne zbiory do deduplication — wspólne dla wszystkich regionów
    seen_urls   = set()
    seen_titles = set()
 
    print(f"\n🔍 Start scrapowania KAS — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
 
    for office in IAS_OFFICES:
        print(f"\n📌 {office['city']} ({office['region']}) [{office['system']}]")
        listings = scrape_ias(session, office, seen_urls, seen_titles)
        all_listings.extend(listings)
        print(f"  🏁 Region łącznie: {len(listings)} ogłoszeń")
        time.sleep(1)
 
    by_region   = {}
    by_category = {}
    for item in all_listings:
        by_region[item["region"]]     = by_region.get(item["region"], 0) + 1
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
 
    result = {
        "scraped_at":  datetime.now().isoformat(),
        "total":       len(all_listings),
        "listings":    all_listings,
        "by_region":   by_region,
        "by_category": by_category,
    }
 
    print(f"\n📊 GOTOWE — {len(all_listings)} unikalnych ogłoszeń z całej Polski")
    return result
 
 
if __name__ == "__main__":
    data = run_scraper()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 Zapisano do data.json")
