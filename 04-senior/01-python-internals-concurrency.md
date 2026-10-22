<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 01
<!-- /nav:top -->

# Python internals & concurrency

> ⏱️ Thời lượng: ~4.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành Level 03 (đặc biệt là [Async & asyncio](../03-middle/01-async-asyncio.md)).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Thấu hiểu kiến trúc bộ nhớ CPython**: Nắm vững cấu trúc gốc `PyObject`, cơ chế đếm tham chiếu (Reference Counting), và cách hoạt động của bộ thu gom rác chu trình (Cyclic Garbage Collector) qua các thế hệ Gen 0, 1, 2.
- **Tối ưu hóa bộ nhớ với `__slots__`**: Hiểu rõ sự khác biệt giữa từ điển động `__dict__` và mảng con trỏ cố định của `__slots__`, giúp tiết kiệm từ 40% đến 70% RAM khi xử lý hàng triệu đối tượng.
- **Giải mã bản chất Global Interpreter Lock (GIL)**: Hiểu vì sao Python có GIL, cơ chế thread-switch, tại sao đa luồng (`threading`) không thể tận dụng đa nhân cho CPU-bound nhưng lại giải phóng lock rất tốt cho I/O-bound.
- **Nắm bắt bước chuyển mình Free-threaded Python (PEP 703)**: Hiểu cấu trúc Python 3.13t+ (no-GIL), cơ chế Biased Reference Counting, Immortal Objects và bộ cấp phát mimalloc.
- **Làm chủ Ma trận Concurrency**: Phân biệt và ứng dụng chuẩn xác 3 mô hình: `asyncio` (Non-blocking I/O), `ThreadPoolExecutor` (Blocking I/O / C-extensions), và `ProcessPoolExecutor` (CPU-bound song song thực thụ).
- **Offload tác vụ chuẩn mực trong FastAPI**: Đẩy các tác vụ nặng ra khỏi Event Loop mà không làm nghẽn server bằng `asyncio.to_thread` và `loop.run_in_executor` kết hợp vòng đời `lifespan`.

---

## 🔁 So sánh với C# / ASP.NET

Đối với kỹ sư C# / .NET, cơ chế vận hành của Common Language Runtime (CLR) đã trở thành phản xạ tự nhiên: CLR biên dịch JIT ra mã máy gốc, quản lý bộ nhớ hoàn toàn bằng Generational Tracing Garbage Collector, và hỗ trợ đa luồng native thật sự (mỗi `Thread` của C# ánh xạ 1:1 với luồng của hệ điều hành và chạy song song trên nhiều CPU cores). 

Khi chuyển sang CPython, bạn sẽ gặp những khác biệt mang tính nền tảng sau:

| Tiêu chí | C# / .NET Runtime (CLR) | Python (CPython 3.12 / 3.13) |
|---|---|---|
| **Cơ chế thực thi** | Trình biên dịch JIT (Just-In-Time) biên dịch CIL bytecode thành machine code gốc của CPU. | Trình thông dịch (Bytecode Interpreter) duyệt qua từng bytecode opcode trong vòng lặp `_PyEval_EvalFrameDefault`. |
| **Cấu trúc đối tượng cơ bản** | `System.Object`: 8 bytes MethodTable pointer + 8 bytes SyncBlock index (trên 64-bit OS) + payload. | `PyObject`: 8 bytes `ob_refcnt` + 8 bytes `ob_type` + payload (tối thiểu 16 bytes overhead cho mọi biến). |
| **Thu gom bộ nhớ chính** | **Tracing Garbage Collector (Mark & Sweep)**: Dọn dẹp theo chu kỳ định kỳ qua Gen 0, Gen 1, Gen 2 khi bộ nhớ chạm ngưỡng. Không có reference counting. | **Reference Counting**: Tăng/giảm biến đếm ngay lập tức. Khi `ob_refcnt == 0`, vùng nhớ được giải phóng ngay lập tức (Deterministic Deallocation). |
| **Xử lý chu trình tham chiếu (Cyclic References)** | Tự nhiên xử lý được: Tracing GC xuất phát từ GC Roots (stack, static variables), object nào không chạm tới được sẽ bị dọn dẹp. | Reference counting bất lực (ref count không bao giờ về 0). CPython phải có thêm **Cyclic GC** chạy ngầm quét tìm chu trình kín. |
| **Đa luồng & CPU Cores** | **True Native Multi-threading**: N luồng C# chạy song song 100% trên N nhân CPU vật lý mà không bị khóa toàn cục. | **Global Interpreter Lock (GIL)**: Khóa toàn bộ tiến trình. Tại một thời điểm, chỉ đúng **1 luồng** được thực thi mã bytecode Python. |
| **Tác vụ CPU-bound** | Dùng `Parallel.ForEach`, `Task.Run` hoặc `ThreadPool` để tận dụng toàn bộ số core máy tính. | Bắt buộc phải dùng **Đa tiến trình (`multiprocessing` / `ProcessPoolExecutor`)** để vượt qua ranh giới của GIL. |
| **Tối ưu layout bộ nhớ** | Dùng `struct` (Value Type) nằm trực tiếp trên Stack hoặc trong mảng liên tục, tránh heap allocation. | Dùng `__slots__` để loại bỏ `__dict__` hash table, đưa thuộc tính về dạng mảng con trỏ C liên tục. |
| **Tương lai Free-threading** | Đã là bản chất vốn có từ phiên bản .NET đầu tiên. | **PEP 703 (Python 3.13t+)**: Tùy chọn experimental gỡ bỏ GIL, tiến tới đa luồng thực thụ. |

