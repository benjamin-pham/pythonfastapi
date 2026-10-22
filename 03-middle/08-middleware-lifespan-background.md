<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 08
<!-- /nav:top -->

# Middleware, lifespan & background tasks

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 07: Testing FastAPI](./07-testing-fastapi.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Làm chủ cơ chế quản lý vòng đời ứng dụng hiện đại **`lifespan`** bằng `@asynccontextmanager`, thay thế dứt điểm các decorator cũ đã bị deprecated (`@app.on_event("startup")` / `@app.on_event("shutdown")`).
- Khởi tạo và giải phóng an toàn các tài nguyên nặng (Database Connection Pool, HTTP Client session, Redis connection) xuyên suốt vòng đời ứng dụng.
- Cấu hình chuẩn xác **`CORSMiddleware`** để bảo vệ API và cho phép Single Page Applications (React, Vue, Mobile apps) gọi API an toàn.
- Xây dựng **Custom Middleware** đo thời gian xử lý request (`X-Process-Time`) và tự động sinh mã vết truy vết **`X-Request-ID`**.
- Phân biệt rạch ròi sự khác nhau giữa **`BaseHTTPMiddleware`** và **Pure ASGI Middleware** về mặt hiệu năng và độ ổn định khi xử lý Streaming.
- Khai thác tính năng **`BackgroundTasks`** của FastAPI cho các tác vụ phi đồng bộ nhẹ trong tiến trình (gửi email, ghi audit log) và nắm rõ giới hạn kiến trúc khi nào cần chuyển sang Distributed Task Queue chuyên dụng.

---

## 🔁 So sánh với C# / ASP.NET

Đối với lập trình viên ASP.NET Core, Pipeline Middleware và Hosted Services là những thành phần cốt lõi của kiến trúc ứng dụng Web. Dưới đây là bảng đối chiếu chi tiết:

| Khái niệm / Thành phần | ASP.NET Core (C#) | FastAPI (Python 3.12+) |
|---|---|---|
| **Vòng đời khởi tạo & kết thúc (Lifecycle)** | `IHostedService` hoặc `IHostApplicationLifetime` (`ApplicationStarted`, `ApplicationStopping`) | `@asynccontextmanager async def lifespan(app: FastAPI): yield` |
| **Quản lý Connection Pool** | `services.AddDbContextPool<AppDbContext>()`, `services.AddHttpClient()` | Khởi tạo trong `lifespan`, lưu vào `app.state` hoặc module singleton |
| **Pipeline Middleware** | `app.UseMiddleware<CustomMiddleware>()` hoặc `app.Use(async (context, next) => ...)` | `app.add_middleware(BaseHTTPMiddleware, dispatch=...)` hoặc class kế thừa |
| **Cấu hình CORS** | `builder.Services.AddCors(...)` kết hợp `app.UseCors(...)` | `from fastapi.middleware.cors import CORSMiddleware` + `app.add_middleware(CORSMiddleware, ...)` |
| **Đính kèm Header phản hồi** | `context.Response.Headers.Append("X-Process-Time", elapsed)` | `response.headers["X-Process-Time"] = f"{elapsed:.4f}s"` |
| **Tác vụ nền nhẹ trong tiến trình** | `IHostedService`, `BackgroundService`, `QueueBackgroundWorkItem` | `fastapi.BackgroundTasks` (chạy sau khi HTTP response đã trả về) |
| **Hàng đợi tác vụ phân tán (Distributed Queue)** | Hangfire, MassTransit, Quartz.NET | Celery, ARQ, Redis Queue (Học ở Level Senior) |

---

## 📖 Lý thuyết

### 1. Quản lý vòng đời hiện đại với `@asynccontextmanager` (`lifespan`)

Trước FastAPI 0.93.0, lập trình viên thường dùng:
```python
# ❌ CÚ PHÁP CŨ - ĐÃ BỊ DEPRECATED:
@app.on_event("startup")
async def startup_event(): ...


@app.on_event("shutdown")
async def shutdown_event(): ...
```

Cú pháp cũ có nhiều nhược điểm: xử lý lỗi tách rời, không có ngữ cảnh `try ... finally` đồng nhất, và khó chia sẻ trạng thái dùng chung.

Tiêu chuẩn hiện đại của ASGI và Starlette/FastAPI là sử dụng **`lifespan` handler** dựa trên decorator `@asynccontextmanager` từ thư viện chuẩn `contextlib`:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   VÒNG ĐỜI ỨNG DỤNG (LIFESPAN LIFECYCLE)               │
│                                                                        │
│   Uvicorn khởi động tiến trình                                        │
│          │                                                             │
│          ▼                                                             │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ [STARTUP]: Trước từ khóa `yield`                              │    │
│   │ - Khởi tạo Database Connection Pool (SQLAlchemy Engine)      │    │
│   │ - Mở httpx.AsyncClient tái sử dụng socket                    │    │
│   │ - Kiểm tra kết nối ngoại vi (Ping DB, Redis)                 │    │
│   └──────────────────────────────────────────────────────────────┘    │
│          │                                                             │
│          ├───────────────────────► [Ứng dụng SẴN SÀNG phục vụ requests]│
│          │                                                             │
│          ▼ (Nhận tín hiệu SIGTERM / SIGINT từ OS / Docker)             │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ [SHUTDOWN]: Sau từ khóa `yield`                               │    │
│   │ - Đóng HTTP Client connections                               │    │
│   │ - Đóng và giải phóng Database Engine (`engine.dispose()`)    │    │
│   │ - Đợi các kết nối dở dang hoàn tất                           │    │
│   └──────────────────────────────────────────────────────────────┘    │
│          │                                                             │
│          ▼                                                             │
│   Tiến trình kết thúc an toàn (Graceful Shutdown)                      │
└────────────────────────────────────────────────────────────────────────┘
```

Đoạn code chuẩn mực:

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Startup phase: Khởi tạo tài nguyên
    engine = create_async_engine("postgresql+asyncpg://...")
    http_client = httpx.AsyncClient(timeout=10.0)

    # Gắn vào app.state để truy cập từ bất kỳ route nào
    app.state.db_engine = engine
    app.state.http_client = http_client

    print("🚀 Ứng dụng đã khởi động thành công!")
    yield  # Ứng dụng chạy và lắng nghe các HTTP request tại đây

    # 2. Shutdown phase: Dọn dẹp tài nguyên
    await http_client.aclose()
    await engine.dispose()
    print("🛑 Ứng dụng đã dọn dẹp tài nguyên và tắt an toàn!")


app = FastAPI(lifespan=lifespan)
```

### 2. Cấu hình Cross-Origin Resource Sharing (CORS)

Khi bạn xây dựng Single Page Application (React chạy tại `http://localhost:3000`) gọi sang FastAPI Backend (chạy tại `http://localhost:8000`), trình duyệt sẽ chặn request do vi phạm **Same-Origin Policy** nếu server không trả về các header CORS phù hợp.

FastAPI cung cấp sẵn `CORSMiddleware`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://taskflow.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Danh sách domain được phép gọi API
    allow_credentials=True,  # Cho phép gửi Cookies, Authorization header
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

> ⚠️ **Quy tắc vàng bảo mật:** Tuyệt đối **không** dùng đồng thời `allow_origins=["*"]` và `allow_credentials=True`. Các trình duyệt hiện đại sẽ từ chối cấu hình này vì lý do bảo mật CSRF!

### 3. Custom Middleware: `BaseHTTPMiddleware` vs Pure ASGI

Middleware là đoạn code bao bọc quanh mỗi request đi vào và response đi ra:

```text
Request ────► [Middleware 1] ────► [Middleware 2] ────► [Endpoint Handler]
                                                               │
Response ◄─── [Middleware 1] ◄──── [Middleware 2] ◄────────────┘
```

#### Cách 1: Sử dụng `BaseHTTPMiddleware` (Dễ tiếp cận)
Thích hợp cho các nhu cầu đo đạc cơ bản:
```python
import time
import uuid
from collections.abc import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()


class ObservabilityMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: Callable[..., Response]
    ) -> Response:
        # Trước khi vào endpoint:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        # Thực thi endpoint handler:
        response = await call_next(request)

        # Sau khi endpoint trả kết quả:
        process_time = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response


app.add_middleware(ObservabilityMiddleware)
```

#### Cách 2: Pure ASGI Middleware (Hiệu năng cao nhất)
`BaseHTTPMiddleware` có một nhược điểm nổi tiếng trong cộng đồng Starlette: nó bọc response body vào một generator ngầm, có thể gây mất đồng bộ với `StreamingResponse` lớn hoặc làm tăng độ trễ dưới tải cao. Khi cần hiệu năng tối đa, ta dùng chuẩn ASGI thuần túy:

```python
import time
import uuid
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class PureASGIRequestIdMiddleware:

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                process_time = f"{time.perf_counter() - start_time:.4f}s"
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                headers.append(
                    (b"x-process-time", process_time.encode("latin-1"))
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

### 4. Xử lý tác vụ nền trong tiến trình: `BackgroundTasks`

Trong các API thực tế, người dùng không nên phải chờ đợi các tác vụ phụ trợ (ví dụ: gửi email chào mừng, gửi thông báo Slack, ghi nhật ký kiểm toán).

FastAPI tích hợp lớp **`BackgroundTasks`**:
- **Cơ chế**: Endpoint trả phản hồi HTTP về cho client ngay lập tức, sau đó Event Loop của FastAPI tiếp tục thực thi các hàm được đăng ký trong `BackgroundTasks`.
- **Phạm vi phù hợp**: Các tác vụ in-process nhanh, không yêu cầu độ tin cậy tuyệt đối (email thông báo, ghi audit log, update cache đơn giản).
- **Giới hạn**: Nếu server bị tắt, crash hoặc OOM, các background tasks đang nằm trong RAM sẽ bị **mất vĩnh viễn**. Nếu cần đảm bảo 100% không mất job, retry tự động hoặc xử lý nặng (render video, xuất file Excel 1 triệu dòng), bắt buộc phải sử dụng Message Broker + Distributed Task Queue (RabbitMQ / Redis + Celery / ARQ).

---

## 💻 Ví dụ thực hành

Dưới đây là mã nguồn tích hợp hoàn chỉnh: Lifespan + CORS + Custom Timing Middleware + BackgroundTasks.

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import time
import uuid
from fastapi import BackgroundTasks, Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from starlette.middleware.base import BaseHTTPMiddleware


# 1. Lifespan quản lý tài nguyên
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("▶️ [LIFESPAN] Khởi tạo kết nối dịch vụ...")
    app.state.is_ready = True
    yield
    print("⏹️ [LIFESPAN] Giải phóng kết nối dịch vụ...")
    app.state.is_ready = False


app = FastAPI(title="TaskFlow Ops API", lifespan=lifespan)

# 2. Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. Custom Middleware gắn Request ID và đo thời gian
class TimingAndRequestIdMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: object
    ) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = req_id
        start_time = time.perf_counter()

        response = await call_next(request)  # type: ignore[operator]

        duration = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = f"{duration:.4f}s"
        return response


app.add_middleware(TimingAndRequestIdMiddleware)


# 4. Tác vụ Background Tasks
def send_welcome_email(email: str, username: str) -> None:
    # Mô phỏng gửi email (I/O)
    time.sleep(0.5)
    print(f"📧 [EMAIL SENT] Gửi email chào mừng tới {username} <{email}>")


def log_audit_trail(action: str, target: str, request_id: str) -> None:
    print(f"📝 [AUDIT LOG] ReqID={request_id} | Hành động={action} trên {target}")


# 5. Schema và Route
class RegisterUserRequest(BaseModel):
    email: EmailStr
    username: str


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterUserRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> dict[str, str]:
    # Logic lưu user vào DB tại đây...
    user_id = "usr_12345"

    # Đăng ký các tác vụ chạy nền:
    background_tasks.add_task(
        send_welcome_email, email=payload.email, username=payload.username
    )
    background_tasks.add_task(
        log_audit_trail,
        action="USER_REGISTERED",
        target=user_id,
        request_id=request.state.request_id,
    )

    # Client nhận phản hồi ngay lập tức, không phải chờ gửi email:
    return {
        "message": "Đăng ký thành công!",
        "user_id": user_id,
    }
```

---

## ⚠️ Lỗi thường gặp

### 1. Dùng đồng thời `allow_origins=["*"]` và `allow_credentials=True`

**Hiện tượng:** Trình duyệt phía Frontend (React/Vue) ném lỗi:
`Access to fetch at '...' from origin '...' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' when the request's credentials mode is 'include'.`

❌ **Cấu hình sai:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # LỖI: Không được dùng wildcard khi cho phép credentials!
    allow_credentials=True,
)
```

✅ **Cấu hình chuẩn:**
Chỉ định rõ ràng danh sách tên miền cụ thể hoặc sử dụng `allow_origin_regex`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.taskflow.dev"],
    allow_credentials=True,
)
```

---

### 2. Dùng `BackgroundTasks` cho tác vụ tài chính hoặc tác vụ quá nặng

**Rủi ro nghiêm trọng:**
- Nếu bạn xử lý giao dịch trừ tiền ví điện tử hoặc chuyển đổi file video 4K bằng `BackgroundTasks`:
  - `BackgroundTasks` chạy trên worker tiến trình của FastAPI. Tác vụ nặng về CPU sẽ chiếm dụng tài nguyên và làm nghẽn tiến trình API.
  - Khi container Kubernetes scale down hoặc server restart, tác vụ đang chạy dở sẽ bị hủy ngang và không bao giờ được phục hồi lại.

✅ **Quy tắc:**
- `BackgroundTasks`: Dành cho tác vụ phụ trợ (gửi email thông báo, push notification, log kiểm toán).
- Tác vụ tài chính, đồng bộ dữ liệu quan trọng, render nặng: Bắt buộc dùng **Celery / ARQ / BullMQ** lưu trữ trạng thái tác vụ trên Redis / RabbitMQ có cơ chế Retry và ACK an toàn.

---

### 3. Tiếp tục sử dụng `@app.on_event("startup")`

Nhiều lập trình viên vẫn sao chép code cũ trên mạng sử dụng `@app.on_event`. 
Từ Starlette 0.28+, tính năng này đã chính thức bị đánh dấu là **deprecated** và sẽ bị gỡ bỏ trong tương lai. Luôn luôn sử dụng `lifespan` handler!

---

## ✍️ Bài tập thực hành

### Bài tập 1: Viết Middleware chặn IP (IP Blacklist Middleware)
Hãy viết một Custom Middleware kiểm tra `request.client.host`. Nếu địa chỉ IP nằm trong danh sách đen (`BLOCKED_IPS = {"192.168.1.100", "10.0.0.99"}`), lập tức trả về `HTTP 403 Forbidden` với định dạng JSON Problem Details mà không cho phép request đi tiếp vào endpoint.

<details>
<summary>💡 Gợi ý</summary>

```python
from collections.abc import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

BLOCKED_IPS = {"192.168.1.100", "10.0.0.99"}


class IPBlacklistMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: Callable[..., Response]
    ) -> Response:
        client_ip = request.client.host if request.client else ""
        if client_ip in BLOCKED_IPS:
            return JSONResponse(
                status_code=403,
                content={
                    "type": "https://errors.taskflow.dev/ip-blocked",
                    "title": "Access Denied",
                    "status": 403,
                    "detail": f"Địa chỉ IP {client_ip} đã bị chặn truy cập.",
                },
            )
        return await call_next(request)


app = FastAPI()
app.add_middleware(IPBlacklistMiddleware)
```
</details>

---

### Bài tập 2: Kiểm tra trạng thái Cơ sở dữ liệu trong Lifespan
Xây dựng một `lifespan` handler thực hiện:
1. Khi startup: Thực thi câu lệnh `SELECT 1` kiểm tra kết nối tới Database. Nếu thất bại sau 3 lần thử lại (retry), ném ngoại lệ ngăn ứng dụng khởi động (Fail-fast).
2. Khi shutdown: Gọi `await engine.dispose()` và in ra log thông báo giải phóng kết nối.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL)


