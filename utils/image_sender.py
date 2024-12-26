from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Event
import nonebot
from typing import Union

class ImageSender:
    @staticmethod
    async def send_base64_image(bot: Bot, event: Event, image_base64: str, error_msg: str = "发送图片时发生错误") -> bool:
        try:
            await bot.send(event, MessageSegment.image(f"base64://{image_base64}"))
            return True
        except Exception as e:
            nonebot.logger.error(f"{error_msg}: {str(e)}")
            await bot.send(event, f"{error_msg}: {str(e)}")
            return False