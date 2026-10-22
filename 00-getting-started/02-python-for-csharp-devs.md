<!-- nav:top -->
[🏠 Home](../README.md) › [Getting Started](./README.md) › Bài 02
<!-- /nav:top -->

# Python cho dev C#

> ⏱️ Thời lượng: ~2.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành Bài 01 và cài đặt môi trường thành công với `uv` và VS Code.

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Nắm vững sự khác biệt cốt lõi giữa C# và Python: hệ thống kiểu **Strong Dynamic Typing** kết hợp với **Optional Static Type Hints**, và mô hình thực thi CPython VM.
- Hiểu sâu cơ chế **thụt đầu dòng (indentation)** làm khối lệnh thay cho cặp ngoặc nhọn `{}` và quy ước chuẩn **PEP 8** (`snake_case` vs `PascalCase`).
- Tiếp thu triết lý thiết kế **Pythonic** thông qua **The Zen of Python** (`import this`).
- Làm chủ cơ chế **Truthiness** (`bool([]) == False`), sự khác biệt sống còn giữa `is None` và `== None`.
- Chuyển dịch tư duy xử lý ngoại lệ từ **LBYL** (*Look Before You Leap*) quen thuộc trong C# sang **EAFP** (*Easier to Ask for Forgiveness than Permission*) trong Python.

---

## 🔁 So sánh với C# / ASP.NET

Bảng đối chiếu toàn diện dưới đây giúp bạn nhanh chóng liên hệ kinh nghiệm C# sẵn có sang các khái niệm tương ứng trong Python:

| Đặc điểm ngôn ngữ | C# / .NET (.NET 8/9) | Python hiện đại (Python 3.13+) |
|---|---|---|
| **Hệ thống kiểu (Type System)** | Static, Manifest / Inferred Typing (`int x`, `var x`) | Strong Dynamic Typing + Optional Static Type Hints (`x: int`) |
| **Khối lệnh (Code Block)** | Cặp ngoặc nhọn `{ ... }` | Thụt lề thụt dòng (Indentation - chuẩn 4 spaces) |
| **Mô hình thực thi** | Biên dịch sang CIL Bytecode → JIT compile sang mã máy | Biên dịch sang CPython Bytecode (`.pyc`) → Chạy trên CPython VM |
| **Quy ước đặt tên (Naming)** | Class, Method, Property: `PascalCase`<br>Biến cục bộ, tham số: `camelCase` | Class: `PascalCase`<br>Function, Method, Variable, Module: `snake_case`<br>Hằng số: `SCREAMING_SNAKE_CASE` |
| **Quản lý bộ nhớ (GC)** | Generational GC (Gen 0, 1, 2) dọn dẹp theo chu kỳ | **Reference Counting** (giải phóng tức thì khi refcount = 0) + Cycle GC |
| **Tổ chức mã nguồn** | `namespace Company.App`<br>Quy ước 1 file `.cs` chứa 1 Class | Module (mỗi file `.py` là 1 module), Package (thư mục)<br>1 file `.py` chứa nhiều class, function, biến tự do |
| **Giá trị rỗng (Null)** | `null` (hoặc `Nullable<T>`, `T?`) | `None` (singleton object thuộc kiểu `NoneType`) |
| **Kiểm tra rỗng** | `if (user == null)` hoặc `if (user is null)` | `if user is None:` (tuyệt đối không dùng `== None`) |
| **Toán tử logic** | `&&`, `||`, `!` | `and`, `or`, `not` |
| **Giá trị Boolean** | `true`, `false` | `True`, `False` |
| **Nội suy chuỗi (Interpolation)** | `$"Xin chào {user.Name}"` | `f"Xin chào {user.name}"` (f-string) |
| **Khởi tạo đối tượng** | `var u = new User("Alice");` | `u = User("Alice")` (không có từ khóa `new`) |
| **Hàm khởi tạo (Constructor)** | `public User(string name) { ... }` | `def __init__(self, name: str) -> None: ...` |
| **Tham chiếu bản thân** | `this` (truy cập ngầm định hoặc tường minh) | `self` (phải khai báo tường minh làm tham số đầu tiên của method) |

