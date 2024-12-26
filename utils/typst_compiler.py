import asyncio
from pathlib import Path
import base64
import tempfile
from typing import Tuple
import re

class TypstCompiler:
    @staticmethod
    def format_error_message(error_msg: str, file_path: str) -> str:
        """格式化错误信息，使其更易读"""
        # 移除临时文件路径
        error_msg = error_msg.replace(file_path, "input.typ")
        
        # 提取关键错误信息
        error_lines = error_msg.split('\n')
        formatted_lines = []
        
        for line in error_lines:
            # 移除不必要的文件路径信息
            if line.strip().startswith("error:"):
                formatted_lines.append(line.strip())
            elif "at" in line and "input.typ" in line:
                # 提取行号和列号信息
                match = re.search(r"at .*:(\d+):(\d+)", line)
                if match:
                    line_num, col_num = match.groups()
                    formatted_lines.append(f"位置：第 {line_num} 行，第 {col_num} 列")
            elif line.strip():
                formatted_lines.append(line.strip())
                
        return "\n".join(formatted_lines)

    @staticmethod
    async def compile_document(content: str, timeout: int = 30) -> str:
        """编译Typst文档并返回base64编码的图片"""
        async with asyncio.timeout(timeout):
            with tempfile.TemporaryDirectory() as tmpdir:
                input_file = Path(tmpdir) / "input.typ"
                output_file = Path(tmpdir) / "output.png"
                
                try:
                    input_file.write_text(content, encoding='utf-8')
                    await TypstCompiler._run_compiler(input_file, output_file)
                    return base64.b64encode(output_file.read_bytes()).decode('utf-8')
                except Exception as e:
                    raise RuntimeError(f"编译失败：\n{str(e)}")

    @staticmethod
    async def _run_compiler(input_file: Path, output_file: Path) -> None:
        process = await asyncio.create_subprocess_shell(
            f'typst compile "{input_file}" "{output_file}" --format png --ppi 300',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            formatted_error = TypstCompiler.format_error_message(error_msg, str(input_file))
            raise RuntimeError(f"Typst 编译错误：\n{formatted_error}")