# Bexio Tools: Downloader & AI Renamer

By Noevu GmbH

**Deine Daten gehören dir.**

Dieses Projekt besteht aus einer CLI-Anwendung und zwei Tools, die dir helfen, deine Buchhaltungsbelege vollständig aus Bexio zu exportieren und mittels künstlicher Intelligenz (Google Gemini) automatisch zu analysieren, zu benennen und zu sortieren.

## Hintergrund & Motivation

Wir waren frustriert. Lösungen wie der [Kontera Belegexport](https://help.kontera.ch/de/articles/8906695-beleg-download) sind für Basisfunktionen wie den Download der _eigenen_ Dokumente kostenpflichtig. Wir finden: Der Zugriff auf die eigenen Geschäftsunterlagen sollte keine Paywall haben.

**Unsere Ziele:**

1. **Datenhoheit:** Kostenloser und vollständiger Export aller Belege.
2. **Automatisierung:** Kein manuelles Umbenennen von `Scan_2023_X.pdf` mehr.
3. **Archivierung:** Vorbereitung für eine revisionssichere Ablage (z.B. in [E-Post der Schweizerischen Post](https://www.epost.ch/de-ch/geschaeftskunden/ablegen) oder einem DMS).

---

## Projektstruktur

```
Bexio-Tools/
├── bexio-tools.py          # 🤖 Haupteinstiegspunkt (CLI mit Menü)
├── readme.md
├── LICENSE
│
├── lib/                    # Shared Library
│   ├── config.py           # Konfigurationsmanager (persistente Einstellungen)
│   └── utils.py            # Hilfsfunktionen
│
├── tools/                  # Einzelne Tools (auch standalone nutzbar)
│   ├── downloader.py       # Bexio Dokument-Downloader
│   └── ai-renamer.py       # KI-basierte Umbenennung
│
└── data/                   # Laufzeitdaten
    ├── accounts.csv        # Dein Kontenplan
    ├── downloads/          # Heruntergeladene Dateien
    ├── benannt/            # Umbenannte Dateien
    ├── verarbeitet/        # Archiv der Originale
    └── logs/               # Log-Dateien
```

---

## Die Tools

1. **`bexio-tools.py`**: Unified CLI mit Menü – der einfachste Weg, alle Funktionen zu nutzen.
2. **`tools/downloader.py`**: Lädt alle Dokumente (Inbox oder Archiv) aus deinem Bexio-Konto herunter.
3. **`tools/ai-renamer.py`**: Analysiert den Inhalt der Dateien mit Google Gemini, benennt sie logisch um.

## Voraussetzungen

- **Python 3** installiert.
- **Node.js & npm** installiert (wird für das KI-Interface benötigt).
- Ein **Bexio-Konto**.
- Ein **Google AI Studio Konto** (kostenlos).

---

## Schnellstart

### Mit der CLI (Empfohlen)

```bash
python bexio-tools.py
```

Das CLI führt dich durch alle Schritte:
1. API Key eingeben (wird gespeichert in `~/.bexio-tools/config.json`)
2. Firmenname eingeben
3. Menü: Download, Rename, oder beides

### Einzelne Tools direkt aufrufen

```bash
# Nur Dokumente herunterladen
python tools/downloader.py

# Nur Dokumente umbenennen
python tools/ai-renamer.py
```

---

## Einrichtung

### 1. Bexio Token (für den Downloader)

Damit das Skript Dateien laden darf, benötigst du einen **Personal Access Token**.

1. Gehe zu [developer.bexio.com/pat](https://developer.bexio.com/pat).
2. Logge dich ein und erstelle einen Token.
3. Kopiere den Token sofort (er wird nur einmal angezeigt).

### 2. Google Gemini API Key (für den Renamer)

Damit die KI deine Belege lesen kann.

1. Gehe zu [Google AI Studio](https://aistudio.google.com/).
2. Erstelle einen **API Key**.

### 3. Kontenplan (Optional, aber empfohlen)

Erstelle im `data/` Ordner eine Datei namens `accounts.csv`. Das KI-Skript nutzt diese, um den Belegen direkt das korrekte Buchhaltungskonto zuzuweisen.

**Format der `accounts.csv` (Trennzeichen: Semikolon):**

```csv
6000;Raumaufwand Miete;Aufwand
6200;Fahrzeugunterhalt;Aufwand
6500;Büromaterial;Aufwand
6570;Strom, Wasser, Gas;Aufwand
```

---

## Konfiguration

Die CLI speichert deine Einstellungen automatisch in `~/.bexio-tools/config.json`:

- API Key
- Firmenname
- Custom AI-Anweisungen (z.B. "Dokumente an Person X als Privatauslage markieren")
- Ordner-Pfade
- Modell & Parallelität

Du kannst die Einstellungen jederzeit über das Menü (Option 4) ändern.

---

## Nutzung mit Parametern

### Downloader

```bash
python tools/downloader.py --download-dir /pfad/zu/downloads
```

### AI Renamer

```bash
python tools/ai-renamer.py \
  --input-dir data/downloads \
  --out-dir data/benannt \
  --archive-dir data/verarbeitet \
  --log-dir data/logs \
  --model gemini-2.5-flash \
  --concurrency 4
```

**Parameter:**

| Parameter | Beschreibung | Standard |
|-----------|--------------|----------|
| `--input-dir` | Ordner mit zu verarbeitenden Dateien | `data/downloads` |
| `--out-dir` | Ordner für umbenannte Dateien | `data/benannt` |
| `--archive-dir` | Ordner für verarbeitete Originale | `data/verarbeitet` |
| `--log-dir` | Ordner für Log-Dateien | `data/logs` |
| `--model` | Gemini Modell | `gemini-2.5-flash` |
| `-c, --concurrency` | Anzahl gleichzeitiger Threads | `4` |
| `--limit` | Maximale Anzahl Dateien | `0` (alle) |

---

## Lizenz & Rechtliches

Dieses Projekt steht unter der **MIT Lizenz**. Nutzung auf eigene Verantwortung.

Die Tools basieren auf Open-Source-Code und nutzen die APIs von Bexio und Google. Bitte beachte die Datenschutzbestimmungen der jeweiligen Anbieter, insbesondere beim Upload von sensiblen Firmendaten zur Analyse an Google.

**[Copyright © Noevu GmbH – AI Lösungen für Schweizer KMU](https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio-tools)**
