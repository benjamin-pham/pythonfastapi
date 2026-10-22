<!-- nav:top -->
[🏠 Home](../README.md) › Phụ lục › C# vs Python
<!-- /nav:top -->

# C# vs Python: Sổ Tay Tra Cứu Toàn Diện Cho Kỹ Sư .NET

> **Mục tiêu tài liệu**: Đóng vai trò kim chỉ nam và cuốn sổ tay tra cứu (Rosetta Stone) nhanh, thực chiến, chuyên sâu dành cho các kỹ sư phần mềm đã có kinh nghiệm vững chắc với nền tảng **C# / .NET (.NET 8/9, ASP.NET Core, EF Core)** khi chuyển dịch sang hệ sinh thái **Python hiện đại (Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0)**.

---

## 🧭 Lời mở đầu: Chuyển dịch Tư duy từ .NET sang Python

Khi chuyển từ C# sang Python, thách thức lớn nhất của các kỹ sư không nằm ở cú pháp (vốn rất tinh gọn và dễ đọc của Python), mà nằm ở **mô hình tư duy (Mental Model)**:
1. **Từ Manifest Nominal Typing sang Structural & Duck Typing**: Trong C#, mọi đối tượng phải khai báo kiểu tường minh hoặc ngầm định suy diễn kiểu lúc compile-time (`var`), kế thừa tường minh từ một `interface` hoặc `class`. Trong Python, hệ thống kiểu vận hành theo triết lý *Duck Typing* ("Nếu nó đi như một con vịt và kêu như một con vịt, nó là một con vịt") kết hợp với *Static Type Hints* (PEP 484, PEP 544 Protocol) được kiểm tra qua `mypy` hoặc `pyright` mà không sinh ra chi phí phụ trội ở runtime.
2. **Từ Multi-Threaded ThreadPool sang Single-Threaded Cooperative Event Loop**: C# xử lý async bằng cách phân bổ công việc lên cụm luồng điều phối của hệ điều hành (ThreadPool với cơ chế Work-Stealing). Python (CPython) sử dụng mô hình vòng lặp sự kiện đơn luồng hợp tác (**Event Loop**) được bảo vệ bởi **GIL** (Global Interpreter Lock). Do đó, việc gọi một hàm đồng bộ gây nghẽn (Blocking I/O hay `Thread.Sleep`) trong coroutine Python sẽ làm đóng băng toàn bộ máy chủ API!
3. **Từ "Ceremony" sang "Pragmatism"**: .NET khuyến khích việc tạo hàng loạt các lớp trừu tượng (Interface, Factory, Dependency Injection Service Lifetime). Python tôn trọng sự tối giản: một hàm thuần túy (pure function) hoặc một module có thể thay thế hoàn hảo cho một Service Class nếu nó không cần lưu trạng thái (state).

---

## 1. 🛠️ Công cụ & Hệ sinh thái (Tooling & Ecosystem)

Hệ sinh thái Python hiện đại (2024–2026) đã trải qua một cuộc cách mạng vượt bậc với sự xuất hiện của **`uv`** (viết bằng Rust từ Astral), đem lại trải nghiệm quản lý gói và môi trường tương đương, thậm chí vượt trội hơn tốc độ của `dotnet CLI`.

### Bảng Đối chiếu Lệnh & Khái niệm

