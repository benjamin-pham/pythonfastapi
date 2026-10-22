<!-- nav:top -->
[🏠 Home](../README.md) › Junior
<!-- /nav:top -->

# Level 02: Junior – Python Nâng Cao & FastAPI Nền Tảng

Chào mừng bạn đến với **Level 02: Junior**. Nếu Level 01 đã trang bị cho bạn nền tảng vững chắc về cú pháp và mô hình dữ liệu cốt lõi của Python, thì Level 02 chính là bước chuyển mình quan trọng nhất để đưa bạn từ một lập trình viên C# / .NET sang một kỹ sư backend Python hiện đại, sẵn sàng làm việc với framework mạnh mẽ hàng đầu hiện nay: **FastAPI**.

Trong giai đoạn này, lộ trình được chia làm hai phần chiến lược:
1. **Phần 1: Python Nâng Cao & Testing (Bài 01 – 04)**: Đi sâu vào những cơ chế nội tại mà FastAPI và các framework hiện đại dựa vào: Iterator/Generator (`yield`), Decorator (higher-order functions), Context Manager (`with`), Hệ thống Static Typing chuyên sâu (PEP 695, `Protocol`, `Annotated`) và kỹ năng viết Unit Test chuyên nghiệp với `pytest`.
2. **Phần 2: Làm Chủ FastAPI & Pydantic v2 (Bài 05 – 09)**: Xây dựng RESTful API chuẩn production với FastAPI, khai thác sức mạnh parse & validate dữ liệu tốc độ cao của Pydantic v2, làm chủ cơ chế Dependency Injection độc đáo và tổ chức cấu trúc dự án chuẩn mực.

---

## 🎯 Mục tiêu đầu ra

Sau khi hoàn thành Level 02 (thời lượng dự kiến: **`4–5 tuần`**, tương đương khoảng 40–50 giờ học tập và thực hành), bạn sẽ đạt được các năng lực sau:

