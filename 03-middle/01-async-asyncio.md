<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 01
<!-- /nav:top -->

# Async & asyncio

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành Level 02 Junior.

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Thấu hiểu bản chất kiến trúc **Event Loop đơn luồng** (single-threaded event loop) trong Python và cơ chế Non-blocking I/O dựa trên hệ thống multiplexing (epoll trên Linux, kqueue trên macOS).
- Phân biệt triệt để mô hình **ThreadPool đa luồng** của .NET CLR và mô hình **Cooperative Multitasking** của Python `asyncio`.
- Nắm vững vòng đời của một **Coroutine**: tại sao gọi hàm `async def` chỉ tạo ra một `coroutine object` ở trạng thái "ngủ" và không hề tự động chạy như `Task` trong C#.
- Làm chủ mô hình **Structured Concurrency** hiện đại trong Python 3.11+ thông qua **`asyncio.TaskGroup`**, so sánh trực quan với `Task.WhenAll` kết hợp `CancellationTokenSource` trong C#.
- Hiểu rõ rủi ro rò rỉ tác vụ (orphan tasks / unhandled exceptions) khi sử dụng phương thức cũ `asyncio.gather()`.
- Nằm lòng **Quy tắc vàng trong FastAPI**: phân biệt bản chất thực thi giữa endpoint khai báo bằng `async def` (chạy trên Event Loop chính) và `def` thông thường (chạy trên worker thread pool).
- Biết cách chuyển đổi và offload các tác vụ đồng bộ (blocking I/O hoặc CPU-bound) sang thread pool an toàn bằng **`asyncio.to_thread`**.

---

## 🔁 So sánh với C# / ASP.NET

Đối với lập trình viên C#, từ khóa `async` và `await` đã quá quen thuộc từ thời C# 5.0 (.NET Framework 4.5). Tuy nhiên, bên dưới nắp ca-pô, runtime của .NET và runtime của Python (CPython) vận hành cơ chế bất đồng bộ theo hai triết lý hoàn toàn khác biệt:

| Khái niệm / Cơ chế | C# / .NET CLR | Python / `asyncio` |
|---|---|---|
| **Mô hình luồng (Threading Model)** | Đa luồng thật sự (Multi-threaded). Khi một `Task` bắt đầu, nó thường được dispatch lên **ThreadPool** (`System.Threading.ThreadPool`). | **Đơn luồng (Single-threaded Event Loop)**. Mọi coroutine chia sẻ chung một luồng OS duy nhất trong tiến trình. |
| **Tính chất khởi chạy (Hot vs Cold)** | **"Hot" Task**: Ngay khi bạn gọi hàm async hoặc `Task.Run(...)`, tác vụ đã lập tức được đưa vào hàng đợi ThreadPool và bắt đầu thực thi ngầm. | **"Cold" Coroutine**: Gọi `coro = fetch_data()` **hoàn toàn chưa chạy gì cả**. Nó chỉ trả về một `coroutine object`. Phải có `await coro` hoặc `asyncio.create_task(coro)` thì coroutine mới được nạp vào Event Loop. |
| **Đa nhiệm (Multitasking)** | Preemptive (Hệ điều hành / runtime có quyền ngắt luồng đang chạy để chuyển sang luồng khác). | Cooperative (Bắt tay cộng tác: Một coroutine chỉ nhường quyền điều khiển khi nó chủ động gặp từ khóa `await`). |
| **Chạy đồng thời nhiều tác vụ** | `await Task.WhenAll(task1, task2)` | `async with asyncio.TaskGroup() as tg:` (Python 3.11+) hoặc `asyncio.gather(coro1, coro2)`. |
| **Hủy tác vụ (Cancellation)** | Truyền tường minh `CancellationToken` và gọi `token.ThrowIfCancellationRequested()`. | Runtime ném ngoại lệ `asyncio.CancelledError` trực tiếp vào coroutine tại vị trí `await` khi gọi `task.cancel()`. |
| **Gọi mã đồng bộ / Blocking I/O** | `await Task.Run(() => LongRunningSyncMethod())` | `await asyncio.to_thread(long_running_sync_method, *args)` |
| **Tác động khi gọi hàm chặn (Blocking)** | Chỉ làm nghẽn một worker thread trong ThreadPool, CLR có thể tự động co giãn thêm thread mới. | **Làm đóng băng toàn bộ Event Loop!** Mọi request khác của toàn bộ server đều bị tê liệt cho tới khi hàm đồng bộ đó chạy xong. |

---

