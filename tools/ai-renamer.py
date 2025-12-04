#!/usr/bin/env python3
"""
AI-powered document renamer for Bexio financial documents.
Uses Gemini AI to analyze documents and generate structured filenames.
"""
import os
import sys
import shutil
import argparse
import logging
import subprocess
import re
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Enable readline for better input editing (arrow keys, cursor movement)
try:
    import readline
except ImportError:
    pass  # readline not available on Windows

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.utils import open_url, open_file, open_directory, set_finder_comment, get_data_dir

# --- CONFIGURATION ---
DEFAULT_MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
DEFAULT_CONCURRENCY = int(os.environ.get("CONCURRENCY", 20))
DATA_DIR = get_data_dir()
DEFAULT_INPUT_DIR = DATA_DIR / "downloads"
DEFAULT_OUT_DIR = DATA_DIR / "benannt"
DEFAULT_ARCHIVE_DIR = DATA_DIR / "verarbeitet"
DEFAULT_LOG_DIR = DATA_DIR / "logs"
EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}

# App-Name für Log-Datei
APP_NAME = Path(__file__).stem

# Global Lock to prevent input prompts from overlapping with logs
CONSOLE_LOCK = threading.Lock()

# Setup Logging (wird später in main() mit dynamischem Log-Dir aufgerufen)
log = None
RAW_DIR = None


def get_now_iso():
    return datetime.now().astimezone().isoformat()


def resolve_gemini_command():
    """Prüft ob gemini installiert ist, sonst verwendet npx gemini-chat-cli."""
    result = subprocess.run(["which", "gemini"], capture_output=True, text=True)
    if result.returncode == 0:
        return ["gemini"]
    
    result = subprocess.run(["which", "npx"], capture_output=True, text=True)
    if result.returncode == 0:
        return ["npx", "gemini-chat-cli"]
    
    print("FEHLER: Weder 'gemini' noch 'npx' wurde gefunden.")
    print("Bitte installiere eines der folgenden:")
    print("  - gemini CLI Tool")
    print("  - Node.js (für npx)")
    sys.exit(1)


def check_google_api_key():
    """Prüft ob Google API Key gesetzt ist, fragt danach falls nicht."""
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        url = "https://aistudio.google.com/"
        print("\n" + "-" * 70)
        print("  KEIN GOOGLE API KEY GEFUNDEN")
        print("-" * 70)
        print(f"  1. Gehe zu: {url}")
        print("  2. Melde dich mit deinem Google-Konto an.")
        print("  3. Klicke auf 'Get API Key' oder gehe zu den API-Einstellungen.")
        print("  4. Erstelle einen neuen API Key oder kopiere einen bestehenden.")
        print("-" * 70)
        
        open_choice = input(f"\n  Soll {url} im Browser geöffnet werden? (j/n): ").strip().lower()
        if open_choice in ['j', 'y', 'ja', 'yes']:
            print(f"  🔗 Öffne {url} im Browser...")
            open_url(url)
        print()
        
        while True:
            api_key = input("Google API Key (GOOGLE_API_KEY oder GEMINI_API_KEY) [oder 'q' zum Beenden]: ").strip()
            if api_key.lower() in ['q', 'quit', 'exit', 'beenden']:
                print("  Bye bye 👋")
                sys.exit(0)
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key
                return api_key
            print("  ⚠️  Bitte gib einen gültigen API Key ein oder 'q' zum Beenden.")
    return api_key


def check_company_name():
    """Prüft ob Firmenname gesetzt ist, fragt danach falls nicht."""
    company_name = os.environ.get("COMPANY_NAME")
    if not company_name:
        while True:
            company_name = input("Firmenname (COMPANY_NAME) [oder 'q' zum Beenden]: ").strip()
            if company_name.lower() in ['q', 'quit', 'exit', 'beenden']:
                print("  App wird beendet.")
                sys.exit(0)
            if company_name:
                os.environ["COMPANY_NAME"] = company_name
                return company_name
            print("  ⚠️  Bitte gib einen gültigen Firmenname ein oder 'q' zum Beenden.")
    return company_name


