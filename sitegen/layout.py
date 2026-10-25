"""Page chrome: navbar, favicons, analytics, and the page and redirect templates."""

from urllib.parse import urlsplit

from .css import site_host
from .search import build_search_script

ICON_ATTRS = {".svg": ' type="image/svg+xml"', ".ico": ' sizes="any"', ".png": ' type="image/png"'}


def favicon_links(cfg):
    """One <link rel="icon"> per path in config `favicons` (default /assets/favicon.ico)."""
    paths = cfg.get("favicons") or ["/assets/favicon.ico"]
    links = []
    for href in paths:
        ext = href[href.rfind("."):].lower() if "." in href else ""
        links.append(f'<link rel="icon" href="{href}"{ICON_ATTRS.get(ext, "")}>')
    return "\n  ".join(links)


def build_logo_img(cfg):
    """The navbar logo from config `logo_path`, or the site name as text."""
    site_name = cfg.get("site_name", "")
    logo_path = cfg.get("logo_path", "")
    if logo_path:
        return f'<img class="nav-logo-img" src="{logo_path}" alt="{site_name}">'
    return f'<span class="nav-logo-text">{site_name}</span>'


def build_nav(pages, cfg):
    """The top bar. Links come from config `nav` (an item with `children` is a dropdown),
    or else from the pages' `nav_order`, `nav_label` and `nav_children` front matter.
    Config `demo_url` adds a demo button beside the CTA (`nav_cta_label`, linking to `app_url`)."""
    nav_items = cfg.get("nav")
    links = ""
    if nav_items:
        for item in nav_items:
            children = item.get("children", [])
            if children:
                sub = "".join(f'<a href="{ch["url"]}">{ch["label"]}</a>\n' for ch in children)
                links += f'''    <div class="nav-dropdown">
      <a href="{item.get("url", children[0]["url"])}" class="nav-dropdown-trigger">{item["label"]}</a>
      <div class="nav-dropdown-menu">{sub}</div>
    </div>\n'''
            else:
                links += f'    <a href="{item["url"]}">{item["label"]}</a>\n'
    else:
        nav_pages = sorted(
            [p for p in pages if p.get("nav_order") is not None],
            key=lambda p: p["nav_order"]
        )
        for p in nav_pages:
            label = p.get("nav_label", p.get("title", ""))
            path = p.get("path", "/")
            children = p.get("nav_children", [])
            if children:
                sub = ""
                for ch in children:
                    sub += f'<a href="{ch["path"]}">{ch["label"]}</a>\n'
                links += f'''    <div class="nav-dropdown">
      <a href="{path}" class="nav-dropdown-trigger">{label}</a>
      <div class="nav-dropdown-menu">{sub}</div>
    </div>\n'''
            else:
                links += f'    <a href="{path}">{label}</a>\n'

    app_url = cfg.get("app_url", "")
    cta_label = cfg.get("nav_cta_label", "Try it free")
    demo_url = cfg.get("demo_url", "")
    demo_html = ""
    if demo_url:
        demo_label = cfg.get("nav_demo_label", "Demo")
        demo_html = f'    <a class="btn-secondary nav-demo" href="{demo_url}">{demo_label}</a>\n'
    logo = build_logo_img(cfg)
    search_form = '''    <form class="site-search-form" action="/search" method="get" role="search">
      <label class="sr-only" for="nav-search-input">Search the site</label>
      <input
        id="nav-search-input"
        class="search-input"
        type="search"
        name="q"
        placeholder="Search"
        autocomplete="off"
      >
      <button type="submit" class="search-submit" aria-label="Submit search">&#8594;</button>
    </form>
'''

    return f'''<nav class="navbar">
  <div class="container nav-inner">
    <a href="/" class="nav-logo">{logo}</a>
    <button class="nav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="nav-links">
      <span></span><span></span><span></span>
    </button>
    <div class="nav-links" id="nav-links">
{links}    </div>
{search_form}{demo_html}    <a class="btn-cta nav-cta" href="{app_url}">{cta_label}</a>
  </div>
</nav>
<div class="accent-stripe"></div>'''


