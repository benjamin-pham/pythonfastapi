<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 07
<!-- /nav:top -->

# Testing FastAPI

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 06: Authorization](./06-authorization.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ tại sao **`httpx.AsyncClient`** kết hợp **`ASGITransport(app=app)`** là tiêu chuẩn vàng cho kiểm thử FastAPI hiện đại thay vì `TestClient` đồng bộ truyền thống.
- Cấu hình công cụ kiểm thử **`pytest`** và plugin **`pytest-asyncio`** với chế độ `asyncio_mode = "auto"` để chạy test async thanh thoát, tự nhiên.
- Làm chủ kỹ thuật **Dependency Overrides (`app.dependency_overrides`)** tương đương với `ConfigureTestServices` trong ASP.NET Core để thay thế Database Session, dịch vụ gửi email hoặc bypass tầng Authentication.
- Nắm vững chiến lược cô lập cơ sở dữ liệu đỉnh cao: **Transaction Rollback & Nested Savepoints (`session.begin_nested()`)**, giúp mỗi ca kiểm thử chạy trong một transaction biệt lập và tự động rollback 100%, đạt tốc độ thực thi milli-giây mà không gây ô nhiễm DB.
- Xây dựng bộ kiểm thử tích hợp (Integration Tests) hoàn chỉnh bao phủ đầy đủ các kịch bản: Happy Path (200, 201), Lỗi ràng buộc dữ liệu (422), Lỗi xác thực (401), Lỗi phân quyền (403), và Kiểm tra dữ liệu thực tế sau khi ghi.

---

## 🔁 So sánh với C# / ASP.NET

Đối với các kỹ sư backend C#, việc viết Integration Test cho ASP.NET Core Web API là một phần không thể thiếu trong quy trình CI/CD. Dưới đây là bảng đối chiếu giữa các khái niệm quen thuộc trong hệ sinh thái .NET và FastAPI / pytest:

| Khái niệm / Kỹ thuật | ASP.NET Core (C#) | FastAPI (Python 3.12+) |
|---|---|---|
| **Máy chủ ảo trong bộ nhớ (In-Memory Test Server)** | `WebApplicationFactory<Program>` tạo ra `TestServer` chạy in-memory | `httpx.AsyncClient` kết hợp `ASGITransport(app=app)` nạp thẳng ASGI app vào bộ nhớ |
| **HTTP Client để gọi API** | `HttpClient client = factory.CreateClient();` | `async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:` |
| **Môi trường Test Async** | xUnit / NUnit hỗ trợ tự nhiên `public async Task TestMethod()` | `pytest` + `pytest-asyncio` với `asyncio_mode = "auto"` |
| **Đè Dependency Injection (DI Override)** | `factory.WithWebHostBuilder(builder => builder.ConfigureTestServices(services => ...))` | `app.dependency_overrides[get_db] = override_get_db` |
| **Bypass Authentication** | Viết custom `AuthenticationHandler` giả lập ClaimsPrincipal | Override dependency `get_current_user` trả về entity `User` giả lập |
| **Cô lập dữ liệu Database** | `TransactionScope`, In-Memory EF Core, hoặc thư viện `Respawn` | Nested Transaction / Savepoint rollback (`session.begin_nested()`) |
| **Thiết lập & Dọn dẹp (Setup / Teardown)** | `IAsyncLifetime` (`InitializeAsync`, `DisposeAsync`) | Pytest Fixtures sử dụng từ khóa `yield` |
| **Kiểm tra kết quả (Assertions)** | `Assert.Equal(200, (int)res.StatusCode);` hoặc FluentAssertions | Câu lệnh `assert res.status_code == 200` của Python |

---

## 📖 Lý thuyết

### 1. Tại sao nên dùng `httpx.AsyncClient` thay vì `TestClient`?

Trong tài liệu cơ bản của FastAPI, bạn thường thấy hướng dẫn sử dụng `fastapi.testclient.TestClient`. Tuy nhiên, trong các dự án thực tế sử dụng cơ sở dữ liệu bất đồng bộ (asyncpg, SQLAlchemy 2.0 async), `TestClient` bộc lộ những hạn chế nghiêm trọng:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   SO SÁNH CƠ CHẾ GỌI TEST FASTAPI                      │
│                                                                        │
│ 1. TestClient (Starlette / Requests - ĐỒNG BỘ):                       │
│    [Pytest Thread] ──(requests.get)──> [Tạo Event Loop Mới ngầm]       │
│                                              │                         │
│    ⚠️ Nguy cơ: Xung đột Event Loop với AsyncSession của SQLAlchemy,     │
│    không await trực tiếp được trong test case, khó test Lifespan.       │
│                                                                        │
│ 2. httpx.AsyncClient + ASGITransport (CHUẨN DOANH NGHIỆP):            │
│    [Pytest Event Loop duy nhất]                                        │
│           │                                                            │
│           ├──> await client.get("/api/v1/tasks")                        │
│           │         │ (Gọi trực tiếp qua bộ nhớ RAM, KHÔNG tốn TCP)    │
│           │         ▼                                                  │
│           └──> [FastAPI ASGI Application]                              │
│                     │                                                  │
│                     └──> await session.execute(...) [Chung Loop]       │
└────────────────────────────────────────────────────────────────────────┘
```

**Ưu điểm vượt trội của `httpx.AsyncClient`:**
- **Chạy trên cùng Event Loop**: Toàn bộ fixture, test case, và mã nguồn API dùng chung một vòng lặp sự kiện duy nhất, loại bỏ hoàn toàn lỗi kinh điển: `RuntimeError: Task attached to a different loop`.
- **Hỗ trợ đầy đủ Lifespan**: Kích hoạt chính xác các khối `@asynccontextmanager async def lifespan(app)` (startup / shutdown).
- **Hiệu năng đỉnh cao**: `ASGITransport` chuyển giao đối tượng request thẳng vào hàm callable của ASGI app qua RAM mà không cần mở socket TCP vật lý.

### 2. Cấu hình `pytest-asyncio` với `asyncio_mode = "auto"`

Mặc định, `pytest` được thiết kế cho mã đồng bộ. Để kiểm thử các hàm `async def test_*()`, chúng ta sử dụng plugin `pytest-asyncio`. 

Hãy cấu hình `asyncio_mode = "auto"` trong file `pyproject.toml` (hoặc `pytest.ini`). Thiết lập này cho phép bạn viết trực tiếp `async def test_something():` mà không cần phải đặt decorator `@pytest.mark.asyncio` trên từng test function:

```toml
# pyproject.toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

### 3. Chiến lược cô lập Database: Nested Transaction Rollback

Khi kiểm thử các API có tương tác cơ sở dữ liệu, thử thách lớn nhất là: **Làm sao để dữ liệu do Test A tạo ra không làm sai lệch kết quả của Test B?**

Có 3 trường phái xử lý:
1. **Drop & Recreate Database trước mỗi test**: Cực kỳ chậm chạp. Nếu có 100 bài test, bộ test suite có thể mất 5-10 phút để chạy.
2. **Truncate toàn bộ các bảng sau mỗi test**: Nhanh hơn phương án 1 nhưng vẫn tốn chi phí I/O ghi đĩa và dễ vướng lỗi ràng buộc khóa ngoại (Foreign Key Constraints).
3. **Transaction Rollback với Nested Savepoint (Tiêu chuẩn vàng)**:
   - Trước khi test chạy: Bắt đầu một Connection và Transaction ở fixture.
   - Trong mỗi test case: Tạo một **Savepoint** (`session.begin_nested()`). Mọi thao tác `session.commit()` trong code API thực chất chỉ commit vào Savepoint này mà không thực sự ghi xuống database vĩnh viễn.
   - Khi test kết thúc: Fixture thực hiện **Rollback** toàn bộ transaction ngoài cùng. Dữ liệu lập tức biến mất sạch sẽ trong RAM của DB server!

```text
┌────────────────────────────────────────────────────────────────────────┐
│               CHIẾN LƯỢC TRANSACTION VÀ SAVEPOINT CHO TEST             │
│                                                                        │
│   db_engine (Session-scoped)                                           │
│       │                                                                │
│       └──> db_connection (Function-scoped)                            │
│                 │ (connection.begin() - Transaction mẹ)               │
│                 │                                                      │
│                 ├──> [Test Case 1]                                     │
│                 │       │ session.begin_nested() -> SAVEPOINT test_1    │
│                 │       │ API: INSERT task -> chỉ lưu trong savepoint  │
│                 │       │ Kết thúc test -> ROLLBACK TO SAVEPOINT       │
│                 │       ▼ Database trở lại sạch 100%!                  │
│                 │                                                      │
│                 ├──> [Test Case 2]                                     │
│                 │       │ session.begin_nested() -> SAVEPOINT test_2    │
│                 │       │ Hoàn toàn không nhìn thấy dữ liệu Test 1     │
│                 │       ▼                                              │
│                 └──> connection.rollback() (Dọn dẹp triệt để)          │
└────────────────────────────────────────────────────────────────────────┘
```

### 4. Kỹ thuật `app.dependency_overrides`

FastAPI tích hợp sẵn cơ chế ghi đè Dependency cực kỳ mạnh mẽ qua từ điển `app.dependency_overrides`. Bạn chỉ cần gán hàm dependency gốc bằng một hàm mock/fake mong muốn:

```python
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()


async def get_db() -> AsyncGenerator[AsyncSession, None]: ...


# Trong file test hoặc fixture:
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    yield test_session


app.dependency_overrides[get_db] = override_get_db

# QUAN TRỌNG: Sau khi test xong, phải luôn dọn dẹp để không làm ảnh hưởng test khác:
app.dependency_overrides.clear()
```

---

## 💻 Ví dụ thực hành

Dưới đây là kiến trúc bộ kiểm thử hoàn chỉnh cho một ứng dụng FastAPI chuẩn production sử dụng async SQLAlchemy.

### 1. File cấu hình fixtures dùng chung: `tests/conftest.py`

```python
from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Giả định import từ cấu trúc dự án thực tế
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole

# Sử dụng database test chuyên biệt (ví dụ SQLite in-memory hoặc PostgreSQL test container)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Tạo Engine cho toàn bộ phiên kiểm thử, khởi tạo schema bảng."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_connection(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    """Mở một connection riêng cho mỗi test function và bọc trong transaction mẹ."""
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        yield conn
        await trans.rollback()


@pytest.fixture
async def db_session(
    db_connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    """Tạo AsyncSession gắn chặt với connection và tự động rollback qua savepoint."""
    session_factory = async_sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        # Bắt đầu một savepoint lồng nhau (nested savepoint)
        await session.begin_nested()
        yield session
        # Sau khi test kết thúc, session tự đóng và fixture db_connection sẽ rollback


@pytest.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP Client bất đồng bộ đã được tiêm session test độc lập."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_user() -> User:
    """Tạo đối tượng User giả lập phục vụ cho việc bypass Authentication."""
    return User(
        id=1,
        email="developer@taskflow.dev",
        full_name="Nguyễn Văn Dev",
        role=UserRole.MEMBER,
        is_active=True,
    )


@pytest.fixture
async def auth_client(
    client: AsyncClient,
    mock_user: User,
) -> AsyncClient:
    """Client đã được chứng thực danh tính (đăng nhập thành công)."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return client
```

### 2. Viết Integration Test cho chức năng Task: `tests/test_tasks.py`

```python
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserRole


async def test_create_task_success(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    """Kiểm tra tạo task mới thành công khi đã xác thực (Happy Path)."""
    payload = {
        "title": "Viết Unit Test cho Module Auth",
        "description": "Bao phủ ít nhất 90% logic",
        "priority": "high",
    }

    response = await auth_client.post("/api/v1/tasks", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert "id" in data

    # Kiểm chứng trực tiếp trong cơ sở dữ liệu:
    stmt = select(Task).where(Task.id == data["id"])
    created_task = (await db_session.scalars(stmt)).first()
    assert created_task is not None
    assert created_task.title == payload["title"]


async def test_create_task_unauthenticated(client: AsyncClient) -> None:
    """Từ chối tạo task khi client chưa đăng nhập (Thiếu Token -> 401)."""
    payload = {"title": "Task không được phép"}
    response = await client.post("/api/v1/tasks", json=payload)

    assert response.status_code == 401


async def test_create_task_validation_error(auth_client: AsyncClient) -> None:
    """Trả về 422 Unprocessable Entity khi dữ liệu đầu vào không hợp lệ."""
    # Tiêu đề quá ngắn (< 3 ký tự theo schema validator)
    payload = {"title": "ab"}
    response = await auth_client.post("/api/v1/tasks", json=payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err["loc"][-1] == "title" for err in errors)


async def test_admin_only_endpoint_forbidden_for_member(
    auth_client: AsyncClient,
    mock_user: User,
) -> None:
    """Người dùng có role MEMBER không được phép truy cập endpoint của ADMIN (403)."""
    mock_user.role = UserRole.MEMBER

    response = await auth_client.delete("/api/v1/admin/tasks/purge-all")
    assert response.status_code == 403
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên dọn dẹp `app.dependency_overrides.clear()`

**Triệu chứng:** Một test case ở file `test_auth.py` ghi đè `get_current_user`, sau đó các file test khác (`test_tasks.py`, `test_projects.py`) chạy bị sai lệch kết quả hoặc luôn nhận được user giả lập mà không rõ lý do.

❌ **Sai lầm (Gây rò rỉ trạng thái):**
```python
def test_something():
    app.dependency_overrides[get_current_user] = lambda: mock_user
    # Test xong nhưng không dọn dẹp -> leak sang toàn bộ các test tiếp theo!
```

✅ **Giải pháp chuẩn:**
Luôn sử dụng cấu trúc `try ... finally` hoặc bọc trong fixture có `yield`:
```python
@pytest.fixture
async def custom_client():
    app.dependency_overrides[some_dep] = mock_dep
    yield client
    app.dependency_overrides.clear()  # Bắt buộc dọn dẹp
```

---

### 2. Dùng chung một Session giữa các Test khiến dữ liệu bị nhiễm bẩn

**Triệu chứng:** Test 1 tạo ra một bản ghi với email `test@example.com`. Khi Test 2 chạy và cũng cố gắng tạo người dùng với email đó thì bị ném lỗi `IntegrityError (Unique constraint failed)`.

❌ **Sai lầm:** Tạo một fixture `session` với `scope="session"` mà không rollback sau mỗi test.

✅ **Giải pháp:** Áp dụng mô hình **Savepoint Rollback** với `scope="function"` như đã trình bày ở phần Ví dụ thực hành. Mỗi hàm test phải là một hòn đảo độc lập tuyệt đối.

---

### 3. Gọi blocking code trong hàm async test

**Triệu chứng:** Test case chạy rất lâu hoặc bị treo (hang) khi thực hiện các lệnh sleep, đọc ghi file đồng bộ hoặc dùng thư viện `requests` thay cho `httpx`.

❌ **Sai lầm:**
```python
import time


async def test_slow_operation(auth_client: AsyncClient):
    time.sleep(2)  # Làm nghẽn toàn bộ Event Loop!
    res = await auth_client.get("/api/v1/tasks")
```

✅ **Giải pháp:**
Luôn dùng các thư viện async tương ứng:
```python
import asyncio


async def test_fast_operation(auth_client: AsyncClient):
    await asyncio.sleep(0.01)  # Nhường quyền cho Event loop
    res = await auth_client.get("/api/v1/tasks")
```

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Fixture tạo Admin Client
Hãy tạo một pytest fixture tên là `admin_client` kế thừa từ `client`. Fixture này tự động override `get_current_user` để trả về một người dùng có vai trò `UserRole.ADMIN`. Viết 2 test case:
1. `admin_client` gọi endpoint `DELETE /api/v1/admin/users/99` nhận về kết quả thành công (hoặc `204 No Content`).
2. `auth_client` (user thường) gọi cùng endpoint trên bị chặn với mã `403 Forbidden`.

<details>
<summary>💡 Gợi ý</summary>

```python
import pytest
from httpx import AsyncClient
from app.api.deps import get_current_user
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture
def admin_user() -> User:
    return User(
        id=999,
        email="superadmin@taskflow.dev",
        full_name="Quản Trị Viên Hệ Thống",
        role=UserRole.ADMIN,
        is_active=True,
    )


@pytest.fixture
async def admin_client(client: AsyncClient, admin_user: User) -> AsyncClient:
    app.dependency_overrides[get_current_user] = lambda: admin_user
    return client


async def test_admin_can_access_admin_route(admin_client: AsyncClient) -> None:
    response = await admin_client.delete("/api/v1/admin/users/99")
    assert response.status_code in (200, 204, 404)  # Không bị 403


async def test_regular_member_cannot_access_admin_route(auth_client: AsyncClient) -> None:
    response = await auth_client.delete("/api/v1/admin/users/99")
    assert response.status_code == 403
```
</details>

---

### Bài tập 2: Kiểm tra tính toàn vẹn Transaction khi API gặp lỗi
Viết một bài test chứng minh tính nguyên tử (Atomicity): Giả sử API `POST /api/v1/projects-with-tasks` thực hiện tạo 1 Project và 2 Task con. Nếu Task con thứ 2 bị lỗi validation, toàn bộ giao dịch phải được rollback và **không có bất kỳ Project nào được lưu lại trong DB**.

<details>
<summary>💡 Gợi ý</summary>

```python
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project


async def test_atomic_transaction_rollback_on_failure(
    auth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Lấy số lượng dự án hiện tại
    initial_count = await db_session.scalar(select(func.count(Project.id)))

    # Gửi payload có task thứ 2 không hợp lệ (title rỗng)
    payload = {
        "name": "Dự án thử nghiệm nguyên tử",
        "tasks": [
            {"title": "Task 1 hợp lệ"},
            {"title": ""},  # Gây lỗi validation / ném ngoại lệ
        ],
    }

    response = await auth_client.post("/api/v1/projects-with-tasks", json=payload)
    assert response.status_code in (400, 422)

    # Đảm bảo số lượng project không hề tăng lên (không bị rò rỉ dữ liệu dở dang)
    current_count = await db_session.scalar(select(func.count(Project.id)))
    assert current_count == initial_count
```
</details>

---

### Bài tập 3: Fixture sinh trước dữ liệu phân trang (Data Seeding)
Viết một fixture `seed_tasks` tự động chèn 15 bản ghi `Task` vào database thông qua `db_session`. Sau đó, viết test case gọi endpoint `GET /api/v1/tasks?limit=5&offset=10` và kiểm tra:
1. Độ dài mảng dữ liệu trả về đúng bằng 5.
2. Trường `total` trong metadata trả về bằng 15.

<details>
<summary>💡 Gợi ý</summary>

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskPriority, TaskStatus


@pytest.fixture
async def seed_tasks(db_session: AsyncSession) -> list[Task]:
    tasks = [
        Task(
            title=f"Công việc số {i:02d}",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
        )
        for i in range(1, 16)
    ]
    db_session.add_all(tasks)
    await db_session.flush()
    return tasks


async def test_pagination_limit_and_offset(
    auth_client: AsyncClient,
    seed_tasks: list[Task],
) -> None:
    response = await auth_client.get("/api/v1/tasks?limit=5&offset=10")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 5
    assert data["total"] == 15
    assert data["items"][0]["title"] == "Công việc số 11"
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi hiểu rõ tại sao `httpx.AsyncClient` kết hợp `ASGITransport(app=app)` giải quyết được các nhược điểm của `TestClient` đồng bộ.
- [ ] Tôi biết cách cấu hình `asyncio_mode = "auto"` trong `pyproject.toml` để viết test async tự nhiên.
- [ ] Tôi làm chủ kỹ thuật `app.dependency_overrides` để thay thế database session và mock người dùng đăng nhập.
- [ ] Tôi giải thích được nguyên lý hoạt động của cơ chế Transaction Rollback & Nested Savepoint trong việc cô lập môi trường test.
- [ ] Tôi luôn nhớ gọi `app.dependency_overrides.clear()` để tránh rò rỉ trạng thái giữa các bài kiểm thử.

---

## 📚 Đọc thêm

- [FastAPI Documentation – Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [HTTPX Documentation – Async Client & ASGITransport](https://www.python-httpx.org/async/)
- [pytest-asyncio Configuration & Loop Scopes](https://pytest-asyncio.readthedocs.io/en/latest/reference/configuration.html)
- [SQLAlchemy 2.0 – Managing Transactions in Tests](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Tiếp theo: Bài 08 – Middleware, lifespan & background tasks](./08-middleware-lifespan-background.md)

<!-- nav:bottom -->
---

[⬅️ Authorization](./06-authorization.md) | [📚 Mục lục Middle](./README.md) | [Middleware, lifespan & background tasks ➡️](./08-middleware-lifespan-background.md)
<!-- /nav:bottom -->