---

## 📖 Lý thuyết

### 1. Strong Dynamic Typing: Python không phải là JavaScript!

Một hiểu lầm rất phổ biến của các lập trình viên C# khi mới nhìn vào Python là nghĩ rằng: *"Python là dynamic language giống như JavaScript, nghĩa là nó sẽ tự động ép kiểu lộn xộn"*.

Thực tế hoàn toàn ngược lại. Cần phân biệt rõ hai trục độc lập:
1. **Static Typing vs. Dynamic Typing**: Thời điểm kiểm tra kiểu dữ liệu (lúc compile-time hay runtime).
2. **Strong Typing vs. Weak Typing**: Mức độ nghiêm ngặt trong việc chuyển đổi kiểu dữ liệu ngầm định (coercion).

```
                 Static Typing                 Dynamic Typing
        ┌─────────────────────────────┬─────────────────────────────┐
Strong  │ C#, Java, Rust, Go          │ Python, Ruby                │
Typing  │                             │                             │
        ├─────────────────────────────┼─────────────────────────────┤
Weak    │ C, C++ (cho phép cast con   │ JavaScript, PHP (cũ)        │
Typing  │ trỏ void* và tràn kiểu)     │ ("1" + 1 == "11", "1" - 1 == 0)│
        └─────────────────────────────┴─────────────────────────────┘
```

Trong JavaScript (Weak Dynamic Typing):
```javascript
"10" + 2  // Cho ra chuỗi "102" (tự ép kiểu ngầm int thành string)
"10" - 2  // Cho ra số 8 (tự ép kiểu ngầm string thành int)
```

Trong Python (Strong Dynamic Typing):
```python
# Cả hai dòng dưới đều lập tức ném lỗi TypeError!
# "10" + 2  -> TypeError: can only concatenate str (not "int") to str
# "10" - 2  -> TypeError: unsupported operand type(s) for -: 'str' and 'int'
```
Python **tuyệt đối không bao giờ tự động ép kiểu ngầm** giữa các kiểu dữ liệu không tương thích. Mọi thao tác chuyển đổi kiểu bắt buộc phải thực hiện tường minh: `int("10") + 2` hoặc `"10" + str(2)`.

#### Bản chất Dynamic trong Python: Biến chỉ là "nhãn dán" (Name Binding)
Trong C#, khi bạn khai báo `int age = 25;`, hệ điều hành cấp phát 4 bytes trên Stack (hoặc Heap nếu là boxing/field) mang kiểu cố định `int`. Biến `age` chính là ô nhớ đó.

Trong Python, mọi thứ đều là đối tượng trong Heap. Biến số chỉ là một chiếc **nhãn dán (reference)** trỏ tới đối tượng đó.
```python
age = 25       # Tạo một int object (25) trên Heap, dán nhãn 'age' vào nó
age = "hai mươi lăm"  # Tạo một str object trên Heap, bóc nhãn 'age' dán sang str object
```
Bản thân biến `age` không có kiểu, chính đối tượng mà nó trỏ tới mới có kiểu.

#### Vai trò của Static Type Hints (PEP 484)
Kể từ Python 3.5 và đặc biệt hoàn thiện ở Python 3.12+, Python cho phép bạn khai báo type hints:
```python
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    return amount * rate
```
- **Lúc Runtime**: Trình thông dịch CPython hoàn toàn phớt lờ type hints này để giữ nguyên tốc độ và tính linh hoạt vốn có.
- **Lúc Development**: Công cụ phân tích tĩnh (**Pylance**, **Mypy**, **Ruff**) đọc các type hints này và cảnh báo lỗi kiểu ngay lập tức trên IDE giống hệt như trình biên dịch C# Roslyn!

### 2. Truthiness và Giá trị Falsy trong Python

