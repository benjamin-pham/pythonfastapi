<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 07
<!-- /nav:top -->

# Xử lý lỗi trong FastAPI

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 06: Pydantic v2](./06-pydantic-v2.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Nắm vững cơ chế xử lý ngoại lệ nguyên bản trong FastAPI với **`HTTPException`** và hiểu rõ cấu trúc phản hồi lỗi **`422 Unprocessable Content`** do Pydantic sinh ra khi validation thất bại.
- Hiểu thấu đáo nguyên lý **Separation of Concerns (Phân tách trách nhiệm)** trong kiến trúc phần mềm: tách biệt hoàn toàn **Domain Exceptions** (ngoại lệ nghiệp vụ thuần túy) khỏi tầng giao thức Web/HTTP.
- Tự thiết kế hệ thống phân cấp Domain Exception chuyên nghiệp (`TaskNotFoundError`, `DuplicateProjectNameError`, `InvalidStateTransitionError`).
- Nắm vững đặc tả quốc tế **RFC 9457** (bản nâng cấp chuẩn mực của RFC 7807) về **Problem Details for HTTP APIs** (`type`, `title`, `status`, `detail`, `instance`).
- Đăng ký và làm chủ các bộ xử lý lỗi toàn cục với **`@app.exception_handler(...)`**.
- Chuẩn hóa toàn bộ cấu trúc lỗi của ứng dụng (từ validation 422, domain error 404/409, đến unhandled exception 500) về duy nhất một định dạng RFC 9457 nhất quán.

---

## 🔁 So sánh với C# / ASP.NET

Trong hệ sinh thái .NET, xử lý ngoại lệ và chuẩn hóa cấu trúc lỗi đã được Microsoft định hình rất rõ qua các phiên bản ASP.NET Core (đặc biệt từ .NET 7 và .NET 8 với giao diện `IExceptionHandler` và lớp `ProblemDetails`). Khi làm việc với FastAPI, bạn sẽ nhận thấy sự tương đồng đáng kinh ngạc trong tư duy thiết kế:

| Nghiệp vụ / Khái niệm | C# / ASP.NET Core (.NET 8) | Python / FastAPI |
|---|---|---|
| **Ném lỗi HTTP trực tiếp** | `throw new BadHttpRequestException(...)` hoặc `return Results.NotFound(...)` | `raise HTTPException(status_code=404, detail="...")` |
| **Ngoại lệ nghiệp vụ thuần túy** | Custom Exception: `public class EntityNotFoundException : Exception` | Custom Exception: `class TaskNotFoundError(Exception): pass` |
| **Định dạng lỗi chuẩn quốc tế** | `Microsoft.AspNetCore.Mvc.ProblemDetails` (RFC 7807 / RFC 9457) | Pydantic model `ProblemDetails` tự định nghĩa hoặc thư viện chuẩn |
| **Xử lý ngoại lệ toàn cục** | Middleware `app.UseExceptionHandler()` kết hợp `IExceptionHandler` | Decorator `@app.exception_handler(CustomException)` |
| **Lỗi Validation mặc định** | `ValidationProblemDetails` (tự động kích hoạt bởi `[ApiController]`) | `RequestValidationError` (mã lỗi 422 mặc định của FastAPI) |
| **Ghi đè phản hồi validation** | `services.Configure<ApiBehaviorOptions>(options => ...)` | `@app.exception_handler(RequestValidationError)` |
| **Xử lý lỗi chưa bắt (500)** | Pipeline Exception Handler ghi log và ẩn chi tiết nhạy cảm | `@app.exception_handler(Exception)` bắt toàn bộ lỗi unhandled |

---

## 📖 Lý thuyết

### 1. Cơ chế cơ bản: `fastapi.HTTPException`

FastAPI cung cấp sẵn lớp ngoại lệ `HTTPException` (được kế thừa và mở rộng từ Starlette). Khi muốn ngắt luồng xử lý và trả về mã lỗi HTTP cho client, bạn dùng lệnh `raise`:

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item ID phải là số nguyên dương!",
            headers={"X-Error-Code": "INVALID_ID"},
        )
    return {"item_id": item_id}