---

## 📖 Lý thuyết

### 1. Quản lý bộ nhớ trong CPython: `PyObject` và Vòng đời Đối tượng

Trong CPython, tất cả mọi thực thể từ số nguyên `int`, chuỗi `str`, cho đến hàm số hay lớp class đều được biểu diễn bằng một C struct mang tên `PyObject` (hoặc `PyVarObject` cho các kiểu có độ dài thay đổi như `list`, `str`):

```c
/* Định nghĩa trong file cpython/Include/object.h */
struct _object {
    _PyObject_HEAD_EXTRA
    Py_ssize_t ob_refcnt;          /* Số lượng tham chiếu đang trỏ tới đối tượng */
    struct _typeobject *ob_type;   /* Con trỏ tới kiểu dữ liệu của đối tượng */
};
```

#### 1.1 Cơ chế Đếm tham chiếu (Reference Counting)
- Khi một đối tượng được tạo hoặc được gán cho một biến mới, con trỏ tham chiếu `ob_refcnt` tăng lên 1.
- Khi biến ra khỏi phạm vi (out of scope), bị gán đè, hoặc bị xóa tường minh bằng lệnh `del`, `ob_refcnt` giảm đi 1.
- **Ưu điểm lớn nhất**: Tính chất giải phóng tức thì (Deterministic Destruction). Ngay khi `ob_refcnt == 0`, bộ nhớ của đối tượng sẽ được hàm `tp_dealloc` thu hồi ngay lập tức mà không cần chờ đợi đợt quét thu gom rác.

```python
import sys

# Tạo một danh sách mới
sample_list: list[int] = [1, 2, 3]

# sys.getrefcount() nhận tham số và tạm thời tăng refcount thêm 1
print(sys.getrefcount(sample_list))  # Kết quả: 2 (1 từ sample_list, 1 từ tham số hàm)

another_ref = sample_list
print(sys.getrefcount(sample_list))  # Kết quả: 3

del another_ref
print(sys.getrefcount(sample_list))  # Kết quả: 2
```

#### 1.2 Vấn đề Chu trình Tham chiếu và Bộ thu gom rác Cyclic GC
Điểm yếu chí mạng của Reference Counting là **Circular References (Tham chiếu vòng)**: Đối tượng A giữ tham chiếu tới B, và B cũng giữ tham chiếu tới A.

```python
class Node:

    def __init__(self, name: str) -> None:
        self.name = name
        self.partner: Node | None = None


node_a = Node("A")
node_b = Node("B")

# Tạo liên kết vòng
node_a.partner = node_b
node_b.partner = node_a

# Xóa tham chiếu ngoài
del node_a
del node_b
# Lúc này refcount của cả 2 node vẫn bằng 1 (vì trỏ chéo lẫn nhau),
# nhưng chương trình không còn bất kỳ biến nào để truy cập tới chúng!
```

