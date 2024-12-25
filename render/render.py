import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.typing import T_State
from pathlib import Path
import asyncio
import tempfile
import base64
import opencc
from ..config_manager import config_manager, Feature

renderer = on_message(priority=5)
converter = opencc.OpenCC('s2hk') # 简体中文转香港繁体中文

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

async def send_image(bot: Bot, event: MessageEvent, image_path: Path) -> None:
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    await bot.send(event, MessageSegment.image(f"base64://{encoded_string}"))

@renderer.handle()
async def handle_typst(bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, GroupMessageEvent):
        if not config_manager.is_feature_enabled(event.group_id, Feature.RENDER):
            return

    msg = event.get_plaintext().strip()
    
    current_dir = Path(__file__).parent

    if msg.startswith("typ "):
        code = msg[4:].strip()
        template_file = current_dir / "typ.typ"
    elif msg.startswith("teq "):
        equation = msg[4:].strip()
        equation = equation.replace("$", r"\$")
        template_file = current_dir / "teq.typ"
    elif msg.startswith("typc "):
        script = msg[5:].strip()
        template_file = current_dir / "typc.typ"
    elif msg.startswith("yau "):
        text = msg[4:].strip()
        text = converter.convert(text)
        template_file = current_dir / "yau.typ"
    else:
        return  # 非相关命令，忽略

    if not template_file.exists():
        await bot.send(event, f"模板文件 {template_file} 不存在。")
        return

    # 读取模板并填充内容
    template_content = template_file.read_text(encoding='utf-8')
    if msg.startswith("typ "):
        wrapped_code = template_content.format(code=code)
    elif msg.startswith("teq "):
        wrapped_code = template_content.format(equation=equation)
    elif msg.startswith("typc "):
        wrapped_code = template_content.format(script=script)
    elif msg.startswith("yau "):  # 新增 yau 命令处理
        wrapped_code = template_content.format(text=text)
    else:
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.typ"
        output_file = Path(tmpdir) / "output.png"

        input_file.write_text(wrapped_code, encoding='utf-8')

        try:
            await asyncio.wait_for(compile_typst(input_file, output_file), timeout=30)
            if not output_file.exists():
                raise FileNotFoundError(f"Output file not found: {output_file}")
            await send_image(bot, event, output_file)
        except asyncio.TimeoutError:
            await bot.send(event, "渲染超时，请尝试简化你的代码。")
        except FileNotFoundError as e:
            await bot.send(event, f"渲染失败: {str(e)}")
        except Exception as e:
            await bot.send(event, f"发生错误: {str(e)}")
