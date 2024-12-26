from pathlib import Path

class WelcomeConfig:
    def __init__(self):
        self.current_dir = Path(__file__).parent
        self.default_template_path = self.current_dir / "welcome.typ"
        self.group_templates = {
            793548390: self.current_dir / "welcome_main.typ",
            725048672: self.current_dir / "welcome_main.typ",
        }
        self.group_template_urls = {
            793548390: "https://gist.githubusercontent.com/ParaN3xus/b0b6988a823e13b24a8398acccf034cc/raw/welcome.typ",
            725048672: "https://gist.githubusercontent.com/ParaN3xus/b0b6988a823e13b24a8398acccf034cc/raw/welcome.typ",
        }