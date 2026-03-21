"""
Scraper licytacji KAS - obsługuje dwa systemy:
1. gov.pl        - nowy portal rządowy (czyste linki z tytułami)
2. kas.gov.pl    - stary system Liferay (linki "Czytaj więcej »")
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
 
# Każde województwo ma DWIE adresy — gov.pl i kas.gov.pl
# system: "govpl" lub "kaspl"
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
    "obwieszczen", "zawiadomien", "przetarg", "informacja roczna",
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
 
 
# ── Parser dla gov.pl ─────────────────────────────────────────────────────
def parse_govpl(soup, office):
    """
    gov.pl ma listę artykułów w strukturze:
    <article> lub <div class="article-..."> z bezpośrednim linkiem tytułu.
    """
    listings = []
 
    # Szukaj linków w głównej treści
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"main|content"))
        or soup.find(class_=re.compile(r"content|article|listing"))
        or soup.body
    )
 
    for a_tag in main.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        title = a_tag.get_text(strip=True)
 
        if not title or len(title) < 10:
            continue
        if is_nav(title):
            continue
        if not is_content(title):
            continue
 
        # Na gov.pl tytuły są bezpośrednie — nie ma "Czytaj więcej"
        title = title.rstrip("»›> ").strip()
 
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            full_url = office["base_url"] + href
        else:
            continue
 
        listings.append({
            "title": title,
            "url":   full_url,
        })
 
    return listings
 
 
# ── Parser dla kas.gov.pl ─────────────────────────────────────────────────
def parse_kaspl(soup, office):
    """
    kas.gov.pl (Liferay) ma linki "Czytaj więcej o TYTUŁ »"
    lub bezpośrednie linki z tytułem.
    """
    listings = []
 
    content_area = (
        soup.find(id="main-content")
        or soup.find(class_=re.compile(r"portlet-content|journal-content|asset-publisher"))
        or soup.body
    )
 
    for a_tag in content_area.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        raw = a_tag.get_text(strip=True)
 
        if not raw or len(raw) < 10:
            continue
        if is_nav(raw):
            continue
 
        title = clean_title(raw)
        if not title or len(title) < 10:
            continue
        if not is_content(title):
            continue
 
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            full_url = office["base_url"] + href
        else:
            full_url = office["base_url"] + "/" + href
 
        listings.append({
            "title": title,
            "url":   full_url,
        })
 
    return listings
 
 
# ── Paginacja gov.pl ──────────────────────────────────────────────────────
def get_next_govpl(soup, base_url, current_url, page):
    """gov.pl używa ?page=N lub linków 'Następna'."""
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True).lower()
        href = a_tag.get("href", "")
        if text in ["następna", "next", "›", "»"]:
            if href.startswith("http"):
                return href
            return base_url + href
 
    # Spróbuj ?page=N
    if "?" not in current_url:
        next_url = current_url + f"?page={page + 1}"
    else:
        next_url = re.sub(r"page=\d+", f"page={page + 1}", current_url)
        if f"page={page + 1}" not in next_url:
            next_url = current_url + f"&page={page + 1}"
    return next_url
 
 
# ── Paginacja kas.gov.pl ──────────────────────────────────────────────────
def get_next_kaspl(soup, base_url, page):
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True).lower().strip()
        href = a_tag.get("href", "")
        if text in ["»", "następna", "next", str(page + 1)]:
            if href.startswith("http"):
                return href
            elif href.startswith("/"):
                return base_url + href
    return None
 
 
# ── Główna funkcja scrapowania ─────────────────────────────────────────────
def scrape_ias(session, office):
    all_listings = []
    seen_urls   = set()
    seen_titles = set()
    current_url = office["url"]
    page = 1
    empty_pages = 0
 
    while current_url and page <= 25:
        print(f"    📄 Strona {page}: {current_url}")
        try:
            resp = session.get(current_url, headers=HEADERS, timeout=25)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
        except requests.RequestException as e:
            print(f"  ❌ Błąd {office['city']} str.{page}: {e}")
            break
 
        soup = BeautifulSoup(resp.text, "html.parser")
 
        if office["system"] == "govpl":
            raw_listings = parse_govpl(soup, office)
        else:
            raw_listings = parse_kaspl(soup, office)
 
        found = 0
        for item in raw_listings:
            title_key = re.sub(r"\s+", " ", item["title"].lower().strip())
            if item["url"] in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(item["url"])
            seen_titles.add(title_key)
 
            all_listings.append({
                "region":     office["region"],
                "city":       office["city"],
                "title":      item["title"],
                "url":        item["url"],
                "category":   detect_category(item["title"]),
                "type":       detect_type(item["title"]),
                "date":       extract_date(item["title"]),
                "source_url": current_url,
            })
            found += 1
 
        if found == 0:
            empty_pages += 1
            if empty_pages >= 2:
                break
        else:
            empty_pages = 0
 
        # Następna strona
        if office["system"] == "govpl":
            next_url = get_next_govpl(soup, office["base_url"], current_url, page)
            # Weryfikacja — jeśli ta sama strona, stop
            if next_url == current_url:
                break
        else:
            next_url = get_next_kaspl(soup, office["base_url"], page)
 
        current_url = next_url
        page += 1
        if current_url:
            time.sleep(0.5)
 
    print(f"  ✅ {office['city']} ({office['region']}): "
          f"{len(all_listings)} ogłoszeń ({page-1} stron, {office['system']})")
    return all_listings
 
 
def run_scraper():
    session = requests.Session()
    all_listings = []
 
    print(f"\n🔍 Start scrapowania KAS — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
 
    for office in IAS_OFFICES:
        print(f"📌 {office['city']} ({office['region']}) [{office['system']}]...")
        listings = scrape_ias(session, office)
        all_listings.extend(listings)
        time.sleep(1)
 
    # Globalna deduplication
    seen_global = set()
    unique = []
    for item in all_listings:
        key = re.sub(r"\s+", " ", item["title"].lower().strip())
        if key not in seen_global:
            seen_global.add(key)
            unique.append(item)
 
    by_region   = {}
    by_category = {}
    for item in unique:
        by_region[item["region"]]     = by_region.get(item["region"], 0) + 1
        by_category[item["category"]] = by_category.get(item["category"], 0) + 1
 
    result = {
        "scraped_at":  datetime.now().isoformat(),
        "total":       len(unique),
        "listings":    unique,
        "by_region":   by_region,
        "by_category": by_category,
    }
 
    print(f"\n📊 Łącznie: {len(unique)} unikalnych ogłoszeń")
    return result
 
 
if __name__ == "__main__":
    data = run_scraper()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("💾 Zapisano do data.json")
