"""Admin feature models."""

from typing import Dict, Set, Optional
from pydantic import Field

from .common import BaseModel, BaseConfig, FeatureType

class GroupConfig(BaseModel):
    """群组功能配置"""
    disabled_features: Set[FeatureType] = Field(default_factory=set)
    custom_settings: Dict[str, dict] = Field(default_factory=dict)

class AdminConfig(BaseConfig):
    """管理功能配置"""
    superusers: Set[str] = Field(default_factory=set)
    group_configs: Dict[str, GroupConfig] = Field(default_factory=dict)
    default_config: GroupConfig = Field(default_factory=GroupConfig)

    def get_group_config(self, group_id: str) -> GroupConfig:
        """获取群组配置，如不存在则创建新配置"""
        if group_id not in self.group_configs:
            self.group_configs[group_id] = GroupConfig()
        return self.group_configs[group_id]

    def is_feature_enabled(self, group_id: str, feature: FeatureType) -> bool:
        """检查特定群组的功能是否启用"""
        config = self.get_group_config(group_id)
        return feature not in config.disabled_features

    def set_feature_state(self, group_id: str, feature: FeatureType, enabled: bool) -> None:
        """设置特定群组的功能状态"""
        config = self.get_group_config(group_id)
        if enabled:
            config.disabled_features.discard(feature)
        else:
            config.disabled_features.add(feature)

    def is_superuser(self, user_id: str) -> bool:
        """检查用户是否为超级管理员"""
        return user_id in self.superusers

    def add_superuser(self, user_id: str) -> None:
        """添加超级管理员"""
        self.superusers.add(user_id)

    def remove_superuser(self, user_id: str) -> None:
        """移除超级管理员"""
        self.superusers.discard(user_id)
