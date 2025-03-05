"""Admin feature for the Typst bot."""

import json
from pathlib import Path
from typing import Optional
from nonebot import on_command
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.permission import SUPERUSER

from ..core import default_sender
from ..models import AdminConfig, FeatureType

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="管理功能",
    description="管理机器人功能的启用/禁用",
    usage="""
    命令格式：
    /enable <功能名> - 启用功能
    /disable <功能名> - 禁用功能
    /status - 查看功能状态
    /add_admin <QQ号> - 添加管理员
    /remove_admin <QQ号> - 移除管理员
    
    可用功能：
    - render: Typst渲染
    - welcome: 欢迎消息
    - daily_summary: 每日总结
    - yau: Yau功能
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Your Name",
        "version": "0.2.0",
        "priority": 1,
    },
)

class AdminFeature:
    """管理功能"""
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> AdminConfig:
        """加载配置"""
        try:
            if self.config_path.exists():
                data = json.loads(self.config_path.read_text(encoding='utf-8'))
                return AdminConfig.parse_obj(data)
        except Exception as e:
            print(f"加载管理配置失败: {e}")
        
        return AdminConfig()

    def _save_config(self) -> bool:
        """保存配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(
                self.config.json(indent=2),
                encoding='utf-8'
            )
            return True
        except Exception as e:
            print(f"保存管理配置失败: {e}")
            return False

    def is_feature_enabled(self, group_id: str, feature: FeatureType) -> bool:
        """检查功能是否启用"""
        return self.config.is_feature_enabled(group_id, feature)

    def set_feature_state(self, group_id: str, feature: FeatureType, enabled: bool) -> bool:
        """设置功能状态"""
        try:
            self.config.set_feature_state(group_id, feature, enabled)
            return self._save_config()
        except Exception as e:
            print(f"设置功能状态失败: {e}")
            return False

    def is_superuser(self, user_id: str) -> bool:
        """检查是否为超级管理员"""
        return self.config.is_superuser(user_id)

    def add_superuser(self, user_id: str) -> bool:
        """添加超级管理员"""
        try:
            self.config.add_superuser(user_id)
            return self._save_config()
        except Exception as e:
            print(f"添加超级管理员失败: {e}")
            return False

    def remove_superuser(self, user_id: str) -> bool:
        """移除超级管理员"""
        try:
            self.config.remove_superuser(user_id)
            return self._save_config()
        except Exception as e:
            print(f"移除超级管理员失败: {e}")
            return False

    def get_feature_status(self, group_id: str) -> str:
        """获取功能状态信息"""
        status_lines = ["当前功能状态："]
        for feature in FeatureType:
            enabled = self.is_feature_enabled(group_id, feature)
            status = "启用" if enabled else "禁用"
            status_lines.append(f"- {feature.value}: {status}")
        return "\n".join(status_lines)

# 创建功能实例
admin_feature = AdminFeature(Path("data/admin/config.json"))

# 命令处理器
enable_cmd = on_command("enable", permission=SUPERUSER, priority=1)
disable_cmd = on_command("disable", permission=SUPERUSER, priority=1)
status_cmd = on_command("status", priority=1)
add_admin_cmd = on_command("add_admin", permission=SUPERUSER, priority=1)
remove_admin_cmd = on_command("remove_admin", permission=SUPERUSER, priority=1)

@enable_cmd.handle()
async def handle_enable(bot: Bot, event: GroupMessageEvent):
    """处理启用功能命令"""
    args = str(event.get_message()).strip().split()
    if len(args) != 1:
        await default_sender.send_message(
            bot, event,
            "请指定要启用的功能",
            at_sender=True
        )
        return

    try:
        feature = FeatureType(args[0])
    except ValueError:
        await default_sender.send_message(
            bot, event,
            f"未知功能: {args[0]}",
            at_sender=True
        )
        return

    if admin_feature.set_feature_state(str(event.group_id), feature, True):
        await default_sender.send_message(
            bot, event,
            f"已启用功能: {feature.value}",
            at_sender=True
        )
    else:
        await default_sender.send_message(
            bot, event,
            "设置失败，请检查日志",
            at_sender=True
        )

@disable_cmd.handle()
async def handle_disable(bot: Bot, event: GroupMessageEvent):
    """处理禁用功能命令"""
    args = str(event.get_message()).strip().split()
    if len(args) != 1:
        await default_sender.send_message(
            bot, event,
            "请指定要禁用的功能",
            at_sender=True
        )
        return

    try:
        feature = FeatureType(args[0])
    except ValueError:
        await default_sender.send_message(
            bot, event,
            f"未知功能: {args[0]}",
            at_sender=True
        )
        return

    if admin_feature.set_feature_state(str(event.group_id), feature, False):
        await default_sender.send_message(
            bot, event,
            f"已禁用功能: {feature.value}",
            at_sender=True
        )
    else:
        await default_sender.send_message(
            bot, event,
            "设置失败，请检查日志",
            at_sender=True
        )

@status_cmd.handle()
async def handle_status(bot: Bot, event: GroupMessageEvent):
    """处理查看状态命令"""
    status = admin_feature.get_feature_status(str(event.group_id))
    await default_sender.send_message(bot, event, status)

@add_admin_cmd.handle()
async def handle_add_admin(bot: Bot, event: MessageEvent):
    """处理添加管理员命令"""
    args = str(event.get_message()).strip().split()
    if len(args) != 1:
        await default_sender.send_message(
            bot, event,
            "请指定要添加的管理员QQ号",
            at_sender=True
        )
        return

    user_id = args[0]
    if admin_feature.add_superuser(user_id):
        await default_sender.send_message(
            bot, event,
            f"已添加管理员: {user_id}",
            at_sender=True
        )
    else:
        await default_sender.send_message(
            bot, event,
            "添加失败，请检查日志",
            at_sender=True
        )

@remove_admin_cmd.handle()
async def handle_remove_admin(bot: Bot, event: MessageEvent):
    """处理移除管理员命令"""
    args = str(event.get_message()).strip().split()
    if len(args) != 1:
        await default_sender.send_message(
            bot, event,
            "请指定要移除的管理员QQ号",
            at_sender=True
        )
        return

    user_id = args[0]
    if admin_feature.remove_superuser(user_id):
        await default_sender.send_message(
            bot, event,
            f"已移除管理员: {user_id}",
            at_sender=True
        )
    else:
        await default_sender.send_message(
            bot, event,
            "移除失败，请检查日志",
            at_sender=True
        )
