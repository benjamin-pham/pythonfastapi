"""Render breadcrumb / footer navigation blocks from the manifest."""

from __future__ import annotations

import posixpath
import re

from tools.manifest import HOME, PROJECT_INDEX, READING_ORDER, Page, level_index

TOP_START, TOP_END = "<!-- nav:top -->", "<!-- /nav:top -->"
BOTTOM_START, BOTTOM_END = "<!-- nav:bottom -->", "<!-- /nav:bottom -->"
STUB_MARKER = "<!-- STUB -->"

_TOP_RE = re.compile(re.escape(TOP_START) + r".*?" + re.escape(TOP_END), re.DOTALL)
_BOTTOM_RE = re.compile(
    re.escape(BOTTOM_START) + r".*?" + re.escape(BOTTOM_END), re.DOTALL
)


def rel(src: str, dst: str) -> str:
    """Relative link from page `src` to page `dst` (both repo-relative POSIX paths)."""
    result = posixpath.relpath(dst, posixpath.dirname(src) or ".")
    return result if result.startswith("../") else f"./{result}"


def link(src: Page, dst: Page, label: str) -> str:
    return f"[{label}]({rel(src.path, dst.path)})"


def breadcrumb(page: Page) -> str:
    if page.kind == "home":
        return ""
    home = link(page, HOME, "🏠 Home")
    if page.kind == "level":
        return f"{home} › {page.section}"
    if page.kind == "lesson":
        number = posixpath.basename(page.path)[:2]
        return f"{home} › {link(page, level_index(page), page.section)} › Bài {number}"
    if page.kind == "milestone":
        short = page.title.split(" – ")[0]
        return f"{home} › {link(page, PROJECT_INDEX, PROJECT_INDEX.title)} › {short}"
    if page == PROJECT_INDEX:
        return f"{home} › {page.title}"
    return f"{home} › {page.section} › {page.title}"


def footer(page: Page) -> str:
    if page.kind == "reference":
        return link(page, HOME, "🏠 Về trang chủ")
    index = READING_ORDER.index(page)
    if page.kind == "home":
        first = READING_ORDER[1]
        return link(page, first, f"Bắt đầu: {first.title} ➡️")
    prev = READING_ORDER[index - 1]
    left = link(page, prev, f"⬅️ {prev.title}")
    if page.kind == "lesson":
        middle = link(page, level_index(page), f"📚 Mục lục {page.section}")
    elif page.kind == "milestone":
        middle = link(page, PROJECT_INDEX, f"📚 {PROJECT_INDEX.title}")
    else:
        middle = link(page, HOME, "🏠 Home")
    if index + 1 < len(READING_ORDER):
        nxt = READING_ORDER[index + 1]
        right = link(page, nxt, f"{nxt.title} ➡️")
    else:
        right = link(page, HOME, "🏁 Hoàn thành – về Home")
    return f"{left} | {middle} | {right}"


def top_block(page: Page) -> str:
    crumb = breadcrumb(page)
    return f"{TOP_START}\n{crumb}\n{TOP_END}" if crumb else ""


def bottom_block(page: Page) -> str:
    return f"{BOTTOM_START}\n---\n\n{footer(page)}\n{BOTTOM_END}"


def stub(page: Page) -> str:
    parts = [top_block(page), f"# {page.title}", STUB_MARKER, bottom_block(page)]
    return "\n\n".join(part for part in parts if part) + "\n"


def apply_nav(text: str, page: Page) -> str:
    """Insert or refresh both nav blocks; everything else in `text` is preserved."""
    top = top_block(page)
    if _TOP_RE.search(text):
        text = _TOP_RE.sub(lambda _: top, text, count=1)
    elif top:
        text = f"{top}\n\n{text}"
    bottom = bottom_block(page)
    if _BOTTOM_RE.search(text):
        text = _BOTTOM_RE.sub(lambda _: bottom, text, count=1)
    else:
        text = f"{text.rstrip()}\n\n{bottom}\n"
    return text
