#!/usr/bin/env python3
"""
Shared utilities for Bexio-Tools.
"""
import os
import platform
import subprocess
from pathlib import Path


def open_url(url: str):
    """Öffnet eine URL im Standard-Browser."""
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", url], check=False)
        elif system == "Windows":
            subprocess.run(["start", url], check=False, shell=True)
        else:
            subprocess.run(["xdg-open", url], check=False)
    except Exception:
        pass


def open_file(filepath: Path):
    """Öffnet eine Datei mit der Standard-Anwendung."""
    try:
        system = platform.system()
        file_path_str = str(filepath.resolve())
        if system == "Darwin":
            subprocess.run(["open", file_path_str], check=False)
        elif system == "Windows":
            subprocess.run(["start", file_path_str], check=False, shell=True)
        else:
            subprocess.run(["xdg-open", file_path_str], check=False)
    except Exception:
        pass


def open_directory(dirpath: Path):
    """Öffnet einen Ordner im Datei-Explorer/Finder."""
    try:
        system = platform.system()
        dir_path_str = str(dirpath.resolve())
        if system == "Darwin":
            subprocess.run(["open", dir_path_str], check=False)
        elif system == "Windows":
            subprocess.run(["explorer", dir_path_str], check=False)
        else:
            subprocess.run(["xdg-open", dir_path_str], check=False)
    except Exception:
        pass


def clear_screen():
    """Bildschirm leeren."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def set_finder_comment(filepath: Path, comment: str):
    """Setzt Finder-Kommentar (nur macOS)."""
    if platform.system() != "Darwin":
        return
    try:
        safe_comment = comment.replace("\\", "\\\\").replace('"', '\\"')
        safe_path = str(filepath.resolve())
        script = f'tell application "Finder" to set comment of (POSIX file "{safe_path}") to "{safe_comment}"'
        subprocess.run(["osascript", "-e", script], check=False, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def get_project_root() -> Path:
    """Gibt den Pfad zum Projekt-Root-Verzeichnis zurück."""
    return Path(__file__).parent.parent.resolve()


def get_data_dir() -> Path:
    """Returns the data directory path."""
    return get_project_root() / "data"


# ─────────────────────────────────────────────────────────────────────────────
# ARROW KEY MENU SELECTION (no external dependencies)
# ─────────────────────────────────────────────────────────────────────────────

def _get_key():
    """Read a single keypress. Returns special keys as strings like 'up', 'down', 'enter'."""
    system = platform.system()
    
    if system == "Windows":
        import msvcrt
        key = msvcrt.getch()
        if key == b'\r':
            return 'enter'
        elif key == b'\x1b':
            return 'escape'
        elif key == b'\xe0':  # Arrow key prefix on Windows
            key2 = msvcrt.getch()
            if key2 == b'H':
                return 'up'
            elif key2 == b'P':
                return 'down'
        return key.decode('utf-8', errors='ignore')
    else:
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # Escape sequence
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'up'
                    elif ch3 == 'B':
                        return 'down'
                    elif ch3 == 'C':
                        return 'right'
                    elif ch3 == 'D':
                        return 'left'
                return 'escape'
            elif ch == '\r' or ch == '\n':
                return 'enter'
            elif ch == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def select_menu(options: list, title: str = None, selected_idx: int = 0) -> int:
    """
    Display an interactive menu with arrow key navigation.
    
    Args:
        options: List of option strings to display
        title: Optional title to show above menu
        selected_idx: Initial selected index
    
    Returns:
        Selected index (0-based), or -1 if cancelled
    """
    import sys
    
    def render():
        # Move cursor up to redraw menu
        if hasattr(render, 'rendered'):
            # Move up: title (if any) + options + 1 for hint
            lines_up = len(options) + (1 if title else 0) + 1
            sys.stdout.write(f"\033[{lines_up}A")
        
        if title:
            print(f"  {title}")
        
        for i, option in enumerate(options):
            if i == selected_idx:
                print(f"  \033[7m  {option}  \033[0m")  # Inverted colors for selection
            else:
                print(f"     {option}  ")
        
        print("  ↑↓ Auswählen  Enter Bestätigen  q Abbrechen", end="", flush=True)
        render.rendered = True
    
    try:
        render()
        
        while True:
            key = _get_key()
            
            if key == 'up':
                selected_idx = (selected_idx - 1) % len(options)
                render()
            elif key == 'down':
                selected_idx = (selected_idx + 1) % len(options)
                render()
            elif key == 'enter':
                print()  # New line after selection
                return selected_idx
            elif key in ('q', 'escape'):
                print()
                return -1
                
    except KeyboardInterrupt:
        print()
        return -1


def confirm(prompt: str, default: bool = True) -> bool:
    """
    Display a yes/no confirmation with arrow key selection.
    
    Args:
        prompt: Question to ask
        default: Default value (True = Yes, False = No)
    
    Returns:
        True for Yes, False for No
    """
    options = ["Ja", "Nein"]
    selected = 0 if default else 1
    
    print(f"  {prompt}")
    result = select_menu(options, selected_idx=selected)
    
    if result == -1:  # Cancelled
        return default
    return result == 0  # 0 = Ja, 1 = Nein


def print_copyright():
    """Zeigt Copyright-Informationen."""
    print("\n" + "-" * 70)
    print("  Copyright © Noevu GmbH – AI Lösungen für Schweizer KMU")
    print("  https://noevu.ch/ai-beratung-kmu-schweiz?utm_source=bexio_tools")
    print("-" * 70 + "\n")
