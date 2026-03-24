# Bexio-Tools: Migration zu Claude Code + Notion-Import

**Goal:** GitHub-Projekt `Noevu/bexio-tools` lokal einrichten, AI-Backend von Gemini CLI auf Claude Code CLI umstellen, rulesync einrichten, und ~419 bereits umbenannte Rechnungen in die bestehende Notion-Datenbank "Rechnungen & Belege" importieren.

**Architecture:** Das bestehende Python-CLI bleibt erhalten. Der `gemini` CLI-Subprocess wird durch `claude -p` ersetzt (gleiche Pattern wie Jarvis). Kein API-Key für AI nötig — Claude Code authentifiziert über Max Subscription. Config vereinfacht sich auf `bexio_access_token` + `company_name`. Projekt erhält `.rulesync/` für einheitliche AI-Konfiguration. Notion-Import der alten Rechnungen erfolgt durch Parsen der strukturierten Dateinamen und Batch-Erstellung via Notion MCP.

---

## Phase 1: Projekt einrichten

### Task 1: Repository klonen und aufräumen

**Files:**
- Create: `~/projects/bexio-tools/` (via git clone)
- Delete: `.gemini/` Ordner

**Steps:**
1. `cd ~/projects && gh repo clone Noevu/bexio-tools`
2. Bestätigen: `ls ~/projects/bexio-tools/` zeigt `bexio-tools.py`, `tools/`, `lib/`, `data/`
3. `.gemini/` Ordner entfernen
4. Commit: `chore: remove gemini-specific config`

### Task 2: Rulesync initialisieren

**Files:**
- Create: `~/projects/bexio-tools/.rulesync/` (via `rulesync init`)
- Create: `~/projects/bexio-tools/.rulesync/rules/project.md` (Projekt-Kontext)

**Steps:**
1. `cd ~/projects/bexio-tools && rulesync init && rulesync import`
2. `project.md` erstellen mit:
   - Projektbeschreibung: Python CLI für Bexio-Dokumentenmanagement
   - Stack: Python 3, Claude Code CLI, Notion MCP
   - Konventionen: Deutsche UI-Texte, Schweizer Orthographie
3. `rulesync generate`
4. Verifizierung: `.claude/CLAUDE.md` existiert und enthält Projektregeln
5. Commit: `chore: initialize rulesync`

---

## Phase 2: Gemini → Claude Code Migration

### Task 3: Config vereinfachen

**Files:**
- Modify: `lib/config.py`

**Changes:**
- `google_api_key` komplett entfernen — Claude Code braucht keinen API-Key
- `DEFAULT_CONFIG` bereinigen: nur noch `company_name`, `bexio_access_token`, `model`, `concurrency`, `limit`, `directories`, `custom_prompt_suffix`, `default_workflow`
- Default-Modell: `gemini-2.5-flash` → `claude-sonnet-4-6` (für `--model` Flag bei `claude -p`)
- `has_required_settings()`: prüft nur noch `company_name` (Bexio-Token wird bei Bedarf abgefragt)
- Properties `google_api_key` / `anthropic_api_key` entfernen

**Steps:**
1. `google_api_key` aus `DEFAULT_CONFIG`, Properties und allen Referenzen entfernen
2. Default model auf `claude-sonnet-4-6` setzen
3. Verifizierung: `python3 -c "from lib.config import get_config; c = get_config(); print(c.model)"` → `claude-sonnet-4-6`
4. Commit: `refactor: simplify config — remove AI API key (claude code handles auth)`

### Task 4: AI-Renamer auf Claude Code CLI umstellen (Kernstück)

**Files:**
- Modify: `tools/ai-renamer.py`

**Changes — was entfällt:**
- `resolve_gemini_command()` — komplett entfernen
- `check_google_api_key()` — komplett entfernen
- Env-Variablen `GOOGLE_API_KEY`, `GEMINI_API_KEY` — nicht mehr gesetzt
- `--allow-ignored` und `--no-mcp` Flags — nicht relevant für Claude Code

**Changes — was sich ändert:**
- Neue Funktion `resolve_claude_command()`:
  ```python
  def resolve_claude_command():
      result = subprocess.run(["which", "claude"], capture_output=True, text=True)
      if result.returncode == 0:
          return result.stdout.strip()
      print("FEHLER: 'claude' CLI nicht gefunden.")
      print("Installiere Claude Code: https://docs.anthropic.com/en/docs/claude-code")
      sys.exit(1)
  ```
