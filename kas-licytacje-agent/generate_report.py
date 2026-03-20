"""
Generator raportu HTML dla licytacji KAS.
Rozbudowane filtry, podkategorie, województwa, inteligentna wyszukiwarka.
"""
 
import json
import sys
from datetime import datetime
 
SUBCATEGORY_MAP = {
    "Mieszkanie":         ["mieszkan", "lokal mieszk", "apartament"],
    "Dom":                ["dom jednorodzinn", "dom mieszk", "budynek mieszk"],
    "Działka":            ["działk", "grunt", "parcela", "teren"],
    "Lokal użytkowy":     ["lokal użytk", "lokal usług", "sklep", "biuro", "magazyn", "hala"],
    "Kamienica":          ["kamienica", "budynek wielomieszkaniowy"],
    "Garaż":              ["garaż", "miejsce parkingowe"],
    "Inna nieruchomość":  ["nieruchom"],
    "Samochód osobowy":   ["samochód osobowy", "auto osobow", "osobowy", "BMW", "Audi", "Ford",
                           "VW", "Volkswagen", "Opel", "Mercedes", "Toyota", "Renault", "Peugeot",
                           "Skoda", "Fiat", "Hyundai", "Kia", "Seat", "Honda", "Mazda",
                           "Citroen", "Nissan", "Volvo", "Suzuki", "Dacia"],
    "Samochód ciężarowy": ["samochód ciężar", "ciężarowy", "dostawczy"],
    "Bus / Van":          ["bus", "van", "minibus", "mikrobus", "Sprinter", "Transit", "Vivaro",
                           "Jumper", "Boxer", "Ducato", "Kangoo", "Partner", "Berlingo"],
    "Motocykl":           ["motocykl", "motorower", "skuter"],
    "Traktor / Ciągnik":  ["traktor", "ciągnik", "kombajn"],
    "Inne pojazdy":       ["pojazd", "samochód"],
    "Przyczepa":          ["przyczepa"],
    "Naczepa":            ["naczepa"],
    "Maszyna / Sprzęt":   ["maszyn", "sprzęt", "urządzen", "kopark", "ładowark", "wózek",
                           "dźwig", "narzędzi", "piłar", "agregat", "kompresor"],
    "Biżuteria":          ["biżuteria", "złoto", "srebro", "pierścień", "naszyjnik", "zegarek"],
    "Elektronika":        ["telefon", "komputer", "laptop", "tablet", "elektronik"],
    "Komórka lokatorska": ["komórka lokatorska", "piwnica", "schowek"],
    "Inne ruchomości":    [],
}
 
SUBCATEGORY_ORDER = {
    "Nieruchomości":   ["Mieszkanie","Dom","Działka","Lokal użytkowy","Kamienica","Garaż","Inna nieruchomość"],
    "Pojazdy":         ["Samochód osobowy","Samochód ciężarowy","Bus / Van","Motocykl","Traktor / Ciągnik","Inne pojazdy"],
    "Inne ruchomości": ["Przyczepa","Naczepa","Maszyna / Sprzęt","Biżuteria","Elektronika","Komórka lokatorska","Inne ruchomości"],
}
 
SALE_TYPES = ["I licytacja","II licytacja","Wolna ręka","Przetarg","Odwołanie","Licytacja","Ogłoszenie"]
 
REGIONS = [
    "Dolnośląskie","Kujawsko-Pomorskie","Lubelskie","Lubuskie","Łódzkie",
    "Małopolskie","Mazowieckie","Opolskie","Podkarpackie","Podlaskie",
    "Pomorskie","Śląskie","Świętokrzyskie","Warmińsko-Mazurskie",
    "Wielkopolskie","Zachodniopomorskie",
]
 
 
def detect_category(title):
    tl = title.lower()
    if any(k.lower() in tl for k in ["nieruchom","mieszkan","lokal","działk","grunt","budynek","kamienica","garaż"]):
        return "Nieruchomości"
    if any(k.lower() in tl for k in ["samochód","auto","pojazd","motorow","motocykl","ciągnik","BMW","Audi","Ford",
        "VW","Opel","Mercedes","Toyota","Renault","Peugeot","Skoda","Fiat","Hyundai","Kia","Seat","Honda","Mazda",
        "Nissan","Volvo","Suzuki","Dacia","Sprinter","Transit","Vivaro","Boxer","Ducato","Kangoo","Berlingo"]):
        return "Pojazdy"
    return "Inne ruchomości"
 
 