def build_analytics_html(cfg):
    # Each tracker is injected only when its own key is configured, so a site
    # can run either, both or neither.
    analytics = cfg.get("analytics", {}) or {}
    tags = []

    umami_id = (analytics.get("umami_id") or "").strip()
    if umami_id:
        umami_script = (analytics.get("umami_script") or "https://cloud.umami.is/script.js").strip()
        tags.append(
            f'<script defer src="{umami_script}" '
            f'data-website-id="{umami_id}"></script>'
        )

    # GoatCounter is the one that records whether a hit was a bot, which Umami
    # does not; the value is the full count URL from the GoatCounter snippet.
    goatcounter = (analytics.get("goatcounter") or "").strip()
    if goatcounter:
        tags.append(
            f'<script data-goatcounter="{goatcounter}" '
            f'async src="//gc.zgo.at/count.js"></script>'
        )

    return "\n  ".join(tags)


def build_referrer_passthrough_script(cfg):
    """With config `app_ref_host: true`: stamp app links with the host that referred
    this visitor to the site.

    document.referrer read on the app only ever names this site (the direct previous
    page), so the deeper origin, e.g. google.com or linkedin.com, is lost unless we pass
    it along ourselves. Session-scoped so it survives clicking between our own pages but
    not a return visit later; falls back silently (no ref_host param) if referrer is
    empty, same-site, or unreadable.
    """
    if not cfg.get("app_ref_host"):
        return ""
    app_host = urlsplit(cfg.get("app_url", "")).netloc.lower()
    if not app_host:
        return ""
    return f'''<script>
(function(){{
  try {{
    var KEY = "cm_ext_ref";
    var ref = document.referrer || "";
    var refHost = "";
    try {{ refHost = ref ? new URL(ref).hostname : ""; }} catch (e) {{}}
    if (refHost && refHost !== location.hostname && !sessionStorage.getItem(KEY)) {{
      sessionStorage.setItem(KEY, refHost);
    }}
    var stored = sessionStorage.getItem(KEY) || "";
    if (!stored) return;
    document.querySelectorAll("a[href]").forEach(function(a) {{
      try {{
        var u = new URL(a.getAttribute("href"), location.href);
        if (u.hostname !== "{app_host}" || u.searchParams.has("ref_host")) return;
        u.searchParams.set("ref_host", stored);
        a.setAttribute("href", u.toString());
      }} catch (e) {{}}
    }});
  }} catch (e) {{}}
}})();
</script>'''