## 📖 Lý thuyết

### 1. Bản chất Event Loop đơn luồng trong Python

Hãy tưởng tượng Event Loop giống như một người bồi bàn duy nhất trong một quán ăn:
- Bồi bàn đến bàn số 1, ghi đơn món ăn rồi chuyển vào bếp (bắt đầu một tác vụ I/O như truy vấn Database hoặc gọi HTTP API).
- Trong khi bếp đang nấu (I/O đang chờ phản hồi từ mạng/đĩa cứng), bồi bàn **không đứng đợi một chỗ**. Người bồi bàn ngay lập tức đi sang bàn số 2 để tiếp nhận order của khách hàng tiếp theo.
- Khi chuông nhà bếp reo báo món ăn bàn số 1 đã nấu xong (I/O hoàn tất), bồi bàn quay lại bưng đĩa thức ăn lên bàn số 1.

```text
┌──────────────────────────────────────────────────────────────┐
│                    PYTHON EVENT LOOP                         │
│                                                              │
│      ┌────────────┐                                          │
│  ┌───┤ Task 1     │ (Chạy tới await fetch() -> nhường quyền) │
│  │   └────────────┘                                          │
│  │   ┌────────────┐                                          │
│  │   │ Task 2     │ (Tiếp quản Event Loop -> xử lý dữ liệu)  │
│  │   └────────────┘                                          │
│  │                                                           │
│  │   OS Kernel Multiplexing (epoll / kqueue / IOCP)          │
│  └──► Socket I/O đang chờ phản hồi...                        │
│       ├── DB Query (PostgreSQL)                              │
│       └── External API (HTTP request)                        │
└──────────────────────────────────────────────────────────────┘
```

Vì chỉ có **một luồng duy nhất**, nếu tại bàn số 1 bồi bàn quyết định đứng gọt một củ khoai tây nặng nhọc kéo dài 5 giây (`time.sleep(5)` hoặc vòng lặp CPU 100%), **toàn bộ quán ăn phải đứng hình**: không ai được phục vụ, không đơn hàng nào được ghi!

### 2. Coroutine Object vs Task: Vòng đời và sự khác biệt cốt tử

Đây là cạm bẫy lớn nhất khiến nhiều kỹ sư C# bỡ ngỡ khi bước sang Python:

Trong C#:
```csharp
// Trong C#, Task bắt đầu chạy ngầm ngay thời điểm này!
Task<string> task = FetchFromDatabaseAsync();
DoSomethingElse();
string result = await task;
```

Trong Python:
```python
async def fetch_data() -> str:
    return "data"


# CHÚ Ý: Dòng này KHÔNG THỰC THI fetch_data!
# Nó chỉ trả về một Coroutine Object đang nằm yên trong RAM:
coro = fetch_data()
print(type(coro))  # <class 'coroutine'>
```

Để coroutine thực sự chạy, bạn có hai lựa chọn:

1. **Tuần tự (Inline execution)**: `await coro`
   - Coroutine hiện tại tạm dừng cho đến khi `coro` hoàn thành.
2. **Đồng thời (Concurrent execution)**: `task = asyncio.create_task(coro)`
   - Coroutine được bao bọc vào một `asyncio.Task`, đăng ký vào Event Loop để sẵn sàng chạy đồng thời cùng các task khác ngay khi có cơ hội nhường quyền.

### 3. Structured Concurrency với `asyncio.TaskGroup` (Python 3.11+)

Trong các phiên bản Python trước 3.11, lập trình viên thường dùng `asyncio.gather()`:
```python
# Cách tiếp cận cũ: asyncio.gather
results = await asyncio.gather(task1(), task2(), task3())
```

**Nhược điểm chí mạng của `asyncio.gather()`:**
Nếu `task1` bị lỗi ném ngoại lệ, `asyncio.gather()` sẽ lập tức raise ngoại lệ đó ra ngoài. Tuy nhiên, `task2` và `task3` **vẫn tiếp tục chạy ngầm trong Event Loop** mà không ai quản lý hay hủy bỏ chúng. Chúng biến thành các "tác vụ mồ côi" (orphan tasks), gây lãng phí tài nguyên, rò rỉ kết nối database, hoặc ghi đè dữ liệu sai lệch.

**Chuẩn hiện đại: `asyncio.TaskGroup`**
Từ Python 3.11, Python giới thiệu chuẩn **Structured Concurrency** thông qua Context Manager `asyncio.TaskGroup`:

