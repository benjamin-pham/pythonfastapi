<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 08
<!-- /nav:top -->

# Dependency Injection

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 07: Xử lý lỗi trong FastAPI](./07-error-handling.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu thấu đáo triết lý và cơ chế hoạt động của hệ thống **Dependency Injection (DI)** trong FastAPI thông qua hàm **`Depends()`**.
- Áp dụng thành thạo cú pháp tiêm phụ thuộc hiện đại theo chuẩn PEP 593: **`Annotated[ServiceType, Depends(dependency_fn)]`**.
- So sánh sâu sắc với **IoC / DI Container** của ASP.NET Core: đối chiếu các vòng đời dịch vụ kinh điển (**`Scoped`**, **`Singleton`**, **`Transient`**) với cơ chế của FastAPI (**`use_cache=True`**, **`lifespan`**, **`use_cache=False`**).
- Nắm vững mô hình dọn dẹp và giải phóng tài nguyên cuối request bằng từ khóa **`yield`** (tương đương với `IDisposable` / `Dispose()` trong C#).
- Xây dựng và điều phối cây phụ thuộc phân cấp (**Sub-dependencies / Dependency Graph**) và hiểu quy tắc giải quyết (Resolution Order).
- Phân biệt và ứng dụng Dependency ở các phạm vi khác nhau: **Route Parameter**, **Route Level**, **APIRouter Level**, và **FastAPI App Level**.
- Làm chủ kỹ thuật Mocking mạnh mẽ trong kiểm thử tự động với **`app.dependency_overrides`**.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET, hệ thống DI (`Microsoft.Extensions.DependencyInjection`) là trái tim của framework ASP.NET Core. Mọi dịch vụ đều phải được đăng ký tập trung vào `IServiceCollection` trong file `Program.cs` và được giải quyết thông qua Constructor Injection (`public MyController(IService service)`).

Trong FastAPI, Dependency Injection được thiết kế theo phong cách phi tập trung, hàm tính (functional), và tiêm trực tiếp qua tham số của hàm (Parameter Injection) vô cùng tinh gọn:

| Khái niệm / Cơ chế | C# / ASP.NET Core | Python / FastAPI |
|---|---|---|
| **Hình thức tiêm** | Constructor Injection trên Controller / Minimal API lambda | Parameter Injection trên hàm xử lý route |
| **Đăng ký dịch vụ** | Đăng ký tập trung trong `Program.cs`: `builder.Services.AddScoped<ITaskService, TaskService>()` | Không cần đăng ký trước: Bất kỳ callable nào (hàm, class, generator) đều dùng được ngay với `Depends()` |
| **Khai báo nhận dependency** | Khai báo tham số trong hàm khởi tạo: `public TaskController(ITaskService service)` | Khai báo trong type hint: `service: Annotated[TaskService, Depends(get_task_service)]` |
| **Vòng đời Scoped** | `AddScoped`: Một instance duy nhất cho mỗi HTTP request | **Mặc định** với `Depends(fn, use_cache=True)`: Chỉ gọi hàm 1 lần trong suốt vòng đời của 1 request |
| **Vòng đời Transient** | `AddTransient`: Tạo mới một instance mỗi khi được yêu cầu | `Depends(fn, use_cache=False)`: Luôn thực thi lại hàm dependency mỗi khi được inject |
| **Vòng đời Singleton** | `AddSingleton`: Một instance duy nhất cho toàn bộ vòng đời ứng dụng | Khởi tạo tài nguyên tập trung trong `@asynccontextmanager def lifespan(app: FastAPI)` |
| **Dọn dẹp tài nguyên (Teardown)** | Tự động gọi `Dispose()` trên các dịch vụ thực thi `IDisposable` khi HttpContext kết thúc | Sử dụng từ khóa `yield` bên trong dependency function (khối `finally:` chạy sau khi gửi response) |
| **Giả lập trong Unit Test** | `builder.ConfigureTestServices(services => services.AddSingleton<ITaskService, MockService>())` | Gán đè trực tiếp qua từ điển: `app.dependency_overrides[get_task_service] = get_mock_service` |

---

## 📖 Lý thuyết

### 1. Triết lý DI trong FastAPI: Tinh gọn và Linh hoạt

Trong nhiều framework truyền thống, bạn phải học hàng tá khái niệm phức tạp: Service Provider, Service Locator, Service Lifetime, Reflection, Container registration.

FastAPI tiếp cận bài toán Dependency Injection với một triết lý tối giản:
1. **Một Dependency thực chất là một "Callable"**: Bất kỳ hàm Python thông thường nào (`def`), hàm bất đồng bộ (`async def`), hoặc Class có hàm khởi tạo đều có thể đóng vai trò là một dependency.
2. **Không cần Container đăng ký trước**: Bạn không cần một file cấu hình đăng ký hàng trăm interface. Khi một route cần một phụ thuộc, nó chỉ việc gọi `Depends(tên_hàm)`.
3. **Tự động suy luận cây phụ thuộc (DAG)**: Nếu dependency A cần dependency B, và B lại cần C, FastAPI sẽ tự động phân tích cây phụ thuộc, gọi C trước, truyền C vào B, rồi truyền B vào A!

### 2. Cú pháp `Annotated[T, Depends(...)]` chuẩn PEP 593

Trong các phiên bản FastAPI trước đây, bạn thường bắt gặp cú pháp gán giá trị mặc định:
```python
# Cách cũ (không khuyến khích)
@app.get("/tasks")
def get_tasks(service: TaskService = Depends(get_task_service)): ...
```
Cách viết này khiến trình kiểm tra kiểu tĩnh (như Mypy) nhầm lẫn rằng `Depends(...)` là một instance hợp lệ của `TaskService`, và làm mất khả năng gán giá trị mặc định thực sự của tham số.

Từ Python 3.9+ và PEP 593, cú pháp chuẩn mực là:
```python
from typing import Annotated
from fastapi import Depends


#  Chuẩn hiện đại: Tách bạch rõ ràng Type và Metadata
@app.get("/tasks")
def get_tasks(
    service: Annotated[TaskService, Depends(get_task_service)],
) -> list[Task]: ...
```

### 3. Vòng đời dịch vụ (Lifetimes): So sánh chi tiết với ASP.NET Core

#### a. `use_cache=True` ↔ Scoped Lifetime (Mặc định)
Trong ASP.NET Core, `AddScoped` tạo ra một instance duy nhất cho mỗi HTTP Request.
Trong FastAPI, tham số `use_cache=True` là giá trị mặc định:

```python
def get_current_user(token: str = Header()):
    print("Xác thực người dùng...")
    return decode_token(token)


@app.get("/profile")
def view_profile(
    user_a: Annotated[User, Depends(get_current_user)],
    user_b: Annotated[User, Depends(get_current_user)],
):
    # Dù khai báo 2 lần trong cùng một request, hàm get_current_user
    # chỉ được thực thi ĐÚNG 1 LẦN duy nhất! Kết quả được cache lại và dùng chung cho cả user_a và user_b.
    assert user_a is user_b
    return user_a
```

#### b. `use_cache=False` ↔ Transient Lifetime
Khi bạn muốn một dependency luôn được tính toán lại mỗi khi được tiêm (ví dụ: tạo ID ngẫu nhiên, sinh mã OTP, hoặc đo thời gian độc lập):

```python
import uuid


def generate_request_tracking_id() -> str:
    return str(uuid.uuid4())


@app.get("/action")
def do_action(
    id_1: Annotated[
        str, Depends(generate_request_tracking_id, use_cache=False)
    ],
    id_2: Annotated[
        str, Depends(generate_request_tracking_id, use_cache=False)
    ],
):
    # id_1 và id_2 sẽ nhận hai giá trị UUID hoàn toàn khác nhau!
    return {"id_1": id_1, "id_2": id_2}
```

#### c. Singleton Lifetime trong FastAPI với `lifespan`
Trong ASP.NET Core, `AddSingleton` giữ một instance xuyên suốt thời gian chạy của ứng dụng. Trong FastAPI, các tài nguyên toàn cục (như Database Connection Pool, Redis Client, hoặc Machine Learning Model) được quản lý thông qua context manager **`lifespan`**:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request


class HeavyConnectionPool:

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # --- SETUP LÚC KHỞI ĐỘNG (Singleton Init) ---
    pool = HeavyConnectionPool()
    pool.connect()
    # Gắn vào app.state để truy cập toàn cục
    app.state.db_pool = pool

    yield  # Ứng dụng lắng nghe và phục vụ requests...

    # --- TEARDOWN LÚC DỪNG ỨNG DỤNG (Singleton Dispose) ---
    pool.disconnect()


app = FastAPI(lifespan=lifespan)


# Dependency inject Singleton pool vào route:
def get_db_pool(request: Request) -> HeavyConnectionPool:
    return request.app.state.db_pool
```

### 4. Dọn dẹp tài nguyên (Teardown) với `yield`

Một trong những tính năng mạnh nhất của FastAPI DI là khả năng thực thi logic dọn dẹp sau khi HTTP Response đã được gửi về cho client. Điều này hoàn toàn tương đương với việc DI Container trong C# tự động gọi `Dispose()` trên các dịch vụ kế thừa `IDisposable`:

```python
from collections.abc import Generator


def get_db_session() -> Generator[DatabaseSession, None, None]:
    # 1. SETUP: Chạy trước khi vào Route Handler
    session = SessionLocal()
    try:
        yield session  # 2. INJECT: Trao quyền điều khiển và session cho Route Handler
        session.commit()  # 3. TEARDOWN (Thành công): Commit transaction
    except Exception:
        session.rollback()  # 4. TEARDOWN (Có lỗi): Rollback nếu có exception ném ra
        raise
    finally:
        session.close()  # 5. DỌN DẸP: Luôn đóng kết nối an toàn!
```

> [!IMPORTANT]
> Luôn đặt mã dọn dẹp trong khối `finally:` để đảm bảo kết nối cơ sở dữ liệu hoặc file handle luôn được đóng ngay cả khi Route Handler phát sinh lỗi!

### 5. Cây phụ thuộc phân cấp (Sub-dependencies)

FastAPI tự động giải quyết các phụ thuộc lồng nhau. Hãy xem xét ví dụ một Service phụ thuộc vào Repository, và Repository phụ thuộc vào Database Connection:

```text
       ┌───────────────┐
       │  HTTP Request │
       └───────┬───────┘
               │
               ▼
       ┌───────────────┐
       │ Route Handler │
       └───────┬───────┘
               │ cần
               ▼
       ┌───────────────┐
       │  TaskService  │
       └───────┬───────┘
               │ cần
               ▼
       ┌────────────────┐
       │ TaskRepository │
       └───────┬────────┘
               │ cần
               ▼
       ┌────────────────┐
       │   get_db()     │ ◄─── Chạy đầu tiên (Setup)
       └────────────────┘      Chạy cuối cùng (Teardown qua yield)
```

Khi có nhiều `yield` dependencies lồng nhau, thứ tự thực thi tuân thủ nguyên tắc **LIFO (Last In, First Out)**: Dependency được mở đầu tiên sẽ được đóng lại sau cùng.

### 6. Các cấp độ gắn Dependency trong FastAPI

FastAPI cho phép gắn Dependency ở 4 cấp độ linh hoạt tùy theo phạm vi ảnh hưởng:

1. **Cấp độ Route Parameter**: Khi endpoint cần lấy dữ liệu trả về của dependency:
   ```python
   @app.get("/tasks")
   def get_tasks(db: Annotated[Session, Depends(get_db)]): ...
   ```

2. **Cấp độ Route Decorator**: Khi cần kiểm tra điều kiện (Authentication, Header, Permission) mà không cần lấy giá trị:
   ```python
   @app.post("/admin/reset", dependencies=[Depends(verify_admin_role)])
   def reset_system(): ...
   ```

3. **Cấp độ APIRouter**: Áp dụng tự động cho toàn bộ các route nằm trong router đó:
   ```python
   admin_router = APIRouter(
       prefix="/admin",
       dependencies=[Depends(require_superadmin_api_key)],
   )
   ```

4. **Cấp độ FastAPI App (Toàn cục)**: Áp dụng cho 100% mọi request đi vào server:
   ```python
   app = FastAPI(dependencies=[Depends(check_maintenance_mode)])
   ```

### 7. Mocking và Testing với `app.dependency_overrides`

Trong ASP.NET Core, để mock một service trong bài test tích hợp, bạn phải dùng `WebApplicationFactory` kết hợp `ConfigureTestServices`. Trong FastAPI, việc này đơn giản hơn rất nhiều nhờ từ điển `app.dependency_overrides`:

```python
def test_get_task_with_mock():
    # 1. Định nghĩa dependency giả lập (Mock)
    def mock_get_task_service():
        return MockTaskService()

    # 2. Ghi đè dependency thật bằng mock
    app.dependency_overrides[get_task_service] = mock_get_task_service

    # 3. Thực hiện test bằng TestClient
    response = client.get("/api/v1/tasks/1")
    assert response.status_code == 200

    # 4. BẮT BUỘC: Xóa sạch overrides để không ảnh hưởng các test khác!
    app.dependency_overrides.clear()
```

---

## 💻 Ví dụ thực hành

Dưới đây là một ví dụ kiến trúc hoàn chỉnh thể hiện trọn vẹn sức mạnh của FastAPI Dependency Injection:
- Quản lý vòng đời kết nối với `yield`.
- Cây phụ thuộc 3 tầng: `Database` -> `TaskRepository` -> `TaskService`.
- Dependency kiểm tra Authorization header.
- Bài test mẫu với `pytest` và `TestClient` sử dụng `app.dependency_overrides`:

```python
from collections.abc import Generator
from typing import Annotated, Protocol
from fastapi import Depends, FastAPI, HTTPException, Header, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ==============================================================================
# 1. Tầng Hạ Tầng: Quản lý Kết Nối Database với yield
# ==============================================================================
class FakeDatabaseSession:
    def __init__(self) -> None:
        self.is_connected = True
        self.data: dict[int, str] = {
            1: "Học FastAPI Dependency Injection",
            2: "Áp dụng kiến trúc Clean Architecture",
        }

    def close(self) -> None:
        self.is_connected = False


def get_db() -> Generator[FakeDatabaseSession, None, None]:
    """Dependency cung cấp session database và tự động giải phóng sau request."""
    session = FakeDatabaseSession()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# 2. Tầng Repository & Service: Cây phụ thuộc lồng nhau
# ==============================================================================
class TaskRepository:
    def __init__(self, db: FakeDatabaseSession) -> None:
        self.db = db

    def get_by_id(self, task_id: int) -> str | None:
        return self.db.data.get(task_id)


def get_task_repository(
    db: Annotated[FakeDatabaseSession, Depends(get_db)],
) -> TaskRepository:
    return TaskRepository(db=db)


class TaskService:
    def __init__(self, repo: TaskRepository) -> None:
        self.repo = repo

    def retrieve_task(self, task_id: int) -> str:
        title = self.repo.get_by_id(task_id)
        if not title:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} không tồn tại!",
            )
        return title


