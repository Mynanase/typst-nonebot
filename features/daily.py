"""Daily summary feature for the Typst bot."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from sqlalchemy import create_engine, Column, String, DateTime, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from jinja2 import Environment, FileSystemLoader, select_autoescape
from nonebot import on_command, require, get_driver, get_bot
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER

# 声明依赖
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from ..models import (
    DailySummaryConfig,
    MessageRecord,
    ModelConfig,
    TemplateConfig,
    SummaryResult,
    FeatureType
)
from ..models.daily import DatabaseError, TemplateError, SummaryError
from .admin import admin_feature

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="每日总结",
    description="自动生成群聊技术讨论日报",
    usage="""
    被动功能：
    - 自动记录群聊消息
    - 每日23:00自动生成技术讨论总结
    
    主动命令：
    /summary - 手动触发生成今日总结
    /summary_template [模板名] - 切换总结模板
    可用模板: concise(简洁版), technical(技术详细版), community(社区互动版)
    
    环境变量配置：
    - OPENAI_API_KEY: OpenAI API密钥
    - OPENAI_BASE_URL: OpenAI API基础URL（可选）
    - DAILY_SUMMARY_MODEL: 使用的模型名称（默认：gpt-4-turbo）
    - DAILY_SUMMARY_TIME: 每日总结时间（默认：23:00）
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Your Name",
        "version": "0.1.0",
        "priority": 5,
        "required_envs": ["OPENAI_API_KEY"],
        "optional_envs": ["OPENAI_BASE_URL", "DAILY_SUMMARY_MODEL", "DAILY_SUMMARY_TIME"],
    },
)

# SQLAlchemy基类
Base = declarative_base()

class MessageTable(Base):
    """消息数据表"""
    __tablename__ = "messages"

    msg_id = Column(String, primary_key=True)
    group_id = Column(String, nullable=False, index=True)
    sender_id = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    content = Column(String, nullable=False)
    msg_type = Column(String, default="text")
    timestamp = Column(DateTime, default=datetime.now, index=True)
    reference_id = Column(String, nullable=True)
    topic_id = Column(String, nullable=True, index=True)

    def to_model(self) -> MessageRecord:
        """转换为Pydantic模型"""
        return MessageRecord(
            msg_id=self.msg_id,
            group_id=self.group_id,
            sender_id=self.sender_id,
            sender_name=self.sender_name,
            content=self.content,
            msg_type=self.msg_type,
            timestamp=self.timestamp,
            reference_id=self.reference_id,
            topic_id=self.topic_id
        )

