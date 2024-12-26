import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.typing import T_State
from pathlib import Path
import asyncio
import traceback
from typing import Optional, Tuple

from ..config_manager import config_manager, Feature
from ..utils.image_sender import ImageSender
from ..utils.typst_compiler import TypstCompiler
from .config import RendererConfig
from .template_processor import TemplateProcessor

class RenderError(Exception):
    """渲染错误的基类"""
    pass

class TemplateError(RenderError):
    """模板相关错误"""
    pass

class CompilationError(RenderError):
    """编译过程错误"""
    pass

class RendererManager:
    def __init__(self):
        try:
            self.config = RendererConfig()
            self.processor = TemplateProcessor()
        except (FileNotFoundError, NotADirectoryError, ValueError) as e:
            nonebot.logger.error(f"初始化 RendererManager 失败: {e}")
            raise TemplateError(f"初始化失败: {e}")

    async def render_content(self, template_type: str, content: str) -> str:
        """
        渲染内容并返回base64编码的图片
        
        Args:
            template_type (str): 模板类型
            content (str): 要渲染的内容
            
        Returns:
            str: base64编码的图片数据
            
        Raises:
            TemplateError: 模板相关错误
            CompilationError: 编译错误
            TimeoutError: 渲染超时
        """
        try:
            # 获取并验证模板
            template_path = self.config.get_template_path(template_type)
            if not template_path.exists():
                raise TemplateError(f"模板文件不存在: {template_type}")
            
            # 读取模板内容
            try:
                template_content = template_path.read_text(encoding='utf-8')
            except Exception as e:
                raise TemplateError(f"读取模板文件失败: {e}")
            
            # 处理模板
            try:
                wrapped_content = self.processor.format_template(
                    template_content, 
                    template_type, 
                    content
                )
            except Exception as e:
                raise TemplateError(f"处理模板内容失败: {e}")
            
            # 编译文档
            return await TypstCompiler.compile_document(wrapped_content)
            
        except Exception as e:
            nonebot.logger.error(f"渲染失败:\n{traceback.format_exc()}")
            raise

class RenderHandler:
    """处理渲染请求的类"""
    
    def __init__(self):
        self.renderer = RendererManager()
    
    async def process_message(
        self, 
        bot: Bot, 
        event: MessageEvent,
        msg: str
    ) -> Optional[bool]:
        """
        处理消息并返回渲染结果
        
        Returns:
            Optional[bool]: 是否成功处理了消息
        """
        try:
            # 解析消息
            template_type, raw_content, processed_content = \
                TemplateProcessor.process_message(msg)
            
            if not template_type:
                return None
            
            # 记录渲染请求
            nonebot.logger.info(
                f"收到渲染请求:\n"
                f"用户: {event.user_id}\n"
                f"模板: {template_type}\n"
                f"内容长度: {len(processed_content)}"
            )
            
            # 渲染内容
            image_base64 = await self.renderer.render_content(
                template_type, 
                processed_content
            )
            
            # 发送结果
            await ImageSender.send_base64_image(
                bot, 
                event, 
                image_base64,
                error_msg="发送渲染结果失败"
            )
            
            return True
            
        except TemplateError as e:
            await bot.send(event, f"模板错误: {str(e)}")
        except CompilationError as e:
            await bot.send(event, f"编译错误:\n{str(e)}")
        except asyncio.TimeoutError:
            await bot.send(event, "渲染超时，请尝试简化代码或联系管理员。")
        except Exception as e:
            nonebot.logger.exception(f"渲染过程中发生未知错误: {e}")
            await bot.send(
                event, 
                f"渲染失败，发生未知错误。\n"
                f"错误信息: {str(e)}\n"
                f"请联系管理员检查日志。"
            )
        return False

# 创建全局处理器实例
render_handler = RenderHandler()
renderer = on_message(priority=5)

@renderer.handle()
async def handle_typst(bot: Bot, event: MessageEvent, state: T_State):
    """处理渲染请求的入口函数"""
    # 检查群组权限
    if isinstance(event, GroupMessageEvent):
        if not config_manager.is_feature_enabled(event.group_id, Feature.RENDER):
            return
    
    msg = event.get_plaintext()
    await render_handler.process_message(bot, event, msg)