```

Mặc định, khi gặp `HTTPException`, FastAPI sẽ trả về một JSON body có dạng:
```json
{
  "detail": "Item ID phải là số nguyên dương!"
}
```

> [!WARNING]
> Luôn import `HTTPException` từ `fastapi` chứ **KHÔNG PHẢI** từ `starlette.exceptions`. Phiên bản của FastAPI cho phép bạn truyền bất kỳ kiểu dữ liệu nào vào tham số `detail` (dict, list, hoặc string), trong khi Starlette chỉ hỗ trợ string thuần.

### 2. Cấu trúc lỗi mặc định `422 Unprocessable Content`

Khi client gửi dữ liệu không đúng với khai báo Type Hint hoặc vi phạm các rule của Pydantic (ví dụ: gửi chữ vào trường số, chuỗi quá ngắn, thiếu trường bắt buộc), FastAPI sẽ tự động chặn request và trả về HTTP status `422`:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 3 characters",
      "input": "ab",
      "ctx": {
        "min_length": 3
      }
    }
  ]
}
```

- `loc`: Vị trí xảy ra lỗi (trong `body`, `query`, hay `path`).
- `msg`: Thông điệp mô tả lỗi do Pydantic sinh ra.
- `type`: Định danh loại lỗi validation.
- `input`: Giá trị đầu vào mà client đã gửi lên.

Mặc dù rất chi tiết cho lập trình viên, cấu trúc này là định dạng riêng của FastAPI và chưa tuân theo chuẩn REST API toàn cầu.

### 3. Nguyên tắc kiến trúc: Đừng để HTTP rò rỉ vào Domain Layer!

Một sai lầm kinh điển của các lập trình viên Junior là ném `HTTPException` ngay bên trong Repository hoặc Service:

```python
# ❌ SAI LẦM KIẾN TRÚC: Service bị trói chặt vào giao thức HTTP!
class TaskService:

    def get_task(self, task_id: int):
        task = self.repo.find_by_id(task_id)
        if not task:
            # Nguy hiểm: Nếu ngày mai bạn dùng service này cho CLI, Background Worker,
            # hoặc gRPC, bạn sẽ phải xử lý HTTPException của web framework!
            raise HTTPException(status_code=404, detail="Task not found")
        return task
```

####  Giải pháp chuẩn mực: Sử dụng Domain Exceptions

Domain Layer (Service & Repository) chỉ nên biết về nghiệp vụ, không được biết về HTTP. Hãy tạo các class ngoại lệ thuần Python:

```python
#  ĐÚNG: Ngoại lệ nghiệp vụ thuần túy (Domain Exception)
class DomainError(Exception):
    """Lớp cha cho mọi lỗi nghiệp vụ trong hệ thống."""


class TaskNotFoundError(DomainError):

    def __init__(self, task_id: int) -> None:
        super().__init__(f"Không tìm thấy công việc với ID: {task_id}")
        self.task_id = task_id


class DuplicateProjectNameError(DomainError):

    def __init__(self, name: str) -> None:
        super().__init__(f"Dự án với tên '{name}' đã tồn tại!")
        self.name = name
```

Khi Service phát hiện lỗi, nó chỉ cần `raise TaskNotFoundError(task_id)`. Tầng Router hoặc Global Exception Handler sẽ lắng nghe ngoại lệ này và chuyển thành HTTP Status 404 tương ứng!

### 4. Chuẩn hóa lỗi theo RFC 9457 (Problem Details for HTTP APIs)

**RFC 9457** (xuất bản năm 2023, thay thế RFC 7807) là tiêu chuẩn chính thức của IETF nhằm định nghĩa định dạng JSON chuẩn cho phản hồi lỗi của HTTP API. Định dạng này bao gồm các trường chính:

