"""Common models shared across features."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel as PydanticBaseModel

class FeatureType(str, Enum):
    """功能类型枚举"""
    ADMIN = "admin"
    RENDER = "render"
    WELCOME = "welcome"
    DAILY_SUMMARY = "daily_summary"
    YAU = "yau"

class BaseConfig(PydanticBaseModel):
    """基础配置类"""
    enabled: bool = True
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseModel(PydanticBaseModel):
    """基础模型类"""
    class Config:
        arbitrary_types_allowed = True

class BaseResult(BaseModel):
    """基础结果类"""
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
