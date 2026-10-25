"""Files written beside the pages, and syncing the build into dist/."""

import html as html_lib
import os
import re
import shutil
import stat
from pathlib import Path


def site_url_for(base, path):
    """Absolute canonical URL for a page path. Directory paths get a trailing slash."""
    base = base.rstrip("/")
    stripped = path.strip("/")
    if not stripped:
        return base + "/"
    if "." in stripped.split("/")[-1]:
        return f"{base}/{stripped}"
    return f"{base}/{stripped}/"


def build_sitemap_xml(pages, base):
    """XML sitemap of indexable pages (skips redirects and the 404 page)."""
    urls = []
    for page in sorted(pages, key=lambda p: p["_path"]):
        if page.get("redirect"):
            continue
        path = page["_path"]
        if path == "/404.html":
            continue
        loc = html_lib.escape(site_url_for(base, path), quote=True)
        date = str(page.get("date") or "").strip()
        lastmod = f"\n    <lastmod>{date}</lastmod>" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else ""
        urls.append(f"  <url>\n    <loc>{loc}</loc>{lastmod}\n  </url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def build_robots_txt(base):
    return (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {base.rstrip('/')}/sitemap.xml\n"
    )


def redirect_rules_for(path, redirect):
    src = path.rstrip("/") or "/"
    if src == "/":
        return []
    return [
        f"{src} {redirect} 301",
        f"{src}/ {redirect} 301",
    ]


def remove_tree(path):
    # Drive marks a folder read-only once it adds a desktop.ini, and that blocks rmdir.
    for p in (path, *path.rglob("*")):
        os.chmod(p, p.stat().st_mode | stat.S_IWRITE)
    shutil.rmtree(path)


def sync_tree(src, dst):
    """Make dst match src, rewriting only files whose bytes differ.

    dist/ sits in a Google Drive mirror. Deleting and recreating it while Drive is
    still uploading the previous build orphans those files into the Drive root, so
    dst itself is never removed. Returns (files written, entries removed)."""
    written = removed = 0
    for root, _dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            s, d = Path(root) / name, dst / rel / name
            if d.is_dir():
                remove_tree(d)
            if not d.is_file() or d.read_bytes() != s.read_bytes():
                shutil.copy2(s, d)
                written += 1
    for root, dirs, files in os.walk(dst):
        rel = Path(root).relative_to(dst)
        for name in files:
            # Drive for Desktop writes desktop.ini into every folder; leave it be.
            if name != "desktop.ini" and not (src / rel / name).is_file():
                (Path(root) / name).unlink()
                removed += 1
        for name in list(dirs):
            if not (src / rel / name).is_dir():
                remove_tree(Path(root) / name)
                dirs.remove(name)
                removed += 1
    return written, removed