```python
import asyncio


async def fetch_user(user_id: int) -> dict[str, str]:
    await asyncio.sleep(0.1)
    return {"id": str(user_id), "name": f"User {user_id}"}


async def fetch_orders(user_id: int) -> list[str]:
    await asyncio.sleep(0.2)
    return ["Order #1", "Order #2"]


async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        # tg.create_task tự động quản lý vòng đời của task trong group
        task1 = tg.create_task(fetch_user(42))
        task2 = tg.create_task(fetch_orders(42))

    # Khi thoát khỏi khối `async with`, CẢ HAI task đều đảm bảo đã kết thúc!
    print("User:", task1.result())
    print("Orders:", task2.result())
```

**Nguyên lý an toàn của `TaskGroup`:**
- Khi **bất kỳ task con nào ném ra ngoại lệ**, `TaskGroup` sẽ **tự động phát tín hiệu hủy (`cancel()`) toàn bộ các task con còn lại** trong group.
- `TaskGroup` đợi cho tất cả các task hoàn tất việc dọn dẹp (cleanup).
- Nếu có lỗi, nó gom toàn bộ các ngoại lệ lại và ném ra một **`ExceptionGroup`** duy nhất. Cơ chế này hoàn toàn tương đương với việc bạn truyền chung một `CancellationTokenSource` vào một danh sách các Task trong C# và gọi `Task.WhenAll`.

### 4. Quy tắc vàng trong FastAPI: `async def` vs `def`

FastAPI xử lý hàm endpoint theo hai cách thức đối lập dựa vào cách bạn khai báo từ khóa:

```text
Request tới ──► Endpoint khai báo là 'async def'?
                 ├── YES ──► Chạy trực tiếp trên Main Event Loop
                 │           (Yêu cầu: 100% Non-blocking, cấm tuyệt đối time.sleep / sync driver)
                 │
                 └── NO (def thông thường) ──► Offload sang AnyIO Worker ThreadPool
                                              (An toàn cho sync blocking I/O: requests, I/O đĩa)
```

#### Quy tắc 1: Trong `async def`, KHÔNG BAO GIỜ gọi mã chặn (blocking code)
Nếu bạn viết:
```python
# SAI LẦM TAI HẠI:
@app.get("/bad-endpoint")
async def bad_endpoint():
    time.sleep(5)  # ❌ Chặn toàn bộ Event Loop trong 5 giây!
    return {"status": "ok"}
```
Trong 5 giây đó, **không một client nào khác trên thế giới có thể kết nối hay nhận phản hồi** từ server FastAPI của bạn, dù họ chỉ gọi endpoint `/health` đơn giản!

#### Quy tắc 2: Dùng `asyncio.to_thread` khi cần gọi mã đồng bộ trong hàm async
Nếu bạn đang ở trong hàm `async def` và buộc phải gọi một thư viện đồng bộ (ví dụ: băm mật khẩu CPU nặng, đọc file qua thư viện sync cũ, gọi API bằng SDK của bên thứ ba chưa hỗ trợ async):

```python
import asyncio
import time
from fastapi import FastAPI

app = FastAPI()


def heavy_cpu_computation(x: int) -> int:
    # Hàm đồng bộ tiêu tốn CPU hoặc blocking I/O
    time.sleep(2)
    return x * 42


@app.get("/good-endpoint")
async def good_endpoint() -> dict[str, int]:
    # ✅ Đẩy hàm đồng bộ sang worker thread riêng, Event Loop vẫn tự do phục vụ request khác!
    result = await asyncio.to_thread(heavy_cpu_computation, 10)
    return {"result": result}
```

#### Quy tắc 3: Dùng `def` thông thường nếu endpoint thuần túy gọi thư viện đồng bộ
Nếu toàn bộ endpoint của bạn chỉ sử dụng các thư viện sync (như `requests`, `psycopg2` đồng bộ):
```python
@app.get("/sync-endpoint")
def sync_endpoint() -> dict[str, str]:
    # ✅ FastAPI tự động chuyển hàm này chạy trên AnyIO ThreadPool riêng biệt!
    # Event loop chính hoàn toàn không bị ảnh hưởng.
    time.sleep(1)
    return {"message": "Executed safely in worker thread"}
```

---

## 💻 Ví dụ thực hành

### Ví dụ 1: Structured Concurrency tải song song dữ liệu với `asyncio.TaskGroup`

Kịch bản: Xây dựng Dashboard tổng hợp thông tin dự án gồm thông tin chung, danh sách thành viên và các task gần nhất.

