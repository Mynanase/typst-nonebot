import nonebot
from nonebot import on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, MessageSegment
from pathlib import Path
import asyncio
import tempfile
import aiohttp
from ..config_manager import config_manager, Feature
import base64

welcome = on_notice()

# 获取当前脚本文件所在目录
current_dir = Path(__file__).parent

DEFAULT_TEMPLATE_PATH = current_dir / "welcome.typ"
GROUP_TEMPLATES = {
    793548390: current_dir / "welcome_main.typ",  # 主群的模板
    725048672: current_dir / "welcome_main.typ",
}

GROUP_TEMPLATE_URLS = {
    793548390: "https://gist.githubusercontent.com/ParaN3xus/b0b6988a823e13b24a8398acccf034cc/raw/welcome.typ",
    725048672: "https://gist.githubusercontent.com/ParaN3xus/b0b6988a823e13b24a8398acccf034cc/raw/welcome.typ",
    # 其他群的URL配置
}

async def fetch_template(url: str) -> str:
    """从网络获取模板内容"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise RuntimeError(f"Failed to fetch template: HTTP {response.status}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch template: {str(e)}")
        
async def get_template_content(group_id: int) -> str:
    """
    按优先级获取模板内容
    优先级：GROUP_TEMPLATE_URLS > GROUP_TEMPLATES > DEFAULT_TEMPLATE_PATH
    """
    # 1. 尝试从URL获取
    if group_id in GROUP_TEMPLATE_URLS:
        try:
            template_content = await fetch_template(GROUP_TEMPLATE_URLS[group_id])
            nonebot.logger.info(f"Successfully fetched template from URL for group {group_id}")
            return template_content
        except Exception as e:
            nonebot.logger.warning(f"Failed to fetch template from URL for group {group_id}: {e}, falling back to local template")
            # URL获取失败，继续尝试本地模板
    
    # 2. 尝试从本地群特定模板获取
    if group_id in GROUP_TEMPLATES:
        template_path = GROUP_TEMPLATES[group_id]
        if template_path.exists():
            nonebot.logger.info(f"Using local group template for group {group_id}")
            return template_path.read_text(encoding='utf-8')
        else:
            nonebot.logger.warning(f"Local template not found for group {group_id}: {template_path}, falling back to default template")
    
    # 3. 使用默认模板
    if DEFAULT_TEMPLATE_PATH.exists():
        nonebot.logger.info(f"Using default template for group {group_id}")
        return DEFAULT_TEMPLATE_PATH.read_text(encoding='utf-8')
    else:
        raise FileNotFoundError("Default template not found")


async def compile_typst(input_file: Path, output_file: Path) -> None:        
    process = await asyncio.create_subprocess_shell(
        f'typst compile "{input_file}" "{output_file}" --format png --ppi 300',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(f"Typst compilation failed:\n{error_msg}")
    return stdout.decode().strip()

async def send_image(bot: Bot, event: GroupIncreaseNoticeEvent, image_path: Path) -> None:
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    await bot.send(event, MessageSegment.image(f"base64://{encoded_string}"))

@welcome.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    group_id = event.group_id
    if not config_manager.is_feature_enabled(group_id, Feature.WELCOME):
        return

    user_id = event.user_id
    
    # 获取群信息和成员昵称
    group_info = await bot.get_group_info(group_id=group_id)
    group_name = group_info['group_name']
    
    member_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    nickname = member_info.get('nickname')
    
    try:
        # 按优先级获取模板内容
        template_content = await get_template_content(group_id)
        welcome_text = template_content.replace('{group_name}', group_name).replace('{name}', nickname)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "welcome.typ"
            output_file = Path(tmpdir) / "welcome.png"

            input_file.write_text(welcome_text, encoding='utf-8')

            try:
                await asyncio.wait_for(compile_typst(input_file, output_file), timeout=30)
                if not output_file.exists():
                    raise FileNotFoundError(f"Output file not found: {output_file}")
                await send_image(bot, event, output_file)
            except Exception as e:
                await bot.send(event, f"生成欢迎消息时发生错误: {str(e)}")
                
    except Exception as e:
        await bot.send(event, f"获取欢迎模板时发生错误: {str(e)}")
