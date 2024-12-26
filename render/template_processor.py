from pathlib import Path
from typing import Tuple, Optional

class TemplateProcessor:
    @staticmethod
    def process_message(msg: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        处理消息，返回(模板类型, 内容, 处理后的内容)
        """
        msg = msg.strip()
        
        if msg.startswith("typ "):
            return 'typ', msg[4:].strip(), msg[4:].strip()
        elif msg.startswith("teq "):
            equation = msg[4:].strip()
            return 'teq', equation, equation.replace("$", r"\$")
        elif msg.startswith("typc "):
            return 'typc', msg[5:].strip(), msg[5:].strip()
        
        return None, None, None

    @staticmethod
    def format_template(template_content: str, template_type: str, content: str) -> str:
        """
        根据模板类型格式化内容
        """
        if template_type == 'typ':
            return template_content.format(code=content)
        elif template_type == 'teq':
            return template_content.format(equation=content)
        elif template_type == 'typc':
            return template_content.format(script=content)
        raise ValueError(f"Unknown template type: {template_type}")