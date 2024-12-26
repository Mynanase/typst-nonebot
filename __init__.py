from .config_manager import config_manager  # 如果有的话
from nonebot.plugin import PluginMetadata

# 导入子插件的功能
from .welcome import welcome
from .render import renderer
from .yaubot import yaubot
from .admin import disable_feature, enable_feature

__plugin_meta__ = PluginMetadata(
    name="TypBot",
    description="用于渲染 typst 代码和生成欢迎消息",
    usage="""
    基础命令：
    - typ <typst 代码>：markup 模式渲染
    - teq <typst 代码>：数学公式模式渲染
    - typc <typst 代码>：脚本模式渲染
    
    管理员命令：
    - /disable <feature>：禁用特定功能
    - /enable <feature>：启用特定功能
    
    可用功能(feature)：
    - welcome：欢迎消息
    - render：Typst 渲染
    """,
    type="application",
    extra={
        "author": "qosmos",
        "version": "1.0.0",
        "priority": 1,
    },
)

# 导出所有需要的变量
__all__ = [
    'welcome',
    'renderer',
    'disable_feature',
    'enable_feature',
    'config_manager',  # 如果需要在其他地方使用
]


