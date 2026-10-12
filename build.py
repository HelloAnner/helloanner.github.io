#!/usr/bin/env python3
"""
Static site builder for helloanner.github.io.

Two kinds of output:
1. Homepage — src/index.template.html with {{PARTIAL:name}} placeholders
   filled from src/partials/<name>.html; src/styles.css copied as-is.
2. Books — src/projects/<book>/ holds a book.json plus Markdown chapters
   (NN-slug.md with YAML-ish front matter). Every chapter is rendered into
   dist/projects/<book>/<slug>.html with the shared article module
   (src/article/article.css + article.js), so every article on the site
   shares exactly the same typography, spacing, light/dark theme, TOC rail,
   code blocks, figures and math rendering.

Requires: python3 -m pip install markdown
"""

import html as html_lib
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SRC = ROOT / "src"
PARTIALS = SRC / "partials"
ARTICLE = SRC / "article"
PROJECTS = SRC / "projects"
OUTPUT = ROOT / "dist"

PARTIAL_PATTERN = re.compile(r"\{\{PARTIAL:([a-zA-Z0-9_-]+)\}\}")

MD_EXTENSIONS = ["fenced_code", "tables", "md_in_html"]

KATEX_HEAD = """  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
        integrity="sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+" crossorigin="anonymous">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
          integrity="sha384-7zkQWkzuo3B5mTepMUcHkMB5jZaolc2xDwL6VFqjFALcbeS9Ggm/Yr2r3Dy4xpFg" crossorigin="anonymous"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
          integrity="sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XUzwPTstBeZFe/+rCMvRwr4yROQP43s0Xk" crossorigin="anonymous"
          onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});"></script>"""

THEME_INIT = """  <script>/* set theme before first paint to avoid a flash */
    if (localStorage.getItem("theme") === "dark") document.documentElement.classList.add("dark");</script>"""

SUN_ICON = ('<svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line>'
            '<line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>'
            '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line>'
            '<line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>'
            '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>')
MOON_ICON = ('<svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
             'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M21 12.79A9 9 0 0 1 11.21 3a7 7 0 1 0 9.79 9.79z"></path></svg>')


# ---------------------------------------------------------------- homepage

def load_partial(name: str) -> str:
    path = PARTIALS / f"{name}.html"
    if not path.exists():
        raise FileNotFoundError(f"Partial not found: {path}")
    return path.read_text(encoding="utf-8")


def render_homepage() -> None:
    content = (SRC / "index.template.html").read_text(encoding="utf-8")
    rendered = PARTIAL_PATTERN.sub(lambda m: load_partial(m.group(1)), content)
    (OUTPUT / "index.html").write_text(rendered, encoding="utf-8")
    shutil.copy2(SRC / "styles.css", OUTPUT / "styles.css")
    print(f"Built: {OUTPUT / 'index.html'}")


# ---------------------------------------------------------------- markdown

