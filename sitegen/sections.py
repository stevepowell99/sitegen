"""Section renderers: one function per front-matter `type`, each returning an HTML string.

Every renderer takes (section, cfg, pages): the section's front matter, the site
config, and every parsed page (for sections that list other pages). A site adds or
replaces renderers by passing `renderers=` to sitegen.build().
"""

import html as html_lib
import re

from .content import inline_html, md, render_fa_icon


def render_hero(section, cfg, pages):
    """Dark hero. With a second CTA, both buttons sit in a row: the first in the
    secondary style, the second in the accent style."""
    headline = section.get("headline", "")
    subhead = inline_html(section.get("subhead", ""))
    cta_text = section.get("cta_text", "")
    cta_url = section.get("cta_url", "#")
    secondary_text = section.get("secondary_cta_text", "")
    secondary_url = section.get("secondary_cta_url", "#")
    if secondary_text:
        cta_bits = []
        if cta_text:
            cta_bits.append(f'<a class="btn-secondary" href="{cta_url}">{cta_text}</a>')
        cta_bits.append(f'<a class="btn-cta" href="{secondary_url}">{secondary_text}</a>')
        cta_html = f'<div class="hero-actions">{"".join(cta_bits)}</div>'
    elif cta_text:
        cta_html = f'<a class="btn-cta" href="{cta_url}">{cta_text}</a>'
    else:
        cta_html = ""
    return f'''<section class="hero">
  <div class="container">
    <h1>{headline}</h1>
    <div class="hero-sub" data-hl-cycle>{subhead}</div>
    {cta_html}
  </div>
</section>'''


def render_hero_light(section, cfg, pages):
    headline = section.get("headline", "")
    subhead = inline_html(section.get("subhead", ""))
    pillars = section.get("pillars")
    pills_block = ""
    if pillars:
        pills_inner = render_stand_pillar_articles(pillars, cfg)
        pills_block = f'''
  <div class="hero-light-pills">
    <div class="stand-pills-grid">
{pills_inner}    </div>
  </div>'''
    mod = " hero-light--with-pills" if pillars else ""
    return f'''<section class="hero-light{mod}">
  <div class="container">
    <h1>{headline}</h1>
    {f'<div class="hero-sub" data-hl-cycle>{subhead}</div>' if subhead else ''}
    {pills_block}
  </div>
</section>'''


def render_stand_pillar_articles(pillars, cfg):
    """Rounded cards inside hero-light: badge title, optional intro and bullets, links."""
    app_url = cfg.get("app_url", "")
    parts = []
    for i, p in enumerate(pillars):
        heading = html_lib.escape(p.get("heading", ""))
        page_url = (p.get("page_url") or "").strip()
        page_label = html_lib.escape(p.get("page_label", "Learn more"))
        secondary_url = (p.get("secondary_url") or "").strip()
        sec_label_raw = p.get("secondary_label", "")
        if i == 0 and sec_label_raw and not secondary_url:
            secondary_url = app_url.rstrip("/") + "/"
        items = p.get("items") or []
        intro = p.get("intro", "")
        extra_links = p.get("links") or []

        bullets = ""
        for it in items:
            bullets += f'<li><span class="stand-pill-check" aria-hidden="true">&#10003;</span> {html_lib.escape(it)}</li>'
        list_html = f'<ul class="stand-pill-list">{bullets}</ul>' if bullets else ""
        intro_html = f'<div class="stand-pill-intro">{md(intro)}</div>' if intro else ""

        action_bits = []
        if page_url:
            action_bits.append(f'<a class="stand-pill-action" href="{page_url}">{page_label}</a>')
        if secondary_url and sec_label_raw:
            action_bits.append(
                f'<a class="stand-pill-action" href="{secondary_url}">{html_lib.escape(sec_label_raw)}</a>'
            )
        for L in extra_links:
            u = (L.get("url") or "").strip()
            lab = html_lib.escape(L.get("label", u))
            if u:
                action_bits.append(f'<a class="stand-pill-action" href="{u}">{lab}</a>')
        actions_html = f'<div class="stand-pill-actions">{"".join(action_bits)}</div>' if action_bits else ""

        parts.append(
            f'''<article class="stand-pill">
      <p class="stand-pill-badge-wrap"><span class="stand-pill-badge">{heading}</span></p>
      {intro_html}
      {list_html}
      {actions_html}
    </article>\n'''
        )
    return "".join(parts)


