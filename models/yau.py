"""Yau feature models."""

from typing import Optional
from pathlib import Path
from pydantic import Field

from .common import BaseModel, BaseConfig, BaseResult

class YauBotConfig(BaseConfig):
    """YauBot配置"""
    template_dir: Path = Field(
        default=Path("src/plugins/typst_bot/data/yaubot/templates"),
        description="模板目录"
    )
    template_name: str = Field(
        default="yau",
        description="默认模板名称"
    )
    timeout: int = Field(
        default=30,
        description="渲染超时时间（秒）"
    )
    ppi: int = Field(
        default=300,
        description="输出图片DPI"
    )
    opencc_config: str = Field(
        default="s2hk",
        description="OpenCC转换配置"
    )

class YauBotRequest(BaseModel):
    """YauBot请求"""
    content: str
    timestamp: str = Field(
        default_factory=lambda: "",
        description="处理时间"
    )

class YauBotResult(BaseResult):
    """YauBot处理结果"""
    image_data: Optional[str] = None  # base64编码的图片数据

class YauBotError(Exception):
    """YauBot错误基类"""
    pass

class TemplateError(YauBotError):
    """模板相关错误"""
    pass

class ConversionError(YauBotError):
    """文字转换错误"""
    pass

class RenderError(YauBotError):
    """渲染相关错误"""
    pass