- `process_file()` Subprocess-Aufruf anpassen:
  ```python
  # Alt (Gemini):
  cmd_args = gemini_cmd + ["--model", args.model]
  proc = subprocess.run(cmd_args, input=prompt, text=True, capture_output=True, env=env, cwd=filepath.parent)

  # Neu (Claude Code):
  cmd_args = [claude_cmd, "-p", prompt, "--model", args.model, "--dangerously-skip-permissions", "--output-format", "text"]
  proc = subprocess.run(cmd_args, text=True, capture_output=True, cwd=filepath.parent)
  ```
- `build_prompt()`: `@{fname}` Datei-Referenz ersetzen durch expliziten Pfad:
  `"Lies die Datei {filepath.resolve()} und analysiere den Inhalt..."`
  Claude Code kann Dateien (inkl. PDFs und Bilder) mit seinem Read-Tool lesen.
- `format_gemini_output()` → `format_ai_output()` (nur Rename)
- Alle UI-Texte: "Gemini" → "Claude"
- Log-Ordner: `gemini_raw` → `claude_raw`
- `main()`: `gemini_cmd` durch `claude_cmd` ersetzen, `check_google_api_key()` Aufruf entfernen

**Steps:**
1. `resolve_gemini_command()` durch `resolve_claude_command()` ersetzen
2. `check_google_api_key()` Aufruf und Funktion entfernen
3. `process_file()` Subprocess-Aufruf auf `claude -p` umstellen
4. `build_prompt()`: Datei-Referenz anpassen
5. UI-Texte und Log-Ordner umbenennen
6. Verifizierung: `python3 tools/ai-renamer.py --limit 1` mit einer Test-Datei in `data/downloads/`
7. Commit: `feat: replace gemini CLI with claude code for document analysis`

### Task 5: Hauptmenü anpassen

**Files:**
- Modify: `bexio-tools.py`

**Changes:**
- `prompt_api_key()` komplett entfernen — nicht mehr nötig
- `configure_settings()`: API-Key-Menüpunkt [2] entfernen
- Alle UI-Texte: "Google" / "Gemini" → "Claude"
- Env-Variablen `GOOGLE_API_KEY` Handling entfernen
- Ersteinrichtung: nur noch `company_name` abfragen (kein API-Key)
- `run_renamer()`: `GOOGLE_API_KEY` nicht mehr setzen

**Steps:**
1. `prompt_api_key()` Funktion und alle Aufrufe entfernen
2. Einstellungsmenü anpassen (API-Key-Option raus)
3. UI-Texte aktualisieren
4. Verifizierung: `python3 bexio-tools.py` — Menü zeigt "Claude", kein API-Key-Prompt
5. Commit: `refactor: simplify main menu — remove AI API key prompts`

### Task 6: README aktualisieren

**Files:**
- Modify: `readme.md`

**Changes:**
- Alle Gemini → Claude Code Referenzen
- Voraussetzung: Claude Code CLI installiert (Max Subscription)
- API-Key-Anleitung entfernen (nur Bexio Token bleibt)
- Projektstruktur: `.gemini/` → `.rulesync/`, kein `requirements.txt` nötig (kein SDK)

**Steps:**
1. README durchgehen und aktualisieren
2. Commit: `docs: update readme for claude code migration`

---

## Phase 3: Alte Rechnungen in Notion importieren

### Task 7: Dateinamen parsen und Notion-Einträge erstellen

**Ansatz:** Kein separates Python-Script nötig. Die ~419 umbenannten Dateien werden in dieser Claude Code Session geparst und direkt via Notion MCP (`notion-create-pages`) in Batches importiert.

**Quelldaten:**
- Ordner: `~/Documents/Noevu/Admin/Aufbewahrung Archiv/benannt/`
- ~419 Dateien mit strukturierten Namen
- Muster: `YYYY-MM-DD - Issuer - DocType - Recipient - [Customer -] AccountNum - AccountName - Description.ext`
  - Varianten: mit/ohne Doppelpunkt nach DocType, mit/ohne Kundenname, unterschiedliche Account-Formate

**Mapping auf Notion-Felder:**

| Dateiname-Part | Notion-Feld | Typ | Transformation |
|---------------|-------------|-----|----------------|
| YYYY-MM-DD | Rechnungsdatum | date | Direkt |
| Issuer | Absender | text | Direkt |
| Issuer + Description | Name (title) | title | `"{Issuer} — {Description}"` |
| DocType | Typ | select | Map: Rechnung/Quittung→Rechnung, Bestaetigung→Beleg |
| AccountNum + AccountName | Bexio Konto | select | Fuzzy-Match gegen bestehende Optionen |
| — | Status | select | `"Bezahlt"` (Annahme für alle alten) |
| — | Erfasst von | select | `"Jarvis"` |
| — | Währung | select | `"CHF"` (Default, da Schweizer Rechnungen) |

