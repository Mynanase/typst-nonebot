"""Yau feature for the Typst bot."""

import opencc
from datetime import datetime
from pathlib import Path
from nonebot import on_message
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent

from ..core import TypstCompiler, CompilerConfig, TemplateManager, default_sender
from ..models import YauBotConfig, YauBotRequest, YauBotResult, FeatureType
from ..models.yau import TemplateError, ConversionError, RenderError
from .admin import admin_feature

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="YauBot",
    description="将文字转换为香港繁体并生成图片",
    usage="""
    命令格式：
    yau <文字> - 将文字转换为香港繁体并生成图片
    
    示例：
    yau 你好世界
    
    配置说明：
    - 支持自定义模板
    - 支持自定义字体和样式
    - 支持自定义OpenCC配置
    
    环境变量：
    YAUBOT_TIMEOUT: 渲染超时时间（默认30秒）
    YAUBOT_PPI: 图片DPI（默认300）
    YAUBOT_OPENCC: OpenCC配置（默认s2hk）
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Your Name",
        "version": "0.2.0",
        "priority": 5,
    },
)

class YauFeature:
    """YauBot功能"""
    def __init__(self, config: YauBotConfig):
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
        
        # 初始化OpenCC转换器
        try:
            self.converter = opencc.OpenCC(config.opencc_config)
        except Exception as e:
            raise ConversionError(f"初始化OpenCC失败: {e}")

    def _init_default_templates(self) -> None:
        """初始化默认模板"""
        default_template = """
#set page(
    width: auto,
    height: auto,
    margin: 0.5em
)

#set text(font: ("Source Han Serif HK", "Source Han Serif K"))

#align(center)[
  #text(size: 1.2em)[{text}]
  
  #v(0.5em)
  
  #text(size: 0.8em)[{datetime_now}]
]
"""
        
        if not self.template_manager.get_template("yau"):
            self.template_manager.save_template(
                "yau",
                default_template,
                "YauBot默认模板"
            )

    def _convert_text(self, text: str) -> str:
        """转换文本为香港繁体中文"""
        try:
            return self.converter.convert(text.strip())
        except Exception as e:
            raise ConversionError(f"文本转换失败: {e}")

    @staticmethod
    def parse_message(msg: str) -> YauBotRequest | None:
        """解析消息内容"""
        msg = msg.strip()
        
        if msg.startswith("yau "):
            content = msg[4:].strip()
            if not content:
                return None
            
            return YauBotRequest(
                content=content,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        
        return None

    async def process(self, request: YauBotRequest) -> YauBotResult:
        """处理YauBot请求"""
        try:
            # 转换文本
            converted_text = self._convert_text(request.content)
            
            # 获取模板
            template = self.template_manager.get_template(self.config.template_name)
            if not template:
                raise TemplateError(f"未找到模板: {self.config.template_name}")
            
            # 渲染模板
            rendered_content = self.template_manager.render_template(
                self.config.template_name,
                {
                    "text": converted_text,
                    "datetime_now": request.timestamp
                }
            )
            if not rendered_content:
                raise TemplateError("模板渲染失败")
            
            # 编译文档
            result = await self.compiler.compile(rendered_content)
            if not result.success:
                raise RenderError(result.error or "编译失败")
            
            return YauBotResult(
                success=True,
                image_data=result.content
            )
            
        except TemplateError as e:
            return YauBotResult(
                success=False,
                error=f"模板错误: {str(e)}"
            )
        except ConversionError as e:
            return YauBotResult(
                success=False,
                error=f"转换错误: {str(e)}"
            )
        except RenderError as e:
            return YauBotResult(
                success=False,
                error=f"渲染错误: {str(e)}"
            )
        except Exception as e:
            return YauBotResult(
                success=False,
                error=f"处理失败: {str(e)}"
            )

# 确保数据目录存在
DATA_DIR = Path("src/plugins/typst_bot/data/yaubot")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 从配置文件加载配置
from ..core.config import config_manager

feature_config = config_manager.get_feature_config("yau")
config = YauBotConfig(**feature_config)

# 创建功能实例
yau_feature = YauFeature(config)

# 消息处理器
yaubot = on_message(priority=5)

@yaubot.handle()
async def handle_yaubot(bot: Bot, event: MessageEvent):
    """处理YauBot请求"""
    # 检查群组权限
    if isinstance(event, GroupMessageEvent):
        if not admin_feature.is_feature_enabled(str(event.group_id), FeatureType.YAU):
            return
    
    # 解析消息
    msg = event.get_plaintext()
    request = yau_feature.parse_message(msg)
    if not request:
        return
    
    # 处理请求
    result = await yau_feature.process(request)
    
    # 发送结果
    if result.success and result.image_data:
        await default_sender.send_image(
            bot,
            event,
            result.image_data,
            "发送结果失败"
        )
    else:
        await default_sender.send_message(
            bot,
            event,
            result.error or "处理失败",
            at_sender=True
        )