Để giải quyết vấn đề rò rỉ này, CPython trang bị thêm bộ thu gom rác **Cyclic Garbage Collector** (quản lý qua module `gc`):
- GC chỉ theo dõi các đối tượng dạng container có khả năng chứa đối tượng khác (`list`, `dict`, `set`, `tuple`, custom classes).
- Chia đối tượng thành 3 thế hệ (Generations):
  - **Generation 0**: Nơi chứa các đối tượng mới được khởi tạo. Tần suất quét dọn thường xuyên nhất.
  - **Generation 1**: Các đối tượng sống sót qua các đợt quét của Gen 0.
  - **Generation 2**: Các đối tượng sống lâu nhất (như biến toàn cục, cấu hình hệ thống). Tần suất quét thấp nhất.
- Thuật toán của Cyclic GC: Tạm thời trừ đi số lượng tham chiếu nội bộ trong đồ thị container. Nếu đối tượng nào có refcount giảm về 0 từ nguồn nội bộ mà không có tham chiếu từ bên ngoài (GC Roots), chúng xác thực là rác trong chu trình và bị tiêu hủy.

#### 1.3 Tối ưu hóa bộ nhớ với `__slots__`
Theo mặc định, mỗi instance của một class Python lưu các thuộc tính động của nó trong một cuốn từ điển bí mật tên là `self.__dict__`. 
- Từ điển `__dict__` là một hash table, cực kỳ linh hoạt (bạn có thể gán tùy tiện `obj.anything = 123` bất cứ lúc nào), nhưng tiêu tốn overhead từ 150 đến 300 bytes trên mỗi instance chỉ để duy trì bảng băm.
- Khi sử dụng `__slots__`, bạn thông báo cho CPython biết trước danh sách thuộc tính cố định. CPython sẽ phân bổ một mảng con trỏ C liên tục ngay bên trong struct của instance và **hoàn toàn loại bỏ `__dict__`**.

```python
class NormalPoint:

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class SlottedPoint:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
```

*Kết quả*: Khi tạo 1,000,000 đối tượng, `SlottedPoint` giảm tới hơn 60% tổng dung lượng RAM và tăng tốc độ truy xuất thuộc tính thêm 15%–20%.

---

### 2. Bản chất Global Interpreter Lock (GIL)

#### 2.1 Tại sao CPython cần có GIL?
Vào đầu những năm 1990, khi Guido van Rossum thiết kế Python, các hệ điều hành bắt đầu hỗ trợ luồng (threads). Tuy nhiên:
1. Cơ chế quản lý bộ nhớ của CPython dựa trên `ob_refcnt`. Nếu nhiều luồng OS cùng đồng thời đọc/ghi vào `ob_refcnt` mà không có đồng bộ, điều kiện tranh chấp (race condition) sẽ xảy ra dẫn đến giải phóng bộ nhớ sai thời điểm hoặc rò rỉ vùng nhớ nghiêm trọng.
2. Việc đặt mutex khóa riêng cho từng `PyObject` sẽ khiến các thao tác đơn luồng cơ bản bị giảm hiệu năng thảm hại do lock overhead.
3. Giải pháp được chọn là một ổ khóa toàn cục: **Global Interpreter Lock (GIL)**. GIL đảm bảo rằng tại bất kỳ thời điểm nào, chỉ có đúng một luồng OS duy nhất được phép nắm giữ quyền điều khiển và thực thi mã Python bytecode trong một tiến trình.

#### 2.2 Đa luồng trong Python hoạt động ra sao dưới cái bóng của GIL?
- **Tác vụ I/O-bound (Mạng, Đọc ghi file, Database, `time.sleep`)**:
  Khi một luồng gọi system call của hệ điều hành để đọc socket hay file đĩa, CPython sẽ **chủ động nhả GIL** (`Py_BEGIN_ALLOW_THREADS`). Trong lúc luồng 1 đang chờ OS trả lời, luồng 2 ngay lập tức giành lấy GIL và tiếp tục chạy. Do đó, mô hình `threading` trong Python **vẫn rất hiệu quả cho các tác vụ I/O-bound**.
