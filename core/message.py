from typing import Union, Optional
from pathlib import Path
import base64
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Event, Message, GroupMessageEvent
from pydantic import BaseModel

class MessageResult(BaseModel):
    """消息发送结果"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

class MessageSender:
    """消息发送工具类"""
    @staticmethod
    async def send_message(
        bot: Bot,
        event: Event,
        message: Union[str, Message, MessageSegment],
        at_sender: bool = False
    ) -> MessageResult:
        """发送消息"""
        try:
            if isinstance(message, str):
                message = Message(message)
            
            if at_sender and isinstance(event, GroupMessageEvent):
                message = MessageSegment.at(event.user_id) + message
            
            result = await bot.send(event, message)
            return MessageResult(
                success=True,
                message_id=str(result)
            )
        except Exception as e:
            return MessageResult(
                success=False,
                error=str(e)
            )

    @staticmethod
    async def send_image(
        bot: Bot,
        event: Event,
        image: Union[str, Path, bytes],
        error_msg: str = "发送图片失败"
    ) -> MessageResult:
        """发送图片
        
        Args:
            image: 可以是base64字符串、文件路径或字节数据
        """
        try:
            if isinstance(image, Path):
                image = image.read_bytes()
            elif isinstance(image, str) and not image.startswith("base64://"):
                # 如果是base64字符串但没有前缀
                image = f"base64://{image}"
            elif isinstance(image, bytes):
                image = f"base64://{base64.b64encode(image).decode()}"
            
            result = await bot.send(
                event,
                MessageSegment.image(image)
            )
            return MessageResult(
                success=True,
                message_id=str(result)
            )
        except Exception as e:
            return MessageResult(
                success=False,
                error=f"{error_msg}: {e}"
            )

    @staticmethod
    async def recall_message(
        bot: Bot,
        message_id: Union[str, int]
    ) -> MessageResult:
        """撤回消息"""
        try:
            await bot.delete_msg(message_id=message_id)
            return MessageResult(success=True)
        except Exception as e:
            return MessageResult(
                success=False,
                error=f"撤回消息失败: {e}"
            )

    @staticmethod
    async def send_group_message(
        bot: Bot,
        group_id: Union[str, int],
        message: Union[str, Message, MessageSegment]
    ) -> MessageResult:
        """发送群组消息"""
        try:
            if isinstance(message, str):
                message = Message(message)
            
            result = await bot.send_group_msg(
                group_id=int(group_id),
                message=message
            )
            return MessageResult(
                success=True,
                message_id=str(result)
            )
        except Exception as e:
            return MessageResult(
                success=False,
                error=f"发送群组消息失败: {e}"
            )

# 创建默认发送器实例
default_sender = MessageSender()
