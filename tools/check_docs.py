"""Validate the roadmap: links, navigation, required sections, Python snippets, stubs."""

from __future__ import annotations

import argparse
import ast
import posixpath
import re
import sys
import textwrap
from pathlib import Path

from tools.manifest import ALL_PAGES, BY_PATH, Page, required_links
from tools.nav import STUB_MARKER, bottom_block, top_block

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = {
    ".git",
    ".agents",
    ".superpowers",
    ".venv",
    ".pytest_cache",
    "docs",
    "tools",
    "tests",
    "node_modules",
}

FENCE_RE = re.compile(r"^([ \t]*)```.*?^\1```", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
PY_BLOCK_RE = re.compile(
    r"(<!-- nocheck -->[ \t]*\n)?^([ \t]*)```python[ \t]*\n(.*?)^\2```",
    re.DOTALL | re.MULTILINE,
)

SECTIONS: dict[str, tuple[str, ...]] = {
    "lesson": (
        "Mục tiêu",
        "Lý thuyết",
        "Ví dụ",
        "Lỗi thường gặp",
        "Bài tập",
        "Checklist tự đánh giá",
        "Đọc thêm",
    ),
    "milestone": (
        "Bối cảnh",
        "Yêu cầu chức năng",
        "Yêu cầu kỹ thuật",
        "Gợi ý cấu trúc thư mục",
        "Gợi ý triển khai",
        "Definition of Done",
        "Thử thách thêm",
    ),
    "level": ("Mục tiêu đầu ra", "Mục lục"),
}


def strip_code(text: str) -> str:
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))


def _local_targets(text: str) -> list[str]:
    return [
        t
        for t in LINK_RE.findall(strip_code(text))
        if not t.startswith(("http://", "https://", "mailto:", "#"))
    ]


def _resolve(page_path: str, target: str) -> str:
    return posixpath.normpath(
        posixpath.join(posixpath.dirname(page_path), target.split("#", 1)[0])
    )


def check_links(page_path: str, text: str, root: Path) -> list[str]:
    errors: list[str] = []
    for target in _local_targets(text):
        if target.startswith("/"):
            errors.append(f"{page_path}: absolute link not allowed -> {target}")
        elif not (root / _resolve(page_path, target)).exists():
            errors.append(f"{page_path}: broken link -> {target}")
    return errors


def check_required_links(page: Page, text: str) -> list[str]:
    have = {_resolve(page.path, t) for t in _local_targets(text)}
    return [
        f"{page.path}: missing link to {p.path}"
        for p in required_links(page)
        if p.path not in have
    ]


def check_sections(page: Page, text: str) -> list[str]:
    return [
        f"{page.path}: missing section '{name}'"
        for name in SECTIONS.get(page.kind, ())
        if not re.search(rf"^## .*{re.escape(name)}", text, re.MULTILINE)
    ]


def check_python_blocks(page_path: str, text: str) -> list[str]:
    errors: list[str] = []
    for match in PY_BLOCK_RE.finditer(text):
        if match.group(1):
            continue
        try:
            ast.parse(textwrap.dedent(match.group(3)))
        except SyntaxError as exc:
            line = text.count("\n", 0, match.start(2)) + 1 + (exc.lineno or 0)
            errors.append(f"{page_path}:{line}: python syntax error: {exc.msg}")
    return errors


def check_nav(page: Page, text: str) -> list[str]:
    errors: list[str] = []
    top = top_block(page)
    if top and top not in text:
        errors.append(
            f"{page.path}: nav:top missing or outdated (run: python3 -m tools.scaffold)"
        )
    if bottom_block(page) not in text:
        errors.append(
            f"{page.path}: nav:bottom missing or outdated (run: python3 -m tools.scaffold)"
        )
    return errors


def iter_markdown(root: Path) -> list[str]:
    found = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root)
        if rel.parts[0] not in EXCLUDED_DIRS:
            found.append(rel.as_posix())
    return sorted(found)


def run_checks(
    root: Path, strict: bool = False, no_stub: set[str] | None = None
) -> list[str]:
    errors: list[str] = []
    must_be_written = no_stub or set()
    for page in ALL_PAGES:
        path = root / page.path
        if not path.exists():
            errors.append(f"{page.path}: missing file")
            continue
        text = path.read_text(encoding="utf-8")
        errors += check_links(page.path, text, root)
        errors += check_nav(page, text)
        errors += check_python_blocks(page.path, text)
        if STUB_MARKER in text:
            if strict or page.path in must_be_written:
                errors.append(f"{page.path}: still a stub")
            continue
        errors += check_sections(page, text)
        errors += check_required_links(page, text)
    for orphan in sorted(set(iter_markdown(root)) - set(BY_PATH)):
        errors.append(f"{orphan}: not listed in tools/manifest.py")
    return errors


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 12):
        print(
            f"Warning: Python {sys.version_info.major}.{sys.version_info.minor} detected. "
            "Python 3.12+ is recommended to parse modern Python AST snippets.",
            file=sys.stderr,
        )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict", action="store_true", help="fail if any page is still a stub"
    )
    parser.add_argument(
        "--no-stub",
        nargs="+",
        default=[],
        metavar="PATH",
        help="repo-relative page paths that must not be stubs",
    )
    args = parser.parse_args(argv)
    no_stub = {Path(p).as_posix() for p in args.no_stub}
    errors = run_checks(ROOT, strict=args.strict, no_stub=no_stub)
    for error in errors:
        print(error)
    print(f"check_docs: {len(errors)} error(s) in {len(ALL_PAGES)} pages")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
