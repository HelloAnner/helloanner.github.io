#!/usr/bin/env python3
"""
Simple static site builder for helloanner.github.io.
Reads src/index.template.html and replaces {{PARTIAL:name}} placeholders
with content from src/partials/<name>.html. Copies styles.css to the output dir.
"""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
PARTIALS = SRC / "partials"
OUTPUT = ROOT / "dist"  # rendered output directory

PARTIAL_PATTERN = re.compile(r"\{\{PARTIAL:([a-zA-Z0-9_-]+)\}\}")


def load_partial(name: str) -> str:
    path = PARTIALS / f"{name}.html"
    if not path.exists():
        raise FileNotFoundError(f"Partial not found: {path}")
    return path.read_text(encoding="utf-8")


def render_template(template_path: Path) -> str:
    content = template_path.read_text(encoding="utf-8")

    def replace(match: re.Match) -> str:
        name = match.group(1)
        return load_partial(name)

    return PARTIAL_PATTERN.sub(replace, content)


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rendered = render_template(SRC / "index.template.html")
    (OUTPUT / "index.html").write_text(rendered, encoding="utf-8")
    shutil.copy2(SRC / "styles.css", OUTPUT / "styles.css")
    print(f"Built: {OUTPUT / 'index.html'}")
    print(f"Copied: {OUTPUT / 'styles.css'}")


if __name__ == "__main__":
    build()