- **Tác vụ CPU-bound (Tính toán toán học, mã hóa, nén ảnh, xử lý dữ liệu lớn)**:
  Vì luồng không thực hiện I/O, nó giữ chặt GIL. Sau mỗi khoảng thời gian nhất định (mặc định là `sys.getswitchinterval() = 5ms`), luồng hiện tại buộc phải nhả GIL để nhường cơ hội cho luồng khác. Trên các CPU đa nhân, hiện tượng tranh chấp lock liên tục giữa các luồng OS xảy ra dẫn đến tình trạng suy giảm hiệu năng: **chạy 2 luồng CPU-bound trên 2 core còn chậm hơn chạy tuần tự trên 1 luồng đơn duy nhất!**

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        TIẾN TRÌNH PYTHON CÓ GIL                        │
│                                                                        │
│   Luồng 1 (I/O):  [Thực thi] ──► Chờ Socket (Nhả GIL) ───► [Tiếp tục]  │
│                                           │                 ▲          │
│   Luồng 2 (CPU):                          └─► Giành lấy GIL ┘          │
│                                                                        │
│   Kết luận: 1 thời điểm chỉ 1 luồng chạy mã Python Bytecode.           │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Cuộc cách mạng Free-threaded Python (PEP 703 / Python 3.13t+)

Nhận thức được rào cản thế kỷ của GIL đối với kỷ nguyên tính toán AI, Data Science và xử lý song song trên chip hàng chục nhân, cộng đồng Python đã chính thức chấp thuận **PEP 703 – Making the Global Interpreter Lock Optional in CPython**.

Từ Python 3.13, bản dựng thử nghiệm `python3.13t` (free-threaded build) cho phép chạy Python hoàn toàn **không có GIL**. Để giữ an toàn bộ nhớ khi không còn GIL, CPython 3.13t áp dụng các kỹ thuật tiên tiến:

1. **Biased Reference Counting**:
   Mỗi đối tượng phân biệt rõ luồng đã tạo ra nó (owning thread) và các luồng khác. Luồng sở hữu có thể tăng/giảm refcount cục bộ mà không cần atomic operations. Chỉ các luồng khác truy cập mới dùng atomic instructions tốn kém.
2. **Immortal Objects (PEP 683)**:
   Các đối tượng bất biến dùng chung toàn hệ thống (`None`, `True`, `False`, các số nguyên nhỏ, chuỗi ký tự cơ bản) được đánh dấu là "bất tử" (`refcount` ở trạng thái cố định đặc biệt) và không bao giờ bị tăng giảm refcount, loại bỏ hoàn toàn tranh chấp giữa các luồng.
3. **Deferred Reference Counting**:
   Các đối tượng cấp module hoặc mã bytecode được trì hoãn đếm tham chiếu, chỉ quét dọn khi GC chạy.
4. **Bộ cấp phát mimalloc của Microsoft**:
   Thay thế `pymalloc` truyền thống bằng `mimalloc` – một memory allocator đa luồng hiệu năng cực cao, quản lý các heap phân mảnh cục bộ theo từng luồng.

---

### 4. Ma trận lựa chọn mô hình Concurrency

Là một Senior Backend Engineer, bạn phải chọn đúng công cụ cho đúng bài toán thực tế:

| Mô hình | Cơ chế vận hành | Bộ nhớ chia sẻ | Trường hợp sử dụng tối ưu (Sweet Spot) |
|---|---|---|---|
| **`asyncio`** | Đơn luồng, Cooperative Multitasking dựa trên Non-blocking Event Loop | Dùng chung toàn bộ trong 1 tiến trình | Hàng chục ngàn kết nối I/O đồng thời: REST API, WebSockets, gọi microservices, async PostgreSQL queries. |
| **`ThreadPoolExecutor`** | Đa luồng OS (`threading`), chịu sự kiểm soát của GIL | Dùng chung không gian địa chỉ bộ nhớ (cần lock để tránh data races) | Blocking I/O không có bản async: Đọc file ổ cứng bằng `open()`, thư viện SDK cũ chỉ hỗ trợ sync, gọi các C-extensions đã tự nhả GIL (NumPy matrix multiply). |
| **`ProcessPoolExecutor`** | Đa tiến trình độc lập (`multiprocessing`), mỗi tiến trình có 1 Python interpreter và GIL riêng | Không chia sẻ bộ nhớ; giao tiếp qua IPC (Inter-Process Communication / `pickle`) | Tác vụ CPU-bound nặng: Xử lý/nén ảnh (Pillow), render PDF, phân tích dữ liệu Pandas/Polars, băm mật khẩu hàng loạt (Argon2), nén file ZIP dung lượng lớn. |

