"""Single source of truth for every page of the roadmap and its reading order."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from typing import Literal

Kind = Literal["home", "level", "lesson", "milestone", "reference"]


@dataclass(frozen=True)
class Page:
    path: str  # POSIX path relative to the repo root
    title: str
    kind: Kind
    section: str = ""  # display name of the owning level / section

    @property
    def folder(self) -> str:
        return posixpath.dirname(self.path)


def _level(folder: str, name: str, lessons: list[tuple[str, str]]) -> list[Page]:
    index = Page(f"{folder}/README.md", name, "level", name)
    return [
        index,
        *(
            Page(f"{folder}/{slug}.md", title, "lesson", name)
            for slug, title in lessons
        ),
    ]


HOME = Page("README.md", "Lộ trình Python & FastAPI: Fresher → Senior", "home")

PROJECT = "Dự án TaskFlow"
PROJECT_INDEX = Page("project/README.md", PROJECT, "reference", PROJECT)
M0 = Page(
    "project/m0-cli-task-manager.md", "M0 – CLI Task Manager", "milestone", PROJECT
)
M1 = Page("project/m1-crud-api.md", "M1 – CRUD API", "milestone", PROJECT)
M2 = Page("project/m2-production-api.md", "M2 – Production API", "milestone", PROJECT)
M3 = Page("project/m3-scalable-api.md", "M3 – Scalable API", "milestone", PROJECT)

GETTING_STARTED = _level(
    "00-getting-started",
    "Getting Started",
    [
        ("01-setup-environment", "Cài đặt môi trường"),
        ("02-python-for-csharp-devs", "Python cho dev C#"),
    ],
)
FRESHER = _level(
    "01-fresher",
    "Fresher",
    [
        ("01-syntax-variables-types", "Cú pháp, biến & kiểu dữ liệu"),
        ("02-control-flow", "Điều kiện & vòng lặp"),
        ("03-collections", "Collections: list, tuple, dict, set"),
        ("04-comprehensions", "Comprehension"),
        ("05-functions", "Hàm"),
        ("06-modules-packages", "Module & package"),
        ("07-exceptions", "Exceptions"),
        ("08-file-io-json", "File I/O & JSON"),
        ("09-oop-dataclasses", "OOP & dataclass"),
        ("10-type-hints-basics", "Type hints cơ bản"),
        ("11-tooling-ruff-debugging", "Công cụ: ruff & debugging"),
    ],
)
JUNIOR = _level(
    "02-junior",
    "Junior",
    [
        ("01-iterators-generators", "Iterator & generator"),
        ("02-decorators-context-managers", "Decorator & context manager"),
        ("03-advanced-typing-mypy", "Typing nâng cao & mypy"),
        ("04-pytest-basics", "pytest cơ bản"),
        ("05-fastapi-first-app", "FastAPI đầu tiên"),
        ("06-pydantic-v2", "Pydantic v2"),
        ("07-error-handling", "Xử lý lỗi trong FastAPI"),
        ("08-dependency-injection", "Dependency Injection"),
        ("09-project-structure-settings", "Cấu trúc project & settings"),
    ],
)
MIDDLE = _level(
    "03-middle",
    "Middle",
    [
        ("01-async-asyncio", "Async & asyncio"),
        ("02-sqlalchemy-orm", "SQLAlchemy 2.0 ORM"),
        ("03-alembic-migrations", "Alembic migrations"),
        ("04-repository-service-layer", "Repository & Service layer"),
        ("05-authentication-jwt", "Authentication với JWT"),
        ("06-authorization", "Authorization"),
        ("07-testing-fastapi", "Testing FastAPI"),
        (
            "08-middleware-lifespan-background",
            "Middleware, lifespan & background tasks",
        ),
        ("09-pagination-filtering", "Phân trang, lọc & sắp xếp"),
        ("10-logging-error-handling", "Logging & xử lý lỗi toàn cục"),
        ("11-docker-compose", "Docker & docker-compose"),
        ("12-ci-github-actions", "CI với GitHub Actions"),
    ],
)
SENIOR = _level(
    "04-senior",
    "Senior",
    [
        ("01-python-internals-concurrency", "Python internals & concurrency"),
        ("02-profiling-performance", "Profiling & hiệu năng"),
        ("03-caching-redis", "Caching với Redis"),
        ("04-task-queues", "Task queue"),
        ("05-websockets-sse", "WebSocket & SSE"),
        ("06-clean-architecture", "Clean Architecture"),
        ("07-advanced-api-design", "Thiết kế API nâng cao"),
        ("08-security-owasp", "Bảo mật: OWASP API Top 10"),
        ("09-observability", "Observability"),
        ("10-production-deployment", "Deploy production"),
        ("11-system-design-scaling", "System design & scaling"),
        ("12-senior-soft-skills", "Kỹ năng senior"),
    ],
)

APPENDIX = [
    Page("appendix/csharp-vs-python.md", "C# vs Python", "reference", "Phụ lục"),
    Page("appendix/glossary.md", "Thuật ngữ", "reference", "Phụ lục"),
    Page("appendix/resources.md", "Tài nguyên học", "reference", "Phụ lục"),
    Page("appendix/self-assessment.md", "Tự đánh giá", "reference", "Phụ lục"),
]
SELF_ASSESSMENT = APPENDIX[3]

LEVELS = [GETTING_STARTED, FRESHER, JUNIOR, MIDDLE, SENIOR]
MILESTONE_OF_LEVEL = {
    "01-fresher": M0,
    "02-junior": M1,
    "03-middle": M2,
    "04-senior": M3,
}

READING_ORDER = [
    HOME,
    *GETTING_STARTED,
    *FRESHER,
    M0,
    *JUNIOR,
    M1,
    *MIDDLE,
    M2,
    *SENIOR,
    M3,
]
REFERENCE_PAGES = [PROJECT_INDEX, *APPENDIX]
ALL_PAGES = [*READING_ORDER, *REFERENCE_PAGES]
BY_PATH = {page.path: page for page in ALL_PAGES}


def level_index(page: Page) -> Page:
    """README of the level folder that owns `page`."""
    return BY_PATH[f"{page.folder}/README.md"]


def required_links(page: Page) -> list[Page]:
    """Pages that `page` must link to once it is no longer a stub (its table of contents)."""
    if page.kind == "home":
        return [level[0] for level in LEVELS] + REFERENCE_PAGES
    if page.kind == "level":
        lessons = [
            p for p in ALL_PAGES if p.kind == "lesson" and p.folder == page.folder
        ]
        milestone = MILESTONE_OF_LEVEL.get(page.folder)
        return [*lessons, *([milestone] if milestone else []), SELF_ASSESSMENT]
    if page == PROJECT_INDEX:
        return [M0, M1, M2, M3]
    if page == SELF_ASSESSMENT:
        return [level[0] for level in LEVELS]
    return []
