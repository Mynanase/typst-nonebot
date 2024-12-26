from pathlib import Path
import nonebot

class RendererConfig:
    def __init__(self):
        self.current_dir = Path(__file__).parent
        self.template_dir = self.current_dir / "templates"
        
        # 确保模板目录存在
        if not self.template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found at: {self.template_dir}\n"
                f"Please ensure the 'templates' directory exists in {self.current_dir}"
            )
        
        if not self.template_dir.is_dir():
            raise NotADirectoryError(
                f"Expected {self.template_dir} to be a directory"
            )

        self.templates = {
            'typ': self.template_dir / "typ.typ",
            'teq': self.template_dir / "teq.typ",
            'typc': self.template_dir / "typc.typ",
        }
        
        # 在初始化时验证所有模板
        self._validate_templates()

    def _validate_templates(self) -> None:
        """
        验证所有模板文件是否存在和可访问
        
        Raises:
            FileNotFoundError: 当模板文件不存在时
        """
        missing_templates = []
        for template_type, template_path in self.templates.items():
            if not template_path.exists():
                missing_templates.append((template_type, template_path))
            elif not template_path.is_file():
                raise ValueError(f"Template path exists but is not a file: {template_path}")
        
        if missing_templates:
            error_msg = "Missing template files:\n"
            for template_type, path in missing_templates:
                error_msg += f"- {template_type}: {path}\n"
            error_msg += f"\nPlease ensure all template files exist in {self.template_dir}"
            raise FileNotFoundError(error_msg)

    def get_template_path(self, template_type: str) -> Path:
        """
        获取模板文件路径
        
        Args:
            template_type: 模板类型
            
        Returns:
            Path: 模板文件路径
            
        Raises:
            ValueError: 如果模板类型不存在或文件不可访问
        """
        if template_type not in self.templates:
            raise ValueError(
                f"Invalid template type: '{template_type}'\n"
                f"Available templates: {list(self.templates.keys())}"
            )
        
        template_path = self.templates[template_type]
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}\n"
                f"Please ensure the file exists in {self.template_dir}"
            )
        
        return template_path