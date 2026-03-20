# 🏛️ Agent Licytacji KAS

Agent automatycznie pobiera codziennie o **8:00** ogłoszenia o licytacjach ze wszystkich
**16 Izb Administracji Skarbowej** w Polsce i publikuje czytelny raport na GitHub Pages.

## 📋 Co robi agent?

1. **Scrapuje** strony wszystkich regionalnych IAS (cała Polska)
2. **Klasyfikuje** ogłoszenia na kategorie: Nieruchomości, Pojazdy, Maszyny/Sprzęt
3. **Generuje** interaktywny raport HTML z filtrami
4. **Publikuje** raport na GitHub Pages — dostępny przez przeglądarkę

## 🚀 Instalacja (5 minut)

### Krok 1: Utwórz repozytorium na GitHub

1. Zaloguj się na [github.com](https://github.com)
2. Kliknij **"New repository"**
3. Nazwij je np. `kas-licytacje`
4. Ustaw jako **Public** (wymagane dla darmowych GitHub Pages)
5. Kliknij **"Create repository"**

### Krok 2: Wgraj pliki

Wgraj wszystkie pliki z tego projektu do repozytorium:

```bash
git init
git add .
git commit -m "Inicjalny commit"
git branch -M main
git remote add origin https://github.com/TWOJ-LOGIN/kas-licytacje.git
git push -u origin main
```

### Krok 3: Włącz GitHub Pages

1. Wejdź w repozytorium → **Settings** → **Pages**
2. W sekcji **Source** wybierz **"Deploy from a branch"**
3. Gałąź: `main`, folder: `/docs`
4. Kliknij **Save**

Po chwili raport będzie dostępny pod adresem:
```
https://TWOJ-LOGIN.github.io/kas-licytacje/
```

### Krok 4: Pierwsze uruchomienie

1. Wejdź w **Actions** → **🏛️ Pobierz licytacje KAS**
2. Kliknij **"Run workflow"** → **"Run workflow"**
3. Po ok. 2 minutach raport pojawi się na GitHub Pages ✅

## ⏰ Harmonogram

Agent uruchamia się automatycznie **codziennie o 8:00** (czas polski, latem).
Możesz też uruchomić go ręcznie w zakładce **Actions**.

## 📁 Struktura plików

```
kas-licytacje/
├── .github/
│   └── workflows/
│       └── daily.yml        ← harmonogram GitHub Actions
├── docs/
│   ├── index.html           ← raport HTML (GitHub Pages)
│   └── data.json            ← surowe dane JSON
├── scraper.py               ← pobiera dane ze stron KAS
├── generate_report.py       ← generuje raport HTML
├── main.py                  ← łączy scraper + generator
├── requirements.txt         ← zależności Python
└── README.md
```

## 🗺️ Źródła danych

Agent pobiera dane z oficjalnych stron BIP wszystkich 16 IAS:

| Region | IAS | URL |
|--------|-----|-----|
| Dolnośląskie | Wrocław | dolnoslaskie.kas.gov.pl |
| Kujawsko-Pomorskie | Bydgoszcz | kujawsko-pomorskie.kas.gov.pl |
| Lubelskie | Lublin | lubelskie.kas.gov.pl |
| Lubuskie | Zielona Góra | lubuskie.kas.gov.pl |
| Łódzkie | Łódź | lodzkie.kas.gov.pl |
| Małopolskie | Kraków | malopolskie.kas.gov.pl |
| Mazowieckie | Warszawa | mazowieckie.kas.gov.pl |
| Opolskie | Opole | opolskie.kas.gov.pl |
| Podkarpackie | Rzeszów | podkarpackie.kas.gov.pl |
| Podlaskie | Białystok | podlaskie.kas.gov.pl |
| Pomorskie | Gdańsk | pomorskie.kas.gov.pl |
| Śląskie | Katowice | slaskie.kas.gov.pl |
| Świętokrzyskie | Kielce | swietokrzyskie.kas.gov.pl |
| Warmińsko-Mazurskie | Olsztyn | warminsko-mazurskie.kas.gov.pl |
| Wielkopolskie | Poznań | wielkopolskie.kas.gov.pl |
| Zachodniopomorskie | Szczecin | zachodniopomorskie.kas.gov.pl |

## ℹ️ Uwaga: Portal eLicytacje KAS

KAS buduje centralny portal **eLicytacje** (planowany start: **30 czerwca 2026**).
Po jego uruchomieniu agent zostanie zaktualizowany, by pobierać dane z jednego miejsca.

## 🔧 Lokalne uruchomienie (opcjonalne)

```bash
pip install -r requirements.txt
python main.py
# Raport: docs/index.html
```