@asynccontextmanager
async def database_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    max_retries = 3
    connected = False
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"✅ Kết nối cơ sở dữ liệu thành công (lần thử {attempt})")
            connected = True
            break
        except Exception as exc:
            print(
                f"⚠️ Lỗi kết nối DB lần {attempt}/{max_retries}: {exc}. Đang thử lại..."
            )
            await asyncio.sleep(1)

    if not connected:
        raise RuntimeError(
            "Không thể kết nối đến cơ sở dữ liệu sau 3 lần thử! Dừng ứng dụng."
        )

    yield

    await engine.dispose()
    print("🔒 Đã đóng toàn bộ pool kết nối cơ sở dữ liệu.")


app = FastAPI(lifespan=database_lifespan)
```
</details>

---

### Bài tập 3: Background Task ghi nhật ký thay đổi trạng thái Task (Audit Log)
Viết endpoint `PATCH /api/v1/tasks/{task_id}/status` nhận trạng thái mới (`status: TaskStatus`). Endpoint sử dụng `BackgroundTasks` để ghi lại lịch sử thay đổi vào file hoặc database:
- `task_id`: Mã công việc
- `old_status`: Trạng thái trước khi cập nhật
- `new_status`: Trạng thái sau khi cập nhật
- `changed_by`: ID người dùng thực hiện
- `timestamp`: Thời điểm thực hiện

<details>
<summary>💡 Gợi ý</summary>

```python
from datetime import datetime, timezone
from enum import StrEnum
from fastapi import BackgroundTasks, FastAPI, status
from pydantic import BaseModel


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class StatusUpdateRequest(BaseModel):
    new_status: TaskStatus


