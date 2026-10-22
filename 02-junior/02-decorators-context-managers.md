<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 02
<!-- /nav:top -->

# Decorator & context manager

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 01: Iterator & generator](./01-iterators-generators.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu sâu sắc bản chất của **Decorator**: Decorator trong Python thực chất là một **Higher-Order Function** (`fn = decorator(fn)`), bọc hàm đích ngay tại thời điểm import.
- Phân biệt sự khác nhau mang tính cốt lõi giữa **Python Decorator** (code thực thi động) và **C# Attribute** (metadata tĩnh đọc qua Reflection).
- Tự tay xây dựng thành thạo cả decorator không có tham số và decorator có cấu hình tham số động.
- Hiểu rõ vì sao luôn bắt buộc phải sử dụng **`@functools.wraps`** để bảo toàn signature và metadata của hàm, đặc biệt quan trọng khi làm việc với **FastAPI OpenAPI / Swagger**.
- Làm chủ giao thức **Context Manager Protocol** (`__enter__`, `__exit__`), so sánh trực diện với mẫu `IDisposable` và câu lệnh `using` của C#.
- Biết cách sử dụng **`@contextlib.contextmanager`** kết hợp cú pháp `yield` để tạo context manager nhanh chóng, an toàn với `try...finally`.

---

## 🔁 So sánh với C# / ASP.NET

Trong hệ sinh thái .NET, bạn liên tục sử dụng các Attributes như `[Authorize]`, `[HttpGet]`, `[ServiceFilter]`, cùng với từ khóa `using` cho các tài nguyên `IDisposable`. Cả hai khái niệm này đều có người anh em sinh đôi vô cùng quyền lực trong Python:

| Khái niệm / Mẫu thiết kế | C# / ASP.NET | Python 3.12+ |
|---|---|---|
| **Khai báo tiền tố** | `[Route("api/users")]` (C# Attribute) | `@app.get("/users")` (Python Decorator) |
| **Bản chất hoạt động** | **Metadata tĩnh**: Chỉ lưu thông tin vào Assembly Metadata Table. Phải dùng Reflection hoặc Action Filter Pipeline để đọc lúc runtime | **Hàm bọc thực thi (Higher-Order Function)**: Thực thi ngay khi nạp module, bọc trực tiếp hàm gốc bằng một hàm wrapper mới |
| **Chặn & bọc hành vi (AOP)** | Action Filter, Middleware hoặc PostSharp (IL Weaving) | Decorator thuần túy trong ngôn ngữ, không cần thư viện ngoài |
| **Bảo toàn chữ ký hàm** | Compiler tự xử lý thông qua Reflection MethodInfo | Bắt buộc phải dùng `@functools.wraps` để giữ lại signature và docstring |
| **Quản lý giải phóng tài nguyên** | Interface `IDisposable` (chứa phương thức `Dispose()`) | Giao thức Context Manager (`__enter__` và `__exit__`) |
| **Cú pháp khối an toàn** | `using (var client = new HttpClient()) { ... }` | `with open("file.txt") as f: ...` |
| **Tạo khối giải phóng nhanh** | Cần viết class kế thừa `IDisposable` | Decorator `@contextlib.contextmanager` kết hợp lệnh `yield` |
| **Nuốt ngoại lệ trong khối** | Không hỗ trợ trong `using`, phải dùng `try/catch` lồng | `__exit__` trả về `True` để dập tắt ngoại lệ |

---

## 📖 Lý thuyết

### 1. Bản chất của Decorator: Higher-Order Function

Trong Python, hàm là **First-Class Citizen** (công dân hạng nhất):
- Hàm có thể được gán vào biến.
- Hàm có thể được truyền vào như tham số của một hàm khác.
- Hàm có thể được định nghĩa bên trong một hàm khác và được trả về như một kết quả.

Một **Decorator** đơn giản là một hàm nhận vào một hàm khác làm tham số, và trả về một hàm thay thế (thường là một wrapper mở rộng tính năng của hàm ban đầu).

Cú pháp `@decorator`:

```python
@my_decorator
def greet(name: str) -> str:
    return f"Xin chào, {name}!"
```

Thực chất chỉ là cú pháp "đường ăn cỏ" (syntactic sugar) hoàn toàn tương đương với:

```python
def greet(name: str) -> str:
    return f"Xin chào, {name}!"


# Bản chất: Hàm gốc bị thay thế bằng kết quả trả về của my_decorator
greet = my_decorator(greet)
```

Quá trình gán `greet = my_decorator(greet)` diễn ra **ngay tại thời điểm nạp file (module import time)**, chứ không phải đợi tới lúc hàm `greet()` được gọi!

### 2. Xây dựng Decorator cơ bản (Không tham số)

Mô hình chuẩn của một decorator gồm 2 tầng hàm:
1. Hàm bên ngoài: nhận hàm mục tiêu `func`.
2. Hàm wrapper bên trong: nhận các đối số `*args, **kwargs` truyền vào cho `func`, thực thi logic bổ sung (trước và sau khi gọi `func`), rồi trả về kết quả.

```python
from collections.abc import Callable
import functools
import time


def timer(func: Callable) -> Callable:
    """Decorator đo thời gian thực thi của một hàm."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        # Gọi hàm gốc
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start_time
        print(f"⏱️ Hàm '{func.__name__}' mất {duration:.6f}s để hoàn tất.")
        return result

    return wrapper


@timer
def compute_heavy_task(n: int) -> int:
    return sum(i * i for i in range(n))


compute_heavy_task(500_000)
```

### 3. Tầm quan trọng chí mạng của `@functools.wraps` đối với FastAPI

Hãy quan sát điều gì xảy ra nếu bạn **quên** gắn `@functools.wraps(func)` trên `wrapper`:

```python
def bad_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@bad_decorator
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    """Tính thuế giá trị gia tăng."""
    return amount * rate


print(calculate_tax.__name__)  # In ra: 'wrapper' (mất tên hàm gốc!)
print(calculate_tax.__doc__)  # In ra: None (mất docstring!)
```

#### Tại sao điều này có thể làm sập FastAPI?
FastAPI hoạt động dựa trên cơ chế phản chiếu chữ ký hàm thông qua thư viện chuẩn `inspect.signature(func)`:
- FastAPI đọc tên tham số (`amount`, `rate`), kiểu dữ liệu (`float`), và giá trị mặc định (`0.1`) để tự động sinh Swagger UI (OpenAPI Docs) và kiểm tra validate dữ liệu.
- Nếu decorator của bạn không dùng `@functools.wraps`, FastAPI sẽ kiểm tra `wrapper(*args, **kwargs)`. Khi đó, FastAPI thấy endpoint không có bất kỳ tham số tường minh nào!
- **Hậu quả**: Swagger UI mất hoàn toàn tài liệu tham số, và request gửi lên không thể bind vào các biến!

`@functools.wraps(func)` sao chép toàn bộ metadata (`__name__`, `__doc__`, `__annotations__`, `__module__`, `__wrapped__`) từ hàm gốc sang `wrapper`, đảm bảo `inspect.signature` luôn đọc đúng hàm gốc.

> [!CAUTION]
> Luôn luôn sử dụng `@functools.wraps(func)` cho mọi decorator mà bạn viết!

### 4. Xây dựng Decorator có tham số (Parameterized Decorator)

Nếu bạn muốn truyền cấu hình vào decorator, ví dụ `@retry(max_attempts=3, delay_seconds=1.0)`, bạn cần viết **3 tầng hàm**:
1. Tầng ngoài cùng: Nhận cấu hình decorator (`max_attempts`, `delay_seconds`).
2. Tầng giữa: Nhận hàm mục tiêu `func`.
3. Tầng trong cùng: Hàm `wrapper` nhận `*args, **kwargs` của hàm mục tiêu.

```python
from collections.abc import Callable
import functools
import time


def retry(max_attempts: int = 3, delay_seconds: float = 0.5) -> Callable:
    """Decorator tự động thử lại khi hàm ném ngoại lệ."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                try:
                    attempts += 1
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempts >= max_attempts:
                        print(f"❌ Đã thử lại {attempts} lần nhưng thất bại. Re-raise exception!")
                        raise exc
                    print(
                        f"⚠️ Thử lần {attempts} gặp lỗi '{exc}'. Thử lại sau {delay_seconds}s..."
                    )
                    time.sleep(delay_seconds)

        return wrapper

    return decorator


# Sử dụng:
@retry(max_attempts=3, delay_seconds=0.1)
def fetch_api_data(url: str) -> dict:
    # Giả lập lỗi mạng tạm thời
    return {"url": url, "status": "ok"}
```

### 5. Giao thức Context Manager: `__enter__` và `__exit__`

Trong C#, bạn giải phóng tài nguyên qua `IDisposable`:
```csharp
using (var stream = new FileStream("data.bin", FileMode.Open))
{
    // thao tác file
} // Tự động gọi stream.Dispose()
```

Trong Python, cơ chế này được gọi là **Context Manager**, điều khiển bởi câu lệnh **`with`**. Một đối tượng là Context Manager khi nó triển khai 2 phương thức:
- **`__enter__(self)`**: Chạy khi bắt đầu khối `with`. Giá trị trả về của nó được gán vào biến đứng sau từ khóa `as`.
- **`__exit__(self, exc_type, exc_val, exc_tb)`**: Chạy khi khối `with` kết thúc (dù thành công hay gặp lỗi).
  - Nếu xảy ra exception trong khối `with`, 3 tham số sẽ chứa thông tin ngoại lệ: `exc_type` (loại lỗi), `exc_val` (instance lỗi), `exc_tb` (traceback).
  - **Dập tắt ngoại lệ (Suppress Exception)**: Nếu `__exit__` trả về `True`, Python hiểu là bạn đã xử lý xong lỗi và sẽ **nuốt (suppress)** ngoại lệ, chương trình không bị dừng. Nếu trả về `False` hoặc `None`, ngoại lệ sẽ tiếp tục bị ném lên trên (re-raise).

```python
class ManagedDatabaseConnection:
    """Context Manager quản lý kết nối cơ sở dữ liệu mô phỏng."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.is_connected = False

    def __enter__(self) -> "ManagedDatabaseConnection":
        print(f"🔌 [__enter__] Mở kết nối tới: {self.dsn}")
        self.is_connected = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        print(f"🔒 [__exit__] Đóng kết nối: {self.dsn}")
        self.is_connected = False
        if exc_type is not None:
            print(f"💥 [__exit__] Bắt được ngoại lệ: {exc_val}")
            # Trả về False để ngoại lệ tiếp tục văng lên cho tầng trên xử lý
            return False
        return True


# Sử dụng:
with ManagedDatabaseConnection("postgres://localhost:5432/db") as conn:
    print(f"Trạng thái kết nối: {conn.is_connected}")
```

### 6. Viết nhanh Context Manager với `@contextlib.contextmanager`

Thay vì viết nguyên một class với `__enter__` và `__exit__`, module chuẩn `contextlib` cung cấp decorator `@contextlib.contextmanager`. Bạn chỉ cần viết một hàm Generator với **đúng một lệnh `yield`**:

- Mọi code **trước `yield`** tương đương với `__enter__`.
- Giá trị được **`yield`** chính là giá trị sau từ khóa `as`.
- Mọi code **sau `yield`** tương đương với `__exit__`.

> [!IMPORTANT]
> Luôn luôn bọc lệnh `yield` trong khối `try...finally` để đảm bảo code dọn dẹp tài nguyên phía sau `yield` luôn được thực thi, ngay cả khi khối lệnh bên trong `with` văng ra ngoại lệ!

```python
from collections.abc import Generator
from contextlib import contextmanager
import os


@contextmanager
def temporary_working_directory(new_dir: str) -> Generator[None, None, None]:
    """Tạm thời chuyển thư mục làm việc hiện tại và khôi phục khi xong."""
    old_dir = os.getcwd()
    os.chdir(new_dir)
    print(f"📂 Đã chuyển sang: {new_dir}")
    try:
        yield
    finally:
        os.chdir(old_dir)
        print(f"🔙 Đã khôi phục về: {old_dir}")


# Sử dụng:
with temporary_working_directory("/tmp"):
    print(f"Đang làm việc tại: {os.getcwd()}")
```

---

## 💻 Ví dụ thực hành

Dưới đây là một kịch bản hoàn chỉnh: Kết hợp **Decorator phân quyền (RBAC)** và **Context Manager Unit of Work / Transaction** cho một hệ thống ngân hàng:

```python
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
import functools


# 1. Quản lý ngữ cảnh người dùng hiện tại (Giả lập Security Context trong .NET)
CURRENT_USER_ROLES = ["teller", "auditor"]


def require_role(required_role: str) -> Callable:
    """Decorator kiểm tra quyền hạn trước khi thực thi endpoint/service."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if required_role not in CURRENT_USER_ROLES:
                raise PermissionError(
                    f"Truy cập bị từ chối! Yêu cầu vai trò: '{required_role}', "
                    f"vai trò hiện tại: {CURRENT_USER_ROLES}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# 2. Context Manager Unit of Work (Quản lý Transaction)
@dataclass
class UnitOfWork:
    transaction_id: str
    operations: list[str] = field(default_factory=list)
    committed: bool = False


@contextmanager
def unit_of_work(tx_id: str) -> Generator[UnitOfWork, None, None]:
    uow = UnitOfWork(transaction_id=tx_id)
    print(f"\n--- [BEGIN TX #{uow.transaction_id}] ---")
    try:
        yield uow
        uow.committed = True
        print(f"✅ [COMMIT TX #{uow.transaction_id}] Toàn bộ {len(uow.operations)} tác vụ thành công.")
    except Exception as exc:
        uow.committed = False
        print(f"❌ [ROLLBACK TX #{uow.transaction_id}] Thao tác thất bại do lỗi: {exc}")
        raise
    finally:
        print(f"--- [END TX #{uow.transaction_id}] ---")


# 3. Áp dụng phối hợp Decorator & Context Manager
@require_role("teller")
def transfer_money(from_acc: str, to_acc: str, amount: float) -> None:
    """Chuyển tiền an toàn giữa 2 tài khoản."""
    with unit_of_work("TX_1002") as uow:
        print(f"Đang trừ {amount:,.0f} VND từ tài khoản {from_acc}...")
        uow.operations.append(f"DEBIT {from_acc} {amount}")

        if amount > 100_000_000:
            raise ValueError("Số tiền vượt quá hạn mức chuyển khoản một lần của Giao dịch viên!")

        print(f"Đang cộng {amount:,.0f} VND vào tài khoản {to_acc}...")
        uow.operations.append(f"CREDIT {to_acc} {amount}")


# Chạy kịch bản thành công:
print(">>> KỊCH BẢN 1: Chuyển khoản trong hạn mức:")
transfer_money("ACC_001", "ACC_002", 20_000_000)

# Chạy kịch bản thất bại kích hoạt Rollback:
print("\n>>> KỊCH BẢN 2: Chuyển khoản vượt hạn mức (Rollback):")
try:
    transfer_money("ACC_001", "ACC_002", 500_000_000)
except ValueError as e:
    print(f"Ứng dụng đã bắt ngoại lệ: {e}")
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên `@functools.wraps(func)`
Như đã giải thích, đây là lỗi phổ biến nhất của lập trình viên Python khi bắt đầu viết decorator. Quên `wraps` làm mất `__name__`, docstring, và khiến FastAPI không nhận diện được tham số của route trong Swagger UI.

### 2. Quên trả về `wrapper` ở cuối Decorator
```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # ❌ QUÊN LỆNH: return wrapper
    # Khi gọi @my_decorator, hàm gốc sẽ bị gán thành None!
    # Lỗi khi gọi hàm: TypeError: 'NoneType' object is not callable
```

### 3. Nhầm lẫn khi gọi Decorator có tham số và không có tham số
Nếu decorator được định nghĩa có tham số:
```python
def log_tag(tag: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ❌ LỖI: Quên dấu ngoặc tròn () khi gọi
# @log_tag
# def do_something(): pass
# Lỗi: tag nhận vào hàm do_something thay vì chuỗi tag!

#  ĐÚNG:
# @log_tag(tag="USER_SERVICE")
# def do_something(): pass
```

### 4. Quên `try...finally` trong `@contextmanager`
Nếu trong khối lệnh `with` xảy ra lỗi, code phía sau `yield` sẽ **không bao giờ được chạy** nếu bạn không bọc `yield` trong `try...finally`. Điều này gây rò rỉ tài nguyên (chẳng hạn kết nối Database bị treo, lock không được giải phóng).

---

## ✍️ Bài tập thực hành

### Bài 1: Decorator Cache kết quả (Simple Memoize)
Viết một decorator `@memoize` lưu trữ kết quả trả về của một hàm theo các tham số truyền vào:
- Sử dụng một từ điển `cache = {}` bên trong closure của decorator.
- Khóa (cache key) là tuple các đối số `args` (giả sử các hàm được truyền vào chỉ nhận các tham số hashable).
- Nếu kết quả đã có trong cache, in thông báo `"[CACHE HIT] Trả về từ bộ nhớ"` và trả về giá trị đã lưu.
- Nếu chưa có, in `"[CACHE MISS] Tính toán mới"`, gọi hàm, lưu vào cache và trả về kết quả.
- Sử dụng đầy đủ `@functools.wraps`. Thử nghiệm với hàm tính số Fibonacci.

<details>
<summary>💡 Gợi ý</summary>

- Cấu trúc:
  ```python
  def memoize(func):
      cache = {}

      @functools.wraps(func)
      def wrapper(*args):
          if args in cache:
              print(f"[CACHE HIT] {args}")
              return cache[args]
          result = func(*args)
          cache[args] = result
          print(f"[CACHE MISS] {args}")
          return result

      return wrapper
  ```
</details>

---

### Bài 2: Decorator Validate kiểu dữ liệu tham số lúc Runtime
Viết decorator `@validate_types` nhận vào các kiểu dữ liệu tương ứng của các tham số keyword và kiểm tra kiểu lúc chạy:
- Ví dụ: `@validate_types(age=int, name=str)`.
- Nếu tham số truyền vào không đúng kiểu dữ liệu, ném ngoại lệ `TypeError(f"Tham số {k} phải là {expected_type}, nhận được {type(v)}")`.
- Áp dụng kiểm tra cho các keyword arguments `kwargs`.

<details>
<summary>💡 Gợi ý</summary>

- Đây là decorator có tham số:
  ```python
  def validate_types(**expected_types):
      def decorator(func):
          @functools.wraps(func)
          def wrapper(*args, **kwargs):
              for key, expected in expected_types.items():
                  if key in kwargs and not isinstance(kwargs[key], expected):
                      raise TypeError(
                          f"Tham số '{key}' phải là {expected.__name__}, "
                          f"nhưng nhận được {type(kwargs[key]).__name__}"
                      )
              return func(*args, **kwargs)

          return wrapper

      return decorator
  ```
</details>

---

### Bài 3: Context Manager đo thời gian và ghi nhận ngoại lệ
Viết một class `Stopwatch` triển khai giao thức Context Manager:
- Khi vào khối `with`: ghi nhận thời điểm bắt đầu bằng `time.perf_counter()`.
- Thuộc tính `elapsed`: trả về thời gian đã trôi qua tính đến thời điểm hiện tại.
- Khi thoát khỏi khối `with`: tính tổng thời gian chạy và in ra màn hình.
- Nếu có lỗi xảy ra trong khối `with`: in ra thông báo lỗi và thời gian chạy tính đến lúc xảy ra lỗi, nhưng **không dập tắt ngoại lệ** (cho phép lỗi văng tiếp ra ngoài).

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng `__enter__` lưu `self.start_time = time.perf_counter()`, trả về `self`.
- Tạo phương thức `elapsed(self) -> float`: trả về `time.perf_counter() - self.start_time`.
- Trong `__exit__(self, exc_type, exc_val, exc_tb)`: tính `total = time.perf_counter() - self.start_time`. Kiểm tra `if exc_type is not None:` in thông báo lỗi và thời gian, sau đó trả về `False`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ cơ chế Higher-Order Function của Decorator và thời điểm decorator được thực thi (module import time)?
- [ ] Bạn phân biệt được sự khác nhau giữa Decorator của Python và Attribute của C#?
- [ ] Bạn hiểu tại sao `@functools.wraps(func)` là bắt buộc và hậu quả của nó đối với FastAPI Swagger UI?
- [ ] Bạn có thể tự viết một Decorator có tham số với cấu trúc 3 tầng hàm?
- [ ] Bạn nắm vững giao thức Context Manager với `__enter__` và `__exit__`, cũng như cơ chế dập tắt ngoại lệ khi trả về `True`?
- [ ] Bạn thành thạo việc tạo Context Manager bằng `@contextlib.contextmanager` và khối an toàn `try...finally`?

---

## 📚 Đọc thêm

- [PEP 318 – Decorators for Functions and Methods](https://peps.python.org/pep-0318/)
- [PEP 343 – The "with" Statement (Context Managers)](https://peps.python.org/pep-0343/)
- [Python Documentation – functools.wraps](https://docs.python.org/3/library/functools.html#functools.wraps)
- [Python Documentation – contextlib](https://docs.python.org/3/library/contextlib.html)

<!-- nav:bottom -->
---

[⬅️ Iterator & generator](./01-iterators-generators.md) | [📚 Mục lục Junior](./README.md) | [Typing nâng cao & mypy ➡️](./03-advanced-typing-mypy.md)
<!-- /nav:bottom -->