Trong C#, điều kiện của câu lệnh `if` bắt buộc phải là một biểu thức có giá trị trả về kiểu `bool`:
```csharp
// Trong C#: Bắt buộc phải so sánh rõ ràng ra bool
if (users != null && users.Count > 0) { ... }
if (name != null && name.Length > 0) { ... }
```

Trong Python, **mọi đối tượng đều có thể được ép kiểu thành bool một cách tự nhiên (Truth Value Testing)**. Các giá trị sau đây được coi là **Falsy** (tương đương `False`):
- `False` và `None`
- Số `0`, `0.0`, `0j` (số phức 0)
- Chuỗi rỗng: `""`
- Các collection rỗng: `[]` (list), `()` (tuple), `{}` (dict), `set()`

Mọi giá trị khác đều là **Truthy** (tương đương `True`).

Vì vậy, phong cách chuẩn Pythonic sẽ viết:
```python
users: list[str] = ["Alice", "Bob"]

# Thay vì viết: if len(users) > 0:
if users:
    print("Có người dùng trong danh sách!")

name = ""
# Thay vì viết: if len(name) == 0:
if not name:
    print("Tên không được để trống!")
```

> [!WARNING]
> **Cẩn thận bẫy số 0**: Nếu một hàm nhận tham số `count: int | None = None` và bạn kiểm tra `if count:`, khi người dùng truyền `count = 0`, điều kiện sẽ đánh giá thành `False`! Hãy luôn kiểm tra rõ ràng `if count is not None:` khi biến có thể nhận giá trị số 0 hoặc chuỗi rỗng hợp lệ.

### 3. EAFP vs LBYL: Thay đổi tư duy xử lý lỗi

Trong C#, thói quen phổ biến là **LBYL (Look Before You Leap)**: Kiểm tra điều kiện cẩn thận trước khi thực hiện hành động để tránh exception (vì ném Exception trong .NET có chi phí tạo StackTrace rất tốn kém):
```csharp
// Phong cách LBYL trong C#:
if (userDictionary.ContainsKey(userId))
{
    var user = userDictionary[userId];
    Process(user);
}
```

Trong Python, triết lý được ưa chuộng là **EAFP (Easier to Ask for Forgiveness than Permission)**: Cứ thực hiện hành động, nếu có lỗi phát sinh thì bắt và xử lý trong khối `except`:
```python
# Phong cách EAFP trong Python:
try:
    user = user_dictionary[user_id]
    process(user)
except KeyError:
    handle_missing_user(user_id)
```

**Tại sao Python lại chuộng EAFP?**
1. **Hiệu năng (Zero-cost exceptions)**: Trong Python 3.11+, các khối `try` bình thường không tốn bất kỳ chi phí thực thi nào nếu không có exception xảy ra (*Zero-cost exception tables*).
2. **Tránh Race Condition (TOCTOU - Time of Check to Time of Use)**: Trong LBYL, giữa lúc bạn kiểm tra `os.path.exists(file)` và lúc bạn gọi `open(file)`, một tiến trình khác có thể đã xóa mất file đó. Với EAFP, bạn gọi thẳng `open(file)` trong `try...except FileNotFoundError`, đảm bảo tính nguyên tử.
3. **Mã nguồn tự nhiên**: Phương thức built-in của `dict` kết hợp cả hai triết lý: `user = user_dictionary.get(user_id, default_user)`.

### 4. Triết lý "The Zen of Python"

Hãy mở terminal hoặc Python REPL và gõ `python -c "import this"`. Bạn sẽ thấy 19 dòng triết lý của Tim Peters định hình toàn bộ văn hóa lập trình Python:

- *Beautiful is better than ugly.* (Đẹp đẽ tốt hơn xấu xí.)
- *Explicit is better than implicit.* (Tường minh tốt hơn ngầm định.)
- *Simple is better than complex.* (Đơn giản tốt hơn phức tạp.)
- *Flat is better than nested.* (Phẳng tốt hơn lồng ghép nhiều tầng.)
- *Readability counts.* (Khả năng đọc hiểu là ưu tiên tối thượng.)
- *There should be one-- and preferably only one --obvious way to do it.* (Nên có một — và tốt nhất chỉ một — cách rõ ràng nhất để giải quyết vấn đề.)

