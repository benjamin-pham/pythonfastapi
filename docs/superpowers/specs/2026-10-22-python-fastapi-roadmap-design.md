# Design: Lộ trình học Python & FastAPI (Fresher → Senior)

- **Ngày:** 2026-10-22
- **Trạng thái:** Chờ review
- **Loại:** Bộ tài liệu Markdown liên kết (không kèm source code chạy được)

## 1. Mục tiêu

Tạo bộ tài liệu tự học giúp một developer **C#/ASP.NET** (biết chút TypeScript/React, chưa biết Python) đi từ Fresher đến Senior Python/FastAPI.

**Tiêu chí thành công**
- Đọc được trọn vẹn trong VS Code Markdown Preview và GitHub/GitLab; mọi link nội bộ click được, không link chết.
- Mỗi bài theo cùng một template (mục 4).
- Có dự án xuyên suốt (TaskFlow API) lớn dần theo level.
- Liên hệ kiến thức C#/ASP.NET ở những chỗ có tương đương.

**Ngoài phạm vi (YAGNI)**
- Không có source code lời giải chạy được, không có thư mục code dự án. (Ngoại lệ: script QA nội bộ trong `tools/` để kiểm tra tài liệu — không phải nội dung học.)
- Không build website (MkDocs...), không dùng wikilink Obsidian.
- Không có GraphQL, không có file câu hỏi phỏng vấn riêng.

## 2. Quy ước chung

- Ngôn ngữ: tiếng Việt, giữ thuật ngữ kỹ thuật tiếng Anh.
- Link: **chỉ dùng link tương đối** dạng `[text](../02-junior/README.md)`; không dùng đường dẫn tuyệt đối, không dùng wikilink.
- Tên file: `kebab-case`, có tiền tố số 2 chữ số để giữ thứ tự (`01-...md`).
- Sơ đồ: Mermaid (`flowchart`), chỉ ở README gốc và README level khi cần.
- Gợi ý / lời giải gợi ý: đặt trong `<details><summary>💡 Gợi ý</summary> ... </details>`.
- Stack: Python 3.13+, uv, ruff, mypy/pyright, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, Redis, pytest + httpx, Docker, GitHub Actions, OpenTelemetry.

## 3. Cấu trúc thư mục

```
pythonfastapi/
├── README.md
├── 00-getting-started/
│   ├── README.md
│   ├── 01-setup-environment.md
│   └── 02-python-for-csharp-devs.md
├── 01-fresher/
│   ├── README.md
│   ├── 01-syntax-variables-types.md
│   ├── 02-control-flow.md
│   ├── 03-collections.md
│   ├── 04-comprehensions.md
│   ├── 05-functions.md
│   ├── 06-modules-packages.md
│   ├── 07-exceptions.md
│   ├── 08-file-io-json.md
│   ├── 09-oop-dataclasses.md
│   ├── 10-type-hints-basics.md
│   └── 11-tooling-ruff-debugging.md
├── 02-junior/
│   ├── README.md
│   ├── 01-iterators-generators.md
│   ├── 02-decorators-context-managers.md
│   ├── 03-advanced-typing-mypy.md
│   ├── 04-pytest-basics.md
│   ├── 05-fastapi-first-app.md
│   ├── 06-pydantic-v2.md
│   ├── 07-error-handling.md
│   ├── 08-dependency-injection.md
│   └── 09-project-structure-settings.md
├── 03-middle/
│   ├── README.md
│   ├── 01-async-asyncio.md
│   ├── 02-sqlalchemy-orm.md
│   ├── 03-alembic-migrations.md
│   ├── 04-repository-service-layer.md
│   ├── 05-authentication-jwt.md
│   ├── 06-authorization.md
│   ├── 07-testing-fastapi.md
│   ├── 08-middleware-lifespan-background.md
│   ├── 09-pagination-filtering.md
│   ├── 10-logging-error-handling.md
│   ├── 11-docker-compose.md
│   └── 12-ci-github-actions.md
├── 04-senior/
│   ├── README.md
│   ├── 01-python-internals-concurrency.md
│   ├── 02-profiling-performance.md
│   ├── 03-caching-redis.md
│   ├── 04-task-queues.md
│   ├── 05-websockets-sse.md
│   ├── 06-clean-architecture.md
│   ├── 07-advanced-api-design.md
│   ├── 08-security-owasp.md
│   ├── 09-observability.md
│   ├── 10-production-deployment.md
│   ├── 11-system-design-scaling.md
│   └── 12-senior-soft-skills.md
├── project/
│   ├── README.md
│   ├── m0-cli-task-manager.md
│   ├── m1-crud-api.md
│   ├── m2-production-api.md
│   └── m3-scalable-api.md
└── appendix/
    ├── csharp-vs-python.md
    ├── glossary.md
    ├── resources.md
    └── self-assessment.md
```

Tổng: 46 bài học + 6 README (gốc, 00–04) + 5 file project + 4 appendix = **61 file** (cộng file spec này).