def configure_directories(args):
    """Fragt nach allen Ordner-Pfaden mit Defaults (außer Log-Ordner)."""
    print(f"\n{'─'*70}")
    print("  📁 ORDNER-KONFIGURATION")
    print(f"{'─'*70}")
    
    input_dir = input(f"  Input-Ordner (Downloads) [Standard: {args.input_dir}]: ").strip()
    if input_dir.lower() in ['q', 'quit', 'exit', 'beenden']:
        print("  Bye bye 👋")
        sys.exit(0)
    if input_dir:
        args.input_dir = Path(input_dir).resolve()
    else:
        args.input_dir = Path(args.input_dir).resolve()
    
    out_dir = input(f"  Output-Ordner (Benannt) [Standard: {args.out_dir}]: ").strip()
    if out_dir.lower() in ['q', 'quit', 'exit', 'beenden']:
        print("  Bye bye 👋")
        sys.exit(0)
    if out_dir:
        args.out_dir = Path(out_dir).resolve()
    else:
        args.out_dir = Path(args.out_dir).resolve()
    
    archive_dir = input(f"  Archiv-Ordner (Verarbeitet) [Standard: {args.archive_dir}]: ").strip()
    if archive_dir.lower() in ['q', 'quit', 'exit', 'beenden']:
        print("  Bye bye 👋")
        sys.exit(0)
    if archive_dir:
        args.archive_dir = Path(archive_dir).resolve()
    else:
        args.archive_dir = Path(args.archive_dir).resolve()
    
    args.log_dir = Path(args.log_dir).resolve()
    print(f"{'─'*70}\n")


def configure_startup(args):
    """Interactively asks user for config overrides."""
    print(f"{'─'*70}")
    print("  ⚙️  VERARBEITUNGS-KONFIGURATION")
    print(f"{'─'*70}")
    
    p_limit = input(f"  Anzahl der zu verarbeitenden Dateien [Standard: {'Alle' if args.limit==0 else args.limit}]: ").strip()
    if p_limit.lower() in ['q', 'quit', 'exit', 'beenden']:
        print("  Bye bye 👋")
        sys.exit(0)
    if p_limit:
        try:
            args.limit = int(p_limit)
        except ValueError:
            print("  ⚠️  Ungültige Zahl, verwende Standardwert.")

    p_conc = input(f"  Gleichzeitige Aufgaben [Standard: {args.concurrency}]: ").strip()
    if p_conc.lower() in ['q', 'quit', 'exit', 'beenden']:
        print("  Bye bye 👋")
        sys.exit(0)
    if p_conc:
        try:
            val = int(p_conc)
            if val > 0: args.concurrency = val
        except ValueError:
            print("  ⚠️  Ungültige Zahl, verwende Standardwert.")

    p_model = input(f"  Gemini Modell [Standard: {args.model}]: ").strip()
    if p_model.lower() in ['q', 'quit', 'exit', 'beenden']:
        print("  Bye bye 👋")
        sys.exit(0)
    if p_model:
        args.model = p_model
        
    print(f"{'─'*70}\n")


