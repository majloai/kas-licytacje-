"""
Scraper licytacji KAS v7 - kompletny
- gov.pl: paginacja ?page=N&size=10, parsowanie artykułów
- kas.gov.pl: odkrywa wszystkie US z menu, wchodzi na każdy osobno
- Globalna deduplication, pełna paginacja
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
    {
        "region": "Dolnośląskie", "city": "Wrocław",
        "url": "https://www.gov.pl/web/ias-wroclaw/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
        "ias_slug": "ias-wroclaw",
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
        "ias_slug": "ias-lodz",
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
        "ias_slug": "ias-rzeszow",
    },
    {
        "region": "Podlaskie", "city": "Białystok",
        "url": "https://www.gov.pl/web/ias-bialystok/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
        "ias_slug": "ias-bialystok",
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
        "ias_slug": "ias-katowice",
    },
    {
        "region": "Świętokrzyskie", "city": "Kielce",
        "url": "https://www.gov.pl/web/ias-kielce/obwieszczenia-o-licytacjach",
        "base_url": "https://www.gov.pl", "system": "govpl",
        "ias_slug": "ias-kielce",
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
    "obwieszczen", "zawiadomien", "przetarg", "opis i oszacow",
    "samochód", "samochod", "pojazd", "mieszkan", "działk",
    "grunt", "lokal", "maszyn", "naczepa", "przyczepa",
    "motocykl", "ciągnik", "traktor", "autobus", "ciężar",
    "osobowy", "budynek", "dom ", "opel", "ford", "bmw", "audi",
    "toyota", "honda", "fiat", "renault", "peugeot", "skoda",
    "mercedes", "volkswagen", "hyundai", "kia", "mazda",
    "nissan", "volvo", "dacia", "kawasaki", "yamaha", "suzuki",
]
 
NAV_SKIP_STARTS = [
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
    "Umów wizytę", "Zgłoś", "Przydatne", "Zasady",
    "Skargi", "Stan spraw", "Rejestr", "Logowanie",
    "Usługi dla", "Profil zaufany", "Baza wiedzy",
    "Co robimy", "Załatw sprawę", "Jak załatwić",
    "O izbie", "Informacje o izbie", "Struktura",
]
 
 
def is_content(title):
    return any(kw in title.lower() for kw in CONTENT_KEYWORDS)
 
 
def is_nav(title):
    t = title.strip()
    return any(t.startswith(s) for s in NAV_SKIP_STARTS) or len(t) < 15
 
 
def clean_title_kaspl(raw):
    """Wyciąga tytuł z 'Czytaj więcej o TYTUŁ»' lub zwraca jak jest."""
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
                              "ciężar", "autobus", "bus ", "van ", "naczepa",
                              "przyczepa"]):
        return "Pojazdy"
    return "Inne ruchomości"
 
 
def detect_type(title):
    tl = title.lower()
    if ("pierwsz" in tl or " i licytacj" in tl) and "licytacj" in tl:
        return "I licytacja"
    if ("drug" in tl or " ii licytacj" in tl) and "licytacj" in tl:
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
 
 
def fetch_html(session, url):
    try:
        resp = session.get(url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"    ⚠️ Błąd HTTP: {e}")
        return None
 
 
# ══════════════════════════════════════════════════════════════════
# PARSER GOV.PL
# ══════════════════════════════════════════════════════════════════
 
def parse_govpl_articles(html, base_url, ias_slug):
    """
    Parsuje stronę gov.pl z listą artykułów.
    Zwraca listę (title, url) i obiekt soup.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
 
    # Artykuły na gov.pl są w liście <ul> lub <ol> z linkami
    # Każdy artykuł to <li><a href="/web/ias-X/slug">Tytuł</a></li>
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        title = a_tag.get_text(strip=True)
 
        if not title or len(title) < 15:
            continue
        if is_nav(title):
            continue
        if not is_content(title):
            continue
 
        # Linki artykułów na gov.pl mają format /web/ias-X/slug-artykulu
        # Muszą zawierać slug IAS i być dłuższe niż sama strona główna
        if ias_slug not in href:
            continue
        # Pomiń link do samej strony licytacji (menu)
        if href.endswith("/obwieszczenia-o-licytacjach"):
            continue
 
        title = title.rstrip("»›> ").strip()
 
        if href.startswith("http"):
            full_url = href
        elif href.startswith("/"):
            full_url = base_url + href
        else:
            continue
 
        results.append((title, full_url))
 
    return results, soup
 
 
