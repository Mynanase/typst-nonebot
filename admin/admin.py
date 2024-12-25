import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER
from ..config_manager import config_manager, Feature

disable_feature = on_command("disable", permission=SUPERUSER)
enable_feature = on_command("enable", permission=SUPERUSER)

@disable_feature.handle()
async def handle_disable(bot: Bot, event: GroupMessageEvent):
    msg = str(event.get_message()).strip()
    cmd_parts = msg.split(maxsplit=1)

    if len(cmd_parts) != 2:
        await bot.send(event, "用法: /disable {feature}\n可用功能: welcome, render")
        return

    feature_name = cmd_parts[1].lower()

    try:
        feature = Feature(feature_name)
        config_manager.disable_feature(event.group_id, feature)
        await bot.send(event, f"已禁用群 {event.group_id} 的 {feature.value} 功能")
    except ValueError:
        await bot.send(event, f"无效的功能名称。可用功能: {', '.join(f.value for f in Feature)}")

@enable_feature.handle()
async def handle_enable(bot: Bot, event: GroupMessageEvent):
    msg = str(event.get_message()).strip()
    cmd_parts = msg.split(maxsplit=1)

    if len(cmd_parts) != 2:
        await bot.send(event, "用法: /enable {feature}\n可用功能: welcome, render")
        return

    feature_name = cmd_parts[1].lower()

    try:
        feature = Feature(feature_name)
        config_manager.enable_feature(event.group_id, feature)
        await bot.send(event, f"已启用群 {event.group_id} 的 {feature.value} 功能")
    except ValueError:
        await bot.send(event, f"无效的功能名称。可用功能: {', '.join(f.value for f in Feature)}")
