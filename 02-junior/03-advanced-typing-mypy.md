<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 03
<!-- /nav:top -->

# Typing nâng cao & mypy

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 02: Decorator & context manager](./02-decorators-context-managers.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Làm chủ cú pháp **Generic** hiện đại của Python 3.12+ theo **PEP 695** (`def func[T](...)`, `class Box[T]`, `type Alias[T] = ...`) và so sánh với cú pháp `TypeVar` truyền thống.
- Hiểu sâu bản chất **Structural Subtyping (Static Duck Typing)** với **`typing.Protocol`**, đối chiếu với `interface` của C# (.NET).
- Khai thác sức mạnh của **`Annotated[T, ...]`** (PEP 593) – công cụ gắn metadata nền tảng cho **FastAPI** (`Depends`, `Query`, `Path`, `Body`).
- Nắm vững các công cụ typing chuyên sâu: `ParamSpec`, `TypeGuard`, `Literal`, và toán tử hợp kiểu Union (`|`).
- Thiết lập cấu hình kiểm tra kiểu tĩnh ở mức độ nghiêm ngặt cao nhất (**`mypy --strict`**) trong tệp `pyproject.toml`.

---

## 🔁 So sánh với C# / ASP.NET

Trong C#, hệ thống Type System là tĩnh hoàn toàn (Static & Nominal Typing) và được enforced ở cả tầng Compiler (Roslyn) lẫn Runtime (CLR). Trong Python, kiểu dữ liệu lúc runtime vẫn là dynamic, nhưng thông qua **Type Hints (PEP 484+)** và công cụ phân tích tĩnh như **`mypy`** hoặc **Pylance**, bạn có thể đạt được mức độ an toàn kiểu (Type Safety) tương đương C# mà vẫn giữ được sự linh hoạt kỳ diệu của Python.

| Khái niệm / Cú pháp | C# / .NET | Python 3.12+ |
|---|---|---|
| **Cơ chế kiểm tra kiểu** | Nominal Typing (so khớp theo tên class/interface được kế thừa tường minh) | Structural Subtyping (Static Duck Typing qua `typing.Protocol`) |
| **Khai báo Generic** | `public T First<T>(List<T> items)` | `def first[T](items: list[T]) -> T:` (PEP 695) |
| **Generic Class** | `public class Box<T> { public T Value { get; set; } }` | `class Box[T]: value: T` |
| **Định nghĩa Type Alias** | `using UserId = System.Guid;` | `type UserId = int` hoặc `type StringList = list[str]` |
| **Interface / Khế ước** | `public interface IRepository<T> { ... }` (Bắt buộc phải `: IRepository<T>`) | `class Repository[T](Protocol): ...` (Không cần kế thừa tường minh!) |
| **Gắn Metadata vào Kiểu** | `[FromQuery] string query` (Custom Attributes) | `Annotated[str, Query()]` (PEP 593) |
| **Tập giá trị hữu hạn** | `public enum Status { Pending, Active }` | `Literal["pending", "active"]` hoặc `Enum` |
| **Kiểm tra kiểu lúc Runtime** | `if (obj is IDisposable d) { ... }` | `isinstance(obj, ...)` (cần `@runtime_checkable` với `Protocol`) |
| **Trình kiểm tra kiểu tĩnh** | C# Roslyn Compiler (tích hợp sẵn) | `mypy --strict` hoặc `pyright` (chạy độc lập qua CLI / IDE) |

---

## 📖 Lý thuyết

### 1. Cú pháp Generic hiện đại trong Python 3.12+ (PEP 695)

Trước Python 3.12, việc viết hàm Generic đòi hỏi bạn phải import `TypeVar` từ module `typing`:

```python
# Cách cũ (Python 3.11 trở về trước)
from typing import TypeVar

T = TypeVar("T")


def get_first_old(items: list[T]) -> T:
    return items[0]
```

Từ **Python 3.12+ (PEP 695)**, Python giới thiệu cú pháp Generic trực tiếp bằng dấu ngoặc vuông `[T]` ngay sau tên hàm hoặc tên class, hoàn toàn quen thuộc với các kỹ sư C#:

#### a. Generic Function
```python
def get_first[T](items: list[T]) -> T:
    """Trả về phần tử đầu tiên của danh sách với kiểu dữ liệu được giữ nguyên."""
    return items[0]


num = get_first([1, 2, 3])  # mypy suy luận kiểu: int
name = get_first(["alice", "bob"])  # mypy suy luận kiểu: str
```

#### b. Generic Class
```python
class Box[T]:
    """Hộp chứa một giá trị bất kỳ."""

    def __init__(self, value: T) -> None:
        self.value: T = value

    def get_value(self) -> T:
        return self.value


box_int = Box(100)  # Box[int]
box_str = Box("FastAPI")  # Box[str]
```

#### c. Ràng buộc kiểu dữ liệu (Type Constraints & Bounds)
Trong C#, bạn dùng mệnh đề `where T : class` hoặc `where T : IComparable`. Trong Python 3.12+:

```python
# T chỉ có thể là int hoặc str (Type constraint)
def double[T: (int, str)](val: T) -> T:
    return val * 2


# T phải kế thừa từ Exception (Type bound)
def handle_error[T: Exception](exc: T) -> str:
    return f"Lỗi: {exc}"
```

#### d. Cú pháp `type` statement mới cho Type Alias
```python
type Result[T] = dict[str, T]
type Coordinates = tuple[float, float]
type Matrix[T] = list[list[T]]
```

### 2. Structural Subtyping với `typing.Protocol` (Static Duck Typing)

Đây là điểm khác biệt triệt để nhất giữa OOP trong C# và Python:

- **Nominal Typing trong C#**: Class `UserRepository` **bắt buộc** phải ghi rõ `class UserRepository : IRepository` thì mới được coi là một `IRepository`. Dù nó có đủ các phương thức y hệt nhưng không kế thừa thì compiler vẫn báo lỗi.
- **Structural Subtyping trong Python (`typing.Protocol`)**: Nếu một đối tượng có hình dáng, thuộc tính và phương thức khớp với `Protocol`, trình kiểm tra kiểu (`mypy`) sẽ chấp nhận nó **mà không cần class đó kế thừa từ Protocol**! Đây chính là triết lý: *"Nếu nó đi như một con vịt và kêu như một con vịt, thì nó là một con vịt"*, nhưng được kiểm tra an toàn tại thời điểm phân tích tĩnh (Static Time).

```python
from typing import Protocol, runtime_checkable


# Định nghĩa khế ước (tương đương Interface trong C#)
@runtime_checkable
class Notifiable(Protocol):

    def send_notification(self, message: str) -> bool:
        """Gửi thông báo tới người nhận."""
        ...


# Class EmailService HOÀN TOÀN KHÔNG kế thừa Notifiable!
class EmailService:

    def send_notification(self, message: str) -> bool:
        print(f"📧 Gửi email: {message}")
        return True


# Class SMSService cũng KHÔNG kế thừa Notifiable!
class SMSService:

    def send_notification(self, message: str) -> bool:
        print(f"📱 Gửi SMS: {message}")
        return True


# Hàm nhận vào bất kỳ đối tượng nào thỏa mãn Notifiable Protocol
def broadcast_alert(notifier: Notifiable, msg: str) -> None:
    notifier.send_notification(msg)


# mypy HOÀN TOÀN HỢP LỆ VÀ KHÔNG BÁO LỖI:
broadcast_alert(EmailService(), "Cảnh báo bảo mật!")
broadcast_alert(SMSService(), "OTP xác thực: 123456")
```

> [!NOTE]
> Decorator `@runtime_checkable` cho phép bạn dùng `isinstance(EmailService(), Notifiable)` lúc runtime để kiểm tra xem một object có đáp ứng Protocol hay không. Nếu không có decorator này, `isinstance` trên Protocol sẽ ném ngoại lệ `TypeError`.

### 3. `Annotated[T, ...]`: Trái tim của FastAPI hiện đại

Được giới thiệu trong PEP 593 (Python 3.9), **`Annotated[T, Metadata1, Metadata2]`** cho phép bạn gắn thêm các thông tin phụ trợ (metadata) vào một kiểu dữ liệu mà **không làm thay đổi ý nghĩa kiểm tra kiểu tĩnh của `mypy`**.

Đối với `mypy`, `Annotated[int, ...]` đơn giản là một số nguyên `int`. Nhưng đối với các thư viện đọc metadata như **FastAPI** và **Pydantic**, các thông tin đi kèm này quyết định toàn bộ logic vận hành!

#### Ví dụ tiến hóa cú pháp trong FastAPI:
```python
# Phong cách cũ (FastAPI < 0.95): Dùng default parameter (dễ gây hiểu nhầm giá trị mặc định)
# def search(query: str = Query(min_length=3), db: Session = Depends(get_db)): ...

# Phong cách hiện đại (FastAPI khuyến nghị chuẩn): Sử dụng Annotated!
from typing import Annotated


# Định nghĩa Type Alias tái sử dụng
type DbSession = Annotated[dict, "Dependency: get_db_session"]
type SearchQuery = Annotated[str, "QueryParam: min_length=3, max_length=50"]


def search_users(q: SearchQuery, db: DbSession) -> list[str]:
    # mypy hiểu: q là str, db là dict
    # FastAPI hiểu: q cần validate QueryParam, db cần inject qua Depends
    return [f"Kết quả cho {q}"]
```

Nhờ `Annotated`, bạn có thể tạo ra các định dạng kiểu dữ liệu vừa được kiểm tra kiểu tĩnh nghiêm ngặt bởi `mypy`, vừa được tự động validate bởi Pydantic và FastAPI.

### 4. Các công cụ Typing chuyên sâu khác

#### a. `Literal`: Ràng buộc tập giá trị hằng
Thay vì tạo enum cồng kềnh cho các tập trạng thái nhỏ, hãy dùng `Literal`:

```python
from typing import Literal

type OrderStatus = Literal["pending", "processing", "completed", "cancelled"]


def update_status(status: OrderStatus) -> None:
    print(f"Cập nhật: {status}")


update_status("pending")  #  Hợp lệ
# update_status("deleted")  # ❌ mypy báo lỗi: Literal value không hợp lệ!
```

#### b. `TypeGuard`: Tinh chỉnh kiểu dữ liệu (Narrowing)
Tương tự tính năng Type Guard của TypeScript hoặc pattern matching của C#:

```python
from typing import Any, TypeGuard


def is_string_list(val: list[Any]) -> TypeGuard[list[str]]:
    """Kiểm tra xem danh sách có chứa toàn bộ phần tử kiểu chuỗi hay không."""
    return all(isinstance(x, str) for x in val)


def process_items(items: list[Any]) -> None:
    if is_string_list(items):
        # Bên trong khối if này, mypy tự động hiểu items là list[str]!
        print(", ".join(items))
```


#### c. `ParamSpec`: Bảo toàn Type Signature cho Decorator

Trong bài học trước ([02. Decorator & Context Manager](./02-decorators-context-managers.md)), khi tạo decorator bằng `Callable[..., Any]`, bạn sẽ đánh mất gợi ý tham số và kiểu trả về của hàm gốc trong IDE.

Python 3.10+ bổ sung **`ParamSpec`** (PEP 612) để giải quyết triệt để vấn đề này. `ParamSpec` đại diện cho toàn bộ danh sách tham số (args và kwargs) của một callable:

```python
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def log_execution(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator bảo toàn 100% chữ ký tham số (signature) và kiểu trả về."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Gọi hàm: {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


@log_execution
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    return amount * rate


# mypy và VS Code biết chính xác:
# calculate_tax(amount: float, rate: float = ...) -> float
total = calculate_tax(100.0, rate=0.08)  # ✅ Type-safe hoàn hảo!
```

### 5. Cấu hình `mypy --strict` trong `pyproject.toml`

Để dự án Python đạt tiêu chuẩn an toàn cấp doanh nghiệp (Enterprise-grade Type Safety), bạn nên cấu hình `mypy` ở chế độ khắt khe nhất (`--strict`).

Thêm đoạn cấu hình sau vào tệp `pyproject.toml` của dự án:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

Các cờ quan trọng:
- `disallow_untyped_defs = true`: Cấm viết hàm không có type annotation cho tham số và kết quả trả về.
- `no_implicit_optional = true`: Không cho phép tham số gán mặc định `arg: str = None` (phải viết tường minh `arg: str | None = None`).
- `strict = true`: Kích hoạt toàn bộ các cờ kiểm tra nghiêm ngặt của mypy.

---

## 💻 Ví dụ thực hành

Dưới đây là một mô hình thực chiến: Triển khai mẫu **Generic Repository Pattern** sử dụng cú pháp Generic Python 3.12+, `typing.Protocol`, và `Annotated` phục vụ Dependency Injection:

```python
from dataclasses import dataclass
from typing import Annotated, Protocol, runtime_checkable


# 1. Định nghĩa Entity có trường id
@dataclass
class User:
    id: int
    username: str
    email: str


@dataclass
class Product:
    id: int
    title: str
    price: float


# 2. Định nghĩa Generic Protocol cho Repository
@runtime_checkable
class Repository[T](Protocol):

    def get_by_id(self, entity_id: int) -> T | None:
        ...

    def add(self, entity: T) -> None:
        ...

    def list_all(self) -> list[T]:
        ...


# 3. Triển khai Generic In-Memory Repository
class InMemoryRepository[T]:
    """Không cần ghi kế thừa từ Repository[T], vẫn thỏa mãn Protocol!"""

    def __init__(self) -> None:
        self._storage: dict[int, T] = {}

    def get_by_id(self, entity_id: int) -> T | None:
        return self._storage.get(entity_id)

    def add(self, entity: T) -> None:
        # Giả định entity có thuộc tính id
        entity_id = getattr(entity, "id")
        self._storage[entity_id] = entity

    def list_all(self) -> list[T]:
        return list(self._storage.values())


# 4. Sử dụng Annotated cho Dependency Injection
type UserRepository = Annotated[
    Repository[User], "Dependency: Cung cấp Repository quản lý User"
]


# 5. Service Layer tiêu thụ Repository qua Interface
class UserService:

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def register_user(self, user_id: int, username: str, email: str) -> User:
        user = User(id=user_id, username=username, email=email)
        self.repo.add(user)
        print(f"Đã lưu user '{username}' vào hệ thống.")
        return user


# 6. Kiểm thử hoạt động
user_repo = InMemoryRepository[User]()
assert isinstance(user_repo, Repository), "Phải thỏa mãn Protocol!"

service = UserService(repo=user_repo)
service.register_user(1, "alice", "alice@example.com")

retrieved = user_repo.get_by_id(1)
assert retrieved is not None
print(f"Tìm thấy: {retrieved.username} - {retrieved.email}")
```

---

## ⚠️ Lỗi thường gặp

### 1. Hiểu lầm `Annotated` tự động kiểm tra dữ liệu lúc runtime

`Annotated` thuần túy là một công cụ khai báo Type Hint tĩnh. Bản thân CPython hoàn toàn không thực hiện bất kỳ hành động kiểm tra nào:

```python
from typing import Annotated

# Khai báo kiểu có metadata nhưng Python runtime sẽ không làm gì nếu không có thư viện đọc!
Age = Annotated[int, "gt=0, lt=120"]

# Đoạn code sau KHÔNG ném lỗi lúc runtime:
user_age: Age = -50  # Python vẫn cho chạy bình thường!
```
> [!WARNING]
> Để metadata trong `Annotated` được thực thi và validate dữ liệu thực tế, bạn cần các thư viện như **Pydantic v2** hoặc **FastAPI** phân tích và áp dụng validation rules.

### 2. Dùng `isinstance()` trên `Protocol` không có `@runtime_checkable`

Nếu bạn tạo một Protocol mà không đính kèm decorator `@runtime_checkable`, việc gọi `isinstance(obj, MyProtocol)` sẽ làm sập ứng dụng với lỗi:
`TypeError: Instance and class checks can only be used with @runtime_checkable protocols`.

### 3. Type Hints bị bỏ qua lúc Runtime

Nhiều lập trình viên C# lầm tưởng rằng khai báo `def add(a: int, b: int) -> int:` sẽ ngăn chặn việc người dùng truyền vào chuỗi. Trong Python, Type Hints chỉ dùng cho công cụ phân tích tĩnh (`mypy`, IDE). Nếu gọi `add("hello", "world")` lúc runtime, CPython vẫn thực thi bình thường!

### 4. Cấu hình mypy lơ là để lọt kiểu `Any`

Nếu không bật `disallow_untyped_defs = true` và `warn_return_any = true`, các biến hoặc kết quả hàm bị suy luận thành `Any` sẽ làm vô hiệu hóa khả năng kiểm tra lỗi của mypy ở các tầng tiếp theo.

---

## ✍️ Bài tập thực hành

### Bài 1: Xây dựng Generic Stack với cú pháp Python 3.12+
Triển khai một class Generic `Stack[T]` (ngăn xếp LIFO) với các phương thức:
- `push(item: T) -> None`: Thêm phần tử vào đỉnh ngăn xếp.
- `pop() -> T`: Lấy và xóa phần tử khỏi đỉnh ngăn xếp. Ném ngoại lệ `IndexError("Stack is empty")` nếu ngăn xếp rỗng.
- `peek() -> T | None`: Xem phần tử ở đỉnh mà không xóa. Trả về `None` nếu rỗng.
- `is_empty() -> bool`: Kiểm tra ngăn xếp có rỗng không.
- `__len__() -> int`: Trả về số lượng phần tử.
Viết type hint đầy đủ và kiểm tra với `Stack[int]` và `Stack[str]`.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng cú pháp Generic mới:
  ```python
  class Stack[T]:

      def __init__(self) -> None:
          self._items: list[T] = []

      def push(self, item: T) -> None:
          self._items.append(item)

      def pop(self) -> T:
          if not self._items:
              raise IndexError("Stack is empty")
          return self._items.pop()

      def peek(self) -> T | None:
          return self._items[-1] if self._items else None

      def is_empty() -> bool:
          return len(self._items) == 0

      def __len__(self) -> int:
          return len(self._items)
  ```
</details>

---

### Bài 2: Thiết kế Pipeline Transformer với `Protocol`
Định nghĩa một `Protocol` tên là `Transformer[InputT, OutputT]`:
- Phương thức `transform(self, data: InputT) -> OutputT`.
- Viết 2 class độc lập (không kế thừa tường minh từ `Transformer`):
  1. `TextNormalizer`: nhận vào `str` và trả về `str` (chuyển chữ thường, xóa khoảng trắng đầu cuối).
  2. `WordCounter`: nhận vào `str` và trả về `dict[str, int]` (đếm số lần xuất hiện của mỗi từ).
- Viết hàm `apply_transformation[In, Out](transformer: Transformer[In, Out], data: In) -> Out` nhận transformer và dữ liệu để thực thi.

<details>
<summary>💡 Gợi ý</summary>

- Định nghĩa Protocol với 2 biến kiểu:
```python
from typing import Protocol


class Transformer[InputT, OutputT](Protocol):

    def transform(self, data: InputT) -> OutputT:
        ...
```
- Các class chỉ cần triển khai phương thức `transform` có signature tương ứng.
</details>

---

### Bài 3: Ràng buộc kiểu dữ liệu số với Type Constraints (Ràng buộc tập kiểu)
Viết hàm Generic `calculate_discount[T: (int, float)](price: T, discount_percentage: float) -> float`:
- Ràng buộc tham số `price` chỉ được phép là `int` hoặc `float`.
- Nếu truyền vào kiểu dữ liệu khác như `str`, mypy sẽ phát hiện lỗi tĩnh.
- Tính toán giá tiền sau chiết khấu và trả về số thực `float`.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng cú pháp ràng buộc type bound: `def calculate_discount[T: (int, float)](price: T, discount_percentage: float) -> float:`.
- Logic tính: `return float(price) * (1.0 - discount_percentage / 100.0)`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn đã nắm vững cú pháp Generic PEP 695 mới (`def func[T]()`, `class Box[T]`, `type Alias[T]`)?
- [ ] Bạn hiểu rõ Structural Subtyping (`typing.Protocol`) khác với Interface kế thừa của C# như thế nào?
- [ ] Bạn hiểu vai trò của `Annotated[T, ...]` và cách FastAPI tận dụng nó cho Dependency Injection và Validation?
- [ ] Bạn phân biệt được khi nào dùng `Literal`, `Union` (`|`), và `TypeGuard`?
- [ ] Bạn biết cách cấu hình `mypy --strict` trong `pyproject.toml` để đảm bảo an toàn kiểu tối đa?

---

## 📚 Đọc thêm

- [PEP 695 – Type Parameter Syntax (Python 3.12)](https://peps.python.org/pep-0695/)
- [PEP 544 – Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [PEP 593 – Flexible function and variable annotations (`Annotated`)](https://peps.python.org/pep-0593/)
- [Mypy Documentation – Strict Mode and Configuration](https://mypy.readthedocs.io/en/stable/config_file.html)

<!-- nav:bottom -->
---

[⬅️ Decorator & context manager](./02-decorators-context-managers.md) | [📚 Mục lục Junior](./README.md) | [pytest cơ bản ➡️](./04-pytest-basics.md)
<!-- /nav:bottom -->
