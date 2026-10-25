"""The stylesheet: base.css, filled in with the site's colours, values and CSS blocks.

base.css holds every rule the sites share. Where they differ it has a $placeholder,
and each site passes its own text for it as `css=` to sitegen.build():

- VALUES must be given by every site (sizes and colours on which the sites differ);
- SLOTS are CSS blocks only some sites need, inserted at that point in the cascade
  (the name says where), empty unless the site gives one;
- the rest are worked out from config.yml, and a site may override them.
"""

import re
from pathlib import Path
from string import Template

BASE_CSS = Template(Path(__file__).with_name("base.css").read_text(encoding="utf-8"))

VALUES = (
    "scroll_padding_top",      # clears anchor targets of the sticky navbar
    "nav_logo_height",
    "nav_logo_height_mobile",
    "nav_links",               # the .nav-links and .nav-links > a rules
    "search_form_flex",        # flex of the navbar search box
    "button_text",             # text colour on .btn-cta and .btn-secondary
    "ink_deep",                # dark end of the hero and CTA-banner gradients
)

SLOTS = (
    "after_navbar", "after_nav_logo", "after_search_form",
    "button_props",            # extra declarations inside both button rules
    "after_btn_cta", "after_buttons", "after_video", "after_step_number",
    "after_search", "prose_lists", "after_prose",
    "before_footer_copy", "after_footer_copy",
    "mobile_after_hero", "mobile_after_features",
    "before_print",
)


def hex_to_rgb(hex_color):
    hex_color = hex_color.strip().lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgba(hex_color, alpha):
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def rgb_csv(hex_color):
    return ",".join(str(c) for c in hex_to_rgb(hex_color))


def site_host(cfg):
    return re.sub(r"^https?://", "", cfg.get("site_url", "")).rstrip("/")


def build_css(cfg, site_css):
    colors = cfg.get("colors", {})
    cm_ink = colors.get("accent_ink", "#1f1f36")
    cm_pink = colors.get("accent_pink", "#ff8fb8")
    cm_green = colors.get("accent_primary", "#00ffaf")
    cm_teal = colors.get("accent_secondary", "#6dc4c8")
    cm_yellow = colors.get("highlight_yellow", "#f7ed73")
    cm_bg = colors.get("body_bg", "#fcfcfc")
    cm_text = colors.get("text", "#222")

    # The navbar demo button (config demo_url) takes a place in the mobile nav order.
    demo = bool(cfg.get("demo_url"))
    derived = {
        "site_host": site_host(cfg),
        "pink_rgb": rgb_csv(cm_pink),
        "tint_a": rgb_csv(cm_green),
        "tint_b": rgb_csv(cm_teal),
        "hero_grid_line": rgba(cm_teal, 0.05),
        "mobile_nav_order": "  .nav-demo { order: 3; }\n  .nav-cta { order: 4; }" if demo else "  .nav-cta { order: 3; }",
        "mobile_nav_links_order": "5" if demo else "4",
        "mobile_search_order": "6" if demo else "5",
    }
    missing = [k for k in VALUES if k not in site_css]
    unknown = sorted(set(site_css) - set(VALUES) - set(SLOTS) - set(derived))
    if missing or unknown:
        raise ValueError(f"sitegen css: missing values {missing}, unknown names {unknown}")
    fill = dict(derived)
    fill.update({k: "" for k in SLOTS})
    fill.update(site_css)
    return f''':root {{
  --cm-ink: {cm_ink};
  --cm-pink: {cm_pink};
  --cm-green: {cm_green};
  --cm-teal: {cm_teal};
  --cm-yellow: {cm_yellow};
  --cm-bg: {cm_bg};
  --cm-text: {cm_text};
  --cm-light: #f4f6f8;
  --cm-border: #e2e6ea;
  --radius: 8px;
  --cm-green-light: {rgba(cm_green, 0.08)};
  --cm-teal-light: {rgba(cm_teal, 0.10)};
  --cm-yellow-light: {rgba(cm_yellow, 0.75)};
  --cm-pink-light: {rgba(cm_pink, 0.45)};
}}

{BASE_CSS.substitute(fill)}'''

