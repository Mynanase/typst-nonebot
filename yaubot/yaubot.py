import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.typing import T_State
from pathlib import Path
from datetime import datetime
import opencc
import traceback

from ..config_manager import config_manager, Feature
from ..utils.image_sender import ImageSender
from ..utils.typst_compiler import TypstCompiler

class YauBotError(Exception):
    """YauBot 相关错误的基类"""
    pass

class TemplateError(YauBotError):
    """模板相关错误"""
    pass

class YauBotManager:
    """处理 YauBot 功能的管理类"""
    
    def __init__(self):
        self.converter = opencc.OpenCC('s2hk')  # 简体中文转香港繁体中文
        self.template_path = Path(__file__).parent / "yau.typ"
        
        # 验证模板文件存在
        if not self.template_path.exists():
            raise TemplateError(f"模板文件不存在: {self.template_path}")
        
        # 读取模板内容
        try:
            self.template_content = self.template_path.read_text(encoding='utf-8')
        except Exception as e:
            raise TemplateError(f"读取模板文件失败: {e}")

    def _convert_text(self, text: str) -> str:
        """转换文本为香港繁体中文"""
        try:
            return self.converter.convert(text.strip())
        except Exception as e:
            nonebot.logger.error(f"文本转换失败: {e}")
            raise YauBotError(f"文本转换失败: {e}")

    def _format_template(self, text: str) -> str:
        """格式化模板内容"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.template_content.format(
                text=text,
                datetime_now=now
            )
        except Exception as e:
            nonebot.logger.error(f"模板格式化失败: {e}")
            raise TemplateError(f"模板格式化失败: {e}")

    async def process_message(self, text: str) -> str:
        """
        处理消息并返回渲染结果
        
        Args:
            text: 要处理的文本内容
            
        Returns:
            str: base64编码的图片数据
            
        Raises:
            YauBotError: 处理过程中的错误
        """
        try:
            # 转换文本
            converted_text = self._convert_text(text)
            
            # 格式化模板
            formatted_content = self._format_template(converted_text)
            
            # 编译生成图片
            return await TypstCompiler.compile_document(formatted_content)
            
        except Exception as e:
            nonebot.logger.error(f"处理消息失败:\n{traceback.format_exc()}")
            raise YauBotError(f"处理消息失败: {e}")

class YauBotHandler:
    """处理 YauBot 消息的类"""
    
    def __init__(self):
        self.manager = YauBotManager()

    def _parse_command(self, msg: str) -> tuple[bool, str]:
        """解析命令"""
        msg = msg.strip()
        if msg.startswith("yau "):
            return True, msg[4:].strip()
        return False, ""

    async def handle_message(self, bot: Bot, event: MessageEvent) -> None:
        """处理消息"""
        try:
            msg = event.get_plaintext()
            is_command, content = self._parse_command(msg)
            
            if not is_command:
                return
                
            # 记录处理请求
            nonebot.logger.info(
                f"处理 YauBot 请求:\n"
                f"用户: {event.user_id}\n"
                f"内容长度: {len(content)}"
            )
            
            # 处理消息并发送结果
            image_base64 = await self.manager.process_message(content)
            await ImageSender.send_base64_image(
                bot,
                event,
                image_base64,
                error_msg="发送结果失败"
            )
            
        except YauBotError as e:
            await bot.send(event, f"处理失败: {str(e)}")
        except Exception as e:
            nonebot.logger.exception(f"处理消息时发生未知错误: {e}")
            await bot.send(
                event,
                f"发生未知错误: {str(e)}\n请联系管理员检查日志。"
            )

# 创建全局处理器实例
yau_handler = YauBotHandler()
yaubot = on_message(priority=5)

@yaubot.handle()
async def handle_message(bot: Bot, event: MessageEvent, state: T_State):
    """消息处理入口"""
    # 检查群组权限
    if isinstance(event, GroupMessageEvent):
        if not config_manager.is_feature_enabled(event.group_id, Feature.YAUBOT):
            return
    
    await yau_handler.handle_message(bot, event)