def detect_subcategory(title, category):
    tl = title.lower()
    for sub in SUBCATEGORY_ORDER.get(category, []):
        if any(k.lower() in tl for k in SUBCATEGORY_MAP.get(sub, [])):
            return sub
    if category == "Nieruchomości": return "Inna nieruchomość"
    if category == "Pojazdy":       return "Inne pojazdy"
    return "Inne ruchomości"
 
 
def detect_type(title):
    tl = title.lower()
    if "pierwsz" in tl and "licytacj" in tl: return "I licytacja"
    if "drug" in tl and "licytacj" in tl:    return "II licytacja"
    if "wolnej ręki" in tl:  return "Wolna ręka"
    if "przetarg" in tl:     return "Przetarg"
    if "odwołan" in tl:      return "Odwołanie"
    if "licytacj" in tl:     return "Licytacja"
    return "Ogłoszenie"
 
 
def generate_html(data):
    scraped_at = datetime.fromisoformat(data["scraped_at"]).strftime("%d.%m.%Y, %H:%M")
    listings = data["listings"]
 
    for item in listings:
        if "category" not in item:
            item["category"] = detect_category(item["title"])
        if "type" not in item:
            item["type"] = detect_type(item["title"])
        item["subcategory"] = detect_subcategory(item["title"], item["category"])
 
    total = len(listings)
 
    cat_colors = {
        "Nieruchomości":   ("#1e40af","#dbeafe"),
        "Pojazdy":         ("#065f46","#d1fae5"),
        "Inne ruchomości": ("#4b5563","#f3f4f6"),
    }
    type_colors = {
        "I licytacja":  ("#15803d","#dcfce7"),
        "II licytacja": ("#b45309","#fef9c3"),
        "Wolna ręka":   ("#6d28d9","#ede9fe"),
        "Przetarg":     ("#0369a1","#e0f2fe"),
        "Odwołanie":    ("#b91c1c","#fee2e2"),
        "Licytacja":    ("#15803d","#dcfce7"),
        "Ogłoszenie":   ("#374151","#f9fafb"),
    }
 
    def badge(text, fg, bg):
        return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
                f'border-radius:999px;font-size:0.72rem;font-weight:600;white-space:nowrap">{text}</span>')
 
    by_region = {}
    by_type   = {}
    by_cat    = {}
    for item in listings:
        by_region[item["region"]] = by_region.get(item["region"], 0) + 1
        by_type[item["type"]]     = by_type.get(item["type"], 0) + 1
        by_cat[item["category"]]  = by_cat.get(item["category"], 0) + 1
 
    rows_html = ""
    for item in listings:
        cat = item["category"]; sub = item["subcategory"]; typ = item["type"]
        fg_c, bg_c = cat_colors.get(cat, ("#374151","#f3f4f6"))
        fg_t, bg_t = type_colors.get(typ, ("#374151","#f9fafb"))
        date_cell = (f'<span style="color:#374151;font-weight:500">{item.get("date","")}</span>'
                     if item.get("date") else '<span style="color:#9ca3af">—</span>')
        search_data = f'{item["title"]} {cat} {sub} {typ} {item["region"]}'.lower()
        rows_html += f"""
        <tr class="row" data-region="{item['region']}" data-category="{cat}"
            data-subcategory="{sub}" data-type="{typ}" data-search="{search_data}">
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">
            <a href="{item['url']}" target="_blank"
               style="color:#1d4ed8;text-decoration:none;font-size:0.88rem;line-height:1.4">{item['title']}</a>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;white-space:nowrap">
            <span style="font-size:0.82rem;color:#374151">{item['region']}</span><br>
            <span style="font-size:0.75rem;color:#6b7280">{item['city']}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">
            {badge(cat,fg_c,bg_c)}<br>
            <span style="font-size:0.75rem;color:#6b7280;margin-top:3px;display:inline-block">{sub}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{badge(typ,fg_t,bg_t)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{date_cell}</td>
        </tr>"""
 
    region_stats = ""
    for region, count in sorted(by_region.items(), key=lambda x: -x[1]):
        pct = int(count/total*100) if total else 0
        region_stats += f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #f3f4f6">
          <span style="font-size:0.8rem;color:#374151">{region}</span>
          <div style="display:flex;align-items:center;gap:6px">
            <div style="width:60px;height:5px;background:#e5e7eb;border-radius:3px;overflow:hidden">
              <div style="width:{pct}%;height:100%;background:#2563eb;border-radius:3px"></div></div>
            <span style="font-size:0.78rem;font-weight:700;color:#1e40af;min-width:18px;text-align:right">{count}</span>
          </div></div>"""
 
    type_stats = ""
    for typ in SALE_TYPES:
        count = by_type.get(typ, 0)
        if count == 0: continue
        fg, bg = type_colors.get(typ, ("#374151","#f9fafb"))
        type_stats += f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #f3f4f6">
          <span>{badge(typ,fg,bg)}</span><span style="font-size:0.82rem;font-weight:700;color:{fg}">{count}</span></div>"""
 
    region_chips = "\n".join(
        f'<div class="chip teal" data-region="{r}">{r}</div>' for r in REGIONS
    )
 
    nierucho = by_cat.get("Nieruchomości", 0)
    pojazdy  = by_cat.get("Pojazdy", 0)
    inne     = by_cat.get("Inne ruchomości", 0)
 
    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Licytacje KAS — {datetime.now().strftime("%d.%m.%Y")}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh}}