---

## 💻 Ví dụ thực tế

### 1. Thực nghiệm kiểm chứng: Đo đạc bộ nhớ với `__slots__`

Hãy viết một script đo đạc chính xác mức tiêu thụ bộ nhớ và thời gian khởi tạo của 1,000,000 đối tượng đại diện cho dữ liệu vị trí GPS của ứng dụng giao hàng:

```python
import sys
import time
import tracemalloc


class DeliveryTrackNormal:

    def __init__(self, lat: float, lng: float, driver_id: int) -> None:
        self.lat = lat
        self.lng = lng
        self.driver_id = driver_id


class DeliveryTrackSlotted:
    __slots__ = ("driver_id", "lat", "lng")

    def __init__(self, lat: float, lng: float, driver_id: int) -> None:
        self.lat = lat
        self.lng = lng
        self.driver_id = driver_id


def benchmark_memory(cls, total_items: int = 1_000_000) -> tuple[float, float]:
    tracemalloc.start()
    start_time = time.perf_counter()

    # Khởi tạo danh sách items
    items = [cls(10.762622, 106.660172, i) for i in range(total_items)]

    elapsed_time = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Giữ reference để không bị GC giải phóng sớm
    _ = len(items)
    peak_mb = peak / (1024 * 1024)
    return peak_mb, elapsed_time


def main() -> None:
    normal_mb, normal_sec = benchmark_memory(DeliveryTrackNormal)
    print(f"Normal Class  : {normal_mb:.2f} MB RAM | Thời gian: {normal_sec:.3f}s")

    slotted_mb, slotted_sec = benchmark_memory(DeliveryTrackSlotted)
    print(f"Slotted Class : {slotted_mb:.2f} MB RAM | Thời gian: {slotted_sec:.3f}s")
    saved_percent = (1 - slotted_mb / normal_mb) * 100
    print(f"==> Tiết kiệm được: {saved_percent:.1f}% RAM!")


if __name__ == "__main__":
    main()
```

*Kết quả thực tế trên máy 64-bit:*
- `Normal Class`: ~150 MB RAM
- `Slotted Class`: ~55 MB RAM (**giảm hơn 63% dung lượng RAM**)

---

### 2. Thực nghiệm CPU-bound: Đơn luồng vs Đa luồng (GIL) vs Đa tiến trình

Chúng ta thực hiện tính toán hàm băm CPU-bound nặng 4 lần trên máy tính có 4 cores trở lên:

```python
import concurrent.futures
import hashlib
import time


def cpu_heavy_hash(n: int) -> str:
    """Tác vụ CPU-bound thuần túy: băm liên tục chuỗi ký tự."""
    data = b"benchmark-seed-taskflow"
    for _ in range(n):
        data = hashlib.sha256(data).digest()
    return data.hex()


def run_sequential(iterations: list[int]) -> float:
    start = time.perf_counter()
    for it in iterations:
        cpu_heavy_hash(it)
    return time.perf_counter() - start


def run_threads(iterations: list[int]) -> float:
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(cpu_heavy_hash, iterations))
    return time.perf_counter() - start


def run_processes(iterations: list[int]) -> float:
    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        list(executor.map(cpu_heavy_hash, iterations))
    return time.perf_counter() - start


if __name__ == "__main__":
    tasks = [1_500_000] * 4
    print("Bắt đầu benchmark CPU-bound...")

    t_seq = run_sequential(tasks)
    print(f"1. Tuần tự (Sequential)      : {t_seq:.3f}s")

    t_thr = run_threads(tasks)
    print(f"2. Đa luồng (ThreadPool - GIL): {t_thr:.3f}s (Không nhanh hơn, thậm chí chậm hơn do context switch)")

    t_proc = run_processes(tasks)
    print(f"3. Đa tiến trình (ProcessPool): {t_proc:.3f}s (Tận dụng song song cả 4 CPU cores)")
```

*Kết quả đo đạc thực tế:*
- `Sequential`: ~2.8s
- `ThreadPool`: ~2.9s – 3.1s (Bị GIL serialize hoàn toàn, tốn thêm chi phí tranh chấp lock!)
- `ProcessPool`: ~0.8s (Tăng tốc gần 3.5x trên 4 CPU cores!)

---