```python
import asyncio
from dataclasses import dataclass


@dataclass
class ProjectOverview:
    title: str
    member_count: int
    recent_tasks: list[str]


async def fetch_project_info(project_id: int) -> str:
    await asyncio.sleep(0.15)  # Giả lập I/O database
    return f"TaskFlow Core v{project_id}"


async def fetch_members(project_id: int) -> int:
    await asyncio.sleep(0.10)  # Giả lập I/O database
    return 8


async def fetch_recent_tasks(project_id: int) -> list[str]:
    await asyncio.sleep(0.20)  # Giả lập I/O database
    return ["Setup Alembic", "Implement JWT", "Dockerize"]


async def get_project_dashboard(project_id: int) -> ProjectOverview:
    # Chạy đồng thời cả 3 tác vụ I/O, thời gian thực thi chỉ bằng max(0.15, 0.10, 0.20) = ~0.20s
    async with asyncio.TaskGroup() as tg:
        info_task = tg.create_task(fetch_project_info(project_id))
        members_task = tg.create_task(fetch_members(project_id))
        tasks_task = tg.create_task(fetch_recent_tasks(project_id))

    # Cả 3 tasks đã hoàn thành an toàn khi ra khỏi context manager
    return ProjectOverview(
        title=info_task.result(),
        member_count=members_task.result(),
        recent_tasks=tasks_task.result(),
    )


async def main() -> None:
    dashboard = await get_project_dashboard(101)
    print(f"Project: {dashboard.title}")
    print(f"Members: {dashboard.member_count}")
    print(f"Tasks: {', '.join(dashboard.recent_tasks)}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Ví dụ 2: Xử lý ngoại lệ và tự động hủy task trong `TaskGroup`

Minh họa cơ chế an toàn: Khi 1 task con gặp sự cố, `TaskGroup` lập tức hủy các task còn lại, ngăn ngừa tác vụ chạy rông.

```python
import asyncio


async def reliable_service() -> str:
    try:
        print("[Service 1] Bắt đầu xử lý...")
        await asyncio.sleep(2.0)  # Cần 2 giây
        print("[Service 1] Hoàn thành!")
        return "Service 1 OK"
    except asyncio.CancelledError:
        print("[Service 1] Nhận tín hiệu hủy (Cancelled)! Tiến hành dọn dẹp tài nguyên...")
        raise  # Bắt buộc re-raise CancelledError


async def failing_service() -> str:
    print("[Service 2] Bắt đầu xử lý...")
    await asyncio.sleep(0.3)  # Lỗi sau 0.3 giây
    print("[Service 2] Gặp lỗi nghiêm trọng!")
    raise ConnectionResetError("Không thể kết nối máy chủ thanh toán!")


async def run_resilient_flow() -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(reliable_service())
            tg.create_task(failing_service())
    except* ConnectionResetError as eg:
        # Python 3.11 cú pháp except* xử lý ExceptionGroup
        print(f"Bắt được ngoại lệ nhóm: {eg.exceptions[0]}")


if __name__ == "__main__":
    asyncio.run(run_resilient_flow())
```

### Ví dụ 3: Xử lý file nặng hoặc CPU-bound trong FastAPI an toàn

```python
import asyncio
import hashlib
from typing import Annotated
from fastapi import FastAPI, File, UploadFile

app = FastAPI(title="Async CPU Offloading Demo")


def calculate_sha256_blocking(file_bytes: bytes) -> str:
    """Hàm băm CPU-bound đồng bộ thuần túy."""
    hasher = hashlib.sha256()
    # Giả lập xử lý khối lượng tính toán lớn
    hasher.update(file_bytes)
    return hasher.hexdigest()


@app.post("/files/checksum")
async def compute_file_checksum(file: Annotated[UploadFile, File()]) -> dict[str, str]:
    # 1. Đọc nội dung file bất đồng bộ qua non-blocking I/O
    content = await file.read()

    # 2. Chuyển phép toán tính toán SHA-256 CPU-bound sang AnyIO ThreadPool
    # Giữ cho Event Loop chính luôn thanh thoát phục vụ hàng ngàn kết nối khác
    checksum = await asyncio.to_thread(calculate_sha256_blocking, content)

    return {
        "filename": file.filename or "unknown",
        "sha256": checksum,
    }
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên từ khóa `await` khi gọi hàm bất đồng bộ
```python
async def get_user_balance(user_id: int) -> int:
    await asyncio.sleep(0.01)
    return 1000


async def checkout() -> None:
    # ❌ SAI: Không có await, balance lúc này là một coroutine object!
    balance = get_user_balance(42)
    if balance > 500:  # TypeError: '>' not supported between instances of 'coroutine' and 'int'
        print("Đủ tiền thanh toán")
```
Khi chạy đoạn code trên, Python sẽ cảnh báo:
`RuntimeWarning: coroutine 'get_user_balance' was never awaited`.
**Cách khắc phục:** Luôn luôn đặt `await` trước mỗi lời gọi coroutine: `balance = await get_user_balance(42)`.

