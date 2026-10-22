from pathlib import Path

from tools.check_docs import check_links, check_python_blocks, check_sections, run_checks
from tools.manifest import BY_PATH
from tools.scaffold import scaffold


def test_check_links_reports_broken_and_absolute_ignores_external_and_code(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    text = (
        "[ok](./a.md#part) [web](https://fastapi.tiangolo.com) [anchor](#top)\n"
        "`[inline](./nope.md)`\n"
        "```markdown\n[fenced](./nope.md)\n```\n"
        "[bad](./missing.md) [abs](/a.md)\n"
    )
    assert check_links("b.md", text, tmp_path) == [
        "b.md: broken link -> ./missing.md",
        "b.md: absolute link not allowed -> /a.md",
    ]


def test_check_sections_lists_missing_lesson_sections():
    page = BY_PATH["01-fresher/02-control-flow.md"]
    text = "## 🎯 Mục tiêu\n## 📖 Lý thuyết\n## 💻 Ví dụ\n## ⚠️ Lỗi thường gặp\n## 🏋️ Bài tập\n"
    assert check_sections(page, text) == [
        "01-fresher/02-control-flow.md: missing section 'Checklist tự đánh giá'",
        "01-fresher/02-control-flow.md: missing section 'Đọc thêm'",
    ]


def test_check_python_blocks_flags_syntax_errors_unless_nocheck():
    good = "```python\nx: int = 1\n```\n"
    skipped = "<!-- nocheck -->\n```python\ndef broken(:\n```\n"
    indented = "1. Step\n\n   ```python\n   print('hi')\n   ```\n"
    assert check_python_blocks("p.md", good + skipped + indented) == []
    errors = check_python_blocks("p.md", "```python\ndef broken(:\n```\n")
    assert len(errors) == 1
    assert "python syntax error" in errors[0]


def test_scaffolded_tree_passes_and_strict_reports_every_stub(tmp_path: Path):
    scaffold(tmp_path)
    assert run_checks(tmp_path) == []
    assert run_checks(tmp_path, no_stub={"README.md"}) == ["README.md: still a stub"]
    strict = run_checks(tmp_path, strict=True)
    assert len(strict) == 61
    assert all(error.endswith("still a stub") for error in strict)


def test_orphans_and_missing_toc_links_are_reported(tmp_path: Path):
    scaffold(tmp_path)
    (tmp_path / "extra.md").write_text("# Extra\n", encoding="utf-8")
    home = tmp_path / "README.md"
    home.write_text(home.read_text(encoding="utf-8").replace("<!-- STUB -->", "Nội dung"), encoding="utf-8")
    errors = run_checks(tmp_path)
    assert "extra.md: not listed in tools/manifest.py" in errors
    assert "README.md: missing link to 01-fresher/README.md" in errors