def get_max_page_govpl(soup):
    """Wykrywa liczbę stron na gov.pl z linków paginacji."""
    max_page = 1
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        m = re.search(r"[?&]page=(\d+)", href)
        if m:
            p = int(m.group(1))
            if p > max_page:
                max_page = p
    return max_page
 
 
def scrape_govpl(session, base_url, start_url, ias_slug, region, city, seen_urls, seen_titles):
    """Scrapuje wszystkie strony gov.pl dla danej IAS."""
    listings = []
 
    # Pierwsza strona — wykryj max liczbę stron
    html = fetch_html(session, start_url)
    if not html:
        return listings
 
    raw, soup = parse_govpl_articles(html, base_url, ias_slug)
    max_page = get_max_page_govpl(soup)
    print(f"    📄 gov.pl — wykryto {max_page} stron")
 
    # Dodaj wyniki ze strony 1
    for title, url in raw:
        title_key = re.sub(r"\s+", " ", title.lower().strip())
        if url not in seen_urls and title_key not in seen_titles:
            seen_urls.add(url)
            seen_titles.add(title_key)
            listings.append({
                "region": region, "city": city, "title": title, "url": url,
                "category": detect_category(title), "type": detect_type(title),
                "date": extract_date(title), "source_url": start_url,
            })
 
    # Pobierz pozostałe strony
    for page in range(2, max_page + 1):
        page_url = f"{start_url}?page={page}&size=10"
        time.sleep(0.4)
        html = fetch_html(session, page_url)
        if not html:
            continue
        raw, _ = parse_govpl_articles(html, base_url, ias_slug)
        for title, url in raw:
            title_key = re.sub(r"\s+", " ", title.lower().strip())
            if url not in seen_urls and title_key not in seen_titles:
                seen_urls.add(url)
                seen_titles.add(title_key)
                listings.append({
                    "region": region, "city": city, "title": title, "url": url,
                    "category": detect_category(title), "type": detect_type(title),
                    "date": extract_date(title), "source_url": page_url,
                })
 
    return listings
 
 
# ══════════════════════════════════════════════════════════════════
# PARSER KAS.GOV.PL
# ══════════════════════════════════════════════════════════════════
 
def parse_kaspl_page(html, base_url):
    """Parsuje stronę kas.gov.pl. Zwraca (wyniki, soup)."""
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
        title = clean_title_kaspl(raw)
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
 
 
def get_next_kaspl(soup, base_url, page):
    """Zwraca URL następnej strony lub None."""
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True).lower().strip()
        href = a_tag.get("href", "")
        if text in ["»", "następna", "next", str(page + 1)]:
            if href.startswith("http"):
                return href
            elif href.startswith("/"):
                return base_url + href
    return None
 
 
def scrape_kaspl_url(session, start_url, base_url, region, city, seen_urls, seen_titles):
    """Scrapuje jeden URL kas.gov.pl ze wszystkimi stronami."""
    listings = []
    current_url = start_url
    page = 1
    empty_streak = 0
 
    while current_url and page <= 30:
        html = fetch_html(session, current_url)
        if not html:
            break
        raw, soup = parse_kaspl_page(html, base_url)
 
        found = 0
        for title, url in raw:
            title_key = re.sub(r"\s+", " ", title.lower().strip())
            if url in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(url)
            seen_titles.add(title_key)
            listings.append({
                "region": region, "city": city, "title": title, "url": url,
                "category": detect_category(title), "type": detect_type(title),
                "date": extract_date(title), "source_url": current_url,
            })
            found += 1
 
        if found == 0:
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0
 
        next_url = get_next_kaspl(soup, base_url, page)
        current_url = next_url
        page += 1
        if current_url:
            time.sleep(0.4)
 
    return listings
 
 
# ══════════════════════════════════════════════════════════════════
# ODKRYWANIE URZĘDÓW SKARBOWYCH (KAS.GOV.PL)
# ══════════════════════════════════════════════════════════════════
 
