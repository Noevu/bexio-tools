#!/usr/bin/env python3
"""
Configuration manager for Bexio-Tools.
Handles persistent storage of settings in ~/.bexio-tools/config.json
"""
import json
import os
from pathlib import Path
from typing import Any

# Default configuration values
DEFAULT_CONFIG = {
    "google_api_key": "",
    "company_name": "",
    "default_workflow": "",  # "download", "rename", "both"
    "custom_prompt_suffix": "",
    "directories": {
        "input_dir": "downloads",
        "out_dir": "benannt",
        "archive_dir": "verarbeitet",
        "log_dir": "logs"
    },
    "model": "gemini-2.5-flash",
    "concurrency": 4,
    "limit": 0
}

# Config file location
CONFIG_DIR = Path.home() / ".bexio-tools"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    """Configuration manager with persistent storage."""
    
    def __init__(self):
        self._config: dict = {}
        self._load()
    
    def _load(self):
        """Load configuration from file, or create with defaults."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                # Merge with defaults to ensure all keys exist
                self._config = self._merge_defaults(self._config, DEFAULT_CONFIG)
            except (json.JSONDecodeError, IOError):
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
    
    def _merge_defaults(self, config: dict, defaults: dict) -> dict:
        """Recursively merge defaults into config for missing keys."""
        result = defaults.copy()
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_defaults(value, result[key])
            else:
                result[key] = value
        return result
    
    def save(self):
        """Save current configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value if value != "" else default
    
    def set(self, key: str, value: Any):
        """Set a configuration value and save."""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def get_directory(self, name: str) -> Path:
        """Get a directory path, resolved relative to script location."""
        dir_value = self.get(f"directories.{name}", DEFAULT_CONFIG["directories"].get(name, ""))
        return Path(dir_value)
    
    def set_directory(self, name: str, path: str | Path):
        """Set a directory path."""
        self.set(f"directories.{name}", str(path))
    
    @property
    def google_api_key(self) -> str:
        return self.get("google_api_key", "")
    
    @google_api_key.setter
    def google_api_key(self, value: str):
        self.set("google_api_key", value)
    
    @property
    def company_name(self) -> str:
        return self.get("company_name", "")
    
    @company_name.setter
    def company_name(self, value: str):
        self.set("company_name", value)
    
    @property
    def default_workflow(self) -> str:
        return self.get("default_workflow", "")
    
    @default_workflow.setter
    def default_workflow(self, value: str):
        self.set("default_workflow", value)
    
    @property
    def custom_prompt_suffix(self) -> str:
        return self.get("custom_prompt_suffix", "")
    
    @custom_prompt_suffix.setter
    def custom_prompt_suffix(self, value: str):
        self.set("custom_prompt_suffix", value)
    
    @property
    def model(self) -> str:
        return self.get("model", DEFAULT_CONFIG["model"])
    
    @model.setter
    def model(self, value: str):
        self.set("model", value)
    
    @property
    def concurrency(self) -> int:
        return self.get("concurrency", DEFAULT_CONFIG["concurrency"])
    
    @concurrency.setter
    def concurrency(self, value: int):
        self.set("concurrency", value)
    
    @property
    def limit(self) -> int:
        return self.get("limit", DEFAULT_CONFIG["limit"])
    
    @limit.setter
    def limit(self, value: int):
        self.set("limit", value)
    
    def to_dict(self) -> dict:
        """Return current config as dictionary."""
        return self._config.copy()
    
    def has_required_settings(self) -> bool:
        """Check if all required settings are configured."""
        return bool(self.google_api_key and self.company_name)


# Singleton instance
_config_instance: Config | None = None


def get_config() -> Config:
    """Get the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
