#!/usr/bin/env python3
"""
Bexio-Tools CLI - Unified entry point for document management.
"""
import os
import sys
from pathlib import Path

# Enable readline for better input editing (arrow keys, cursor movement)
try:
    import readline
except ImportError:
    pass  # readline not available on Windows

# Add current directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent))

from lib import get_config, open_url, open_directory, clear_screen


# ─────────────────────────────────────────────────────────────────────────────
# INTRO & COPYRIGHT
# ─────────────────────────────────────────────────────────────────────────────

def print_intro():
    """Zeigt einen hübschen Intro Screen."""
    print("\n\n" + "=" * 70)
    print("  🤖 BEXIO-TOOLS")
    print("  Dokumentenmanagement mit KI-Unterstützung")
    print("=" * 70)


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
            print_copyright()
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
            print_copyright()
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
    """Zeigt das detaillierte Einstellungsmenü, in dem jede Option einzeln geändert werden kann."""
    while True:
        clear_screen()
        print("\n" + "─" * 70)
        print("  ⚙️  EINSTELLUNGEN ANPASSEN")
        print("─" * 70)
        
        # Mask API key for display
        masked_api = config.google_api_key or ""
        if masked_api:
            masked_api = masked_api[:8] + "..." + masked_api[-4:] if len(masked_api) > 12 else "***"

        # Mask Bexio token for display
        masked_bexio = ""
        try:
            bex = config.get("bexio_access_token", "")
            if bex:
                masked_bexio = bex[:8] + "..." + bex[-4:] if len(bex) > 12 else "***"
        except Exception:
            masked_bexio = "(nicht abrufbar)"

        print("\n  Wähle die Einstellung, die du ändern möchtest:\n")
        print(f"  [1] 🏢 Firmenname:      {config.company_name or '(nicht gesetzt)'}")
        print(f"  [2] 🔑 API Key:         {masked_api or '(nicht gesetzt)'}")
        print(f"  [3] 🔐 Bexio Token:     {masked_bexio or '(wird bei Bedarf gefragt)'}")
        print(f"  [4] 🤖 AI Modell:       {config.model}")
        print(f"  [5] ⚡ Parallelität:    {config.concurrency}")
        print(f"  [6] ⭐ Default Workflow: {config.default_workflow or '(nicht gesetzt)'}")
        print(f"  [7] 🎨 Custom Prompt:   {'✓ Gesetzt' if config.custom_prompt_suffix else '(nicht gesetzt)'}")
        print(f"  [8] 📁 Ordner")
        print("\n  [0] ← Zurück zum Hauptmenü")
        print("─" * 70)
        
        choice = input("  Auswahl: ").strip()
        
        if choice in ["0", ""]:
            break
        elif choice == "1":
            prompt_company_name(config)
        elif choice == "2":
            prompt_api_key(config)
        elif choice == "3":
            new_token = input("  Neuer Bexio Token [leer lassen zum Abbrechen]: ").strip()
            if new_token:
                config.set("bexio_access_token", new_token)
        elif choice == "4":
            new_model = input(f"  Neues AI Modell [{config.model}]: ").strip()
            if new_model:
                config.model = new_model
        elif choice == "5":
            try:
                new_conc_str = input(f"  Neue Parallelität [{config.concurrency}]: ").strip()
                if new_conc_str:
                    new_conc = int(new_conc_str)
                    if new_conc > 0:
                        config.concurrency = new_conc
            except (ValueError, TypeError):
                print("  ⚠️ Ungültige Zahl. Parallelität nicht geändert.")
                input("  Enter zum Fortfahren...")
        elif choice == "6":
            print("  Mögliche Workflows: 'download', 'rename', 'both'")
            new_default = input(f"  Neuer Default Workflow [{config.default_workflow}]: ").strip().lower()
            if new_default in ["download", "rename", "both", ""]:
                config.default_workflow = new_default
        elif choice == "7":
            prompt_custom_prompt(config)
        elif choice == "8":
            configure_directories(config)
        else:
            print("  ⚠️ Ungültige Auswahl.")
            input("  Enter zum Fortfahren...")


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
    print("\n  📥 Starte Dokument-Exporter...")
    print("─" * 70 + "\n")
    
    if config.google_api_key:
        os.environ["GOOGLE_API_KEY"] = config.google_api_key
    if config.company_name:
        os.environ["COMPANY_NAME"] = config.company_name
    
    try:
        import subprocess
        downloader_path = Path(__file__).parent / "tools" / "bexio-document-exporter.py"
        subprocess.run([sys.executable, str(downloader_path)], check=False)
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
        import subprocess
        renamer_path = Path(__file__).parent / "tools" / "ai-renamer.py"
        subprocess.run([sys.executable, str(renamer_path)], check=False)
    except Exception as e:
        print(f"  ❌ Fehler: {e}")