| Khái niệm / Tác vụ | C# / .NET (.NET 8+) | Python Hiện Đại (Astral `uv` / PyPI) |
|---|---|---|
| **Kho gói thư viện trung tâm** | NuGet Gallery (`nuget.org`) | Python Package Index (`pypi.org`) |
| **Công cụ CLI hợp nhất** | `dotnet` | `uv` (hoặc `pip` + `venv` truyền thống) |
| **Tập tin cấu hình dự án** | `.csproj` / `Directory.Build.props` (XML) | `pyproject.toml` (chuẩn PEP 517 / 518 / 621) |
| **Khóa phiên bản (Lockfile)** | `packages.lock.json` | `uv.lock` |
| **Tạo dự án mới** | `dotnet new webapi -n TaskFlow` | `uv init --app taskflow` |
| **Cài đặt thư viện phụ thuộc** | `dotnet add package FastAPI` | `uv add fastapi` |
| **Cài đặt thư viện dev/test** | `dotnet add package xunit` | `uv add --dev pytest` |
| **Khởi chạy ứng dụng** | `dotnet run` | `uv run python -m app.main` |
| **Chạy kiểm thử tự động** | `dotnet test` | `uv run pytest` |
| **Định dạng mã nguồn (Format)** | `dotnet format` | `uv run ruff format` |
| **Phân tích tĩnh (Linter)** | Roslyn Analyzers / SonarQube | `uv run ruff check` |
| **Kiểm tra kiểu tĩnh (Typecheck)** | Trình biên dịch Roslyn (`csc`) | `uv run mypy` hoặc `uv run pyright` |
| **Quản lý phiên bản SDK/Runtime** | `dotnet-install.sh` / Global SDKs | `uv python install 3.12 3.13` |
| **Môi trường ảo (Isolation)** | Global GAC / `bin/` & `obj/` per project | Virtual Environment (`.venv`) độc lập tuyệt đối |

---

## 2. 🔤 Cú pháp & Kiểu Dữ liệu (Syntax & Data Types)

### 2.1. Giá trị Rỗng: `null` vs `None`

Trong C#, `null` là một con trỏ rỗng và toán tử so sánh `== null` có thể bị overload bởi class. Trong Python, `None` là một đối tượng duy nhất (Singleton) thuộc kiểu `NoneType`.

```csharp
// C# (.NET 8)
string? name = null;
if (name is null) {
    Console.WriteLine("Name is empty");
}
```

```python
# Python 3.12+
name: str | None = None
if name is None:
    print("Name is empty")

# ❌ TUYỆT ĐỐI TRÁNH: if name == None:
# Lý do: '==' gọi dunder method __eq__, có thể bị class tùy biến ghi đè gây sai lệch logic.
# 'is' so sánh địa chỉ bộ nhớ (identity check) - cực nhanh và an toàn tuyệt đối.
```

### 2.2. Hệ thống Kiểu Dữ liệu & Type Hints

```csharp
// C# - Static Manifest Typing
int count = 42;
double price = 19.99;
bool isActive = true;
string title = "TaskFlow";
List<string> tags = new() { "Backend", "FastAPI" };
Dictionary<string, int> scores = new() { { "Alice", 100 } };
```

```python
# Python 3.12+ - Strong Dynamic Typing kết hợp Static Type Hints
count: int = 42
price: float = 19.99
is_active: bool = True
title: str = "TaskFlow"
tags: list[str] = ["Backend", "FastAPI"]
scores: dict[str, int] = {"Alice": 100}
```

### 2.3. Cấu trúc Tập hợp (Collections)

| Cấu trúc dữ liệu | C# (.NET) | Python | Đặc tính Python |
|---|---|---|---|
| **Danh sách động (Dynamic List)** | `List<T>` | `list[T]` | `lst = [1, 2, 3]`; `lst.append(4)` |
| **Mảng cố định bất biến** | `ReadOnlyCollection<T>` / `ImmutableArray<T>` | `tuple[T, ...]` | `tpl = (1, 2, 3)`; Bất biến (Immutable), làm được dict key |
| **Bảng băm (Hash Table / Map)** | `Dictionary<TKey, TValue>` | `dict[K, V]` | `d = {"key": "val"}`; Giữ thứ tự thêm vào (insertion-order) |
| **Tập hợp duy nhất (Set)** | `HashSet<T>` | `set[T]` | `s = {1, 2, 3}`; Không trùng lặp, tìm kiếm $O(1)$ |
| **Hàng đợi hai đầu** | `LinkedList<T>` / `Queue<T>` | `collections.deque` | Tối ưu hóa append/pop ở cả hai đầu $O(1)$ |

### 2.4. Nội suy Chuỗi (String Interpolation)

```csharp
// C#
var title = "Bug";
var priority = 1;
var message = $"Task '{title}' has priority: {priority:D2}";
```

