"""Rewriting links in generated HTML."""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def output_depth(page_path):
    """Directory depth of the generated page for file:// relative links."""
    stripped = page_path.strip("/")
    if not stripped:
        return 0
    if "." in stripped.split("/")[-1]:
        parent = stripped.rsplit("/", 1)[0] if "/" in stripped else ""
        return parent.count("/") + 1 if parent else 0
    return stripped.count("/") + 1


def relative_site_path(target_path, from_path):
    """Relative URL from one generated page to another, ending in index.html,
    so the site also works when opened from file://."""
    from_depth = output_depth(from_path)
    prefix = "../" * from_depth if from_depth > 0 else "./"
    stripped = target_path.lstrip("/")
    if stripped == "":
        return prefix.rstrip("/") + "/index.html"
    if "." in stripped.split("/")[-1]:
        return prefix + stripped
    return prefix + stripped + "/index.html"


def make_links_relative(html, page_path):
    """Convert absolute internal URLs to relative paths for file:// preview."""
    def replace_href(m):
        attr, path = m.group(1), m.group(2)
        if path.startswith("//"):
            return m.group(0)
        fragment = ""
        if "#" in path:
            path, fragment = path.split("#", 1)
            fragment = "#" + fragment
        return f'{attr}="{relative_site_path(path, page_path)}{fragment}"'

    return re.sub(r'(href|src|action)="(/[^"]*)"', replace_href, html)


def add_external_link_attrs(html):
    """Open external site links in a new tab."""
    def replace_anchor(match):
        tag = match.group(0)
        href = match.group(1)
        if not (href.startswith("http://") or href.startswith("https://") or href.startswith("//")):
            return tag
        if 'target=' in tag:
            return tag
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'

    return re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>', replace_anchor, html)


def tag_app_links(html, cfg):
    """Append UTM params to links pointing to the app host, so signups from this site
    are attributed. Configured once via `app_utm` in config.yml; links already carrying
    utm_source are left untouched."""
    utm = {k: v for k, v in (cfg.get("app_utm") or {}).items() if v}
    if not utm:
        return html
    app_host = urlsplit(cfg.get("app_url", "")).netloc.lower()
    if not app_host:
        return html

    def add_utm(href):
        parts = urlsplit(href)
        if parts.netloc.lower() != app_host:
            return href
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        if "utm_source" in query:
            return href
        query.update(utm)
        path = parts.path or "/"
        return urlunsplit((parts.scheme, parts.netloc, path, urlencode(query), parts.fragment))

    return re.sub(r'(href|src|action)="(https?://[^"]+)"', lambda m: f'{m.group(1)}="{add_utm(m.group(2))}"', html)
