from tools.manifest import ALL_PAGES, BY_PATH, M0, M3, READING_ORDER
from tools.nav import apply_nav, bottom_block, breadcrumb, footer, rel, stub, top_block


def test_rel_same_folder_parent_and_child():
    assert rel("01-fresher/02-control-flow.md", "01-fresher/README.md") == "./README.md"
    assert rel("01-fresher/02-control-flow.md", "README.md") == "../README.md"
    assert rel("README.md", "01-fresher/README.md") == "./01-fresher/README.md"


def test_manifest_has_61_unique_pages():
    assert len(ALL_PAGES) == 61
    assert len(BY_PATH) == 61


def test_lesson_breadcrumb():
    page = BY_PATH["01-fresher/03-collections.md"]
    assert breadcrumb(page) == "[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 03"


def test_first_lesson_footer_points_back_to_level_index():
    page = BY_PATH["01-fresher/01-syntax-variables-types.md"]
    assert footer(page) == (
        "[⬅️ Fresher](./README.md) | [📚 Mục lục Fresher](./README.md) | "
        "[Điều kiện & vòng lặp ➡️](./02-control-flow.md)"
    )


def test_last_lesson_leads_to_milestone_then_next_level():
    last = BY_PATH["01-fresher/11-tooling-ruff-debugging.md"]
    assert footer(last).endswith("[M0 – CLI Task Manager ➡️](../project/m0-cli-task-manager.md)")
    assert footer(M0).endswith("[Junior ➡️](../02-junior/README.md)")


def test_getting_started_last_lesson_goes_to_fresher():
    page = BY_PATH["00-getting-started/02-python-for-csharp-devs.md"]
    assert footer(page).endswith("[Fresher ➡️](../01-fresher/README.md)")


def test_final_milestone_returns_home():
    assert READING_ORDER[-1] == M3
    assert footer(M3).endswith("[🏁 Hoàn thành – về Home](../README.md)")


def test_home_has_no_breadcrumb_and_a_start_link():
    home = READING_ORDER[0]
    assert top_block(home) == ""
    assert footer(home) == "[Bắt đầu: Getting Started ➡️](./00-getting-started/README.md)"


def test_apply_nav_is_idempotent_and_replaces_stale_blocks():
    page = BY_PATH["02-junior/04-pytest-basics.md"]
    fresh = stub(page)
    assert apply_nav(fresh, page) == fresh
    stale = fresh.replace("Bài 04", "Bài 99")
    assert apply_nav(stale, page) == fresh


def test_apply_nav_adds_missing_blocks():
    page = BY_PATH["appendix/glossary.md"]
    result = apply_nav("# Thuật ngữ\n", page)
    assert top_block(page) in result
    assert bottom_block(page) in result