### 2. Sử dụng thư viện đồng bộ (blocking) trong hàm `async def` của FastAPI
Nhiều kỹ sư quen tay import thư viện HTTP đồng bộ `requests` hoặc `time.sleep()` trong endpoint `async def`:
```python
import requests  # ❌ Thư viện đồng bộ blocking


@app.get("/weather")
async def get_weather():
    # ❌ SAI: requests.get là hàm chặn đồng bộ, làm nghẽn toàn bộ Event Loop!
    resp = requests.get("https://api.weather.com/data")
    return resp.json()
```
**Cách khắc phục:**
1. Chuyển sang thư viện HTTP bất đồng bộ chuẩn: **`httpx.AsyncClient`**.
2. Hoặc nếu bắt buộc dùng `requests`, hãy đổi endpoint thành hàm `def` thông thường: `def get_weather(): ...`.

### 3. Nuốt ngoại lệ `asyncio.CancelledError`
Khi một task bị hủy (bởi timeout hoặc do `TaskGroup` hủy khi có lỗi xảy ra ở task khác), Event Loop sẽ inject ngoại lệ `asyncio.CancelledError` vào coroutine.
```python
# ❌ SAI: Bắt chước Exception và nuốt mất tín hiệu hủy!
try:
    await asyncio.sleep(10)
except Exception:  # Lưu ý: Từ Python 3.8+, CancelledError kế thừa từ BaseException
    pass

# Nguy hiểm hơn nếu vô tình bắt BaseException:
try:
    await asyncio.sleep(10)
except BaseException:
    print("Bỏ qua mọi lỗi!")  # TaskGroup không thể dừng task này lại được nữa!
```
**Cách khắc phục:** Nếu cần bắt lỗi dọn dẹp, luôn re-raise `CancelledError`:
```python
try:
    await perform_work()
except asyncio.CancelledError:
    await cleanup_resources()
    raise  # BẮT BUỘC re-raise để runtime hoàn tất việc hủy
```

### 4. Quên giữ tham chiếu (Reference) tới background task
Khi tạo task chạy ngầm bằng `asyncio.create_task()`, nếu không lưu lại biến tham chiếu, bộ thu gom rác (Garbage Collector) của Python có thể giải phóng đối tượng Task ngay giữa chừng khi nó chưa kịp chạy xong!
```python
# ❌ RỦI RO: Không lưu biến task, có thể bị Garbage Collector thu hồi bất ngờ!
asyncio.create_task(send_notification_email())

# ✅ AN TOÀN: Giữ tham chiếu trong một tập hợp (background_tasks set)
background_tasks: set[asyncio.Task[None]] = set()


def fire_and_forget(coro) -> None:
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
```
*(Trong FastAPI, bạn nên ưu tiên sử dụng `fastapi.BackgroundTasks` để framework tự quản lý).*

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Crawler tải song song có giới hạn Concurrency bằng `Semaphore`
Viết chương trình Python tải nội dung mô phỏng từ danh sách 10 URLs.
Yêu cầu:
1. Sử dụng `asyncio.TaskGroup` để quản lý các tác vụ tải đồng thời.
2. Sử dụng `asyncio.Semaphore(3)` để đảm bảo tại một thời điểm **tối đa chỉ có 3 URLs** được xử lý đồng thời (tránh làm quá tải server đích).
3. Đo tổng thời gian thực hiện để chứng minh tính song song.

<details>
<summary>💡 Gợi ý</summary>

Sử dụng cấu trúc `async with sem:` bên trong hàm fetch:
```python
import asyncio
import time


async def fetch_url(url: str, sem: asyncio.Semaphore) -> str:
    async with sem:
        print(f"Bắt đầu tải: {url}")
        await asyncio.sleep(0.5)  # Giả lập I/O
        print(f"Xong: {url}")
        return f"Data from {url}"


async def main() -> None:
    urls = [f"https://api.example.com/item/{i}" for i in range(10)]
    sem = asyncio.Semaphore(3)
    start = time.perf_counter()

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_url(u, sem)) for u in urls]

    results = [t.result() for t in tasks]
    print(f"Tổng số kết quả: {len(results)} trong {time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
```
</details>

