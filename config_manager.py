import json
from pathlib import Path
from enum import Enum
from typing import Dict, Set
from dataclasses import dataclass

# 功能枚举
class Feature(Enum):
    WELCOME = "welcome"
    RENDER = "render"

@dataclass
class GroupConfig:
    disabled_features: Set[Feature] = None

    def __post_init__(self):
        self.disabled_features = set() if self.disabled_features is None else self.disabled_features

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "group_configs.json"

# 群组配置管理
class ConfigManager:
    def __init__(self):
        self.group_configs: Dict[int, GroupConfig] = {}
        self.load_configs()

    def load_configs(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
                for group_id, config in data.items():
                    features = set(Feature(feature) for feature in config.get("disabled_features", []))
                    self.group_configs[int(group_id)] = GroupConfig(disabled_features=features)

    def save_configs(self):
        data = {}
        for group_id, config in self.group_configs.items():
            data[group_id] = {
                "disabled_features": [f.value for f in config.disabled_features]
            }
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_group_config(self, group_id: int) -> GroupConfig:
        if group_id not in self.group_configs:
            self.group_configs[group_id] = GroupConfig()
        return self.group_configs[group_id]

    def is_feature_enabled(self, group_id: int, feature: Feature) -> bool:
        config = self.get_group_config(group_id)
        return feature not in config.disabled_features

    def disable_feature(self, group_id: int, feature: Feature) -> None:
        config = self.get_group_config(group_id)
        config.disabled_features.add(feature)
        self.save_configs()

    def enable_feature(self, group_id: int, feature: Feature) -> None:
        config = self.get_group_config(group_id)
        config.disabled_features.discard(feature)
        self.save_configs()

# 创建单例配置管理器
config_manager = ConfigManager()