def load_accounts_csv() -> str | None:
    """Lädt accounts.csv falls vorhanden und gibt den Inhalt als String zurück."""
    accounts_file = DATA_DIR / "accounts.csv"
    
    if not accounts_file.exists():
        return None
    
    try:
        with open(accounts_file, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        if log:
            log.warning(f"Fehler beim Lesen von accounts.csv: {e}")
        else:
            print(f"  ⚠️  Fehler beim Lesen von accounts.csv: {e}")
        return None


def build_prompt(filepath: Path, company_name: str) -> str:
    fname = filepath.name
    accounts_content = load_accounts_csv()
    
    if accounts_content:
        accounts_section = f"""Aufwandskonto (verwende diese Liste zur Zuordnung):
{accounts_content}

Wichtig: Das "account" Feld muss im Format "Nummer - Name" sein (z.B. "4400 -Einkauf Dienstleistungen")."""
    else:
        accounts_section = """Aufwandskonto:
Hinweis: Keine Kontenliste verfügbar. Schätze den passenden Kontonamen basierend auf üblichen Schweizer Buchhaltungskonten.
Das "account" Feld sollte im Format "Nummer - Name" sein (z.B. "4400 – Einkauf Dienstleistungen")."""
    
    custom_suffix = os.environ.get("CUSTOM_PROMPT_SUFFIX", "")
    custom_section = f"\n\nZusätzliche Anweisungen:\n{custom_suffix}" if custom_suffix else ""
    
    return f"""Du bist ein erfahrener Buchhaltungsassistent.
Deine Aufgabe ist es, strukturierte Daten aus der Datei @{fname} zu extrahieren, damit diese ordnungsgemäß umbenannt werden kann.

Analysiere den Inhalt (Bild oder PDF) und den Dateinamen.
Antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt. Keine Markdown-Formatierung, kein Text davor oder danach.

Das JSON muss folgende Felder enthalten:
{{
  "date": "YYYY-MM-DD",          // Das Belegdatum. Falls nicht auffindbar: null.
  "issuer": "Firmenname",        // Wer hat das Dokument ausgestellt?
  "document_type": "Typ",        // "Rechnung", "Quittung", "Bestaetigung" oder "Anderes"
  "recipient": "Empfänger",      // Default: "{company_name}". Wenn nicht {company_name}, dann ist der Empfänger ein Kunde.
  "customer": "Kundenname",      // Optional: Name des Kunden, falls zutreffend (sonst null oder leerer String).
  "account": "Konto",            // Das Aufwandskonto
  "description": "Beschreibung"  // Kurze Beschreibung der Transaktion (max 5-6 Wörter, Deutsch).
}}

{accounts_section}

Hinweise:
1. Datum: Format YYYY-MM-DD.
2. recipient: Wenn kein Empfänger erkennbar ist, nimm "{company_name}".
3. Sanitize: Die Werte in den Feldern dürfen keine ungültigen Dateinamen-Zeichen enthalten.{custom_section}
"""


def sanitize_part(text: str) -> str:
    if not text: return ""
    text = text.replace("/", "-").replace("\\", "-").replace(":", "-")
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    return text.strip()


def extract_data_from_json(raw_output: str) -> dict | None:
    try:
        match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
        if not match: return None
        return json.loads(match.group(1))
    except:
        return None


def interactive_fill_missing_fields(data: dict, filepath: Path, company_name: str) -> dict:
    """Prüft auf fehlende Pflichtfelder und fragt diese gezielt ab."""
    mandatory_fields = {
        "date": "Datum (YYYY-MM-DD)",
        "issuer": "Aussteller",
        "document_type": "Dokumenttyp (Rechnung/Quittung/etc)",
        "account": "Konto",
        "description": "Beschreibung"
    }
    
    if not data.get("recipient"):
        data["recipient"] = company_name

    missing = [k for k in mandatory_fields if not data.get(k)]
    
    if not missing:
        return data
        
    with CONSOLE_LOCK:
        print(f"\n{'!'*60}")
        print(f"FEHLENDE DATEN: {filepath.name}")
        print(f"{'-'*60}")
        
        open_file(filepath)
        
        for field in missing:
            label = mandatory_fields[field]
            while True:
                value = input(f"  > Bitte eingeben: {label}: ").strip()
                if value:
                    data[field] = value
                    break
        print(f"{'-'*60}\n")
            
    return data


def construct_filename(data: dict, original_ext: str, company_name: str) -> str:
    date = data.get("date")
    issuer = sanitize_part(data.get("issuer", "Unbekannt"))
    doc_type = sanitize_part(data.get("document_type", "Anderes"))
    recipient = sanitize_part(data.get("recipient", company_name))
    customer = sanitize_part(data.get("customer", ""))
    account = sanitize_part(data.get("account", "Unbekannt"))
    description = sanitize_part(data.get("description", ""))
    
    base_name = f"{date} - {issuer} - {doc_type}: {recipient} - "
    if customer: base_name += f"{customer} - "
    base_name += f"{account} - {description}"
    
    full_name = f"{base_name}.{original_ext}".replace("\n", " ").replace("\r", "")
    return full_name


def get_unique_path(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists(): return target
    stem, suffix = target.stem, target.suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        candidate = directory / new_name
        if not candidate.exists(): return candidate
        counter += 1


def format_gemini_output(raw_output: str) -> str:
    """Formatiert Gemini-Output schön für die Konsole."""
    lines = []
    
    try:
        match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            lines.append("  📋 Extrahierte Daten:")
            field_labels = {
                "date": "📅 Datum",
                "issuer": "🏢 Aussteller",
                "document_type": "📄 Dokumenttyp",
                "recipient": "👤 Empfänger",
                "customer": "🧑‍💼 Kunde",
                "account": "💰 Konto",
                "description": "📝 Beschreibung"
            }
            for key, label in field_labels.items():
                value = data.get(key, "—")
                if value:
                    lines.append(f"     {label}: {value}")
            return "\n".join(lines)
    except:
        pass
    
    raw_lines = raw_output.strip().splitlines()
    lines.append("  📋 Gemini Ausgabe:")
    for line in raw_lines[:8]:
        clean_line = line.strip()
        if clean_line:
            lines.append(f"     {clean_line}")
    if len(raw_lines) > 8:
        lines.append("     ... (weitere Zeilen gekürzt) ...")
    return "\n".join(lines)


def manual_intervention(filepath: Path, raw_output: str, original_ext: str) -> str | None:
    """Shows output, asks user for filename. Thread-safe durch Queue."""
    with CONSOLE_LOCK:
        print(f"{'─'*70}")
        print(f"\n  ❌ FEHLER BEIM PARSEN: {filepath.name}")
        print(f"{'─'*70}")
        
        print(format_gemini_output(raw_output))
        print(f"{'─'*70}")
        
        print(f"\n  📄 Öffne Datei: {filepath.name}")
        open_file(filepath)
        print()
    
    with CONSOLE_LOCK:
        while True:
            print("  Optionen:")
            print("    [1] Name manuell eingeben")
            print("    [2] Fallback verwenden (Datum-Unbekannt)")
            print("    [3] Datei überspringen")
            choice = input("  > ").strip()
            
            if choice == "1":
                user_name = input("  Neuen Dateinamen eingeben (ohne Erweiterung): ").strip()
                if user_name:
                    return f"{user_name}.{original_ext}"
            elif choice == "2":
                return None
            elif choice == "3":
                return "SKIP"
            else:
                print("  ⚠️  Ungültige Auswahl.")


def process_file(filepath: Path, args, company_name: str, gemini_cmd: list, file_index: int, total_files: int):
    import platform
    try:
        ext = filepath.suffix.lower().lstrip(".")
        
        with CONSOLE_LOCK:
            print(f"[{file_index}/{total_files}] Verarbeite: {filepath.name}")
        
        prompt = build_prompt(filepath, company_name)
        
        env = os.environ.copy()
        if args.allow_ignored:
            env.update({"MODEL_CONTEXT_ALLOW_IGNORED_FILES": "1", "MODEL_CONTEXT_DISABLE_GITIGNORE": "1"})

        cmd_args = gemini_cmd + ["--model", args.model]
        
        if args.disable_mcp:
            cmd_args.extend(["--allowed-mcp-server-names", "__DISABLED__"])

        raw_output = ""
        clean_output = ""
        data = None
        retries = 3

        for attempt in range(retries):
            proc = subprocess.run(
                cmd_args,
                input=prompt, text=True, capture_output=True, env=env,
                cwd=filepath.parent
            )
            
            raw_output = proc.stdout
            clean_output = "\n".join([line for line in raw_output.splitlines() if "IDEClient" not in line])

            if clean_output.strip():
                data = extract_data_from_json(clean_output)
                if data:
                    break  # Success, exit retry loop
            
            with CONSOLE_LOCK:
                log_func = log.warning if log else print
                log_func(f"  Versuch {attempt + 1}/{retries} für {filepath.name} fehlgeschlagen (keine validen Daten von Gemini).")
                if attempt + 1 < retries:
                    log_func("  Wiederhole in 1 Sekunde...")
                    time.sleep(1)

        raw_dir = args.log_dir / "gemini_raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        with open(raw_dir / f"{filepath.name}.raw.txt", "w", encoding="utf-8") as f:
            f.write(f"=== {get_now_iso()} | {filepath.name} ===\n{clean_output}\n")

        new_filename = None
        
        if data:
            data = interactive_fill_missing_fields(data, filepath, company_name)
            new_filename = construct_filename(data, ext, company_name)
        else:
            user_result = manual_intervention(filepath, clean_output, ext)
            if user_result == "SKIP":
                log_entry = f"ÜBERSPRUNGEN | {filepath.name} | - | Gemini Output:\n{clean_output}"
                log.info(log_entry)
                return False
            elif user_result:
                new_filename = user_result
                
        if not new_filename:
            try:
                ts = filepath.stat().st_mtime
                date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except: date_str = "unbekanntes-datum"
            new_filename = f"{date_str} - unbekannt - anderes - {company_name} - unbekannt - {filepath.stem}.{ext}"

        if platform.system() == "Windows": new_filename = new_filename.replace(":", "-")
        else: new_filename = new_filename.replace("/", "-")

        dest_path = get_unique_path(args.out_dir, new_filename)
        shutil.copy2(filepath, dest_path)
        set_finder_comment(dest_path, filepath.name)
        
        archive_path = get_unique_path(args.archive_dir, filepath.name)
        shutil.move(filepath, archive_path)
        set_finder_comment(archive_path, dest_path.name)

        log_entry = f"ERFOLG | {filepath.name} | {dest_path.name} | Gemini Output:\n{clean_output}"
        
        with CONSOLE_LOCK:
            print(f"  ✓ {filepath.name} → {dest_path.name}")
            log.info(log_entry)
        return True

    except Exception as e:
        error_entry = f"FEHLER | {filepath.name} | - | Fehler: {e}"
        with CONSOLE_LOCK:
            log.error(f"Fehler beim Verarbeiten von {filepath}: {e}")
            log.error(error_entry)
        return False


def print_intro():
    """Zeigt einen hübschen Intro Screen."""
    print("\n" + "─" * 70)
    print(" " * 15 + "🤖 BEXIO DOKUMENTE AI RENAMER")
    print("  Automatische Umbenennung von Finanzdokumenten mit Gemini AI")
    print("\n  Format: YYYY-MM-DD - Issuer - DocType: Recipient - Customer - Account - Description.ext")
    print("\n  💡 Tipp: Du kannst jederzeit mit 'q' abbrechen")
    print()


def print_copyright():
    """Zeigt Copyright-Informationen."""
    print("\n" + "-" * 70)
    print("  Copyright © Noevu GmbH – AI Lösungen für Schweizer KMU")
    print("  https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio_ai_renamer")
    print("-" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Finanzdokumente mit Gemini LLM umbenennen.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-mcp", dest="disable_mcp", action="store_true", default=True)
    parser.add_argument("--allow-ignored", action="store_true")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--archive-dir", type=Path, default=DEFAULT_ARCHIVE_DIR)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    args = parser.parse_args()

    print_intro()

    print(f"{'─'*70}")
    print("  🔑 ERFORDERLICHE KONFIGURATION")
    print(f"{'─'*70}\n")
    
    check_google_api_key()
    company_name = check_company_name()
    
    gemini_cmd = resolve_gemini_command()
    
    accounts_available = load_accounts_csv() is not None
    if accounts_available:
        print("  ✓ Kontenliste (accounts.csv) gefunden")
    else:
        print("  ⚠️  Kontenliste (accounts.csv) nicht gefunden - Kontonamen werden geschätzt")
    print()
    
    configure_directories(args)
    
    args.input_dir.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.archive_dir.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    (args.log_dir / "gemini_raw").mkdir(parents=True, exist_ok=True)
    
    global log, RAW_DIR
    RAW_DIR = args.log_dir / "gemini_raw"
    log_file = args.log_dir / f"{APP_NAME}.log"
    logger = logging.getLogger("processor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)
    log = logger
    
    configure_startup(args)

    files = sorted([f for f in args.input_dir.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS])
    
    if not files:
        print("Keine passenden Dateien gefunden.")
        sys.exit(0)

    if args.limit > 0:
        files = files[:args.limit]

    total_files = len(files)
    print(f"\n{'─'*70}")
    print(f"  Starte Verarbeitung: {total_files} Datei(en) mit {args.concurrency} Thread(s)")
    print()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(process_file, f, args, company_name, gemini_cmd, idx+1, total_files): f 
                   for idx, f in enumerate(files)}
        for _ in as_completed(futures): pass

    print(f"\n{'─'*70}")
    print(f"  ✓ Verarbeitung abgeschlossen!")
    print(f"  Prüfe den Ordner '{args.out_dir}' für die umbenannten Dateien.")
    
    open_choice = input(f"\n  Soll der Ordner '{args.out_dir}' geöffnet werden? (j/n): ").strip().lower()
    if open_choice in ['j', 'y', 'ja', 'yes']:
        print(f"  📂 Öffne Ordner: {args.out_dir}")
        open_directory(args.out_dir)
    
    print_copyright()


if __name__ == "__main__":
    main()
