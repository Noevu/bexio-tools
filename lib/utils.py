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
    """Returns the project root directory."""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Returns the data directory path."""
    return get_project_root() / "data"
