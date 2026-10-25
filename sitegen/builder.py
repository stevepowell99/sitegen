"""The build: content/*.md to dist/, through a temporary folder outside Google Drive."""

import shutil
import tempfile
from pathlib import Path

from .content import load_config, parse_page
from .css import build_css
from .layout import build_nav, page_template, redirect_template
from .links import add_external_link_attrs, make_links_relative, tag_app_links
from .output import build_robots_txt, build_sitemap_xml, redirect_rules_for, sync_tree
from .search import build_search_index
from .sections import SECTION_RENDERERS, render_sections

# Netlify serves this page at whatever URL was missing, at any depth, so its links
# stay root-absolute rather than relative to where the file sits.
NOT_FOUND_PATH = "/404.html"


def build(root, footer, css, renderers=None, extend_pages=None, after_write=None):
    """Build the site whose config.yml and content/ are in `root`.

    footer(cfg) returns the site's footer HTML.
    css is a dict of the site's CSS values and blocks (see sitegen.css).
    renderers adds or replaces section renderers: {type: fn(section, cfg, pages)}.
    extend_pages(pages, cfg) runs once every page is rendered, before the search
    index and nav are built; it may change pages or append generated ones (each
    with `_path` and `_content_html`).
    after_write(output_dir) runs once pages and content/assets are in the temporary
    output folder, before it is synced into dist/.
    """
    root = Path(root)
    cfg = load_config(root / "config.yml")
    input_dir = root / cfg.get("input_dir", "content")
    final_dir = root / cfg.get("output_dir", "dist")

    # Build outside Drive, then sync into dist/ (see sync_tree).
    output_dir = Path(tempfile.gettempdir()) / f"build-{root.name}"
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_renderers = dict(SECTION_RENDERERS)
    all_renderers.update(renderers or {})

    pages = []
    md_files = sorted(p for p in input_dir.rglob("*.md") if "assets" not in p.parts)
    for mdfile in md_files:
        page = parse_page(mdfile)
        page["_file"] = str(mdfile.relative_to(input_dir)).replace("\\", "/")
        # Default path respects nested folders: content/blog/foo.md -> /blog/foo.
        default_path = "/" + str(mdfile.relative_to(input_dir).with_suffix("")).replace("\\", "/")
        page["_path"] = page.get("path", default_path)
        pages.append(page)

    # Render after every page is parsed, so a section can list other pages.
    for page in pages:
        if not page.get("redirect"):
            page["_content_html"] = render_sections(page, cfg, pages, all_renderers)

    if extend_pages:
        extend_pages(pages, cfg)

    search_index = build_search_index(pages)
    nav_html = build_nav(pages, cfg)
    footer_html = footer(cfg)
    css_text = build_css(cfg, css)
    redirect_rules = []

    for page in pages:
        title = page.get("title", "Untitled")
        meta_desc = page.get("description", "")
        path = page["_path"]
        redirect = page.get("redirect")
        if redirect:
            html = redirect_template(title, redirect, cfg)
            redirect_rules.extend(redirect_rules_for(path, redirect))
        else:
            html = page_template(
                title,
                nav_html,
                page["_content_html"],
                footer_html,
                cfg,
                css_text,
                meta_desc,
                search_index if path == "/search" else None,
            )
            if path != NOT_FOUND_PATH:
                html = make_links_relative(html, path)
        html = add_external_link_attrs(html)
        html = tag_app_links(html, cfg)
        if path == "/":
            out_file = output_dir / "index.html"
        elif "." in path.strip("/").split("/")[-1]:
            out_file = output_dir / path.strip("/")
            out_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = output_dir / path.strip("/")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "index.html"

        out_file.write_text(html, encoding="utf-8")
        print(f"  {path} -> {final_dir.name}/{out_file.relative_to(output_dir).as_posix()}")

    assets_src = input_dir / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, output_dir / "assets", dirs_exist_ok=True)
        print("  assets/ copied")

    if after_write:
        after_write(output_dir)

    if redirect_rules:
        redirects_path = output_dir / "_redirects"
        redirects_path.write_text("\n".join(redirect_rules) + "\n", encoding="utf-8")
        print("  _redirects written")

    base_url = cfg["site_url"]
    (output_dir / "sitemap.xml").write_text(build_sitemap_xml(pages, base_url), encoding="utf-8")
    (output_dir / "robots.txt").write_text(build_robots_txt(base_url), encoding="utf-8")
    print("  sitemap.xml + robots.txt written")

    written, removed = sync_tree(output_dir, final_dir)
    shutil.rmtree(output_dir, ignore_errors=True)
    print(f"\nBuilt {len(pages)} pages to {final_dir.relative_to(root)}/ "
          f"({written} files changed, {removed} removed)")
