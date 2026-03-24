# Bexio Tools: Dein digitaler Assistent für eine saubere Buchhaltung
_Von Noevu GmbH_

**Hol dir die Kontrolle über deine Geschäftsbelege zurück.**

Dieses Projekt bietet eine Sammlung von Kommandozeilen-Tools, die den Umgang mit Buchhaltungsbelegen aus [Bexio](https://bexio.com) revolutionieren. Lade Hunderte von Dokumenten mit einem Klick herunter, benenne sie automatisch mit künstlicher Intelligenz (Claude AI) und bereite sie für die revisionssichere Archivierung vor.

**Deine Daten. Deine Kontrolle. Keine Paywalls.**

## Das Problem: Manuelle Buchhaltung ist mühsam

Jeder, der Bexio nutzt, kennt es:
- **Manueller Download:** Jeden Beleg einzeln herunterladen, um ihn extern zu sichern.
- **Chaotische Dateinamen:** `Scan_2024_08_15.pdf` oder `Beleg-123.jpg` sagen nichts über den Inhalt aus.
- **Zeitaufwand:** Stundenlanges Sortieren und Umbenennen vor dem Jahresabschluss oder für den Treuhänder.
- **Archivierungslücke:** Wie gelangen die Dokumente aus Bexio einfach und strukturiert in ein revisionssicheres Archiv wie [ePost von der Schweizerischen Post](https://www.epost.ch/de-ch/geschaeftskunden/ablegen)?

## Die Lösung: Automatisierung mit Bexio-Tools

Unsere Tools nehmen dir diese Arbeit ab.
1.  **Bexio Dokumenten-Exporter:** Lade dein gesamtes Belegarchiv – oder nur eine Auswahl – mit einem einzigen Befehl herunter.
2.  **AI-Renamer:** Analysiert den Inhalt jedes Dokuments, erkennt Datum, Betrag, Lieferant sowie Buchhaltungskonto und benennt die Datei nach einem sauberen Schema: `JJJJ-MM-TT - Lieferant - Betrag - Beschreibung.pdf`.

**Das Ergebnis:** Ein perfekt organisierter Ordner, bereit für die langfristige, revisionssichere Ablage oder die Übergabe an deinen Treuhänder.

---

## Anleitung: In 5 Minuten startklar

Folge diesen Schritten, um die Tools einzurichten und zu nutzen.

### Schritt 1: Voraussetzungen schaffen

Stelle sicher, dass folgende Tools installiert sind:
- **Python 3**
- **Claude Code CLI** — installieren via [claude.ai/claude-code](https://docs.anthropic.com/en/docs/claude-code) (benötigt Max Subscription oder API Key)

### Schritt 2: Konfiguration

1.  **Bexio Access Token erstellen:**
    *   Erstelle unter [developer.bexio.com/pat](https://developer.bexio.com/pat) einen persönlichen Token.
    *   Speichere ihn sicher, er wird nur einmal angezeigt.

2.  **Projekt herunterladen & starten:**
    *   Lade dieses Projekt als ZIP herunter oder klone es.
    *   Öffne ein Terminal im Projektordner und starte die Anwendung:
      ```bash
      python bexio-tools.py
      ```

3.  **Geführte Einrichtung:**
    *   Beim ersten Start wirst du nach deinem **Firmennamen** gefragt. Claude Code CLI handhabt die AI-Authentifizierung automatisch.

### Schritt 3: Kontenplan hinterlegen (Empfohlen)

Damit die künstliche Intelligenz deine Belege direkt den richtigen Buchhaltungskonten zuordnen kann, benötigt sie deinen Kontenplan.

1.  Exportiere deinen Kontenplan aus Bexio als **CSV-Datei**.
2.  Speichere diese Datei unter dem Namen `accounts.csv` im Ordner `data/` oder benenne die Beispieldatei `accounts-beispiel.csv` um.

**Format der `accounts.csv` (Semikolon als Trennzeichen):**
```csv
Konto;Beschreibung;Typ
6000;Raumaufwand Miete;Aufwand
6200;Fahrzeugunterhalt;Aufwand
6500;Büromaterial;Aufwand
```

### Schritt 4: Tools anwenden

Nach der Einrichtung begrüsst dich das Hauptmenü.

1.  **Option 1: Dokumente herunterladen**
    *   Wähle diese Option, um den **Dokumenten-Exporter** zu starten.
    *   Ein interaktives Menü lässt dich wählen, welche Dokumente du laden möchtest (z.B. nur die der letzten 30 Tage, alle aus der Inbox etc.).
    *   Die Dateien werden im Ordner `data/downloads` gespeichert.

2.  **Option 2: Dokumente mit AI umbenennen**
    *   Wähle diese Option, um den **AI-Renamer** auf die Dateien im `data/downloads`-Ordner anzuwenden.
    *   Das Tool verarbeitet jede Datei, benennt sie um und verschiebt sie in den Ordner `data/benannt`. Die Originale werden in `data/verarbeitet` archiviert.

3.  **Option 3: Herunterladen UND Umbenennen**
    *   Der vollautomatische Workflow. Führt beide Schritte nacheinander aus.

### Schritt 5: Archivieren
Deine sauber benannten Belege im Ordner `data/benannt` sind nun bereit, in ein System wie **ePost** oder ein anderes digitales Archiv hochgeladen zu werden.

---

## Detaillierte Tool-Optionen

Beide Werkzeuge können auch direkt und mit spezifischen Parametern aufgerufen werden.

### Bexio Dokumenten-Exporter
`python tools/bexio-document-exporter.py`

Startet ein interaktives Menü mit vielen Filteroptionen. Alternativ sind Kommandozeilen-Parameter verfügbar (z.B. `--days 30`, um die Belege der letzten 30 Tage zu laden).

### AI-Renamer
`python tools/ai-renamer.py`

Verarbeitet standardmässig die Dateien aus `data/downloads`. Auch hier können über Parameter andere Ordner oder Limits definiert werden.

---

## Projektstruktur

```
Bexio-Tools/
├── bexio-tools.py              # 🤖 Haupteinstiegspunkt (CLI mit Menü)
├── readme.md                   # Diese Anleitung
├── .gitignore
├── .rulesync/                  # AI-Konfiguration (Claude, Gemini, Codex)
├── LICENSE
├── data/
│   ├── accounts-beispiel.csv   # Dein Kontenplan (hier ablegen!)
│   ├── benannt/                # ✅ Fertig benannte Dokumente
│   ├── downloads/              # 📥 Hier landen die Bexio-Downloads
│   ├── logs/
│   └── verarbeitet/            # 🗄️ Archiv der Originaldateien
├── lib/                        # Geteilte Code-Bibliothek
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   └── utils.py
└── tools/
    ├── __init__.py
    ├── ai-renamer.py           # KI-basiertes Umbenennungs-Tool (Claude AI)
    └── bexio-document-exporter.py # Tool für den Dokumenten-Download
```

---

## Lizenz & Rechtliches

Dieses Projekt steht unter der **MIT Lizenz**. Die Nutzung erfolgt auf eigene Verantwortung.

Die Tools nutzen die offiziellen APIs von Bexio und Anthropic (Claude). Bitte beachte die Datenschutzbestimmungen der jeweiligen Anbieter, insbesondere beim Upload von sensiblen Firmendaten zur Analyse.

**[Copyright © Noevu GmbH – KI-Lösungen für Schweizer KMU](https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio-tools)**