---

### Bài tập 2: Cơ chế Timeout và Fallback an toàn cho Microservice
Viết hàm `get_price_with_timeout(supplier_name: str, delay: float, fallback_price: float) -> float`.
Yêu cầu:
1. Sử dụng hàm `asyncio.timeout(1.0)` (chuẩn Python 3.11+) để giới hạn thời gian chờ phản hồi tối đa là 1.0 giây.
2. Nếu dịch vụ phản hồi kịp, trả về giá trị thực tế.
3. Nếu quá 1.0 giây (`TimeoutError`), in ra cảnh báo và trả về `fallback_price` mà không làm sập luồng điều khiển của ứng dụng.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio


async def query_supplier_api(supplier: str, delay: float) -> float:
    await asyncio.sleep(delay)
    return 149.99


async def get_price_with_timeout(supplier: str, delay: float, fallback_price: float) -> float:
    try:
        async with asyncio.timeout(1.0):
            return await query_supplier_api(supplier, delay)
    except TimeoutError:
        print(f"Cảnh báo: Nhà cung cấp {supplier} phản hồi quá lâu (>1.0s). Dùng fallback!")
        return fallback_price
```
</details>

---

### Bài tập 3: Tối ưu hóa Endpoint FastAPI xử lý file nén
Hãy phân tích và sửa lại đoạn code sau đây trong FastAPI để không làm tắc nghẽn Event Loop:
```python
# Đoạn code lỗi ban đầu cần sửa:
import time
import zipfile
from fastapi import FastAPI, UploadFile

app = FastAPI()


@app.post("/extract-zip")
async def extract_zip(file: UploadFile):
    content = await file.read()
    # Giả lập giải nén file ZIP đồng bộ tốn nhiều CPU và I/O đĩa
    time.sleep(3)
    return {"status": "extracted", "size": len(content)}
```

<details>
<summary>💡 Gợi ý</summary>

Tách logic giải nén đồng bộ thành một hàm riêng biệt và đẩy sang `asyncio.to_thread`:
```python
import asyncio
import time
from fastapi import FastAPI, UploadFile

app = FastAPI()


def process_zip_sync(content_bytes: bytes) -> int:
    # Logic giải nén file ZIP đồng bộ nặng nhọc
    time.sleep(3)
    return len(content_bytes)


@app.post("/extract-zip")
async def extract_zip(file: UploadFile) -> dict[str, str | int]:
    content = await file.read()
    # Đẩy sang worker thread
    size = await asyncio.to_thread(process_zip_sync, content)
    return {"status": "extracted", "size": size}
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được sự khác nhau căn bản giữa Event Loop đơn luồng của `asyncio` và ThreadPool đa luồng của .NET CLR.
- [ ] Tôi hiểu rõ tại sao gọi `coro = my_func()` trong Python không kích hoạt coroutine chạy ngay như `Task` trong C#.
- [ ] Tôi biết cách sử dụng `asyncio.TaskGroup` trong Python 3.11+ để áp dụng Structured Concurrency và hiểu tại sao nó an toàn hơn `asyncio.gather()`.
- [ ] Tôi nắm vững Quy tắc vàng trong FastAPI: không gọi blocking code trong `async def` và biết cách dùng `asyncio.to_thread` khi cần thiết.
- [ ] Tôi phân biệt được khi nào nên khai báo endpoint là `async def` và khi nào nên dùng `def` thông thường trong FastAPI.
- [ ] Tôi hiểu cách thức xử lý ngoại lệ `asyncio.CancelledError` và không vô tình nuốt mất tín hiệu hủy tác vụ.

---

## 📚 Đọc thêm

- [Python Official Documentation – asyncio: Asynchronous I/O](https://docs.python.org/3/library/asyncio.html)
- [Python 3.11: TaskGroup and ExceptionGroup Specification (PEP 654)](https://peps.python.org/pep-0654/)
- [FastAPI Official Guide: Concurrency and async / await](https://fastapi.tiangolo.com/async/)
- [Tiếp theo: Bài 02 – SQLAlchemy 2.0 ORM](./02-sqlalchemy-orm.md)

<!-- nav:bottom -->
---

[⬅️ Middle](./README.md) | [📚 Mục lục Middle](./README.md) | [SQLAlchemy 2.0 ORM ➡️](./02-sqlalchemy-orm.md)
<!-- /nav:bottom -->
