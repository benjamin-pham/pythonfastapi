<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 01
<!-- /nav:top -->

# Iterator & generator

> ⏱️ Thời lượng: ~3.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Level 01: Fresher](../01-fresher/README.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Phân biệt rạch ròi giữa **Iterable** (đối tượng có thể duyệt) và **Iterator** (đối tượng nắm giữ con trỏ trạng thái duyệt) trong CPython.
- Hiểu sâu bản chất giao thức **Iterator Protocol** (`__iter__`, `__next__`, `StopIteration`) và sự tương đồng tuyệt đối với `IEnumerable<T>` / `IEnumerator<T>` trong C#.
- Làm chủ cú pháp **`yield`** và **`yield from`** để xây dựng các hàm Generator sinh dữ liệu theo cơ chế **Lazy Evaluation** (tính toán lười).
- Đo lường và chứng minh khả năng tối ưu RAM vượt trội khi xử lý luồng dữ liệu lớn (Streaming Big Data) thay vì gom toàn bộ vào `list`.
- Khai thác thành thạo module chuẩn **`itertools`**: `islice`, `chain`, `groupby`, và hàm mới **`batched`** (từ Python 3.12+).
- Nắm bắt trước mẫu kiến trúc **Yield Dependency** – cách FastAPI ứng dụng Generator để quản lý vòng đời tài nguyên và tự động đóng Database Session.

---

## 🔁 So sánh với C# / ASP.NET

Là một kỹ sư C# / .NET, bạn đã quá quen thuộc với LINQ và từ khóa `yield return`. Trong Python, cơ chế Iterator và Generator cũng giải quyết cùng một bài toán tối ưu tài nguyên, nhưng mang tính cốt lõi và xuất hiện ở khắp mọi nơi trong hệ sinh thái.

| Khái niệm / Thao tác | C# / .NET | Python 3.12+ |
|---|---|---|
| **Giao thức lặp (Iterable)** | `IEnumerable<T>` (triển khai phương thức `GetEnumerator()`) | **Iterable**: Đối tượng có phương thức `__iter__()` trả về một Iterator |
| **Con trỏ duyệt (Iterator)** | `IEnumerator<T>` (chứa `Current`, `MoveNext()`, `Reset()`) | **Iterator**: Đối tượng có `__next__()` và `__iter__()` |
| **Báo hiệu hết phần tử** | `MoveNext()` trả về `false` | `__next__()` ném ngoại lệ ngầm `StopIteration` |
| **Sinh phần tử lười (Lazy)** | `yield return item;` | `yield item` |
| **Kết thúc lặp sớm** | `yield break;` | `return` bên trong generator function |
| **Ủy quyền cho generator con** | `foreach (var x in sub) yield return x;` | `yield from sub` |
| **Cắt lát dữ liệu lười** | `source.Skip(n).Take(m)` | `itertools.islice(source, n, n + m)` |
| **Gộp luồng lặp** | `sourceA.Concat(sourceB)` | `itertools.chain(sourceA, sourceB)` |
| **Chia khối dữ liệu (Chunk/Batch)** | `.Chunk(size)` (từ .NET 6+) | `itertools.batched(source, n)` (từ Python 3.12+) |
| **Quản lý vòng đời tài nguyên** | `using (var db = new AppDbContext())` | `yield` bên trong FastAPI `Depends` (setup -> `yield` -> teardown) |

---

## 📖 Lý thuyết

### 1. Giao thức Iterator (Iterator Protocol)

Để hiểu được Generator, trước tiên bạn cần nắm vững cơ chế mà vòng lặp `for` của Python vận hành bên dưới mui xe (under the hood).

Trong Python:
- **Iterable** là bất kỳ đối tượng nào có thể trả về một Iterator khi truyền vào hàm `iter(obj)`. Ví dụ: `list`, `tuple`, `dict`, `str`, `set`. Các đối tượng này triển khai dunder method `__iter__()`.
- **Iterator** là đối tượng biểu diễn một dòng dữ liệu (stream of data). Nó triển khai phương thức `__next__()` để trả về phần tử tiếp theo. Khi không còn phần tử nào, nó ném ngoại lệ `StopIteration`. Mọi Iterator cũng chính là một Iterable (phương thức `__iter__()` của nó trả về chính nó: `return self`).

Khi bạn viết một vòng lặp `for`:

```python
numbers = [10, 20, 30]
for item in numbers:
    print(item)
```

CPython thực chất sẽ biên dịch và thực thi logic tương đương với đoạn mã sau:

```python
numbers = [10, 20, 30]
# 1. Lấy iterator từ iterable thông qua hàm iter()
iterator = iter(numbers)

# 2. Lặp vô hạn để lấy từng giá trị bằng next()
while True:
    try:
        item = next(iterator)
        print(item)
    except StopIteration:
        # 3. Khi hết phần tử, StopIteration được kích hoạt để ngắt lặp an toàn
        break
```

Bạn có thể tự tạo một Iterator thuần túy bằng class tuân thủ giao thức này:

```python
class CountDown:
    """Đếm ngược từ start về 1."""

    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self) -> "CountDown":
        # Iterator phải trả về chính nó khi gọi __iter__
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


# Sử dụng Countdown
for n in CountDown(3):
    print(n)  # In: 3, 2, 1
```

### 2. Hàm Generator và từ khóa `yield`

Việc tạo class với đầy đủ `__iter__` và `__next__` khá rườm rà. Python cung cấp **Generator Function** – một cú pháp tinh tế tương tự `yield return` trong C# – cho phép tạo Iterator chỉ bằng một hàm thông thường.

Khi một hàm chứa từ khóa `yield`:
1. Hàm đó trở thành một **Generator Function**.
2. Khi bạn gọi hàm, mã nguồn trong hàm **hoàn toàn chưa chạy ngay**. Thay vào đó, nó trả về một **Generator Object** (đã triển khai sẵn Iterator Protocol).
3. Mỗi khi hàm `next(gen)` được gọi:
   - Hàm chạy tiếp cho đến khi bắt gặp từ khóa `yield`.
   - Giá trị đi kèm `yield` được trả về cho bên gọi.
   - Trạng thái thực thi của hàm (các biến cục bộ, con trỏ lệnh) được **đóng băng (suspended)** tại dòng đó.
4. Ở lần gọi `next(gen)` tiếp theo, hàm tiếp tục chạy ngay từ điểm vừa đóng băng thay vì chạy lại từ đầu!

```python
from collections.abc import Generator


def countdown(start: int) -> Generator[int, None, None]:
    """Hàm generator đếm ngược."""
    print("Bắt đầu generator...")
    current = start
    while current > 0:
        yield current
        current -= 1
    print("Kết thúc generator!")


# Gọi hàm chỉ tạo ra generator object, chưa chạy code bên trong
gen = countdown(3)
print(type(gen))  # <class 'generator'>

print(next(gen))  # In: 'Bắt đầu generator...' rồi trả về 3
print(next(gen))  # Chạy tiếp từ 'current -= 1', in 2
print(next(gen))  # In 1
# next(gen)       # Sẽ ném StopIteration và in: 'Kết thúc generator!'
```

> [!NOTE]
> Để kết thúc một generator sớm trước khi chạy hết vòng lặp, bạn chỉ cần dùng lệnh `return` đơn giản (tương đương `yield break;` trong C#).

### 3. Cú pháp `yield from`: Ủy quyền Generator (Subgenerator Delegation)

Khi bạn muốn duyệt qua các phần tử của một Iterable khác hoặc một Generator con rồi yield từng phần tử ra ngoài, cách viết thủ công là:

```python
def flatten_nested_manual(lists: list[list[int]]) -> Generator[int, None, None]:
    for sublist in lists:
        for item in sublist:
            yield item
```

Từ Python 3.3 (PEP 380), cú pháp `yield from` cho phép bạn ủy quyền trực tiếp cho subgenerator hoặc iterable con:

```python
def flatten_nested(lists: list[list[int]]) -> Generator[int, None, None]:
    for sublist in lists:
        yield from sublist  # Tự động duyệt và yield từng phần tử của sublist!
```

`yield from` không chỉ ngắn gọn hơn mà còn thiết lập một kênh truyền dữ liệu hai chiều trực tiếp giữa caller và subgenerator (bao gồm cả việc gửi giá trị bằng `.send()` hoặc ném exception bằng `.throw()`), giúp tối ưu hiệu năng đáng kể ở tầng CPython.

### 4. Lazy Evaluation: Tối ưu bộ nhớ với luồng dữ liệu lớn

Trong C#, bạn biết rằng `source.ToList()` sẽ tải toàn bộ bản ghi vào RAM, trong khi giữ nguyên `IEnumerable<T>` sẽ chỉ duyệt từng bản ghi khi cần. 

Trong Python, sự khác biệt giữa **Eager Collection** (`list`) và **Lazy Generator** (`Generator`) là yếu tố sống còn cho hiệu năng bộ nhớ:

```python
import sys

# Tạo danh sách 1 triệu số nguyên trong bộ nhớ (Eager)
list_data = [x for x in range(1_000_000)]
print(f"RAM của List: {sys.getsizeof(list_data):,} bytes")  # ~8,448,728 bytes (~8.5 MB)

# Tạo Generator biểu thức (Lazy)
gen_data = (x for x in range(1_000_000))
print(f"RAM của Generator: {sys.getsizeof(gen_data):,} bytes")  # ~200 bytes!
```

Một Generator chỉ chiếm khoảng **`200 bytes`** dù dòng dữ liệu có chứa 1 triệu, 100 triệu hay vô hạn phần tử, vì nó chỉ lưu trữ trạng thái hiện tại của con trỏ và tính toán giá trị tiếp theo theo nhu cầu (on demand).

### 5. Module `itertools`: Thư viện xử lý luồng dữ liệu tối thượng

Thư viện chuẩn `itertools` cung cấp các hàm xây dựng sẵn cực kỳ nhanh (được viết bằng C) để thao tác trên các Iterator. Dưới đây là 4 công cụ quan trọng nhất:

#### a. `itertools.islice`: Cắt lát lười (Lazy Slice)
Tương đương LINQ `.Skip().Take()`. Bạn không thể dùng cú pháp `generator[10:20]` vì generator không hỗ trợ chỉ mục ngẫu nhiên (indexing). Hãy dùng `islice`:

```python
from itertools import islice


def infinite_numbers():
    n = 0
    while True:
        yield n
        n += 1


# Lấy từ phần tử thứ 10 đến 15 (Skip 10, Take 5)
first_slice = list(islice(infinite_numbers(), 10, 15))
print(first_slice)  # [10, 11, 12, 13, 14]
```

#### b. `itertools.chain`: Nối luồng (Concatenation)
Tương đương LINQ `.Concat()`. Nối nhiều iterable thành một luồng lặp liên tục mà không cần tạo list trung gian:

```python
from itertools import chain

users_active = ["Alice", "Bob"]
users_pending = ["Charlie", "David"]

for user in chain(users_active, users_pending):
    print(user)  # Duyệt mượt mà qua cả hai danh sách
```

#### c. `itertools.groupby`: Gom nhóm phần tử liên tiếp
Gom nhóm các phần tử có cùng khóa (key).
> [!IMPORTANT]
> Khác với SQL `GROUP BY` hay C# `source.GroupBy()`, `itertools.groupby` **chỉ gom nhóm các phần tử đứng cạnh nhau liên tiếp**. Do đó, nếu dữ liệu chưa được sắp xếp theo khóa gom nhóm, bạn phải sắp xếp (`sorted()`) trước khi truyền vào `groupby`!

```python
from itertools import groupby

orders = [
    {"status": "PENDING", "id": 1},
    {"status": "PENDING", "id": 2},
    {"status": "SUCCESS", "id": 3},
    {"status": "SUCCESS", "id": 4},
]

for status, group in groupby(orders, key=lambda x: x["status"]):
    order_ids = [o["id"] for o in group]
    print(f"Trạng thái {status}: {order_ids}")
```

#### d. `itertools.batched` (Mới trong Python 3.12+)
Tương đương với `.Chunk(size)` trong .NET 6+. Hàm này chia nhỏ một stream dữ liệu thành từng lô (batch) có kích thước cố định dạng tuple. Rất thích hợp khi cần Bulk Insert vào Database hoặc gọi Batch API bên thứ ba:

```python
from itertools import batched

records = range(1, 11)  # 1 đến 10
# Chia thành các lô 3 phần tử
for batch in batched(records, 3):
    print(batch)
# In ra:
# (1, 2, 3)
# (4, 5, 6)
# (7, 8, 9)
# (10,)
```

### 6. Ứng dụng thực tế: Cơ chế `yield` trong FastAPI Dependency Injection

Trong các ứng dụng backend hiện đại như FastAPI, `yield` không chỉ dùng để duyệt dữ liệu mà còn đóng vai trò là cơ chế **quản lý vòng đời tài nguyên (Resource Lifespan Management)**.

Trong ASP.NET Core, khi bạn đăng ký một Scoped Service (như `DbContext`), hệ thống IoC Container tự động gọi `Dispose()` khi HTTP request kết thúc. Trong FastAPI, điều này được thực hiện kỳ diệu thông qua một Generator function:

```python
# Minh họa pattern FastAPI Yield Dependency
def get_db_session():
    """Dependency cung cấp session kết nối Database."""
    print("🔵 [1] Mở kết nối Database (Arrange / Setup)")
    db_session = {"connection_id": "conn_9981", "is_active": True}
    try:
        # yield tài nguyên ra cho Endpoint FastAPI sử dụng
        yield db_session
    finally:
        # Code phía sau yield LUÔN được thực thi sau khi Endpoint trả response
        db_session["is_active"] = False
        print("🔴 [3] Đã đóng kết nối Database an toàn (Teardown / Cleanup)")


# Mô phỏng cách FastAPI gọi dependency:
def simulate_fastapi_request():
    dep_generator = get_db_session()
    # 1. FastAPI lấy session bằng next()
    session = next(dep_generator)

    # 2. Thực thi Endpoint logic
    print(f"🟢 [2] Endpoint đang xử lý với DB: {session['connection_id']}")

    # 3. Request hoàn tất (hoặc lỗi), FastAPI gọi tiếp để chạy phần cleanup
    try:
        next(dep_generator)
    except StopIteration:
        pass


simulate_fastapi_request()
```

Khi bạn bước vào Bài 08 (Dependency Injection), bạn sẽ thấy mẫu thiết kế này chính là tiêu chuẩn vàng để quản lý Database Session với SQLAlchemy!

---

## 💻 Ví dụ thực hành

Dưới đây là một ví dụ thực tế toàn diện: Xây dựng một **Pipeline xử lý giao dịch tài chính (Streaming Transaction Pipeline)**. Hệ thống giả lập đọc hàng ngàn bản ghi, lọc các giao dịch khả nghi, gom thành từng lô (batch) 3 bản ghi và đẩy sang cổng thanh toán mà hoàn toàn không tốn bộ nhớ RAM:

```python
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from datetime import datetime
from itertools import batched, islice


@dataclass
class Transaction:
    id: int
    user_id: str
    amount: float
    timestamp: str


def transaction_stream(total: int) -> Generator[Transaction, None, None]:
    """Giả lập luồng giao dịch liên tục (streaming generator)."""
    for i in range(1, total + 1):
        # Giả lập số tiền biến thiên
        amount = 5_000_000.0 if i % 5 == 0 else 500_000.0
        yield Transaction(
            id=i,
            user_id=f"user_{i:04d}",
            amount=amount,
            timestamp=datetime.now().isoformat(),
        )


def filter_suspicious_transactions(
    stream: Iterable[Transaction], threshold: float
) -> Generator[Transaction, None, None]:
    """Lọc các giao dịch có số tiền lớn hơn ngưỡng cảnh báo (Lazy pipeline)."""
    for tx in stream:
        if tx.amount >= threshold:
            yield tx


def audit_processor():
    print("=== BẮT ĐẦU XỬ LÝ LUỒNG GIAO DỊCH ===")

    # 1. Khởi tạo pipeline: Giả lập 10,000 giao dịch (chưa tốn RAM)
    raw_stream = transaction_stream(total=10_000)

    # 2. Gắn bộ lọc: Chỉ lấy giao dịch >= 2,000,000 VND
    flagged_stream = filter_suspicious_transactions(raw_stream, threshold=2_000_000.0)

    # 3. Lấy 7 giao dịch đáng ngờ đầu tiên bằng islice
    sample_flagged = islice(flagged_stream, 7)

    # 4. Gom thành từng lô 3 bản ghi bằng batched (Python 3.12+)
    for batch_idx, batch in enumerate(batched(sample_flagged, 3), start=1):
        print(f"\n📦 Lô kiểm toán #{batch_idx} (Số lượng: {len(batch)}):")
        for tx in batch:
            print(f"  - [TX #{tx.id:04d}] User: {tx.user_id} | Số tiền: {tx.amount:,.0f} VND")

    print("\n=== HOÀN TẤT XỬ LÝ TIẾT KIỆM BỘ NHỚ ===")


audit_processor()
```

---

## ⚠️ Lỗi thường gặp

### 1. Cạn kiệt Generator (Generator Exhaustion)

Một Generator chỉ có thể duyệt qua đúng **một lần duy nhất**. Khi con trỏ đã đi tới cuối (ném `StopIteration`), generator bị coi là "cạn kiệt" (exhausted). Các lần duyệt sau sẽ rỗng:

```python
gen = (x * 2 for x in [1, 2, 3])

total = sum(gen)  # Lần 1: Duyệt hết các phần tử, total = 12
print(f"{total=}")

# Lỗi: Duyệt lại lần 2
items = list(gen)
print(f"{items=}")  # Kết quả: [] (Danh sách rỗng!)
```

> [!WARNING]
> Nếu bạn cần duyệt nhiều lần, hãy truyền vào một hàm tạo generator (generator factory) hoặc chuyển thành danh sách (`list(gen)`) nếu dữ liệu nhỏ và vừa vặn trong RAM.

### 2. Eager Conversion vô tội vạ làm tràn RAM

Lập trình viên chuyển từ C# sang thường có thói quen gọi `list()` ngay lập tức (giống thói quen `.ToList()` trong LINQ). Nếu luồng dữ liệu đến từ file log 10GB hoặc truy vấn database 5 triệu dòng, việc gọi `list(stream)` sẽ đánh sập server với lỗi `MemoryError`:

```python
# ❌ NGUY HIỂM: Ép toàn bộ dữ liệu lớn vào RAM cùng lúc
# def process_all_logs(log_file):
#     all_lines = list(read_huge_log(log_file))  # Sập RAM nếu file lớn!

#  ĐÚNG: Giữ nguyên iterator và xử lý từng phần tử hoặc chia lô
# def process_all_logs(log_file):
#     for batch in batched(read_huge_log(log_file), 1000):
#         save_to_db(batch)
```

### 3. Hiểu nhầm cách thức hoạt động của `itertools.groupby`

Như đã lưu ý, `itertools.groupby` không gom nhóm trên toàn bộ danh sách như LINQ `GroupBy()` mà chỉ gom các phần tử liên tiếp:

```python
from itertools import groupby

# Dữ liệu chưa sort
data = ["apple", "banana", "apricot", "cherry"]
# ❌ LỖI: Chữ 'a' xuất hiện 2 lần ở 2 vị trí cách nhau, groupby sẽ tạo 2 nhóm riêng biệt!
result = {k: list(v) for k, v in groupby(data, key=lambda s: s[0])}
# Kết quả chỉ giữ nhóm 'a' sau cùng hoặc phân rã nhóm!

#  ĐÚNG: Luôn sort trước khi groupby
sorted_data = sorted(data, key=lambda s: s[0])
correct_result = {k: list(v) for k, v in groupby(sorted_data, key=lambda s: s[0])}
print(correct_result)  # {'a': ['apple', 'apricot'], 'b': ['banana'], 'c': ['cherry']}
```

### 4. Ném `StopIteration` bên trong Generator (Vi phạm PEP 479)

Trong các phiên bản Python cũ, việc raise `StopIteration` bên trong generator function được dùng để ngắt generator. Tuy nhiên từ Python 3.7+ (PEP 479), nếu bạn chủ động ném `StopIteration`, Python sẽ biến nó thành `RuntimeError: generator raised StopIteration`.

```python
def my_generator():
    # ❌ SAI: raise StopIteration
    #  ĐÚNG: Dùng lệnh return để kết thúc generator
    return
```

---

## ✍️ Bài tập thực hành

### Bài 1: Bộ đọc dòng log theo chunk với `batched`
Viết hàm `chunked_log_reader(lines: Iterable[str], chunk_size: int)` nhận vào một iterable các chuỗi log (chuỗi có định dạng `"[LEVEL] message"`), loại bỏ các dòng trống hoặc khoảng trắng thừa, chỉ lọc ra các dòng log có level `[ERROR]` hoặc `[CRITICAL]`, sau đó chia thành từng batch có kích cỡ `chunk_size` và yield từng batch ra ngoài.

<details>
<summary>💡 Gợi ý</summary>

- Tạo generator phụ để làm sạch và lọc dòng:
  ```python
  def filter_errors(stream):
      for line in stream:
          clean = line.strip()
          if clean.startswith(("[ERROR]", "[CRITICAL]")):
              yield clean
  ```
- Dùng `itertools.batched(filter_errors(lines), chunk_size)` để yield từng lô dạng tuple.
</details>

---

### Bài 2: Triển khai Custom Range Iterator cho số thực (`FloatRange`)
Viết một class `FloatRange` đóng vai trò là một Iterable và Iterator (triển khai `__iter__` và `__next__`), cho phép duyệt các số thực từ `start` đến `stop` (không bao gồm stop) với bước nhảy `step` (mặc định `1.0`).
- Ví dụ: `list(FloatRange(0.0, 1.5, 0.5))` trả về `[0.0, 0.5, 1.0]`.
- Yêu cầu xử lý chính xác điều kiện dừng và ném `StopIteration`.

<details>
<summary>💡 Gợi ý</summary>

- Trong `__init__(self, start: float, stop: float, step: float = 1.0)`: lưu trữ `current = start`, `stop`, `step`. Kiểm tra nếu `step == 0` thì ném `ValueError`.
- `__iter__(self)` trả về `self`.
- Trong `__next__(self)`: kiểm tra nếu `(self.step > 0 and self.current >= self.stop)` hoặc `(self.step < 0 and self.current <= self.stop)` thì `raise StopIteration`. Lưu `val = self.current`, tăng `self.current += self.step`, và trả về `val`.
</details>

---

### Bài 3: Làm phẳng cấu trúc cây thư mục / danh mục đa tầng với `yield from`
Cho một cấu trúc danh mục sản phẩm phân cấp lồng nhau:
```python
category_tree = {
    "name": "Điện tử",
    "products": ["Tivi", "Tủ lạnh"],
    "children": [
        {
            "name": "Điện thoại",
            "products": ["iPhone", "Samsung Galaxy"],
            "children": [
                {
                    "name": "Phụ kiện",
                    "products": ["Cáp sạc", "Tai nghe"],
                    "children": [],
                }
            ],
        }
    ],
}
```
Viết hàm generator đệ quy `extract_all_products(category_node: dict) -> Generator[str, None, None]` sử dụng `yield from` để duyệt và trả về toàn bộ tên sản phẩm trong toàn bộ cây danh mục theo cơ chế Lazy.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng `yield from` để yield toàn bộ sản phẩm của node hiện tại, sau đó duyệt qua `children` và gọi đệ quy:
  ```python
  from collections.abc import Iterator


  def extract_all_products(category_node: dict) -> Iterator[str]:
      yield from category_node.get("products", [])
      for child in category_node.get("children", []):
          yield from extract_all_products(child)
  ```
</details>

---

### Bài 4: Mô phỏng FastAPI Yield Dependency với cơ chế Rollback
Xây dựng một generator `transaction_scope()` mô phỏng phiên làm việc với cơ sở dữ liệu:
- Khi bắt đầu: in thông báo `"Bắt đầu Transaction"`, yield một từ điển trạng thái `{"status": "in_progress", "changes": []}`.
- Nếu code bên ngoài khối hoàn thành bình thường: in `"Commit Transaction thành công!"`.
- Nếu code bên ngoài gặp lỗi (ném Exception): bắt ngoại lệ trong generator, in `"Phát hiện lỗi -> Thực hiện Rollback!"` và ném tiếp lỗi ra ngoài (re-raise).
- Cuối cùng (finally): in `"Đóng kết nối Transaction an toàn"`.
- Viết hàm kiểm thử kịch bản thành công và kịch bản thất bại.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng cấu trúc `try...except...finally` quanh lệnh `yield`:
  ```python
  def transaction_scope():
      print("Bắt đầu Transaction")
      tx = {"status": "in_progress", "changes": []}
      try:
          yield tx
          print("Commit Transaction thành công!")
          tx["status"] = "committed"
      except Exception:
          print("Phát hiện lỗi -> Thực hiện Rollback!")
          tx["status"] = "rolled_back"
          raise
      finally:
          print("Đóng kết nối Transaction an toàn")
  ```
- Dùng phương thức `.throw(Exception)` của generator để mô phỏng lỗi xảy ra trong endpoint.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn phân biệt được sự khác nhau giữa Iterable (`__iter__`) và Iterator (`__next__`)?
- [ ] Bạn hiểu rõ nguyên lý đóng băng và khôi phục ngữ cảnh (suspend/resume) của từ khóa `yield`?
- [ ] Bạn biết cách sử dụng `yield from` để ủy quyền và làm phẳng cấu trúc lồng nhau?
- [ ] Bạn nhận thức được hiện tượng cạn kiệt generator (generator exhaustion) và tránh lỗi ép kiểu `list()` gây cạn kiệt RAM?
- [ ] Bạn sử dụng thành thạo `itertools.islice`, `chain`, `batched` và nắm rõ quy tắc phải sort trước khi dùng `groupby`?
- [ ] Bạn hình dung được cách FastAPI ứng dụng Generator với `yield` để quản lý đóng mở Database Session?

---

## 📚 Đọc thêm

- [Python Documentation – The Iterator Protocol](https://docs.python.org/3/c-api/iter.html)
- [PEP 255 – Simple Generators](https://peps.python.org/pep-0255/)
- [PEP 380 – Syntax for Delegating to a Subgenerator (`yield from`)](https://peps.python.org/pep-0380/)
- [PEP 479 – Change StopIteration handling inside generators](https://peps.python.org/pep-0479/)
- [Python Documentation – itertools library](https://docs.python.org/3/library/itertools.html)

<!-- nav:bottom -->
---

[⬅️ Junior](./README.md) | [📚 Mục lục Junior](./README.md) | [Decorator & context manager ➡️](./02-decorators-context-managers.md)
<!-- /nav:bottom -->
