#!/usr/bin/env python3
"""
Bexio document downloader - Downloads documents from Bexio API.
"""
import os
import json
import re
import sys
import urllib.request
import urllib.error
import argparse
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

# Enable readline for better input editing (arrow keys, cursor movement)
try:
    import readline
except ImportError:
    pass  # readline not available on Windows

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.utils import open_url, open_directory, get_data_dir


def sanitize_filename(name):
    """Ersetzt Zeichen, die in Windows-/Unix-Dateinamen ungültig sind, durch Unterstriche."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def print_intro():
    """Zeigt einen hübschen Intro Screen."""
    print("\n" + "─" * 70)
    print(" " * 15 + "⬇️  BEXIO DOKUMENTE DOWNLOADER")
    print("  Download von Dokumenten aus Bexio")
    print("\n  💡 Tipp: Du kannst jederzeit mit 'q' abbrechen")
    print()


def print_copyright():
    """Zeigt Copyright-Informationen."""
    print("\n" + "-" * 70)
    print("  Copyright © Noevu GmbH – AI Lösungen für Schweizer KMU")
    print("  https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio_downloader")
    print("-" * 70 + "\n")


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
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    request_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(url, data=request_data, headers=headers, method='POST' if data else 'GET')
    
    with urllib.request.urlopen(req) as response:
        response_data = response.read()
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
    print(f"  Download nach: {path}")
    print(f"  (Drücke Ctrl+C zum Abbrechen)")
    print()
    
    def download_file(doc):
        nonlocal downloaded, failed
        raw_name = f"{doc.get('name')}.{doc.get('extension')}"
        filename = sanitize_filename(raw_name)
        full_path = path / filename
        
        file_id = doc.get('id')
        download_url = f"https://api.bexio.com/3.0/files/{file_id}/download"
        
        try:
            dl_req = urllib.request.Request(download_url, headers=headers)
            with urllib.request.urlopen(dl_req) as dl_response:
                with open(str(full_path), 'wb') as f:
                    f.write(dl_response.read())
            
            with lock:
                downloaded += 1
                print(f"  ✓ [{downloaded}/{total}] {filename}")
            return True
        except Exception as e:
            with lock:
                failed += 1
                print(f"  ❌ {filename}: {e}")
            return False
            
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(download_file, doc) for doc in docs]
        for _ in as_completed(futures):
            pass
            
    if failed > 0:
        print(f"\n  ⚠️  {failed} Datei(en) fehlgeschlagen")

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

    args = parser.parse_args()
    
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
        print(f"{'-'*70}")
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
                start_date_str = datetime.strptime(args.date_range[0], '%Y-%m-%d').strftime('%Y-%m-%d')
                end_date_str = datetime.strptime(args.date_range[1], '%Y-%m-%d').strftime('%Y-%m-%d')
                search_payload = [
                    {"field": "created_at", "value": start_date_str, "criteria": ">="},
                    {"field": "created_at", "value": end_date_str, "criteria": "<="}
                ]
                docs = fetch_files_from_bexio(token, url, data=search_payload)
            except ValueError:
                print("❌ Ungültiges Datumsformat für --date-range. Bitte JJJJ-MM-TT verwenden.")
                sys.exit(1)
        
        elif args.since or args.days:
            url = "https://api.bexio.com/3.0/files/search"
            date_str = ""
            if args.since:
                try:
                    date_str = datetime.strptime(args.since, '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    print("❌ Ungültiges Datumsformat. Bitte JJJJ-MM-TT verwenden.")
                    sys.exit(1)
            elif args.days:
                date_obj = datetime.now() - timedelta(days=args.days)
                date_str = date_obj.strftime('%Y-%m-%d')
            
            search_payload = [{"field": "created_at", "value": f"{date_str}", "criteria": ">="}]
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
            print("  [1] ✅ Alles (inklusive Archiv)")
            print("  [2] 📥 Inbox [Standard]")
            print("  [3] 🗃️ Nur nicht archivierte")
            print("  [4] 🗓️ Dateien seit Datum...")
            print("  [5] 📅 Dateien der letzten X Tage...")
            print("  [6] 6️⃣ Letzte X Dateien...")
            print("  [7] ⏳ Dateien in Zeitraum...")
            print("  [8] 🔍 Dateien nach Name suchen...")
            print(f"{'-'*70}")
            option_input = input("  > ").strip()

            if option_input.lower() in ['q', 'quit', 'exit', 'beenden']:
                print_copyright()
                sys.exit(0)
            
            option = option_input or "1"

            if option == '1':
                url += "?archived_state=all"
                docs = fetch_files_from_bexio(token, url)
            elif option == '2':
                docs = fetch_files_from_bexio(token, url)
            elif option == '3':
                url += "?archived_state=not_archived"
                docs = fetch_files_from_bexio(token, url)
            elif option == '4':
                date_input = input("  Datum (JJJJ-MM-TT): ").strip()
                try:
                    date_str = datetime.strptime(date_input, '%Y-%m-%d').strftime('%Y-%m-%d')
                    search_payload = [{"field": "created_at", "value": date_str, "criteria": ">="}]
                    docs = fetch_files_from_bexio(token, "https://api.bexio.com/3.0/files/search", data=search_payload)
                except ValueError:
                    print("❌ Ungültiges Datumsformat.")
                    sys.exit(1)
            elif option == '5':
                days_input = input("  Anzahl Tage: ").strip()
                try:
                    days = int(days_input)
                    date_obj = datetime.now() - timedelta(days=days)
                    date_str = date_obj.strftime('%Y-%m-%d')
                    search_payload = [{"field": "created_at", "value": date_str, "criteria": ">="}]
                    docs = fetch_files_from_bexio(token, "https://api.bexio.com/3.0/files/search", data=search_payload)
                except ValueError:
                    print("❌ Ungültige Eingabe. Bitte eine Zahl eingeben.")
                    sys.exit(1)
            elif option == '6':
                count_input = input("  Anzahl Dateien: ").strip()
                try:
                    count = int(count_input)
                    url += f"?limit={count}&order_by=id_desc" # Annahme
                    docs = fetch_files_from_bexio(token, url)
                except ValueError:
                    print("❌ Ungültige Eingabe. Bitte eine Zahl eingeben.")
                    sys.exit(1)
            elif option == '7':
                start_date_input = input("  Start-Datum (JJJJ-MM-TT): ").strip()
                end_date_input = input("  End-Datum (JJJJ-MM-TT): ").strip()
                try:
                    start_date_str = datetime.strptime(start_date_input, '%Y-%m-%d').strftime('%Y-%m-%d')
                    end_date_str = datetime.strptime(end_date_input, '%Y-%m-%d').strftime('%Y-%m-%d')
                    search_payload = [
                        {"field": "created_at", "value": start_date_str, "criteria": ">="},
                        {"field": "created_at", "value": end_date_str, "criteria": "<="}
                    ]
                    docs = fetch_files_from_bexio(token, "https://api.bexio.com/3.0/files/search", data=search_payload)
                except ValueError:
                    print("❌ Ungültiges Datumsformat.")
                    sys.exit(1)
            elif option == '8':
                name_input = input("  Dateiname (oder Teil davon): ").strip()
                if name_input:
                    search_payload = [{"field": "name", "value": name_input, "criteria": "like"}]
                    docs = fetch_files_from_bexio(token, "https://api.bexio.com/3.0/files/search", data=search_payload)
                else:
                    print("❌ Kein Suchbegriff eingegeben.")
                    sys.exit(1)
            else:
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
        print_copyright()
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
    
    open_choice = input(f"\n  Soll der Ordner '{path}' geöffnet werden? (j/n): ").strip().lower()
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