---

## 💻 Ví dụ

Để thấy rõ sự khác biệt giữa tư duy viết mã C# chuyển dịch máy móc sang Python và tư duy Pythonic thực thụ, hãy xem xét bài toán nghiệp vụ sau:

**Bài toán**: Lọc danh sách tài khoản, chỉ lấy các tài khoản đang hoạt động (`is_active == True`), chuẩn hóa email về chữ thường, và gom nhóm danh sách người dùng theo vai trò (`role`).

### Cách 1: "C# dịch nguyên xi sang Python" (Anti-pattern)

Lập trình viên C# mới sang Python thường tạo class với các trường private giả lập `_name`, phương thức getter/setter thủ công, dùng vòng lặp chỉ số `range(len(...))`, và kiểm tra `== None`:

```python
from typing import Any


class UserCSharpStyle:
    def __init__(self, user_id: int, username: str, email: str | None, role: str, is_active: bool) -> None:
        self._user_id = user_id
        self._username = username
        self._email = email
        self._role = role
        self._is_active = is_active

    def get_user_id(self) -> int:
        return self._user_id

    def get_username(self) -> str:
        return self._username

    def get_email(self) -> str | None:
        return self._email

    def get_role(self) -> str:
        return self._role

    def is_active(self) -> bool:
        return self._is_active


def group_active_users_csharp_style(raw_users: list[UserCSharpStyle]) -> dict[str, list[dict[str, Any]]]:
    # Khởi tạo Dictionary gom nhóm thủ công
    grouped_users: dict[str, list[dict[str, Any]]] = {}

    # Dùng vòng lặp index theo thói quen for (int i = 0; i < list.Count; i++)
    for i in range(len(raw_users)):
        user = raw_users[i]

        # Kiểm tra boolean thủ công
        if user.is_active() is True:
            email_val = user.get_email()
            # Lỗi so sánh: dùng == None thay vì is None
            normalized_email = "" if email_val == None else email_val.strip().lower()

            role = user.get_role()
            # Kiểm tra key tồn tại trước khi khởi tạo (LBYL)
            if role not in grouped_users:
                grouped_users[role] = []

            user_dict = {
                "id": user.get_user_id(),
                "name": user.get_username(),
                "email": normalized_email,
            }
            grouped_users[role].append(user_dict)

    return grouped_users
```

Đoạn mã trên tuy chạy được nhưng rất dài dòng, không tận dụng các tính năng tinh hoa của ngôn ngữ, và vi phạm hàng loạt quy ước Pythonic.

### Cách 2: "Phong cách Pythonic chuẩn mực"

Sử dụng `@dataclass`, unpacking, List Comprehension, `collections.defaultdict`, và toán tử `is None`:

```python
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    user_id: int
    username: str
    email: str | None
    role: str
    is_active: bool


def group_active_users_pythonic(users: list[User]) -> dict[str, list[dict[str, str | int]]]:
    """Lọc và gom nhóm người dùng đang hoạt động theo vai trò (Role)."""
    grouped_users: dict[str, list[dict[str, str | int]]] = defaultdict(list)

    # Lọc trực tiếp bằng Comprehension hoặc vòng lặp for-in tự nhiên
    for user in users:
        # Tận dụng truthiness: if user.is_active
        if not user.is_active:
            continue

        # Chuẩn hóa email an toàn và súc tích
        clean_email = user.email.strip().lower() if user.email is not None else ""

        # defaultdict tự động tạo list rỗng nếu key chưa tồn tại
        grouped_users[user.role].append({
            "id": user.user_id,
            "name": user.username,
            "email": clean_email,
        })

    # Chuyển đổi về dict chuẩn để trả về
    return dict(grouped_users)


# Chạy thử nghiệm
if __name__ == "__main__":
    sample_users = [
        User(1, "alice", "Alice@TaskFlow.IO ", "admin", True),
        User(2, "bob", None, "member", True),
        User(3, "charlie", "charlie@gmail.com", "member", False),
        User(4, "david", " DAVID@org.com", "guest", True),
    ]

    result = group_active_users_pythonic(sample_users)
    print("Kết quả gom nhóm người dùng:", result)
```