**Bexio Konto Mapping (AccountNum → Notion Select):**

| Dateiname-Nummer | Notion Select-Option |
|-----------------|---------------------|
| 4400 | 4400 Einkauf Dienstleistungen |
| 4450 | 4450 Hosting & Domains |
| 4455 | 4455 AI Tools |
| 5832 | 5832 Spesen/Reise/Auto |
| 6000 | 6000 Miete/Coworking |
| 6300 | 6300 Sachversicherungen |
| 6360 | 6360 Abgaben/Gebühren |
| 6500 | 6500 Büromaterial |
| 6510 | 6510 Kommunikationskosten |
| 6512 | 6512 Internet |
| 6530 | 6530 Buchführung |
| 6532 | 6532 Rechtsberatung |
| 6559 | 6559 Sonstiger Verwaltungsaufwand |
| 6570 | 6570 Informatikaufwand |
| 6600 | 6600 Werbeinserate |
| 6900 | 6900 Zinsaufwand |
| 6940 | 6940 Bankspesen |

**Typ Mapping:**

| Dateiname-Wert | Notion Select |
|---------------|---------------|
| Rechnung | Rechnung |
| Quittung | Beleg |
| Bestaetigung | Beleg |
| Anderes | Beleg |

**Notion DB Details:**
- Data Source ID: `56d38b40-70e3-41ce-8b43-914fa8d1f892`
- Batch-Limit: 100 Pages pro `notion-create-pages` Aufruf

**Steps:**
1. Alle Dateinamen aus `benannt/` einlesen
2. Regex-Parser für die verschiedenen Namensmuster
3. Parsen und Mapping auf Notion-Felder
4. Duplikatcheck: Bestehende Einträge in Notion abfragen
5. Import in Batches à 100 via `notion-create-pages`
6. Verifizierung: Stichproben in Notion prüfen

---

## Acceptance Criteria

- [ ] `~/projects/bexio-tools` existiert als Git-Repo mit `.rulesync/`
- [ ] Keine Gemini-Referenzen mehr im Code
- [ ] AI-Renamer nutzt `claude -p` CLI statt `gemini` CLI
- [ ] Kein AI-API-Key nötig — Claude Code handled Authentifizierung
- [ ] Config vereinfacht: nur `company_name` + `bexio_access_token`
- [ ] `python3 bexio-tools.py` startet und zeigt "Claude" im Menü
- [ ] Notion-DB "Rechnungen & Belege" enthält die alten Rechnungen
- [ ] Jeder Notion-Eintrag hat: Name, Absender, Rechnungsdatum, Bexio Konto, Typ, Status, Erfasst von

## Test Strategy

- **Smoke**: `python3 bexio-tools.py` startet ohne Fehler
- **Integration**: `python3 tools/ai-renamer.py --limit 1` verarbeitet eine Test-Datei
- **Notion**: Stichprobe von 10 importierten Einträgen manuell verifizieren
- **Regression**: `python3 tools/bexio-document-exporter.py --help` funktioniert weiterhin

## Reference Implementations

- Jarvis Claude Code CLI Aufruf: `~/projects/jarvis/scripts/jarvis-sync.sh` → `claude --dangerously-skip-permissions -p "/jarvis-sync"`
- Jarvis Finance-Klassifizierung: `~/projects/jarvis/brain/synthesis/finance-classification.md`
- Aktueller Gemini-Aufruf: `tools/ai-renamer.py:409-454` (process_file)
- Aktueller Config-Manager: `lib/config.py`
- Notion DB: Data Source `collection://56d38b40-70e3-41ce-8b43-914fa8d1f892`
- Umbenannte Rechnungen: `~/Documents/Noevu/Admin/Aufbewahrung Archiv/benannt/` (419 Dateien)

## Offene Fragen

1. **Belege in `Quittungen Rechnungen und Belege/` (~285)**: Sollen diese auch importiert werden? Teils unstrukturierte Dateinamen — müssten mit Claude nachbearbeitet werden.
2. **PDF-Attachments**: Sollen die PDFs als File in Notion hochgeladen werden, oder reicht der Datenbank-Eintrag ohne Attachment?
3. **Bexio-Tools-UI** (`~/Documents/Downloads/bexio-tools-ui/`): Separates Projekt oder integrieren?