### 3. Tích hợp `ProcessPoolExecutor` chuẩn kiến trúc trong FastAPI

Trong một hệ thống FastAPI production, tuyệt đối không tạo mới `ProcessPoolExecutor` trong từng HTTP request vì việc fork process rất tốn tài nguyên. Chúng ta quản lý pool vòng đời bằng **FastAPI `lifespan`**:

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI, Request


def heavy_cpu_task(payload_size: int) -> int:
    """Hàm CPU-bound chạy độc lập trong tiến trình worker."""
    total = 0
    for i in range(payload_size):
        total += (i * i) % 997
    return total


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Khởi tạo ProcessPoolExecutor lúc startup ứng dụng
    cpu_pool = ProcessPoolExecutor(max_workers=4)
    app.state.cpu_pool = cpu_pool
    print("[Lifespan] Khởi tạo ProcessPoolExecutor thành công với 4 workers.")
    try:
        yield
    finally:
        # Dọn dẹp graceful shutdown
        cpu_pool.shutdown(wait=True)
        print("[Lifespan] Đã giải phóng toàn bộ worker processes.")


app = FastAPI(title="Concurrency Scalable API", lifespan=lifespan)


def get_cpu_pool(request: Request) -> ProcessPoolExecutor:
    """Dependency trích xuất executor pool từ application state."""
    return request.app.state.cpu_pool


@app.get("/compute-sync-blocking")
async def bad_blocking_endpoint() -> dict[str, str | int]:
    # ❌ SAI LẦM: Chạy CPU-bound trực tiếp trong Event Loop làm đóng băng server
    res = heavy_cpu_task(10_000_000)
    return {"status": "done", "result": res}


@app.get("/compute-parallel")
async def good_parallel_endpoint(
    pool: Annotated[ProcessPoolExecutor, Depends(get_cpu_pool)],
) -> dict[str, str | int]:
    # ✅ CHUẨN SENIOR: Đẩy việc tính toán sang ProcessPoolExecutor thông qua run_in_executor
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(pool, heavy_cpu_task, 10_000_000)
    return {"status": "success", "result": result}
```

---

## ⚠️ Lỗi thường gặp

### 1. Lầm tưởng `threading` giúp tăng tốc tính toán CPU trong Python
Nhiều kỹ sư chuyển từ C# sang Python thường có thói quen tạo `threading.Thread` hoặc `ThreadPoolExecutor` để xử lý song song các tác vụ nén file, tính toán ma trận hoặc băm mật khẩu. 
*Hậu quả*: Do GIL, các luồng này bị tuần tự hóa trên một nhân CPU duy nhất. Hiệu năng không tăng mà còn sụt giảm do liên tục chuyển ngữ cảnh (context switching). 
*Giải pháp*: Luôn dùng `ProcessPoolExecutor` hoặc các thư viện C đã nhả GIL (như NumPy, Polars, OpenCV).

### 2. Tạo chu trình tham chiếu dính phương thức `__del__`
Trước Python 3.4 (PEP 442), các đối tượng có quan hệ tham chiếu vòng chứa phương thức `__del__` sẽ không thể bị thu gom bởi Cyclic GC và bị đẩy vào danh sách `gc.garbage`, gây rò rỉ bộ nhớ vĩnh viễn. Mặc dù Python 3.4+ đã giải quyết được việc gọi `__del__`, việc lạm dụng `__del__` vẫn gây ra hành vi không thể dự đoán được về thứ tự hủy đối tượng. Hãy luôn ưu tiên sử dụng **Context Manager (`with` statement)** để dọn dẹp tài nguyên thay vì trông cậy vào `__del__`.

### 3. Khởi tạo `ProcessPoolExecutor` cục bộ trong từng Request
```python
# ❌ RẤT TỒI TỆ: Tạo mới pool mỗi khi có request tới
@app.post("/process")
async def bad_process_route(data: RequestPayload):
    with ProcessPoolExecutor() as pool:  # Tốn hàng trăm ms để fork process mới!
        result = await loop.run_in_executor(pool, my_task, data)
    return result
