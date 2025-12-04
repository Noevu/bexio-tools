#!/usr/bin/env python3
"""
Bexio-Tools CLI - Unified entry point for document management.
"""
import os
import sys
from pathlib import Path

# Add current directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent))

from lib import get_config, open_url, open_directory, clear_screen


# ─────────────────────────────────────────────────────────────────────────────
# INTRO & COPYRIGHT
# ─────────────────────────────────────────────────────────────────────────────

def print_intro():
    """Zeigt einen hübschen Intro Screen."""
    print("\n" + "─" * 70)
    print(" " * 18 + "🤖 BEXIO-TOOLS CLI")
    print("  Dokumentenmanagement mit KI-Unterstützung")
    print("─" * 70)


def print_copyright():
    """Zeigt Copyright-Informationen."""
    print("\n" + "─" * 70)
    print("  Copyright © Noevu GmbH – AI Lösungen für Schweizer KMU")
    print("  https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio_tools")
    print("─" * 70 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

def prompt_api_key(config):
    """Fragt nach dem Google API Key falls nicht gesetzt."""
    current = config.google_api_key
    if current:
        masked = current[:8] + "..." + current[-4:] if len(current) > 12 else "***"
        print(f"\n  Aktueller API Key: {masked}")
        change = input("  Ändern? (j/n) [n]: ").strip().lower()
        if change not in ['j', 'y', 'ja', 'yes']:
            return current
    
    url = "https://aistudio.google.com/"
    print(f"\n  💡 API Key erstellen: {url}")
    
    open_choice = input(f"  Im Browser öffnen? (j/n): ").strip().lower()
    if open_choice in ['j', 'y', 'ja', 'yes']:
        open_url(url)
    
    while True:
        api_key = input("  Google API Key [oder 'q' zum Beenden]: ").strip()
        if api_key.lower() in ['q', 'quit', 'exit']:
            print("  Bye bye 👋")
            sys.exit(0)
        if api_key:
            config.google_api_key = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
            return api_key
        print("  ⚠️  Bitte gib einen gültigen API Key ein.")


def prompt_company_name(config):
    """Fragt nach dem Firmennamen falls nicht gesetzt."""
    current = config.company_name
    if current:
        print(f"\n  Aktueller Firmenname: {current}")
        change = input("  Ändern? (j/n) [n]: ").strip().lower()
        if change not in ['j', 'y', 'ja', 'yes']:
            os.environ["COMPANY_NAME"] = current
            return current
    
    while True:
        name = input("  Firmenname [oder 'q' zum Beenden]: ").strip()
        if name.lower() in ['q', 'quit', 'exit']:
            print("  Bye bye 👋")
            sys.exit(0)
        if name:
            config.company_name = name
            os.environ["COMPANY_NAME"] = name
            return name
        print("  ⚠️  Bitte gib einen gültigen Firmennamen ein.")


def prompt_custom_prompt(config):
    """Fragt nach optionalen Custom-Prompt-Ergänzungen."""
    current = config.custom_prompt_suffix
    
    print("\n" + "─" * 70)
    print("  🎨 CUSTOM AI-ANWEISUNGEN (Optional)")
    print("─" * 70)
    
    if current:
        print(f"  Aktuelle Anweisung:")
        for line in current.split('\n'):
            print(f"    {line}")
        print()
        choice = input("  [1] Behalten  [2] Ändern  [3] Löschen: ").strip()
        if choice == "1":
            return current
        elif choice == "3":
            config.custom_prompt_suffix = ""
            print("  ✓ Custom-Anweisung gelöscht.")
            return ""
    
    print("  Hier kannst du zusätzliche Anweisungen für die KI eingeben.")
    print("  Beispiel: 'Dokumente an Noel Sidler als Privatauslage markieren.'")
    print("  Leer lassen um zu überspringen.")
    print()
    
    new_prompt = input("  Custom-Anweisung: ").strip()
    if new_prompt:
        config.custom_prompt_suffix = new_prompt
        print("  ✓ Custom-Anweisung gespeichert.")
    
    return new_prompt


def configure_settings(config):
    """Zeigt Einstellungen-Menü."""
    while True:
        clear_screen()
        print("\n" + "─" * 70)
        print("  ⚙️  EINSTELLUNGEN")
        print("─" * 70)
        
        masked_key = config.google_api_key
        if masked_key:
            masked_key = masked_key[:8] + "..." + masked_key[-4:] if len(masked_key) > 12 else "***"
        
        print(f"\n  [1] 🔑 API Key:        {masked_key or '(nicht gesetzt)'}")
        print(f"  [2] 🏢 Firmenname:     {config.company_name or '(nicht gesetzt)'}")
        print(f"  [3] 🤖 AI Modell:      {config.model}")
        print(f"  [4] ⚡ Parallelität:   {config.concurrency}")
        print(f"  [5] 🎨 Custom-Prompt:  {'✓ Gesetzt' if config.custom_prompt_suffix else '(nicht gesetzt)'}")
        print(f"\n  [6] 📁 Ordner-Einstellungen")
        print(f"\n  [0] ← Zurück zum Hauptmenü")
        print("─" * 70)
        
        choice = input("  Auswahl: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            prompt_api_key(config)
        elif choice == "2":
            prompt_company_name(config)
        elif choice == "3":
            new_model = input(f"  Neues Modell [{config.model}]: ").strip()
            if new_model:
                config.model = new_model
        elif choice == "4":
            try:
                new_conc = int(input(f"  Neue Parallelität [{config.concurrency}]: ").strip() or config.concurrency)
                if new_conc > 0:
                    config.concurrency = new_conc
            except ValueError:
                pass
        elif choice == "5":
            prompt_custom_prompt(config)
        elif choice == "6":
            configure_directories(config)


def configure_directories(config):
    """Zeigt Ordner-Einstellungen."""
    print("\n" + "─" * 70)
    print("  📁 ORDNER-EINSTELLUNGEN")
    print("─" * 70)
    
    dirs = [
        ("input_dir", "📥 Download-Ordner"),
        ("out_dir", "📝 Output-Ordner"),
        ("archive_dir", "📦 Archiv-Ordner"),
        ("log_dir", "📋 Log-Ordner")
    ]
    
    for key, label in dirs:
        current = config.get_directory(key)
        new_val = input(f"  {label} [{current}]: ").strip()
        if new_val:
            config.set_directory(key, new_val)
    
    print("  ✓ Ordner-Einstellungen gespeichert.")
    input("  Enter zum Fortfahren...")


# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOW EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def run_downloader(config):
    """Führt den Dokument-Downloader aus."""
    print("\n  📥 Starte Dokument-Downloader...")
    print("─" * 70 + "\n")
    
    if config.google_api_key:
        os.environ["GOOGLE_API_KEY"] = config.google_api_key
    if config.company_name:
        os.environ["COMPANY_NAME"] = config.company_name
    
    try:
        from tools.downloader import main as downloader_main
        downloader_main()
    except Exception as e:
        print(f"  ❌ Fehler: {e}")


def run_renamer(config):
    """Führt den AI-Renamer aus."""
    print("\n  📝 Starte AI-Renamer...")
    print("─" * 70 + "\n")
    
    if config.google_api_key:
        os.environ["GOOGLE_API_KEY"] = config.google_api_key
    if config.company_name:
        os.environ["COMPANY_NAME"] = config.company_name
    
    if config.custom_prompt_suffix:
        os.environ["CUSTOM_PROMPT_SUFFIX"] = config.custom_prompt_suffix
    
    try:
        from tools import ai_renamer
        # Need to use subprocess because of hyphens in filename
        import subprocess
        renamer_path = Path(__file__).parent / "tools" / "ai-renamer.py"
        subprocess.run([sys.executable, str(renamer_path)], check=False)
    except Exception as e:
        print(f"  ❌ Fehler: {e}")


def run_both(config):
    """Führt Download und Rename nacheinander aus."""
    run_downloader(config)
    print("\n" + "─" * 70)
    print("  ✓ Download abgeschlossen. Starte Umbenennung...")
    print("─" * 70)
    run_renamer(config)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────────────

def show_main_menu(config):
    """Zeigt das Hauptmenü."""
    default = config.default_workflow
    
    while True:
        clear_screen()
        print_intro()
        
        print("\n  🔧 HAUPTMENÜ")
        print("─" * 70)
        
        if config.company_name:
            print(f"  Firma: {config.company_name}")
        print()
        
        options = [
            ("1", "📥", "Dokumente von Bexio herunterladen", "download"),
            ("2", "📝", "Vorhandene Dokumente umbenennen", "rename"),
            ("3", "📥📝", "Herunterladen UND Umbenennen", "both"),
        ]
        
        for num, icon, label, key in options:
            default_marker = " ★" if key == default else ""
            print(f"  [{num}] {icon} {label}{default_marker}")
        
        print()
        print(f"  [4] ⚙️  Einstellungen")
        print(f"  [q] 🚪 Beenden")
        print("─" * 70)
        
        choice = input("  Auswahl: ").strip().lower()
        
        if choice == 'q':
            print_copyright()
            print("  Bye bye 👋\n")
            sys.exit(0)
        elif choice == '1':
            config.default_workflow = "download"
            run_downloader(config)
            input("\n  Enter zum Fortfahren...")
        elif choice == '2':
            config.default_workflow = "rename"
            run_renamer(config)
            input("\n  Enter zum Fortfahren...")
        elif choice == '3':
            config.default_workflow = "both"
            run_both(config)
            input("\n  Enter zum Fortfahren...")
        elif choice == '4':
            configure_settings(config)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    config = get_config()
    
    clear_screen()
    print_intro()
    
    print("\n  🔑 KONFIGURATION")
    print("─" * 70)
    
    if not config.google_api_key:
        print("  Kein API Key gefunden.")
        prompt_api_key(config)
    else:
        os.environ["GOOGLE_API_KEY"] = config.google_api_key
        print("  ✓ API Key geladen")
    
    if not config.company_name:
        print("  Kein Firmenname gefunden.")
        prompt_company_name(config)
    else:
        os.environ["COMPANY_NAME"] = config.company_name
        print(f"  ✓ Firma: {config.company_name}")
    
    if not config.custom_prompt_suffix and not config.has_required_settings():
        prompt_custom_prompt(config)
    
    show_main_menu(config)


if __name__ == "__main__":
    main()
