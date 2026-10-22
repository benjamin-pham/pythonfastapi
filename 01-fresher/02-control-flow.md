<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 02
<!-- /nav:top -->

# Điều kiện & vòng lặp

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 01: Cú pháp, biến & kiểu dữ liệu](./01-syntax-variables-types.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Làm chủ các cấu trúc rẽ nhánh điều kiện: `if / elif / else` và biểu thức ba ngôi (ternary expression) `a if cond else b`.
- Nắm vững tính năng **Structural Pattern Matching (`match / case`)** hiện đại từ Python 3.10+, bao gồm sequence patterns, mapping patterns, class patterns và mệnh đề bảo vệ (guards `if`).
- Thấu hiểu bản chất vòng lặp trong Python: `for ... in` luôn là một vòng lặp `foreach`.
- Sử dụng thành thạo bộ ba hàm lặp kinh điển: `range()`, `enumerate()` và `zip()`.
- Hiểu chính xác cơ chế hoạt động của mệnh đề **`for ... else`** và **`while ... else`** — vũ khí tìm kiếm không cần biến cờ (flag).

---

## 🔁 So sánh với C# / ASP.NET

Trong C#, bạn có câu lệnh rẽ nhánh `if / else`, `switch / case`, biểu thức `switch expression` (từ C# 8+), và các loại vòng lặp đa dạng: `for (int i = 0; i < n; i++)`, `foreach`, `while`, `do..while`.

Dưới đây là bảng đối chiếu trực quan sang phong cách Pythonic:

| Cấu trúc / Tác vụ | C# / .NET | Python 3.10+ |
|---|---|---|
| **Điều kiện rẽ nhánh** | `if (x > 0) { ... } else if { ... }` | `if x > 0: ... elif ...:` (không cần ngoặc đơn) |
| **Toán tử ba ngôi** | `var res = isValid ? "OK" : "Err";` | `res = "OK" if is_valid else "Err"` |
| **Khớp mẫu (Pattern Matching)** | `switch (val) { case ... => ... }` | `match val: case ...: ...` |
| **Bảo vệ trong khớp mẫu** | `case User u when u.Age >= 18 =>` | `case User(age=age) if age >= 18:` |
| **Vòng lặp chỉ số (index-based)** | `for (int i = 0; i < n; i++)` | `for i in range(n):` |
| **Vòng lặp duyệt phần tử** | `foreach (var item in list)` | `for item in items:` |
| **Lặp lấy cả index và value** | `items.Select((val, idx) => ...)` | `for idx, val in enumerate(items):` |
| **Lặp song song 2 danh sách** | `items1.Zip(items2, (a, b) => ...)` | `for a, b in zip(items1, items2):` |
| **Vòng lặp do-while** | `do { ... } while (cond);` | Không có! Dùng `while True:` kết hợp `if not cond: break` |
| **Khối kết thúc tìm kiếm** | Phải dùng cờ `bool found = false;` | Mệnh đề `for ... else:` (chạy nếu không bị `break`) |

---

## 📖 Lý thuyết

### 1. Cấu trúc rẽ nhánh: `if / elif / else` và Ternary

Python không dùng ngoặc nhọn `{}` mà dùng **thụt đầu dòng (4 spaces)** để xác định khối mã. Biểu thức điều kiện sau `if` không cần đặt trong cặp ngoặc đơn `()`.

```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "D"
```

#### Biểu thức điều kiện ba ngôi (Conditional Expression)
Cú pháp trong Python đảo ngược so với `cond ? a : b` của C#:
```python
# Cú pháp: <giá_trị_nếu_đúng> if <điều_kiện> else <giá_trị_nếu_sai>
status = "Thành công" if score >= 50 else "Không đạt"
```

### 2. Structural Pattern Matching: `match / case` (Python 3.10+)

Không chỉ đơn thuần là `switch/case` như trong C# cổ điển, `match / case` (PEP 634/635/636) là một hệ thống khớp mẫu cấu trúc cực kỳ mạnh mẽ, tương đương với `switch expression` và Pattern Matching hiện đại của C# 9–12.

Nó có khả năng:
1. Khớp giá trị hằng số (Literal pattern).
2. Tách cấu trúc danh sách / tuple (Sequence pattern).
3. Tách cấu trúc dictionary (Mapping pattern).
4. Khớp kiểu đối tượng (Class pattern).
5. Kết hợp điều kiện phụ với guard `if`.

```python
command = ["move", 10, 20]

match command:
    case ["quit"]:
        print("Thoát chương trình")
    case ["move", x, y]:
        print(f"Di chuyển tới tọa độ ({x}, {y})")
    case ["pickup", str(item)]:
        print(f"Nhặt vật phẩm: {item}")
    case _:
        print("Lệnh không hợp lệ")
```

#### Guard `if` trong `case`
Bạn có thể gắn thêm điều kiện lọc bổ sung sau mẫu khớp:
```python
user_event = {"action": "login", "attempts": 4}

match user_event:
    case {"action": "login", "attempts": a} if a >= 5:
        print("Tài khoản bị khóa do đăng nhập sai quá số lần quy định!")
    case {"action": "login", "attempts": a}:
        print(f"Đăng nhập thất bại lần thứ {a}.")
    case {"action": "logout"}:
        print("Người dùng đăng xuất.")
    case _:
        print("Sự kiện không nhận diện được.")
```

### 3. Vòng lặp `for ... in` và các helper functions

Trong Python, **mọi vòng lặp `for` đều là `foreach`**. Không có cú pháp lặp 3 thành phần kiểu C (`for (i=0; i<10; i++)`). Thay vào đó, bạn lặp qua một **Iterable** (danh sách, chuỗi, dải số...).

#### a. `range(start, stop, step)`
Hàm `range()` sinh ra một dãy số nguyên có tính lười (lazy sequence). Nó không tạo toàn bộ danh sách số trong bộ nhớ mà chỉ tính toán khi cần:
```python
# Lặp từ 0 đến 4
for i in range(5):
    pass

# Lặp từ 1 đến 10 với bước nhảy 2 (1, 3, 5, 7, 9)
for i in range(1, 10, 2):
    pass

# Lặp lùi từ 5 về 1
for i in range(5, 0, -1):
    pass
```

#### b. `enumerate(iterable, start=0)`: Lấy cả index và giá trị
Dev C# mới sang Python thường có thói quen viết `for i in range(len(items)): val = items[i]`. Đây là phong cách phản mẫu (anti-pattern). Cách chuẩn Pythonic là dùng `enumerate()`:

```python
tasks = ["Viết tài liệu", "Review PR", "Deploy staging"]

for idx, task in enumerate(tasks, start=1):
    print(f"{idx}. {task}")
# 1. Viết tài liệu
# 2. Review PR
# 3. Deploy staging
```

#### c. `zip(*iterables, strict=False)`: Lặp song song nhiều danh sách
Khi cần duyệt qua 2 hoặc nhiều danh sách cùng lúc theo từng cặp tương ứng:
```python
names = ["Alice", "Bob", "Charlie"]
scores = [95, 80, 88]

for name, score in zip(names, scores):
    print(f"{name}: {score} điểm")

# Từ Python 3.10: thêm cờ strict=True để báo lỗi ValueError nếu độ dài các danh sách không bằng nhau
# for name, score in zip(names, scores, strict=True): ...
```

### 4. Mệnh đề `for ... else` và `while ... else`

Đây là một trong những tính năng độc đáo nhất của Python khiến hầu hết các lập trình viên C# ban đầu đều kinh ngạc.

> [!IMPORTANT]
> **Quy tắc của `for...else`**: Khối mã trong `else` sẽ được thực thi **CHỈ KHI** vòng lặp kết thúc một cách bình thường trọn vẹn (hết danh sách), và sẽ **BỊ BỎ QUA** nếu vòng lặp bị ngắt cưỡng bức bởi lệnh **`break`**.

Hãy xem bài toán tìm kiếm:
Trong C#, bạn cần:
```csharp
bool found = false;
foreach (var item in list) {
    if (item == target) { found = true; break; }
}
if (!found) { /* xử lý không tìm thấy */ }
```

Trong Python với `for...else`:
```python
users = ["alice", "bob", "charlie"]
target = "david"

for user in users:
    if user == target:
        print(f"Tìm thấy người dùng: {user}")
        break
else:
    # Chạy khi không tìm thấy target và vòng lặp duyệt hết sạch phần tử
    print(f"Không tìm thấy người dùng: {target}")
```

---

## 💻 Ví dụ thực hành

Dưới đây là một chương trình xử lý hàng đợi sự kiện (Event Queue) mô phỏng trong hệ thống thanh toán:

```python
from typing import Any

# Danh sách sự kiện nhận được từ Message Broker
events: list[dict[str, Any]] = [
    {"type": "PAYMENT_REQUESTED", "order_id": "ORD-101", "amount": 250_000},
    {"type": "PAYMENT_REQUESTED", "order_id": "ORD-102", "amount": -5_000},
    {"type": "REFUND_REQUESTED", "order_id": "ORD-099", "amount": 100_000, "reason": "Defective product"},
    {"type": "UNKNOWN_ACTION", "raw_data": "raw-log-hex"},
]

print("=== BẮT ĐẦU XỬ LÝ HÀNG ĐỢI SỰ KIỆN ===")

for idx, event in enumerate(events, start=1):
    print(f"\n[Event #{idx}] Đang xử lý:")
    
    match event:
        # Trường hợp 1: Yêu cầu thanh toán hợp lệ (có guard if)
        case {"type": "PAYMENT_REQUESTED", "order_id": oid, "amount": amt} if amt > 0:
            status = "Ưu tiên cao" if amt >= 200_000 else "Bình thường"
            print(f"  -> Xử lý thanh toán hợp lệ cho đơn {oid}: {amt:,.0f} VND ({status})")

        # Trường hợp 2: Thanh toán nhưng số tiền không hợp lệ
        case {"type": "PAYMENT_REQUESTED", "order_id": oid, "amount": amt}:
            print(f"  -> CẢNH BÁO: Số tiền thanh toán không hợp lệ ({amt}) cho đơn {oid}!")

        # Trường hợp 3: Hoàn tiền
        case {"type": "REFUND_REQUESTED", "order_id": oid, "amount": amt, "reason": r}:
            print(f"  -> Xử lý hoàn tiền cho đơn {oid}: {amt:,.0f} VND. Lý do: {r}")

        # Trường hợp mặc định
        case _:
            print(f"  -> Sự kiện không hỗ trợ: {event}")

# Kiểm tra xem có đơn hàng nghi vấn (số tiền âm) trong danh sách hay không bằng for...else
target_flagged_order = "ORD-102"
for event in events:
    if event.get("order_id") == target_flagged_order and event.get("amount", 0) < 0:
        print(f"\n[Kiểm toán] Đã chặn thành công đơn hàng gian lận: {target_flagged_order}!")
        break
else:
    print(f"\n[Kiểm toán] Không phát hiện đơn gian lận {target_flagged_order}.")
```

---

## ⚠️ Lỗi thường gặp

### 1. Hiểu sai logic của `for...else`
Nhiều dev lầm tưởng rằng `else` sẽ chạy khi danh sách rỗng (như logic `if list: ... else: ...`).
Thực tế: nếu danh sách rỗng, vòng lặp không thực hiện bước nào, không hề gặp lệnh `break`, do đó **khối `else` VẪN ĐƯỢC CHẠY**!
```python
empty_list: list[int] = []
for item in empty_list:
    if item == 10:
        break
else:
    print("Vẫn in ra dòng này!")  # Chạy vì không bị break ngắt!
```

### 2. Sửa đổi danh sách ngay trong khi đang lặp qua nó
Khi bạn xóa hoặc thêm phần tử vào danh sách trong khi đang lặp trực tiếp trên danh sách đó, index nội bộ của iterator bị dịch chuyển dẫn đến bỏ sót phần tử:

```python
numbers = [1, 2, 3, 4, 5, 6]

# SAI LẦM:
# for num in numbers:
#     if num % 2 == 0:
#         numbers.remove(num)  # Gây nhảy cóc phần tử!

# ĐÚNG CÁCH: Lặp trên một bản sao (slice copy) hoặc dùng list comprehension
for num in numbers[:]:  # numbers[:] tạo shallow copy
    if num % 2 == 0:
        numbers.remove(num)

print(numbers)  # [1, 3, 5]
```

### 3. Dùng `range(len(...))` thay cho `enumerate()`
Viết `for i in range(len(items)): ... items[i]` làm code dài dòng, khó đọc và chậm hơn một chút so với cú pháp tự nhiên `for i, item in enumerate(items):`.

---

## ✍️ Bài tập thực hành

### Bài 1: Bộ định tuyến tác vụ (Task Dispatcher) với `match / case`
Hệ sinh thái Task Management nhận các chỉ thị dòng lệnh dưới dạng danh sách từ khóa:
- `["add", title, priority]` (ví dụ: `["add", "Fix bug", "high"]`): In ra thông báo tạo task với độ ưu tiên.
- `["list"]` hoặc `["list", "--all"]`: In ra thông báo liệt kê task.
- `["done", task_id]` (với điều kiện `task_id` là số nguyên dương): In ra thông báo hoàn thành task.
- Mọi câu lệnh khác: In ra cú pháp trợ giúp (help text).

Hãy viết một hàm hoặc script dùng cấu trúc `match / case` kết hợp guard `if` để phân tích và xử lý 4 mẫu lệnh trên.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng sequence pattern: `case ["add", str(title), ("low" | "medium" | "high") as priority]:`.
- Dùng guard `if`: `case ["done", int(task_id)] if task_id > 0:`.
- Dùng wildcard `case _:` ở cuối cùng.
</details>

---

### Bài 2: Ghép cặp dữ liệu kiểm tra với `zip` và `enumerate`
Bạn có 3 danh sách:
- `students = ["An", "Bình", "Cường", "Dũng"]`
- `math_scores = [8.5, 7.0, 9.0, 6.5]`
- `english_scores = [9.0, 8.0, 8.5, 7.5]`

Yêu cầu:
1. Dùng `zip` để ghép cặp từng học sinh với điểm Toán và Tiếng Anh.
2. Dùng `enumerate` để đánh số thứ tự từ 1.
3. Tính điểm trung bình môn của mỗi học sinh.
4. Xác định học sinh có điểm trung bình cao nhất và in ra thông tin chi tiết.

<details>
<summary>💡 Gợi ý</summary>

- Cú pháp kết hợp: `for idx, (name, m_score, e_score) in enumerate(zip(students, math_scores, english_scores), start=1):`.
- Tính `avg = (m_score + e_score) / 2`.
- Duy trì hai biến `highest_avg` và `best_student` để tìm người có điểm cao nhất.
</details>

---

### Bài 3: Kiểm tra số nguyên tố bằng `for ... else`
Viết chương trình kiểm tra xem một số nguyên $N$ nhập vào có phải là số nguyên tố hay không:
- Nếu $N < 2$: Không phải số nguyên tố.
- Nếu $N \ge 2$: Sử dụng vòng lặp duyệt từ 2 đến $\lfloor\sqrt{N}\rfloor$. Nếu phát hiện ước số thì lập tức `break`.
- Sử dụng mệnh đề `else` của vòng lặp để khẳng định $N$ là số nguyên tố mà **tuyệt đối không dùng biến cờ boolean** (`is_prime = True/False`).

<details>
<summary>💡 Gợi ý</summary>

- Dùng `int(n ** 0.5) + 1` để tìm chặn trên căn bậc hai.
- Vòng lặp: `for i in range(2, int(n ** 0.5) + 1): if n % i == 0: break`.
- Khối `else:` theo sau vòng lặp sẽ là nơi kết luận số nguyên tố.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn có thể sử dụng thành thạo `match / case` với sequence pattern và guard `if`?
- [ ] Bạn hiểu rõ tại sao `for ... in` trong Python tương đương với `foreach` trong C#?
- [ ] Bạn đã từ bỏ thói quen `range(len(items))` để chuyển hẳn sang `enumerate(items)`?
- [ ] Bạn biết cách dùng `zip(a, b)` để xử lý đồng thời nhiều danh sách?
- [ ] Bạn giải thích được chính xác khi nào khối `else` trong `for...else` được chạy và khi nào bị bỏ qua?

---

## 📚 Đọc thêm

- [PEP 634 – Structural Pattern Matching: Specification](https://peps.python.org/pep-0634/)
- [PEP 636 – Structural Pattern Matching: Tutorial](https://peps.python.org/pep-0636/)
- [Python Control Flow Documentation](https://docs.python.org/3/tutorial/controlflow.html)

<!-- nav:bottom -->
---

[⬅️ Cú pháp, biến & kiểu dữ liệu](./01-syntax-variables-types.md) | [📚 Mục lục Fresher](./README.md) | [Collections: list, tuple, dict, set ➡️](./03-collections.md)
<!-- /nav:bottom -->