```python
# Python 3.12+ (f-string)
title = "Bug"
priority = 1
message = f"Task '{title}' has priority: {priority:02d}"
```

### 2.5. Khớp Mẫu Cấu trúc (Structural Pattern Matching)

C# có `switch` expressions (từ C# 8), Python giới thiệu `match / case` (từ Python 3.10 - PEP 634):

```csharp
// C#
string GetStatusMessage(object status) => status switch
{
    "TODO" => "Chưa bắt đầu",
    "IN_PROGRESS" => "Đang xử lý",
    "DONE" => "Hoàn thành",
    _ => "Không xác định"
};
```

```python
# Python 3.10+
def get_status_message(status: str | dict[str, str]) -> str:
    match status:
        case "TODO":
            return "Chưa bắt đầu"
        case "IN_PROGRESS":
            return "Đang xử lý"
        case "DONE":
            return "Hoàn thành"
        case {"custom": name}:
            return f"Tùy biến: {name}"
        case _:
            return "Không xác định"
```

---

## 3. 🧩 Hướng Đối Tượng & Lập Trình Hàm (OOP & Functional)

### 3.1. DTO & Data Transfer Objects: `record` vs `@dataclass` vs Pydantic

Trong C#, `record` cung cấp ngữ nghĩa giá trị (value-based equality) và tính bất biến. Trong Python:
- Dùng `@dataclass(slots=True, frozen=True)` cho cấu trúc dữ liệu thuần túy nội bộ (Internal Domain/Memory).
- Dùng Pydantic `BaseModel` cho tầng giao tiếp bên ngoài (API Input/Output/Serialization).

```csharp
// C#
public sealed record TaskDto(
    Guid Id,
    string Title,
    bool IsCompleted = false
);
```

```python
# Python 3.12+ (Pure Dataclass)
from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class TaskDto:
    id: UUID
    title: str
    is_completed: bool = False
```

```python
# Python 3.12+ (Pydantic v2 - Dành cho API DTO với Data Validation)
from uuid import UUID
from pydantic import BaseModel, Field


class TaskReadSchema(BaseModel):
    id: UUID
    title: str = Field(min_length=3, max_length=120)
    is_completed: bool = False

    model_config = {"frozen": True}
```

### 3.2. Đa hình & Giao diện: Nominal `interface` vs Structural `typing.Protocol`

Trong C#, một class bắt buộc phải khai báo tường minh `: ITaskRepository` (Nominal Subtyping). Python hỗ trợ **Structural Subtyping** (Static Duck Typing) thông qua `typing.Protocol` (PEP 544):

```csharp
// C#
public interface ITaskRepository
{
    Task<TaskEntity?> GetByIdAsync(Guid id);
}

public class SqlTaskRepository : ITaskRepository
{
    public async Task<TaskEntity?> GetByIdAsync(Guid id) { ... }
}
```

```python
# Python 3.12+
from typing import Protocol
from uuid import UUID


class TaskProtocol(Protocol):
    """Protocol đóng vai trò hợp đồng không cần kế thừa trực tiếp."""

    async def get_by_id(self, task_id: UUID) -> dict[str, str] | None: ...


class SqlTaskRepo:
    """Class này KHÔNG cần kế thừa TaskProtocol, chỉ cần có cùng chữ ký hàm."""

    async def get_by_id(self, task_id: UUID) -> dict[str, str] | None:
        return {"id": str(task_id), "title": "Database Task"}


def execute_query(repo: TaskProtocol, task_id: UUID) -> None:
    # Mypy / Pyright chấp nhận SqlTaskRepo hoàn toàn hợp lệ!
    pass
```

### 3.3. Thao tác Dữ liệu: LINQ vs Comprehensions & Itertools

C# nổi tiếng với thư viện LINQ (`System.Linq`). Trong Python, các kỹ thuật tương đương được tích hợp trực tiếp vào cú pháp ngôn ngữ qua **List/Dict Comprehensions** và module chuẩn **`itertools`**:

