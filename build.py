#!/usr/bin/env python3
"""
Static site builder for helloanner.github.io.

Two kinds of output:
1. Homepage — src/index.template.html with {{PARTIAL:name}} placeholders
   filled from src/partials/<name>.html; src/styles.css copied as-is.
2. Books — src/projects/<book>/ holds a book.json plus Markdown chapters
   (NN-slug.md with YAML-ish front matter). Every book gets a guide-style
   index page (dist/projects/<book>/index.html, listing chapters and their
   sections) and one page per chapter, all rendered with the shared article
   module (src/article/article.css + article.js) — a 1:1 replica of the
   simonwillison.net guide design system, so every article on the site shares
   exactly the same typography, colors, light/dark theme and code rendering.

Requires: python3 -m pip install markdown pygments
"""

import hashlib
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

MD_EXTENSIONS = ["fenced_code", "codehilite", "tables", "md_in_html", "toc"]

THEME_INIT = """  <script>
    (function() { // Apply theme immediately to prevent flash
      const theme = localStorage.getItem('theme');
      if (theme === 'light' || theme === 'dark') {
        document.documentElement.setAttribute('data-theme', theme);
      }
    })();
  </script>"""

THEME_TOGGLE = """<button id="theme-toggle" type="button" aria-label="Toggle theme">
          <!-- Auto/System icon (default) -->
          <svg id="icon-auto" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2V4a8 8 0 1 0 0 16z"/></svg>
          <!-- Light icon -->
          <svg id="icon-light" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="display:none"><path d="M12 18a6 6 0 1 1 0-12 6 6 0 0 1 0 12zm0-2a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z"/></svg>
          <!-- Dark icon -->
          <svg id="icon-dark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="display:none"><path d="M10 7a7 7 0 0 0 12 4.9v.1c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2h.1A6.979 6.979 0 0 0 10 7zm-6 5a8 8 0 0 0 15.062 3.762A9 9 0 0 1 8.238 4.938 7.999 7.999 0 0 0 4 12z"/></svg>
        </button>"""

HEAD_TEMPLATE = """<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <link rel="icon" href="../../assets/avatar.png" type="image/png">
  <title>{page_title}</title>
  <meta name="description" content="{description}">
{theme_init}
  <link rel="stylesheet" href="../../assets/article.css?v={css_v}">
</head>"""

SMALLHEAD = """<div id="smallhead">
  <div id="smallhead-inner">
    <h1><a href="../../index.html">Anner 的作品集</a></h1>
    <a id="smallhead-about" href="../../index.html">Portfolio</a>
  </div>
</div><!-- #smallhead -->"""

FOOTER = """<div id="ft">
    <ul>
      <li>&copy;</li>
      <li>2026</li>
      <li><a href="../../index.html">Anner</a></li>
      <li><a href="https://github.com/HelloAnner">GitHub</a></li>
      <li><a href="mailto:helloanner@gmail.com">Email</a></li>
      <li>
        {theme_toggle}
      </li>
    </ul>
</div>"""


# ---------------------------------------------------------------- homepage

def load_partial(name: str) -> str:
    path = PARTIALS / f"{name}.html"
    if not path.exists():
        raise FileNotFoundError(f"Partial not found: {path}")
    return path.read_text(encoding="utf-8")


def asset_version(path: Path) -> str:
    """Short content hash used to cache-bust static asset URLs."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def render_homepage() -> None:
    content = (SRC / "index.template.html").read_text(encoding="utf-8")
    rendered = PARTIAL_PATTERN.sub(lambda m: load_partial(m.group(1)), content)
    rendered = rendered.replace('href="styles.css"',
                                f'href="styles.css?v={asset_version(SRC / "styles.css")}"')
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


def postprocess(html_text: str) -> str:
    """Small component mappings on top of vanilla markdown HTML."""
    # standalone image paragraph -> figure + figcaption
    def figure(m):
        alt, src = m.group(1), m.group(2)
        cap = f"<figcaption>{alt}</figcaption>" if alt else ""
        return f'<figure><img src="{src}" alt="{html_lib.escape(alt)}">{cap}</figure>'
    html_text = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)"\s*/></p>', figure, html_text)
    # tables scroll horizontally on narrow screens
    html_text = re.sub(r"(<table>[\s\S]*?</table>)",
                       r'<div class="tablewrap">\1</div>', html_text)
    return html_text


def render_chapter_body(body: str):
    """Render markdown; return (html, [(h2_id, h2_text), ...]) for the index page."""
    rendered = postprocess(md_render(body))
    sections = [(sid, re.sub(r"<[^>]+>", "", t))
                for sid, t in re.findall(r'<h2 id="([^"]+)">([\s\S]*?)</h2>', rendered)]
    return rendered, sections


# ---------------------------------------------------------------- book pages

def chapter_file(chapter: dict) -> str:
    return f"{chapter['slug']}.html"


def sidebar(book: dict, chapters: list, current: dict | None) -> str:
    if current is not None:
        this_is = (f'<p class="this-is">这是项目指南 <strong><a href="./">{html_lib.escape(book["title"])}</a></strong> 中的一章。</p>')
    else:
        this_is = (f'<p class="this-is">Anner 的项目指南，共 {len(chapters)} 章，持续更新。</p>')
    items = []
    for ch in chapters:
        if current is not None and ch is current:
            items.append(f'<li><strong>{html_lib.escape(ch["title"])}</strong></li>')
        else:
            items.append(f'<li><a href="{chapter_file(ch)}">{html_lib.escape(ch["title"])}</a></li>')
    return f'''<div id="secondary">

<div class="metabox">
{this_is}
<div class="series-info">
  <p><strong>本书章节</strong></p>
  <ol>
    {"".join(items)}
  </ol>
</div>
</div>

</div> <!-- #secondary -->'''


def page_shell(book: dict, page_title: str, description: str, primary_html: str,
               secondary_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
{HEAD_TEMPLATE.format(
        page_title=html_lib.escape(page_title),
        description=html_lib.escape(description[:150]),
        theme_init=THEME_INIT,
        css_v=asset_version(ARTICLE / "article.css"))}
<body class="smallhead">

{SMALLHEAD}

<div id="wrapper">
<div id="primary">

{primary_html}

</div> <!-- #primary -->

{secondary_html}
</div> <!-- #wrapper -->

{FOOTER.format(theme_toggle=THEME_TOGGLE)}

<script src="../../assets/article.js?v={asset_version(ARTICLE / "article.js")}"></script>
</body>
</html>
"""


