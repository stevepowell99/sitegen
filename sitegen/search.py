"""Client-side site search: an index of every page, embedded in the /search page."""

import json

from .content import html_to_plain_text, normalize_whitespace
from .links import relative_site_path


def build_search_index(pages):
    docs = []
    for page in pages:
        if page.get("redirect"):
            continue
        path = page["_path"]
        if path == "/search":
            continue
        docs.append({
            "title": page.get("title", "Untitled"),
            "path": path,
            "href": relative_site_path(path, "/search"),
            "description": normalize_whitespace(page.get("description", "")),
            "content": html_to_plain_text(page.get("_content_html", "")),
        })
    return docs


def build_search_script(search_index):
    search_json = json.dumps(search_index, ensure_ascii=False).replace("<", "\\u003c").replace("</", "<\\/")
    return f'''<script>
(function () {{
  const root = document.getElementById("site-search-root");
  if (!root) return;

  const searchIndex = {search_json};
  const form = root.querySelector("[data-search-form]");
  const input = root.querySelector("[data-search-input]");
  const status = root.querySelector("[data-search-status]");
  const results = root.querySelector("[data-search-results]");
  const params = new URLSearchParams(window.location.search);
  const initialQuery = (params.get("q") || "").trim();

  function tokenize(text) {{
    return [...new Set((text.toLowerCase().match(/[a-z0-9]+/g) || []))];
  }}

  function scoreDoc(doc, terms) {{
    const title = doc.title.toLowerCase();
    const description = doc.description.toLowerCase();
    const content = doc.content.toLowerCase();
    let score = 0;

    for (const term of terms) {{
      if (title.includes(term)) score += 12;
      if (description.includes(term)) score += 6;
      if (content.includes(term)) score += 2;
    }}

    return score;
  }}

  function buildSnippet(doc, terms) {{
    const source = doc.content || doc.description;
    if (!source) return "";

    const lower = source.toLowerCase();
    let start = 0;
    for (const term of terms) {{
      const index = lower.indexOf(term);
      if (index !== -1) {{
        start = Math.max(0, index - 80);
        break;
      }}
    }}

    const end = Math.min(source.length, start + 190);
    const snippet = source.slice(start, end).trim();
    const prefix = start > 0 ? "..." : "";
    const suffix = end < source.length ? "..." : "";
    return prefix + snippet + suffix;
  }}

  function renderResults(query) {{
    results.replaceChildren();
    const terms = tokenize(query);

    if (!terms.length) {{
      status.textContent = "Search page titles and content.";
      return;
    }}

    const matches = searchIndex
      .map((doc) => ({{ doc, score: scoreDoc(doc, terms) }}))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score || a.doc.title.localeCompare(b.doc.title))
      .slice(0, 20);

    status.textContent = matches.length
      ? `${{matches.length}} result${{matches.length === 1 ? "" : "s"}} for "${{query}}"`
      : `No results for "${{query}}"`;

    for (const match of matches) {{
      const card = document.createElement("article");
      card.className = "search-result-card";

      const heading = document.createElement("h2");
      const link = document.createElement("a");
      link.href = match.doc.href;
      link.textContent = match.doc.title;
      heading.appendChild(link);
      card.appendChild(heading);

      if (match.doc.description) {{
        const description = document.createElement("p");
        description.className = "search-result-desc";
        description.textContent = match.doc.description;
        card.appendChild(description);
      }}

      const snippetText = buildSnippet(match.doc, terms);
      if (snippetText) {{
        const snippet = document.createElement("p");
        snippet.className = "search-result-snippet";
        snippet.textContent = snippetText;
        card.appendChild(snippet);
      }}

      results.appendChild(card);
    }}
  }}

  function submitSearch(event) {{
    event.preventDefault();
    const query = input.value.trim();
    const nextUrl = new URL(window.location.href);

    if (query) {{
      nextUrl.searchParams.set("q", query);
    }} else {{
      nextUrl.searchParams.delete("q");
    }}

    window.history.replaceState({{}}, "", nextUrl);
    renderResults(query);
  }}

  form.addEventListener("submit", submitSearch);
  input.value = initialQuery;
  if (initialQuery) renderResults(initialQuery);
}})();
</script>'''
