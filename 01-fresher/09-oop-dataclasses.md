<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 09
<!-- /nav:top -->

# OOP & dataclass

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 08: File I/O & JSON](./08-file-io-json.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Thấu hiểu mô hình hướng đối tượng (OOP) trong Python: Khởi tạo đối tượng qua phương thức `__init__`, cơ chế truyền tường minh tham số `self` (đối chiếu với từ khóa ngầm định `this` trong C#).
- Phân biệt bản chất bộ nhớ giữa **Instance Attributes** (thuộc tính theo từng thể hiện) và **Class Attributes** (thuộc tính tĩnh chia sẻ chung) và cách tránh lỗi chia sẻ trạng thái ngoài ý muốn.
- Thiết kế các thuộc tính đóng gói an toàn bằng decorator **`@property`** và setter tương đương Property trong C#.
- Phân biệt chính xác mục đích sử dụng giữa **`@classmethod`** (nhận `cls`, thường dùng cho Factory methods) và **`@staticmethod`** (hàm tiện ích độc lập).
- Nắm vững các quy ước truy cập: `_single_underscore` (quy ước protected nội bộ) và `__double_underscore` (Name Mangling chống ghi đè thuộc tính khi kế thừa).
- Làm chủ các Dunder Methods (Special/Magic Methods) phổ biến: **`__repr__`**, **`__str__`**, **`__eq__`**, **`__len__`**, **`__hash__`**.
- Áp dụng kế thừa đơn (`class Child(Parent):`) và hàm **`super()`** để tái sử dụng và mở rộng logic từ lớp cha (tương đương từ khóa `base` trong C#).
- Xây dựng trừu tượng hóa (Abstraction) chuẩn mực bằng **`abc.ABC`** và **`@abstractmethod`** tương đương interface / abstract class trong C#.
- Sử dụng **`enum.StrEnum`** (Python 3.11+) cho các tập giá trị hằng số thân thiện với JSON serialization.
- Làm chủ **`@dataclass(slots=True, frozen=True)`** tương đương với `record` trong C# hiện đại: Tự động sinh boilerplate code, tối ưu hóa bộ nhớ và thiết lập tính bất biến (immutability).

---

## 🔁 So sánh với C# / ASP.NET

Lập trình viên C# đã thấm nhuần tư tưởng OOP chặt chẽ với các từ khóa `public`, `private`, `protected`, `interface`, `abstract class`, và gần đây là `record`. Bảng dưới đây so sánh các khái niệm cốt lõi giữa hai ngôn ngữ:

| Khái niệm / Cú pháp | C# / .NET | Python 3.11+ |
|---|---|---|
| **Con trỏ thể hiện** | `this` (ngầm định, không cần khai báo ở danh sách tham số) | `self` (tường minh, phải là tham số đầu tiên của mọi instance method) |
| **Hàm khởi tạo (Constructor)** | `public TaskItem(int id) { ... }` | `def __init__(self, id: int) -> None:` |
| **Quyền truy cập (Access Modifiers)** | `private`, `protected`, `public` do compiler cưỡng chế nghiêm ngặt | Dựa trên **quy ước danh dự (Honor system)**: `_protected` (nội bộ), `__mangled` (chống va chạm) |
| **Getter / Setter** | Property: `public string Title { get; set; }` | Decorator `@property` và `@title.setter` |
| **Phương thức tĩnh** | `public static void DoWork()` | `@staticmethod` (không nhận ngữ cảnh) |
| **Factory Method / Đa hình cấp class** | Không có tương đương trực tiếp (thường dùng Static Method kèm Type parameter) | `@classmethod` (nhận tham số đầu tiên là class `cls`) |
| **Lớp trừu tượng (Abstract Class)** | `public abstract class RepositoryBase` | `class BaseRepository(abc.ABC):` |
| **Phương thức trừu tượng** | `public abstract Task<T> GetByIdAsync(int id);` | `@abc.abstractmethod def get_by_id(self, id: int):` |
| **Ép kiểu chuỗi hiển thị** | `ToString()` | `__str__()` (cho người dùng) & `__repr__()` (cho lập trình viên debug) |
| **Kế thừa & gọi lớp cha** | `class Child : Parent` và `base(...)` / `base.Method()` | `class Child(Parent):` và `super().__init__(...)` / `super().method()` |
| **Kiểm tra bằng nhau theo giá trị** | `Equals()` hoặc tự động trên `record` | `__eq__()` |
| **Kiểu Record / Value Object** | `public record TaskRecord(int Id, string Title);` | `@dataclass(slots=True, frozen=True)` |
| **Định nghĩa chuỗi Enum** | `enum TaskStatus { Todo, Done }` (thường phải serialize sang int hoặc chuỗi tùy cấu hình) | `class TaskStatus(StrEnum):` (kế thừa trực tiếp `str`) |

---

## 📖 Lý thuyết

### 1. Khởi tạo class, `__init__`, và tham số `self`

Trong CPython, `class` tạo ra một kiểu dữ liệu mới. Khi bạn gọi `Task(id=1, title="Học OOP")`, Python sẽ:
1. Cấp phát bộ nhớ cho đối tượng bằng phương thức `__new__()`.
2. Khởi tạo các giá trị cho đối tượng thông qua `__init__()`.

```python
class Task:
    def __init__(self, task_id: int, title: str) -> None:
        # self đại diện cho chính instance đang được tạo ra
        self.task_id = task_id
        self.title = title
        self.completed = False

    def mark_completed(self) -> None:
        self.completed = True
```

> [!NOTE]
> **Tại sao `self` phải được viết tường minh?**
> Triết lý của Python là *"Explicit is better than implicit"* (Tường minh tốt hơn ngầm định). Khi bạn gọi `t.mark_completed()`, CPython thực chất chuyển đổi lời gọi thành `Task.mark_completed(t)`. Việc viết `self` giúp phân biệt rõ ràng giữa biến cục bộ của hàm và thuộc tính của instance.

---

### 2. Instance Attributes vs Class Attributes: Cạm bẫy Mutable

- **Instance Attribute**: Được gán vào `self.attribute` bên trong `__init__` hoặc các method. Mỗi đối tượng sở hữu bản sao độc lập của biến này.
- **Class Attribute**: Được khai báo trực tiếp ở thân class (ngoài hàm). Tất cả các instance đều dùng chung một vùng nhớ duy nhất!

```python
# CẠM BẪY CHIA SẺ VÙNG NHỚ:
class ProjectManagerBad:
    tasks: list[str] = []  # CLASS ATTRIBUTE KIỂU MUTABLE! DÙNG CHUNG TOÀN HỆ THỐNG!


pm1 = ProjectManagerBad()
pm2 = ProjectManagerBad()
pm1.tasks.append("Task của PM1")
print(pm2.tasks)  # In ra: ['Task của PM1'] -> pm2 bị ảnh hưởng dù không hề thêm!

# ĐÚNG CHUẨN (INSTANCE ATTRIBUTE):
class ProjectManagerGood:
    def __init__(self) -> None:
        self.tasks: list[str] = []  # Mỗi instance sở hữu một danh sách riêng biệt trong RAM
```

---

### 3. Đóng gói thuộc tính với `@property`

Thay vì phải viết các phương thức getter/setter dài dòng kiểu Java như `get_title()` và `set_title(value)`, Python cung cấp decorator **`@property`** giúp bạn kiểm tra tính hợp lệ dữ liệu mà người dùng vẫn truy cập tự nhiên như một thuộc tính thông thường:

```python
class TaskItem:
    def __init__(self, title: str) -> None:
        self._title = title

    @property
    def title(self) -> str:
        """Getter: Đọc tiêu đề."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Setter: Kiểm tra tính hợp lệ trước khi gán."""
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("Tiêu đề công việc không được rỗng!")
        self._title = clean_value
```

---

### 4. `@classmethod` và `@staticmethod`

- **`@classmethod`**: Nhận tham số đầu tiên là class hiện tại (`cls`). Được dùng phổ biến nhất để làm **Factory Methods** (các hàm khởi tạo thay thế như `from_dict`, `from_json`).
- **`@staticmethod`**: Không nhận `self` cũng chẳng nhận `cls`. Nó hoạt động như một hàm thông thường nhưng được đặt vào trong namespace của class để gom nhóm logic liên quan.

```python
from datetime import datetime
from typing import Any, Self


class TaskRecord:
    def __init__(self, title: str, created_at: datetime) -> None:
        self.title = title
        self.created_at = created_at

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Factory method tạo instance từ dictionary."""
        created = datetime.fromisoformat(data["created_at"])
        return cls(title=data["title"], created_at=created)

    @staticmethod
    def validate_title(title: str) -> bool:
        """Hàm tiện ích độc lập không phụ thuộc trạng thái của class hay instance."""
        return len(title.strip()) >= 3
```

---

### 5. Quy ước đóng gói: `_single` vs `__double`

Python không có từ khóa `private` cưỡng chế cấp máy ảo như C#. Cộng đồng Python áp dụng nguyên tắc *"We are all consenting adults here"* (Chúng ta đều là người trưởng thành có trách nhiệm):

1. **`_single_leading_underscore` (`_protected`)**:
   - Báo hiệu cho các lập trình viên khác: *"Đây là chi tiết triển khai nội bộ, đừng đụng vào nếu không hiểu rõ."*
   - Công cụ linter và IDE sẽ cảnh báo nếu truy cập biến này từ bên ngoài class.
2. **`__double_leading_underscore` (`__mangled`)**:
   - Kích hoạt cơ chế **Name Mangling**: CPython tự động đổi tên thuộc tính `__title` thành `_ClassName__title` trong bảng `__dict__`.
   - Mục đích duy nhất: Tránh việc class con vô tình ghi đè (shadow) lên biến của class cha khi kế thừa phức tạp, **không phải là cơ chế bảo mật**.

---

### 6. Các Dunder Methods thiết yếu (`__repr__`, `__str__`, `__eq__`, `__hash__`)

Dunder (Double Underscore) methods định hình cách đối tượng của bạn tương tác với các hàm tích hợp sẵn của Python:

- **`__str__(self) -> str`**: Biểu diễn chuỗi thân thiện cho người dùng cuối (gọi khi dùng `print(obj)` hoặc `str(obj)`).
- **`__repr__(self) -> str`**: Biểu diễn chuỗi chính xác kỹ thuật cho lập trình viên khi debug (hiển thị trong console interactive hoặc traceback log). Nguyên tắc lý tưởng: `eval(repr(obj)) == obj`.
- **`__eq__(self, other) -> bool`**: Định nghĩa toán tử so sánh bằng `obj1 == obj2`. Mặc định Python so sánh theo địa chỉ ô nhớ (`is`).
- **`__len__(self) -> int`**: Cho phép gọi `len(obj)`.
- **`__hash__(self) -> int`**: Cho phép đối tượng được dùng làm Key trong `dict` hoặc phần tử trong `set`. Để một class hashable, nó bắt buộc phải bất biến (immutable) và có định nghĩa `__eq__`.

```python
class Priority:
    def __init__(self, level: int, label: str) -> None:
        self.level = level
        self.label = label

    def __repr__(self) -> str:
        return f"Priority(level={self.level}, label={self.label!r})"

    def __str__(self) -> str:
        return f"[{self.level}] {self.label}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Priority):
            return False
        return self.level == other.level
```

---

### 7. Kế thừa và hàm `super()`

Trong Python, kế thừa đơn được khai báo bằng cách đặt tên lớp cha trong dấu ngoặc đơn ngay sau tên lớp con: `class Child(Parent):`.

Khi ghi đè (override) phương thức khởi tạo `__init__` hoặc bất kỳ phương thức nào của lớp cha, bạn sử dụng hàm **`super()`** để gọi phiên bản của lớp cha (tương đương với từ khóa `base` trong C#):

```python
class BaseNotification:
    """Lớp cha định nghĩa thông báo cơ bản."""

    def __init__(self, recipient: str) -> None:
        self.recipient = recipient

    def send(self, message: str) -> bool:
        print(f"[BASE] Gửi tin tới {self.recipient}: {message}")
        return True


class EmailNotification(BaseNotification):
    """Lớp con kế thừa và mở rộng thêm tiêu đề email."""

    def __init__(self, recipient: str, subject: str) -> None:
        # Gọi hàm khởi tạo của lớp cha (tương đương base(recipient) trong C#)
        super().__init__(recipient)
        self.subject = subject

    def send(self, message: str) -> bool:
        # Mở rộng logic và gọi tiếp phương thức send của lớp cha
        print(f"[EMAIL] Tiêu đề: {self.subject}")
        return super().send(message)


# Chạy thử
email_alert = EmailNotification("dev@company.com", "Cảnh báo lỗi 500")
email_alert.send("Hệ thống database đang mất kết nối!")
# Output:
# [EMAIL] Tiêu đề: Cảnh báo lỗi 500
# [BASE] Gửi tin tới dev@company.com: Hệ thống database đang mất kết nối!
```

> [!TIP]
> **Khác biệt quan trọng với C#**: Trong C#, nếu lớp con không gọi `base(...)` tường minh, trình biên dịch vẫn tự động chèn lời gọi đến constructor không tham số `base()`. Trong Python, nếu bạn định nghĩa `__init__` ở lớp con mà quên gọi `super().__init__(...)`, các thuộc tính của lớp cha sẽ **không bao giờ được khởi tạo** và dẫn đến lỗi `AttributeError` khi truy cập!

---

### 8. Interface trừu tượng với `abc.ABC` & `@abstractmethod`

Trong Python, bạn tạo interface hoặc abstract class bằng cách kế thừa từ **`abc.ABC`** (Abstract Base Class) và trang trí các phương thức bắt buộc bằng decorator **`@abstractmethod`**:

```python
from abc import ABC, abstractmethod
from typing import Any


class TaskStorage(ABC):
    """Interface định nghĩa giao ước lưu trữ cho Task."""

    @abstractmethod
    def get(self, task_id: int) -> dict[str, Any] | None:
        """Lấy thông tin task theo ID."""

    @abstractmethod
    def save(self, task: dict[str, Any]) -> None:
        """Lưu trữ một task."""
```

Nếu một class kế thừa từ `TaskStorage` mà không hiện thực hóa đầy đủ cả `get` và `save`, CPython sẽ chặn ngay lúc khởi tạo:
`TypeError: Can't instantiate abstract class InMemoryTaskStorage without an implementation for abstract method 'save'`.

---

### 9. `enum.StrEnum` (Python 3.11+)

Trước Python 3.11, việc định nghĩa Enum chuỗi cần kế thừa cả `str` và `Enum`. Python 3.11 cung cấp sẵn class **`enum.StrEnum`**:

```python
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


# Lợi thế vượt trội:
status = TaskStatus.TODO
print(status == "TODO")  # True! Hoạt động như chuỗi string thuần túy!
print(f"Trạng thái: {status}")  # "Trạng thái: TODO"
# Dễ dàng serialize sang JSON mà không cần converter phụ trợ!
```

---

### 10. `@dataclass(slots=True, frozen=True)` (C# `record` của Python)

Module `dataclasses` (PEP 557) loại bỏ toàn bộ mã boilerplate nhàm chán khi tạo class chỉ dùng để chứa dữ liệu (DTO, Value Object).

Khi bạn trang trí một class với `@dataclass`:
- CPython tự động sinh ra: `__init__`, `__repr__`, `__eq__`.
- **`frozen=True`**: Biến đối tượng thành bất biến (immutable), cố tình gán lại giá trị thuộc tính sẽ ném `FrozenInstanceError`. Tự động sinh `__hash__` để làm key cho dict/set.
- **`slots=True`** (Python 3.10+): Loại bỏ dictionary ngầm `__dict__` của mỗi instance, giảm tới **50% dung lượng RAM** và tăng tốc độ truy cập thuộc tính đáng kể.

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True, frozen=True)
class TaskModel:
    id: int
    title: str
    status: str = "TODO"
    tags: list[str] = field(default_factory=list)  # Khởi tạo mutable an toàn!
    created_at: datetime = field(default_factory=datetime.now)
```

> [!WARNING]
> **Tuyệt đối không gán `tags: list[str] = []` trong dataclass**:
> Dataclass sẽ ném lỗi `ValueError: mutable default <class 'list'> for field tags is not allowed: use default_factory`. Luôn sử dụng `field(default_factory=list)`!

---

## 💻 Ví dụ thực hành

Dưới đây là một mô hình thiết kế hướng đối tượng hoàn chỉnh áp dụng toàn bộ kiến thức trên để quản lý tác vụ trong TaskFlow:

```python
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Self


# 1. Định nghĩa các Enum nghiệp vụ
class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


# 2. Định nghĩa Data Model bất biến với @dataclass
@dataclass(slots=True, frozen=True)
class Task:
    id: int
    title: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    tags: tuple[str, ...] = ()  # Tuple bất biến thay cho list
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def mark_completed(self) -> Self:
        """Vì class là frozen (bất biến), phương thức trả về một bản sao mới với trạng thái DONE."""
        return Task(
            id=self.id,
            title=self.title,
            priority=self.priority,
            status=TaskStatus.DONE,
            tags=self.tags,
            created_at=self.created_at,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# 3. Interface Repository trừu tượng
class ITaskRepository(ABC):
    @abstractmethod
    def add(self, task: Task) -> None:
        """Thêm task mới."""

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        """Tìm task theo ID."""

    @abstractmethod
    def list_all(self) -> list[Task]:
        """Liệt kê toàn bộ task."""


# 4. Triển khai InMemory Repository cụ thể
class InMemoryTaskRepository(ITaskRepository):
    def __init__(self) -> None:
        self._storage: dict[int, Task] = {}

    def add(self, task: Task) -> None:
        self._storage[task.id] = task

    def get_by_id(self, task_id: int) -> Task | None:
        return self._storage.get(task_id)

    def list_all(self) -> list[Task]:
        return list(self._storage.values())


# 5. Kiểm thử hoạt động
def main() -> None:
    repo: ITaskRepository = InMemoryTaskRepository()

    t1 = Task(id=1, title="Học lập trình Python hiện đại", priority=TaskPriority.HIGH)
    t2 = Task(
        id=2,
        title="Triển khai Milestone M0",
        priority=TaskPriority.CRITICAL,
        tags=("python", "cli"),
    )

    repo.add(t1)
    repo.add(t2)

    print(f"Tổng số task trong kho: {len(repo.list_all())}")
    for item in repo.list_all():
        print(f"[{item.priority}] {item.title} -> {item.status}")

    # Cập nhật trạng thái bất biến
    t1_updated = t1.mark_completed()
    repo.add(t1_updated)
    print(f"\nSau khi hoàn thành: Task 1 Status = {repo.get_by_id(1).status}")  # type: ignore[union-attr]


if __name__ == "__main__":
    main()
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên tham số `self` trong phương thức của instance
- **Lỗi**:
  ```python
  class Worker:
      def run():  # Quên self!
          print("Working...")
  ```
- **Hậu quả**: Khi gọi `Worker().run()`, Python sẽ báo lỗi:
  `TypeError: Worker.run() takes 0 positional arguments but 1 was given` (bởi vì Python luôn tự động truyền instance vào vị trí đối số đầu tiên).

### 2. Sử dụng class attribute mutable thay vì gán trong `__init__`
- Khai báo biến danh sách hay từ điển trực tiếp trong thân class sẽ biến nó thành biến tĩnh dùng chung giữa tất cả các instance, gây lỗi rò rỉ dữ liệu chéo rất khó phát hiện.

### 3. Dùng `__private` biến tướng thay vì `_protected`
- Lạm dụng 2 gạch dưới `__foo` tạo ra sự phức tạp không cần thiết (Name Mangling) khiến việc kế thừa, debug hoặc viết unit test gặp nhiều trở ngại. Hãy dùng 1 gạch dưới `_foo` cho 99% các trường hợp nội bộ.

### 4. Gán mutable default trực tiếp trong `@dataclass`
- Viết `items: list[str] = []` sẽ bị dataclass chặn lại ngay từ lúc khởi chạy module. Hãy dùng `items: list[str] = field(default_factory=list)`.

---

## ✍️ Bài tập thực hành

### Bài 1: Xây dựng tập hằng số nghiệp vụ với `StrEnum`
Tạo file chứa các enum đại diện cho hệ thống phân quyền:
1. Tạo `UserRole(StrEnum)` gồm các giá trị: `ADMIN = "ADMIN"`, `MEMBER = "MEMBER"`, `GUEST = "GUEST"`.
2. Tạo hàm `can_delete_task(role: UserRole) -> bool` trả về `True` nếu là `ADMIN`, ngược lại trả về `False`.
3. Kiểm tra xem chuỗi `"ADMIN"` khi so sánh với `UserRole.ADMIN` có bằng nhau không.

<details>
<summary>💡 Gợi ý</summary>

```python
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"


def can_delete_task(role: UserRole) -> bool:
    return role == UserRole.ADMIN


# Kiểm thử so sánh
assert "ADMIN" == UserRole.ADMIN
assert can_delete_task(UserRole.ADMIN) is True
assert can_delete_task(UserRole.MEMBER) is False
```
</details>

---

### Bài 2: Mô hình hóa Task Model với `@dataclass(slots=True, frozen=True)`
Xây dựng lớp dữ liệu `TaskItem`:
1. Sử dụng decorator `@dataclass(slots=True, frozen=True)`.
2. Các trường thuộc tính:
   - `id`: kiểu `int`.
   - `title`: kiểu `str`.
   - `is_done`: kiểu `bool`, mặc định `False`.
   - `notes`: kiểu `list[str]`, sử dụng `field(default_factory=list)`.
3. Viết phương thức `add_note(self, note: str) -> Self` trả về một instance mới với danh sách ghi chú đã bổ sung (do instance hiện tại bị đóng băng bất biến).

<details>
<summary>💡 Gợi ý</summary>

```python
from dataclasses import dataclass, field
from typing import Self


@dataclass(slots=True, frozen=True)
class TaskItem:
    id: int
    title: str
    is_done: bool = False
    notes: list[str] = field(default_factory=list)

    def add_note(self, note: str) -> Self:
        new_notes = [*self.notes, note]
        return TaskItem(
            id=self.id,
            title=self.title,
            is_done=self.is_done,
            notes=new_notes,
        )
```
</details>

---

### Bài 3: Thiết kế Repository Pattern với Abstract Base Class
1. Định nghĩa interface `IRepository[T]` sử dụng `abc.ABC`:
   - `@abstractmethod def add(self, item: T) -> None`
   - `@abstractmethod def get(self, id: int) -> T | None`
   - `@abstractmethod def delete(self, id: int) -> bool`
2. Tạo class cụ thể `InMemoryUserRepository` hiện thực hóa interface trên để quản lý một dictionary `{id: username}`.

<details>
<summary>💡 Gợi ý</summary>

```python
from abc import ABC, abstractmethod


class IRepository[T](ABC):
    @abstractmethod
    def add(self, item: T) -> None:
        pass

    @abstractmethod
    def get(self, id: int) -> T | None:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass


class InMemoryUserRepository(IRepository[str]):
    def __init__(self) -> None:
        self._data: dict[int, str] = {}

    def add(self, item: str) -> None:
        new_id = len(self._data) + 1
        self._data[new_id] = item

    def get(self, id: int) -> str | None:
        return self._data.get(id)

    def delete(self, id: int) -> bool:
        return self._data.pop(id, None) is not None
```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ cơ chế truyền `self` tường minh trong Python so với `this` trong C#?
- [ ] Bạn phân biệt được nguy cơ rò rỉ dữ liệu của mutable class attribute và biết cách khởi tạo đúng trong `__init__`?
- [ ] Bạn biết cách sử dụng `@property` và `@setter` để đóng gói dữ liệu mà vẫn giữ cú pháp truy cập tự nhiên?
- [ ] Bạn hiểu sự khác biệt giữa `@classmethod` (nhận `cls`) và `@staticmethod`?
- [ ] Bạn hiểu ý nghĩa của quy ước `_protected` và cơ chế name mangling của `__mangled`?
- [ ] Bạn nắm vững các dunder methods cốt lõi (`__str__`, `__repr__`, `__eq__`, `__hash__`)?
- [ ] Bạn nắm vững cú pháp kế thừa `class Child(Parent):` và biết cách gọi `super().__init__(...)` để khởi tạo lớp cha?
- [ ] Bạn biết cách tạo abstract class / interface bằng `abc.ABC` và `@abstractmethod`?
- [ ] Bạn thành thạo việc tạo dữ liệu bất biến, tiết kiệm RAM với `@dataclass(slots=True, frozen=True)`?

---

## 📚 Đọc thêm

- [Python Documentation – Classes and Object-Oriented Programming](https://docs.python.org/3/tutorial/classes.html)
- [Python Documentation – `dataclasses` module](https://docs.python.org/3/library/dataclasses.html)
- [PEP 557 – Data Classes](https://peps.python.org/pep-0557/)
- [Python Documentation – `abc` — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [Python Documentation – `enum` — Support for enumerations](https://docs.python.org/3/library/enum.html)

<!-- nav:bottom -->
---

[⬅️ File I/O & JSON](./08-file-io-json.md) | [📚 Mục lục Fresher](./README.md) | [Type hints cơ bản ➡️](./10-type-hints-basics.md)
<!-- /nav:bottom -->