def render_book(book_dir: Path) -> None:
    book = json.loads((book_dir / "book.json").read_text(encoding="utf-8"))
    slug = book_dir.name
    out_dir = OUTPUT / "projects" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    images = book_dir / "images"
    if images.exists():
        shutil.copytree(images, out_dir / "images", dirs_exist_ok=True)

    chapters = []
    for path in sorted(book_dir.glob("[0-9][0-9]-*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        content, sections = render_chapter_body(body)
        chapters.append({
            "order": int(path.name[:2]),
            "slug": path.stem[3:],
            "title": meta.get("title", path.stem[3:]),
            "tldr": meta.get("tldr", ""),
            "content": content,
            "sections": sections,
        })
    chapters.sort(key=lambda c: c["order"])

    # ---- chapter pages ----
    for idx, ch in enumerate(chapters):
        prev_ch = chapters[idx - 1] if idx > 0 else None
        next_ch = chapters[idx + 1] if idx + 1 < len(chapters) else None
        prev_html = (f'<div>&larr; <a href="{chapter_file(prev_ch)}">{html_lib.escape(prev_ch["title"])}</a></div>'
                     if prev_ch else "<div></div>")
        next_html = (f'<div><a href="{chapter_file(next_ch)}">{html_lib.escape(next_ch["title"])}</a> &rarr;</div>'
                     if next_ch else "<div></div>")
        primary = f'''<p style="margin-bottom: 1em"><a href="../../index.html">作品集</a> &gt; <a href="./">{html_lib.escape(book["title"])}</a></p>

<h2 class="archive-h2">{html_lib.escape(ch["title"])}</h2>

<div class="note">{ch["content"]}</div>

<div class="pager">
  {prev_html}
  {next_html}
</div>'''
        page = page_shell(book, f"{ch['title']} · {book['title']}", ch["tldr"],
                          primary, sidebar(book, chapters, ch))
        (out_dir / chapter_file(ch)).write_text(page, encoding="utf-8")
        print(f"Built: {out_dir / chapter_file(ch)}")

    # ---- guide-style index page ----
    items = []
    for ch in chapters:
        subs = "".join(
            f'<li><a href="{chapter_file(ch)}#{sid}">{html_lib.escape(title)}</a></li>'
            for sid, title in ch["sections"])
        sub_html = f'<ul>{subs}</ul>' if subs else ""
        items.append(f'<li><a href="{chapter_file(ch)}">{html_lib.escape(ch["title"])}</a>{sub_html}</li>')
    primary = f'''<p style="margin-bottom: 1em"><a href="../../index.html">作品集</a> &gt; 项目指南</p>

<h2 class="archive-h2">{html_lib.escape(book["title"])}</h2>

<p>{html_lib.escape(book.get("intro", ""))}</p>

<ol class="chapter-index">
  {"".join(items)}
</ol>'''
    page = page_shell(book, book["title"], book.get("intro", ""),
                      primary, sidebar(book, chapters, None))
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    print(f"Built: {out_dir / 'index.html'}")


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    render_homepage()

    # shared article module + site assets (avatar, …)
    assets = OUTPUT / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copy2(ARTICLE / "article.css", assets / "article.css")
    shutil.copy2(ARTICLE / "article.js", assets / "article.js")
    shared_assets = SRC / "assets"
    if shared_assets.exists():
        for asset in shared_assets.iterdir():
            if asset.is_file():
                shutil.copy2(asset, assets / asset.name)

    if PROJECTS.exists():
        for book_dir in sorted(p for p in PROJECTS.iterdir() if p.is_dir()):
            if (book_dir / "book.json").exists():
                render_book(book_dir)


if __name__ == "__main__":
    build()