```
Việc liên tục spawn tiến trình mới sẽ gây kiệt quệ tài nguyên OS (cạn PID, tràn swap). Luôn khởi tạo pool ở cấp độ application lifespan và chia sẻ pool dùng chung.

### 4. Thiếu khối `if __name__ == '__main__':` khi chạy Multiprocessing
Trên hệ điều hành Windows và macOS (nơi cơ chế khởi tạo process mặc định là `spawn` thay vì `fork`), nếu không đặt mã khởi chạy bên dưới khối `if __name__ == '__main__':`, tiến trình con khi được tạo ra sẽ import lại chính file đó từ đầu, gây ra vòng lặp vô tận sinh tiến trình (`RuntimeError: freeze_support / an attempt has been made to start a new process before the current process has finished its bootstrapping phase`).

---

## ✍️ Bài tập thực hành

### Bài tập 1: Tối ưu bộ nhớ hệ thống IoT Telemetry với `__slots__`
Một hệ thống IoT tiếp nhận 500,000 gói tin đo lường chất lượng không khí mỗi phút. Mỗi gói tin gồm: `device_id` (chuỗi), `timestamp` (float), `pm25` (float), `co2` (float), `temperature` (float).
Yêu cầu:
1. Viết class `TelemetryRecord` tối ưu với `__slots__`.
2. Sử dụng `tracemalloc` để so sánh dung lượng RAM của 500,000 bản ghi giữa class có `__slots__` và class thông thường không có `__slots__`.
3. Đo lường tỷ lệ tiết kiệm RAM đạt tối thiểu 50%.

<details>
<summary>💡 Gợi ý</summary>

```python
import sys
import tracemalloc


class TelemetryStandard:

    def __init__(self, dev_id: str, ts: float, pm25: float, co2: float, temp: float) -> None:
        self.dev_id = dev_id
        self.ts = ts
        self.pm25 = pm25
        self.co2 = co2
        self.temp = temp


class TelemetryOptimized:
    __slots__ = ("co2", "dev_id", "pm25", "temp", "ts")

    def __init__(self, dev_id: str, ts: float, pm25: float, co2: float, temp: float) -> None:
        self.dev_id = dev_id
        self.ts = ts
        self.pm25 = pm25
        self.co2 = co2
        self.temp = temp


def measure_class(cls, count: int = 500_000) -> float:
    tracemalloc.start()
    records = [
        cls(f"sensor-{i % 1000}", 1700000000.0 + i, 12.5, 410.0, 28.5)
        for i in range(count)
    ]
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    _ = len(records)
    return peak / (1024 * 1024)


if __name__ == "__main__":
    mem_std = measure_class(TelemetryStandard)
    mem_opt = measure_class(TelemetryOptimized)
    saved = (1 - mem_opt / mem_std) * 100
    print(f"Tiêu thụ RAM Standard : {mem_std:.2f} MB")
    print(f"Tiêu thụ RAM Optimized: {mem_opt:.2f} MB (Tiết kiệm {saved:.1f}%)")
    assert saved > 50.0, "Mức tiết kiệm phải vượt qua 50%!"
```
</details>

---

### Bài tập 2: Phát hiện và can thiệp Circular Reference bằng module `gc`
Viết chương trình tạo một đồ án chu trình phức tạp giữa 3 thực thể: `Author`, `Book`, và `Reviewer`.
Yêu cầu:
1. Tạo liên kết vòng giữa 3 đối tượng này.
2. Tắt bộ thu gom tự động bằng `gc.disable()`.
3. Xóa các biến tham chiếu ngoài bằng `del`.
4. Gọi `gc.collect()` tường minh, in ra số lượng đối tượng không thể truy cập (unreachable objects) mà GC đã phát hiện và dọn dẹp.
5. Bật lại GC bằng `gc.enable()`.

<details>
<summary>💡 Gợi ý</summary>

```python
import gc


class Author:

    def __init__(self, name: str) -> None:
        self.name = name
        self.books: list[Book] = []


class Book:

    def __init__(self, title: str, author: Author) -> None:
        self.title = title
        self.author = author
        self.reviewer: Reviewer | None = None


class Reviewer:

    def __init__(self, name: str) -> None:
        self.name = name
        self.assigned_author: Author | None = None


