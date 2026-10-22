<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 10
<!-- /nav:top -->

# Logging & xử lý lỗi toàn cục

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 09: Phân trang, lọc & sắp xếp](./09-pagination-filtering.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Thấu hiểu sự khác biệt bản chất giữa Text Logging truyền thống và **Structured JSON Logging** hiện đại trong việc giám sát hệ thống phân tán (ELK Stack, Grafana Loki, Datadog).
- Sử dụng thành thạo **`contextvars.ContextVar`** để truyền vết **`request_id`** và danh tính người dùng xuyên suốt toàn bộ vòng đời của coroutine bất đồng bộ mà không cần truyền thủ công qua từng hàm.
- Nắm vững giải pháp thay thế chuẩn cho `AsyncLocal<T>` và Serilog `LogContext` trong hệ sinh thái Python.
- Xây dựng tầng **Global Exception Handling** đạt chuẩn bảo mật doanh nghiệp: Che giấu 100% Stack Trace nội bộ đối với người dùng cuối, trả về cấu trúc lỗi chuẩn hóa quốc tế **RFC 9457 Problem Details**.
- Phân tầng xử lý ngoại lệ theo đúng nguyên lý Clean Architecture: Tách biệt rạch ròi giữa Lỗi xác thực Pydantic (`RequestValidationError`), Ngoại lệ miền nghiệp vụ (`AppException`), và Lỗi sập hệ thống không lường trước (`Unhandled Exception 500`).

---

## 🔁 So sánh với C# / ASP.NET

Đối với lập trình viên C#, Serilog và cơ chế Exception Handling Middleware là chuẩn mực công nghiệp để thu thập log có cấu trúc và xử lý lỗi. Dưới đây là bảng đối chiếu chi tiết:

| Khái niệm / Kỹ thuật | ASP.NET Core & Serilog (C#) | FastAPI & Python 3.12+ |
|---|---|---|
| **Structured Logging** | Serilog với JSON Formatter (`CompactJsonFormatter`) | `structlog` hoặc `logging.dictConfig` với JSON Formatter |
| **Lưu ngữ cảnh Async** | `System.Threading.AsyncLocal<T>` | `contextvars.ContextVar[T]` |
| **Gắn thuộc tính vết (Correlation Scope)** | `using (LogContext.PushProperty("RequestId", id))` hoặc `ILogger.BeginScope` | Gán giá trị vào `ContextVar` trong Middleware |
| **Chuẩn hóa lỗi RFC 9457** | `builder.Services.AddProblemDetails()` (Tích hợp từ .NET 7+) | Tự định nghĩa Pydantic schema `ProblemDetail` và `JSONResponse` |
| **Bắt ngoại lệ toàn cục** | `app.UseExceptionHandler(...)` hoặc Custom Exception Middleware | `@app.exception_handler(Exception)` |
| **Lỗi xác thực Model** | `ActionFilterAttribute` bắt `ModelState.IsValid == false` | `@app.exception_handler(RequestValidationError)` |
| **Ngoại lệ miền nghiệp vụ (Domain Exceptions)** | Class kế thừa `System.Exception` (ví dụ `NotFoundException`) | Class kế thừa `AppException` (Python `Exception`) |

---

## 📖 Lý thuyết

### 1. Tại sao Structured JSON Logging là bắt buộc ở Production?

Trong môi trường phát triển (Local Development), log dạng văn bản tự do (Plain Text) rất dễ đọc bằng mắt thường:
```text
2026-10-22 14:30:15 [INFO] User 42 created task 101 in 0.045s
```

Tuy nhiên, khi ứng dụng phục vụ hàng triệu người dùng trên các cụm máy chủ Docker / Kubernetes, log dạng văn bản trở thành thảm họa:
- Không thể lọc chính xác: Muốn tìm tất cả các request của `User 42` có thời gian xử lý `> 0.5s` đòi hỏi phải viết Regex rất phức tạp và chậm chạp.
- Khi lập trình viên thay đổi định dạng câu văn log, toàn bộ các script parser/alert của đội DevOps sẽ lập tức bị gãy.

**Structured JSON Logging** giải quyết triệt để vấn đề này bằng cách xuất ra từng dòng log là một đối tượng JSON hợp lệ:
```json
{"timestamp": "2026-10-22T14:30:15.123Z", "level": "info", "event": "task_created", "user_id": 42, "task_id": 101, "duration_ms": 45.2, "request_id": "c1f7a2d3-8e9b-4a5c-b1d2-e3f4a5b6c7d8"}
```

Các công cụ tập trung log như **Elasticsearch (ELK), Datadog, AWS CloudWatch, Grafana Loki** sẽ tự động bóc tách từng trường dữ liệu, cho phép bạn truy vấn, lọc chỉ mục và vẽ biểu đồ giám sát với tốc độ tức thì.

### 2. Quản lý ngữ cảnh Async với `contextvars.ContextVar`

Trong các ứng dụng đa luồng truyền thống của Python, ta dùng `threading.local()` để lưu biến theo từng luồng. 
Nhưng trong FastAPI / `asyncio`, hàng nghìn request bất đồng bộ **cùng chia sẻ chung một luồng OS duy nhất (Single Thread)**. Nếu dùng `threading.local()`, `request_id` của Request A sẽ bị ghi đè hoặc lộ sang Request B!

Để giải quyết vấn đề này, Python 3.7 giới thiệu mô-đun chuẩn **`contextvars`**:
- `ContextVar` hoạt động giống như `AsyncLocal<T>` trong .NET: Mỗi coroutine khi được sinh ra sẽ kế thừa ngữ cảnh từ coroutine cha và sở hữu không gian lưu trữ độc lập. Khi Event Loop chuyển đổi qua lại giữa các coroutine, ngữ cảnh của `ContextVar` được tự động chuyển đổi theo.

```text
┌────────────────────────────────────────────────────────────────────────┐
│             CƠ CHẾ BẢO LƯU CONTEXT TRONG EVENT LOOP                    │
│                                                                        │
│   Request A (request_id="REQ-A")        Request B (request_id="REQ-B") │
│           │                                     │                      │
│           ├──> contextvars.set("REQ-A")          ├──> contextvars.set("REQ-B")
│           │                                     │                      │
│           ▼ (await DB query)                    ▼ (await Redis get)    │
│    [Event Loop tạm dừng Task A]          [Event Loop chuyển sang Task B]│
│           │                                     │                      │
│           ▼                                     ▼                      │
│    log.info("Query done")                log.info("Cache hit")         │
│    -> Tự động kèm "REQ-A"               -> Tự động kèm "REQ-B"        │
│                                                                        │
│    ✨ Hoàn toàn biệt lập, không bao giờ bị lẫn lộn giữa các Request!   │
└────────────────────────────────────────────────────────────────────────┘
```

### 3. Chuẩn hóa lỗi RFC 9457 Problem Details

Theo khuyến nghị của IETF trong **RFC 9457 (thay thế RFC 7807)**, một API chuyên nghiệp phải trả về lỗi với định dạng JSON thống nhất có `Content-Type: application/problem+json` gồm các trường tiêu chuẩn:

- **`type`**: URI định danh phân loại lỗi (giúp client hoặc lập trình viên đọc tài liệu giải thích lỗi).
- **`title`**: Tóm tắt ngắn gọn loại lỗi bằng tiếng Anh (ví dụ "Resource Not Found").
- **`status`**: Mã trạng thái HTTP (ví dụ `404`).
- **`detail`**: Thông báo chi tiết, dễ hiểu về nguyên nhân cụ thể của lần gọi lỗi này.
- **`instance`**: Đường dẫn endpoint đã xảy ra lỗi (ví dụ `/api/v1/tasks/99`).
- **Phần mở rộng (Extensions)**: Các trường bổ sung hữu ích, đặc biệt là **`request_id`**.

### 4. Phân tầng kiến trúc Exception: 3 cấp độ

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   KIẾN TRÚC PHÂN TẦNG XỬ LÝ NGOẠI LỆ                   │
│                                                                        │
│  [HTTP Request]                                                        │
│        │                                                               │
│        ├── 1. RequestValidationError (FastAPI / Pydantic)              │
│        │      -> Sai kiểu dữ liệu, thiếu trường bắt buộc              │
│        │      -> Trả về HTTP 422 Problem Details                       │
│        │                                                               │
│        ├── 2. AppException (Domain Exceptions từ Service Layer)        │
│        │      -> NotFoundError, DuplicateNameError, BusinessRuleViolate│
│        │      -> Trả về HTTP 400, 404, 409 Problem Details             │
│        │                                                               │
│        └── 3. Unhandled Exception (Cơ sở dữ liệu sập, Null pointer)    │
│               -> Log TOÀN BỘ Stack Trace và Metadata vào hệ thống     │
│               -> Trả về HTTP 500 "Internal Server Error"               │
│               -> Kèm `request_id` để khách hàng liên hệ CSKH          │
│               -> 🔒 TUYỆT ĐỐI KHÔNG để lộ Stack Trace ra ngoài!        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Ví dụ thực hành

Dưới đây là một hệ thống Logging có cấu trúc kết hợp bộ xử lý ngoại lệ toàn cục hoàn chỉnh.

### 1. Quản lý Ngữ cảnh: `app/core/context.py`

```python
import contextvars

# ContextVar lưu trữ request_id cho mỗi async task
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="unknown"
)
```

### 2. Cấu hình Structured Logger: `app/core/logging.py`

```python
import json
import logging
import sys
from datetime import datetime, timezone
from app.core.context import request_id_ctx


class JSONFormatter(logging.Formatter):
    """Formatter biến đổi log record thành dòng JSON chuẩn máy đọc."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }

        # Bổ sung thông tin vị trí file nếu là cảnh báo hoặc lỗi
        if record.levelno >= logging.WARNING:
            log_obj["caller"] = f"{record.filename}:{record.lineno}"

        # Bổ sung stack trace nếu có ngoại lệ
        if record.exc_info and record.exc_info[1]:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Thu thập các trường dữ liệu ngữ cảnh truyền qua tham số extra={...}
        standard_attrs = {
            "args", "asctime", "created", "exc_info", "exc_text", "filename",
            "funcName", "levelname", "levelno", "lineno", "module", "msecs",
            "message", "msg", "name", "pathname", "process", "processName",
            "relativeCreated", "stack_info", "thread", "threadName",
        }
        for key, val in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_obj[key] = val

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

    # Tắt log thừa từ thư viện bên thứ ba
    logging.getLogger("uvicorn.access").disabled = True
```

### 3. Định nghĩa Domain Exceptions: `app/core/exceptions.py`

```python
class AppException(Exception):
    """Ngoại lệ cơ sở cho toàn bộ lỗi nghiệp vụ của ứng dụng."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundException(AppException):

    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            message=f"Không tìm thấy tài nguyên '{resource}' với định danh: {identifier}",
            status_code=404,
        )


class ConflictException(AppException):

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=409)
```

### 4. Tích hợp Middleware và Exception Handlers: `app/main.py`

```python
import logging
import uuid
from collections.abc import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.context import request_id_ctx
from app.core.exceptions import AppException, NotFoundException
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger("taskflow.api")

app = FastAPI(title="TaskFlow Enterprise API")


# Middleware gán Request ID vào ContextVar
class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: Callable[..., Response]
    ) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)


app.add_middleware(RequestContextMiddleware)


# 1. Handler cho Lỗi xác thực Pydantic (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    logger.warning("Lỗi validation dữ liệu đầu vào", extra={"errors": errors})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        media_type="application/problem+json",
        content={
            "type": "https://errors.taskflow.dev/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": "Dữ liệu gửi lên không đúng định dạng.",
            "instance": request.url.path,
            "request_id": request_id_ctx.get(),
            "invalid_params": errors,
        },
    )


# 2. Handler cho Ngoại lệ Nghiệp vụ Miền (AppException: 400, 404, 409...)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.info(f"Ngoại lệ nghiệp vụ: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": "https://errors.taskflow.dev/business-error",
            "title": "Business Rule Violation",
            "status": exc.status_code,
            "detail": exc.message,
            "instance": request.url.path,
            "request_id": request_id_ctx.get(),
        },
    )


# 3. Handler Toàn Cục cho Lỗi Hệ thống Không Mong Muốn (500)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = request_id_ctx.get()
    # Log đầy đủ stack trace vào stdout để kỹ sư xem xét
    logger.exception(
        f"Lỗi hệ thống nghiêm trọng chưa xử lý: {exc}",
        extra={"path": request.url.path, "method": request.method},
    )

    # Trả về mã lỗi an toàn cho người dùng, tuyệt đối KHÔNG lộ stack trace:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/problem+json",
        content={
            "type": "https://errors.taskflow.dev/internal-server-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Đã xảy ra lỗi hệ thống bất khả kháng. Vui lòng liên hệ hỗ trợ kèm theo mã request_id bên dưới.",
            "instance": request.url.path,
            "request_id": req_id,
        },
    )


# Endpoint thử nghiệm
@app.get("/api/v1/tasks/{task_id}")
async def get_task_by_id(task_id: int):
    if task_id == 999:
        raise NotFoundException(resource="Task", identifier=task_id)
    if task_id == 0:
        # Giả lập lỗi ném ra phép chia cho 0 ngoài ý muốn
        _ = 1 / 0
    return {"id": task_id, "title": "Hoàn thiện hệ thống Logging"}
```

---

## ⚠️ Lỗi thường gặp

### 1. Dùng `logger.error(exc)` thay vì `logger.exception(...)`

Khi bắt được ngoại lệ, nếu bạn chỉ gọi `logger.error(exc)` hoặc `logger.error(str(exc))`, Python chỉ ghi lại vỏn vẹn một dòng thông báo lỗi ngắn (ví dụ `'division by zero'`). Toàn bộ thông tin quý giá về file nào, dòng lệnh nào gây ra lỗi (**Stack Trace**) sẽ bị **mất sạch hoàn toàn**!

❌ **Sai lầm:**
```python
try:
    ...
except Exception as e:
    logger.error(f"Lỗi: {e}")  # Không có Stack Trace!
```

✅ **Giải pháp:** Luôn sử dụng `logger.exception(...)` (tự động bật `exc_info=True`):
```python
try:
    ...
except Exception as e:
    logger.exception("Đã xảy ra lỗi nghiêm trọng khi xử lý đơn hàng")
```

---

### 2. Để lộ Stack Trace nội bộ ra phản hồi HTTP ở Production

Nhiều lập trình viên mới chuyển từ môi trường dev lên production thường trả thẳng `str(traceback.format_exc())` về cho client để "tiện debug".

```text
┌────────────────────────────────────────────────────────────────────────┐
│             LỖ HỔNG BẢO MẬT: OWASP SECURITY MISCONFIGURATION           │
│                                                                        │
│  Client nhận được:                                                     │
│  "File '/app/internal/db.py', line 82, in connect                      │
│   password='SecretPassword123!', host='postgres-cluster-internal.local'│
│   OperationalError: connection refused"                                │
│                                                                        │
│  🚨 Kẻ tấn công ngay lập tức biết được:                                │
│  - Cấu trúc thư mục mã nguồn server                                    │
│  - Tên máy chủ database nội bộ                                         │
│  - Mật khẩu hoặc token lộ trong biến cục bộ!                           │
└────────────────────────────────────────────────────────────────────────┘
```

**Quy tắc bất di bất dịch:** Stack trace chỉ được phép xuất hiện trong Log nội bộ của Server, tuyệt đối **không bao giờ** xuất hiện trong HTTP response gửi cho Client!

---

### 3. Ném trực tiếp `HTTPException` trong Domain Service Layer

Nếu trong tầng Service hoặc Domain Model của bạn xuất hiện code:
```python
from fastapi import HTTPException


class TaskService:

    def get_task(self, task_id: int):
        task = self.repo.find_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Không tìm thấy task")
```

Điều này vi phạm nghiêm trọng nguyên lý phân tầng của Clean Architecture:
- Tầng Service bị gắn chặt (tightly coupled) vào framework Web `fastapi`.
- Bạn không thể tái sử dụng `TaskService` trong CLI script, Background Worker, hay gRPC server vì các môi trường đó không hiểu `HTTPException`.

✅ **Giải pháp:** Tầng Service chỉ ném các ngoại lệ nghiệp vụ thuần túy (`NotFoundException`, `BusinessRuleException`). Tầng API Router hoặc Global Exception Handler sẽ chịu trách nhiệm chuyển đổi ngoại lệ đó thành mã trạng thái HTTP tương ứng.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Hệ thống Domain Exceptions và Auto HTTP Status
Hãy mở rộng cây kế thừa ngoại lệ miền nghiệp vụ:
- `EntityNotFoundError` (mã HTTP 404)
- `DuplicateResourceError` (mã HTTP 409)
- `UnauthorizedAccessError` (mã HTTP 403)
- `InvalidOperationError` (mã HTTP 400)

Viết một Exception Handler chung cho lớp cha `AppException` có khả năng tự động đọc thuộc tính `status_code` của từng lớp con để trả về mã lỗi HTTP và chi tiết RFC 9457 thích hợp.

<details>
<summary>💡 Gợi ý</summary>

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.context import request_id_ctx


class AppException(Exception):

    def __init__(
        self,
        detail: str,
        status_code: int = 400,
        title: str = "Business Rule Error",
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.title = title


class EntityNotFoundError(AppException):

    def __init__(self, entity_name: str, entity_id: object) -> None:
        super().__init__(
            detail=f"{entity_name} với mã {entity_id} không tồn tại.",
            status_code=404,
            title="Entity Not Found",
        )


class DuplicateResourceError(AppException):

    def __init__(self, message: str) -> None:
        super().__init__(
            detail=message, status_code=409, title="Resource Conflict"
        )


async def generic_app_exception_handler(
    request: Request, exc: AppException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": f"https://errors.taskflow.dev/{exc.title.lower().replace(' ', '-')}",
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
            "request_id": request_id_ctx.get(),
        },
    )
```
</details>

---

### Bài tập 2: Lưu trữ `user_id` vào `ContextVar` và tự động gắn vào Structured Log
Mở rộng hệ thống Logging sao cho:
1. Khi request đi qua tầng Authentication (sau khi decode JWT thành công), `user_id` được ghi vào một `ContextVar` tên là `current_user_id_ctx`.
2. Lớp `JSONFormatter` tự động kiểm tra: nếu `current_user_id_ctx` có giá trị thì tự động thêm trường `"user_id": 123` vào mọi dòng log được ghi ra trong suốt request đó.

<details>
<summary>💡 Gợi ý</summary>

```python
import contextvars
import json
import logging

current_user_id_ctx: contextvars.ContextVar[int | None] = (
    contextvars.ContextVar("current_user_id", default=None)
)


class EnrichedJSONFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "user_id": current_user_id_ctx.get(),
        }
        return json.dumps(log_data)
```
</details>

---

### Bài tập 3: Viết Unit Test kiểm tra hợp đồng lỗi RFC 9457
Sử dụng `httpx.AsyncClient` để viết test case kiểm tra:
1. Khi gọi một endpoint cố tình ném lỗi 500, API phải trả về `status_code == 500`.
2. Header `Content-Type` của response phải là `application/problem+json`.
3. Body của response phải có đủ các trường: `type`, `title`, `status`, `detail`, `instance`, và `request_id`.
4. Body phản hồi tuyệt đối **không** được chứa các từ khóa nhạy cảm như `"Traceback"`, `"File"`, `"line"`.

<details>
<summary>💡 Gợi ý</summary>

```python
from httpx import AsyncClient


async def test_unhandled_error_returns_clean_problem_details(
    client: AsyncClient,
) -> None:
    # Gọi endpoint cố tình ném lỗi chia cho 0
    response = await client.get("/api/v1/tasks/0")

    assert response.status_code == 500
    assert "application/problem+json" in response.headers["content-type"]

    data = response.json()
    assert data["status"] == 500
    assert data["title"] == "Internal Server Error"
    assert "request_id" in data
    assert len(data["request_id"]) > 0

    # Đảm bảo không có dấu hiệu lộ stack trace ra ngoài:
    raw_text = response.text
    assert "Traceback" not in raw_text
    assert "ZeroDivisionError" not in raw_text
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được lợi ích sống còn của Structured JSON Logging so với plain text log khi vận hành trên Kubernetes/Cloud.
- [ ] Tôi biết cách sử dụng `contextvars.ContextVar` để chia sẻ `request_id` an toàn giữa các hàm async coroutine.
- [ ] Tôi hiểu rõ các trường thông tin tiêu chuẩn của đặc tả lỗi RFC 9457 Problem Details.
- [ ] Tôi nắm vững nguyên tắc bảo mật: Không bao giờ để lộ stack trace nội bộ ra client trong phản hồi lỗi 500.
- [ ] Tôi biết cách tách biệt ngoại lệ nghiệp vụ miền (Domain Exceptions) khỏi ngoại lệ của framework Web HTTP.

---

## 📚 Đọc thêm

- [RFC 9457 – Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [Python Documentation – contextvars Module](https://docs.python.org/3/library/contextvars.html)
- [FastAPI – Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Structlog – Structured Logging for Python](https://www.structlog.org/en/stable/)
- [Tiếp theo: Bài 11 – Docker & docker-compose](./11-docker-compose.md)

<!-- nav:bottom -->
---

[⬅️ Phân trang, lọc & sắp xếp](./09-pagination-filtering.md) | [📚 Mục lục Middle](./README.md) | [Docker & docker-compose ➡️](./11-docker-compose.md)
<!-- /nav:bottom -->