- **Làm chủ các cơ chế Python đứng sau FastAPI**:
  - Hiểu sâu bản chất giao thức Iterator & Generator, ứng dụng `yield` để stream dữ liệu lớn tiết kiệm RAM và quản lý vòng đời tài nguyên trong FastAPI Dependency Injection.
  - Nắm vững bản chất Decorator (khác biệt triệt để với C# `[Attribute]`), biết cách viết decorator giữ toàn vẹn metadata qua `@functools.wraps` để FastAPI đọc schema chính xác.
  - Làm chủ Context Manager (`__enter__`, `__exit__` ↔ `IDisposable` trong C#) và tạo nhanh bằng `@contextlib.contextmanager`.
  - Sử dụng thành thạo hệ thống Static Typing hiện đại: cú pháp Generic Python 3.12+ (PEP 695), Structural Subtyping với `typing.Protocol` (static duck typing), `Annotated[T, ...]` và thiết lập kiểm tra kiểu nghiêm ngặt với `mypy --strict`.
- **Kiểm thử tự động chuyên nghiệp với `pytest`**:
  - Viết unit test nhanh gọn, tự nhiên với assert rewriting thay vì các thư viện Assert cồng kềnh.
  - Thiết kế test suite theo mô hình Arrange–Act–Assert với `@pytest.fixture` (quản lý scope, teardown bằng `yield`), tham số hóa test case với `@pytest.mark.parametrize` và kiểm thử ngoại lệ với `pytest.raises`.
  - Cô lập môi trường test bằng built-in fixture `tmp_path` và `monkeypatch`.
- **Xây dựng REST API chuẩn mực với FastAPI & Pydantic v2**:
  - Hiểu rõ kiến trúc ASGI và vòng đời request trong FastAPI.
  - Định nghĩa Request/Response DTO với Pydantic v2 `BaseModel`, viết custom validators và kiểm soát schema serialization.
  - Xử lý lỗi toàn cục theo chuẩn RESTful HTTP status code, format thông điệp lỗi nhất quán.
  - Thiết kế hệ thống Dependency Injection linh hoạt với `Depends` và `Annotated` (tương đương nhưng tinh gọn hơn `IServiceProvider` / DI container của ASP.NET Core).
  - Cấu trúc mã nguồn dự án nhiều tầng sạch sẽ, quản lý biến môi trường an toàn qua `pydantic-settings`.
- **Hoàn thành dự án cột mốc thực chiến Milestone M1**:
  - Tự tay phát triển hoàn chỉnh dự án [**M1 – RESTful CRUD API**](../project/m1-crud-api.md) có đầy đủ validation, xử lý lỗi, dependency injection và bộ test coverage cao.

---

## 📚 Mục lục

Dưới đây là 9 bài học chi tiết của Level 02:

| STT | Bài học | Thời lượng | Trọng tâm kiến thức |
|:---:|---|:---:|---|
| 01 | [**Iterator & generator**](./01-iterators-generators.md) | ~3.0 giờ | Giao thức `__iter__`/`__next__` (↔ `IEnumerable`/`IEnumerator`), `yield`, `yield from`, stream dữ liệu bộ nhớ thấp, module `itertools`, hé lộ pattern `yield` trong FastAPI `Depends`. |
| 02 | [**Decorator & context manager**](./02-decorators-context-managers.md) | ~3.5 giờ | Higher-order function `fn = dec(fn)` (khác biệt với C# `[Attribute]`), decorator có tham số, `@functools.wraps`, context manager `__enter__`/`__exit__` (↔ `IDisposable`), `@contextlib.contextmanager`. |
| 03 | [**Typing nâng cao & mypy**](./03-advanced-typing-mypy.md) | ~3.5 giờ | Generic PEP 695 (`[T]`), `typing.Protocol` (structural subtyping ↔ C# interface), `Annotated[T, ...]` (trọng tâm của FastAPI DI/Validation), cấu hình `mypy --strict`. |
| 04 | [**pytest cơ bản**](./04-pytest-basics.md) | ~3.0 giờ | Assert rewriting, mô hình AAA, `@pytest.fixture` (scopes, teardown `yield`), `@pytest.mark.parametrize` (↔ `[Theory]`), `pytest.raises`, `tmp_path`, `monkeypatch`. |
| 05 | [**FastAPI đầu tiên**](./05-fastapi-first-app.md) | ~2.5 giờ | ASGI server Uvicorn, ứng dụng FastAPI đầu tiên, tự động tạo OpenAPI / Swagger UI, route handlers, path & query parameters. |
| 06 | [**Pydantic v2**](./06-pydantic-v2.md) | ~3.5 giờ | `BaseModel`, `Field`, validation (`@field_validator`, `@model_validator`), serialization model sang dict/JSON, so sánh với FluentValidation trong .NET. |
| 07 | [**Xử lý lỗi trong FastAPI**](./07-error-handling.md) | ~2.5 giờ | `HTTPException`, custom exception handlers toàn cục, chuẩn hóa định dạng lỗi RFC 7807, xử lý `RequestValidationError`. |
| 08 | [**Dependency Injection**](./08-dependency-injection.md) | ~3.5 giờ | Hệ thống DI trong FastAPI bằng `Depends`, sub-dependencies, yield dependency quản lý vòng đời kết nối DB, so sánh với IoC Container của ASP.NET Core. |
| 09 | [**Cấu trúc project & settings**](./09-project-structure-settings.md) | ~3.0 giờ | Tổ chức thư mục dự án theo domain/layer, cấu hình an toàn bằng `pydantic-settings` và file `.env`, tích hợp `APIRouter`. |

---

## 🏆 Cột mốc thực hành: Milestone M1

Sau khi hoàn thành 9 bài học lý thuyết và thực hành, bạn sẽ thực hiện đồ án cột mốc của Level 02:

👉 [**M1 – RESTful CRUD API**](../project/m1-crud-api.md)

Bạn sẽ xây dựng một dịch vụ RESTful API hoàn chỉnh phục vụ bài toán quản lý dữ liệu thực tế:
- Áp dụng triệt để kiến trúc phân tầng (Router, Service, Repository/In-memory Store).
- Validation dữ liệu chặt chẽ từ request payload bằng Pydantic v2.
- Quản lý dependencies (Database Session, Repository, Auth context) bằng hệ thống Dependency Injection của FastAPI.
- Viết test suite toàn diện đạt độ bao phủ cao với `pytest` và `TestClient`.

---

## 🧭 Đánh giá năng lực

Sau khi hoàn thành nội dung Level 02 và đồ án M1, hãy truy cập [**Bảng tự đánh giá năng lực**](../appendix/self-assessment.md) để rà soát lại các kỹ năng, sẵn sàng bước vào Level 03: Middle (Async, SQLAlchemy ORM, Alembic & Authentication)!

<!-- nav:bottom -->
---

[⬅️ M0 – CLI Task Manager](../project/m0-cli-task-manager.md) | [🏠 Home](../README.md) | [Iterator & generator ➡️](./01-iterators-generators.md)
<!-- /nav:bottom -->