def feature_doc_url(col, cfg):
    """A card's documentation link: its doc_url, or its help_anchor placed into
    config `help_anchor_url` (default "{help_url}/{anchor}/")."""
    if col.get("doc_url"):
        return col["doc_url"]
    anchor = (col.get("help_anchor") or "").strip().lstrip("#")
    if not anchor:
        return ""
    help_url = (cfg.get("help_url") or "").rstrip("/")
    return cfg.get("help_anchor_url", "{help_url}/{anchor}/").format(help_url=help_url, anchor=anchor)


def render_features(section, cfg, pages):
    cols = section.get("columns", [])
    heading = section.get("heading", "")
    # Card titles sit one level below a section heading when present; without one
    # they follow the page h1 directly, so they must be h2 to avoid skipping a level.
    card_tag = "h3" if heading else "h2"
    cards = ""
    for col in cols:
        icon_html = render_fa_icon(col.get("icon"), "feature-icon")
        title = col.get("title", "")
        doc_url = feature_doc_url(col, cfg)
        title_html = f"<{card_tag}>{title}</{card_tag}>"
        link_html = ""
        if doc_url:
            link_html = (
                f'<a class="feature-card-link" href="{doc_url}" '
                f'target="_blank" rel="noopener noreferrer" '
                f'aria-label="{html_lib.escape(title)} — documentation"></a>'
            )
        cards += f'''<div class="feature-card">
      {link_html}
      {icon_html}
      {title_html}
      {inline_html(col.get("text", ""))}
    </div>\n'''
    h = f'<h2 class="features-heading">{heading}</h2>' if heading else ""
    return f'''<section class="features">
  <div class="container">
    {h}
    <div class="features-grid" data-hl-cycle>{cards}</div>
  </div>
</section>'''


def render_callout(section, cfg, pages):
    icon_html = render_fa_icon(section.get("icon"), "callout-icon")
    title = section.get("title", "")
    text = inline_html(section.get("text", ""))
    return f'''<section class="callout-section">
  <div class="container">
    <div class="callout-card">
      {icon_html}
      <div data-hl-cycle>
        <h2>{title}</h2>
        {text}
      </div>
    </div>
  </div>
</section>'''


def render_video(section, cfg, pages):
    url = section.get("url", "")
    vid_id = ""
    if "vimeo.com" in url:
        vid_id = url.rstrip("/").split("/")[-1]
        # dnt=1 stops Vimeo setting tracking cookies / loading analytics.
        embed = f'https://player.vimeo.com/video/{vid_id}?dnt=1'
    elif "youtube.com" in url or "youtu.be" in url:
        m = re.search(r'(?:v=|youtu\.be/)([^&?]+)', url)
        vid_id = m.group(1) if m else ""
        # youtube-nocookie defers cookies until the visitor plays the video.
        embed = f'https://www.youtube-nocookie.com/embed/{vid_id}'
    else:
        embed = url
    return f'''<section class="video-section">
  <div class="container">
    <div class="video-wrap">
      <iframe src="{embed}" frameborder="0" allowfullscreen loading="lazy"></iframe>
    </div>
  </div>
</section>'''


def render_two_col(section, cfg, pages):
    lt = section.get("left_title", "")
    lb = md(section.get("left_body", ""))
    rt = section.get("right_title", "")
    rb = md(section.get("right_body", ""))
    return f'''<section class="two-col">
  <div class="container">
    <div class="two-col-grid">
      <div>
        <h2>{lt}</h2>
        {lb}
      </div>
      <div>
        <h2>{rt}</h2>
        {rb}
      </div>
    </div>
  </div>
</section>'''


def render_steps(section, cfg, pages):
    """Numbered steps; an item's optional `icon` replaces its number."""
    items = section.get("items", [])
    cards = ""
    for i, item in enumerate(items, 1):
        marker = render_fa_icon(item.get("icon"), "step-icon") or str(i)
        cards += f'''<div class="step-item">
      <div class="step-number">{marker}</div>
      <h3>{item.get("title","")}</h3>
      {md(item.get("text",""))}
    </div>\n'''
    return f'''<section class="steps">
  <div class="container">
    <div class="steps-grid">{cards}</div>
  </div>
</section>'''


def render_trust_strip(section, cfg, pages):
    heading = section.get("heading", "")
    orgs = section.get("organisations", "")
    return f'''<section class="trust-strip">
  <div class="container">
    <p><strong>{heading}</strong> {orgs}</p>
  </div>
</section>'''


def render_logos(section, cfg, pages):
    heading = section.get("heading", "")
    image = section.get("image", "")
    return f'''<section class="logos-section">
  <div class="container">
    <h3>{heading}</h3>
    <img src="/{image}" alt="{heading}" loading="lazy">
  </div>
</section>'''