- **`type`** (URI reference): Đường dẫn định danh loại lỗi (ví dụ: `https://api.taskflow.dev/errors/not-found` hoặc `"about:blank"` nếu sử dụng ngữ nghĩa HTTP chuẩn).
- **`title`** (string): Tiêu đề ngắn gọn, dễ đọc về loại lỗi (ví dụ: `"Task Not Found"`).
- **`status`** (integer): Mã trạng thái HTTP (ví dụ: `404`, `409`, `422`).
- **`detail`** (string): Lời giải thích cụ thể cho lần phát sinh lỗi này.
- **`instance`** (URI reference): Đường dẫn URL cụ thể nơi lỗi vừa xảy ra (ví dụ: `/api/v1/tasks/123`).
- **Phần mở rộng tùy biến**: Ví dụ trường `invalid_params` chứa danh sách chi tiết các trường bị lỗi validation.

Header `Content-Type` chuẩn mực khi trả về Problem Details là:
`application/problem+json`.

### 5. Đăng ký Custom Exception Handler với `@app.exception_handler`

FastAPI cho phép bạn đăng ký hàm bắt ngoại lệ toàn cục. Bất cứ khi nào một ngoại lệ thuộc class đã đăng ký (hoặc lớp con của nó) được ném ra từ bất kỳ đâu trong quá trình xử lý request, FastAPI sẽ chuyển quyền kiểm soát cho handler đó:

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError
) -> JSONResponse:
    problem = {
        "type": "https://errors.taskflow.dev/task-not-found",
        "title": "Task Not Found",
        "status": status.HTTP_404_NOT_FOUND,
        "detail": str(exc),
        "instance": str(request.url.path),
    }
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=problem,
        media_type="application/problem+json",
    )
```

---

## 💻 Ví dụ thực hành

Dưới đây là một hệ thống hoàn chỉnh kết hợp: Pydantic Schema cho RFC 9457 Problem Details, Hệ thống Domain Exceptions, Custom Handler cho `RequestValidationError` (422), và Global Handler cho lỗi hệ thống không lường trước (500):

```python
from typing import Annotated, Any
from fastapi import FastAPI, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# 1. Định nghĩa Schema chuẩn RFC 9457 Problem Details
# ==============================================================================
class InvalidParam(BaseModel):
    name: str = Field(description="Tên tham số hoặc trường bị lỗi")
    reason: str = Field(description="Lý do không hợp lệ")


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = Field(
        default="about:blank",
        description="URI định danh loại lỗi",
    )
    title: str = Field(description="Tiêu đề ngắn gọn của lỗi")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Mô tả chi tiết nguyên nhân phát sinh lỗi")
    instance: str = Field(description="URI nơi xảy ra lỗi")
    invalid_params: list[InvalidParam] | None = Field(
        default=None,
        description="Chi tiết các trường vi phạm validation (nếu có)",
    )


# ==============================================================================
# 2. Hệ thống Domain Exceptions (Không phụ thuộc vào FastAPI)
# ==============================================================================
class DomainException(Exception):
    """Gốc của mọi ngoại lệ nghiệp vụ."""


class TaskNotFoundError(DomainException):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"Công việc với ID {task_id} không tồn tại trong hệ thống.")
        self.task_id = task_id


class DuplicateProjectNameError(DomainException):
    def __init__(self, name: str) -> None:
        super().__init__(f"Dự án với tên '{name}' đã tồn tại.")
        self.name = name


# ==============================================================================
# 3. Khởi tạo ứng dụng và Đăng ký Exception Handlers
# ==============================================================================
app = FastAPI(title="TaskFlow RFC 9457 Error Handling API")


