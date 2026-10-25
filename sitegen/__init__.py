"""sitegen: the static site generator behind causalmap.app and qualiainterviews.com.

A site calls sitegen.build(root, footer=..., css=..., ...) from its own build.py;
see README.md. The helpers below are exported for a site's own renderers and hooks.
"""

from .builder import build
from .content import html_to_plain_text, inline_html, md, normalize_whitespace, render_fa_icon

__version__ = "0.1.0"

__all__ = ["build", "md", "inline_html", "render_fa_icon", "normalize_whitespace", "html_to_plain_text"]
