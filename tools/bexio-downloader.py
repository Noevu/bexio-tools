#!/usr/bin/env python3
"""
Bexio document downloader - Downloads documents from Bexio API.
"""
import os
import json
import logging
import re
import sys
import urllib.request
import urllib.error
import argparse
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

# Enable readline for better input editing (arrow keys, cursor movement)
try:
    import readline
except ImportError:
    pass  # readline not available on Windows

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.utils import open_url, open_directory, get_data_dir, clear_screen, get_project_root, print_copyright


debug_logger = None


def sanitize_filename(name):
    """Ersetzt Zeichen, die in Windows-/Unix-Dateinamen ungültig sind, durch Unterstriche."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def print_intro():
    """Zeigt einen hübschen Intro Screen."""
    clear_screen()
    print("\n" + "─" * 70)
    print("  ⬇️  BEXIO DOKUMENTE DOWNLOADER")
    print("  Download von Dokumenten aus Bexio")
    print("\n  💡 Tipp: Du kannst jederzeit mit 'q' abbrechen")
    print()


def print_token_help():
    url = "https://developer.bexio.com/pat"
    print("\n" + "-" * 70)
    print("  KEIN TOKEN GEFUNDEN. ANLEITUNG:")
    print("-" * 70)
    print(f"  1. Gehe zu: {url}")
    print("  2. Melde dich mit deinen Bexio-Zugangsdaten an.")
    print("  3. Klicke auf 'Generate Token'.")
    print("  4. Vergib dem Token einen Namen (z. B. 'Downloader') und wähle die Firma aus.")
    print("  5. Kopiere die generierte Token-Zeichenfolge.")
    print("\n  (Hinweis: PATs haben dieselbe Rechte wie dein Benutzer. Bewahre sie geheim auf!)")
    print("-" * 70)
    
    open_choice = input(f"\n  Soll {url} im Browser geöffnet werden? (j/n): ").strip().lower()
    if open_choice in ['j', 'y', 'ja', 'yes']:
        print(f"  🔗 Öffne {url} im Browser...")
        open_url(url)
    print()


def fetch_files_from_bexio(token, url, data=None):
    """Holt die Dateiliste von der Bexio API, unterstützt GET und POST (für Suche)."""
    global debug_logger
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    request_data = json.dumps(data).encode('utf-8') if data else None
    
    method = 'POST' if data else 'GET'
    req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

    if debug_logger:
        request_log = f"REQUEST: {method} {url}\nHeaders: {json.dumps(headers, indent=2)}"
        if data:
            request_log += f"\nBody: {json.dumps(data, indent=2)}"
        debug_logger.debug(request_log)

    with urllib.request.urlopen(req) as response:
        response_data = response.read()
        
        if debug_logger:
            response_log = f"RESPONSE: {response.getcode()}\n"
            try:
                # Try to pretty-print if it's JSON
                parsed_json = json.loads(response_data)
                pretty_response = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                response_log += pretty_response
            except (json.JSONDecodeError, TypeError):
                # If not JSON, log as is
                response_log += response_data.decode('utf-8', errors='ignore')
            debug_logger.debug(response_log)

        return json.loads(response_data)


def download_files_in_parallel(docs, path, token):
    """Lädt eine Liste von Dokumenten parallel herunter."""
    downloaded = 0
    failed = 0
    total = len(docs)
    lock = threading.Lock()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    print(f"\n{'─'*70}")
    print(f"  ✓ {total} Dokument(e) gefunden")
    print(f"  Download nach: {get_display_path(path)}")
    print(f"  (Drücke Ctrl+C zum Abbrechen)")
    print()
    
    def download_file(doc):
        nonlocal downloaded, failed
        raw_name = f"{doc.get('name')}.{doc.get('extension')}"
        original_filename = sanitize_filename(raw_name)
        
        filename_to_try = original_filename
        counter = 1
        
        while True:
            full_path = path / filename_to_try
            try:
                # Use exclusive creation mode 'x' to atomically create the file.
                # This prevents race conditions in parallel downloads.
                with open(full_path, 'xb') as f:
                    file_id = doc.get('id')
                    download_url = f"https://api.bexio.com/3.0/files/{file_id}/download"
                    
                    dl_req = urllib.request.Request(download_url, headers=headers)
                    with urllib.request.urlopen(dl_req) as dl_response:
                        f.write(dl_response.read())

                with lock:
                    downloaded += 1
                    print(f"  ✓ [{downloaded}/{total}] {filename_to_try}")
                return True

            except FileExistsError:
                # If file exists, generate a new name and retry.
                stem = Path(original_filename).stem
                suffix = Path(original_filename).suffix
                filename_to_try = f"{stem}_{counter}{suffix}"
                counter += 1
            
            except Exception as e:
                with lock:
                    failed += 1
                    print(f"  ❌ {filename_to_try}: {e}")
                
                # If we created a file but the download failed, try to clean it up.
                if full_path.exists():
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass # Ignore cleanup errors, it's not critical.
                return False
            
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(download_file, doc) for doc in docs]
        for _ in as_completed(futures):
            pass
            
    if failed > 0:
        print(f"\n  ⚠️  {failed} Datei(en) fehlgeschlagen")

def get_display_path(abs_path: Path) -> str:

    project_root = get_project_root()

    try:

        return str(abs_path.relative_to(project_root))

    except ValueError:

        return str(abs_path)





def ask_archive_status():

    """Asks user for archive status and returns the API string."""

    print()

    print("  Welchen Archiv-Status sollen die durchsuchten Dateien haben?")

    print("  [1] Alle (inkl. archivierte) [Standard]")

    print("  [2] Nur aus der Inbox (nicht archiviert)")

    print("  [3] Nur archivierte")

    choice = input("  > ").strip() or "1"

    

    if choice == '2':

        return "not_archived"

    elif choice == '3':

        return "archived"

    else:

        return "all"



def ask_referenced_status():

    """Asks user for referenced status and returns a search criterion dict or None."""

    print()

    print("  Sollen alle oder nur mit Belegen verknüpfte Dateien berücksichtigt werden?")

    print("  [1] Alle Dateien (egal ob verknüpft oder nicht) [Standard]")

    print("  [2] Nur verknüpfte Dateien")

    print("  [3] Nur NICHT verknüpfte Dateien")

    choice = input("  > ").strip() or "1"

    

    if choice == '2':

        return {"field": "is_referenced", "value": True, "criteria": "="}

    elif choice == '3':

        return {"field": "is_referenced", "value": False, "criteria": "="}

    else:

        return None





def main():
    parser = argparse.ArgumentParser(
        description="Dokumente aus Bexio herunterladen.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    parser.add_argument("--download-dir", type=Path, default=None, help="Ordner für heruntergeladene Dateien (Standard: data/downloads).")
    
    # Gruppe für Download-Modi, die sich gegenseitig ausschliessen
    mode_group = parser.add_argument_group('Download Modi')
    mode_group.add_argument("--name", type=str, help="Dateiname: Lade Dateien, die den Suchbegriff im Namen enthalten.")
    mode_group.add_argument("--date-range", type=str, nargs=2, metavar=('START_DATE', 'END_DATE'), help="Datum (JJJJ-MM-TT): Lade Dateien innerhalb eines Zeitraums.")
    mode_group.add_argument("--since", type=str, help="Datum (JJJJ-MM-TT): Lade nur Dateien, die seit diesem Datum erstellt wurden.")
    mode_group.add_argument("--days", type=int, help="Anzahl Tage: Lade nur Dateien aus den letzten X Tagen.")
    mode_group.add_argument("--latest", type=int, help="Anzahl: Lade die X neuesten Dateien.")
    mode_group.add_argument("--all", action='store_true', help="Lade alle Dateien (inkl. archivierte).")
    mode_group.add_argument("--not-archived", action='store_true', help="Lade nur nicht-archivierte Dateien.")
    mode_group.add_argument("--inbox", action='store_true', help="Lade nur Dateien aus der Inbox.")

    parser.add_argument("--debug", action='store_true', help="Aktiviert das Debug-Logging für die Bexio API-Antworten.")

    args = parser.parse_args()

    # --- Debug Logger Setup ---
    global debug_logger
    if args.debug:
        from lib.logger import setup_debug_logger
        debug_logger = setup_debug_logger()
        print(f"  🐞 Debug-Modus aktiviert. API-Antworten werden in 'data/logs/bexio-api-debug.log' geloggt.\n")
    
    print_intro()
    
    # --- 1. Token abrufen ---
    token = os.environ.get('BEXIO_ACCESS_TOKEN')
    
    if not token:
        print_token_help()
        while True:
            token = input("Bitte gib den Personal Access Token ein [oder 'q' zum Beenden]: ").strip()
            if token.lower() in ['q', 'quit', 'exit', 'beenden']:
                print_copyright()
                print("  Bye bye 👋")
                sys.exit(0)
            if token:
                break
            print("  ⚠️  Bitte gib einen gültigen Token ein oder 'q' zum Beenden.")

    # --- 2. Zielpfad ermitteln & erstellen ---
    default_path = get_data_dir() / 'downloads'
    run_interactively = not any([args.name, args.date_range, args.since, args.days, args.latest, args.all, args.inbox, args.not_archived])

    if args.download_dir:
        path = Path(args.download_dir).resolve()
    else:
        path = default_path
    
    if run_interactively:
        print(f"\n{'─'*70}")
        print("  📁 ORDNER-KONFIGURATION")
        print(f"{'─'*70}")
        if args.download_dir:
             print(f"  Zielordner: {path} (via --download-dir)")
        else:
             print(f"  Zielordner: {path} (Standard)")
        print(f"{'-'*70}\n")
    else:
        print(f"  📁 Zielordner: {path}")


    # Ordner prüfen/erstellen
    if not path.exists():
        if run_interactively:
            print(f"Ordner '{path}' existiert nicht.")
            confirm = input("Soll er erstellt werden? (j/n): ").lower()
            if confirm in ['j', 'y', 'ja', 'yes']:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    print(f"Fehler beim Erstellen des Ordners: {e}")
                    sys.exit(1)
            else:
                sys.exit(0)
        else: # Non-interactive
            print(f"  -> Ordner '{path}' existiert nicht, wird erstellt.")
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"  ❌ Fehler beim Erstellen des Ordners: {e}")
                sys.exit(1)
    
    docs = []
    
    try:
        print(f"\n{'─'*70}")
        print("  Lade Dateiliste...")
        print(f"{'-'*70}")
        
        # --- 3. Modus bestimmen und Dateien abrufen ---
        url = "https://api.bexio.com/3.0/files"
        search_payload = None

        # Modus via CLI-Argumente
        if args.name:
            url = "https://api.bexio.com/3.0/files/search"
            search_payload = [{"field": "name", "value": args.name, "criteria": "like"}]
            docs = fetch_files_from_bexio(token, url, data=search_payload)

        elif args.date_range:
            url = "https://api.bexio.com/3.0/files/search"
            try:
                start_date = datetime.strptime(args.date_range[0], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                end_date = datetime.strptime(args.date_range[1], '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                search_payload = [
                    {"field": "created_at", "value": start_date.isoformat(), "criteria": ">="},
                    {"field": "created_at", "value": end_date.isoformat(), "criteria": "<="}
                ]
                docs = fetch_files_from_bexio(token, url, data=search_payload)
            except ValueError:
                print("❌ Ungültiges Datumsformat für --date-range. Bitte JJJJ-MM-TT verwenden.")
                sys.exit(1)
        
        elif args.since or args.days:
            url = "https://api.bexio.com/3.0/files/search"
            date_obj = None
            if args.since:
                try:
                    date_obj = datetime.strptime(args.since, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                except ValueError:
                    print("❌ Ungültiges Datumsformat. Bitte JJJJ-MM-TT verwenden.")
                    sys.exit(1)
            elif args.days:
                date_obj = (datetime.now(timezone.utc) - timedelta(days=args.days)).replace(hour=0, minute=0, second=0, microsecond=0)

            if date_obj:
                search_payload = [{"field": "created_at", "value": date_obj.isoformat(), "criteria": ">="}]
                docs = fetch_files_from_bexio(token, url, data=search_payload)

        elif args.latest:
            url += f"?limit={args.latest}&order_by=id_desc" # Annahme: id_desc sortiert nach neuesten
            docs = fetch_files_from_bexio(token, url)
            
        elif args.all:
            url += "?archived_state=all"
            docs = fetch_files_from_bexio(token, url)
            
        elif args.not_archived:
            url += "?archived_state=not_archived"
            docs = fetch_files_from_bexio(token, url)

        elif args.inbox:
             docs = fetch_files_from_bexio(token, url)

        # Interaktiver Modus
        else:
            print("  ⚙️  DOWNLOAD-OPTIONEN")
            print(f"{'-'*70}")
            print("  [1] ✅ Alle Dateien herunterladen (inkl. Archiv)")
            print("  [2] 📥 Nur Inbox herunterladen (nicht archiviert)")
            print("  [3] 🗃️  Nur archivierte Dateien herunterladen")
            print("\n  --- Nach Kriterien filtern ---")
            print("  [4] 🗓️  Dateien seit Datum...")
            print("  [5] 📅 Dateien aus den letzten X Tagen...")
            print("  [6] 🔢 Die letzten X Dateien...")
            print("  [7] ⏳ Dateien in Zeitraum...")
            print("  [8] 🔍 Dateien nach Name suchen...")
            print(f"{'-'*70}")
            option = input("  > ").strip()

            if option.lower() in ['q', 'quit', 'exit', 'beenden']:
                print_copyright()
                sys.exit(0)

            # Direct downloads
            if option == '1':
                url += "?archived_state=all"
                docs = fetch_files_from_bexio(token, url)
            elif option == '2':
                url += "?archived_state=not_archived"
                docs = fetch_files_from_bexio(token, url)
            elif option == '3':
                url += "?archived_state=archived"
                docs = fetch_files_from_bexio(token, url)
            
            # Filtered searches
            else:
                search_payload = []
                # Get primary filter criteria
                if option == '4': # Seit Datum
                    date_input = input("  Datum (JJJJ-MM-TT): ").strip()
                    try:
                        date_obj = datetime.strptime(date_input, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                        search_payload.append({"field": "created_at", "value": date_obj.isoformat(), "criteria": ">="})
                    except ValueError:
                        print("❌ Ungültiges Datumsformat.")
                        sys.exit(1)

                elif option == '5': # Letzte X Tage
                    days_input = input("  Anzahl Tage: ").strip()
                    try:
                        days = int(days_input)
                        date_obj = (datetime.now(timezone.utc) - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
                        search_payload.append({"field": "created_at", "value": date_obj.isoformat(), "criteria": ">="})
                    except ValueError:
                        print("❌ Ungültige Eingabe. Bitte eine Zahl eingeben.")
                        sys.exit(1)

                elif option == '7': # Zeitraum
                    start_date_input = input("  Start-Datum (JJJJ-MM-TT): ").strip()
                    end_date_input = input("  End-Datum (JJJJ-MM-TT): ").strip()
                    try:
                        start_date = datetime.strptime(start_date_input, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                        end_date = datetime.strptime(end_date_input, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                        search_payload.extend([
                            {"field": "created_at", "value": start_date.isoformat(), "criteria": ">="},
                            {"field": "created_at", "value": end_date.isoformat(), "criteria": "<="}
                        ])
                    except ValueError:
                        print("❌ Ungültiges Datumsformat.")
                        sys.exit(1)
                
                elif option == '8': # Nach Name
                    name_input = input("  Dateiname (oder Teil davon): ").strip()
                    if name_input:
                        search_payload.append({"field": "name", "value": name_input, "criteria": "like"})
                    else:
                        print("❌ Kein Suchbegriff eingegeben.")
                        sys.exit(1)

                # --- Handle search execution ---
                if option in ['4', '5', '7', '8']:
                    archive_state = ask_archive_status()
                    ref_criterion = ask_referenced_status()
                    if ref_criterion:
                        search_payload.append(ref_criterion)
                    
                    search_url = f"https://api.bexio.com/3.0/files/search?archived_state={archive_state}"
                    docs = fetch_files_from_bexio(token, search_url, data=search_payload)
                
                elif option == '6': # Letzte X Dateien - special handling
                    count_input = input("  Anzahl Dateien: ").strip()
                    try:
                        count = int(count_input)
                        # NOTE: "is_referenced" cannot be filtered with this endpoint, only archive status.
                        archive_state = ask_archive_status()
                        
                        url += f"?limit={count}&order_by=id_desc&archived_state={archive_state}"
                        docs = fetch_files_from_bexio(token, url)
                    except ValueError:
                        print("❌ Ungültige Eingabe. Bitte eine Zahl eingeben.")
                        sys.exit(1)
                
                # Options 1-3 were already handled, so we just check for invalid input here.
                elif option not in ['1','2','3']:
                    print("Ungültige Option")
                    sys.exit()

        # --- 4. Download ---
        if docs:
            download_files_in_parallel(docs, path, token)
        else:
            print(f"\n{'─'*70}")
            print("  Keine Dokumente für die Auswahl gefunden.")

    except KeyboardInterrupt:
        print("\n\n" + "─" * 70)
        print("  ⚠️  Download abgebrochen")
        sys.exit(0)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\n{'─'*70}")
        print(f"  ❌ HTTP-Fehler: {e.code} - {e.reason}")
        if e.code == 401:
            print("  Der Token ist ungültig oder abgelaufen.")
        else:
            print(f"  Server-Antwort: {body}")

    except Exception as e:
        print(f"\n{'─'*70}")
        print(f"  ❌ Fehler: {e}")

    print(f"\n{'─'*70}")
    print("  ✓ Download abgeschlossen!")
    
    open_choice = input(f"\n  Möchten Sie die heruntergeladenen Dateien anzeigen? (j/n): ").strip().lower()
    if open_choice in ['j', 'y', 'ja', 'yes']:
        print(f"  📂 Öffne Ordner: {path}")
        open_directory(path)

    # Frage ob AI Renamer gestartet werden soll
    renamer_script = Path(__file__).parent / "ai-renamer.py"
    if renamer_script.exists() and docs: # Nur fragen wenn Dateien geladen wurden
        print(f"\n{'─'*70}")
        print("  🤖 AI RENAMER")
        print(f"{'-'*70}")
        rename_choice = input("  Möchtest du die heruntergeladenen Dateien jetzt mit AI umbenennen? (j/n): ").strip().lower()
        if rename_choice in ['j', 'y', 'ja', 'yes']:
            print(f"\n  🚀 Starte AI Renamer...")
            try:
                import subprocess
                subprocess.run([sys.executable, str(renamer_script), "--input-dir", str(path)], check=False)
            except Exception as e:
                print(f"  ❌ Fehler beim Starten des Renamers: {e}")
    
    print_copyright()


if __name__ == "__main__":
    main()