app = FastAPI()


async def write_audit_log(
    task_id: int,
    old_status: str,
    new_status: str,
    user_id: int,
    at: datetime,
) -> None:
    # Mô phỏng ghi log vào database audit table
    print(
        f"📝 [AUDIT] Task #{task_id}: {old_status} -> {new_status} bởi User #{user_id} lúc {at.isoformat()}"
    )


@app.patch("/api/v1/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    payload: StatusUpdateRequest,
    bg: BackgroundTasks,
) -> dict[str, str]:
    # Giả định lấy trạng thái cũ từ DB:
    current_status = TaskStatus.TODO
    current_user_id = 42

    # Đăng ký audit log chạy ngầm:
    bg.add_task(
        write_audit_log,
        task_id=task_id,
        old_status=current_status,
        new_status=payload.new_status,
        user_id=current_user_id,
        at=datetime.now(timezone.utc),
    )

    return {"message": f"Trạng thái đã chuyển sang {payload.new_status}"}
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách cấu hình vòng đời ứng dụng bằng `@asynccontextmanager async def lifespan(app: FastAPI)` và không còn dùng `@app.on_event`.
- [ ] Tôi hiểu cách cấu hình `CORSMiddleware` an toàn và lý do không thể dùng `allow_origins=["*"]` kèm `allow_credentials=True`.
- [ ] Tôi có thể tự viết Custom Middleware để đo thời gian phản hồi và inject `X-Request-ID`.
- [ ] Tôi phân biệt được ưu nhược điểm giữa `BaseHTTPMiddleware` và Pure ASGI Middleware.
- [ ] Tôi hiểu cơ chế hoạt động của `BackgroundTasks` và nhận thức được các trường hợp bắt buộc phải dùng Task Queue phân tán.

---

## 📚 Đọc thêm

- [FastAPI – Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [Starlette Middleware & ASGI Architecture](https://www.starlette.io/middleware/)
- [Mozilla Developer Network (MDN) – Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI – Background Tasks Guide](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Tiếp theo: Bài 09 – Phân trang, lọc & sắp xếp](./09-pagination-filtering.md)

<!-- nav:bottom -->
---

[⬅️ Testing FastAPI](./07-testing-fastapi.md) | [📚 Mục lục Middle](./README.md) | [Phân trang, lọc & sắp xếp ➡️](./09-pagination-filtering.md)
<!-- /nav:bottom -->
