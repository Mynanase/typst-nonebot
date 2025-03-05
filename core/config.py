"""Configuration management for the Typst bot."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Configuration manager for the Typst bot."""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self.load_config()
    
    @property
    def config_path(self) -> Path:
        """Get the path to the config file."""
        return Path("src/plugins/typst_bot/data/config.json")
    
    def load_config(self) -> None:
        """Load configuration from the JSON file."""
        try:
            if self.config_path.exists():
                self._config = json.loads(self.config_path.read_text(encoding='utf-8'))
            else:
                self._config = {}
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = {}
    
    def save_config(self) -> None:
        """Save configuration to the JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_feature_config(self, feature_name: str) -> Dict[str, Any]:
        """Get configuration for a specific feature."""
        return self._config.get(feature_name, {})
    
    def update_feature_config(self, feature_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific feature."""
        self._config[feature_name] = config
        self.save_config()
    
    def get_value(self, feature_name: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        feature_config = self.get_feature_config(feature_name)
        return feature_config.get(key, default)

# Global instance
config_manager = ConfigManager()
