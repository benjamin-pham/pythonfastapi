<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 02
<!-- /nav:top -->

# Profiling & hiệu năng

> ⏱️ Thời lượng: ~4.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 01: Python internals & concurrency](./01-python-internals-concurrency.md) và [SQLAlchemy 2.0 ORM](../03-middle/02-sqlalchemy-orm.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Thấu hiểu chu trình tối ưu hiệu năng có cơ sở (Data-driven Performance Engineering)**: Nằm lòng quy trình *Measure → Profile → Optimize → Verify* và tránh bẫy tối ưu hóa sớm (premature optimization).
- **Làm chủ CPU Profiling chuyên nghiệp**: Sử dụng thành thạo `cProfile` (deterministic profiler trong phát triển) và `py-spy` (sampling profiler viết bằng Rust, an toàn 100% để tạo flamegraph trực tiếp trên production mà không làm gián đoạn dịch vụ).
- **Phát hiện và cô lập rò rỉ bộ nhớ với `tracemalloc`**: Chụp và so sánh snapshot bộ nhớ để tìm chính xác dòng mã nguồn gây rò rỉ RAM (memory leak).
- **Kiểm thử tải hệ thống bằng `locust`**: Viết kịch bản kiểm thử tải bằng mã Python (`HttpUser`, `task`), đo đạc RPS, độ trễ phân vị p50, p95, p99 dưới áp lực cao.
- **Tiêu diệt triệt để vấn nạn N+1 queries trong SQLAlchemy 2.0**: Phân biệt và ứng dụng chính xác `selectinload` (quan hệ 1-N / M-N) và `joinedload` (quan hệ N-1 / 1-1), tránh bẫy bùng nổ Cartesian Product.
- **Tinh chỉnh Connection Pool chuẩn Production**: Cấu hình tối ưu `pool_size`, `max_overflow`, `pool_pre_ping=True`, và `pool_recycle` để ngăn chặn hoàn toàn lỗi ngắt kết nối âm thầm.
- **Tăng tốc độ tuần tự hóa dữ liệu (Serialization)**: Khai thác Pydantic v2 core (Rust) và tích hợp `orjson` / `ORJSONResponse` trong FastAPI để tăng thông lượng xử lý JSON lên 2x–4x.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET doanh nghiệp, hệ sinh thái công cụ đo đạc hiệu năng cực kỳ hoàn chỉnh và được tích hợp sâu từ cấp độ IDE đến CLR Runtime:

| Nhu cầu / Công cụ | C# / .NET Ecosystem | Python & FastAPI Ecosystem |
|---|---|---|
| **CPU Profiling** | JetBrains dotTrace, Visual Studio Diagnostic Tools, PerfView. | **`cProfile`** (Deterministic dev profiling) & **`py-spy`** (Zero-overhead sampling profiler cho production). |
| **Memory Profiling** | JetBrains dotMemory, Visual Studio Memory Profiler, SOS CLR extension. | **`tracemalloc`** (Standard library snapshot allocator), `memory_profiler`, `pympler`. |
| **Hiển thị trực quan** | Flame Graphs trong PerfView, dotTrace Timeline. | **`snakeviz`** (cho cProfile) và Flamegraph SVG tương tác từ **`py-spy`**. |
| **Kiểm thử tải (Load Testing)** | k6 (JS), NBomber (C#), BenchmarkDotNet (micro-benchmarking). | **`locust`** (Kịch bản kiểm thử hoàn toàn bằng Python, Web UI & Headless), `wrk`, `hey`. |
| **Kiểm soát N+1 Queries** | EF Core `Include()` / `ThenInclude()`, MiniProfiler, EF Core Query Interceptors. | SQLAlchemy 2.0 **`selectinload()`** & **`joinedload()`**, SQLAlchemy SQL echo, custom event listener query counter. |
| **Quản lý Database Pool** | ADO.NET Connection Pooling tích hợp sẵn (`MaxPoolSize`, `MinPoolSize` trong Connection String). | **SQLAlchemy QueuePool** với các tham số: `pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle`. |
| **JSON Serialization** | `System.Text.Json` với Source Generators (cực nhanh, zero-allocation). | **Pydantic v2 Core** (viết bằng Rust) kết hợp **`orjson`** (`ORJSONResponse` trong FastAPI). |

---

## 📖 Lý thuyết

### 1. Triết lý Tối ưu hóa: Measure, Don't Guess

Một trong những sai lầm phổ biến nhất của các kỹ sư là tự phán đoán xem phần nào của hệ thống đang chạy chậm. Nhà khoa học máy tính Donald Knuth từng phát biểu nổi tiếng:
> *"Premature optimization is the root of all evil (or at least most of it) in programming."*

Quy trình tối ưu hóa chuẩn Senior luôn tuân theo chu trình 4 bước:

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. MEASURE  │ ──► │  2. PROFILE  │ ──► │  3. OPTIMIZE │ ──► │  4. VERIFY   │
│ (Đo độ trễ,  │     │ (Tìm chính   │     │ (Áp dụng giải│     │ (Đối chiếu số│
│  RPS, RAM)   │     │  xác điểm nghẽn)   │  pháp kỹ thuật)    │  liệu đo lại)│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

1. **Measure**: Ghi nhận số liệu baseline trước khi sửa bất kỳ dòng code nào (ví dụ: Endpoint `/orders` đang có latency p95 = 450ms, RPS = 60).
2. **Profile**: Dùng công cụ chuyên dụng (py-spy, tracemalloc, SQL query logger) để xác định điểm nghẽn cổ chai (bottleneck) nằm ở đâu: I/O Database? CPU băm mật khẩu? Hay do tuần tự hóa JSON?
3. **Optimize**: Thực hiện thay đổi tập trung vào đúng 1-2 điểm nghẽn lớn nhất (theo nguyên lý Pareto 80/20).
4. **Verify**: Chạy lại kịch bản đo đạc cũ để chứng minh bằng con số cụ thể xem hiệu năng đã tăng bao nhiêu % và không phát sinh hồi quy (regression).

---

### 2. CPU Profiling: `cProfile` vs `py-spy`

#### 2.1 `cProfile` (Deterministic Profiling)
`cProfile` là thư viện chuẩn tích hợp sẵn trong CPython. Nó hoạt động theo cơ chế **Deterministic Profiling**: can thiệp vào máy ảo CPython để đếm chính xác từng lần hàm được gọi và ghi nhận thời gian thực thi.

Các thông số cốt lõi trong báo cáo `cProfile`:
- **`ncalls`**: Tổng số lần hàm được gọi.
- **`tottime`**: Tổng thời gian chạy bên trong chính hàm đó (không tính thời gian các hàm con mà nó gọi tới).
- **`cumtime`**: Tổng thời gian tích lũy từ lúc bắt đầu hàm cho tới khi hàm kết thúc (bao gồm toàn bộ thời gian của các hàm con).
- **`percall`**: Thời gian trung bình trên mỗi lần gọi (`tottime / ncalls` hoặc `cumtime / ncalls`).

*Lưu ý quan trọng*: Do phải hook vào mọi lần gọi hàm, `cProfile` tạo ra overhead đáng kể (làm chậm chương trình từ 2x đến 5x). Vì vậy, chỉ nên dùng `cProfile` trong môi trường phát triển (Development / Staging) hoặc Unit Benchmark.

#### 2.2 `py-spy` (Sampling Profiler cho Production)
`py-spy` là một công cụ mã nguồn mở viết bằng Rust. Nó hoạt động theo nguyên lý **Sampling Profiling** hoàn toàn độc lập từ bên ngoài (out-of-process):
- `py-spy` gắn vào tiến trình Python thông qua Process ID (`PID`) và đọc trực tiếp call stack từ không gian địa chỉ bộ nhớ của CPython với tần suất cao (ví dụ: 100 lần mỗi giây).
- **Ưu điểm vượt trội**: Không can thiệp bytecode, không cần khởi động lại ứng dụng, overhead cực kỳ thấp (< 1%–2% CPU), an toàn 100% để bật trực tiếp trên Kubernetes Pod đang phục vụ người dùng thực tế!
- Hỗ trợ xuất trực tiếp ra biểu đồ **Flame Graph SVG** tương tác: Chiều rộng của mỗi thanh đại diện cho tỷ lệ % thời gian CPU mà hàm đó chiếm dụng.

```bash
# Giám sát trực tiếp trên terminal như lệnh top:
py-spy top --pid 12345

# Ghi lại và xuất ra Flamegraph SVG trong vòng 30 giây:
py-spy record -o profile.svg --pid 12345 --duration 30
```

---

### 3. Memory Profiling với `tracemalloc`

Rò rỉ bộ nhớ (Memory Leak) trong Python thường xuất phát từ việc vô tình giữ tham chiếu lâu dài tới các đối tượng không còn sử dụng (ví dụ: lưu vào biến toàn cục, bộ nhớ đệm vô hạn không có TTL, hoặc các danh sách log tích lũy trong RAM).

Module `tracemalloc` là vũ khí đắc lực để truy lùng các khối bộ nhớ được cấp phát:
- `tracemalloc.start(n_frames)`: Bắt đầu theo dõi các khối phân bổ bộ nhớ với độ sâu stack trace.
- `snapshot = tracemalloc.take_snapshot()`: Chụp lại ảnh trạng thái bộ nhớ tại một thời điểm.
- `snapshot2.compare_to(snapshot1, 'lineno')`: So sánh sự biến động giữa 2 thời điểm, liệt kê chính xác file và dòng code nào đang chiếm dụng thêm nhiều byte RAM nhất.

---

### 4. Diệt triệt để N+1 Queries trong SQLAlchemy 2.0

Vấn đề N+1 Query là sát thủ số một giết chết hiệu năng của các hệ thống Backend sử dụng ORM.

#### 4.1 Bản chất vấn đề
Giả sử ta có bảng `User` (1) liên kết với bảng `Task` (N).
Nếu bạn query 100 users, sau đó trong vòng lặp bạn truy cập `user.tasks`:
- 1 câu query đầu tiên: `SELECT * FROM users LIMIT 100;`
- Khi lặp qua từng user, ORM phát thêm 100 câu query riêng biệt: `SELECT * FROM tasks WHERE user_id = ?;`
- **Tổng cộng**: 1 + 100 = 101 câu truy vấn đập vào Database chỉ để render một màn hình danh sách!

#### 4.2 Giải pháp Eager Loading trong SQLAlchemy 2.0

SQLAlchemy 2.0 cung cấp hai chiến lược nạp dữ liệu đón đầu (Eager Loading) cực kỳ mạnh mẽ:

| Kỹ thuật | Bản chất câu truy vấn SQL | Quan hệ tối ưu | Lưu ý quan trọng |
|---|---|---|---|
| **`selectinload`** | Phát ra đúng **2 câu truy vấn**: Câu 1 lấy danh sách bảng cha, Câu 2 dùng `WHERE parent_id IN (...)` để lấy toàn bộ bản ghi con. | **1-N** (One-to-Many) & **M-N** (Many-to-Many) | Rất tối ưu cho danh sách con dạng Collection. Không bị nhân bản dữ liệu trên đường truyền. |
| **`joinedload`** | Phát ra **1 câu truy vấn duy nhất** sử dụng mệnh đề `LEFT OUTER JOIN` gộp cả 2 bảng. | **N-1** (Many-to-One) & **1-1** (One-to-One) | Cực tốt cho việc lấy thực thể cha đơn lẻ. **Cảnh báo**: Nếu dùng `joinedload` trên nhiều quan hệ 1-N cùng lúc, Database sẽ sinh ra tích Descartes khổng lồ khiến RAM bùng nổ! |

```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

# 1. Truy vấn User kèm danh sách Tasks (Quan hệ 1-N) -> Dùng selectinload
stmt_users = select(User).options(selectinload(User.tasks))

# 2. Truy vấn Task kèm thông tin User người tạo (Quan hệ N-1) -> Dùng joinedload
stmt_tasks = select(Task).options(joinedload(Task.creator))
```

---

### 5. Tinh chỉnh Database Connection Pool

Khởi tạo kết nối TCP và thực hiện bắt tay xác thực (TLS/Auth Handshake) với Database là thao tác rất tốn kém (thường mất từ 10ms đến 50ms). Do đó, chúng ta luôn sử dụng Connection Pool để tái sử dụng các kết nối có sẵn.

Trong SQLAlchemy async với `create_async_engine`, các tham số production cốt lõi bao gồm:

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/taskflow_db",
    # Số kết nối cố định duy trì thường trực trong pool
    pool_size=20,
    # Số kết nối tối đa được phép mở thêm vượt mức khi có spike lưu lượng
    max_overflow=10,
    # Thời gian tối đa (giây) chờ đợi một kết nối rảnh trước khi ném ngoại lệ TimeoutError
    pool_timeout=30.0,
    # Tự động gửi lệnh ping nhẹ ("SELECT 1") kiểm tra kết nối còn sống trước khi cấp phát
    pool_pre_ping=True,
    # Tự động làm mới kết nối sau 1800 giây (30 phút) để tránh bị DB server ngắt ngầm
    pool_recycle=1800,
)
```

- **`pool_pre_ping=True`**: Đây là lá chắn sinh tử trên production. Nếu Database khởi động lại hoặc tường lửa giữa k8s pod và DB đóng các kết nối nhàn rỗi (idle sockets), việc không bật `pool_pre_ping` sẽ khiến người dùng nhận hàng loạt lỗi 500 (`OperationalError: connection unexpectedly closed`).

---

### 6. Tối ưu hóa Serialization với Pydantic v2 & `orjson`

Trong một Web API chịu tải cao, việc chuyển đổi qua lại giữa Python objects và chuỗi JSON (Serialization / Deserialization) chiếm từ 30% đến 50% thời gian xử lý CPU của mỗi request.

1. **Pydantic v2 Core (Rust)**:
   Khác với Pydantic v1 được viết bằng pure Python, Pydantic v2 có nhân `pydantic-core` được viết hoàn toàn bằng Rust. Các thao tác validation và serialization nhanh hơn từ 5x đến 17x.
   - Luôn sử dụng cú pháp mới: `Model.model_validate(obj)` thay cho `parse_obj()`.
   - Sử dụng `model.model_dump()` thay cho `.dict()`.
2. **`orjson`**:
   `orjson` là thư viện JSON nhanh nhất trong hệ sinh thái Python (viết bằng Rust). Nó hỗ trợ encode trực tiếp các kiểu dữ liệu phức tạp như `datetime`, `date`, `UUID`, `dataclasses`, `numpy` mà không cần hàm chuyển đổi thủ công.
   - Trong FastAPI, ta có thể kích hoạt `orjson` toàn cục bằng cách cấu hình `default_response_class=ORJSONResponse`.

---

## 💻 Ví dụ thực hành

### 1. Truy lùng và cô lập rò rỉ bộ nhớ bằng `tracemalloc`

Đoạn mã sau mô phỏng một dịch vụ xử lý sự kiện audit log bị rò rỉ RAM do vô tình lưu trữ các sự kiện vào biến danh sách toàn cục:

```python
import tracemalloc

# Biến toàn cục vô tình lưu trữ dữ liệu không giới hạn (Memory Leak)
_leaked_audit_log_store: list[dict[str, str | int]] = []


def process_audit_events(batch_id: int) -> None:
    for i in range(10_000):
        event = {
            "batch": batch_id,
            "event_id": i,
            "payload": f"User action details log message {i} for batch {batch_id}",
        }
        # Lỗi: Giữ tham chiếu vĩnh viễn khiến Garbage Collector không thể thu hồi
        _leaked_audit_log_store.append(event)


def main() -> None:
    tracemalloc.start(10)  # Ghi nhận stack trace 10 frames
    print("Chụp snapshot 1 (Baseline)...")
    snapshot_before = tracemalloc.take_snapshot()

    # Thực thi tác vụ nhiều đợt
    for batch in range(5):
        process_audit_events(batch)

    print("Chụp snapshot 2 (Sau khi chạy 5 batches)...")
    snapshot_after = tracemalloc.take_snapshot()

    # So sánh và lọc ra Top 3 dòng code chiếm dụng bộ nhớ tăng đột biến
    top_diffs = snapshot_after.compare_to(snapshot_before, "lineno")

    print("\n=== TOP CÁC DÒNG CODE GÂY TĂNG BỘ NHỚ ===")
    for stat in top_diffs[:3]:
        print(stat)

    # Hiển thị chi tiết stack trace của dòng gây leak nhiều nhất
    first_stat = top_diffs[0]
    print(f"\nChi tiết stacktrace gây leak tại: {first_stat.traceback.format()[-1]}")
    tracemalloc.stop()


if __name__ == "__main__":
    main()
```

---

### 2. Triệt phá N+1 Query trong FastAPI & SQLAlchemy 2.0

Dưới đây là một ví dụ hoàn chỉnh về cách khắc phục lỗi N+1 và cấu hình `ORJSONResponse` trong FastAPI:

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from sqlalchemy import ForeignKey, String, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)

# 1. Khai báo Models


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

    # Quan hệ 1-N với Task
    tasks: Mapped[list["TaskItem"]] = relationship(back_populates="project")


class TaskItem(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))

    project: Mapped[Project] = relationship(back_populates="tasks")


# 2. Pydantic Response Schemas


class TaskItemOut(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True


class ProjectWithTasksOut(BaseModel):
    id: int
    name: str
    tasks: list[TaskItemOut]

    class Config:
        from_attributes = True


# 3. Database Engine & Session setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# 4. Lifespan tạo seed data
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data
    async with async_session_factory() as session:
        p1 = Project(name="TaskFlow Core")
        p2 = Project(name="Analytics Engine")
        session.add_all([p1, p2])
        await session.flush()

        t1 = TaskItem(title="Setup CI/CD", project_id=p1.id)
        t2 = TaskItem(title="Write Unit Tests", project_id=p1.id)
        t3 = TaskItem(title="Design DB Schema", project_id=p2.id)
        session.add_all([t1, t2, t3])
        await session.commit()
    yield
    await engine.dispose()


# 5. Khởi tạo FastAPI với ORJSONResponse làm default response class
app = FastAPI(title="Optimized API", default_response_class=ORJSONResponse, lifespan=lifespan)


@app.get("/projects", response_model=list[ProjectWithTasksOut])
async def list_projects_optimized(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[Project]:
    # ✅ GIẢI PHÁP DIỆT N+1: Dùng selectinload nạp trước toàn bộ tasks trong đúng 2 câu SQL!
    stmt = select(Project).options(selectinload(Project.tasks)).order_by(Project.id)
    result = await session.scalars(stmt)
    return list(result.all())
```

---

### 3. Kịch bản kiểm thử tải bằng `locust`

File `locustfile.py` dưới đây mô phỏng hành vi của người dùng thực tế duyệt danh sách dự án và tạo mới công việc:

```python
# File: locustfile.py
import random
from locust import HttpUser, between, task


class TaskFlowLoadTestUser(HttpUser):
    # Thời gian nghỉ ngẫu nhiên giữa các request từ 0.5 đến 2.0 giây
    wait_time = between(0.5, 2.0)

    @task(3)  # Trọng số 3: Tần suất người dùng xem danh sách cao gấp 3 lần
    def view_projects(self) -> None:
        self.client.get("/projects", name="/projects [GET]")

    @task(1)  # Trọng số 1: Hành vi tạo mới
    def health_check(self) -> None:
        self.client.get("/health", name="/health [GET]")
```

Chạy kịch bản kiểm thử không cần giao diện (Headless mode) để tích hợp vào CI/CD:
```bash
locust -f locustfile.py --headless -u 100 -r 10 --run-time 1m --host http://localhost:8000
```
- `-u 100`: Giả lập 100 người dùng đồng thời (concurrent virtual users).
- `-r 10`: Ramp-up rate (mỗi giây tăng thêm 10 người dùng mới cho tới khi chạm mốc 100).
- `--run-time 1m`: Chạy kiểm thử liên tục trong 1 phút.

---

## ⚠️ Lỗi thường gặp

### 1. Dùng `cProfile` trực tiếp trên Production chịu tải
Nhiều kỹ sư chạy script profiling bằng `cProfile` hoặc bật middleware cProfile trên server production.
*Hậu quả*: Do cơ chế deterministic ghi nhận mọi stack frame, độ trễ API tăng gấp 3 đến 5 lần, làm nghẽn Event Loop và gây sập dịch vụ.
*Giải pháp*: Luôn dùng **`py-spy`** trên production vì đây là công cụ đọc bộ nhớ ngoài tiến trình không gây gián đoạn.

### 2. Lạm dụng `joinedload` cho nhiều quan hệ Một-Nhiều (1-N)
Khi cố gắng nạp cả danh sách `Order -> OrderItems` và `Order -> OrderLogs` bằng `joinedload`, câu lệnh SQL sinh ra:
```sql
SELECT * FROM orders 
LEFT JOIN order_items ON ... 
LEFT JOIN order_logs ON ...;
```
Nếu 1 order có 50 items và 50 logs, kết quả trả về từ database sẽ là $1 \times 50 \times 50 = 2,500$ dòng dữ liệu trùng lặp (Cartesian Explosion).
*Giải pháp*: Luôn dùng **`selectinload`** cho các tập hợp collection (1-N).

### 3. Cấu hình Connection Pool thiếu `pool_pre_ping=True`
Mặc định nếu không bật `pool_pre_ping`, khi kết nối TCP với PostgreSQL bị rớt (do tường lửa đóng idle connection hoặc DB restart), SQLAlchemy vẫn tin rằng kết nối còn tốt và trao cho request kế tiếp, dẫn tới lỗi nghiêm trọng:
`asyncpg.exceptions.ConnectionDoesNotExistError` hoặc `SSL connection has been closed unexpectedly`.

### 4. Đặt kích thước Connection Pool quá lớn
Nhiều người nghĩ đặt `pool_size=200` trên mỗi pod là tốt. Nếu ứng dụng scale lên 10 pods, tổng số kết nối mở tới PostgreSQL sẽ là $10 \times 200 = 2,000$ kết nối! Điều này làm PostgreSQL cạn kiệt RAM cho quy trình quản lý kết nối và gây từ chối dịch vụ. Hãy tính toán `pool_size` cẩn thận dựa trên `max_connections` của database chia đều cho số lượng pod tối đa.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Dùng `tracemalloc` phát hiện memory leak trong Batch Processing
Cho một hàm xử lý hàng loạt log entries giả lập. Viết một hàm kiểm tra tự động sử dụng `tracemalloc`:
1. Chụp snapshot trước và sau khi xử lý 20,000 log entries.
2. Xác định dòng code nào đang lưu trữ các chuỗi thừa thãi và in ra dung lượng RAM tăng thêm.
3. Tái cấu trúc lại code để giải phóng bộ nhớ ngay sau mỗi batch, chứng minh lượng RAM tăng thêm xấp xỉ 0 MB.

<details>
<summary>💡 Gợi ý</summary>

```python
import tracemalloc


class LogCollector:

    def __init__(self) -> None:
        self.cached_logs: list[str] = []

    def process_and_clear(self, records: list[str]) -> int:
        count = len(records)
        # Giả lập xử lý log...
        # Tái cấu trúc: Thay vì append vào cached_logs vĩnh viễn, xử lý xong thì dọn sạch
        return count


def test_no_leak() -> None:
    collector = LogCollector()
    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()

    for i in range(10):
        batch = [f"Audit event log entry #{j}" for j in range(2_000)]
        collector.process_and_clear(batch)

    snap2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    top_diffs = snap2.compare_to(snap1, "lineno")
    total_diff_kb = sum(stat.size_diff for stat in top_diffs) / 1024
    print(f"Tổng bộ nhớ chênh lệch: {total_diff_kb:.2f} KB")
    assert total_diff_kb < 500, "Phát hiện rò rỉ bộ nhớ vượt mức 500KB!"


if __name__ == "__main__":
    test_no_leak()
```
</details>

---

### Bài tập 2: Viết Pytest Fixture đếm số câu truy vấn SQL để diệt N+1 trong CI/CD
Tạo một cơ chế kiểm tra (Query Counter) trong SQLAlchemy:
1. Đăng ký event listener `before_cursor_execute` của SQLAlchemy Engine để đếm số lượng câu query thực thi trong một khối lệnh.
2. Viết context manager `assert_max_queries(session, max_queries=2)` kiểm tra xem đoạn mã có vượt quá số lượng câu query dự kiến hay không.
3. Viết test case chứng minh: Truy vấn 5 Projects kèm Tasks bằng `selectinload` chỉ tốn đúng 2 câu queries, trong khi lặp thông thường sẽ tốn 6 câu queries (N+1).

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

# Tái sử dụng Base, Project, TaskItem từ phần ví dụ trên...


@asynccontextmanager
async def assert_max_queries(
    session: AsyncSession, max_queries: int
) -> AsyncGenerator[None, None]:
    query_count = 0

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    sync_engine = session.bind.sync_engine  # Lấy underlying sync engine
    event.listen(sync_engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield
    finally:
        event.remove(sync_engine, "before_cursor_execute", before_cursor_execute)
        assert query_count <= max_queries, (
            f"Vượt quá số lượng queries! Thực thi: {query_count}, Tối đa cho phép: {max_queries}"
        )


async def run_query_test():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        # Seed 3 projects
        p1 = Project(name="P1")
        p2 = Project(name="P2")
        session.add_all([p1, p2])
        await session.commit()

        # Kiểm tra: selectinload chỉ được phép phát đúng 2 queries (1 cho Projects, 1 cho Tasks)
        async with assert_max_queries(session, max_queries=2):
            stmt = select(Project).options(selectinload(Project.tasks))
            projects = (await session.scalars(stmt)).all()
            for p in projects:
                _ = len(p.tasks)

        print("✅ Thành công: Đoạn code hoàn toàn không bị N+1!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_query_test())
```
</details>

---

### Bài tập 3: Tối ưu hóa serialization cho API danh bạ 10,000 bản ghi
Viết một endpoint FastAPI trả về danh sách 10,000 đối tượng khách hàng (gồm: `id`, `name`, `email`, `created_at`, `balance`).
Yêu cầu:
1. So sánh thời gian phản hồi giữa phản hồi JSON mặc định của FastAPI (`JSONResponse`) và phản hồi tối ưu bằng `ORJSONResponse`.
2. Đo lường kích thước payload và thời gian serialization, chứng minh `ORJSONResponse` đạt tốc độ cải thiện tối thiểu 2x.

<details>
<summary>💡 Gợi ý</summary>

```python
from datetime import datetime, timezone
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse, ORJSONResponse
from pydantic import BaseModel

app = FastAPI()


class CustomerSchema(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    balance: float


# Dữ liệu mẫu 10,000 records
sample_data = [
    CustomerSchema(
        id=i,
        name=f"Customer Name {i}",
        email=f"customer_{i}@example.com",
        created_at=datetime.now(timezone.utc),
        balance=1250.75 + i,
    )
    for i in range(10_000)
]
raw_dicts = [c.model_dump() for c in sample_data]


@app.get("/customers-standard", response_class=JSONResponse)
def get_customers_standard():
    return raw_dicts


@app.get("/customers-orjson", response_class=ORJSONResponse)
def get_customers_orjson():
    return raw_dicts


# Benchmark độc lập hàm encode:
def benchmark_json():
    import json
    import orjson

    start = time.perf_counter()
    _ = json.dumps(raw_dicts, default=str)
    t_std = time.perf_counter() - start

    start = time.perf_counter()
    _ = orjson.dumps(raw_dicts)
    t_or = time.perf_counter() - start

    print(f"Standard json.dumps : {t_std:.4f}s")
    print(f"orjson.dumps        : {t_or:.4f}s (Tăng tốc: {t_std / t_or:.1f}x)")


if __name__ == "__main__":
    benchmark_json()
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi hiểu rõ chu trình 4 bước tối ưu hóa: *Measure → Profile → Optimize → Verify* và nguyên tắc "đo đạc, không phỏng đoán".
- [ ] Tôi biết khi nào nên dùng `cProfile` (môi trường dev) và khi nào dùng `py-spy` (sampling trực tiếp trên production với flamegraph).
- [ ] Tôi biết cách dùng `tracemalloc` để chụp snapshot và tìm chính xác dòng code gây tăng bộ nhớ bất thường.
- [ ] Tôi có khả năng viết kịch bản Locust bằng Python và phân tích các chỉ số RPS, latency p95/p99.
- [ ] Tôi giải thích được sự khác nhau giữa `selectinload` và `joinedload` trong SQLAlchemy 2.0 và biết cách ngăn ngừa bùng nổ Cartesian Product.
- [ ] Tôi nắm vững các thông số cấu hình Connection Pool (`pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle`).
- [ ] Tôi biết cách tích hợp `orjson` và `ORJSONResponse` vào FastAPI để tăng tốc serialization.

---

## 📚 Đọc thêm

- [py-spy GitHub Repository: Sampling profiler for Python programs](https://github.com/benfred/py-spy)
- [SQLAlchemy 2.0 Documentation: Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [SQLAlchemy 2.0 Documentation: Engine Configuration and Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Locust Official Documentation: An open-source load testing tool](https://docs.locust.io/en/stable/)
- [orjson GitHub Repository: Fast, correct Python JSON library](https://github.com/ijl/orjson)
- [Tiếp theo: Bài 03 – Caching với Redis](./03-caching-redis.md)

<!-- nav:bottom -->
---

[⬅️ Python internals & concurrency](./01-python-internals-concurrency.md) | [📚 Mục lục Senior](./README.md) | [Caching với Redis ➡️](./03-caching-redis.md)
<!-- /nav:bottom -->
