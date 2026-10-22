<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 10
<!-- /nav:top -->

# Type hints cơ bản

> ⏱️ Thời lượng: ~2.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 09: OOP & dataclass](./09-oop-dataclasses.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ triết lý của hệ thống kiểu trong Python: Ngôn ngữ kiểu động (dynamically typed) có bổ trợ kiểm tra kiểu tĩnh (gradual typing), giải thích vì sao type hints **không bao giờ tự kiểm tra ở runtime**.
- Sử dụng thành thạo cú pháp Type Hints hiện đại nhất (Python 3.10–3.13+): Các collection chuẩn `list[T]`, `dict[K, V]`, toán tử Union `T | None` thay thế cú pháp cũ `Optional[T]` và `Union[...]`.
- Phân biệt bản chất giữa **`Any`** (tắt kiểm tra kiểu, tương đương `dynamic` trong C#) và **`object`** (kiểu cơ sở an toàn, tương đương `object` trong C#).
- Làm chủ các kiểu chuyên biệt: **`Literal`** (giới hạn giá trị cụ thể), **`Final`** (khai báo hằng số bất biến), **`TypedDict`** (định nghĩa schema chặt chẽ cho dictionary), và **`Callable`** (type hint cho hàm / delegate).
- Cập nhật cú pháp khai báo kiểu mới **`type AliasName = ...`** (PEP 695) từ Python 3.12+.
- Nhận thức vai trò của các công cụ Static Type Checker (`mypy`, `pyright`, Pylance) và thư viện xác thực runtime (`pydantic`) trong hệ sinh thái FastAPI.

---

## 🔁 So sánh với C# / ASP.NET

Là một kỹ sư C#, bạn đã quá quen thuộc với hệ thống kiểu tĩnh (statically typed), nơi trình biên dịch (Roslyn Compiler) từ chối build nếu có bất kỳ sự sai lệch kiểu dữ liệu nào. Trong Python, type hints mang một tâm thế hoàn toàn khác:

| Khái niệm / Kiểu dữ liệu | C# / .NET | Python 3.10–3.13+ |
|---|---|---|
| **Cơ chế thực thi** | Compiler ép kiểu tĩnh tại thời điểm build (Compile-time enforcement) | Type hints hoàn toàn bị runtime bỏ qua (Ignored by runtime). Cần công cụ như mypy/pyright |
| **Kiểu danh sách** | `List<string>` | `list[str]` (từ Python 3.9+) |
| **Kiểu từ điển** | `Dictionary<string, int>` | `dict[str, int]` |
| **Kiểu Nullable / Có thể None** | `string?` | `str | None` (thay thế cho `Optional[str]`) |
| **Hợp nhất nhiều kiểu (Union)** | Thường cần lớp bọc như `OneOf<T1, T2>` | `int | float | str` |
| **Kiểu thoát kiểm tra (Bypass)** | `dynamic` | `typing.Any` |
| **Kiểu cha của mọi đối tượng** | `object` | `object` (yêu cầu `isinstance` trước khi dùng) |
| **Giới hạn tập giá trị chuỗi** | `enum TaskPriority { Low, High }` | `Literal["low", "medium", "high"]` |
| **Hằng số không thể sửa đổi** | `const` hoặc `readonly` | `typing.Final` |
| **Kiểu hàm / Callback / Delegate** | `Func<int, string, bool>` / `Action<int>` | `Callable[[int, str], bool]` / `Callable[[int], None]` |
| **Bí danh kiểu (Type Alias)** | `using UserId = System.Int32;` | `type UserId = int` (Python 3.12+) |
| **Schema cho Dictionary** | Không có tương đương trực tiếp (thường dùng DTO class/record) | `typing.TypedDict` |

---

## 📖 Lý thuyết

### 1. Bản chất của Type Hints: Runtime không hề kiểm tra!

Một cú sốc lớn nhất của lập trình viên C# khi mới sang Python là: **Đoạn mã sau vẫn chạy trơn tru mà không có lỗi gì xảy ra lúc runtime!**

```python
def calculate_discount(price: float, discount_percent: float) -> float:
    return price * (1 - discount_percent / 100)


# Bạn truyền nhầm chuỗi "10" thay vì số float 0.1?
# Python runtime hoàn toàn không kiểm tra kiểu của đối số!
# Nó chỉ thực thi phép tính. Nếu phép tính hợp lệ (hoặc crash vì TypeError trong phép nhân),
# runtime chỉ báo lỗi ở thời điểm thực thi dòng đó, không phải do vi phạm Type Hints!
```

> [!IMPORTANT]
> **Type Hints trong Python thuần chỉ là Metadata (chú thích)!**
> CPython lưu các type hint vào thuộc tính `__annotations__` và hoàn toàn lờ chúng đi khi sinh bytecode.
> - **Để phát hiện lỗi trước khi chạy**: Bạn cần dùng các công cụ phân tích tĩnh (**Static Type Checkers**) như **`mypy`**, **`pyright`** (tích hợp trong VS Code Pylance).
> - **Để tự động ép kiểu và validate dữ liệu ở runtime**: Hệ sinh thái Python sử dụng thư viện như **`pydantic`** (xương sống của FastAPI).

---

### 2. Cú pháp Type Hints hiện đại (Python 3.10–3.13+)

#### Kiểu tích hợp chuẩn (PEP 585)
Từ Python 3.9+, bạn không cần phải `from typing import List, Dict, Set, Tuple` nữa. Hãy sử dụng trực tiếp các kiểu chữ thường có sẵn:

```python
# CÁCH CŨ (Python 3.8 trở về trước - KHÔNG NÊN DÙNG NỮA):
# from typing import List, Dict, Set, Tuple
# names: List[str] = ["Alice", "Bob"]

# CÁCH HIỆN ĐẠI (Python 3.9+):
names: list[str] = ["Alice", "Bob"]
scores: dict[str, int] = {"Alice": 95, "Bob": 88}
unique_tags: set[str] = {"python", "fastapi"}
coordinates: tuple[float, float] = (10.762622, 106.660172)  # Tuple cố định 2 phần tử
arbitrary_numbers: tuple[int, ...] = (1, 2, 3, 4, 5)        # Tuple có độ dài tùy ý
```

#### Toán tử Union hiện đại `|` (PEP 604)
Từ Python 3.10+, toán tử `|` (pipe) thay thế hoàn toàn cho `Union` và `Optional`:

```python
# CÁCH CŨ:
# from typing import Optional, Union
# def find_user(user_id: int) -> Optional[str]: ...

# CÁCH HIỆN ĐẠI (Python 3.10+):
def find_user(user_id: int) -> str | None:
    if user_id == 1:
        return "Admin"
    return None


# Nhận nhiều kiểu dữ liệu khả dĩ:
def format_id(raw_id: int | str) -> str:
    return str(raw_id).strip()
```

---

### 3. `Any` vs `object`: Cần phân biệt rạch ròi

- **`Any` (từ module `typing`)**: Báo hiệu cho Type Checker bỏ cuộc hoàn toàn. Bạn có thể gọi bất kỳ hàm nào, gán bất kỳ thuộc tính nào lên biến `Any` mà mypy/pyright không hề phàn nàn. Đây là "lỗ thoát hiểm" (escape hatch) tương tự `dynamic` trong C#. **Lạm dụng `Any` sẽ biến code của bạn trở về thời kỳ dynamic không an toàn**.
- **`object`**: Là lớp cha gốc của mọi thực thể trong Python. Một biến có kiểu `object` được Type Checker bảo vệ nghiêm ngặt: Bạn **không thể** truy cập các thuộc tính tùy tiện nếu chưa kiểm tra kiểu bằng `isinstance()`.

```python
from typing import Any


def process_dynamic(data: Any) -> None:
    # Type checker cho phép mọi thứ, nhưng RUNTIME SẼ CRASH nếu data không có thuộc tính này!
    data.non_existent_method()


def process_safe(data: object) -> None:
    # Type checker sẽ BÁO LỖI ngay tại dòng dưới nếu gọi trực tiếp:
    # data.split() -> Lỗi: Cannot access member "split" for type "object"

    # Cách làm đúng: Phải Type Narrowing qua isinstance
    if isinstance(data, str):
        print(data.split())  # Bây giờ Type Checker biết chắc data là str!
```

---

### 4. `Literal` và `Final`

#### `Literal` (PEP 586)
Giới hạn một biến hoặc tham số hàm chỉ được phép nhận các giá trị cụ thể định trước:

```python
from typing import Literal

# Chỉ chấp nhận đúng 3 chuỗi này:
type Status = Literal["PENDING", "PROCESSING", "COMPLETED"]


def update_status(task_id: int, status: Status) -> None:
    print(f"Cập nhật task {task_id} thành {status}")


update_status(1, "COMPLETED")  # Hợp lệ!
# update_status(1, "FAILED")    # Mypy/Pyright sẽ gạch đỏ cảnh báo lỗi ngay lập tức!
```

#### `Final` (PEP 591)
Khai báo hằng số không được phép gán lại, hoặc phương thức không được phép override ở class con:

```python
from typing import Final

MAX_RETRIES: Final[int] = 3
# MAX_RETRIES = 5  # Type Checker báo lỗi: Cannot assign to final attribute
```

---

### 5. `TypedDict`: Schema cho Dictionary

Trong các ứng dụng backend, bạn thường nhận các dictionary JSON thô. `TypedDict` cho phép bạn định nghĩa cấu trúc các khóa và kiểu dữ liệu tương ứng của một dictionary mà không cần tạo class đầy đủ:

```python
from typing import TypedDict


class TaskPayload(TypedDict):
    title: str
    priority: int
    is_active: bool


# Sử dụng:
payload: TaskPayload = {
    "title": "Viết tài liệu",
    "priority": 1,
    "is_active": True,
}

# payload["unknown_key"] = 123  # Pyright/Mypy sẽ cảnh báo lỗi ngay!
```

---

### 6. `Callable`: Type hints cho hàm / Delegate

Để truyền hàm như một tham số (First-class citizen), cú pháp là `Callable[[ThamSo1, ThamSo2], KieuTraVe]`:

```python
from collections.abc import Callable


# Hàm filter nhận một hàm kiểm tra điều kiện (predicate):
def filter_tasks(
    task_ids: list[int],
    predicate: Callable[[int], bool],
) -> list[int]:
    return [tid for tid in task_ids if predicate(tid)]


def is_even(n: int) -> bool:
    return n % 2 == 0


result = filter_tasks([1, 2, 3, 4, 5, 6], is_even)  # [2, 4, 6]
```

---

### 7. Cú pháp `type AliasName = ...` (Python 3.12+ PEP 695)

Từ Python 3.12, Python giới thiệu câu lệnh `type` giúp khai báo bí danh kiểu một cách tường minh, ngắn gọn và hỗ trợ generic tự nhiên:

```python
# Cú pháp Python 3.12+:
type TaskId = int
type JsonDict = dict[str, object]
type TaskFilter[T] = Callable[[T], bool]  # Generic type alias siêu ngắn gọn!


def get_task(tid: TaskId) -> JsonDict:
    return {"id": tid, "name": "Task A"}
```

---

## 💻 Ví dụ thực hành

Dưới đây là một mô đun xử lý quy trình công việc `workflow_engine.py` áp dụng đầy đủ cú pháp Modern Type Hints:

```python
from collections.abc import Callable
from datetime import datetime
from typing import Final, Literal, TypedDict


# 1. Định nghĩa Type Alias (Python 3.12+)
type TaskId = int
type PriorityLevel = Literal["LOW", "MEDIUM", "HIGH"]

DEFAULT_PRIORITY: Final[PriorityLevel] = "MEDIUM"


# 2. Định nghĩa TypedDict cho DTO
class TaskMetadata(TypedDict, total=False):
    tags: list[str]
    assigned_to: str | None
    estimated_hours: float


class TaskRecord(TypedDict):
    id: TaskId
    title: str
    priority: PriorityLevel
    created_at: str
    metadata: TaskMetadata


# 3. Type hint cho Hàm xử lý (Callable Handler)
type TaskTransformer = Callable[[TaskRecord], TaskRecord]


# 4. Service xử lý logic với Type Hints an toàn
class TaskWorkflowManager:
    def __init__(self) -> None:
        self._tasks: dict[TaskId, TaskRecord] = {}

    def register_task(
        self,
        task_id: TaskId,
        title: str,
        priority: PriorityLevel = DEFAULT_PRIORITY,
        metadata: TaskMetadata | None = None,
    ) -> TaskRecord:
        record: TaskRecord = {
            "id": task_id,
            "title": title.strip(),
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata if metadata is not None else {},
        }
        self._tasks[task_id] = record
        return record

    def find_task(self, task_id: TaskId) -> TaskRecord | None:
        """Trả về TaskRecord nếu có, hoặc None nếu không tìm thấy."""
        return self._tasks.get(task_id)

    def apply_pipeline(
        self,
        task_id: TaskId,
        transformers: list[TaskTransformer],
    ) -> TaskRecord | None:
        """Áp dụng chuỗi các hàm biến đổi lên TaskRecord."""
        task = self.find_task(task_id)
        if task is None:
            return None

        current = task
        for transform in transformers:
            current = transform(current)
        self._tasks[task_id] = current
        return current


# 5. Các hàm Transformer cụ thể
def uppercase_title_transformer(task: TaskRecord) -> TaskRecord:
    task["title"] = task["title"].upper()
    return task


def elevate_priority_transformer(task: TaskRecord) -> TaskRecord:
    task["priority"] = "HIGH"
    return task


def run_demo() -> None:
    manager = TaskWorkflowManager()

    # Đăng ký task
    t1 = manager.register_task(
        task_id=101,
        title="Nghiên cứu kiến trúc Clean Architecture",
        priority="LOW",
        metadata={"tags": ["python", "architecture"], "estimated_hours": 4.5},
    )
    print(f"Khởi tạo task: {t1['title']} - Mức độ: {t1['priority']}")

    # Áp dụng pipeline biến đổi
    pipeline: list[TaskTransformer] = [
        uppercase_title_transformer,
        elevate_priority_transformer,
    ]
    updated = manager.apply_pipeline(101, pipeline)
    if updated is not None:
        print(f"Sau pipeline: {updated['title']} - Mức độ: {updated['priority']}")


if __name__ == "__main__":
    run_demo()
```

---

## ⚠️ Lỗi thường gặp

### 1. Hiểu lầm rằng Type Hints sẽ tự động ép kiểu hoặc báo lỗi lúc runtime
- **Thực tế**: Viết `def add(x: int, y: int) -> int: return x + y`. Nếu bạn gọi `add("a", "b")`, hàm vẫn chạy và trả về `"ab"`.
- **Giải pháp**: Nếu cần validate kiểu ở runtime cho dữ liệu người dùng gửi lên API, hãy dùng **Pydantic Model** (sẽ học ở Junior/Level 02).

### 2. Vẫn import `List`, `Dict`, `Optional` trên Python 3.10+
- Đoạn mã sử dụng `from typing import List, Optional` tuy vẫn chạy để tương thích ngược, nhưng bị coi là cũ kỹ và lỗi thời (outdated style). Hãy dùng `list[str]` và `str | None`.

### 3. Gán giá trị mặc định là `None` nhưng quên khai báo Union `| None`
- **Lỗi**:
  ```python
  def find_item(name: str = None): ...  # Lỗi vi phạm type checker!
  ```
- **Cách sửa đúng**:
  ```python
  def find_item(name: str | None = None) -> None: ...
  ```

### 4. Dùng `Any` vô tội vạ để "dập tắt" cảnh báo của IDE
- Khi gặp lỗi type checking, nhiều người giải quyết nhanh bằng cách đổi kiểu biến thành `Any`. Việc này phá hủy toàn bộ giá trị của type hints, khiến IDE không gợi ý code (IntelliSense) và che giấu các bug tiềm ẩn.

---

## ✍️ Bài tập thực hành

### Bài 1: Refactor mã nguồn legacy sang Modern Type Hints
Chuyển đổi đoạn mã cũ sau đây sang chuẩn Python 3.12+ (sử dụng câu lệnh `type`, toán tử `|`, và các kiểu tích hợp chữ thường):

```python
# MÃ CẦN REFACTOR:
from typing import Dict, List, Optional, Union

UserId = int


def query_tasks(
    filter_status: Optional[str] = None,
    limit: Union[int, None] = 10,
) -> List[Dict[str, Union[str, int]]]:
    pass
```

<details>
<summary>💡 Gợi ý</summary>

```python
type UserId = int
type TaskDict = dict[str, str | int]


def query_tasks(
    filter_status: str | None = None,
    limit: int | None = 10,
) -> list[TaskDict]:
    return []
```
</details>

---

### Bài 2: Khai báo Schema cấu hình với `TypedDict`
Xây dựng cấu trúc `AppConfig`:
1. Sử dụng `TypedDict`.
2. Khóa bắt buộc: `app_name: str`, `port: int`, `debug: bool`.
3. Khóa tùy chọn (sử dụng `NotRequired` từ `typing`): `database_url: str`.
4. Viết hàm `init_server(config: AppConfig) -> str` in ra thông tin cổng lắng nghe.

<details>
<summary>💡 Gợi ý</summary>

```python
from typing import NotRequired, TypedDict


class AppConfig(TypedDict):
    app_name: str
    port: int
    debug: bool
    database_url: NotRequired[str]


def init_server(config: AppConfig) -> str:
    return f"Máy chủ {config['app_name']} đang lắng nghe trên cổng {config['port']}..."
```
</details>

---

### Bài 3: Thiết kế Callback Validator với `Callable` và `Literal`
1. Định nghĩa kiểu `ValidationResult = Literal["VALID", "INVALID", "SKIPPED"]`.
2. Định nghĩa kiểu alias `ValidatorFunc = Callable[[str], ValidationResult]`.
3. Viết hàm `validate_text(text: str, rules: list[ValidatorFunc]) -> bool` trả về `True` nếu không có bất kỳ rule nào trả về `"INVALID"`.

<details>
<summary>💡 Gợi ý</summary>

```python
from collections.abc import Callable
from typing import Literal

type ValidationResult = Literal["VALID", "INVALID", "SKIPPED"]
type ValidatorFunc = Callable[[str], ValidationResult]


def check_not_empty(text: str) -> ValidationResult:
    return "VALID" if text.strip() else "INVALID"


def check_no_special_chars(text: str) -> ValidationResult:
    return "INVALID" if any(c in text for c in "@#$%") else "VALID"


def validate_text(text: str, rules: list[ValidatorFunc]) -> bool:
    for rule in rules:
        if rule(text) == "INVALID":
            return False
    return True
```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ vì sao Python runtime không bao giờ kiểm tra type hints và vai trò của mypy/pyright?
- [ ] Bạn sử dụng thành thạo `list[T]`, `dict[K, V]` và toán tử `T | None` thay cho cú pháp cũ?
- [ ] Bạn phân biệt được bản chất an toàn giữa `object` và lỗ thoát hiểm `Any`?
- [ ] Bạn biết cách dùng `Literal` để giới hạn tập giá trị và `Final` để bảo vệ hằng số?
- [ ] Bạn nắm được cách định nghĩa cấu trúc dữ liệu dictionary bằng `TypedDict`?
- [ ] Bạn biết cách type hint cho hàm callback bằng `Callable`?
- [ ] Bạn nắm bắt được cú pháp `type Alias = ...` của Python 3.12+?

---

## 📚 Đọc thêm

- [Python Documentation – `typing` — Support for type hints](https://docs.python.org/3/library/typing.html)
- [PEP 585 – Type Hinting Generics In Standard Collections](https://peps.python.org/pep-0585/)
- [PEP 604 – Allow writing union types as `X | Y`](https://peps.python.org/pep-0604/)
- [PEP 695 – Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [Mypy Documentation – Getting Started](https://mypy.readthedocs.io/en/stable/)

<!-- nav:bottom -->
---

[⬅️ OOP & dataclass](./09-oop-dataclasses.md) | [📚 Mục lục Fresher](./README.md) | [Công cụ: ruff & debugging ➡️](./11-tooling-ruff-debugging.md)
<!-- /nav:bottom -->
