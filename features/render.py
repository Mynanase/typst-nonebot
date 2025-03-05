"""Render feature for the Typst bot."""

from pathlib import Path
from nonebot import on_message
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent

from ..core import TypstCompiler, CompilerConfig, TemplateManager, default_sender
from ..models import RenderConfig, RenderRequest, RenderResult, FeatureType
from .admin import admin_feature

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="Typst渲染",
    description="渲染Typst代码、数学公式和代码块",
    usage="""
    命令格式：
    typ <Typst代码> - 渲染Typst代码
    teq <数学公式> - 渲染数学公式
    typc <代码> - 渲染代码块（默认Python语法高亮）
    
    示例：
    typ #lorem(10)
    teq x = (-b +- sqrt(b^2 - 4ac))/(2a)
    typc def hello(): print("Hello, World!")
    """,
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "author": "Your Name",
        "version": "0.2.0",
        "priority": 5,
    },
)

class RenderFeature:
    """渲染功能"""
    def __init__(self, config: RenderConfig):
        self.config = config
        
        # 初始化编译器
        self.compiler = TypstCompiler(
            CompilerConfig(
                timeout=config.timeout,
                ppi=config.ppi
            )
        )
        
        # 初始化模板管理器
        self.template_manager = TemplateManager(config.template_dir)
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """初始化默认模板"""
        default_templates = {
            'typ.typ': """
#set page(
    width: auto,
    height: auto,
    margin: 0.5em
)
#show raw: set text(font: "JetBrains Mono")

{code}
""",
            'teq.typ': """
#set page(
    width: auto,
    height: auto,
    margin: 0.5em
)
$ {equation} $
""",
            'typc.typ': """
#set page(
    width: auto,
    height: auto,
    margin: 0.5em
)
#show raw: set text(font: "JetBrains Mono")

```python
{script}
```
"""
        }
        
        for name, content in default_templates.items():
            if not self.template_manager.get_template(name.replace('.typ', '')):
                self.template_manager.save_template(
                    name.replace('.typ', ''),
                    content
                )

    def parse_message(self, msg: str) -> RenderRequest | None:
        """解析消息内容"""
        msg = msg.strip()
        
        # 解析命令和内容
        if msg.startswith(("typ ", "teq ", "typc ")):
            parts = msg.split(maxsplit=1)
            if len(parts) != 2:
                return None
                
            template_type = parts[0]
            content = parts[1].strip()
            
            # 特殊处理数学公式
            if template_type == "teq":
                raw_content = content
                content = content.replace("$", r"\$")
            else:
                raw_content = content
            
            return RenderRequest(
                template_type=template_type,
                content=content,
                raw_content=raw_content
            )
        
        return None

    async def render(self, request: RenderRequest) -> RenderResult:
        """渲染内容"""
        try:
            # 获取模板
            template = self.template_manager.get_template(request.template_type)
            if not template:
                return RenderResult(
                    success=False,
                    error=f"未找到模板: {request.template_type}"
                )
            
            # 渲染模板
            rendered_content = self.template_manager.render_template(
                request.template_type,
                {
                    "code": request.content,
                    "equation": request.content,
                    "script": request.content
                }
            )
            if not rendered_content:
                return RenderResult(
                    success=False,
                    error="模板渲染失败"
                )
            
            # 编译文档
            result = await self.compiler.compile(rendered_content)
            if not result.success:
                return RenderResult(
                    success=False,
                    error=f"编译错误: {result.error}"
                )
            
            return RenderResult(
                success=True,
                image_data=result.content
            )
            
        except Exception as e:
            return RenderResult(
                success=False,
                error=f"渲染失败: {str(e)}"
            )

# 确保数据目录存在
DATA_DIR = Path("src/plugins/typst_bot/data/render")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 从配置文件加载配置
from ..core.config import config_manager

feature_config = config_manager.get_feature_config("render")
config = RenderConfig(**feature_config)

# 创建功能实例
render_feature = RenderFeature(config)

# 消息处理器
render_handler = on_message(priority=5)

@render_handler.handle()
async def handle_render(bot: Bot, event: MessageEvent):
    """处理渲染请求"""
    # 检查群组权限
    if isinstance(event, GroupMessageEvent):
        if not admin_feature.is_feature_enabled(event.group_id, FeatureType.RENDER):
            return
    
    # 解析消息
    msg = event.get_plaintext()
    request = render_feature.parse_message(msg)
    if not request:
        return
    
    # 渲染内容
    result = await render_feature.render(request)
    
    # 发送结果
    if result.success and result.image_data:
        await default_sender.send_image(
            bot,
            event,
            result.image_data,
            "发送渲染结果失败"
        )
    else:
        await default_sender.send_message(
            bot,
            event,
            result.error or "渲染失败",
            at_sender=True
        )