def parse_front_matter(text: str):
    """Return (meta dict, body). Front matter is a --- delimited key: value block."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip().strip('"').strip("'")
            text = text[end + 4:].lstrip("\n")
    return meta, text


def md_render(text: str) -> str:
    return markdown.markdown(text, extensions=MD_EXTENSIONS)


def md_inline(text: str) -> str:
    """Render inline markdown only (strip the wrapping <p>)."""
    out = md_render(text)
    return re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)


def postprocess(html_text: str) -> str:
    """Map vanilla markdown HTML onto the design-system components."""
    # fenced code -> .codeblock card with language label + copy button
    def codeblock(m):
        lang = m.group(1) or "text"
        inner = m.group(0)
        return (f'<div class="codeblock"><span class="code-lang">{html_lib.escape(lang)}</span>'
                f'<button class="copy-btn" type="button">Copy</button>{inner}</div>')
    html_text = re.sub(
        r'<pre><code class="language-([\w+-]*)">[\s\S]*?</code></pre>', codeblock, html_text)
    html_text = re.sub(r'(<pre><code>)[\s\S]*?</code></pre>', codeblock, html_text)

    # blockquote -> tight inset note
    html_text = re.sub(r"<blockquote>([\s\S]*?)</blockquote>",
                       r'<div class="note tight">\1</div>', html_text)

    # standalone image paragraph -> figure + figcaption
    def figure(m):
        alt, src = m.group(1), m.group(2)
        cap = f"<figcaption>{md_inline(alt)}</figcaption>" if alt else ""
        return f'<figure><img src="{src}" alt="{html_lib.escape(alt)}">{cap}</figure>'
    html_text = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)"\s*/></p>', figure, html_text)

    # tables scroll horizontally on narrow screens
    html_text = re.sub(r"(<table>[\s\S]*?</table>)",
                       r'<div class="tablewrap">\1</div>', html_text)
    return html_text


def render_chapter_body(body: str):
    """Split on '## ' headings. Returns (intro_html, sections[(id, title, html)])."""
    chunks = re.split(r"(?m)^## ", body)
    intro = postprocess(md_render(chunks[0])) if chunks[0].strip() else ""
    sections = []
    for i, chunk in enumerate(chunks[1:], start=1):
        title, _, rest = chunk.partition("\n")
        title = title.strip()
        sections.append((f"sec-{i}", title, postprocess(md_render(rest))))
    return intro, sections


# ---------------------------------------------------------------- book pages

def chapter_file(book: dict, chapter: dict) -> str:
    return "index.html" if chapter["order"] == 1 else f"{chapter['slug']}.html"


def build_book_nav(book: dict, chapters: list, current: dict, sections: list) -> str:
    items = []
    for ch in chapters:
        cls = ' class="current"' if ch is current else ""
        items.append(f'<li{cls}><span class="n">{ch["order"]}</span>'
                     f'<a href="{chapter_file(book, ch)}">{html_lib.escape(ch["title"])}</a></li>')
    toc_items = "".join(
        f'<li><span class="n">{i}</span><a href="#{sid}">{md_inline(title)}</a></li>'
        for i, (sid, title, _) in enumerate(sections, start=1))
    toc_html = ""
    if toc_items:
        toc_html = ('<hr class="rail-divider"><div class="toc-label">On This Page</div>'
                    f'<ol id="page-toc">{toc_items}</ol>')
    return f'''<div class="book-wrap">
  <nav class="book" aria-label="Book chapters">
    <a class="backlink" href="../../index.html">← Portfolio</a>
    <p class="book-title">{html_lib.escape(book["title"])}</p>
    <p class="book-sub">{html_lib.escape(book.get("sub", ""))}</p>
    <div class="toc-label">Chapters</div>
    <ol class="chapters">{"".join(items)}</ol>
    {toc_html}
  </nav>
</div>'''


def build_pager(book: dict, chapters: list, idx: int) -> str:
    prev_ch = chapters[idx - 1] if idx > 0 else None
    next_ch = chapters[idx + 1] if idx + 1 < len(chapters) else None
    prev_html = (f'<a href="{chapter_file(book, prev_ch)}"><span class="dir">← Previous</span>'
                 f'<span class="name">{html_lib.escape(prev_ch["title"])}</span></a>') if prev_ch else '<span class="spacer"></span>'
    next_html = (f'<a class="next" href="{chapter_file(book, next_ch)}"><span class="dir">Next →</span>'
                 f'<span class="name">{html_lib.escape(next_ch["title"])}</span></a>') if next_ch else '<span class="spacer"></span>'
    return f'<div class="col"><div class="pager">{prev_html}{next_html}</div></div>'


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <meta name="description" content="{description}">
{theme_init}
  <link rel="stylesheet" href="../../assets/article.css">
{katex}
</head>
<body>

<div class="topbar">
  <div class="nav-container">
    <div class="nav-links">
      <a href="../../index.html">Home</a>
    </div>
    <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
      {sun}
      {moon}
    </button>
  </div>
</div>

<header class="hero">
  <div class="col">
    <div class="eyebrow title-kicker">{eyebrow}</div>
    <h1>{title}</h1>
    <div class="tldr">
      <div class="lab">TL;DR</div>
      <p class="txt">{tldr}</p>
    </div>
    <div class="byline">
      <div class="authors">Anner</div>
      <div class="affil">{book_title} &nbsp;·&nbsp; {date}</div>
    </div>
  </div>
</header>

{book_nav}

<main>
{content}
</main>

{pager}

<div class="col">
  <footer class="article-footer">
    <p>© 2026 Anner · <a href="../../index.html">Portfolio</a></p>
  </footer>
</div>

<button id="to-top" aria-label="Back to top" title="Back to top">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V6M6 11l6-6 6 6"/></svg>
</button>
<script src="../../assets/article.js"></script>
</body>
</html>
"""


def render_book(book_dir: Path) -> None:
    book = json.loads((book_dir / "book.json").read_text(encoding="utf-8"))
    slug = book_dir.name
    out_dir = OUTPUT / "projects" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # images ship next to the chapter pages
    images = book_dir / "images"
    if images.exists():
        shutil.copytree(images, out_dir / "images", dirs_exist_ok=True)

    chapters = []
    for path in sorted(book_dir.glob("[0-9][0-9]-*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        chapters.append({
            "order": int(path.name[:2]),
            "slug": path.stem[3:],
            "title": meta.get("title", path.stem[3:]),
            "eyebrow": meta.get("eyebrow", ""),
            "tldr": meta.get("tldr", ""),
            "date": meta.get("date", ""),
            "body": body,
        })
    chapters.sort(key=lambda c: c["order"])

    for idx, ch in enumerate(chapters):
        intro, sections = render_chapter_body(ch["body"])
        parts = []
        if intro:
            parts.append(f'<section><div class="col">{intro}</div></section>')
        for i, (sid, title, body_html) in enumerate(sections, start=1):
            parts.append(
                f'<section id="{sid}"><div class="col">'
                f"<h2>Section {i}</h2>"
                f'<div class="h2-title">{md_inline(title)}</div>'
                f"{body_html}</div></section>")
        page = PAGE_TEMPLATE.format(
            page_title=f"{ch['title']} · {book['title']}",
            description=html_lib.escape(ch["tldr"][:150]),
            theme_init=THEME_INIT,
            katex=KATEX_HEAD,
            sun=SUN_ICON, moon=MOON_ICON,
            eyebrow=html_lib.escape(ch["eyebrow"]),
            title=html_lib.escape(ch["title"]),
            tldr=md_inline(ch["tldr"]),
            book_title=html_lib.escape(book["title"]),
            date=html_lib.escape(ch["date"]),
            book_nav=build_book_nav(book, chapters, ch, sections),
            content="\n".join(parts),
            pager=build_pager(book, chapters, idx),
        )
        target = out_dir / chapter_file(book, ch)
        target.write_text(page, encoding="utf-8")
        print(f"Built: {target}")


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    render_homepage()

    # shared article module assets
    assets = OUTPUT / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copy2(ARTICLE / "article.css", assets / "article.css")
    shutil.copy2(ARTICLE / "article.js", assets / "article.js")

    if PROJECTS.exists():
        for book_dir in sorted(p for p in PROJECTS.iterdir() if p.is_dir()):
            if (book_dir / "book.json").exists():
                render_book(book_dir)


if __name__ == "__main__":
    build()
