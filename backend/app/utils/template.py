"""
Config file templating using Jinja2.
Used for generating Nginx vhosts, PHP-FPM pools, DNS zones, etc.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape([]),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def render_template(template_name: str, **context) -> str:
    """
    Render a Jinja2 template with the given context.
    
    Args:
        template_name: Name of template file (e.g., 'nginx_vhost.conf.j2')
        **context: Template variables
    
    Returns:
        Rendered template string
    """
    template = _env.get_template(template_name)
    return template.render(**context)


def render_string_template(template_str: str, **context) -> str:
    """Render a template from a string instead of a file."""
    from jinja2 import Template
    template = Template(template_str)
    return template.render(**context)
