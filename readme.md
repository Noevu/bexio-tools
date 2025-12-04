# Bexio Tools: Downloader & AI Renamer

By Noevu GmbH

**Deine Daten gehören dir.**

Dieses Projekt besteht aus zwei Skripten, die dir helfen, deine Buchhaltungsbelege vollständig aus Bexio zu exportieren und mittels künstlicher Intelligenz (Google Gemini) automatisch zu analysieren, zu benennen und zu sortieren.

## Hintergrund & Motivation

Wir waren frustriert. Lösungen wie der [Kontera Belegexport](https://help.kontera.ch/de/articles/8906695-beleg-download) sind für Basisfunktionen wie den Download der _eigenen_ Dokumente kostenpflichtig. Wir finden: Der Zugriff auf die eigenen Geschäftsunterlagen sollte keine Paywall haben.

**Unsere Ziele:**

1. **Datenhoheit:** Kostenloser und vollständiger Export aller Belege.
2. **Automatisierung:** Kein manuelles Umbenennen von `Scan_2023_X.pdf` mehr.
3. **Archivierung:** Vorbereitung für eine revisionssichere Ablage (z.B. in [E-Post der Schweizerischen Post](https://www.epost.ch/de-ch/geschaeftskunden/ablegen) oder einem DMS).

---

## Die Tools

1. **`bexio_documents_downloader.py`**: Lädt alle Dokumente (Inbox oder Archiv) aus deinem Bexio-Konto herunter.
2. **`bexio_documents_ai_renamer.py`**: Analysiert den Inhalt der Dateien mit Google Gemini, benennt sie logisch um (Datum, Lieferant, Konto) und sortiert sie.

## Voraussetzungen

- **Python 3** installiert.
- **Node.js & npm** installiert (wird für das KI-Interface benötigt).
- Ein **Bexio-Konto**.
- Ein **Google AI Studio Konto** (kostenlos).

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

Erstelle im Ordner der Skripte eine Datei namens `accounts.csv`. Das KI-Skript nutzt diese, um den Belegen direkt das korrekte Buchhaltungskonto zuzuweisen.

**Format der `accounts.csv` (Trennzeichen: Semikolon):**

```csv
6000;Raumaufwand Miete;Aufwand
6200;Fahrzeugunterhalt;Aufwand
6500;Büromaterial;Aufwand
6570;Strom, Wasser, Gas;Aufwand
```

### 4. Umgebungsvariablen (Optional)

Du kannst die Keys bei jedem Start eingeben oder sie dauerhaft in deinem System (`.zshrc`, `.bashrc` oder Windows Umgebungsvariablen) hinterlegen:

```bash
export BEXIO_ACCESS_TOKEN="dein-bexio-token"
export GOOGLE_API_KEY="dein-google-key"
export COMPANY_NAME="Muster GmbH"  # Hilft der KI, Empfänger vs. Absender zu unterscheiden
```

---

## Nutzung

### Schritt 1: Dokumente herunterladen

Starte den Downloader. Er speichert die Dateien standardmäßig in den Ordner `downloads`.

```bash
python3 bexio_documents_downloader.py
```

**Parameter:**

- `--download-dir <pfad>`: Ordner für heruntergeladene Dateien (Standard: `downloads`)

**Beispiel:**

```bash
python3 bexio_documents_downloader.py --download-dir /pfad/zu/meine/downloads
```

_Folge den Anweisungen im Terminal (Wahl zwischen "Alles" oder "Inbox"). Am Ende wird gefragt, ob der Download-Ordner geöffnet werden soll._

### Schritt 2: Dokumente analysieren & umbenennen

Starte den AI Renamer. Er nimmt die Dateien aus `downloads`, schickt sie zur Analyse an die KI und speichert das Ergebnis in `benannt`.

```bash
python3 bexio_documents_ai_renamer.py
```

**Parameter:**

- `--input-dir <pfad>`: Ordner mit zu verarbeitenden Dateien (Standard: `downloads`)
- `--out-dir <pfad>`: Ordner für umbenannte Dateien (Standard: `benannt`)
- `--archive-dir <pfad>`: Ordner für verarbeitete Originale (Standard: `verarbeitet`)
- `--log-dir <pfad>`: Ordner für Log-Dateien (Standard: `logs`)
- `--model <modell>`: Gemini Modell (Standard: `gemini-2.5-flash`)
- `-c, --concurrency <anzahl>`: Anzahl gleichzeitiger Threads (Standard: `4`)
- `--limit <anzahl>`: Maximale Anzahl zu verarbeitender Dateien (Standard: `0` = alle)

**Beispiel:**

```bash
python3 bexio_documents_ai_renamer.py --input-dir downloads --out-dir benannt --archive-dir archiv --log-dir logs
```

_Beim Start werden alle Ordner-Pfade abgefragt (mit Standardwerten). Am Ende wird gefragt, ob der Output-Ordner geöffnet werden soll._

**Was passiert dabei?**

1. Das Skript fragt nach allen Ordner-Pfaden (mit Standardwerten) oder verwendet die übergebenen Parameter.
2. Das Skript prüft, ob das nötige CLI-Tool (`gemini-chat-cli`) installiert ist. Falls nicht, bietet es an, dies via `npm` automatisch zu tun.
3. Jede Datei wird analysiert (Datum, Lieferant, Typ, Inhalt).
4. Die Datei wird nach dem Schema `YYYY-MM-DD - Lieferant - Typ - Empfänger - Beschreibung.ext` umbenannt.
5. Die Datei wird in den Output-Ordner (`benannt/` standardmäßig) kopiert.
6. Das Original wird in den Archiv-Ordner (`verarbeitet/` standardmäßig) verschoben.
7. Am Ende wird gefragt, ob der Output-Ordner geöffnet werden soll.

---

## Ordnerstruktur

Nach der Ausführung sieht dein Ordner so aus:

```text
.
├── bexio_documents_downloader.py
├── bexio_documents_ai_renamer.py
├── accounts.csv            # Dein Kontenplan
├── downloads/              # (Leer, da verarbeitet)
├── benannt/                # HIER liegen deine fertigen Dateien
│   ├── 2023-10-12 - Swisscom - Rechnung - Muster_GmbH - Internet.pdf
│   └── 2023-11-05 - SBB - Quittung - Mitarbeiter - Halbtax.jpg
├── verarbeitet/            # Archiv der Original-Dateien (Backup)
└── logs/                   # Technische Logs der KI-Antworten
```

---

## Lizenz & Rechtliches

Dieses Projekt steht unter der **MIT Lizenz**. Nutzung auf eigene Verantwortung.

Die Tools basieren auf Open-Source-Code und nutzen die APIs von Bexio und Google. Bitte beachte die Datenschutzbestimmungen der jeweiligen Anbieter, insbesondere beim Upload von sensiblen Firmendaten zur Analyse an Google.

**[Copyright © Noevu GmbH – AI Lösungen für Schweizer KMU](https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio-tools)**
