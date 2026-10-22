<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 03
<!-- /nav:top -->

# Collections: list, tuple, dict, set

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 02: Điều kiện & vòng lặp](./02-control-flow.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Làm chủ 4 cấu trúc dữ liệu tích hợp cốt lõi của Python: `list`, `tuple`, `dict`, và `set` (kèm `frozenset`).
- Sử dụng thành thạo kỹ thuật cắt mảng (**Slicing** `[start:stop:step]`) và trích xuất dữ liệu đa năng (**Unpacking** `a, b, *rest = ...`).
- Nắm vững các thao tác trên `dict`: truy xuất an toàn với `.get()`, `.setdefault()`, và toán tử gộp từ điển `|` (Python 3.9+).
- Áp dụng các toán tử tập hợp toán học trên `set`: hợp (`|`), giao (`&`), hiệu (`-`), hiệu đối xứng (`^`).
- Thấu hiểu bản chất **Hashable** và lý do tại sao các kiểu khả biến (mutable) không thể làm key của `dict` hay phần tử của `set`.

---

## 🔁 So sánh với C# / ASP.NET

Trong C#, bạn làm việc với thư viện `System.Collections.Generic` và các kiểu dữ liệu có định kiểu tĩnh nghiêm ngặt (`List<T>`, `Dictionary<TKey, TValue>`). Trong Python, các cấu trúc dữ liệu là kiểu tích hợp sẵn (built-in types), không cần import và có thể chứa các phần tử thuộc nhiều kiểu khác nhau (dù trong thực tế chúng ta nên dùng type hints để giữ tính đồng nhất).

| Khái niệm / Cấu trúc | C# / .NET | Python 3.13+ |
|---|---|---|
| **Mảng động (Dynamic Array)** | `List<T>` | `list` (khả biến - mutable) |
| **Bản ghi bất biến (Immutable Sequence)** | `(int, string)` (Tuple / ValueTuple) | `tuple` (bất biến - immutable) |
| **Bảng băm (Hash Map)** | `Dictionary<TKey, TValue>` | `dict` (bảo toàn thứ tự chèn từ Python 3.7+) |
| **Tập hợp giá trị duy nhất** | `HashSet<T>` | `set` (mutable) và `frozenset` (immutable) |
| **Cắt mảng (Slicing)** | `items[1..^1]` (từ C# 8) | `items[1:-1]` hoặc `items[start:stop:step]` |
| **Trích xuất (Destructuring/Unpacking)** | `var (a, b) = tuple;` | `a, b = tuple` hoặc `a, *rest, b = items` |
| **Lấy giá trị an toàn trong Dictionary** | `dict.TryGetValue(key, out var val)` | `val = d.get(key, default_val)` |
| **Gộp hai Dictionary** | Viết extension method hoặc vòng lặp | Toán tử `merged = d1 \| d2` (Python 3.9+) |
| **Kiểm tra tính băm được (Hashing)** | Interface `IEquatable<T>` & `GetHashCode()` | Thuộc tính `__hash__` (chỉ kiểu immutable) |

---

## 📖 Lý thuyết

### 1. `list`: Danh sách động khả biến (Mutable Sequence)

`list` là cấu trúc mảng động, cho phép thay đổi kích thước, sửa đổi phần tử tại chỗ và chứa các phần tử có kiểu dữ liệu bất kỳ.

```python
fruits: list[str] = ["táo", "chuối", "cam"]
fruits.append("xoài")         # Thêm vào cuối: O(1)
fruits.insert(0, "dưa hấu")   # Chèn vào đầu: O(n)
last_item = fruits.pop()      # Lấy và xóa phần tử cuối: O(1)
fruits.extend(["nho", "lê"])  # Nối thêm một collection khác
```

#### Nghệ thuật Slicing (`[start:stop:step]`)
Python hỗ trợ cắt mảng cực kỳ trực quan với chỉ số âm (đếm ngược từ cuối: `-1` là phần tử cuối cùng):
- `start`: Vị trí bắt đầu (tính cả vị trí này).
- `stop`: Vị trí kết thúc (không tính vị trí này).
- `step`: Bước nhảy (mặc định là `1`).

```python
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

print(numbers[2:6])    # [2, 3, 4, 5] (từ index 2 đến index 5)
print(numbers[:4])     # [0, 1, 2, 3] (từ đầu đến index 3)
print(numbers[6:])     # [6, 7, 8, 9] (từ index 6 đến hết)
print(numbers[-3:])    # [7, 8, 9]    (3 phần tử cuối cùng)
print(numbers[::2])    # [0, 2, 4, 6, 8] (bước nhảy 2)
print(numbers[::-1])   # [9, 8, 7, ..., 0] (đảo ngược danh sách)
```

### 2. `tuple`: Dữ liệu bất biến và Unpacking

`tuple` là chuỗi phần tử có thứ tự nhưng **không thể thay đổi (immutable)** sau khi tạo.
- Thường dùng làm bản ghi nhẹ (record), đại diện cho tọa độ, cặp giá trị trả về từ hàm.
- Có thể dùng làm key trong `dict` hoặc phần tử trong `set` (nếu các phần tử con đều hashable).

```python
point = (10, 20)
# point[0] = 15  # LỖI: TypeError: 'tuple' object does not support item assignment

# BẪY CÚ PHÁP: Tuple 1 phần tử bắt buộc phải có dấu phẩy ','
single_element_tuple = (42,)   # kiểu tuple
not_a_tuple = (42)             # kiểu int!
```

#### Unpacking đa năng (Extended Unpacking)
```python
# Đổi giá trị 2 biến không cần biến tạm
a, b = 10, 20
a, b = b, a  # a=20, b=10

# Dùng dấu sao '*' để gom phần dư thừa
scores = [100, 95, 88, 72, 60]
first, second, *others, last = scores
print(first)   # 100
print(second)  # 95
print(others)  # [88, 72]
print(last)    # 60
```

### 3. `dict`: Bảng băm bảo toàn thứ tự chèn

Từ Python 3.7+, `dict` chính thức đảm bảo **bảo toàn thứ tự chèn (insertion-order preserved)** theo đặc tả ngôn ngữ. 

#### Các phương thức thao tác an toàn
```python
user = {"name": "Alice", "role": "admin"}

# 1. Truy xuất an toàn với .get() (tránh văng KeyError)
age = user.get("age", 18)  # Trả về 18 nếu không tìm thấy key "age"

# 2. .setdefault(): Lấy giá trị nếu có, nếu chưa có thì gán mặc định và trả về
user.setdefault("permissions", []).append("write")

# 3. Duyệt dict
for key, value in user.items():
    print(f"{key}: {value}")
```

#### Toán tử gộp từ điển (Dictionary Merge `|` và Update `|=`)
Từ Python 3.9 (PEP 584), bạn có thể gộp hai `dict` bằng toán tử `|`:
```python
default_config = {"host": "localhost", "port": 8000, "debug": False}
custom_config = {"port": 8080, "debug": True}

# Dict bên phải sẽ ghi đè các key trùng của dict bên trái
final_config = default_config | custom_config
print(final_config)  # {'host': 'localhost', 'port': 8080, 'debug': True}
```

### 4. `set` & `frozenset`: Tập hợp toán học

`set` lưu trữ các phần tử duy nhất, không có thứ tự và không cho phép trùng lặp. Tốc độ kiểm tra tồn tại `x in my_set` là **$O(1)$** (nhanh hơn rất nhiều so với kiểm tra trên `list` vốn là $O(n)$).

Các toán tử đại số tập hợp:
```python
dev_team = {"Alice", "Bob", "Charlie", "David"}
backend_team = {"Charlie", "David", "Emma"}

# Hợp (Union): Xuất hiện ở ít nhất một nhóm
print(dev_team | backend_team)  # {'Alice', 'Bob', 'Charlie', 'David', 'Emma'}

# Giao (Intersection): Xuất hiện ở cả hai nhóm
print(dev_team & backend_team)  # {'Charlie', 'David'}

# Hiệu (Difference): Chỉ thuộc dev_team mà không thuộc backend_team
print(dev_team - backend_team)  # {'Alice', 'Bob'}

# Hiệu đối xứng (Symmetric Difference): Thuộc nhóm này hoặc nhóm kia nhưng không thuộc cả hai
print(dev_team ^ backend_team)  # {'Alice', 'Bob', 'Emma'}
```

`frozenset` là phiên bản bất biến của `set`. Vì là bất biến nên `frozenset` là hashable và có thể đặt làm key trong `dict` hoặc làm phần tử của một `set` khác.

### 5. Quy tắc Hashable: Tại sao `list` không thể làm key của `dict`?

Một đối tượng được coi là **hashable** nếu:
1. Nó có một mã băm (`hash value`) không đổi trong suốt vòng đời của nó (thông qua phương thức `__hash__()`).
2. Nó có thể so sánh bình đẳng với các đối tượng khác (thông qua `__eq__()`).

Nếu một đối tượng là khả biến (mutable) như `list` hay `dict`, nội dung của nó có thể thay đổi sau khi chèn vào bảng băm. Khi nội dung thay đổi, vị trí bucket băm bị sai lệch, khiến bảng băm không thể tìm lại đối tượng đó nữa. Vì vậy:
- **Hashable (Immutable)**: `int`, `float`, `str`, `bytes`, `frozenset`, `tuple` (chỉ chứa các phần tử con hashable).
- **Unhashable (Mutable)**: `list`, `dict`, `set`.

```python
valid_dict = {
    ("127.0.0.1", 8080): "Server 1",  # HỢP LỆ: tuple là immutable
    frozenset(["read", "write"]): "Editor Role",  # HỢP LỆ: frozenset
}

# invalid_dict = {["admin", "mod"]: "Moderators"}
# LỖI NGAY: TypeError: unhashable type: 'list'
```

---

## 💻 Ví dụ thực hành

Dưới đây là một chương trình phân tích log truy cập Web API, đếm tần suất truy cập, loại bỏ IP trùng và tính toán phân quyền:

```python
from typing import Any

# 1. Dữ liệu thô giả lập từ server logs
access_logs: list[dict[str, Any]] = [
    {"ip": "192.168.1.10", "endpoint": "/api/v1/tasks", "status": 200},
    {"ip": "10.0.0.5",     "endpoint": "/api/v1/auth",  "status": 401},
    {"ip": "192.168.1.10", "endpoint": "/api/v1/tasks", "status": 200},
    {"ip": "172.16.0.2",   "endpoint": "/api/v1/users", "status": 200},
    {"ip": "10.0.0.5",     "endpoint": "/api/v1/auth",  "status": 200},
]

# 2. Thu thập danh sách các địa chỉ IP duy nhất bằng set
unique_ips: set[str] = set()
for log in access_logs:
    unique_ips.add(log["ip"])
print(f"Tổng số IP duy nhất đã ghé thăm: {len(unique_ips)} -> {unique_ips}")

# 3. Đếm tần suất gọi endpoint bằng dict và get()
endpoint_counts: dict[str, int] = {}
for log in access_logs:
    ep = log["endpoint"]
    endpoint_counts[ep] = endpoint_counts.get(ep, 0) + 1

print("\nThống kê lượt gọi từng Endpoint:")
for ep, count in endpoint_counts.items():
    print(f"  {ep:<20}: {count} lượt")

# 4. Phân tích quyền hạn người dùng bằng set operations
user_roles = {"VIEW_DASHBOARD", "CREATE_TASK"}
admin_required_roles = {"VIEW_DASHBOARD", "CREATE_TASK", "DELETE_TASK", "MANAGE_USERS"}

# Kiểm tra xem người dùng có đủ quyền admin không (kiểm tra tập con <=)
is_admin = admin_required_roles <= user_roles
missing_roles = admin_required_roles - user_roles
print(f"\nUser có quyền Admin không? {is_admin}")
print(f"Các quyền còn thiếu: {missing_roles}")

# 5. Gộp cấu hình hệ thống bằng toán tử |
base_headers = {"Content-Type": "application/json", "X-Server-Version": "2.4"}
auth_headers = {"Authorization": "Bearer token-xyz-123", "X-Server-Version": "2.5"}
request_headers = base_headers | auth_headers
print(f"\nRequest Headers sau khi gộp: {request_headers}")
```

---

## ⚠️ Lỗi thường gặp

### 1. Bẫy tạo tuple một phần tử
```python
val = (100)    # Python hiểu đây là số nguyên 100 đặt trong ngoặc đơn!
print(type(val))  # <class 'int'>

correct_tuple = (100,)
print(type(correct_tuple))  # <class 'tuple'>
```

### 2. Gán biến gán nhãn thay vì sao chép (Aliasing vs Copy)
Khi bạn viết `b = a` với `list` hoặc `dict`, cả hai biến đều trỏ vào cùng một đối tượng trong bộ nhớ:
```python
list_a = [1, 2, 3]
list_b = list_a  # CÙNG TRỎ VÀO MỘT DANH SÁCH!
list_b.append(4)
print(list_a)  # [1, 2, 3, 4] - Bị sửa ngoài ý muốn!

# Cách sửa: Tạo bản sao độc lập (shallow copy)
list_c = list_a.copy()  # hoặc list_a[:]
list_c.append(5)
print(list_a)  # [1, 2, 3, 4]
print(list_c)  # [1, 2, 3, 4, 5]
```

### 3. Sửa kích thước `dict` khi đang duyệt qua nó (`RuntimeError`)
```python
data = {"a": 1, "b": 2, "c": 3}

# SAI:
# for k in data:
#     if data[k] == 2:
#         del data[k]  # LỖI: RuntimeError: dictionary changed size during iteration

# ĐÚNG: Duyệt qua một danh sách bản sao các key
for k in list(data.keys()):
    if data[k] == 2:
        del data[k]
```

---

## ✍️ Bài tập thực hành

### Bài 1: Quản lý hàng tồn kho với Dictionary
Cho thông tin kho hàng của hai chi nhánh:
- Chi nhánh 1: `branch_1 = {"áo thun": 50, "quần jean": 30, "mũ len": 20}`
- Chi nhánh 2: `branch_2 = {"quần jean": 15, "giày thể thao": 25, "áo thun": 10}`

Hãy viết code để:
1. Tìm các mặt hàng có bán ở **cả hai chi nhánh** (dùng `set` keys).
2. Tìm các mặt hàng **chỉ có ở chi nhánh 1** mà không có ở chi nhánh 2.
3. Tạo từ điển `total_stock` tổng hợp toàn bộ số lượng hàng của cả hai chi nhánh (nếu trùng mặt hàng thì cộng dồn số lượng).

<details>
<summary>💡 Gợi ý</summary>

- Lấy keys: `set(branch_1.keys()) & set(branch_2.keys())`.
- Lấy hiệu: `set(branch_1.keys()) - set(branch_2.keys())`.
- Tổng hợp: Bắt đầu với `total = branch_1.copy()`, sau đó lặp qua `branch_2` và dùng `total[k] = total.get(k, 0) + v`.
</details>

---

### Bài 2: Đảo ngược và cắt lọc danh sách công việc
Cho danh sách tác vụ ưu tiên:
`tasks = ["T01-Setup", "T02-Code", "T03-Test", "T04-Review", "T05-Deploy", "T06-Monitor"]`

Thực hiện:
1. Dùng Slicing để lấy danh sách 3 tác vụ đầu tiên.
2. Dùng Slicing để lấy 2 tác vụ cuối cùng.
3. Dùng Slicing bước nhảy để lấy các tác vụ ở vị trí chẵn (index 0, 2, 4).
4. Dùng kỹ thuật Extended Unpacking để gán tác vụ đầu tiên vào `primary`, tác vụ cuối cùng vào `final`, và toàn bộ các tác vụ ở giữa vào danh sách `in_progress`.

<details>
<summary>💡 Gợi ý</summary>

- 3 task đầu: `tasks[:3]`.
- 2 task cuối: `tasks[-2:]`.
- Vị trí chẵn: `tasks[::2]`.
- Unpacking: `primary, *in_progress, final = tasks`.
</details>

---

### Bài 3: Kiểm tra tính hợp lệ của phân quyền người dùng
Một hệ thống quản lý quyền truy cập định nghĩa:
- Các quyền hợp lệ: `VALID_PERMISSIONS = frozenset(["READ", "WRITE", "DELETE", "ADMIN"])`.
- Giả sử có một request mang danh sách quyền yêu cầu cấp phát: `requested = ["READ", "EXECUTE", "WRITE", "READ"]`.

Yêu cầu:
1. Loại bỏ các quyền bị trùng lặp trong `requested`.
2. Xác định các quyền hợp lệ được chấp thuận (phép giao với `VALID_PERMISSIONS`).
3. Xác định các quyền không hợp lệ bị từ chối cấp phép.
4. Kiểm tra xem quyền `ADMIN` có nằm trong danh sách chấp thuận hay không.

<details>
<summary>💡 Gợi ý</summary>

- Chuyển `requested` thành set: `req_set = set(requested)`.
- Chấp thuận: `approved = req_set & VALID_PERMISSIONS`.
- Từ chối: `rejected = req_set - VALID_PERMISSIONS`.
- Kiểm tra: `"ADMIN" in approved`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ sự khác biệt giữa `list` (mutable) và `tuple` (immutable)?
- [ ] Bạn sử dụng thành thạo slicing `[start:stop:step]` và chỉ số âm?
- [ ] Bạn biết cách dùng toán tử `|` để gộp dictionary trong Python 3.9+?
- [ ] Bạn hiểu vì sao độ phức tạp tìm kiếm trong `set` là $O(1)$ còn `list` là $O(n)$?
- [ ] Bạn giải thích được thế nào là một đối tượng `hashable` và tại sao `list` không thể làm key của `dict`?

---

## 📚 Đọc thêm

- [Python Documentation – Data Structures](https://docs.python.org/3/tutorial/datastructures.html)
- [PEP 584 – Add Union Operators To dict](https://peps.python.org/pep-0584/)
- [Python Glossary – Hashable](https://docs.python.org/3/glossary.html#term-hashable)

<!-- nav:bottom -->
---

[⬅️ Điều kiện & vòng lặp](./02-control-flow.md) | [📚 Mục lục Fresher](./README.md) | [Comprehension ➡️](./04-comprehensions.md)
<!-- /nav:bottom -->