#modal-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:1000;padding:16px}}
#modal{{background:white;border-radius:20px;padding:32px;max-width:720px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3);max-height:90vh;overflow-y:auto}}
#modal h2{{font-size:1.4rem;font-weight:800;color:#1e3a8a;margin-bottom:6px}}
#modal p{{font-size:.85rem;color:#6b7280;margin-bottom:22px}}
.modal-section{{margin-bottom:20px}}
.modal-section h3{{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#374151;margin-bottom:10px}}
.chip-group{{display:flex;flex-wrap:wrap;gap:8px}}
.chip{{padding:7px 14px;border-radius:999px;border:2px solid #e5e7eb;background:white;cursor:pointer;font-size:.82rem;font-weight:500;color:#374151;transition:all .15s;user-select:none}}
.chip:hover{{border-color:#93c5fd;background:#eff6ff}}
.chip.active{{border-color:#2563eb;background:#2563eb;color:white}}
.chip.green.active{{border-color:#16a34a;background:#16a34a}}
.chip.purple.active{{border-color:#7c3aed;background:#7c3aed}}
.chip.amber.active{{border-color:#d97706;background:#d97706}}
.chip.red.active{{border-color:#dc2626;background:#dc2626}}
.chip.teal.active{{border-color:#0f766e;background:#0f766e}}
#modal-apply{{width:100%;padding:13px;background:#1e40af;color:white;border:none;border-radius:12px;font-size:1rem;font-weight:700;cursor:pointer;margin-top:8px;transition:background .15s}}
#modal-apply:hover{{background:#1d4ed8}}
#modal-reset{{display:block;text-align:center;margin-top:10px;font-size:.82rem;color:#9ca3af;cursor:pointer;background:none;border:none;width:100%}}
.header{{background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 100%);color:white;padding:24px 32px}}
.header h1{{font-size:1.5rem;font-weight:800}}
.header p{{margin-top:4px;opacity:.8;font-size:.85rem}}
.stats-row{{display:flex;gap:14px;padding:18px 32px;flex-wrap:wrap}}
.stat-card{{background:white;border-radius:12px;padding:14px 18px;box-shadow:0 1px 4px rgba(0,0,0,.08);flex:1;min-width:110px}}
.stat-card .num{{font-size:1.8rem;font-weight:800;color:#1e40af}}
.stat-card .lbl{{font-size:.75rem;color:#6b7280;margin-top:2px}}
.main{{display:flex;gap:18px;padding:0 32px 32px}}
.sidebar{{width:220px;flex-shrink:0}}
.sidebar-card{{background:white;border-radius:12px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:14px}}
.sidebar-card h3{{font-size:.75rem;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}}
.content{{flex:1;min-width:0}}
.filters{{background:white;border-radius:12px;padding:14px 18px;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:14px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.search-wrap{{position:relative;flex:1;min-width:220px}}
.search-wrap input{{width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px 8px 36px;font-size:.85rem;outline:none;transition:border .2s}}
.search-wrap input:focus{{border-color:#2563eb}}
.search-icon{{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9ca3af;font-size:1rem;pointer-events:none}}
.search-hint{{font-size:.72rem;color:#9ca3af;margin-top:3px;padding-left:2px}}
#btn-filters{{padding:8px 16px;background:#1e40af;color:white;border:none;border-radius:8px;font-size:.85rem;font-weight:600;cursor:pointer;white-space:nowrap}}
#btn-filters:hover{{background:#1d4ed8}}
#active-filters{{display:flex;flex-wrap:wrap;gap:6px;width:100%}}
.active-chip{{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:999px;padding:3px 10px;font-size:.75rem;font-weight:600;display:flex;align-items:center;gap:4px}}
.active-chip span{{cursor:pointer;opacity:.6}}.active-chip span:hover{{opacity:1}}
.count-badge{{background:#eff6ff;color:#1d4ed8;border-radius:999px;padding:4px 12px;font-size:.8rem;font-weight:700;white-space:nowrap}}
.table-wrap{{background:white;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden}}
table{{width:100%;border-collapse:collapse}}
thead th{{background:#f8fafc;padding:10px 12px;text-align:left;font-size:.72rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #e5e7eb}}
tbody tr:hover{{background:#f0f7ff;cursor:pointer}}
.empty{{text-align:center;padding:48px;color:#9ca3af;font-size:.9rem}}
.footer{{text-align:center;padding:16px;font-size:.75rem;color:#9ca3af}}
@media(max-width:768px){{.main{{flex-direction:column;padding:0 16px 24px}}.sidebar{{width:100%}}.stats-row{{padding:14px 16px}}.header{{padding:18px 16px}}}}
</style></head><body>
 
<div id="modal-overlay">
  <div id="modal">
    <h2>🏛️ Licytacje KAS</h2>
    <p>Wybierz co Cię interesuje — możesz zaznaczyć wiele opcji. Możesz też pominąć i zobaczyć wszystkie.</p>
 
    <div class="modal-section">
      <h3>🏠 Nieruchomości</h3>
      <div class="chip-group">
        <div class="chip" data-sub="Mieszkanie">Mieszkanie</div>
        <div class="chip" data-sub="Dom">Dom</div>
        <div class="chip" data-sub="Działka">Działka</div>
        <div class="chip" data-sub="Lokal użytkowy">Lokal użytkowy</div>
        <div class="chip" data-sub="Kamienica">Kamienica</div>
        <div class="chip" data-sub="Garaż">Garaż</div>
        <div class="chip" data-sub="Inna nieruchomość">Inne</div>
      </div>
    </div>
 
    <div class="modal-section">
      <h3>🚗 Pojazdy</h3>
      <div class="chip-group">
        <div class="chip green" data-sub="Samochód osobowy">Samochód osobowy</div>
        <div class="chip green" data-sub="Samochód ciężarowy">Ciężarowy</div>
        <div class="chip green" data-sub="Bus / Van">Bus / Van</div>
        <div class="chip green" data-sub="Motocykl">Motocykl</div>
        <div class="chip green" data-sub="Traktor / Ciągnik">Traktor / Ciągnik</div>
        <div class="chip green" data-sub="Inne pojazdy">Inne pojazdy</div>
      </div>
    </div>
 
    <div class="modal-section">
      <h3>📦 Inne ruchomości</h3>
      <div class="chip-group">
        <div class="chip purple" data-sub="Przyczepa">Przyczepa</div>
        <div class="chip purple" data-sub="Naczepa">Naczepa</div>
        <div class="chip purple" data-sub="Maszyna / Sprzęt">Maszyna / Sprzęt</div>
        <div class="chip purple" data-sub="Biżuteria">Biżuteria</div>
        <div class="chip purple" data-sub="Elektronika">Elektronika</div>
        <div class="chip purple" data-sub="Komórka lokatorska">Komórka lokatorska</div>
        <div class="chip purple" data-sub="Inne ruchomości">Inne</div>
      </div>
    </div>
 
    <div class="modal-section">
      <h3>⚖️ Typ sprzedaży</h3>
      <div class="chip-group">
        <div class="chip" data-type="I licytacja">I licytacja</div>
        <div class="chip amber" data-type="II licytacja">II licytacja</div>
        <div class="chip purple" data-type="Wolna ręka">Wolna ręka</div>
        <div class="chip" data-type="Przetarg">Przetarg</div>
        <div class="chip red" data-type="Odwołanie">Odwołanie</div>
      </div>
    </div>
 
    <div class="modal-section">
      <h3>🗺️ Województwo</h3>
      <div class="chip-group">
        {region_chips}
      </div>
    </div>
 
    <button id="modal-apply">Pokaż ogłoszenia →</button>
    <button id="modal-reset">Pokaż wszystkie bez filtrów</button>
  </div>
</div>
 
<div id="app" style="display:none">
  <div class="header">
    <h1>🏛️ Licytacje KAS — Krajowa Administracja Skarbowa</h1>
    <p>Raport: {scraped_at} &nbsp;·&nbsp; 16 Izb Administracji Skarbowej &nbsp;·&nbsp; Cała Polska</p>
  </div>
  <div class="stats-row">
    <div class="stat-card"><div class="num">{total}</div><div class="lbl">Wszystkich ogłoszeń</div></div>
    <div class="stat-card"><div class="num">{nierucho}</div><div class="lbl">Nieruchomości</div></div>
    <div class="stat-card"><div class="num">{pojazdy}</div><div class="lbl">Pojazdy</div></div>
    <div class="stat-card"><div class="num">{inne}</div><div class="lbl">Inne ruchomości</div></div>
    <div class="stat-card"><div class="num">16</div><div class="lbl">Izb Skarbowych</div></div>
  </div>
  <div class="main">
    <div class="sidebar">
      <div class="sidebar-card"><h3>📊 Wg regionu</h3>{region_stats}</div>
      <div class="sidebar-card"><h3>⚖️ Typ sprzedaży</h3>{type_stats}</div>
      <div class="sidebar-card" style="background:#eff6ff;border:1px solid #bfdbfe">
        <h3 style="color:#1e40af">ℹ️ Portal eLicytacje KAS</h3>
        <p style="font-size:.77rem;color:#1e40af;line-height:1.5">Planowany start: <strong>30 czerwca 2026</strong>. Obecnie dane z 16 regionalnych IAS.</p>
      </div>
    </div>
    <div class="content">
      <div class="filters">
        <div style="width:100%;display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap">
          <div class="search-wrap">
            <span class="search-icon">🔍</span>
            <input type="text" id="search" placeholder="Szukaj: BMW, mieszkanie Kraków, naczepa...">
            <div class="search-hint">Wpisz kilka słów — pokaże najlepiej pasujące wyniki</div>
          </div>
          <button id="btn-filters">⚙️ Zmień filtry</button>
          <span class="count-badge" id="count">{total} ogłoszeń</span>
        </div>
        <div id="active-filters"></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Tytuł ogłoszenia</th><th>Region / IAS</th>
            <th>Kategoria / Podkategoria</th><th>Typ sprzedaży</th><th>Data</th>
          </tr></thead>
          <tbody id="tbody">
            {rows_html}
            <tr id="empty-row" style="display:none">
              <td colspan="5" class="empty">Brak wyników.<br>
                <button onclick="resetAll()" style="margin-top:12px;padding:8px 20px;background:#2563eb;color:white;border:none;border-radius:8px;cursor:pointer;font-size:.85rem">Wyczyść filtry</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="footer">Dane z BIP Izb Administracji Skarbowej &nbsp;·&nbsp; Aktualizacja codziennie o 8:00 &nbsp;·&nbsp; <a href="https://www.kas.gov.pl" target="_blank" style="color:#9ca3af">kas.gov.pl</a></div>
</div>
 
<script>
let activeSubs=new Set(),activeTypes=new Set(),activeRegions=new Set();
 
document.querySelectorAll(".chip[data-sub]").forEach(c=>c.addEventListener("click",()=>c.classList.toggle("active")));
document.querySelectorAll(".chip[data-type]").forEach(c=>c.addEventListener("click",()=>c.classList.toggle("active")));
document.querySelectorAll(".chip[data-region]").forEach(c=>c.addEventListener("click",()=>c.classList.toggle("active")));
 
document.getElementById("modal-apply").addEventListener("click",()=>{{
  activeSubs=new Set([...document.querySelectorAll(".chip[data-sub].active")].map(c=>c.dataset.sub));
  activeTypes=new Set([...document.querySelectorAll(".chip[data-type].active")].map(c=>c.dataset.type));
  activeRegions=new Set([...document.querySelectorAll(".chip[data-region].active")].map(c=>c.dataset.region));
  document.getElementById("modal-overlay").style.display="none";
  document.getElementById("app").style.display="block";
  renderChips(); applyFilters();
}});
 
document.getElementById("modal-reset").addEventListener("click",()=>{{
  activeSubs.clear(); activeTypes.clear(); activeRegions.clear();
  document.getElementById("modal-overlay").style.display="none";
  document.getElementById("app").style.display="block";
  renderChips(); applyFilters();
}});
 
document.getElementById("btn-filters").addEventListener("click",()=>{{
  document.getElementById("modal-overlay").style.display="flex";
  document.getElementById("app").style.display="none";
  document.querySelectorAll(".chip[data-sub]").forEach(c=>c.classList.toggle("active",activeSubs.has(c.dataset.sub)));
  document.querySelectorAll(".chip[data-type]").forEach(c=>c.classList.toggle("active",activeTypes.has(c.dataset.type)));
  document.querySelectorAll(".chip[data-region]").forEach(c=>c.classList.toggle("active",activeRegions.has(c.dataset.region)));
}});
 
function renderChips(){{
  const w=document.getElementById("active-filters"); w.innerHTML="";
  activeSubs.forEach(s=>{{const d=document.createElement("div");d.className="active-chip";d.innerHTML=`${{s}} <span onclick="removeSub('${{s}}')" title="Usuń">✕</span>`;w.appendChild(d);}});
  activeTypes.forEach(t=>{{const d=document.createElement("div");d.className="active-chip";d.innerHTML=`${{t}} <span onclick="removeType('${{t}}')" title="Usuń">✕</span>`;w.appendChild(d);}});
  activeRegions.forEach(r=>{{const d=document.createElement("div");d.className="active-chip";d.innerHTML=`${{r}} <span onclick="removeRegion('${{r}}')" title="Usuń">✕</span>`;w.appendChild(d);}});
}}
 
function removeSub(s){{activeSubs.delete(s);renderChips();applyFilters();}}
function removeType(t){{activeTypes.delete(t);renderChips();applyFilters();}}
function removeRegion(r){{activeRegions.delete(r);renderChips();applyFilters();}}
function resetAll(){{activeSubs.clear();activeTypes.clear();activeRegions.clear();document.getElementById("search").value="";renderChips();applyFilters();}}
 
function score(row,kws){{
  if(!kws.length)return 1;
  const t=row.dataset.search; let s=0;
  kws.forEach(k=>{{if(t.includes(k))s++;if(t.substring(0,120).includes(k))s++;}});
  return s;
}}
 
function applyFilters(){{
  const raw=document.getElementById("search").value.toLowerCase().trim();
  const kws=raw?raw.split(/\s+/).filter(k=>k.length>1):[];
  const rows=[...document.querySelectorAll("tr.row")];
  let scored=[];
  rows.forEach(row=>{{
    const mS=activeSubs.size===0||activeSubs.has(row.dataset.subcategory);
    const mT=activeTypes.size===0||activeTypes.has(row.dataset.type);
    const mR=activeRegions.size===0||activeRegions.has(row.dataset.region);
    const sc=score(row,kws);
    const mQ=kws.length===0||sc>0;
    const show=mS&&mT&&mR&&mQ;
    row.style.display=show?"":"none";
    if(show)scored.push({{row,sc}});
  }});
  if(kws.length>0){{const tb=document.getElementById("tbody");scored.sort((a,b)=>b.sc-a.sc);scored.forEach(({{row}})=>tb.appendChild(row));}}
  document.getElementById("count").textContent=scored.length+" ogłoszeń";
  document.getElementById("empty-row").style.display=scored.length===0?"":"none";
}}
 
document.getElementById("search").addEventListener("input",applyFilters);
</script></body></html>"""
    return html
 
 
if __name__ == "__main__":
    input_file  = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "docs/index.html"
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)
    html = generate_html(data)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Raport HTML zapisany: {output_file}  ({data['total']} ogłoszeń)")
