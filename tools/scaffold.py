"""Create missing pages as stubs and (re)write nav blocks on every page. Idempotent."""

from __future__ import annotations

import sys
from pathlib import Path

from tools.manifest import ALL_PAGES
from tools.nav import apply_nav, stub

ROOT = Path(__file__).resolve().parent.parent


def scaffold(root: Path) -> tuple[int, int]:
    """Return (created, updated) page counts."""
    created = updated = 0
    for page in ALL_PAGES:
        path = root / page.path
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(stub(page), encoding="utf-8")
            created += 1
            continue
        old = path.read_text(encoding="utf-8")
        new = apply_nav(old, page)
        if new != old:
            path.write_text(new, encoding="utf-8")
            updated += 1
    return created, updated


def main() -> int:
    created, updated = scaffold(ROOT)
    print(f"scaffold: created={created} updated={updated} total={len(ALL_PAGES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
