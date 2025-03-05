"""Welcome feature models."""

from typing import Dict, Optional
from pathlib import Path
from pydantic import Field, HttpUrl

from .common import BaseModel, BaseConfig, BaseResult

class WelcomeConfig(BaseConfig):
    """欢迎功能配置"""
    template_dir: Path = Field(
        default=Path("src/plugins/typst_bot/data/welcome/templates"),
        description="模板目录"
    )
    default_template: str = Field(
        default="default",
        description="默认模板名称"
    )
    group_templates: Dict[str, str] = Field(
        default_factory=dict,
        description="群组特定模板配置"
    )
    template_urls: Dict[str, HttpUrl] = Field(
        default_factory=dict,
        description="模板URL配置"
    )
    timeout: int = Field(
        default=30,
        description="渲染超时时间（秒）"
    )
    ppi: int = Field(
        default=300,
        description="输出图片DPI"
    )

class WelcomeContext(BaseModel):
    """欢迎消息上下文"""
    group_id: str
    group_name: str
    user_id: str
    nickname: str
    join_time: str
    member_count: int

class WelcomeResult(BaseResult):
    """欢迎消息生成结果"""
    image_data: Optional[str] = None  # base64编码的图片数据

class WelcomeError(Exception):
    """欢迎功能错误基类"""
    pass

class TemplateError(WelcomeError):
    """模板相关错误"""
    pass

class RenderError(WelcomeError):
    """渲染相关错误"""
    pass
