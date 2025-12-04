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


def main():
    parser = argparse.ArgumentParser(description="Dokumente aus Bexio herunterladen.")
    parser.add_argument("--download-dir", type=Path, default=None, help="Ordner für heruntergeladene Dateien")
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

    # --- 2. Zielpfad ermitteln ---
    default_path = get_data_dir() / 'downloads'
    
    if args.download_dir:
        path = Path(args.download_dir).resolve()
    else:
        print(f"\n{'─'*70}")
        print("  📁 ORDNER-KONFIGURATION")
        print(f"{'─'*70}")
        path_input = input(f"  Zielordner [Standard: {default_path}]: ").strip()
        
        if path_input.lower() in ['q', 'quit', 'exit', 'beenden']:
            print_copyright()
            print("  Bye bye 👋")
            sys.exit(0)

        if path_input == "":
            path = default_path
        else:
            path = Path(path_input).resolve()
        print(f"{'─'*70}\n")

    # Ordner prüfen/erstellen
    if not path.exists():
        print(f"Ordner '{path}' existiert nicht.")
        confirm = input("Soll er erstellt werden? (y/n): ").lower()
        if confirm == 'y':
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"Fehler beim Erstellen des Ordners: {e}")
                sys.exit(1)
        else:
            sys.exit(0)

    # --- 3. Option auswählen ---
    print(f"{'─'*70}")
    print("  ⚙️  DOWNLOAD-OPTIONEN")
    print(f"{'─'*70}")
    print("  1 - Alles (inklusive Archiv) [Standard]")
    print("  2 - Inbox")
    print(f"{'─'*70}")
    option_input = input("  > ").strip()
    
    if option_input.lower() in ['q', 'quit', 'exit', 'beenden']:
        print_copyright()
        print("  Bye bye 👋")
        sys.exit(0)
    
    if option_input == "":
        option_input = "1"
    
    if option_input not in ['1', '2']:
        print("Ungültige Option") 
        sys.exit()

    # --- 4. Liste anfordern ---
    url = "https://api.bexio.com/3.0/files"
    if option_input == '1':
        url += "?archived_state=all"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        print(f"\n{'─'*70}")
        print("  Lade Dateiliste...")
        print(f"{'─'*70}")
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            data = response.read()
            docs = json.loads(data)

        print(f"\n{'─'*70}")
        print(f"  ✓ {len(docs)} Dokument(e) gefunden")
        print(f"  Download nach: {path}")
        print(f"  (Drücke Ctrl+C zum Abbrechen)")
        print()

        # --- 5. Parallel Download ---
        downloaded = 0
        failed = 0
        total = len(docs)
        lock = threading.Lock()
        
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
        
        # Download with up to 20 parallel threads
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(download_file, doc) for doc in docs]
            for _ in as_completed(futures):
                pass  # Results handled in download_file
        
        if failed > 0:
            print(f"\n  ⚠️  {failed} Datei(en) fehlgeschlagen")

    except KeyboardInterrupt:
        print("\n\n" + "─" * 70)
        print("  ⚠️  Download abgebrochen")
        print_copyright()
        sys.exit(0)
    except urllib.error.HTTPError as e:
        print(f"\n{'─'*70}")
        print(f"  ❌ HTTP-Fehler: {e.code} - {e.reason}")
        if e.code == 401:
            print("  Der Token ist ungültig oder abgelaufen.")
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
    if renamer_script.exists():
        print(f"\n{'─'*70}")
        print("  🤖 AI RENAMER")
        print(f"{'─'*70}")
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
