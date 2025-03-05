"""Render feature models."""

from typing import Dict, Optional
from pathlib import Path
from pydantic import Field

from .common import BaseModel, BaseConfig, BaseResult

class RenderConfig(BaseConfig):
    """渲染配置"""
    template_dir: Path = Field(
        default=Path("src/plugins/typst_bot/data/render/templates"),
        description="模板目录"
    )
    templates: Dict[str, str] = Field(
        default={
            'typ': 'typ.typ',   # 普通Typst代码
            'teq': 'teq.typ',   # 数学公式
            'typc': 'typc.typ', # 代码块
        },
        description="模板映射"
    )
    timeout: int = Field(
        default=30,
        description="渲染超时时间（秒）"
    )
    ppi: int = Field(
        default=300,
        description="输出图片DPI"
    )

class RenderRequest(BaseModel):
    """渲染请求"""
    template_type: str
    content: str
    raw_content: Optional[str] = None

class RenderResult(BaseResult):
    """渲染结果"""
    image_data: Optional[str] = None  # base64编码的图片数据

class RenderError(Exception):
    """渲染错误基类"""
    pass

class TemplateError(RenderError):
    """模板相关错误"""
    pass

class CompilationError(RenderError):
    """编译错误"""
    pass