```csharp
// C# LINQ
var activeTitles = tasks
    .Where(t => t.IsActive && t.Priority == Priority.High)
    .Select(t => t.Title.ToUpper())
    .Take(5)
    .ToList();

var taskMap = tasks.ToDictionary(t => t.Id, t => t.Title);
```

```python
# Python Comprehensions
active_titles = [
    t.title.upper() for t in tasks if t.is_active and t.priority == Priority.HIGH
][:5]

task_map = {t.id: t.title for t in tasks}
```

#### Bảng Tra Cứu Tương Đương LINQ ↔ Python

| Toán tử C# LINQ | Cú pháp / Hàm Python Tương đương |
|---|---|
| `.Where(x => predicate(x))` | `[x for x in seq if predicate(x)]` hoặc `filter(predicate, seq)` |
| `.Select(x => transform(x))` | `[transform(x) for x in seq]` hoặc `map(transform, seq)` |
| `.Any(x => predicate(x))` | `any(predicate(x) for x in seq)` |
| `.All(x => predicate(x))` | `all(predicate(x) for x in seq)` |
| `.OrderBy(x => x.Prop)` | `sorted(seq, key=lambda x: x.prop)` |
| `.OrderByDescending(x => x.Prop)` | `sorted(seq, key=lambda x: x.prop, reverse=True)` |
| `.Take(n)` | `seq[:n]` hoặc `itertools.islice(seq, n)` |
| `.Skip(n)` | `seq[n:]` hoặc `itertools.islice(seq, n, None)` |
| `.GroupBy(x => x.Key)` | `itertools.groupby(sorted_seq, key=lambda x: x.key)` |
| `.Distinct()` | `list(set(seq))` (nếu không cần giữ thứ tự) hoặc `dict.fromkeys(seq)` |
| `.Aggregate((acc, x) => ...)` | `functools.reduce(lambda acc, x: ..., seq)` |

---

## 4. ⚡ Lập Trình Bất Đồng Bộ (Asynchronous Programming)

Đây là khu vực quan trọng bậc nhất mà developer C# thường vấp phải sai lầm nghiêm trọng khi sang Python.

