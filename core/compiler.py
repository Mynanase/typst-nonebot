import asyncio
from pathlib import Path
import base64
import tempfile
import re
from typing import Optional
from pydantic import BaseModel

class CompilerConfig(BaseModel):
    """编译器配置"""
    timeout: int = 30
    format: str = "png"
    ppi: int = 300
    compiler_path: str = "typst"

class CompileResult(BaseModel):
    """编译结果"""
    success: bool
    content: Optional[str] = None  # base64编码的图片数据
    error: Optional[str] = None    # 错误信息

class TypstCompiler:
    """Typst文档编译器"""
    def __init__(self, config: Optional[CompilerConfig] = None):
        self.config = config or CompilerConfig()

    async def compile(self, content: str) -> CompileResult:
        """编译Typst文档并返回结果"""
        try:
            return CompileResult(
                success=True,
                content=await self._compile_document(content)
            )
        except Exception as e:
            return CompileResult(
                success=False,
                error=str(e)
            )

    async def _compile_document(self, content: str) -> str:
        """编译文档并返回base64编码的图片"""
        async def compile_task():
            with tempfile.TemporaryDirectory() as tmpdir:
                input_file = Path(tmpdir) / "input.typ"
                output_file = Path(tmpdir) / f"output.{self.config.format}"
                
                input_file.write_text(content, encoding='utf-8')
                await self._run_compiler(input_file, output_file)
                
                return base64.b64encode(output_file.read_bytes()).decode('utf-8')
        
        try:
            return await asyncio.wait_for(compile_task(), timeout=self.config.timeout)
        except asyncio.TimeoutError:
            raise RuntimeError("编译超时，请尝试简化代码")

    async def _run_compiler(self, input_file: Path, output_file: Path) -> None:
        """运行编译器进程"""
        cmd = (
            f'{self.config.compiler_path} compile "{input_file}" "{output_file}" '
            f'--format {self.config.format} --ppi {self.config.ppi}'
        )
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            formatted_error = self._format_error_message(error_msg, str(input_file))
            raise RuntimeError(f"Typst编译错误：\n{formatted_error}")

    def _format_error_message(self, error_msg: str, file_path: str) -> str:
        """格式化错误信息"""
        error_msg = error_msg.replace(file_path, "input.typ")
        error_lines = []
        
        for line in error_msg.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("error:"):
                error_lines.append(line)
            elif "at" in line and "input.typ" in line:
                if match := re.search(r"at .*:(\d+):(\d+)", line):
                    line_num, col_num = match.groups()
                    error_lines.append(f"位置：第 {line_num} 行，第 {col_num} 列")
            else:
                error_lines.append(line)
                
        return "\n".join(error_lines)

# 创建默认编译器实例
default_compiler = TypstCompiler()
