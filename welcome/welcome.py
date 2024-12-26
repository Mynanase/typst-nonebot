# welcome/welcome.py
import nonebot
from nonebot import on_notice, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11.event import Event
from typing import Optional, Dict, Any
import traceback
import asyncio

from ..utils.image_sender import ImageSender
from ..utils.typst_compiler import TypstCompiler
from ..config_manager import config_manager, Feature
from .config import WelcomeConfig
from .template_manager import TemplateManager

class WelcomeError(Exception):
    """欢迎功能相关错误的基类"""
    pass

class TemplateError(WelcomeError):
    """模板相关错误"""
    pass

class WelcomeManager:
    def __init__(self):
        try:
            self.config = WelcomeConfig()
        except Exception as e:
            nonebot.logger.error(f"初始化 WelcomeManager 失败: {e}")
            raise WelcomeError(f"初始化失败: {e}")

    async def _get_group_info(self, bot: Bot, group_id: int) -> Dict[str, Any]:
        """获取群组信息"""
        try:
            return await bot.get_group_info(group_id=group_id)
        except Exception as e:
            nonebot.logger.error(f"获取群组信息失败 (群号: {group_id}): {e}")
            raise WelcomeError(f"获取群组信息失败: {e}")

    async def _get_member_info(self, bot: Bot, group_id: int, user_id: int) -> Dict[str, Any]:
        """获取成员信息"""
        try:
            return await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        except Exception as e:
            nonebot.logger.error(f"获取成员信息失败 (群号: {group_id}, 用户: {user_id}): {e}")
            raise WelcomeError(f"获取成员信息失败: {e}")

    async def _get_template(self, group_id: int) -> str:
        """获取欢迎模板"""
        try:
            template_path = self.config.group_templates.get(
                group_id, 
                self.config.default_template_path
            )
            template_url = self.config.group_template_urls.get(group_id)
            
            return await TemplateManager.get_template_content(template_path, template_url)
        except Exception as e:
            nonebot.logger.error(f"获取模板失败 (群号: {group_id}): {e}")
            raise TemplateError(f"获取模板失败: {e}")

    def _format_template(self, template: str, group_name: str, nickname: str) -> str:
        """格式化模板内容"""
        try:
            return template.replace(
                '{group_name}', group_name
            ).replace(
                '{name}', nickname
            )
        except Exception as e:
            nonebot.logger.error(f"格式化模板失败: {e}")
            raise TemplateError(f"格式化模板失败: {e}")

    async def generate_welcome_message(self, bot: Bot, group_id: int, user_id: int) -> str:
        """
        生成欢迎消息
        
        Args:
            bot: Bot 实例
            group_id: 群号
            user_id: 用户 ID
            
        Returns:
            str: base64 编码的图片数据
            
        Raises:
            WelcomeError: 生成欢迎消息时的错误
        """
        try:
            # 获取群组和成员信息
            group_info = await self._get_group_info(bot, group_id)
            member_info = await self._get_member_info(bot, group_id, user_id)
            
            # 获取并处理模板
            template_content = await self._get_template(group_id)
            welcome_text = self._format_template(
                template_content,
                group_info['group_name'],
                member_info.get('nickname', str(user_id))
            )
            
            # 编译生成图片
            return await TypstCompiler.compile_document(welcome_text)
            
        except Exception as e:
            nonebot.logger.error(f"生成欢迎消息失败:\n{traceback.format_exc()}")
            raise WelcomeError(f"生成欢迎消息失败: {e}")

class WelcomeHandler:
    """处理欢迎消息的类"""
    
    def __init__(self):
        self.manager = WelcomeManager()
    
    async def handle_welcome(self, bot: Bot, event: Event, user_id: int) -> None:
        """处理欢迎消息请求"""
        group_id = getattr(event, 'group_id', None)
        if not group_id:
            return
            
        try:
            # 记录欢迎消息请求
            nonebot.logger.info(
                f"处理欢迎消息:\n"
                f"群号: {group_id}\n"
                f"目标用户: {user_id}"
            )
            
            # 生成并发送欢迎消息
            image_base64 = await self.manager.generate_welcome_message(bot, group_id, user_id)
            await ImageSender.send_base64_image(
                bot, 
                event, 
                image_base64, 
                error_msg="发送欢迎消息失败"
            )
            
        except WelcomeError as e:
            error_msg = f"欢迎消息生成失败: {str(e)}"
            nonebot.logger.error(error_msg)
            await bot.send(event, error_msg)
        except asyncio.TimeoutError:
            await bot.send(event, "生成欢迎消息超时，请稍后重试。")
        except Exception as e:
            error_msg = f"发生未知错误: {str(e)}"
            nonebot.logger.exception(f"欢迎消息处理失败: {e}")
            await bot.send(event, f"{error_msg}\n请联系管理员检查日志。")

# 创建全局处理器实例
welcome_handler = WelcomeHandler()
welcome = on_notice()
welcome_cmd = on_command("welcome")

@welcome.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    """处理新成员入群事件"""
    if not config_manager.is_feature_enabled(event.group_id, Feature.WELCOME):
        return
    await welcome_handler.handle_welcome(bot, event, event.user_id)

@welcome_cmd.handle()
async def handle_welcome_command(bot: Bot, event: GroupMessageEvent):
    """处理欢迎命令"""
    if not config_manager.is_feature_enabled(event.group_id, Feature.WELCOME):
        await welcome_cmd.finish("该群未启用欢迎功能")
        return

    target_user_id = event.reply.sender.user_id if event.reply else event.user_id
    await welcome_handler.handle_welcome(bot, event, target_user_id)
