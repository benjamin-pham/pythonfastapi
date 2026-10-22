<!-- nav:top -->
[🏠 Home](../README.md) › Middle
<!-- /nav:top -->

# Level 03: Middle – Backend Kiến Trúc Sâu, Async & Production-Ready API

Chào mừng bạn đến với **Level 03: Middle**. Nếu Level 01 đã cung cấp nền tảng cú pháp cốt lõi và Level 02 giúp bạn làm quen với việc xây dựng REST API cơ bản cùng FastAPI, thì Level 03 chính là nấc thang chuyển mình mang tính quyết định: đưa bạn trở thành một **Backend Engineer thực thụ** làm chủ toàn bộ stack công nghệ hiện đại của Python trong môi trường doanh nghiệp.

Trong thế giới C# / .NET, bạn đã quen thuộc với sự bao bọc chặt chẽ của ASP.NET Core, Entity Framework Core, Identity Framework và hệ sinh thái tooling hoàn chỉnh của Microsoft. Bước sang thế giới Python & FastAPI ở cấp độ Middle, bạn sẽ trực tiếp làm chủ các thư viện cốt lõi cấu thành nên một hệ thống sản xuất (production-grade system): từ cơ chế **đơn luồng bất đồng bộ (single-threaded event loop)** của `asyncio`, ORM mạnh mẽ hàng đầu **SQLAlchemy 2.0 async**, công cụ kiểm soát tiến hóa cơ sở dữ liệu **Alembic**, cho đến tư duy kiến trúc phân tầng chuyên nghiệp (**Repository + Service + Unit of Work**), bảo mật chuẩn công nghiệp với **OAuth2 + JWT** và tự động hóa quy trình triển khai với **Docker & GitHub Actions**.

---

## 🎯 Mục tiêu đầu ra

Sau khi hoàn thành Level 03 (thời lượng dự kiến: **`6–8 tuần`**, tương đương khoảng 60–80 giờ học tập và thực hành), bạn sẽ đạt được các năng lực chuyên môn sau:

- **Lập trình bất đồng bộ chuyên sâu (`async/await` & `asyncio`)**:
  - Nắm vững bản chất Event Loop đơn luồng, mô hình I/O bất đồng bộ non-blocking dựa trên epoll/kqueue.
  - Phân biệt triệt để mô hình Task/ThreadPool của .NET CLR và Coroutine/EventLoop của Python.
  - Sử dụng thành thạo **Structured Concurrency** với `asyncio.TaskGroup` (Python 3.11+), tránh rò rỉ task mồ côi (orphan tasks).
  - Nắm vững quy tắc vàng trong FastAPI: không gọi blocking I/O trong `async def` và biết cách offload an toàn bằng `asyncio.to_thread`.
- **Hệ cơ sở dữ liệu & ORM hiện đại (SQLAlchemy 2.0 async & Alembic)**:
  - Khai báo model 100% chuẩn cú pháp SQLAlchemy 2.0 với `DeclarativeBase`, `Mapped[...]`, và `mapped_column()`.
  - Quản lý kết nối cơ sở dữ liệu phi đồng bộ bằng `create_async_engine` (asyncpg) và `AsyncSession` với `async_sessionmaker`.
  - Hiểu sâu tầm quan trọng của cờ `expire_on_commit=False` để triệt tiêu hoàn toàn lỗi kinh điển `MissingGreenlet`.
  - Soạn thảo câu truy vấn hiện đại bằng hàm `select()`, thực thi qua `scalars()`, và giải quyết triệt để vấn đề N+1 Query bằng kỹ thuật Eager Loading (`selectinload` cho collections, `joinedload` cho scalar).
  - Làm chủ công cụ migration **Alembic** với template async, tự động sinh revision dựa trên `Base.metadata`, review migration an toàn và cấu hình kết nối qua `pydantic-settings`.