## 4. Template

### 4.1 Bài học

```markdown
[🏠 Home](../README.md) › [<Level>](./README.md) › Bài NN

# Bài NN: <Tiêu đề>

> ⏱️ Thời lượng: ~X giờ · 📌 Yêu cầu trước: <link bài trước nếu cần>

## 🎯 Mục tiêu
## 🔁 So sánh với C# / ASP.NET     (bỏ nếu không có tương đương)
## 📖 Lý thuyết
## 💻 Ví dụ
## ⚠️ Lỗi thường gặp
## 🏋️ Bài tập                      (2–4 bài, gợi ý trong <details>)
## ✅ Checklist tự đánh giá          (dạng - [ ])
## 🔗 Đọc thêm                       (ưu tiên docs chính thức)

---
[⬅️ Bài trước](./NN-1-...md) | [📚 Mục lục <Level>](./README.md) | [Bài tiếp ➡️](./NN+1-...md)
```

Breadcrumb và thanh điều hướng **được sinh tự động** từ một manifest duy nhất (`tools/manifest.py`) bởi `python3 -m tools.scaffold`, nằm giữa các marker `<!-- nav:top -->…<!-- /nav:top -->` và `<!-- nav:bottom -->…<!-- /nav:bottom -->`; không sửa tay. Nhãn link ⬅️/➡️ hiển thị **tiêu đề trang đích** (vd. `⬅️ Collections: list, tuple, dict, set`) thay vì chữ "Bài trước/Bài tiếp".

Quy tắc thanh điều hướng ở bài đầu/cuối level:
- Bài đầu level: "⬅️" trỏ về `README.md` của level đó.
- Bài cuối level 01–04: "➡️" trỏ tới milestone dự án của level; milestone trỏ tiếp tới README level kế tiếp (M3 trỏ về README gốc).
- Bài cuối level 00 (không có milestone): "➡️" trỏ thẳng tới `01-fresher/README.md`.

### 4.2 README của level
Breadcrumb · Mục tiêu đầu ra · Thời lượng ước tính · Bảng mục lục (STT, bài, thời lượng) · Link milestone dự án · Link `self-assessment.md` · Thanh điều hướng theo luồng tuyến tính (trang trước trong luồng đọc | 🏠 Home | bài đầu tiên của level).

### 4.3 Milestone dự án
Breadcrumb · Bối cảnh · Yêu cầu chức năng · Yêu cầu kỹ thuật · Gợi ý cấu trúc thư mục · Gợi ý triển khai (`<details>`) · Definition of Done (checklist) · Thử thách thêm · Điều hướng.

## 5. Luồng đọc tuyến tính

```
README → 00 (README → 01 → 02)
       → 01-fresher (README → 01..11) → project/m0
       → 02-junior  (README → 01..09) → project/m1
       → 03-middle  (README → 01..12) → project/m2
       → 04-senior  (README → 01..12) → project/m3 → README (hoàn thành)
```
`appendix/*` và `project/README.md` là trang tra cứu: link về Home, không nằm trong chuỗi prev/next.

## 6. Nội dung chính theo level

| Level | Thời lượng | Trọng tâm | Milestone |
|---|---|---|---|
| 00 Getting Started | 2–3 ngày | Cài đặt, uv, venv, VS Code, tư duy Pythonic cho dev C# | — |
| 01 Fresher | 3–4 tuần | Python core, OOP, type hints, tooling | M0: CLI task manager, lưu JSON |
| 02 Junior | 4–5 tuần | Generator, decorator, typing nâng cao, pytest, FastAPI cơ bản, Pydantic, DI | M1: CRUD API in-memory + test |
| 03 Middle | 6–8 tuần | Async, SQLAlchemy, Alembic, layering, JWT, testing, Docker, CI | M2: Postgres + auth + Docker + CI |
| 04 Senior | 2–3 tháng+ | Internals, performance, Redis, queue, WebSocket, kiến trúc, bảo mật, observability, deploy, system design, soft skills | M3: cache, background jobs, realtime, observability, rate limit |

**Dự án TaskFlow API** — domain: User, Project, Task (title, description, status, priority, due_date, assignee), Comment. M0 chỉ có Task; M1 thêm Project; M2 thêm User/auth/phân quyền; M3 thêm Comment, notification, realtime.

## 7. Kiểm tra chất lượng

- Bộ công cụ QA (Python stdlib, commit trong `tools/` + `tests/`): `tools/manifest.py` (danh sách trang + thứ tự đọc), `tools/scaffold.py` (tạo stub + sinh nav), `tools/check_docs.py` (link chết, nav đúng, section bắt buộc, link mục lục bắt buộc, cú pháp code Python, file mồ côi, `--strict` báo stub còn sót).
- Rà soát mỗi bài có đủ các section bắt buộc của template.
- Code ví dụ phải đúng cú pháp Python 3.13+ / API FastAPI–Pydantic v2–SQLAlchemy 2.0 hiện hành.