class DailySummaryFeature:
    """每日总结功能"""
    def __init__(self, config: DailySummaryConfig):
        self.config = config
        
        # 初始化数据库
        self.db_path = Path(config.storage_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{config.storage_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # 初始化模板环境
        self.template_dir = Path("src/plugins/typst_bot/features/daily/templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """初始化默认模板"""
        templates = {
            "concise.md.jinja": """# {{ date }} 技术社区日报 - 简洁版

## 今日概览
活跃用户数：{{ active_users }}
消息总数：{{ total_messages }}

## 🎯 热点话题
{% for topic in topics %}
{{ loop.index }}. {{ topic.name }} (热度: {{ "★" * topic.heat }})
   - {{ topic.summary }}
{% endfor %}

## ⚠️ 待解决问题
{% for issue in issues %}
- {{ issue.title }} (由 {{ issue.raised_by }} 提出)
{% endfor %}

🤖 由 {{ bot_name }} 生成
""",

            "technical.md.jinja": """# {{ date }} 技术社区日报 - 技术详细版

## 📊 数据统计
- 活跃讨论者：{{ active_users }}人
- 技术话题数：{{ topics|length }}个
- 代码分享数：{{ code_snippets|length }}段
- 总消息量：{{ total_messages }}条

## 🎯 技术话题榜
{% for topic in topics %}
### {{ loop.index }}. {{ topic.name }} (热度: {{ "★" * topic.heat }})
{{ topic.summary }}
{% if topic.key_points %}
关键点：
{% for point in topic.key_points %}
- {{ point }}
{% endfor %}
{% endif %}
{% endfor %}

## 💻 代码分析
{% for snippet in code_snippets %}
### 代码片段 {{ loop.index }}
```{{ snippet.language }}
{{ snippet.code }}
```
**分析**: {{ snippet.analysis }}
{% endfor %}

## ⚠️ 技术难题追踪
{% for issue in issues %}
### {{ issue.title }}
- 提出者：{{ issue.raised_by }}
- 状态：{{ issue.status }}
- 描述：{{ issue.description }}
{% endfor %}

## 📚 学习资源
{% for resource in resources %}
- [{{ resource.title }}]({{ resource.url }}) - {{ resource.description }}
{% endfor %}

🤖 由 {{ bot_name }} 基于 {{ total_messages }} 条消息生成
""",

            "community.md.jinja": """# {{ date }} 技术社区日报 - 社区互动版

## 👥 今日社区数据
活跃成员：{{ active_users }}
消息总量：{{ total_messages }}
互动最多话题数：{{ topics|length }}

## 🌟 精彩讨论
{% for discussion in top_discussions %}
### {{ loop.index }}. {{ discussion.title }}
参与者：{{ discussion.participants|join(", ") }}
热度：{{ "🔥" * discussion.heat }}

{{ discussion.summary }}

{% if discussion.highlights %}
精彩观点：
{% for point in discussion.highlights %}
> {{ point.content }} —— {{ point.author }}
{% endfor %}
{% endif %}
{% endfor %}

## 💡 创新想法墙
{% for idea in innovative_ideas %}
- {{ idea.author }}: {{ idea.content }}
{% endfor %}

## 👏 今日贡献者
{% for contributor in top_contributors %}
- {{ contributor.name }}: {{ contributor.contribution }}
{% endfor %}

🤖 由 {{ bot_name }} 用 ❤️ 生成
"""
        }

        for name, content in templates.items():
            template_path = self.template_dir / name
            if not template_path.exists():
                template_path.write_text(content, encoding='utf-8')

    def save_message(self, message: MessageRecord) -> None:
        """保存消息记录"""
        try:
            with self.Session() as session:
                db_message = MessageTable(
                    msg_id=message.msg_id,
                    group_id=message.group_id,
                    sender_id=message.sender_id,
                    sender_name=message.sender_name,
                    content=message.content,
                    msg_type=message.msg_type,
                    timestamp=message.timestamp,
                    reference_id=message.reference_id,
                    topic_id=message.topic_id
                )
                session.add(db_message)
                session.commit()
        except Exception as e:
            raise DatabaseError(f"保存消息失败: {e}")

    def get_today_messages(self, group_id: str) -> List[MessageRecord]:
        """获取今日消息记录"""
        try:
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            with self.Session() as session:
                query = select(MessageTable).where(
                    MessageTable.group_id == group_id,
                    MessageTable.timestamp >= today_start
                )
                results = session.execute(query).scalars().all()
                return [msg.to_model() for msg in results]
        except Exception as e:
            raise DatabaseError(f"获取消息失败: {e}")

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """调用语言模型"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.model.api_key.get_secret_value()}"
        }
        
        url = self.config.model.base_url or "https://api.openai.com/v1/chat/completions"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json={
                    "model": self.config.model.model_name,
                    "messages": messages,
                    "temperature": self.config.model.temperature,
                    "max_tokens": self.config.model.max_tokens
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise SummaryError(f"API调用失败: {response.text}")
                
            return response.json()["choices"][0]["message"]["content"]

    def _prepare_messages(self, records: List[MessageRecord]) -> str:
        """准备消息格式"""
        messages = []
        current_topic = None
        topic_messages = []
        
        for record in records:
            if record.topic_id != current_topic:
                if topic_messages:
                    messages.append({
                        "topic_id": current_topic,
                        "messages": topic_messages
                    })
                current_topic = record.topic_id
                topic_messages = []
            
            topic_messages.append({
                "sender": record.sender_name,
                "content": record.content,
                "time": record.timestamp.strftime("%H:%M:%S")
            })
        
        if topic_messages:
            messages.append({
                "topic_id": current_topic,
                "messages": topic_messages
            })
        
        return json.dumps(messages, ensure_ascii=False, indent=2)

    async def analyze_messages(self, messages: List[MessageRecord]) -> Dict[str, Any]:
        """分析消息内容"""
        if not messages:
            return {}

        prompt = f"""请分析以下技术社区的聊天记录，生成一份结构化的分析报告。
聊天记录按话题分组，每组包含发送者、内容和时间信息。

聊天记录:
{self._prepare_messages(messages)}

请提供以下信息（JSON格式）：
1. topics: 主要讨论的技术话题列表，每个话题包含:
   - name: 话题名称
   - heat: 热度值(1-5)
   - summary: 讨论要点总结
   - key_points: 关键论点列表
2. code_snippets: 代码片段分析，包含:
   - language: 编程语言
   - code: 代码内容
   - analysis: 代码功能分析
3. issues: 技术难题列表，包含:
   - title: 问题标题
   - raised_by: 提出者
   - status: 状态(unsolved/in_progress/solved)
   - description: 问题描述
4. resources: 相关学习资源，包含:
   - title: 资源标题
   - url: 资源链接
   - description: 资源描述
5. innovative_ideas: 创新想法列表，包含:
   - author: 提出者
   - content: 想法内容
6. top_contributors: 主要贡献者列表，包含:
   - name: 贡献者名称
   - contribution: 贡献内容描述

请确保输出为有效的JSON格式。"""

        try:
            response = await self._call_llm([
                {"role": "system", "content": "你是一个技术社区聊天记录分析专家"},
                {"role": "user", "content": prompt}
            ])
            return json.loads(response)
        except Exception as e:
            raise SummaryError(f"分析消息失败: {e}")

    async def generate_summary(
        self,
        group_id: str,
        template_name: str = "technical"
    ) -> SummaryResult:
        """生成每日总结"""
        try:
            # 获取今日消息
            messages = self.get_today_messages(group_id)
            if not messages:
                return SummaryResult(
                    success=False,
                    error="今日无消息记录",
                    group_id=group_id,
                    date=datetime.now().strftime("%Y-%m-%d")
                )

            # 分析消息
            analysis = await self.analyze_messages(messages)
            
            # 渲染模板
            template = self.env.get_template(f"{template_name}.md.jinja")
            content = template.render(
                date=datetime.now().strftime("%Y-%m-%d"),
                active_users=len({msg.sender_id for msg in messages}),
                total_messages=len(messages),
                topics=analysis.get("topics", []),
                code_snippets=analysis.get("code_snippets", []),
                issues=analysis.get("issues", []),
                resources=analysis.get("resources", []),
                top_discussions=[],  # 从topics中转换
                innovative_ideas=analysis.get("innovative_ideas", []),
                top_contributors=analysis.get("top_contributors", []),
                bot_name="TypstBot"
            )
            
            return SummaryResult(
                success=True,
                content=content,
                group_id=group_id,
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
        except Exception as e:
            return SummaryResult(
                success=False,
                error=str(e),
                group_id=group_id,
                date=datetime.now().strftime("%Y-%m-%d")
            )

# 获取全局驱动器
driver = get_driver()

# 确保数据目录存在
DATA_DIR = Path("src/plugins/typst_bot/data/daily_summary")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 从配置文件加载配置
from ..core.config import config_manager

feature_config = config_manager.get_feature_config("daily_summary")
config = DailySummaryConfig(**feature_config)

# 创建功能实例
daily_summary_feature = DailySummaryFeature(config)

# 手动触发总结命令
manual_summary = on_command("summary", permission=SUPERUSER)
change_template = on_command("summary_template", permission=SUPERUSER)

@manual_summary.handle()
async def handle_manual_summary(bot: Bot, event: GroupMessageEvent):
    """手动触发生成总结"""
    # 检查功能是否启用
    if not admin_feature.is_feature_enabled(str(event.group_id), FeatureType.DAILY_SUMMARY):
        await manual_summary.finish("该群未启用每日总结功能")
        return

    # 生成总结
    result = await daily_summary_feature.generate_summary(
        str(event.group_id),
        config.template.current
    )
    
    # 发送结果
    if result.success:
        await manual_summary.finish(result.content)
    else:
        await manual_summary.finish(f"生成总结失败: {result.error}")

@change_template.handle()
async def handle_change_template(bot: Bot, event: GroupMessageEvent):
    """切换总结模板"""
    # 检查功能是否启用
    if not admin_feature.is_feature_enabled(str(event.group_id), FeatureType.DAILY_SUMMARY):
        await change_template.finish("该群未启用每日总结功能")
        return

    msg = str(event.get_message()).strip()
    template_name = msg.split()[-1] if msg else "technical"
    
    if template_name not in ["concise", "technical", "community"]:
        await change_template.finish(
            "无效的模板名称。可用模板: concise, technical, community"
        )
        return
    
    config.template.current = template_name
    await change_template.finish(f"已切换到{template_name}模板")

# 解析调度时间
schedule_hour, schedule_minute = map(int, config.schedule_time.split(":"))

@scheduler.scheduled_job("cron", hour=schedule_hour, minute=schedule_minute)
async def generate_daily_summary():
    """定时生成每日总结"""
    try:
        # 获取所有活跃群组
        active_groups = {msg.group_id for msg in daily_summary_feature.get_today_messages("")}
        
        # 获取Bot实例
        try:
            bot = get_bot()
        except ValueError as e:
            print(f"获取Bot实例失败: {e}")
            return
        
        for group_id in active_groups:
            # 检查功能是否启用
            if not admin_feature.is_feature_enabled(group_id, FeatureType.DAILY_SUMMARY):
                continue

            try:
                result = await daily_summary_feature.generate_summary(
                    group_id,
                    config.template.current
                )
                
                if result.success:
                    await bot.send_group_msg(
                        group_id=int(group_id),
                        message=result.content
                    )
                else:
                    print(f"为群组 {group_id} 生成总结失败: {result.error}")
            except Exception as e:
                print(f"处理群组 {group_id} 失败: {e}")
                continue
    except Exception as e:
        print(f"生成每日总结失败: {e}")

# 启动时检查配置
@driver.on_startup
async def check_config():
    if not config.model.api_key:
        raise ValueError("未设置 daily_summary.model.api_key 配置")
