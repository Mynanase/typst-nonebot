from pathlib import Path
from typing import Dict, Any, Optional, Union
import shutil
from pydantic import BaseModel

class TemplateConfig(BaseModel):
    """模板配置"""
    name: str
    content: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}

class TemplateManager:
    """模板管理工具类"""
    def __init__(self, template_dir: Union[str, Path]):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, TemplateConfig] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """加载所有模板"""
        for file in self.template_dir.glob("*.typ"):
            try:
                content = file.read_text(encoding='utf-8')
                self._templates[file.stem] = TemplateConfig(
                    name=file.stem,
                    content=content
                )
            except Exception as e:
                print(f"加载模板 {file.name} 失败: {e}")

    def get_template(self, name: str) -> Optional[TemplateConfig]:
        """获取模板"""
        return self._templates.get(name)

    def save_template(self, name: str, content: str, description: Optional[str] = None) -> bool:
        """保存模板"""
        try:
            template_path = self.template_dir / f"{name}.typ"
            template_path.write_text(content, encoding='utf-8')
            
            self._templates[name] = TemplateConfig(
                name=name,
                content=content,
                description=description
            )
            return True
        except Exception as e:
            print(f"保存模板 {name} 失败: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """删除模板"""
        try:
            template_path = self.template_dir / f"{name}.typ"
            if template_path.exists():
                template_path.unlink()
            self._templates.pop(name, None)
            return True
        except Exception as e:
            print(f"删除模板 {name} 失败: {e}")
            return False

    def list_templates(self) -> Dict[str, TemplateConfig]:
        """列出所有模板"""
        return self._templates

    def backup_templates(self, backup_dir: Union[str, Path]) -> bool:
        """备份所有模板"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            for name, template in self._templates.items():
                dest_path = backup_path / f"{name}.typ"
                dest_path.write_text(template.content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"备份模板失败: {e}")
            return False

    def restore_templates(self, backup_dir: Union[str, Path]) -> bool:
        """从备份恢复模板"""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return False
            
            # 清空当前模板
            self._templates.clear()
            for file in self.template_dir.glob("*.typ"):
                file.unlink()
            
            # 恢复备份
            for file in backup_path.glob("*.typ"):
                shutil.copy2(file, self.template_dir)
            
            # 重新加载
            self._load_templates()
            return True
        except Exception as e:
            print(f"恢复模板失败: {e}")
            return False

    def render_template(self, name: str, variables: Dict[str, Any]) -> Optional[str]:
        """渲染模板（简单变量替换）"""
        template = self.get_template(name)
        if not template:
            return None
            
        content = template.content
        for key, value in variables.items():
            # 支持两种变量格式：${key} 和 {key}
            content = content.replace(f"${{{key}}}", str(value))
            content = content.replace(f"{{{key}}}", str(value))
        
        return content
