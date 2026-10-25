# sitegen

The static site generator behind [causalmap.app](https://causalmap.app) and [qualiainterviews.com](https://qualiainterviews.com). Written for whoever maintains those sites, person or agent.

Each site keeps its content (`content/*.md`), its `config.yml` and a short `build.py`. The generator itself lives here, and each site pins a version of it in its `requirements.txt`:

```
sitegen @ git+https://github.com/stevepowell99/sitegen@v0.1.0
```

Netlify runs `pip install -r requirements.txt && python build.py` on every push to a site's `main`, so a site changes generator only when its pin changes.

## What a site's build.py does

```python
from pathlib import Path
import sitegen

def footer(cfg):
    return "<footer>...</footer>"

CSS = {...}  # see "The stylesheet" below

def build():
    sitegen.build(Path(__file__).parent, footer=footer, css=CSS)

if __name__ == "__main__":
    build()
```

`sitegen.build(root, footer, css, renderers=None, extend_pages=None, after_write=None)`:

- `footer(cfg)` returns the site's footer HTML.
- `css` is the site's dict of stylesheet values and blocks.
- `renderers` adds or replaces section types: `{"type": fn(section, cfg, pages)}`, each returning HTML.
- `extend_pages(pages, cfg)` runs once every page is rendered, before the search index and navbar are built. It may change pages or append generated ones, each with `_path` and `_content_html` (causalmap.app adds its tag pages this way).
- `after_write(output_dir)` runs once the pages and `content/assets/` are in the temporary output folder (Qualia copies its brand files this way).

`sitegen.md`, `inline_html`, `render_fa_icon`, `normalize_whitespace` and `html_to_plain_text` are exported for a site's own renderers.

## What the build does

- Reads every `content/**/*.md` outside `content/assets/`. Front matter sets `path` (default: the file's path under `content/`), `title`, `description`, `sections`, navigation and `redirect`.
- Renders each page's `sections` in order. The shared section types are `hero`, `hero-light`, `features`, `callout`, `video`, `two-col`, `steps`, `trust-strip`, `logos`, `testimonials`, `cta-banner`, `team`, `search` and `prose`; an unknown type is skipped with a warning. A page's `cover` image goes above its sections.
- Rewrites internal links as relative paths, so `dist/` also works from `file://`. The exception is `/404.html`: Netlify serves it at whatever URL was missing, so its links stay root-absolute.
- Opens external links in a new tab, adds `app_utm` parameters to links to `app_url`, and with `app_ref_host: true` passes the visitor's referring host on to the app.
- Writes `_redirects` for redirect pages, `sitemap.xml` and `robots.txt` from `site_url`, and copies `content/assets/`.
- Builds in a temporary folder outside Google Drive, then makes `dist/` match it by rewriting only changed files. It never deletes `dist/` itself, because a folder deleted and recreated while Drive is still uploading leaves orphaned files in the Drive root.

## config.yml keys sitegen reads

`site_name`, `site_url`, `app_url`, `help_url`, `help_anchor_url` (default `"{help_url}/{anchor}/"`), `input_dir`, `output_dir`, `logo_path` (empty: the site name as text), `favicons` (default `["/assets/favicon.ico"]`), `default_description`, `nav` (otherwise pages' `nav_order`), `nav_cta_label`, `demo_url`, `nav_demo_label`, `app_utm`, `app_ref_host`, `colors` and `analytics` (`umami_id`, `umami_script`, `goatcounter`).

## The stylesheet

`sitegen/base.css` holds every rule the sites share, with `$placeholders` where they differ. A site's `css` dict fills them (`sitegen/css.py` lists the names):

- **Values** every site must give: `scroll_padding_top`, `nav_logo_height`, `nav_logo_height_mobile`, `nav_links`, `search_form_flex`, `button_text`, `ink_deep`.
- **Slots**: CSS blocks only some sites need, named for where they land in the cascade (`after_navbar`, `after_video`, `before_print` and so on). Empty unless the site gives one.
- **Derived** from `config.yml` and overridable: the host in the print footer, the button-shadow and background tints from `colors`, and the mobile navbar order (which makes room for the demo button).

A rule belongs in `base.css` only when every site uses it. Markup that sitegen can emit but only one site uses (step icons, the two-button hero, the demo button, blog cover images) is styled in that site's slots.

## Changing the generator

1. Edit here and test against each site: build the site's current `main` and your version into separate folders outside Drive and diff the two `dist/` trees. Point a site at your working copy with `pip install -e C:\dev\sitegen`.
2. Bump `__version__` in `sitegen/__init__.py`, commit, push, and tag: `git tag v0.1.1 && git push origin v0.1.1`.
3. In each site that should take the change, edit the pin in `requirements.txt`, then build, diff and push the site. Each push publishes.

Python 3.8 or later. Dependencies: PyYAML and Markdown.

## Licence

[FSL-1.1-MIT](LICENSE.md) (Functional Source License): free for any use except a competing product. Each release becomes MIT-licensed two years after publication.