**Nhận xét**: Phiên bản Pythonic ngắn hơn một nửa số dòng, trong sáng, dễ đọc và tốc độ thực thi cao hơn đáng kể nhờ sử dụng các cấu trúc dữ liệu tối ưu hóa bằng C của Python runtime (`defaultdict`, `dataclass` slots).

---

## ⚠️ Lỗi thường gặp

### 1. So sánh `== None` thay vì `is None`
- **Hiện tượng**: Viết `if result == None:` hoặc `if result != None:`.
- **Bản chất**:
  - Toán tử `==` gọi phương thức ma thuật `__eq__()` của đối tượng bên trái. Một class tùy biến có thể override `__eq__` và trả về kết quả sai lệch hoặc làm chậm chương trình.
  - Toán tử `is` so sánh định danh ô nhớ (*Identity Comparison* - tương đương so sánh con trỏ `Object.ReferenceEquals(a, b)` trong C#).
  - Trong CPython, `None` là một **singleton** duy nhất trong toàn bộ tiến trình.
- **Quy tắc**: Luôn luôn viết `if result is None:` hoặc `if result is not None:`.

### 2. Đặt tên hàm và biến theo `PascalCase` hoặc `camelCase`
- **Hiện tượng**: `def CalculateTotalAmount(customerList):` hoặc `userFirstName = "John"`.
- **Hậu quả**: Vi phạm quy ước chuẩn cộng đồng PEP 8. Linter như Ruff sẽ cảnh báo mã code không chuẩn mực.
- **Quy tắc**:
  - Hàm, biến, module, package: luôn dùng `snake_case` (`calculate_total_amount`, `first_name`).
  - Class: dùng `PascalCase` (`TaskRepository`, `UserRole`).
  - Hằng số: dùng `SCREAMING_SNAKE_CASE` (`MAX_RETRIES`, `DEFAULT_TIMEOUT`).

### 3. Lạm dụng getter/setter thủ công `get_x()` và `set_x()`
- **Hiện tượng**: Tạo hàng loạt phương thức `get_name()`, `set_name()` theo thói quen Java/C# cũ.
- **Triết lý Python**: "Chúng ta đều là người lớn ở đây" (*We are all consenting adults here*). Hãy để các thuộc tính là public tự nhiên: `self.name = name`.
- Khi nào cần validate hoặc biến đổi logic khi truy cập thuộc tính? Hãy sử dụng decorator `@property`:
  ```python
  class Account:
      def __init__(self, balance: float) -> None:
          self._balance = balance

      @property
      def balance(self) -> float:
          return self._balance

      @balance.setter
      def balance(self, value: float) -> None:
          if value < 0:
              raise ValueError("Số dư tài khoản không thể âm!")
          self._balance = value
  ```
  Caller vẫn gọi `acc.balance = 100` tự nhiên như thuộc tính thông thường mà không phá vỡ public contract!

### 4. Bẫy Truthiness với số `0` hoặc chuỗi rỗng `""`
- **Hiện tượng**:
  ```python
  def apply_discount(total: float, discount: float | None = None) -> float:
      # LỖI: nếu người dùng truyền discount = 0.0 (không giảm giá),
      # điều kiện "not discount" sẽ là True và gán lại thành 0.05!
      if not discount:
          discount = 0.05
      return total * (1 - discount)
  ```
- **Khắc phục**: Luôn kiểm tra tường minh với `None`:
  ```python
  if discount is None:
      discount = 0.05
  ```

### 5. Mutable Default Arguments (Đối số mặc định khả biến)
- **Hiện tượng**:
  ```python
  # NGUY HIỂM: list rỗng [] được khởi tạo một lần duy nhất khi hàm được load!
  def add_tag(tag: str, tags: list[str] = []) -> list[str]:
      tags.append(tag)
      return tags

  print(add_tag("python"))  # ['python']
  print(add_tag("fastapi")) # ['python', 'fastapi'] -> Bị giữ lại từ lần gọi trước!
  ```
- **Khắc phục**: Dùng `None` làm sentinel value:
  ```python
  def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
      if tags is None:
          tags = []
      tags.append(tag)
      return tags
  ```

---

## 🏋️ Bài tập

### Bài tập 1: Tái cấu trúc vòng lặp chỉ số sang `enumerate` và Unpacking
Đoạn code C# sau được một bạn sinh viên dịch nguyên văn sang Python:
```python
def print_leaderboard(scores: list[tuple[str, int]]) -> None:
    for i in range(len(scores)):
        pair = scores[i]
        name = pair[0]
        score = pair[1]
        print(f"Hạng {i + 1}: {name} đạt {score} điểm")
```
Hãy viết lại hàm này theo phong cách Pythonic nhất, sử dụng `enumerate` và tuple unpacking trực tiếp trong vòng lặp.

<details>
<summary>💡 Gợi ý</summary>

```python
def print_leaderboard_pythonic(scores: list[tuple[str, int]]) -> None:
    for rank, (name, score) in enumerate(scores, start=1):
        print(f"Hạng {rank}: {name} đạt {score} điểm")


# Chạy thử
sample_scores = [("Alice", 98), ("Bob", 85), ("Charlie", 72)]
print_leaderboard_pythonic(sample_scores)
```
</details>

---

### Bài tập 2: Tái cấu trúc Class C# sang `@property`
Cho class tài khoản ngân hàng sau đây:
```python
class BankAccountLegacy:
    def __init__(self, account_number: str, initial_balance: float) -> None:
        self._account_number = account_number
        self._balance = initial_balance

    def get_account_number(self) -> str:
        return self._account_number

    def get_balance(self) -> float:
        return self._balance

    def set_balance(self, new_balance: float) -> None:
        if new_balance < 0:
            raise ValueError("Số dư không thể là số âm")
        self._balance = new_balance
```
Hãy viết lại class `BankAccount` chuẩn Pythonic:
1. `account_number` là thuộc tính chỉ đọc (read-only property).
2. `balance` là property có getter và setter; setter kiểm tra nếu số tiền mới nhỏ hơn 0 thì ném ngoại lệ `ValueError`.

<details>
<summary>💡 Gợi ý</summary>

```python
class BankAccount:
    def __init__(self, account_number: str, initial_balance: float = 0.0) -> None:
        if initial_balance < 0:
            raise ValueError("Số dư ban đầu không thể âm")
        self._account_number = account_number
        self._balance = initial_balance

    @property
    def account_number(self) -> str:
        """Thuộc tính chỉ đọc, không có setter."""
        return self._account_number

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, new_balance: float) -> None:
        if new_balance < 0:
            raise ValueError("Số dư tài khoản không thể là số âm!")
        self._balance = new_balance


# Chạy thử
account = BankAccount("ACC-1002", 500.0)
print(f"Tài khoản: {account.account_number}, Số dư: {account.balance}")
account.balance += 250.0
print(f"Số dư mới: {account.balance}")
```
</details>

---

### Bài tập 3: Bộ phân tích Log File theo triết lý EAFP
Viết hàm `parse_log_line(line: str) -> dict[str, str | int] | None`. Mỗi dòng log có định dạng: `"[LEVEL] user_id:123 - message"`.
Ví dụ: `"[INFO] user_id:456 - User logged in successfully"`.
Yêu cầu:
- Sử dụng triết lý EAFP (khối `try...except`) để trích xuất `level`, `user_id` (ép kiểu sang `int`), và `message`.
- Nếu dòng log sai định dạng hoặc `user_id` không phải là số nguyên hợp lệ, bắt các lỗi `(ValueError, IndexError)` và trả về `None` thay vì làm gián đoạn chương trình.

<details>
<summary>💡 Gợi ý</summary>

```python
def parse_log_line(line: str) -> dict[str, str | int] | None:
    try:
        # Tách phần LEVEL nằm trong ngoặc vuông [LEVEL]
        prefix, rest = line.split("] ", 1)
        level = prefix.lstrip("[").strip()

        # Tách user_id và message thông qua dấu gạch ngang " - "
        user_part, message = rest.split(" - ", 1)
        _, user_id_str = user_part.split(":", 1)
        user_id = int(user_id_str.strip())

        return {
            "level": level,
            "user_id": user_id,
            "message": message.strip(),
        }
    except (ValueError, IndexError):
        # EAFP: bắt lỗi định dạng nhẹ nhàng và trả về None
        return None


# Kiểm thử hàm
logs = [
    "[INFO] user_id:101 - Đăng nhập thành công",
    "[ERROR] user_id:202 - Kết nối cơ sở dữ liệu thất bại",
    "DÒNG LOG BỊ LỖI ĐỊNH DẠNG",
    "[WARN] user_id:abc - Token sắp hết hạn",
]

for entry in logs:
    parsed = parse_log_line(entry)
    if parsed is not None:
        print("Trích xuất thành công:", parsed)
    else:
        print(f"Bỏ qua dòng log lỗi: '{entry}'")
```
</details>

---

## ✅ Checklist tự đánh giá

Hãy đối chiếu với checklist dưới đây trước khi chuyển sang Level 01 (Fresher):

- [ ] Tôi giải thích được vì sao Python là Strong Dynamic Typing và phân biệt được sự khác nhau giữa Python và JavaScript.
- [ ] Tôi hiểu rõ vai trò của Static Type Hints trong Python và cách Pylance/Mypy giúp phát hiện lỗi kiểu lúc viết code.
- [ ] Tôi biết danh sách các giá trị Falsy trong Python (`False`, `None`, `0`, `""`, `[]`, `{}`) và luôn cẩn thận khi kiểm tra số 0.
- [ ] Tôi luôn sử dụng toán tử `is None` và `is not None` thay cho `== None`.
- [ ] Tôi nắm vững quy tắc đặt tên PEP 8 (`snake_case` cho hàm/biến, `PascalCase` cho class).
- [ ] Tôi hiểu vì sao không nên lạm dụng getter/setter thủ công và biết cách dùng `@property`.
- [ ] Tôi hiểu sự khác biệt giữa triết lý EAFP (*Easier to Ask for Forgiveness than Permission*) và LBYL (*Look Before You Leap*).
- [ ] Tôi biết nguy cơ của Mutable Default Argument (`def func(items=[])`) và cách giải quyết bằng `None`.

---

## 🔗 Đọc thêm

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/): Quy chuẩn phong cách viết code chính thức của Python.
- [PEP 20 – The Zen of Python](https://peps.python.org/pep-0020/): 19 triết lý thiết kế ngôn ngữ của Tim Peters.
- [Python Data Model](https://docs.python.org/3/reference/datamodel.html): Tài liệu nền tảng giải thích bản chất object, dunder methods, reference counting trong Python.
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/): Đặc tả hệ thống chú thích kiểu dữ liệu trong Python.
- [What's New in Python 3.11: Zero-cost Exception Handling](https://docs.python.org/3/whatsnew/3.11.html#faster-cpython): Cơ chế tối ưu hóa ngoại lệ không tốn chi phí trong CPython hiện đại.

<!-- nav:bottom -->
---

[⬅️ Cài đặt môi trường](./01-setup-environment.md) | [📚 Mục lục Getting Started](./README.md) | [Fresher ➡️](../01-fresher/README.md)
<!-- /nav:bottom -->
