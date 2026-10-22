<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 04
<!-- /nav:top -->

# Comprehension

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 03: Collections: list, tuple, dict, set](./03-collections.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Làm chủ 4 biến thể của kỹ thuật Comprehension: **List Comprehension**, **Dict Comprehension**, **Set Comprehension**, và **Generator Expression**.
- Ánh xạ trực tiếp và chuyển đổi thành thạo các mẫu truy vấn **LINQ (C#)** sang cú pháp Pythonic ngắn gọn, tốc độ cao.
- Phân biệt rõ sự khác nhau giữa lọc điều kiện (`if` ở cuối) và biểu thức biến đổi ba ngôi (`if-else` ở đầu).
- Hiểu rõ lợi ích tiết kiệm bộ nhớ vượt trội của **Generator Expression** (đánh giá lười - lazy evaluation) khi làm việc với tập dữ liệu lớn.
- Biết khi nào **KHÔNG** nên dùng comprehension để tránh tạo ra những dòng mã bí hiểm, khó bảo trì.

---

## 🔁 So sánh với C# / ASP.NET

Trong C#, **LINQ (Language Integrated Query)** là một trong những tính năng được yêu thích nhất để xử lý mảng và tập hợp dữ liệu theo phong cách khai báo (declarative programming).

Trong Python, **Comprehension** chính là câu trả lời tương đương trực tiếp cho LINQ. Comprehension được CPython tối ưu hóa ở tầng C bytecode, chạy nhanh hơn đáng kể so với việc khởi tạo danh sách rỗng rồi dùng vòng lặp `for` gọi `.append()`.

Dưới đây là bảng chuyển đổi trực tiếp từng toán tử LINQ quen thuộc sang Python:

| C# LINQ (Method Syntax) | Python Comprehension / Built-in | Ghi chú so sánh |
|---|---|---|
| `items.Select(x => x * 2)` | `[x * 2 for x in items]` | Biến đổi phần tử (Projection) |
| `items.Where(x => x > 0)` | `[x for x in items if x > 0]` | Lọc phần tử (Filtering) |
| `items.Where(cond).Select(map)` | `[map(x) for x in items if cond(x)]` | Kết hợp lọc và ánh xạ |
| `items.SelectMany(x => x.SubList)` | `[sub for x in items for sub in x.sub_list]` | Trải phẳng danh sách (Flatten) |
| `items.ToDictionary(x => x.Id, x => x.Name)` | `{x.id: x.name for x in items}` | Dict Comprehension |
| `items.Distinct()` | `{x for x in items}` (hoặc `set(items)`) | Set Comprehension |
| `items.Any(x => x > 100)` | `any(x > 100 for x in items)` | Generator Expression + `any()` |
| `items.All(x => x > 0)` | `all(x > 0 for x in items)` | Generator Expression + `all()` |
| `items.Sum(x => x.Price)` | `sum(x.price for x in items)` | Generator Expression + `sum()` |
| `items.Count(x => x.IsActive)` | `sum(1 for x in items if x.is_active)` | Đếm phần tử thỏa điều kiện |

---

## 📖 Lý thuyết

### 1. List Comprehension: Cú pháp và cơ chế

Cú pháp tổng quát:
<!-- nocheck -->
```python
[<biểu_thức_kết_quả> for <biến> in <tập_hợp> if <điều_kiện_lọc>]
```

So sánh phong cách truyền thống và List Comprehension:
```python
# Phong cách cổ điển:
squares = []
for n in range(1, 6):
    if n % 2 == 0:
        squares.append(n * n)

# Phong cách Pythonic với List Comprehension:
squares = [n * n for n in range(1, 6) if n % 2 == 0]
# Kết quả: [4, 16]
```

#### Phân biệt vị trí của `if` lọc và `if-else` biến đổi
Đây là điểm dev C# thường xuyên nhầm lẫn:
1. **Lọc bỏ bớt phần tử**: `if` nằm ở **CUỐI CÙNG**.
   ```python
   # Chỉ lấy các số dương (kích thước danh sách kết quả có thể nhỏ hơn)
   positives = [x for x in [-2, -1, 0, 1, 2] if x > 0]  # [1, 2]
   ```
2. **Biến đổi giá trị theo điều kiện ba ngôi**: `if ... else` nằm ở **ĐẦU TIÊN**.
   ```python
   # Gắn nhãn Chẵn / Lẻ cho mọi phần tử (kích thước giữ nguyên)
   labels = ["Chẵn" if x % 2 == 0 else "Lẻ" for x in range(5)]
   # ['Chẵn', 'Lẻ', 'Chẵn', 'Lẻ', 'Chẵn']
   ```

### 2. Dict Comprehension và Set Comprehension

#### a. Dict Comprehension
Dùng để tạo từ điển một cách nhanh chóng từ một danh sách đối tượng hoặc đảo ngược key-value:
```python
users = [
    {"id": "U1", "name": "Alice", "role": "admin"},
    {"id": "U2", "name": "Bob", "role": "member"},
    {"id": "U3", "name": "Charlie", "role": "member"},
]

# Tạo ID Lookup Map (tương đương .ToDictionary(u => u.Id, u => u) trong C#)
user_by_id = {u["id"]: u for u in users}
print(user_by_id["U1"])  # {'id': 'U1', 'name': 'Alice', 'role': 'admin'}

# Đảo ngược Key-Value của một dict có sẵn
roles_map = {"admin": 1, "editor": 2, "viewer": 3}
inverted_map = {v: k for k, v in roles_map.items()}
print(inverted_map)  # {1: 'admin', 2: 'editor', 3: 'viewer'}
```

#### b. Set Comprehension
Tương tự List Comprehension nhưng đặt trong cặp ngoặc nhọn `{}` và tự động khử các giá trị trùng lặp:
```python
tags = ["python", "csharp", "PYTHON", "fastapi", "CSharp"]

# Chuẩn hóa về chữ thường và loại bỏ trùng lặp (tương đương .Select(t => t.ToLower()).Distinct())
unique_tags = {tag.lower() for tag in tags}
print(unique_tags)  # {'python', 'csharp', 'fastapi'}
```

### 3. Generator Expression: Xử lý dòng dữ liệu lớn (Lazy Evaluation)

Khi bạn dùng dấu ngoặc vuông `[...]`, CPython sẽ tính toán toàn bộ và cấp phát bộ nhớ cho toàn bộ danh sách kết quả ngay lập tức (Eager Evaluation).

Nếu bạn thay bằng dấu ngoặc tròn `(...)`, kết quả tạo ra là một **Generator Expression**:
- Không tính toán trước bất kỳ phần tử nào.
- Chỉ sinh ra phần tử khi được yêu cầu (Lazy Evaluation tương tự `IEnumerable<T>` chưa gọi `.ToList()` trong LINQ).
- Tiết kiệm bộ nhớ đến mức tối đa: xử lý hàng triệu phần tử với dung lượng RAM gần như bằng không!

```python
# List comprehension: Tốn 8MB+ bộ nhớ để lưu 1 triệu số
# eager_list = [x * x for x in range(1_000_000)]

# Generator expression: Tốn ~100 bytes bộ nhớ!
lazy_gen = (x * x for x in range(1_000_000))

# Dùng trực tiếp với các hàm tổng hợp không cần chuyển về list:
total_sum = sum(x * x for x in range(1_000_000))
max_val = max(x * x for x in range(1_000_000))
```

> [!TIP]
> Khi generator expression là tham số duy nhất của một hàm (như `sum(...)`, `any(...)`, `all(...)`), bạn có thể bỏ bớt một cặp ngoặc đơn ngoài cùng: `sum(x for x in items)` thay vì `sum((x for x in items))`.

### 4. Comprehension lồng nhau (Nested Comprehension)

Tương đương với `SelectMany` trong LINQ hoặc nhiều vòng lặp `for` lồng nhau. Thứ tự viết các mệnh đề `for` trong comprehension đi theo đúng thứ tự bạn viết các vòng lặp thông thường từ ngoài vào trong:

```python
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

# Trải phẳng ma trận (Flatten)
# Tương đương:
# flattened = []
# for row in matrix:
#     for val in row:
#         flattened.append(val)

flattened = [val for row in matrix for val in row]
print(flattened)  # [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### 5. Khi nào KHÔNG nên dùng Comprehension?

Comprehension sinh ra là để tăng tính súc tích, nhưng lạm dụng sẽ biến code thành "thảm họa đọc hiểu":

1. **Khi có quá 2 tầng `for` lồng nhau**:
   Một list comprehension có 3 mệnh đề `for` trở lên cực kỳ rối rắm. Hãy tách ra vòng lặp `for` thông thường với các hàm helper.
2. **Khi dùng cho Side-Effects (gọi hàm không lấy kết quả)**:
   ```python
   # TỒI TỆ: Không bao giờ dùng comprehension chỉ để in log hay gọi API
   # [print(user) for user in users]

   # ĐÚNG ĐẮN: Dùng vòng for thông thường
   for user in users:
       print(user)
   ```
3. **Khi biểu thức điều kiện quá phức tạp**: Nếu phải dùng nhiều nhánh `if...elif...elif...else` lồng nhau, hãy viết một hàm chuẩn với khối lệnh rõ ràng.

---

## 💻 Ví dụ thực hành

Dưới đây là một pipeline xử lý và làm sạch danh sách đơn đặt hàng từ API bên ngoài:

```python
from typing import Any

raw_orders: list[dict[str, Any]] = [
    {"order_id": "ORD-001", "customer": "Alice", "items": [{"price": 100, "qty": 2}, {"price": 50, "qty": 1}], "status": "COMPLETED"},
    {"order_id": "ORD-002", "customer": "Bob",   "items": [{"price": 300, "qty": 1}],                               "status": "CANCELLED"},
    {"order_id": "ORD-003", "customer": "Charlie", "items": [{"price": 80, "qty": 5}, {"price": 120, "qty": 2}], "status": "COMPLETED"},
    {"order_id": "ORD-004", "customer": "David", "items": [],                                                         "status": "COMPLETED"},
]

# 1. LINQ Where: Chỉ lấy các đơn đã hoàn thành và có sản phẩm
valid_orders = [
    order for order in raw_orders 
    if order["status"] == "COMPLETED" and len(order["items"]) > 0
]

# 2. LINQ Select: Tính tổng giá trị cho mỗi đơn
# Mỗi item có thành tiền = price * qty
order_summaries = [
    {
        "id": order["order_id"],
        "customer": order["customer"],
        "total": sum(item["price"] * item["qty"] for item in order["items"])
    }
    for order in valid_orders
]

print("=== DANH SÁCH ĐƠN HÀNG HỢP LỆ ===")
for summary in order_summaries:
    print(f"Đơn: {summary['id']} | Khách: {summary['customer']:<10} | Tổng: {summary['total']:>6} USD")

# 3. LINQ ToDictionary: Tạo bảng tra cứu nhanh theo ID
order_lookup = {s["id"]: s for s in order_summaries}
print(f"\nTra cứu nhanh đơn ORD-001: {order_lookup['ORD-001']}")

# 4. LINQ SelectMany: Trích xuất danh sách tất cả các đơn giá (price) riêng lẻ
all_item_prices = [
    item["price"]
    for order in valid_orders
    for item in order["items"]
]
print(f"\nTất cả các mức giá sản phẩm đã bán: {all_item_prices}")

# 5. LINQ Any / All kiểm tra điều kiện nghiệp vụ
has_vip_order = any(s["total"] >= 500 for s in order_summaries)
all_positive = all(s["total"] > 0 for s in order_summaries)
print(f"Có đơn hàng VIP (>= 500 USD)? {has_vip_order}")
print(f"Tất cả đơn đều có giá trị dương? {all_positive}")
```

---

## ⚠️ Lỗi thường gặp

### 1. Đặt sai vị trí của `if` lọc điều kiện
```python
# LỖI CÚ PHÁP: Cố đặt "if condition" ở đầu mà không có "else"
# [x * 2 if x > 0 for x in [-1, 2]]  # SyntaxError: expected 'else' after 'if' expression

# ĐÚNG:
# Nếu là lọc: đặt if ở cuối
positives = [x * 2 for x in [-1, 2] if x > 0]
# Nếu là biến đổi ba ngôi: bắt buộc phải có đủ if và else
tagged = [x * 2 if x > 0 else 0 for x in [-1, 2]]
```

### 2. Dùng List Comprehension thay vì Generator Expression cho dữ liệu lớn
Khi tính toán tổng hoặc kiểm tra điều kiện trên tập dữ liệu hàng triệu dòng, viết `sum([x for x in big_data])` sẽ ép CPython tạo một mảng khổng lồ trong RAM rồi mới tính tổng. Viết `sum(x for x in big_data)` sẽ chạy streaming từng phần tử, giảm thiểu tối đa RAM tiêu thụ.

### 3. Biến vòng lặp comprehension bị rò rỉ (Leaking variables)
Trong Python 2 cũ, biến trong list comprehension có thể làm ghi đè biến cùng tên ở phạm vi bên ngoài. Trong **Python 3**, comprehension sở hữu scope độc lập (local function scope), tuy nhiên không nên đặt tên biến trong comprehension trùng với các biến quan trọng ở ngoài để tránh nhầm lẫn khi đọc code.

---

## ✍️ Bài tập thực hành

### Bài 1: Chuyển đổi mã LINQ C# sang Python Comprehension
Cho đoạn mã C# sau:
```csharp
var filteredUsers = users
    .Where(u => u.IsActive && u.Age >= 18)
    .Select(u => new {
        u.Id,
        DisplayName = u.Name.ToUpper(),
        Category = u.Age >= 60 ? "Senior" : "Adult"
    })
    .ToDictionary(x => x.Id, x => x);
```
Giả sử bạn có danh sách `users = [{"id": 1, "name": "alice", "age": 25, "is_active": True}, ...]` trong Python. Hãy viết một Dict Comprehension (hoặc kết hợp List và Dict comprehension) để tái hiện chính xác kết quả trên.

<details>
<summary>💡 Gợi ý</summary>

- Lọc và biến đổi:
  ```python
  result = {
      u["id"]: {
          "id": u["id"],
          "display_name": u["name"].upper(),
          "category": "Senior" if u["age"] >= 60 else "Adult",
      }
      for u in users
      if u["is_active"] and u["age"] >= 18
  }
  ```
</details>

---

### Bài 2: Phân tích và thống kê từ vựng văn bản
Cho một đoạn văn bản:
`text = "Python is powerful and Python is fast and expressive"`

Yêu cầu thực hiện bằng Comprehension:
1. Tách chuỗi thành các từ, chuẩn hóa về chữ thường: `words = [w.lower() for w in text.split()]`.
2. Dùng Set Comprehension để lấy danh sách các từ duy nhất có độ dài lớn hơn 3 ký tự.
3. Dùng Dict Comprehension để tạo từ điển thống kê độ dài của mỗi từ duy nhất đó: `{word: len(word) for word in ...}`.
4. Dùng Generator Expression kết hợp hàm `max()` để tìm độ dài lớn nhất trong số các từ.

<details>
<summary>💡 Gợi ý</summary>

- Set comprehension: `long_words = {w for w in words if len(w) > 3}`.
- Dict comprehension: `word_lengths = {w: len(w) for w in long_words}`.
- Max length: `max(len(w) for w in long_words)`.
</details>

---

### Bài 3: Trải phẳng và lọc ma trận điểm số
Cho ma trận điểm số của các lớp học:
```python
gradebook = [
    [7.5, 8.0, 9.5, 4.0],
    [6.0, 5.5, 8.5],
    [9.0, 10.0, 3.5, 7.0]
]
```
1. Dùng Nested List Comprehension để trải phẳng `gradebook` thành một danh sách điểm số duy nhất gồm các điểm đạt yêu cầu ($\ge 5.0$).
2. Dùng Generator Expression để kiểm tra xem có bất kỳ học sinh nào đạt điểm tuyệt đối $10.0$ hay không (`any()`).
3. Dùng Generator Expression để tính điểm trung bình của tất cả các điểm đạt yêu cầu.

<details>
<summary>💡 Gợi ý</summary>

- Nested list comprehension: `passing_grades = [score for classroom in gradebook for score in classroom if score >= 5.0]`.
- Kiểm tra 10: `has_perfect = any(score == 10.0 for classroom in gradebook for score in classroom)`.
- Trung bình: `avg = sum(passing_grades) / len(passing_grades)`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn có thể chuyển đổi mượt mà giữa các toán tử LINQ (`Select`, `Where`, `SelectMany`, `ToDictionary`) sang cú pháp Comprehension tương ứng?
- [ ] Bạn phân biệt rõ khi nào đặt `if` ở cuối (lọc) và khi nào đặt `if-else` ở đầu (ternary projection)?
- [ ] Bạn hiểu rõ sự khác biệt về cơ chế bộ nhớ giữa `[...]` (List) và `(...)` (Generator)?
- [ ] Bạn biết cách sử dụng Generator Expression với các hàm `sum()`, `any()`, `all()`?
- [ ] Bạn biết từ chối dùng comprehension khi logic quá phức tạp hoặc có side-effects?

---

## 📚 Đọc thêm

- [PEP 202 – List Comprehensions](https://peps.python.org/pep-0202/)
- [PEP 274 – Dict Comprehensions](https://peps.python.org/pep-0274/)
- [PEP 289 – Generator Expressions](https://peps.python.org/pep-0289/)

<!-- nav:bottom -->
---

[⬅️ Collections: list, tuple, dict, set](./03-collections.md) | [📚 Mục lục Fresher](./README.md) | [Hàm ➡️](./05-functions.md)
<!-- /nav:bottom -->
