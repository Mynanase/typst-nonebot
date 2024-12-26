import aiohttp
from pathlib import Path
import nonebot
from typing import Optional

class TemplateManager:
    @staticmethod
    async def fetch_template(url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                raise RuntimeError(f"Failed to fetch template: HTTP {response.status}")

    @staticmethod
    async def get_template_content(template_path: Path, template_url: Optional[str] = None) -> str:
        if template_url:
            try:
                return await TemplateManager.fetch_template(template_url)
            except Exception as e:
                nonebot.logger.warning(f"URL template fetch failed: {e}")

        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        raise FileNotFoundError(f"Template not found at {template_path}")