def render_testimonials(section, cfg, pages):
    heading = section.get("heading", "")
    items = section.get("items", [])
    cards = ""
    for item in items:
        name = item.get("name", "")
        quote = item.get("quote", "")
        cards += f'''<div class="testimonial-card">
      <blockquote>{quote}</blockquote>
      <p class="testimonial-name">{name}</p>
    </div>\n'''
    h = f"<h2>{heading}</h2>" if heading else ""
    return f'''<section class="testimonials">
  <div class="container">
    {h}
    <div class="testimonials-grid">{cards}</div>
  </div>
</section>'''


def render_cta_banner(section, cfg, pages):
    text = section.get("text", "")
    url = section.get("url", "#")
    btn = section.get("button_text", "Learn more")
    return f'''<section class="cta-banner">
  <div class="container">
    <span>{text}</span>
    <a class="btn-cta" href="{url}">{btn}</a>
  </div>
</section>'''


def render_prose(body_html):
    return f'''<section class="prose-section">
  <div class="container">
    {body_html}
  </div>
</section>'''


def render_team(section, cfg, pages):
    heading = section.get("heading", "")
    members = section.get("members", [])
    cards = ""
    for m in members:
        img = ""
        if m.get("image"):
            img = f'<img src="{m["image"]}" alt="{m.get("name","")}" loading="lazy">'
            if m.get("image_link"):
                img = f'<a href="{m["image_link"]}">{img}</a>'
        links = ""
        if m.get("linkedin"):
            links = f' <a href="{m["linkedin"]}" class="team-link">LinkedIn</a>'
        cards += f'''<div class="team-card">
      {img}
      <h3>{m.get("name","")}{links}</h3>
      <p class="team-role">{m.get("role","")}</p>
      <p>{m.get("bio","")}</p>
    </div>\n'''
    h = f"<h2>{heading}</h2>" if heading else ""
    return f'''<section class="team-section">
  <div class="container">
    {h}
    <div class="team-grid">{cards}</div>
  </div>
</section>'''


def render_search(section, cfg, pages):
    heading = section.get("heading", "Search the site")
    intro = md(section.get("intro", "Find pages across the site."))
    return f'''<section class="search-section">
  <div class="container">
    <div id="site-search-root" class="search-shell">
      <h1>{heading}</h1>
      <div class="search-intro">{intro}</div>
      <form class="search-page-form" action="/search" method="get" data-search-form>
        <label class="sr-only" for="search-page-input">Search the site</label>
        <input
          id="search-page-input"
          class="search-input"
          type="search"
          name="q"
          placeholder="Search"
          autocomplete="off"
          data-search-input
        >
        <button type="submit" class="search-submit">Search</button>
      </form>
      <p class="search-status" data-search-status>Search page titles and content.</p>
      <div class="search-results" data-search-results></div>
    </div>
  </div>
</section>'''


SECTION_RENDERERS = {
    "hero": render_hero,
    "hero-light": render_hero_light,
    "features": render_features,
    "callout": render_callout,
    "video": render_video,
    "two-col": render_two_col,
    "steps": render_steps,
    "trust-strip": render_trust_strip,
    "logos": render_logos,
    "testimonials": render_testimonials,
    "cta-banner": render_cta_banner,
    "team": render_team,
    "search": render_search,
}


def render_sections(page, cfg, pages, renderers):
    """The page's content HTML: its `cover` image, then each section in order.
    The markdown body renders where a `prose` section is listed, or at the end."""
    sections = page.get("sections", [])
    body_html = md(page.get("body", ""))
    has_prose = any(s.get("type") == "prose" for s in sections)
    parts = []
    cover = page.get("cover", "")
    if cover:
        parts.append(
            f'<section class="post-cover-hero"><div class="container">'
            f'<img src="{cover}" alt="" loading="lazy"></div></section>'
        )
    for s in sections:
        stype = s.get("type", "")
        if stype == "prose":
            parts.append(render_prose(body_html))
        elif stype in renderers:
            parts.append(renderers[stype](s, cfg, pages))
        else:
            print(f"  WARNING {page.get('_file')}: unknown section type {stype!r} skipped")
    if not has_prose and body_html.strip():
        parts.append(render_prose(body_html))
    result = "\n<hr class=\"section-divider\">\n".join(parts)
    result = result.replace("<td>Yes</td>", '<td class="check">&#10003;</td>')
    return result
