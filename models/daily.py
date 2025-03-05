"""Daily summary feature models."""

from datetime import datetime
from typing import List, Optional
from pydantic import Field, HttpUrl, SecretStr

from .common import BaseModel, BaseConfig, BaseResult

class MessageRecord(BaseModel):
    """聊天消息记录"""
    msg_id: str = Field(..., description="消息唯一ID")
    group_id: str = Field(..., description="群组ID")
    sender_id: str = Field(..., description="发送者ID")
    sender_name: str = Field(..., description="发送者昵称")
    content: str = Field(..., description="消息内容")
    msg_type: str = Field(default="text", description="消息类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间")
    reference_id: Optional[str] = Field(default=None, description="引用消息ID")
    topic_id: Optional[str] = Field(default=None, description="话题ID")

class ModelConfig(BaseModel):
    """语言模型配置"""
    provider: str = Field(default="openai", description="模型提供商")
    model_name: str = Field(default="gpt-4-turbo", description="模型名称")
    base_url: Optional[HttpUrl] = Field(default=None, description="API基础URL")
    api_key: SecretStr = Field(..., description="API密钥")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=2000, gt=0, description="最大token数")

class TemplateConfig(BaseModel):
    """总结模板配置"""
    presets: List[str] = Field(
        default=["简洁版", "技术详细版", "社区互动版"],
        description="预设模板列表"
    )
    current: str = Field(default="技术详细版", description="当前使用的模板")
    custom_path: Optional[str] = Field(default=None, description="自定义模板路径")

class DailySummaryConfig(BaseConfig):
    """每日总结功能配置"""
    schedule_time: str = Field(default="23:00", description="定时任务时间")
    model: ModelConfig = Field(..., description="语言模型配置")
    template: TemplateConfig = Field(
        default_factory=TemplateConfig,
        description="模板配置"
    )
    storage_path: str = Field(
        default="data/daily_summary/messages.db",
        description="消息存储路径"
    )
    backup_interval: str = Field(
        default="24h",
        description="备份间隔"
    )

class SummaryResult(BaseResult):
    """总结生成结果"""
    content: Optional[str] = None  # 总结内容
    group_id: Optional[str] = None  # 群组ID
    date: Optional[str] = None  # 总结日期

class DailySummaryError(Exception):
    """每日总结功能错误基类"""
    pass

class DatabaseError(DailySummaryError):
    """数据库相关错误"""
    pass

class TemplateError(DailySummaryError):
    """模板相关错误"""
    pass

class SummaryError(DailySummaryError):
    """总结生成错误"""
    pass