def discover_all_us(session, ias_url, base_url):
    """
    Pobiera stronę IAS i wyciąga linki do WSZYSTKICH Urzędów Skarbowych.
    Następnie dla każdego US wchodzi na jego stronę i szuka linku do licytacji.
    Zwraca listę dict: {name, licytacje_url}
    """
    html = fetch_html(session, ias_url)
    if not html:
        return []
 
    soup = BeautifulSoup(html, "html.parser")
    us_homepages = {}  # url -> name
 
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        text = a_tag.get_text(strip=True)
 
        if not re.search(r"urzad.skarbowy", href, re.IGNORECASE):
            continue
        if "celno" in href.lower():
            continue
 
        # Zbuduj URL homepage US
        if href.startswith("http"):
            us_url = href.rstrip("/")
        elif href.startswith("/"):
            us_url = base_url + href.rstrip("/")
        else:
            continue
 
        # Chcemy tylko homepage US — usuń zagnieżdżone ścieżki
        # Przykład: https://base.kas.gov.pl/urzad-skarbowy-w-x
        path_after_base = us_url.replace(base_url, "").strip("/")
        segments = [s for s in path_after_base.split("/") if s]
 
        if not segments:
            continue
        # Bierzemy tylko 1-segmentowe (homepage) lub pomijamy głębsze podstrony
        if len(segments) > 1:
            continue
 
        us_homepage = base_url + "/" + segments[0]
        if us_homepage not in us_homepages:
            us_homepages[us_homepage] = text.strip() or segments[0]
 
    results = []
    for us_homepage, us_name in us_homepages.items():
        # Wejdź na stronę US i znajdź link do licytacji
        time.sleep(0.3)
        us_html = fetch_html(session, us_homepage)
        if not us_html:
            continue
 
        us_soup = BeautifulSoup(us_html, "html.parser")
        licytacje_url = None
 
        # Szukaj linku do licytacji w nawigacji i treści
        for a_tag in us_soup.find_all("a", href=True):
            href = a_tag.get("href", "")
            text = a_tag.get_text(strip=True).lower()
            if "licytacj" in href.lower() or "licytacj" in text or "obwieszczen" in href.lower():
                if href.startswith("http"):
                    licytacje_url = href
                elif href.startswith("/"):
                    licytacje_url = base_url + href
                if licytacje_url:
                    break
 
        # Fallback — standardowa ścieżka
        if not licytacje_url:
            licytacje_url = us_homepage + "/ogloszenia/obwieszczenia-o-licytacjach"
 
        results.append({"name": us_name, "url": licytacje_url})
 
    return results
 
 
# ══════════════════════════════════════════════════════════════════
# GŁÓWNA FUNKCJA
# ══════════════════════════════════════════════════════════════════
 
def scrape_ias(session, office, seen_urls, seen_titles):
    all_listings = []
 
    if office["system"] == "govpl":
        # gov.pl: IAS agreguje wszystko, używamy paginacji ?page=N&size=10
        print(f"  📥 gov.pl — scrapuję {office['city']}...")
        listings = scrape_govpl(
            session, office["base_url"], office["url"],
            office["ias_slug"], office["region"], office["city"],
            seen_urls, seen_titles
        )
        all_listings.extend(listings)
        print(f"  ✅ {len(listings)} ogłoszeń")
 
    else:
        # kas.gov.pl: scrapuj IAS + odkryj i scrapuj każdy US
        print(f"  📥 Scrapuję stronę IAS ({office['city']})...")
        ias_listings = scrape_kaspl_url(
            session, office["url"], office["base_url"],
            office["region"], office["city"],
            seen_urls, seen_titles
        )
        all_listings.extend(ias_listings)
        print(f"  ✅ IAS: {len(ias_listings)} ogłoszeń")
 
        # Odkryj wszystkie US
        print(f"  🗺️  Odkrywam Urzędy Skarbowe w {office['region']}...")
        us_list = discover_all_us(session, office["url"], office["base_url"])
        print(f"  📋 Znaleziono {len(us_list)} US — scrapuję każdy...")
 
        for i, us in enumerate(us_list, 1):
            us_listings = scrape_kaspl_url(
                session, us["url"], office["base_url"],
                office["region"], us["name"],
                seen_urls, seen_titles
            )
            if us_listings:
                print(f"    [{i}/{len(us_list)}] {us['name']}: {len(us_listings)} ogłoszeń")
                all_listings.extend(us_listings)
            time.sleep(0.4)
 
    return all_listings
 
 
def run_scraper():
    session = requests.Session()
    all_listings = []
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
