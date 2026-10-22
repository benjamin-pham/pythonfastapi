<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 05
<!-- /nav:top -->

# FastAPI đầu tiên

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 04: pytest cơ bản](./04-pytest-basics.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ kiến trúc nền tảng của **FastAPI**: sự kết hợp sức mạnh giữa **Starlette** (xử lý ASGI, routing, request/response hiệu năng cao) và **Pydantic** (data parsing, validation, serialization, và tự động sinh JSON Schema).
- Nắm vững mô hình máy chủ **ASGI** (Asynchronous Server Gateway Interface) so với WSGI truyền thống; phân biệt vai trò của ASGI server (Uvicorn ↔ Kestrel trong thế giới .NET).
- Khởi chạy dev server thành thạo bằng cả 2 phương thức: CLI mới **`fastapi dev`** và lệnh kinh điển **`uvicorn main:app --reload`**.
- Khai thác tối đa hệ thống sinh tài liệu tương tác tự động chuẩn OpenAPI: **Swagger UI** (`/docs`), **ReDoc** (`/redoc`), và raw schema (`/openapi.json`).
- Khai báo và phân biệt rạch ròi giữa **Path Parameters** và **Query Parameters** sử dụng cú pháp chuẩn hiện đại **`typing.Annotated`** kết hợp với `Path()` và `Query()`.
- Thiết lập mã trạng thái HTTP chuẩn mực bằng **`status_code=status.HTTP_201_CREATED`** từ module `fastapi.status`.
- Bổ sung metadata chuyên nghiệp cho endpoint: `tags`, `summary`, `description`, và `response_description`.

---

## 🔁 So sánh với C# / ASP.NET

Nếu bạn đến từ hệ sinh thái .NET, bạn sẽ thấy FastAPI mang tư duy thiết kế cực kỳ hiện đại, dung hòa giữa sự tinh gọn trực quan của **ASP.NET Core Minimal APIs** (`app.MapGet(...)`) và sức mạnh định kiểu tường minh của **Web API Controllers** (`[ApiController]`, `[Route]`).

| Khái niệm / Thành phần | ASP.NET Core (C#) | FastAPI (Python 3.12+) |
|---|---|---|
| **Mô hình lập trình** | Minimal APIs (`app.MapGet`) hoặc Controllers (`[ApiController]`) | Route Decorators (`@app.get(...)`, `@app.post(...)`) gắn trực tiếp trên hàm |
| **Máy chủ Web (Web Server)** | Kestrel (máy chủ HTTP bất đồng bộ tích hợp sẵn trong .NET) | Uvicorn / Granian (máy chủ ASGI non-blocking trên nền `uvloop` & `httptools`) |
| **Giao diện cổng kết nối** | OWIN / ASP.NET Core Hosting Pipeline | ASGI (Asynchronous Server Gateway Interface) |
| **Khai báo Path Parameter** | `app.MapGet("/tasks/{id:int}", (int id) => ...)` | `@app.get("/tasks/{task_id}")` với `task_id: int` |
| **Khai báo Query Parameter** | `([FromQuery] string? status) => ...` | `status: Annotated[str | None, Query()] = None` |
| **Validation tham số** | DataAnnotations (`[Range(1, 100)]`) hoặc FluentValidation | `Path(ge=1)`, `Query(max_length=50)` tích hợp sẵn trong type hint |
| **Tài liệu OpenAPI / Swagger** | Cần cài gói Swashbuckle / NSwag, cấu hình `AddSwaggerGen()`, `UseSwaggerUI()` | **Tự động 100%**: Sẵn sàng tại `/docs` và `/redoc` ngay khi app khởi động, không cần cài thêm thư viện |
| **HTTP Status Code** | `Results.Created(...)` hoặc `StatusCodes.Status201Created` | `status_code=status.HTTP_201_CREATED` từ `fastapi.status` |
| **Metadata tài liệu** | `.WithTags("Tasks").WithSummary("...")` | `@app.get(..., tags=["Tasks"], summary="...")` |

---

## 📖 Lý thuyết

### 1. Kiến trúc FastAPI: Starlette + Pydantic

FastAPI không xây dựng lại mọi thứ từ đầu mà đứng trên vai hai người khổng lồ:

```text
┌────────────────────────────────────────────────────────┐
│                      FastAPI                           │
│  - Dependency Injection (DI)                           │
│  - OpenAPI & Swagger UI generation                     │
│  - Type Hint inspection & parameter mapping            │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────┐ ┌───────────────────────┐
│          Starlette           │ │       Pydantic        │
│  - ASGI core & event loop    │ │  - Data parsing       │
│  - High-performance routing  │ │  - Schema validation  │
│  - Request / Response engine │ │  - Type coercion      │
│  - WebSockets & Middleware   │ │  - Rust core engine   │
└──────────────┬───────────────┘ └───────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Uvicorn (ASGI)         │
│  - HTTP/1.1 & WebSocket      │
│  - libuv event loop          │
└──────────────────────────────┘
```

1. **Starlette**: Đảm nhận toàn bộ hạ tầng mạng web: định tuyến URL (routing), xử lý Request/Response, quản lý Middleware, WebSockets, background tasks và cookie/session.
2. **Pydantic**: Đảm nhận tầng dữ liệu: phân tích cú pháp (parsing), chuyển đổi kiểu dữ liệu thông minh (type coercion - ví dụ chuyển chuỗi `"123"` từ URL thành số nguyên `123`), kiểm tra tính hợp lệ (validation), và tạo JSON Schema chuẩn cho OpenAPI.
3. **FastAPI**: Đóng vai trò là chất keo kết dính, bổ sung hệ thống Dependency Injection (DI), tự động sinh tài liệu OpenAPI 3.1, và cung cấp các decorator tiện dụng.

### 2. Mô hình ASGI & Máy chủ Uvicorn

Trong quá khứ, chuẩn **WSGI** (Web Server Gateway Interface, như Flask hay Django đời cũ) là tiêu chuẩn đồng bộ: mỗi kết nối HTTP giữ chặt một worker thread.

Với sự bùng nổ của bất đồng bộ (`asyncio`), chuẩn **ASGI** ra đời cho phép xử lý hàng vạn kết nối đồng thời trên một tiến trình duy nhất (tương tự như Kestrel trong ASP.NET Core hay Node.js). **Uvicorn** là máy chủ ASGI phổ biến nhất, sử dụng `uvloop` (bản port C của thư viện `libuv` dùng trong Node.js) mang lại tốc độ phản hồi cực nhanh.

#### Khởi chạy máy chủ phát triển (Development Server)

Có hai cách phổ biến để khởi động ứng dụng:

**Cách 1: Sử dụng FastAPI CLI mới (`fastapi dev`)**
Từ phiên bản FastAPI v0.111+, công cụ CLI chính thức được tích hợp sẵn:

```bash
# Tự động quét file main.py và lắng nghe ở cổng 8000
fastapi dev main.py
```
Lệnh này tự động kích hoạt chế độ auto-reload khi file mã nguồn thay đổi, hiển thị giao diện console đẹp mắt và tự động bind vào địa chỉ `127.0.0.1:8000`.

**Cách 2: Sử dụng Uvicorn trực tiếp (Kinh điển)**
```bash
uvicorn main:app --reload --port 8000
```
- `main`: Tên file `main.py` (module chứa code).
- `app`: Tên biến thể hiện của class `FastAPI()` bên trong file đó.
- `--reload`: Tự động khởi động lại tiến trình khi phát hiện thay đổi trong mã nguồn (chỉ dùng cho môi trường dev).

### 3. Tự động sinh tài liệu: Swagger UI & ReDoc

Một trong những ưu điểm nổi trội nhất của FastAPI là tính năng sinh tài liệu OpenAPI chuẩn hóa ngay lúc runtime:

- **Swagger UI** tại đường dẫn `http://127.0.0.1:8000/docs`: Cung cấp giao diện trực quan cho phép lập trình viên đọc tài liệu và bấm nút **"Try it out"** để trực tiếp gửi request kiểm thử API ngay trên trình duyệt mà không cần cài Postman.
- **ReDoc** tại đường dẫn `http://127.0.0.1:8000/redoc`: Giao diện hiển thị tài liệu dạng 3 cột cực kỳ trang nhã, thích hợp chia sẻ cho đối tác hoặc team frontend tra cứu hợp đồng API.
- **Raw OpenAPI Schema** tại `http://127.0.0.1:8000/openapi.json`: Toàn bộ định nghĩa API theo chuẩn OpenAPI 3.1 dạng JSON. Bạn có thể import file này vào Postman, Insomnia, hoặc dùng công cụ sinh client SDK tự động (như `openapi-generator` hay Kiota của Microsoft).

### 4. Định tuyến & Phân biệt `async def` vs `def`

FastAPI hỗ trợ cả hai loại hàm xử lý route (Route Handlers):

```python
from fastapi import FastAPI

app = FastAPI(title="TaskFlow API", version="1.0.0")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Chào mừng đến với TaskFlow API"}
```

> [!IMPORTANT]
> **Quy tắc vàng khi chọn `async def` hay `def` trong FastAPI**:
> - Dùng **`async def`** khi bạn gọi các thư viện I/O bất đồng bộ có `await` (ví dụ: `httpx`, `asyncpg`, `motor`).
> - Dùng **`def`** thông thường khi bạn gọi các hàm blocking đồng bộ (ví dụ: truy vấn database đồng bộ, đọc file ổ đĩa bằng `open()`, tính toán CPU-heavy). Khi gặp hàm `def`, FastAPI sẽ tự động chuyển nó sang chạy trong một **Threadpool riêng biệt** (`anyio.to_thread`), ngăn không cho mã blocking làm tê liệt Event Loop chính!
> - **Tuyệt đối KHÔNG** viết `async def` rồi gọi hàm blocking bên trong (ví dụ `time.sleep()`), vì điều đó sẽ chặn đứng toàn bộ luồng xử lý của server!

### 5. Path Parameters & Query Parameters với `Annotated`

Trong FastAPI, các tham số khai báo trên hàm route handler được phân loại tự động dựa trên vị trí của chúng:

1. **Path Parameters**: Được khai báo trực tiếp trong URL pattern:
   ```python
   @app.get("/items/{item_id}")
   def read_item(item_id: int): ...
   ```
2. **Query Parameters**: Không nằm trong URL pattern, xuất hiện sau dấu `?` trên URL (ví dụ: `/items?skip=0&limit=10`):
   ```python
   @app.get("/items")
   def list_items(skip: int = 0, limit: int = 20): ...
   ```

#### Chuẩn hóa với `typing.Annotated` (PEP 593)

Trong các tài liệu cũ, bạn thường thấy cú pháp gán trực tiếp: `item_id: int = Path(...)`. Tuy nhiên, từ Python 3.9+ và PEP 593, cộng đồng FastAPI chuyển hẳn sang sử dụng **`Annotated`**:

```python
from typing import Annotated
from fastapi import FastAPI, Path, Query

app = FastAPI()


@app.get("/tasks/{task_id}")
def get_task(
    task_id: Annotated[int, Path(ge=1, description="ID của task, phải >= 1")],
    include_details: Annotated[
        bool, Query(description="Có kèm chi tiết không")
    ] = False,
    tag: Annotated[str | None, Query(max_length=20)] = None,
) -> dict[str, object]:
    return {"task_id": task_id, "include_details": include_details, "tag": tag}
```

**Tại sao `Annotated` lại vượt trội?**
1. **Tách biệt kiểu dữ liệu và metadata**: Kiểu thực sự của biến là `int`, còn `Path(...)` chỉ là metadata gắn kèm dành riêng cho FastAPI.
2. **Hỗ trợ tối ưu cho Linter và Type Checker**: Mypy và Pylance hiểu chính xác kiểu của `task_id` là `int`, không bị nhầm lẫn với đối tượng `Path`.
3. **Giá trị mặc định chuẩn mực**: Tham số có thể dùng cú pháp gán mặc định thông thường `= False` thay vì nhét giá trị mặc định vào trong `Query(default=False)`.

#### Các điều kiện kiểm tra dữ liệu phổ biến:
- Dành cho số (`int`, `float`): `gt` (lớn hơn), `ge` (lớn hơn hoặc bằng), `lt` (nhỏ hơn), `le` (nhỏ hơn hoặc bằng).
- Dành cho chuỗi (`str`): `min_length`, `max_length`, `pattern` (biểu thức chính quy - Regex).

### 6. HTTP Status Codes & Route Metadata

Việc trả về đúng mã trạng thái HTTP là nguyên tắc cốt lõi của một RESTful API chuẩn mực:

```python
from typing import Annotated
from fastapi import FastAPI, Path, status

app = FastAPI()


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
    summary="Xóa vĩnh viễn một task",
    description="Xóa bản ghi công việc khỏi hệ thống theo task_id. Nếu thành công sẽ trả về 204 không có body.",
)
def delete_task(task_id: Annotated[int, Path(ge=1)]) -> None:
    # Thực hiện logic xóa...
    return None
```

- `status_code`: Thiết lập mã HTTP mặc định khi endpoint thực thi thành công (`HTTP_201_CREATED`, `HTTP_204_NO_CONTENT`). Sử dụng `fastapi.status` giúp code dễ đọc và tránh các con số ma thuật (magic numbers).
- `tags`: Gom nhóm các endpoint lại thành từng chuyên mục trực quan trên giao diện Swagger UI.
- `summary`: Dòng tóm tắt ngắn gọn hiển thị ngay tiêu đề của route.
- `description`: Đoạn văn bản mô tả chi tiết nghiệp vụ hỗ trợ định dạng Markdown.

---

## 💻 Ví dụ thực hành

Dưới đây là một ứng dụng FastAPI hoàn chỉnh minh họa toàn bộ các khái niệm đã học: quản lý danh sách công việc in-memory với đầy đủ Path/Query parameters, validation, status codes và Swagger metadata:

```python
from typing import Annotated
from fastapi import FastAPI, HTTPException, Path, Query, status

app = FastAPI(
    title="TaskFlow QuickStart API",
    description="Hệ thống quản lý công việc TaskFlow phiên bản khởi đầu",
    version="1.0.0",
)

# Giả lập cơ sở dữ liệu in-memory
fake_tasks_db: dict[int, dict[str, object]] = {
    1: {
        "id": 1,
        "title": "Cài đặt môi trường Python 3.12",
        "status": "DONE",
        "priority": "HIGH",
    },
    2: {
        "id": 2,
        "title": "Tìm hiểu Starlette và Pydantic",
        "status": "IN_PROGRESS",
        "priority": "HIGH",
    },
    3: {
        "id": 3,
        "title": "Viết Unit Test với Pytest",
        "status": "TODO",
        "priority": "MEDIUM",
    },
}


@app.get(
    "/api/v1/tasks",
    tags=["Tasks"],
    summary="Lấy danh sách công việc có lọc và phân trang",
    response_description="Danh sách các công việc thỏa mãn điều kiện lọc",
)
def list_tasks(
    status_filter: Annotated[
        str | None,
        Query(
            alias="status",
            description="Lọc theo trạng thái: TODO, IN_PROGRESS, DONE",
        ),
    ] = None,
    keyword: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=50,
            description="Tìm kiếm gần đúng theo tiêu đề",
        ),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Số lượng kết quả tối đa")
    ] = 10,
    offset: Annotated[
        int, Query(ge=0, description="Vị trí bắt đầu lấy kết quả")
    ] = 0,
) -> dict[str, object]:
    results = list(fake_tasks_db.values())

    if status_filter:
        results = [t for t in results if t["status"] == status_filter.upper()]

    if keyword:
        results = [
            t
            for t in results
            if keyword.lower() in str(t["title"]).lower()
        ]

    total = len(results)
    paged_results = results[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": paged_results,
    }


@app.get(
    "/api/v1/tasks/{task_id}",
    tags=["Tasks"],
    summary="Lấy thông tin chi tiết một công việc",
)
def get_task_by_id(
    task_id: Annotated[int, Path(ge=1, description="ID của task cần lấy")],
) -> dict[str, object]:
    task = fake_tasks_db.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy công việc với ID = {task_id}",
        )
    return task


@app.post(
    "/api/v1/tasks",
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Tạo công việc mới đơn giản",
)
def create_task_simple(
    title: Annotated[
        str, Query(min_length=3, max_length=100, description="Tiêu đề task")
    ],
    priority: Annotated[
        str, Query(pattern="^(LOW|MEDIUM|HIGH)$", description="Độ ưu tiên")
    ] = "MEDIUM",
) -> dict[str, object]:
    new_id = max(fake_tasks_db.keys(), default=0) + 1
    new_task: dict[str, object] = {
        "id": new_id,
        "title": title,
        "status": "TODO",
        "priority": priority,
    }
    fake_tasks_db[new_id] = new_task
    return new_task


@app.delete(
    "/api/v1/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
    summary="Xóa công việc",
)
def delete_task_by_id(
    task_id: Annotated[int, Path(ge=1, description="ID của task cần xóa")],
) -> None:
    if task_id not in fake_tasks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy task ID = {task_id} để xóa",
        )
    del fake_tasks_db[task_id]
    return None
```

---

## ⚠️ Lỗi thường gặp

### 1. Thứ tự khai báo route tĩnh và route động

Nếu bạn khai báo route có path parameter TRƯỚC một route có đường dẫn cố định, route cố định sẽ không bao giờ được chạm tới:

```python
# ❌ SAI: Route "/tasks/me" sẽ bị nuốt chửng bởi "/tasks/{task_id}"!
@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    return {"id": task_id}


@app.get("/tasks/me")
def get_my_tasks():
    # Khi user truy cập /tasks/me, FastAPI coi "me" là giá trị của task_id!
    return {"message": "Danh sách của tôi"}
```

```python
#  ĐÚNG: Luôn đặt các route tĩnh (static routes) lên TRƯỚC route động!
@app.get("/tasks/me")
def get_my_tasks():
    return {"message": "Danh sách của tôi"}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return {"id": task_id}
```

### 2. Sử dụng `async def` nhưng gọi hàm I/O blocking

Đây là lỗi phổ biến nhất của các lập trình viên mới chuyển từ C# sang Python:

```python
import time
from fastapi import FastAPI

app = FastAPI()


# ❌ SAI NGUY HIỂM: Làm treo toàn bộ Server!
@app.get("/slow-sync")
async def slow_sync():
    # time.sleep() là hàm blocking đồng bộ, nó sẽ khóa cứng event loop của tiến trình!
    time.sleep(5)
    return {"done": True}


#  ĐÚNG Cách 1: Dùng def thông thường (FastAPI sẽ đẩy sang threadpool)
@app.get("/slow-sync-fixed")
def slow_sync_fixed():
    time.sleep(5)
    return {"done": True}


#  ĐÚNG Cách 2: Dùng thư viện async tương ứng
import asyncio


@app.get("/slow-async")
async def slow_async():
    await asyncio.sleep(5)
    return {"done": True}
```

### 3. Nhầm lẫn giữa Path Parameter và Query Parameter

Nếu bạn muốn một biến là Path Parameter nhưng quên không đặt tên nó trong cặp ngoặc nhọn `{}` của URL, FastAPI sẽ tự động hiểu nó là Query Parameter:

```python
# ❌ Muốn /users/10 nhưng URL lại thành /users?user_id=10
@app.get("/users")
def get_user(user_id: int):
    return {"user_id": user_id}


#  ĐÚNG:
@app.get("/users/{user_id}")
def get_user_correct(user_id: int):
    return {"user_id": user_id}
```

---

## ✍️ Bài tập thực hành

### Bài 1: API Tra cứu Sách Thư viện (Book Catalog)
Tạo ứng dụng FastAPI phục vụ tra cứu sách:
- Endpoint `GET /api/v1/books`:
  - Tham số query `keyword`: bắt buộc có độ dài từ 2 đến 30 ký tự.
  - Tham số query `published_year`: số nguyên phải nằm trong khoảng từ `1900` đến `2026` (`ge=1900, le=2026`).
  - Tham số phân trang `limit` (mặc định 10, tối đa 50) và `offset` (mặc định 0).
- Trả về danh sách sách phù hợp kèm tổng số lượng.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng `keyword: Annotated[str, Query(min_length=2, max_length=30)]`.
- Sử dụng `published_year: Annotated[int | None, Query(ge=1900, le=2026)] = None`.
- Kiểm tra điều kiện lọc bằng list comprehension trên dữ liệu mẫu.
</details>

---

### Bài 2: API Quản lý Kho Hàng theo Mã Danh Mục (Inventory)
Tạo ứng dụng quản lý sản phẩm:
- Endpoint `GET /api/v1/categories/{category_code}/items/{item_id}`:
  - `category_code`: Chuỗi ký tự chỉ gồm chữ in hoa và gạch dưới, độ dài từ 3 đến 10 ký tự (sử dụng regex pattern `^[A-Z_]{3,10}$`).
  - `item_id`: Số nguyên dương `>= 1`.
- Nếu không tìm thấy sản phẩm, trả về mã lỗi `404 Not Found` kèm thông điệp chi tiết.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng `category_code: Annotated[str, Path(pattern="^[A-Z_]{3,10}$")]`.
- Sử dụng `item_id: Annotated[int, Path(ge=1)]`.
- Dùng `raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=...)`.
</details>

---

### Bài 3: API Quản lý Đơn hàng với Metadata OpenAPI đầy đủ
Xây dựng 2 endpoint cho tài nguyên `orders`:
1. `POST /api/v1/orders`: Tạo đơn hàng mới, nhận `customer_name` (3-50 ký tự) và `amount` (float > 0), trả về status `201 Created`.
2. `DELETE /api/v1/orders/{order_id}`: Xóa đơn hàng theo `order_id >= 1`, trả về status `204 No Content`.
3. Gắn đầy đủ `tags=["Orders"]`, `summary`, `description` chi tiết cho cả 2 route. Kiểm tra giao diện Swagger UI tại `/docs` để xác nhận tài liệu được render chuẩn xác.

<details>
<summary>💡 Gợi ý</summary>

- Khai báo decorator với `status_code=status.HTTP_201_CREATED` cho POST và `status_code=status.HTTP_204_NO_CONTENT` cho DELETE.
- Hàm DELETE trả về kiểu `-> None` và return `None`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các tiêu chí sau:

- [ ] Bạn hiểu rõ vai trò phối hợp giữa Starlette (ASGI, routing) và Pydantic (data parsing, validation) trong FastAPI?
- [ ] Bạn phân biệt được sự khác nhau giữa máy chủ ASGI (Uvicorn) và Kestrel trong C#?
- [ ] Bạn biết cách khởi chạy dev server bằng `fastapi dev` hoặc `uvicorn main:app --reload`?
- [ ] Bạn thành thạo việc tra cứu và tương tác với Swagger UI (`/docs`) và ReDoc (`/redoc`)?
- [ ] Bạn hiểu nguyên tắc lựa chọn giữa `async def` và `def` thông thường để tránh làm nghẽn Event Loop?
- [ ] Bạn sử dụng thành thạo cú pháp `Annotated[T, Path(...)]` và `Annotated[T, Query(...)]` với các điều kiện ràng buộc (`ge`, `le`, `min_length`, `pattern`)?
- [ ] Bạn biết cách thiết lập HTTP Status Codes chuẩn mực thông qua `status_code=status.HTTP_*`?

---

## 📚 Đọc thêm

- [FastAPI Official Documentation – First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI Official Documentation – Path Parameters and Numeric Validations](https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/)
- [FastAPI Official Documentation – Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)
- [Starlette Official Documentation](https://www.starlette.io/)
- [Uvicorn Official Documentation](https://www.uvicorn.org/)

<!-- nav:bottom -->
---

[⬅️ pytest cơ bản](./04-pytest-basics.md) | [📚 Mục lục Junior](./README.md) | [Pydantic v2 ➡️](./06-pydantic-v2.md)
<!-- /nav:bottom -->
