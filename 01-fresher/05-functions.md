<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 05
<!-- /nav:top -->

# Hàm

> ⏱️ Thời lượng: ~3.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 04: Comprehension](./04-comprehensions.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Định nghĩa hàm chuyên nghiệp với `def`, gắn type hints đầy đủ và trả về nhiều giá trị qua tuple unpacking.
- Sử dụng linh hoạt tham số vị trí biến thiên (`*args`) và tham số từ khóa biến thiên (`**kwargs`).
- Thiết kế API hàm chặt chẽ bằng cách phân định **Positional-Only (`/`)** và **Keyword-Only (`*`)** parameters theo chuẩn PEP 570 / PEP 3102.
- Làm chủ khái niệm First-Class Functions, biểu thức `lambda`, closure và quy tắc tìm kiếm biến **LEGB**.
- Thấu hiểu bản chất và phòng tránh triệt để **bẫy kinh điển Mutable Default Argument** (`def fn(items=[])`).

---

## 🔁 So sánh với C# / ASP.NET

Trong C#, hàm (method) bắt buộc phải thuộc về một `class` hoặc `struct`. Bạn có từ khóa `params` cho mảng tham số, `out` / `tuple` để trả về nhiều giá trị, và delegates (`Func<T>`, `Action<T>`) cho hàm ẩn danh.

Trong Python: Hàm là **công dân hạng nhất (First-Class Citizen)**, có thể tồn tại độc lập ở cấp module mà không cần bao bọc trong class, có thể gán vào biến, truyền vào hàm khác hoặc trả về từ hàm khác một cách tự nhiên.

| Khái niệm / Tính năng | C# / .NET | Python 3.13+ |
|---|---|---|
| **Định nghĩa hàm** | `public int Add(int a, int b) { ... }` | `def add(a: int, b: int) -> int: ...` |
| **Trả về nhiều giá trị** | `(bool Success, string Msg) DoWork()` | `return success, message` (tuple unpacking) |
| **Mảng tham số tùy biến** | `params object[] args` | `*args` (được gom thành `tuple`) |
| **Tham số từ khóa động** | Không có (hoặc dùng `Dictionary<string, object>`) | `**kwargs` (được gom thành `dict`) |
| **Bắt buộc truyền theo tên** | Không có (chỉ có named arguments tùy ý ở phía gọi) | Cú pháp `*`: `def f(*, key_only):` |
| **Bắt buộc truyền theo vị trí** | Mặc định vị trí, không cấm gọi named | Cú pháp `/`: `def f(pos_only, /):` |
| **Delegate / Hàm ẩn danh** | `Func<int, int> sq = x => x * x;` | `sq = lambda x: x * x` (hoặc định nghĩa bằng `def`) |
| **Phạm vi biến (Scope)** | Block scope `{}` | LEGB scope (Function / Module scope, không có block scope) |
| **Giá trị mặc định của tham số** | Đánh giá lại tại mỗi lần gọi hàm | **Đánh giá duy nhất 1 lần khi định nghĩa hàm!** |

---

## 📖 Lý thuyết

### 1. Định nghĩa hàm, Type Hints và Trả về nhiều giá trị

Hàm trong Python bắt đầu bằng từ khóa `def`. Bạn nên luôn luôn gắn type hints cho các tham số và kiểu trả về (chuẩn PEP 484) để IDE và Ruff hỗ trợ kiểm tra tĩnh:

```python
def calculate_tax(gross_salary: float, tax_rate: float = 0.1) -> float:
    return gross_salary * tax_rate
```

#### Trả về nhiều giá trị qua Tuple Unpacking
Khi một hàm trả về nhiều giá trị cách nhau bằng dấu phẩy, Python thực chất đóng gói chúng vào một `tuple`:

```python
def divide_and_remainder(a: int, b: int) -> tuple[int, int]:
    quotient = a // b
    remainder = a % b
    return quotient, remainder  # Tương đương: return (quotient, remainder)

# Ở phía gọi, giải nén trực tiếp:
q, r = divide_and_remainder(17, 5)
print(f"Thương: {q}, Số dư: {r}")  # Thương: 3, Số dư: 2
```

### 2. Hệ thống tham số linh hoạt: `*args` và `**kwargs`

Python cho phép hàm tiếp nhận số lượng đối số tùy ý:

1. **`*args` (Arbitrary Positional Arguments)**: Gom toàn bộ các đối số vị trí dư thừa vào một `tuple`.
2. **`**kwargs` (Arbitrary Keyword Arguments)**: Gom toàn bộ các đối số theo tên (`key=value`) dư thừa vào một `dict`.

```python
def log_event(level: str, *messages: str, **metadata: str) -> None:
    full_message = " ".join(messages)
    print(f"[{level.upper()}] {full_message}")
    if metadata:
        print(f"  Metadata: {metadata}")

# Gọi hàm với số lượng tham số linh hoạt:
log_event("info", "Người dùng", "alice", "vừa đăng nhập.")
log_event("warning", "Kết nối chậm", ip="192.168.1.1", latency_ms="250")
```

#### Unpacking khi gọi hàm (Argument Unpacking)
Bạn có thể dùng `*` để giải nén danh sách/tuple và `**` để giải nén dict truyền vào hàm:
```python
def configure_server(host: str, port: int, debug: bool) -> None:
    print(f"Server chạy tại {host}:{port} (Debug: {debug})")

opts = {"host": "127.0.0.1", "port": 8000, "debug": True}
configure_server(**opts)  # Giải nén dict thành các keyword arguments tương ứng
```

### 3. Thiết kế API: Positional-Only (`/`) và Keyword-Only (`*`)

Python cho phép người thiết kế API quy định chặt chẽ cách thức truyền tham số:

- **Dấu gạch chéo `/`**: Mọi tham số đứng **trước `/`** bắt buộc phải truyền theo vị trí (không được gọi `arg_name=val`).
- **Dấu sao `*`**: Mọi tham số đứng **sau `*`** bắt buộc phải truyền theo tên (keyword-only).

```python
def create_user(
    username: str,           # Có thể truyền theo vị trí hoặc theo tên
    /,                       # --- Mọi tham số trước đây là POSITIONAL-ONLY ---
    full_name: str,          # Vị trí hoặc tên đều được
    *,                       # --- Mọi tham số sau đây là KEYWORD-ONLY ---
    is_active: bool = True,  # Bắt buộc phải gọi theo tên: is_active=...
    role: str = "member"     # Bắt buộc phải gọi theo tên: role=...
) -> dict[str, str | bool]:
    return {
        "username": username,
        "full_name": full_name,
        "is_active": is_active,
        "role": role,
    }

# Gọi hợp lệ:
u1 = create_user("alice99", "Alice Nguyen", is_active=True, role="admin")

# LỖI: create_user(username="alice99", ...) -> TypeError: positional-only argument passed as keyword
# LỖI: create_user("alice99", "Alice Nguyen", True, "admin") -> TypeError: takes 2 positional arguments
```

### 4. Quy tắc Scope LEGB và Closures

Khác với C# kiểm soát biến theo cặp ngoặc nhọn `{}` (Block Scope), Python phân định phạm vi theo **LEGB**:
1. **L (Local)**: Biến khai báo bên trong hàm hiện tại.
2. **E (Enclosing)**: Biến thuộc các hàm bao bên ngoài (trong trường hợp hàm lồng nhau / closure).
3. **G (Global)**: Biến cấp module (file hiện tại).
4. **B (Built-in)**: Các tên hàm/lớp tích hợp sẵn của Python (`len`, `sum`, `range`, `print`).

#### Closure (Hàm bao đóng)
Một hàm bên trong có khả năng ghi nhớ và truy cập các biến trong phạm vi của hàm bên ngoài (Enclosing Scope) ngay cả khi hàm ngoài đã thực thi xong:

```python
def make_multiplier(factor: int):
    # 'factor' nằm ở Enclosing Scope
    def multiply(x: int) -> int:
        return x * factor  # Đóng gói và ghi nhớ 'factor'
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))  # 10
print(triple(5))  # 15
```

> [!NOTE]
> Nếu bạn muốn gán lại giá trị cho biến ở phạm vi Enclosing từ bên trong hàm con, hãy dùng từ khóa `nonlocal`. Nếu muốn gán lại biến ở cấp module, dùng từ khóa `global`.

### 5. Bẫy kinh điển: Mutable Default Argument

Đây là cạm bẫy nổi tiếng nhất trong toàn bộ ngôn ngữ Python đối với mọi lập trình viên đến từ C# hay Java!

#### Vấn đề
Trong C#, giá trị mặc định của tham số được trình biên dịch gán tại mỗi lời gọi hàm.
Trong Python: **Biểu thức giá trị mặc định của tham số được thực thi duy nhất 1 lần khi hàm được ĐỊNH NGHĨA (load module time), chứ KHÔNG PHẢI khi hàm được gọi!**

Nếu bạn đặt một đối tượng khả biến (mutable) như `list` hay `dict` làm giá trị mặc định:
```python
# CẢNH BÁO NGUY HIỂM: KHÔNG BAO GIỜ VIẾT NHƯ THẾ NÀY!
def append_to_list(val: int, items: list[int] = []) -> list[int]:
    items.append(val)
    return items

print(append_to_list(1))  # In ra: [1]
print(append_to_list(2))  # BẤT NGỜ: In ra [1, 2]! (Không phải [2])
print(append_to_list(3))  # In ra: [1, 2, 3]!
```
Danh sách mặc định `[]` được tạo ra một lần duy nhất trong bộ nhớ và dùng chung cho tất cả các lần gọi hàm không truyền tham số `items`.

#### Cách sửa chuẩn mực (Best Practice)
Luôn luôn sử dụng `None` làm giá trị sentinel (lính gác) mặc định:

```python
def append_to_list_safe(val: int, items: list[int] | None = None) -> list[int]:
    if items is None:
        items = []  # Tạo danh sách mới độc lập tại MỖI LẦN gọi hàm
    items.append(val)
    return items

print(append_to_list_safe(1))  # [1]
print(append_to_list_safe(2))  # [2] (Hoàn toàn chính xác)
```

---

## 💻 Ví dụ thực hành

Dưới đây là một mô đun tiện ích xác thực và phân quyền API, áp dụng first-class function, keyword-only args và closure:

```python
from collections.abc import Callable
from datetime import datetime
from typing import Any

# 1. Type alias cho hàm xử lý Request
RequestHandler = Callable[[dict[str, Any]], dict[str, Any]]

# 2. Hàm bậc cao (Higher-Order Function) tạo Middleware xác thực bằng Closure
def create_auth_middleware(required_role: str) -> Callable[[RequestHandler], RequestHandler]:
    def decorator(handler: RequestHandler) -> RequestHandler:
        def wrapped(request: dict[str, Any]) -> dict[str, Any]:
            user_role = request.get("user", {}).get("role", "guest")
            if user_role != required_role:
                return {
                    "status_code": 403,
                    "error": f"Từ chối truy cập: Yêu cầu quyền '{required_role}', vai trò hiện tại: '{user_role}'"
                }
            # Thực thi handler gốc nếu hợp lệ
            return handler(request)
        return wrapped
    return decorator

# 3. Hàm tạo phản hồi API sử dụng Positional-Only và Keyword-Only
def build_api_response(
    data: Any,
    /,                     # data là positional-only
    *,
    status_code: int = 200,
    trace_id: str = "TX-0000"
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(),
        "trace_id": trace_id,
        "status_code": status_code,
        "payload": data
    }

# 4. Handler xử lý nghiệp vụ xóa tác vụ
def delete_task_handler(request: dict[str, Any]) -> dict[str, Any]:
    task_id = request.get("task_id")
    return build_api_response({"message": f"Tác vụ #{task_id} đã bị xóa."}, status_code=200)

# Áp dụng middleware kiểm tra quyền 'admin'
secure_delete_handler = create_auth_middleware(required_role="admin")(delete_task_handler)

# 5. Thử nghiệm với các request khác nhau
guest_request = {"task_id": 42, "user": {"name": "Bob", "role": "member"}}
admin_request = {"task_id": 42, "user": {"name": "Alice", "role": "admin"}}

print("Request từ Member:")
print(" ", secure_delete_handler(guest_request))

print("\nRequest từ Admin:")
print(" ", secure_delete_handler(admin_request))
```

---

## ⚠️ Lỗi thường gặp

### 1. Bẫy Mutable Default Argument
Lỗi đặt `def register(user, tags=[])` hoặc `def cache(key, store={})`. Linter `ruff` (quy tắc `B006`) sẽ phát hiện và gắn cờ cảnh báo lỗi này ngay lập tức. Luôn dùng `= None`.

### 2. Lỗi `UnboundLocalError`
```python
counter = 0

def increment():
    # CPython thấy phép gán counter = counter + 1 nên coi counter là Local!
    # Nhưng counter ở vế phải lại được đọc trước khi gán -> Gây lỗi!
    # counter += 1  # LỖI: UnboundLocalError: cannot access local variable 'counter'
    pass

# Cách sửa nếu muốn sửa biến cấp module:
def increment_fixed():
    global counter
    counter += 1
```

### 3. Lạm dụng `lambda` thay cho `def`
`lambda` trong Python chỉ được phép chứa **duy nhất 1 biểu thức** (không có lệnh `return`, không có vòng lặp, không có nhiều dòng). 

PEP 8 nghiêm cấm việc gán lambda vào biến như:
```python
# SAI PEP 8:
# f = lambda x, y: x + y

# ĐÚNG PEP 8: Hãy dùng def thông thường
def add(x: int, y: int) -> int:
    return x + y
```
Chỉ nên dùng `lambda` cho các hàm ngắn dùng một lần khi truyền vào `sort(key=...)` hoặc `filter()`.

---

## ✍️ Bài tập thực hành

### Bài 1: Thiết kế hàm tính cước vận chuyển chuẩn PEP 570
Viết hàm `calculate_shipping`:
- Tham số `weight` (kg) và `distance` (km): Bắt buộc là **Positional-Only** (`/`).
- Tham số `shipping_type`: Có thể truyền theo vị trí hoặc tên, nhận giá trị `"standard"` hoặc `"express"` (mặc định `"standard"`).
- Tham số `insurance` (bool, mặc định `False`) và `coupon_code` (str | None, mặc định `None`): Bắt buộc là **Keyword-Only** (`*`).
- Công thức: 
  - Standard: 5,000 đ/km + 10,000 đ/kg.
  - Express: 8,000 đ/km + 15,000 đ/kg.
  - Bảo hiểm (`insurance`): cộng thêm 20,000 đ.
  - Coupon `"GIAM10"`: giảm 10% tổng cước.

<details>
<summary>💡 Gợi ý</summary>

- Khai báo: `def calculate_shipping(weight: float, distance: float, /, shipping_type: str = "standard", *, insurance: bool = False, coupon_code: str | None = None) -> float:`.
- Tính chi phí cơ sở tùy theo `shipping_type`.
- Cộng bảo hiểm nếu có, sau đó áp dụng coupon giảm giá.
</details>

---

### Bài 2: Khắc phục lỗi tích lũy dữ liệu giỏ hàng
Một lập trình viên mới viết hàm sau và gặp lỗi dữ liệu của khách hàng này bị dính sang khách hàng khác:
```python
def add_to_cart(item_name: str, price: float, cart: list[dict[str, Any]] = []) -> list[dict[str, Any]]:
    cart.append({"item": item_name, "price": price})
    return cart
```
Hãy sửa lại hàm trên theo đúng chuẩn Pythonic bằng cách dùng sentinel `None`, viết type hints chính xác và kiểm tra tính độc lập của 2 giỏ hàng khách hàng khác nhau.

<details>
<summary>💡 Gợi ý</summary>

- Thay đổi tham số: `cart: list[dict[str, Any]] | None = None`.
- Kiểm tra bên trong thân hàm: `if cart is None: cart = []`.
- Thử nghiệm gọi `cart_1 = add_to_cart("Sách", 50)` và `cart_2 = add_to_cart("Bút", 10)`. Đảm bảo `cart_1` chỉ có 1 phần tử.
</details>

---

### Bài 3: Bộ đếm thời gian thực thi bằng Closure
Viết một hàm `create_execution_counter()` sử dụng cơ chế Closure:
- Bên trong duy trì một biến `count = 0`.
- Trả về một hàm con `track(action_name: str) -> int`.
- Mỗi khi `track` được gọi, tăng `count` lên 1 và in ra thông báo: `"[Thống kê] Hành động '<action_name>' đã chạy tổng cộng: <count> lần"`.
- Trả về số lần đã chạy.
- Lưu ý sử dụng từ khóa `nonlocal` để cập nhật biến `count` ở scope bao ngoài.

<details>
<summary>💡 Gợi ý</summary>

- Định nghĩa:
  ```python
  def create_execution_counter():
      count = 0
      def track(action_name: str) -> int:
          nonlocal count
          count += 1
          print(f"[Thống kê] Hành động '{action_name}' đã chạy tổng cộng: {count} lần")
          return count
      return track
  ```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu và áp dụng thành thạo tuple unpacking để nhận nhiều giá trị trả về từ hàm?
- [ ] Bạn phân biệt rõ công dụng của `*args` (tuple) và `**kwargs` (dict)?
- [ ] Bạn biết cách dùng `/` và `*` để thiết lập Positional-Only và Keyword-Only parameters?
- [ ] Bạn hiểu sâu sắc vì sao mutable default argument là một cạm bẫy và biết cách khắc phục bằng `None`?
- [ ] Bạn nắm vững quy tắc scope LEGB và biết khi nào cần dùng từ khóa `nonlocal` hay `global`?

---

## 📚 Đọc thêm

- [PEP 570 – Python Positional-Only Parameters](https://peps.python.org/pep-0570/)
- [PEP 3102 – Keyword-Only Arguments](https://peps.python.org/pep-3102/)
- [Common Gotchas – Default Parameter Values](https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments)

<!-- nav:bottom -->
---

[⬅️ Comprehension](./04-comprehensions.md) | [📚 Mục lục Fresher](./README.md) | [Module & package ➡️](./06-modules-packages.md)
<!-- /nav:bottom -->
