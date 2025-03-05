"""Welcome feature for the Typst bot."""

import aiohttp
from datetime import datetime
from pathlib import Path
from nonebot import on_notice, on_command
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    GroupIncreaseNoticeEvent
)

from ..core import TypstCompiler, CompilerConfig, TemplateManager, default_sender
from ..models import WelcomeConfig, WelcomeContext, WelcomeResult, FeatureType
from ..models.welcome import TemplateError, RenderError
from .admin import admin_feature

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="入群欢迎",
    description="生成并发送入群欢迎消息",
    usage="""
    被动功能：
    - 新成员入群时自动发送欢迎消息
    
    主动命令：
    /welcome - 手动触发欢迎消息（可回复指定成员）
    
    配置说明：
    - 支持群组自定义模板
    - 支持从URL加载模板
    - 支持自定义渲染参数
    
    环境变量：
    WELCOME_TIMEOUT: 渲染超时时间（默认30秒）
    WELCOME_PPI: 图片DPI（默认300）
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Your Name",
        "version": "0.2.0",
        "priority": 5,
    },
)

class WelcomeFeature:
    """欢迎功能"""
    def __init__(self, config: WelcomeConfig):
        self.config = config
        
        # 初始化编译器
        self.compiler = TypstCompiler(
            CompilerConfig(
                timeout=config.timeout,
                ppi=config.ppi
            )
        )
        
        # 初始化模板管理器
        self.template_manager = TemplateManager(config.template_dir)
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """初始化默认模板"""
        default_template = """
#set page(
    width: auto,
    height: auto,
    margin: 0.5em
)

#align(center)[
  #text(size: 1.5em)[欢迎加入 {group_name}]
  
  #v(0.5em)
  
  #text(size: 1.2em)[👋 {nickname}]
  
  #v(0.5em)
  
  你是第 {member_count} 位成员
]
"""
        
        if not self.template_manager.get_template("default"):
            self.template_manager.save_template(
                "default",
                default_template,
                "默认欢迎模板"
            )

    async def _fetch_template(self, url: str) -> str:
        """从URL获取模板"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    raise TemplateError(f"获取模板失败: HTTP {response.status}")
        except Exception as e:
            raise TemplateError(f"获取模板失败: {e}")

    async def _get_template(self, group_id: str) -> str:
        """获取群组模板"""
        # 尝试从URL获取
        if group_id in self.config.template_urls:
            try:
                return await self._fetch_template(str(self.config.template_urls[group_id]))
            except Exception as e:
                print(f"从URL获取模板失败: {e}")
        
        # 使用本地模板
        template_name = self.config.group_templates.get(group_id, self.config.default_template)
        template = self.template_manager.get_template(template_name)
        if not template:
            raise TemplateError(f"模板不存在: {template_name}")
        
        return template.content

    async def _get_group_info(self, bot: Bot, group_id: int) -> dict:
        """获取群组信息"""
        try:
            return await bot.get_group_info(group_id=group_id)
        except Exception as e:
            raise RenderError(f"获取群组信息失败: {e}")

    async def _get_member_info(self, bot: Bot, group_id: int, user_id: int) -> dict:
        """获取成员信息"""
        try:
            return await bot.get_group_member_info(
                group_id=group_id,
                user_id=user_id
            )
        except Exception as e:
            raise RenderError(f"获取成员信息失败: {e}")

    async def generate_welcome(
        self,
        bot: Bot,
        group_id: int,
        user_id: int
    ) -> WelcomeResult:
        """生成欢迎消息"""
        try:
            # 获取群组和成员信息
            group_info = await self._get_group_info(bot, group_id)
            member_info = await self._get_member_info(bot, group_id, user_id)
            
            # 准备上下文
            context = WelcomeContext(
                group_id=str(group_id),
                group_name=group_info['group_name'],
                user_id=str(user_id),
                nickname=member_info.get('nickname', str(user_id)),
                join_time=datetime.fromtimestamp(
                    member_info.get('join_time', datetime.now().timestamp())
                ).strftime("%Y-%m-%d %H:%M:%S"),
                member_count=group_info.get('member_count', 0)
            )
            
            # 获取并渲染模板
            template_content = await self._get_template(str(group_id))
            rendered_content = self.template_manager.render_template(
                "default",  # 模板名不重要，因为我们直接传入内容
                context.model_dump()
            )
            if not rendered_content:
                raise TemplateError("模板渲染失败")
            
            # 编译文档
            result = await self.compiler.compile(rendered_content)
            if not result.success:
                raise RenderError(result.error or "编译失败")
            
            return WelcomeResult(
                success=True,
                image_data=result.content
            )
            
        except TemplateError as e:
            return WelcomeResult(
                success=False,
                error=f"模板错误: {str(e)}"
            )
        except RenderError as e:
            return WelcomeResult(
                success=False,
                error=f"渲染错误: {str(e)}"
            )
        except Exception as e:
            return WelcomeResult(
                success=False,
                error=f"生成欢迎消息失败: {str(e)}"
            )

# 确保数据目录存在
DATA_DIR = Path("src/plugins/typst_bot/data/welcome")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 从配置文件加载配置
from ..core.config import config_manager

feature_config = config_manager.get_feature_config("welcome")
config = WelcomeConfig(**feature_config)

# 创建功能实例
welcome_feature = WelcomeFeature(config)

# 消息处理器
welcome = on_notice()
welcome_cmd = on_command("welcome")

@welcome.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    """处理新成员入群事件"""
    # 检查功能是否启用
    if not admin_feature.is_feature_enabled(str(event.group_id), FeatureType.WELCOME):
        return
    
    # 生成欢迎消息
    result = await welcome_feature.generate_welcome(
        bot,
        event.group_id,
        event.user_id
    )
    
    # 发送结果
    if result.success and result.image_data:
        await default_sender.send_image(
            bot,
            event,
            result.image_data,
            "发送欢迎消息失败"
        )
    else:
        await default_sender.send_message(
            bot,
            event,
            result.error or "生成欢迎消息失败"
        )

@welcome_cmd.handle()
async def handle_welcome_command(bot: Bot, event: GroupMessageEvent):
    """处理欢迎命令"""
    # 检查功能是否启用
    if not admin_feature.is_feature_enabled(str(event.group_id), FeatureType.WELCOME):
        await welcome_cmd.finish("该群未启用欢迎功能")
        return
    
    # 确定目标用户
    target_user_id = event.user_id
    if event.reply:
        target_user_id = event.reply.sender.user_id
    
    # 生成欢迎消息
    result = await welcome_feature.generate_welcome(
        bot,
        event.group_id,
        target_user_id
    )
    
    # 发送结果
    if result.success and result.image_data:
        await default_sender.send_image(
            bot,
            event,
            result.image_data,
            "发送欢迎消息失败"
        )
    else:
        await default_sender.send_message(
            bot,
            event,
            result.error or "生成欢迎消息失败",
            at_sender=True
        )
