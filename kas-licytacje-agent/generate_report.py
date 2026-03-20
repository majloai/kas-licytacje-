"""
Generator raportu HTML dla licytacji KAS.
Tworzy czytelny raport z filtrowaniem i wyszukiwaniem.
"""

import json
import sys
from datetime import datetime


def generate_html(data: dict) -> str:
    scraped_at = datetime.fromisoformat(data["scraped_at"]).strftime("%d.%m.%Y, %H:%M")
    listings = data["listings"]
    total = data["total"]
    by_category = data.get("by_category", {})
    by_region = data.get("by_region", {})

    # Kolory dla kategorii
    cat_colors = {
        "Nieruchomości":   ("#1e40af", "#dbeafe"),
        "Pojazdy":         ("#065f46", "#d1fae5"),
        "Maszyny/Sprzęt":  ("#92400e", "#fef3c7"),
        "Inne ruchomości": ("#4b5563", "#f3f4f6"),
    }

    type_colors = {
        "I licytacja":  ("#15803d", "#dcfce7"),
        "II licytacja": ("#b45309", "#fef9c3"),
        "Wolna ręka":   ("#6d28d9", "#ede9fe"),
        "Przetarg":     ("#0369a1", "#e0f2fe"),
        "Odwołanie":    ("#b91c1c", "#fee2e2"),
        "Licytacja":    ("#15803d", "#dcfce7"),
        "Ogłoszenie":   ("#374151", "#f9fafb"),
    }

    def badge(text, colors):
        fg, bg = colors
        return (
            f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:999px;font-size:0.72rem;font-weight:600;'
            f'white-space:nowrap">{text}</span>'
        )

    # Buduj wiersze tabeli
    rows_html = ""
    for item in listings:
        cat = item.get("category", "Inne ruchomości")
        typ = item.get("type", "Ogłoszenie")
        cat_color = cat_colors.get(cat, ("#374151", "#f9fafb"))
        typ_color = type_colors.get(typ, ("#374151", "#f9fafb"))
        date_str = item.get("date", "")
        date_cell = f'<span style="color:#374151;font-weight:500">{date_str}</span>' if date_str else '<span style="color:#9ca3af">—</span>'

        rows_html += f"""
        <tr class="row"
            data-region="{item['region']}"
            data-category="{cat}"
            data-type="{typ}"
            data-title="{item['title'].lower()}">
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">
            <a href="{item['url']}" target="_blank"
               style="color:#1d4ed8;text-decoration:none;font-size:0.88rem;line-height:1.4">
              {item['title']}
            </a>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;white-space:nowrap">
            <span style="font-size:0.82rem;color:#374151">{item['region']}</span><br>
            <span style="font-size:0.75rem;color:#6b7280">{item['city']}</span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{badge(cat, cat_color)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{badge(typ, typ_color)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{date_cell}</td>
        </tr>"""

    # Statystyki regionów
    region_stats = ""
    for region, count in sorted(by_region.items(), key=lambda x: -x[1]):
        pct = int(count / total * 100) if total else 0
        region_stats += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:6px 0;border-bottom:1px solid #f3f4f6">
          <span style="font-size:0.82rem;color:#374151">{region}</span>
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:80px;height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden">
              <div style="width:{pct}%;height:100%;background:#2563eb;border-radius:3px"></div>
            </div>
            <span style="font-size:0.8rem;font-weight:600;color:#1e40af;min-width:20px;text-align:right">{count}</span>
          </div>
        </div>"""

    # Statystyki kategorii
    cat_stats = ""
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        fg, bg = cat_colors.get(cat, ("#374151", "#f3f4f6"))
        cat_stats += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:5px 0;border-bottom:1px solid #f3f4f6">
          <span style="font-size:0.82rem">{badge(cat, (fg, bg))}</span>
          <span style="font-size:0.85rem;font-weight:700;color:{fg}">{count}</span>
        </div>"""

    # Lista regionów dla filtra (opcje select)
    region_options = "\n".join(
        f'<option value="{r}">{r}</option>'
        for r in sorted(by_region.keys())
    )

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Licytacje KAS — Raport {datetime.now().strftime("%d.%m.%Y")}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f8fafc; color: #1e293b; min-height: 100vh; }}
  .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
             color: white; padding: 28px 32px; }}
  .header h1 {{ font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px; }}
  .header p  {{ margin-top: 4px; opacity: 0.8; font-size: 0.88rem; }}
  .stats-row {{ display: flex; gap: 16px; padding: 20px 32px; flex-wrap: wrap; }}
  .stat-card {{ background: white; border-radius: 12px; padding: 16px 20px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.08); flex: 1; min-width: 120px; }}
  .stat-card .num {{ font-size: 2rem; font-weight: 800; color: #1e40af; }}
  .stat-card .lbl {{ font-size: 0.78rem; color: #6b7280; margin-top: 2px; }}
  .main {{ display: flex; gap: 20px; padding: 0 32px 32px; }}
  .sidebar {{ width: 240px; flex-shrink: 0; }}
  .sidebar-card {{ background: white; border-radius: 12px; padding: 16px;
                   box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 16px; }}
  .sidebar-card h3 {{ font-size: 0.8rem; font-weight: 700; color: #374151;
                      text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; }}
  .content {{ flex: 1; min-width: 0; }}
  .filters {{ background: white; border-radius: 12px; padding: 16px 20px;
              box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 16px;
              display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
  .filters input, .filters select {{
    border: 1.5px solid #e5e7eb; border-radius: 8px; padding: 8px 12px;
    font-size: 0.85rem; outline: none; transition: border 0.2s;
  }}
  .filters input:focus, .filters select:focus {{ border-color: #2563eb; }}
  .filters input {{ flex: 1; min-width: 200px; }}
  .count-badge {{ background: #eff6ff; color: #1d4ed8; border-radius: 999px;
                  padding: 4px 12px; font-size: 0.8rem; font-weight: 700; }}
  .table-wrap {{ background: white; border-radius: 12px;
                 box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead th {{ background: #f8fafc; padding: 10px 12px; text-align: left;
              font-size: 0.75rem; font-weight: 700; color: #6b7280;
              text-transform: uppercase; letter-spacing: 0.5px;
              border-bottom: 2px solid #e5e7eb; }}
  tbody tr:hover {{ background: #f0f7ff; cursor: pointer; }}
  .empty {{ text-align: center; padding: 48px; color: #9ca3af; font-size: 0.9rem; }}
  .footer {{ text-align: center; padding: 16px; font-size: 0.75rem; color: #9ca3af; }}
  @media (max-width: 768px) {{
    .main {{ flex-direction: column; padding: 0 16px 24px; }}
    .sidebar {{ width: 100%; }}
    .stats-row {{ padding: 16px; }}
    .header {{ padding: 20px 16px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>🏛️ Licytacje KAS — Krajowa Administracja Skarbowa</h1>
  <p>Raport wygenerowany: {scraped_at} &nbsp;·&nbsp; Wszystkie 16 Izb Administracji Skarbowej &nbsp;·&nbsp; Cała Polska</p>
</div>

<div class="stats-row">
  <div class="stat-card">
    <div class="num">{total}</div>
    <div class="lbl">Wszystkich ogłoszeń</div>
  </div>
  <div class="stat-card">
    <div class="num">{by_category.get("Nieruchomości", 0)}</div>
    <div class="lbl">Nieruchomości</div>
  </div>
  <div class="stat-card">
    <div class="num">{by_category.get("Pojazdy", 0)}</div>
    <div class="lbl">Pojazdy</div>
  </div>
  <div class="stat-card">
    <div class="num">{by_category.get("Maszyny/Sprzęt", 0)}</div>
    <div class="lbl">Maszyny/Sprzęt</div>
  </div>
  <div class="stat-card">
    <div class="num">16</div>
    <div class="lbl">Izb Skarbowych</div>
  </div>
</div>

<div class="main">
  <div class="sidebar">
    <div class="sidebar-card">
      <h3>📊 Ogłoszenia wg regionu</h3>
      {region_stats}
    </div>
    <div class="sidebar-card">
      <h3>🏷️ Wg kategorii</h3>
      {cat_stats}
    </div>
    <div class="sidebar-card" style="background:#eff6ff;border:1px solid #bfdbfe">
      <h3 style="color:#1e40af">ℹ️ Portal eLicytacje KAS</h3>
      <p style="font-size:0.78rem;color:#1e40af;line-height:1.5">
        KAS buduje centralny portal eLicytacje (planowany start: <strong>30 czerwca 2026</strong>).
        Obecnie ogłoszenia są dostępne na stronach regionalnych IAS.
      </p>
    </div>
  </div>

  <div class="content">
    <div class="filters">
      <input type="text" id="search" placeholder="🔍 Szukaj w tytule...">
      <select id="filter-region">
        <option value="">Wszystkie regiony</option>
        {region_options}
      </select>
      <select id="filter-category">
        <option value="">Wszystkie kategorie</option>
        <option value="Nieruchomości">Nieruchomości</option>
        <option value="Pojazdy">Pojazdy</option>
        <option value="Maszyny/Sprzęt">Maszyny/Sprzęt</option>
        <option value="Inne ruchomości">Inne ruchomości</option>
      </select>
      <select id="filter-type">
        <option value="">Wszystkie typy</option>
        <option value="I licytacja">I licytacja</option>
        <option value="II licytacja">II licytacja</option>
        <option value="Wolna ręka">Wolna ręka</option>
        <option value="Przetarg">Przetarg</option>
        <option value="Odwołanie">Odwołanie</option>
      </select>
      <span class="count-badge" id="count">{total} ogłoszeń</span>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Tytuł ogłoszenia</th>
            <th>Region / IAS</th>
            <th>Kategoria</th>
            <th>Typ sprzedaży</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody id="tbody">
          {rows_html}
          <tr id="empty-row" style="display:none">
            <td colspan="5" class="empty">Brak wyników dla wybranych filtrów.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<div class="footer">
  Dane pobrane ze stron regionalnych Izb Administracji Skarbowej w Polsce &nbsp;·&nbsp;
  Aktualizacja codziennie o 8:00 &nbsp;·&nbsp;
  <a href="https://www.kas.gov.pl" target="_blank" style="color:#6b7280">kas.gov.pl</a>
</div>

<script>
  const rows = document.querySelectorAll("tr.row");
  const countEl = document.getElementById("count");
  const emptyRow = document.getElementById("empty-row");

  function applyFilters() {{
    const search   = document.getElementById("search").value.toLowerCase();
    const region   = document.getElementById("filter-region").value;
    const category = document.getElementById("filter-category").value;
    const type     = document.getElementById("filter-type").value;
    let visible = 0;

    rows.forEach(row => {{
      const matchSearch   = !search   || row.dataset.title.includes(search);
      const matchRegion   = !region   || row.dataset.region === region;
      const matchCategory = !category || row.dataset.category === category;
      const matchType     = !type     || row.dataset.type === type;
      const show = matchSearch && matchRegion && matchCategory && matchType;
      row.style.display = show ? "" : "none";
      if (show) visible++;
    }});

    countEl.textContent = visible + " ogłoszeń";
    emptyRow.style.display = visible === 0 ? "" : "none";
  }}

  document.getElementById("search").addEventListener("input", applyFilters);
  document.getElementById("filter-region").addEventListener("change", applyFilters);
  document.getElementById("filter-category").addEventListener("change", applyFilters);
  document.getElementById("filter-type").addEventListener("change", applyFilters);
</script>

</body>
</html>"""
    return html


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "docs/index.html"

    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    html = generate_html(data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Raport HTML zapisany: {output_file}")
    print(f"   Ogłoszeń: {data['total']}")