def test_circular_cycle() -> None:
    gc.collect()  # Dọn sạch trước khi test
    gc.disable()

    author = Author("Nguyen Van A")
    book = Book("Python Internals", author)
    author.books.append(book)

    reviewer = Reviewer("Tran Van B")
    book.reviewer = reviewer
    reviewer.assigned_author = author  # Hoàn thành chu trình khép kín: Author -> Book -> Reviewer -> Author

    # Xóa tham chiếu từ stack
    del author
    del book
    del reviewer

    # Thực thi thu gom rác thủ công
    unreachable_count = gc.collect()
    print(f"Số lượng unreachable objects đã được Cyclic GC thu hồi: {unreachable_count}")
    gc.enable()
    assert unreachable_count > 0


if __name__ == "__main__":
    test_circular_cycle()
```
</details>

---

### Bài tập 3: Xây dựng Worker xử lý mã hóa mật khẩu nặng an toàn trong FastAPI
Viết một ứng dụng FastAPI có endpoint `/hash-passwords` nhận vào danh sách mật khẩu dạng thô (strings) và băm chúng bằng thuật toán CPU-bound `hashlib.pbkdf2_hmac` với 200,000 iterations.
Yêu cầu:
1. Sử dụng `ProcessPoolExecutor` được quản lý an toàn trong `lifespan`.
2. Tuyệt đối không để quá trình băm mật khẩu làm nghẽn Event Loop (chứng minh bằng việc một endpoint nhẹ `/health` vẫn phản hồi dưới 5ms trong lúc `/hash-passwords` đang chạy).

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
import hashlib
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel


def hash_single_password(pwd: str) -> str:
    salt = b"taskflow_fixed_salt"
    key = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, iterations=200_000)
    return key.hex()


def process_bulk_hashes(passwords: list[str]) -> list[str]:
    return [hash_single_password(p) for p in passwords]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    executor = ProcessPoolExecutor(max_workers=4)
    app.state.pool = executor
    try:
        yield
    finally:
        executor.shutdown(wait=True)


app = FastAPI(lifespan=lifespan)


class PasswordBatchRequest(BaseModel):
    passwords: list[str]


def get_executor(request: Request) -> ProcessPoolExecutor:
    return request.app.state.pool


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/hash-passwords")
async def hash_passwords_endpoint(
    payload: PasswordBatchRequest,
    pool: Annotated[ProcessPoolExecutor, Depends(get_executor)],
) -> dict[str, list[str]]:
    loop = asyncio.get_running_loop()
    hashed_list = await loop.run_in_executor(pool, process_bulk_hashes, payload.passwords)
    return {"hashes": hashed_list}
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được cấu trúc của `PyObject`, vai trò của `ob_refcnt` và cơ chế giải phóng tức thì khi ref count về 0.
- [ ] Tôi hiểu vì sao Reference Counting không thể tự dọn dẹp Circular References và nguyên lý hoạt động của Cyclic GC qua Gen 0, 1, 2.
- [ ] Tôi hiểu rõ cơ chế hoạt động của `__slots__` và biết cách ứng dụng để tiết kiệm 40%–70% RAM cho các class dữ liệu lớn.
- [ ] Tôi nắm vững bản chất của GIL: tại sao đa luồng trong CPython chỉ hiệu quả với I/O-bound và hoàn toàn bị nghẽn với CPU-bound.
- [ ] Tôi hiểu mục tiêu của PEP 703 (Free-threaded Python 3.13t+) và các cơ chế thay thế như Biased Reference Counting và mimalloc.
- [ ] Tôi làm chủ ma trận lựa chọn giữa `asyncio`, `ThreadPoolExecutor`, và `ProcessPoolExecutor`.
- [ ] Tôi biết cách quản lý `ProcessPoolExecutor` thông qua FastAPI `lifespan` và offload an toàn bằng `loop.run_in_executor`.

---

## 📚 Đọc thêm

- [CPython Internal Documentation: Garbage Collection Design](https://devguide.python.org/internals/garbage-collector/)
- [PEP 703 – Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [PEP 683 – Immortal Objects, Using a Fixed Refcount](https://peps.python.org/pep-0683/)
- [Fluent Python (2nd Edition) - Luciano Ramalho: Chapter 6 (Object References, Mutability, and Recycling)](https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/)
- [Tiếp theo: Bài 02 – Profiling & hiệu năng](./02-profiling-performance.md)

<!-- nav:bottom -->
---

[⬅️ Senior](./README.md) | [📚 Mục lục Senior](./README.md) | [Profiling & hiệu năng ➡️](./02-profiling-performance.md)
<!-- /nav:bottom -->