- **Kiến trúc phân tầng chuyên nghiệp (Repository + Service + Unit of Work)**:
  - Phân tách rạch ròi trách nhiệm giữa Presentation (Router), Business Logic (Service), Data Access (Repository) và Transaction Boundary (Unit of Work).
  - Triệt tiêu thói quen xấu gọi `session.commit()` bừa bãi trong tầng truy cập dữ liệu, đảm bảo tính nguyên tử (ACID) của giao dịch nghiệp vụ.
  - Lắp ráp cây phụ thuộc linh hoạt thông qua hệ thống Dependency Injection của FastAPI.
- **Bảo mật xác thực & phân quyền (OAuth2, JWT & RBAC)**:
  - Băm mật khẩu an toàn hiện đại bằng `pwdlib` với thuật toán Argon2id / Bcrypt (loại bỏ thư viện lỗi thời `passlib`).
  - Thiết kế hệ thống Access Token (ngắn hạn) và Refresh Token (dài hạn) chuẩn RFC 7519 bằng thư viện `PyJWT`.
  - Tích hợp chuẩn `OAuth2PasswordBearer` và `OAuth2PasswordRequestForm` kích hoạt giao diện Authorize tương tác trên Swagger UI.
  - Triển khai phân quyền theo vai trò (Role-Based Access Control - RBAC) và phân quyền theo tài nguyên (Resource-Based / Policy-Based Authorization).
- **Kiểm thử tự động & Vận hành Production**:
  - Viết Integration Tests toàn diện cho FastAPI bằng `httpx.AsyncClient` và cơ sở dữ liệu cô lập (SQLite in-memory async hoặc PostgreSQL via Testcontainers).
  - Thiết kế Middleware tùy biến, quản lý vòng đời ứng dụng với Lifespan Context Manager, và điều phối tác vụ chạy ngầm (Background Tasks).
  - Xây dựng chuẩn phân trang Cursor/Offset, bộ lọc và sắp xếp động, quản lý lỗi toàn cục và logging có cấu trúc.
  - Đóng gói ứng dụng nhiều dịch vụ với **Docker & Docker Compose**, tự động hóa quy trình kiểm tra chất lượng mã nguồn và test tự động bằng **GitHub Actions CI**.

---

## 📚 Mục lục

Toàn bộ Level 03 được chia thành 12 bài học chuyên sâu theo lộ trình tiệm tiến:

| STT | Bài học | Thời lượng | Trọng tâm kiến thức |
|:---:|---|:---:|---|
| 01 | [**Async & asyncio**](./01-async-asyncio.md) | ~3.5 giờ | Event loop đơn luồng vs .NET ThreadPool, coroutine lifecycle, `TaskGroup` (structured concurrency), quy tắc vàng blocking I/O trong FastAPI (`asyncio.to_thread`). |
| 02 | [**SQLAlchemy 2.0 ORM**](./02-sqlalchemy-orm.md) | ~4.0 giờ | `DeclarativeBase`, `Mapped`, `mapped_column`, `AsyncSession`, `expire_on_commit=False`, `select()`, eager loading (`selectinload`, `joinedload`), giải quyết N+1 query và `MissingGreenlet`. |
| 03 | [**Alembic migrations**](./03-alembic-migrations.md) | ~3.0 giờ | Khởi tạo async template, cấu hình `env.py` với `pydantic-settings`, autogenerate revisions, review migration an toàn, `upgrade head` và `downgrade`. |
| 04 | [**Repository & Service layer**](./04-repository-service-layer.md) | ~4.0 giờ | Kiến trúc phân tầng Router – Service – Repository – Unit of Work, quản lý ranh giới transaction tập trung, tiêm phụ thuộc qua `Depends`. |
| 05 | [**Authentication với JWT**](./05-authentication-jwt.md) | ~4.0 giờ | Băm mật khẩu với `pwdlib` (Argon2id/Bcrypt), cấu trúc JWT bằng `PyJWT`, Access/Refresh Token, chuẩn `OAuth2PasswordBearer`, dependency `get_current_user`. |
| 06 | [**Authorization**](./06-authorization.md) | ~3.5 giờ | Phân biệt 401 vs 403, Role-Based Access Control (RBAC) với enum & dependency factory, Resource-based authorization (kiểm tra quyền sở hữu bản ghi). |
| 07 | [**Testing FastAPI**](./07-testing-fastapi.md) | ~4.0 giờ | Integration test với `httpx.AsyncClient`, database fixture cô lập (SQLite async / testcontainers), dependency overrides cho auth, đo lường test coverage. |
| 08 | [**Middleware, lifespan & background tasks**](./08-middleware-lifespan-background.md) | ~3.5 giờ | Vòng đời ứng dụng qua `@asynccontextmanager lifespan`, custom middleware (log latency, correlation ID), tác vụ nền `BackgroundTasks`. |
| 09 | [**Phân trang, lọc & sắp xếp**](./09-pagination-filtering.md) | ~3.5 giờ | Phân trang Offset vs Keyset/Cursor pagination, dynamic filtering & sorting an toàn với SQLAlchemy 2.0, chuẩn hóa Response Envelope metadata. |
| 10 | [**Logging & xử lý lỗi toàn cục**](./10-logging-error-handling.md) | ~3.5 giờ | Structured JSON logging (structlog), global exception handlers theo chuẩn RFC 7807 (Problem Details), correlation ID tracing. |
| 11 | [**Docker & docker-compose**](./11-docker-compose.md) | ~4.0 giờ | Multi-stage Dockerfile tối ưu image size, cấu hình `docker-compose.yml` cho cụm FastAPI + PostgreSQL + Redis, healthchecks và volume persistence. |
| 12 | [**CI với GitHub Actions**](./12-ci-github-actions.md) | ~3.5 giờ | Pipeline CI tự động: linting với `ruff`, static typing với `mypy`, chạy integration test trên PostgreSQL service container với `pytest`. |

---

## 🏆 Cột mốc thực hành: Milestone M2

Sau khi hoàn thành 12 bài học lý thuyết và bài tập thực hành, bạn sẽ bắt tay vào thực hiện đồ án cột mốc của Level 03:

👉 [**M2 – Production API**](../project/m2-production-api.md)

Bạn sẽ xây dựng một dịch vụ RESTful API hoàn chỉnh đạt tiêu chuẩn vận hành thực tế tại doanh nghiệp:
- Cơ sở dữ liệu PostgreSQL thực thụ kết nối qua SQLAlchemy 2.0 async và quản lý migrations bằng Alembic.
- Kiến trúc phân tầng rõ ràng (Router → Service → Repository + Unit of Work).
- Hệ thống bảo mật toàn diện: Đăng ký/Đăng nhập, băm mật khẩu Argon2, cấp phát cặp Access/Refresh JWT token, phân quyền RBAC và Resource-level policies.
- Bộ test suite tích hợp đầy đủ kiểm thử cả luồng nghiệp vụ và bảo mật.
- Đóng gói toàn bộ hệ sinh thái dịch vụ vào Docker Compose sẵn sàng khởi chạy trên mọi máy chủ.

---

## 🧭 Đánh giá năng lực

Sau khi hoàn thành các bài học và đồ án Milestone M2, hãy tự đối chiếu kỹ năng của mình tại [**Bảng tự đánh giá năng lực**](../appendix/self-assessment.md) để khẳng định sự sẵn sàng bước tiếp lên Level 04: Senior (Clean Architecture, Caching Redis, Message Broker, Observability & Scaling)!

<!-- nav:bottom -->
---

[⬅️ M1 – CRUD API](../project/m1-crud-api.md) | [🏠 Home](../README.md) | [Async & asyncio ➡️](./01-async-asyncio.md)
<!-- /nav:bottom -->
