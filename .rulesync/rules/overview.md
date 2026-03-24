---
root: true
targets: ["*"]
description: "Bexio-Tools — Python CLI für Dokumentenmanagement mit KI"
globs: ["**/*"]
---

# Bexio-Tools

Python CLI für Bexio-Dokumentenmanagement mit KI-Unterstützung (Claude Code).

## Stack

- Python 3 (keine externen Dependencies ausser Standard-Lib)
- Claude Code CLI (`claude -p`) für Dokumentenanalyse
- Notion MCP für Rechnungsverwaltung
- macOS Keychain für API-Tokens

## Konventionen

- Deutsche UI-Texte, Schweizer Orthographie (`ss` statt `ß`, Umlaute)
- Tabs für Indentation (Python: 4 Spaces gemäss PEP 8)
- Keine `.env` Dateien — Secrets via macOS Keychain
- Bestehende Config in `~/.bexio-tools/config.json` respektieren

## Architektur

- `bexio-tools.py` — Hauptmenü / Entry Point
- `tools/` — Einzelne Werkzeuge (Exporter, Renamer)
- `lib/` — Geteilte Bibliothek (Config, Utils, Logger)
- `data/` — Arbeitsverzeichnisse (downloads, benannt, verarbeitet, logs)
