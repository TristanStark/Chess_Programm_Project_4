from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class ReportRenderer:
    def __init__(self, templates_directory: Path | str):
        self.templates_directory = Path(templates_directory)
        self.environment = Environment(
            loader=FileSystemLoader(str(self.templates_directory)),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render(self, template_name: str, context: dict) -> str:
        template = self.environment.get_template(template_name)
        return template.render(**context)
