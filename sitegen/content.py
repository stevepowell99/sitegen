"""Reading the site: config.yml, markdown pages with YAML front matter, inline markup."""

import html as html_lib
import re

import markdown
import yaml


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_page(filepath):
    text = filepath.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        meta["body"] = body.strip()
    else:
        meta = {"body": text.strip()}
    return meta


def md(text):
    # toc gives each heading an id, so pages can link to their own sections
    return markdown.markdown(text, extensions=["extra", "tables", "smarty", "toc"])


_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline_html(text):
    """Frontmatter subheads often include raw <span class=\"hl\"> markup."""
    text = (text or "").strip()
    if not text:
        return ""
    if "<" in text and ">" in text:
        def _link(m):
            label, url = m.group(1), m.group(2)
            return (
                f'<a href="{html_lib.escape(url, quote=True)}">'
                f"{html_lib.escape(label)}</a>"
            )
        return _MD_LINK.sub(_link, text)
    return md(text)


def render_fa_icon(icon, class_name):
    icon = html_lib.escape((icon or "").strip(), quote=True)
    if not icon:
        return ""
    return f'<span class="{class_name}" aria-hidden="true"><i class="{icon}"></i></span>'


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def html_to_plain_text(html):
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(html_lib.unescape(text))