def page_template(title, nav_html, content_html, footer_html, cfg, css, meta_desc="", search_index=None):
    site_name = cfg.get("site_name", "")
    desc = meta_desc or cfg.get("default_description", "")
    search_script = build_search_script(search_index) if search_index is not None else ""
    referrer_script = build_referrer_passthrough_script(cfg)
    referrer_block = referrer_script + "\n" if referrer_script else ""
    analytics_html = build_analytics_html(cfg)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{desc}">
  {favicon_links(cfg)}
  <title>{title} | {site_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
  {analytics_html}
  <style>{css}</style>
</head>
<body>
{nav_html}
<main>
<div class="print-banner"><span class="brand">{site_name}</span><span class="url">{site_host(cfg)}</span></div>
{content_html}
</main>
{footer_html}
<script>
(function () {{
  const toggle = document.querySelector(".nav-toggle");
  const links = document.getElementById("nav-links");
  if (toggle && links) {{
    toggle.addEventListener("click", () => {{
      const open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    }});
  }}
}})();
(function () {{
  const headings = document.querySelectorAll("main h1, main h2, main h3");
  if (!headings.length) return;

  headings.forEach((heading) => heading.classList.add("scroll-reveal"));

  if (!("IntersectionObserver" in window)) {{
    headings.forEach((heading) => heading.classList.add("in-view"));
    return;
  }}

  const observer = new IntersectionObserver((entries) => {{
    entries.forEach((entry) => {{
      if (entry.isIntersecting) {{
        entry.target.classList.add("in-view");
      }} else {{
        entry.target.classList.remove("in-view");
      }}
    }});
  }}, {{ threshold: 0.2, rootMargin: "0px 0px -12% 0px" }});

  headings.forEach((heading) => observer.observe(heading));
}})();
function cycleHighlightGroup(root) {{
  const holdMs = 2500;
  const fadeMs = 3000;
  let timer = null;
  let inView = false;
  const cards = root.querySelectorAll(".feature-card");
  const cardData = cards.length
    ? Array.from(cards)
        .map((card) => ({{ phrases: Array.from(card.querySelectorAll(".hl-reveal")) }}))
        .filter((c) => c.phrases.length)
    : [];
  const phrases = cardData.length
    ? cardData.flatMap((c) => c.phrases)
    : Array.from(root.querySelectorAll(".hl-reveal"));
  if (!phrases.length) return;

  function shuffle(arr) {{
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {{
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }}
    return a;
  }}
  function clearPhrases() {{
    phrases.forEach((p) => p.classList.remove("hl-active"));
  }}
  function activeCount(total) {{
    const jitter = Math.random() < 0.5 ? 0 : (Math.random() < 0.5 ? -1 : 1);
    return Math.max(1, Math.round(total / 3 + jitter));
  }}
  function nextDelay() {{
    return holdMs + fadeMs * 2 + Math.floor(Math.random() * 3000);
  }}
  function pick() {{
    if (cardData.length === 1 && phrases.length === 1) {{
      phrases[0].classList.add("hl-active");
      return;
    }}
    clearPhrases();
    void root.offsetHeight;
    if (cardData.length) {{
      const n = activeCount(cardData.length);
      shuffle(cardData).slice(0, n).forEach((c) => {{
        const ps = c.phrases;
        ps[Math.floor(Math.random() * ps.length)].classList.add("hl-active");
      }});
    }} else if (phrases.length === 1) {{
      phrases[0].classList.add("hl-active");
    }} else {{
      shuffle(phrases).slice(0, activeCount(phrases.length)).forEach((p) => p.classList.add("hl-active"));
    }}
  }}
  function stop() {{
    if (timer) clearTimeout(timer);
    timer = null;
  }}
  function schedule() {{
    stop();
    timer = setTimeout(function tick() {{
      pick();
      timer = setTimeout(tick, nextDelay());
    }}, nextDelay());
  }}
  function bump() {{
    stop();
    pick();
    schedule();
  }}
  function onLeave() {{
    stop();
    clearPhrases();
  }}

  if (!("IntersectionObserver" in window)) {{
    bump();
    return;
  }}
  const observer = new IntersectionObserver((entries) => {{
    entries.forEach((entry) => {{
      if (entry.isIntersecting) {{
        if (!inView) {{
          inView = true;
          bump();
        }}
      }} else if (inView) {{
        inView = false;
        onLeave();
      }}
    }});
  }}, {{ threshold: 0.2, rootMargin: "0px 0px -12% 0px" }});
  observer.observe(root);
}}
function cycleHighlights() {{
  document.querySelectorAll("[data-hl-cycle]").forEach(cycleHighlightGroup);
}}
if (document.readyState === "loading") {{
  document.addEventListener("DOMContentLoaded", cycleHighlights);
}} else {{
  cycleHighlights();
}}
</script>
{search_script}
{referrer_block}</body>
</html>'''


def redirect_template(title, redirect, cfg):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0;url={redirect}">
  <meta name="robots" content="noindex">
  {favicon_links(cfg)}
  <link rel="canonical" href="{redirect}">
  <title>{title}</title>
  <script>window.location.replace({redirect!r});</script>
</head>
<body>
  <p>Redirecting to <a href="{redirect}">{redirect}</a>...</p>
</body>
</html>'''