def get_task_service(
    repo: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskService:
    return TaskService(repo=repo)


# ==============================================================================
# 3. Security Dependency: Xác thực Token
# ==============================================================================
def require_api_key(
    x_api_key: Annotated[str, Header(description="Khóa API bí mật")],
) -> str:
    if x_api_key != "secret-token-123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key không hợp lệ hoặc bị thiếu!",
        )
    return x_api_key


# ==============================================================================
# 4. FastAPI App & Route Handlers
# ==============================================================================
app = FastAPI(title="TaskFlow DI Demo API")


class TaskResponse(BaseModel):
    id: int
    title: str


@app.get(
    "/api/v1/tasks/{task_id}",
    response_model=TaskResponse,
    dependencies=[Depends(require_api_key)],  # Route-level dependency kiểm tra bảo mật
)
def read_task(
    task_id: int,
    service: Annotated[TaskService, Depends(get_task_service)],  # Inject Service
) -> TaskResponse:
    title = service.retrieve_task(task_id)
    return TaskResponse(id=task_id, title=title)


# ==============================================================================
# 5. Kiểm thử Tự động với app.dependency_overrides
# ==============================================================================
def test_read_task_with_dependency_override() -> None:
    client = TestClient(app)

    # Giả lập Mock Service không cần chạm vào FakeDatabaseSession
    class MockTaskService:
        def retrieve_task(self, task_id: int) -> str:
            return "Công việc được mock từ Test Suite"

    # Đăng ký override: Bất cứ khi nào route cần get_task_service, trả về MockTaskService
    app.dependency_overrides[get_task_service] = MockTaskService
    # Tạm thời bỏ qua bảo mật API key cho bài test này
    app.dependency_overrides[require_api_key] = lambda: "mock-key"

    try:
        response = client.get(
            "/api/v1/tasks/100",
            headers={"X-API-Key": "any-key"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": 100,
            "title": "Công việc được mock từ Test Suite",
        }
    finally:
        # Bắt buộc xóa sạch overrides sau khi test hoàn tất
        app.dependency_overrides.clear()
```

---

## ⚠️ Lỗi thường gặp

### 1. Gọi nhầm `Depends(get_db())` thay vì `Depends(get_db)`
Đây là lỗi sơ đẳng nhưng cực kỳ phổ biến. Bạn phải truyền **tham chiếu tới hàm** (Callable), chứ không được tự tay gọi hàm bằng dấu ngoặc đơn `()`:

```python
# ❌ SAI: Depends nhận kết quả trả về của get_db()
def my_route(db: Annotated[Session, Depends(get_db())]): ...


#  ĐÚNG: Depends nhận chính hàm get_db
def my_route(db: Annotated[Session, Depends(get_db)]): ...
```

### 2. Quên bọc `try...finally` trong Yield Dependency
Nếu Route Handler ném ra một ngoại lệ hoặc người dùng hủy kết nối giữa chừng, đoạn mã sau `yield` có thể không bao giờ được thực thi nếu bạn không đặt nó trong khối `finally:`:

```python
# ❌ NGUY HIỂM: Rò rỉ kết nối khi có lỗi!
def get_db():
    session = SessionLocal()
    yield session
    session.close()  # Sẽ bị bỏ qua nếu Route Handler ném HTTPException!


#  AN TOÀN TUYỆT ĐỐI:
def get_db_safe():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()  # Luôn luôn được thực thi trong mọi tình huống!
```

### 3. Không xóa `app.dependency_overrides` sau bài test
Nếu bài test A ghi đè một dependency nhưng quên gọi `.clear()`, các bài test B, C chạy sau sẽ vô tình sử dụng đối tượng mock của bài test A, gây ra hiện tượng lỗi chéo bí ẩn (Test Pollution).
> [!TIP]
> Hãy viết một pytest fixture có `autouse=True` và gọi `app.dependency_overrides.clear()` trong phần teardown để bảo vệ toàn bộ test suite tự động!

### 4. Nhầm tưởng `use_cache=True` dùng chung cho toàn server
`use_cache=True` chỉ có tác dụng cache trong phạm vi **MỘT HTTP Request duy nhất** (tương đương Scoped trong C#). Khi một request mới từ người dùng khác đi tới, toàn bộ cây dependency sẽ được thực thi lại từ đầu. Nó hoàn toàn không phải là Singleton toàn cục!

---

## ✍️ Bài tập thực hành

### Bài 1: Dependency Phân Trang Tái Sử Dụng (`PaginationParams`)
Thay vì khai báo lặp đi lặp lại `limit` và `offset` ở mọi endpoint, hãy xây dựng một Dependency Class Callable:
- Class `PaginationParams`:
  - `__init__(self, skip: int = 0, limit: int = 100)` với validation `skip >= 0`, `limit` từ 1 đến 100.
- Viết 2 endpoint `GET /api/v1/users` và `GET /api/v1/products` cùng inject `params: Annotated[PaginationParams, Depends()]`.
- Kiểm tra tính tái sử dụng và hiển thị trên Swagger UI.

<details>
<summary>💡 Gợi ý</summary>

- Khi dependency là một class, cú pháp `Depends(PaginationParams)` hoặc `Depends()` (nếu đã khai báo kiểu trong `Annotated`) sẽ tự động gọi hàm `__init__` của class đó với các query parameters tương ứng!
</details>

---

### Bài 2: Dependency Kiểm Tra Quyền Hạn Động (Dynamic Permission Checker)
Tạo một Dependency Factory (hàm trả về một hàm dependency) để kiểm tra role của người dùng:
- Hàm `require_roles(*allowed_roles: str)`.
- Khi client gửi header `X-User-Role`, dependency sẽ kiểm tra xem role có nằm trong `allowed_roles` hay không. Nếu không, ném `HTTPException(403, detail="Không đủ quyền truy cập!")`.
- Áp dụng `dependencies=[Depends(require_roles("ADMIN", "MANAGER"))]` cho route `DELETE /api/v1/projects/{project_id}`.

<details>
<summary>💡 Gợi ý</summary>

```python
def require_roles(*allowed_roles: str):

    def role_checker(x_user_role: Annotated[str, Header()]):
        if x_user_role not in allowed_roles:
            raise HTTPException(
                status_code=403, detail="Không đủ quyền truy cập!"
            )
        return x_user_role

    return role_checker
```
</details>

---

### Bài 3: Kiểm Thử Độc Lập Service bằng `app.dependency_overrides`
Cho một endpoint `POST /api/v1/notifications/send` phụ thuộc vào `EmailSenderService`.
- Viết một fixture trong Pytest:
  - Tạo instance `MockEmailSender` ghi nhận danh sách email đã gửi vào một mảng `sent_emails: list[str]`.
  - Override dependency thật trong `app.dependency_overrides`.
  - `yield` mock instance cho bài test kiểm tra.
  - Sau bài test, tự động dọn dẹp bằng `app.dependency_overrides.clear()`.
- Viết 2 bài test xác nhận email được gửi đi thành công với đúng người nhận và nội dung.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng cấu trúc fixture với `yield`:
  ```python
  @pytest.fixture
  def mock_email_sender():
      mock = MockEmailSender()
      app.dependency_overrides[get_email_sender] = lambda: mock
      yield mock
      app.dependency_overrides.clear()
```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các tiêu chí sau:

- [ ] Bạn hiểu rõ nguyên lý hoạt động của `Depends()` và tại sao FastAPI không cần Container đăng ký phức tạp?
- [ ] Bạn sử dụng thành thạo cú pháp hiện đại `Annotated[T, Depends(...)]`?
- [ ] Bạn phân biệt rõ ràng 3 vòng đời: `use_cache=True` (Scoped), `lifespan` (Singleton), và `use_cache=False` (Transient)?
- [ ] Bạn nắm vững kỹ thuật giải phóng tài nguyên cuối request với `yield` và khối `finally:`?
- [ ] Bạn biết cách xây dựng cây phụ thuộc nhiều tầng (Database -> Repository -> Service)?
- [ ] Bạn biết cách gắn dependency ở các cấp độ: Parameter, Route, Router, và App level?
- [ ] Bạn thành thạo kỹ thuật Mocking dependency với `app.dependency_overrides` khi viết Unit Test?

---

## 📚 Đọc thêm

- [FastAPI Official Documentation – Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Official Documentation – Sub-dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/sub-dependencies/)
- [FastAPI Official Documentation – Dependencies in path operation decorators](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/)
- [FastAPI Official Documentation – Testing Dependencies with Overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Microsoft Learn – Dependency injection in ASP.NET Core](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/dependency-injection)

<!-- nav:bottom -->
---

[⬅️ Xử lý lỗi trong FastAPI](./07-error-handling.md) | [📚 Mục lục Junior](./README.md) | [Cấu trúc project & settings ➡️](./09-project-structure-settings.md)
<!-- /nav:bottom -->