def run_both(config):
    """Führt Download und Rename nacheinander aus."""
    run_downloader(config)
    print("\n" + "─" * 70)
    print("  ✅ Download abgeschlossen. Starte Umbenennung...")
    print("─" * 70)
    run_renamer(config)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────────────

def show_main_menu(config):
    """Zeigt das Hauptmenü an, nachdem die grundlegende Konfiguration abgeschlossen ist."""
    while True:
        clear_screen()
        print_intro()
        
        company_name = getattr(config, 'company_name', 'Benutzer')
        print(f"\n\n  Hallo {company_name} 👋 was möchtest du tun? \n\n")
        
        default = config.default_workflow
        options = [
            ("1", "📥", "Dokumente von Bexio herunterladen", "download"),
            ("2", "🤖", "Vorhandene Dokumente mit AI umbenennen", "rename"),
            ("3", "📥 + 🤖", "Herunterladen UND Umbenennen", "both"),
        ]

        for num, icon, label, key in options:
            default_marker = " ★" if key == default else ""
            print(f"  [{num}] {icon} {label}{default_marker}")
        
        print()
        print(f"  [e] ⚙️  Einstellungen anpassen")
        print(f"  [q] 👋 Beenden")
        print("\n")
        
        choice = input("  Auswahl: ").strip().lower()
        
        if choice == 'q':
            print_copyright()
            print("  Bye bye 👋\n")
            sys.exit(0)
        elif choice == '1':
            config.default_workflow = "download"
            run_downloader(config)
            input("\n  Enter zum Hauptmenü...")
        elif choice == '2':
            config.default_workflow = "rename"
            run_renamer(config)
            input("\n  Enter zum Hauptmenü...")
        elif choice == '3':
            config.default_workflow = "both"
            run_both(config)
            input("\n  Enter zum Hauptmenü...")
        elif choice == 'e':
            configure_settings(config)
        else:
            print("\n  ⚠️  Ungültige Auswahl.")
            input("  Enter zum Wiederholen...")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def check_and_use_env_key(env_names: list, key_label: str, config_getter, config_setter):
    """
    Prüft ob ein Key in env vars vorhanden ist und fragt ob er verwendet werden soll.
    Returns: (key_value, was_set)
    """
    # Check environment variables
    env_value = None
    for env_name in env_names:
        env_value = os.environ.get(env_name)
        if env_value:
            break
    
    # Check saved config
    saved_value = config_getter()
    
    if env_value:
        masked = env_value[:8] + "..." + env_value[-4:] if len(env_value) > 12 else "***"
        print(f"  {key_label} gefunden (Umgebungsvariable): {masked}")
        use_it = input("  Verwenden? (J/n): ").strip().lower()
        if use_it not in ['n', 'nein', 'no']:
            config_setter(env_value)
            return env_value, True
    elif saved_value:
        masked = saved_value[:8] + "..." + saved_value[-4:] if len(saved_value) > 12 else "***"
        print(f"  {key_label} gefunden (gespeichert): {masked}")
        use_it = input("  Verwenden? (J/n): ").strip().lower()
        if use_it not in ['n', 'nein', 'no']:
            return saved_value, True
    
    return None, False


def prompt_for_key(key_label: str, help_url: str, config_setter):
    """Fragt nach einem Key wenn keiner gefunden wurde."""
    print(f"\n  💡 {key_label} erstellen: {help_url}")
    
    open_choice = input(f"  Im Browser öffnen? (j/n): ").strip().lower()
    if open_choice in ['j', 'y', 'ja', 'yes']:
        open_url(help_url)
    
    while True:
        key = input(f"  {key_label} [oder 'q' zum Beenden]: ").strip()
        if key.lower() in ['q', 'quit', 'exit']:
            print_copyright()
            print("  Bye bye 👋")
            sys.exit(0)
        if key:
            config_setter(key)
            return key
        print(f"  ⚠️  Bitte gib einen gültigen {key_label} ein.")


def main():
    """Main entry point."""
    config = get_config()
    
    # Standard-Parallelität sicherstellen: Default = 20
    if not getattr(config, "concurrency", None) or int(getattr(config, "concurrency", 0)) <= 0:
        config.concurrency = 20
    
    # Prüfen, ob eine Erstkonfiguration notwendig ist
    if not config.company_name or not config.google_api_key:
        clear_screen()
        print_intro()
        print("\n  Willkommen! Lass uns die Ersteinrichtung durchführen.")
        
        # 1. FIRMENNAME
        prompt_company_name(config)
        
        # 2. GOOGLE API KEY
        prompt_api_key(config)
        
        print("\n  ✓ Ersteinrichtung abgeschlossen!")
        input("  Enter um zum Hauptmenü zu gelangen...")

    # Nach der Einrichtung (oder wenn sie schon existiert) das Hauptmenü anzeigen
    show_main_menu(config)


if __name__ == "__main__":
    main()