# Handler cho Domain Exception: TaskNotFoundError -> 404
@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError
) -> JSONResponse:
    problem = ProblemDetails(
        type="https://errors.taskflow.dev/task-not-found",
        title="Resource Not Found",
        status=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
        instance=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


# Handler cho Domain Exception: DuplicateProjectNameError -> 409 Conflict
@app.exception_handler(DuplicateProjectNameError)
async def duplicate_project_handler(
    request: Request, exc: DuplicateProjectNameError
) -> JSONResponse:
    problem = ProblemDetails(
        type="https://errors.taskflow.dev/conflict",
        title="Resource Conflict",
        status=status.HTTP_409_CONFLICT,
        detail=str(exc),
        instance=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


# Handler cho RequestValidationError -> Chuẩn hóa 422 về RFC 9457
@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    invalid_params: list[InvalidParam] = []
    for error in exc.errors():
        loc_str = " -> ".join(str(loc) for loc in error["loc"])
        invalid_params.append(
            InvalidParam(name=loc_str, reason=error["msg"])
        )

    problem = ProblemDetails(
        type="https://errors.taskflow.dev/validation-error",
        title="Validation Failed",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Dữ liệu gửi lên không vượt qua các quy tắc kiểm tra hợp lệ.",
        instance=request.url.path,
        invalid_params=invalid_params,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


# Handler cho Mọi ngoại lệ chưa được xử lý -> 500 Internal Server Error
@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    # Ở môi trường production, bạn sẽ ghi log đầy đủ stack trace vào CloudWatch / ELK tại đây.
    problem = ProblemDetails(
        type="https://errors.taskflow.dev/internal-error",
        title="Internal Server Error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Đã xảy ra sự cố nội bộ trong hệ thống. Vui lòng thử lại sau.",
        instance=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


# ==============================================================================
# 4. Các Endpoints kiểm thử
# ==============================================================================
class CreateProjectPayload(BaseModel):
    name: str = Field(min_length=3, max_length=50)


existing_projects = {"Backend Core", "Mobile App"}


@app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: Annotated[int, Path(ge=1)]) -> dict[str, Any]:
    # Giả lập service ném domain exception
    if task_id == 999:
        raise TaskNotFoundError(task_id)
    return {"id": task_id, "title": "Công việc mẫu"}


@app.post("/api/v1/projects", status_code=status.HTTP_201_CREATED)
def create_project(payload: CreateProjectPayload) -> dict[str, str]:
    if payload.name in existing_projects:
        raise DuplicateProjectNameError(payload.name)
    existing_projects.add(payload.name)
    return {"message": "Tạo dự án thành công", "name": payload.name}


@app.get("/api/v1/crash")
def simulate_crash() -> None:
    # Cố tình gây lỗi chia cho 0 để kiểm tra handler 500
    _ = 1 / 0
```

---

## ⚠️ Lỗi thường gặp

### 1. Ném `HTTPException` sâu trong tầng Repository hoặc Service
Đây là anti-pattern nghiêm trọng nhất. Tầng Domain bị ô nhiễm bởi các khái niệm của Web Framework. Luôn ném Domain Exception thuần túy và để tầng ngoài chuyển đổi.

### 2. Định dạng lỗi không nhất quán (Inconsistent Error Schema)
Một số endpoint trả về `{"error": "Không tìm thấy"}`, chỗ khác trả về `{"message": "Lỗi rồi"}`, chỗ khác lại trả về `{"detail": "..."}`. Điều này gây khó khăn cực lớn cho đội ngũ Frontend và Mobile khi phải viết hàng chục câu lệnh `if-else` chỉ để hiển thị thông báo lỗi. Luôn áp dụng chuẩn RFC 9457 xuyên suốt toàn hệ thống!

### 3. Để lộ chi tiết nhạy cảm trong phản hồi lỗi 500
Trong môi trường phát triển, việc nhìn thấy toàn bộ Python Stack Trace là tiện lợi. Nhưng khi lên Production, việc trả về thông tin chi tiết của `exc` có thể để lộ thông tin nhạy cảm (tên bảng trong cơ sở dữ liệu, câu lệnh SQL truy vấn thất bại, mật khẩu trong chuỗi kết nối).
> [!CAUTION]
> Trong handler bắt `Exception`, chỉ trả về thông điệp thân thiện chung chung cho client. Toàn bộ thông tin chi tiết và stack trace phải được đẩy an toàn vào hệ thống logging tập trung!

### 4. Quên chỉ định `media_type="application/problem+json"`
Theo khuyến nghị của RFC 9457, header phản hồi phải là `application/problem+json` để các HTTP client hiện đại nhận diện được ngay đây là một Problem Details payload.

---

## ✍️ Bài tập thực hành

### Bài 1: Domain Exception cho Nghiệp vụ Số Dư Tài Khoản
Tạo ứng dụng ví điện tử với:
1. Domain Exception `InsufficientBalanceError(current_balance: float, required_amount: float)`.
2. Đăng ký exception handler trả về Problem Details chuẩn RFC 9457 với status `400 Bad Request`, `title="Insufficient Balance"`, và `detail="Số dư hiện tại (X đ) không đủ để thực hiện giao dịch (cần Y đ)"`.
3. Viết endpoint `POST /api/v1/wallet/withdraw` nhận số tiền cần rút và kiểm tra với số dư in-memory hiện có.

<details>
<summary>💡 Gợi ý</summary>

- Tạo class `InsufficientBalanceError(DomainException)`.
- Trong exception handler, định dạng chuỗi `detail` sử dụng `exc.current_balance` và `exc.required_amount`.
</details>

---

### Bài 2: Custom Validation Handler với Trường Bổ Sung
Viết một custom exception handler cho `RequestValidationError`:
- Chuẩn hóa đầu ra theo RFC 9457.
- Bổ sung trường tùy chỉnh `request_id` (được đọc từ header `X-Request-ID` nếu có, hoặc sinh ngẫu nhiên bằng `uuid.uuid4()`) để hỗ trợ tracing lỗi giữa client và server.

<details>
<summary>💡 Gợi ý</summary>

- Đọc header: `req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))`.
- Bổ sung `request_id` vào dict trả về của ProblemDetails.
</details>

---

### Bài 3: Bắt và Ánh xạ Ngoại lệ Toàn cục Cơ Sở Dữ Liệu
Giả lập một exception của database layer `DatabaseIntegrityError(table: str, constraint: str)`.
- Viết một exception handler bắt `DatabaseIntegrityError` và ánh xạ thành mã HTTP `409 Conflict` với thông tin chi tiết về ràng buộc bị vi phạm.
- Viết endpoint `POST /api/v1/users` tạo người dùng mới, ném `DatabaseIntegrityError(table="users", constraint="unique_email")` nếu email đã tồn tại.

<details>
<summary>💡 Gợi ý</summary>

- Định nghĩa class `DatabaseIntegrityError(Exception)`.
- Đăng ký `@app.exception_handler(DatabaseIntegrityError)`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các tiêu chí sau:

- [ ] Bạn hiểu rõ cơ chế hoạt động của `fastapi.HTTPException` và cấu trúc 422 mặc định của Pydantic?
- [ ] Bạn nắm vững nguyên lý kiến trúc: Không bao giờ ném `HTTPException` bên trong Domain/Service Layer?
- [ ] Bạn biết cách xây dựng hệ thống phân tầng Domain Exceptions thuần túy trong Python?
- [ ] Bạn hiểu và áp dụng chính xác các trường chuẩn mực của **RFC 9457 Problem Details** (`type`, `title`, `status`, `detail`, `instance`)?
- [ ] Bạn sử dụng thành thạo `@app.exception_handler` để bắt cả Domain Exceptions lẫn `RequestValidationError`?
- [ ] Bạn biết cách bảo vệ hệ thống, ngăn rò rỉ thông tin nhạy cảm khi xử lý ngoại lệ 500 trên Production?

---

## 📚 Đọc thêm

- [FastAPI Official Documentation – Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [RFC 9457 – Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [Microsoft Learn – Handle errors in ASP.NET Core web APIs (ProblemDetails)](https://learn.microsoft.com/en-us/aspnet/core/web-api/handle-errors)
- [Martin Fowler – Separation of Concerns](https://martinfowler.com/)

<!-- nav:bottom -->
---

[⬅️ Pydantic v2](./06-pydantic-v2.md) | [📚 Mục lục Junior](./README.md) | [Dependency Injection ➡️](./08-dependency-injection.md)
<!-- /nav:bottom -->