### 4.1. So sánh Mô hình Thực thi

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MÔ HÌNH BẤT ĐỒNG BỘ: C# VS PYTHON                     │
│                                                                             │
│  [ C# / .NET ThreadPool Architecture ]                                      │
│  ThreadPool Workers (Luồng OS đa lõi)                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                     │
│  │ OS Thread 1  │   │ OS Thread 2  │   │ OS Thread 3  │   (Preemptive)      │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                     │
│         ▲                  ▲                  ▲                             │
│         └────────── Task.Run / IO Work ───────┘                             │
│                                                                             │
│  [ Python CPython Event Loop Architecture ]                                 │
│  1 OS Thread + GIL (Global Interpreter Lock)                                │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │ Single-Threaded Cooperative Event Loop                       │           │
│  │ ┌───────────────┐   ┌───────────────┐   ┌────────────────┐   │           │
│  │ │ Task A        │──►│ Task B (await)│──►│ Task C         │   │           │
│  │ │ (Running...)  │   │ (Paused IO...)│   │ (Running...)   │   │           │
│  │ └───────────────┘   └───────────────┘   └────────────────┘   │           │
│  └──────────────────────────────────────────────────────────────┘           │
│  * Chú ý: Nếu Task A gọi time.sleep() (blocking), TOÀN TIẾN TRÌNH DỪNG LẠI! │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2. Bảng Đối chiếu Khái niệm & Cơ chế Bất đồng bộ

| Khái niệm Async | C# / .NET | Python `asyncio` |
|---|---|---|
| **Đơn vị công việc bất đồng bộ** | `Task` / `Task<T>` | `asyncio.Task[T]` / `Coroutine` |
| **Khai báo hàm bất đồng bộ** | `public async Task<int> FetchAsync()` | `async def fetch() -> int:` |
| **Chờ đợi kết quả** | `await task;` | `await task` |
| **Tạo và kích hoạt task ngầm** | `Task.Run(() => ...)` | `asyncio.create_task(...)` |
| **Chạy đồng thời nhiều tasks** | `await Task.WhenAll(t1, t2);` | `await asyncio.gather(t1, t2)` |
| **Structured Concurrency** | Không có sẵn (cần tự quản lý Task) | `async with asyncio.TaskGroup() as tg:` (Python 3.11+) |
| **Hủy bỏ tác vụ (Cancellation)** | `CancellationToken` truyền qua tham số | `task.cancel()` → ném ngoại lệ `asyncio.CancelledError` |
| **Hạn chế thời gian (Timeout)** | `CancellationTokenSource(TimeSpan...)` | `async with asyncio.timeout(5.0):` (Python 3.11+) |
| **Đồng bộ hóa / Khóa** | `SemaphoreSlim` / `lock(obj)` | `asyncio.Lock()` (chỉ khóa logic giữa các coroutine) |
| **Đường ống (Queue / Pipeline)** | `System.Threading.Channels.Channel<T>` | `asyncio.Queue[T]` |
| **Đẩy tác vụ chặn (Blocking) ra luồng riêng** | Mặc định ThreadPool | `await asyncio.to_thread(blocking_func, arg)` |

### 4.3. Ví dụ Code Đối chiếu: Chạy Đồng Thời & Xử lý Timeout

```csharp
// C# (.NET 8)
using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
try
{
    var task1 = FetchUserAsync(userId, cts.Token);
    var task2 = FetchOrdersAsync(userId, cts.Token);
    await Task.WhenAll(task1, task2);
    
    var user = await task1;
    var orders = await task2;
}
catch (OperationCanceledException)
{
    Console.WriteLine("Quá hạn thời gian xử lý (Timeout)!");
}
```

```python
# Python 3.12+ (Structured Concurrency với TaskGroup & timeout)
import asyncio


async def main() -> None:
    try:
        async with asyncio.timeout(5.0):  # Hủy bỏ tự động sau 5 giây
            async with asyncio.TaskGroup() as tg:
                t1 = tg.create_task(fetch_user(user_id))
                t2 = tg.create_task(fetch_orders(user_id))

            user = t1.result()
            orders = t2.result()
    except TimeoutError:
        print("Quá hạn thời gian xử lý (Timeout)!")
```

---

## 5. 🌐 Web API & Framework (ASP.NET Core ↔ FastAPI)

Cả **ASP.NET Core Minimal APIs** và **FastAPI** đều hướng tới sự tinh gọn, hiệu năng cực cao và chuẩn mở OpenAPI. Dưới đây là bảng so sánh trực tiếp kiến trúc hai nền tảng:

```csharp
// ASP.NET Core (.NET 8 Minimal API)
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddScoped<ITaskService, TaskService>();
builder.Services.Configure<AppConfig>(builder.Configuration.GetSection("App"));

var app = builder.Build();

app.MapPost("/api/v1/tasks", async (
    CreateTaskRequest request,
    [FromServices] ITaskService service,
    CancellationToken ct) =>
{
    var result = await service.CreateAsync(request, ct);
    return Results.Created($"/api/v1/tasks/{result.Id}", result);
});

app.Run();
```

```python
# FastAPI (Python 3.12+)
from typing import Annotated
from fastapi import FastAPI, Depends, status
from pydantic import BaseModel, Field

app = FastAPI()


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=3, max_length=120)


@app.post("/api/v1/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    return await service.create(request)
```

### Bảng Đối Chiếu Các Thành Phần Web Framework

| Thành phần Web | ASP.NET Core | FastAPI |
|---|---|---|
| **Cơ chế Khởi động & Vòng đời** | `IHostLifetime` / `IHostedService` | `@asynccontextmanager async def lifespan(app: FastAPI):` |
| **Đăng ký Dependency Injection** | `IServiceCollection` (`AddScoped`, `AddSingleton`) | Hàm generator `Depends()` tiêm theo request |
| **Quản lý Cấu hình (Settings)** | `appsettings.json` + `IOptions<T>` | `pydantic-settings` (`BaseSettings`, nạp biến môi trường `.env`) |
| **Validation Dữ liệu** | FluentValidation / DataAnnotations | Pydantic v2 (Rust Core `pydantic-core`, cực nhanh) |
| **Bộ lọc Ngoại lệ (Exceptions)** | `UseExceptionHandler` / Custom Middleware | `@app.exception_handler(ExceptionClass)` |
| **Middleware Pipeline** | `app.UseMiddleware<T>()` / `UseRouting()` | Starlette `BaseHTTPMiddleware` hoặc Pure ASGI Middleware |
| **Tài liệu API Tự động** | Swashbuckle / NSwag (`/swagger`) | Tích hợp sẵn Swagger UI (`/docs`) và ReDoc (`/redoc`) |
| **Tác vụ ngầm nhẹ trong tiến trình** | `IHostedService` / BackgroundService | FastAPI `BackgroundTasks` |
| **Tác vụ ngầm phân tán (Queue)** | Hangfire / MassTransit / RabbitMQ | ARQ / Celery / Dramatiq giao tiếp qua Redis |

---

## 6. 🗄️ Cơ Sở Dữ Liệu & Kiểm Thử (Database & Testing)

### 6.1. ORM: Entity Framework Core vs SQLAlchemy 2.0

SQLAlchemy 2.0 đã chuyển đổi toàn diện sang phong cách hiện đại với `AsyncSession` và cú pháp hàm `select()`, mang tư duy tương tự như LINQ to Entities:

```csharp
// C# - Entity Framework Core 8
public class AppDbContext : DbContext
{
    public DbSet<TaskEntity> Tasks => Set<TaskEntity>();
}

// Truy vấn
var tasks = await dbContext.Tasks
    .Include(t => t.Project)
    .Where(t => t.Status == TaskStatus.InProgress)
    .OrderByDescending(t => t.CreatedAt)
    .ToListAsync(cancellationToken);
```

```python
# Python 3.12+ - SQLAlchemy 2.0 Async
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

# Truy vấn tương đương LINQ
stmt = (
    select(TaskEntity)
    .options(selectinload(TaskEntity.project))  # Tương đương .Include(t => t.Project)
    .where(TaskEntity.status == TaskStatus.IN_PROGRESS)
    .order_by(TaskEntity.created_at.desc())
)
result = await session.execute(stmt)
tasks = result.scalars().all()
```

### 6.2. Di chuyển Lược đồ (Database Migrations)

| Tính năng | EF Core Migrations | Alembic |
|---|---|---|
| **Tạo migration mới từ code** | `dotnet ef migrations add AddUserTable` | `alembic revision --autogenerate -m "add_user_table"` |
| **Áp dụng migration lên DB** | `dotnet ef database update` | `alembic upgrade head` |
| **Hoàn tác (Rollback) 1 bước** | `dotnet ef database update <PrevMigration>` | `alembic downgrade -1` |
| **Xem lịch sử migrations** | `dotnet ef migrations list` | `alembic history` |

### 6.3. Kiểm Thử Tự Động: xUnit / Moq vs Pytest / Pytest-Mock

`pytest` là chuẩn mực vàng trong kiểm thử Python nhờ cú pháp ngắn gọn (dùng lệnh `assert` thuần túy thay vì các hàm `Assert.Equal`), hệ thống fixture linh hoạt và tốc độ thực thi xuất sắc:

```csharp
// C# - xUnit + Moq + WebApplicationFactory
public class TaskApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;
    public TaskApiTests(WebApplicationFactory<Program> factory) => _client = factory.CreateClient();

    [Theory]
    [InlineData("Task 1")]
    [InlineData("Task 2")]
    public async Task CreateTask_ValidTitle_ReturnsCreated(string title)
    {
        var response = await _client.PostAsJsonAsync("/api/v1/tasks", new { Title = title });
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
    }
}
```

```python
# Python - Pytest + pytest-asyncio + httpx
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.parametrize("title", ["Task 1", "Task 2"])
async def test_create_task_valid_title_returns_created(title: str) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/tasks", json={"title": title})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == title
```

---

## 7. ⚠️ Những Thói Quen C# Cần Bỏ Khi Viết Python

Khi chuyển giao kinh nghiệm từ .NET sang Python, việc "bê nguyên xi" các thói quen C# vào dự án Python là nguyên nhân hàng đầu sinh ra mã nguồn cồng kềnh, khó bảo trì (Unpythonic):

| Thói quen C# cần bỏ | Tại sao là Anti-Pattern trong Python? | Cách làm chuẩn Pythonic |
|---|---|---|
| **1. Over-Interfacing (Tạo Interface cho mọi Service)** | Trong C#, bạn thường tạo `ITaskService` chỉ để phục vụ cho `TaskService` (để mock khi unit test). Trong Python, nhờ bản chất dynamic và `unittest.mock`, bạn có thể mock trực tiếp bất kỳ class hay hàm nào mà không cần interface trung gian vô nghĩa. | Chỉ tạo `Protocol` khi bạn thật sự có nhiều triển khai (Multi-implementations) độc lập. |
| **2. Viết Getters / Setters rườm rà** | Viết `get_name()` và `set_name(val)` biến code Python thành Java/C# của 15 năm trước, làm mất đi sự trong sáng của cú pháp. | Dùng public attributes trực tiếp (`task.title = "New"`). Nếu sau này cần validation khi gán giá trị, hãy dùng decorator `@property` mà không làm vỡ API bên ngoài. |
| **3. Đặt tên PascalCase cho phương thức và biến** | C# dùng `PascalCase` cho method (`CreateTask()`). Viết như vậy trong Python vi phạm nghiêm trọng chuẩn **PEP 8** và gây nhầm lẫn với tên Class. | Luôn dùng `snake_case` cho hàm, phương thức, biến và module: `create_task()`, `is_active`. Chỉ Class mới dùng `PascalCase`. |
| **4. Mutable Default Arguments trong hàm** | Viết `def add_item(item, items=[])`: Trong Python, giá trị mặc định của hàm chỉ được khởi tạo **duy nhất 1 lần** khi nạp module. Danh sách `items` sẽ bị chia sẻ (shared state) qua mọi lần gọi hàm tiếp theo! | Luôn dùng `None` làm mặc định: `def add_item(item: str, items: list[str] | None = None): if items is None: items = []`. |
| **5. Gọi Blocking I/O hoặc `time.sleep()` trong async** | Trong C#, ThreadPool sẽ tự spawn thêm thread mới khi phát hiện tắc nghẽn. Trong Python, Event Loop là đơn luồng; gọi `time.sleep(5)` hay thư viện `requests.get()` sẽ chặn đứng 100% người dùng khác trên toàn hệ thống! | Dùng `await asyncio.sleep(5)` và các thư viện async (`httpx`, `asyncpg`, `redis.asyncio`). Nếu bắt buộc phải gọi hàm blocking bên thứ ba, bọc qua `await asyncio.to_thread(func)`. |
| **6. Lạm dụng `isinstance()` để ép kiểu thủ công** | Cố gắng kiểm tra kiểu của đối tượng ở mọi hàm bằng `if isinstance(x, MyType):` đi ngược lại triết lý Duck Typing của Python và làm code bị phụ thuộc cứng. | Hãy tin tưởng Type Hints kết hợp `mypy` lúc kiểm tra tĩnh, và áp dụng triết lý **EAFP** (*Easier to Ask for Forgiveness than Permission*) với khối `try ... except`. |

---

## 8. 🎯 Kết Luận

Nền tảng kiến trúc vững chắc, hiểu biết sâu sắc về OOP, quản lý bộ nhớ và hệ thống phân tán từ thế giới C# / .NET là một **lợi thế cạnh tranh vượt trội** khi bạn bước chân vào thế giới Python. Bằng cách gỡ bỏ các rào cản về thủ tục (ceremony) rườm rà và làm chủ mô hình bất đồng bộ `asyncio`, bạn sẽ khai phá được sức mạnh tối đa của Python: tốc độ phát triển cực nhanh, mã nguồn tinh gọn và hiệu năng xử lý API sánh ngang các ngôn ngữ biên dịch hiện đại!

<!-- nav:bottom -->
---

[🏠 Về trang chủ](../README.md)
<!-- /nav:bottom -->
