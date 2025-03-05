"""Typst bot plugin for nonebot2."""

from nonebot.plugin import PluginMetadata

from .features import (
    admin_feature,
    render_feature,
    welcome_feature,
    daily_summary_feature,
    yau_feature
)

__plugin_meta__ = PluginMetadata(
    name="TypstBot",
    description="基于 Typst 的多功能 QQ 机器人",
    usage="""
    管理功能：
    /enable <功能名> - 启用功能
    /disable <功能名> - 禁用功能
    /status - 查看功能状态
    /add_admin <QQ号> - 添加管理员
    /remove_admin <QQ号> - 移除管理员
    
    Typst渲染：
    typ <Typst代码> - 渲染Typst代码
    teq <数学公式> - 渲染数学公式
    typc <代码> - 渲染代码块（默认Python语法高亮）
    
    入群欢迎：
    - 新成员入群时自动发送欢迎消息
    /welcome - 手动触发欢迎消息（可回复指定成员）
    
    每日总结：
    - 自动记录群聊消息
    - 每日23:00自动生成技术讨论总结
    /summary - 手动触发生成今日总结
    /summary_template [模板名] - 切换总结模板
    
    YauBot：
    yau <文字> - 将文字转换为香港繁体并生成图片
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Your Name",
        "version": "0.2.0",
        "priority": 1,
    },
)

__all__ = [
    "admin_feature",
    "render_feature",
    "welcome_feature",
    "daily_summary_feature",
    "yau_feature",
]
