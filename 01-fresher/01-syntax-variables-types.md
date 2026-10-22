<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 01
<!-- /nav:top -->

# Cú pháp, biến & kiểu dữ liệu

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Level 00: Getting Started](../00-getting-started/README.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu sâu sắc bản chất **Name Binding (gán nhãn đối tượng)** trong CPython và sự khác biệt triệt để so với mô hình "hộp chứa giá trị" (Value Type) của C#.
- Sử dụng thành thạo các kiểu dữ liệu cơ bản: `int` (độ chính xác vô hạn, không lo tràn số), `float` (chuẩn IEEE 754), `bool`, `str`, `bytes` và `None`.
- Phân biệt tuyệt đối giữa so sánh danh tính bộ nhớ (**`is`**) và so sánh giá trị bình đẳng (**`==`**).
- Làm chủ định dạng chuỗi hiện đại với **f-strings** (`f"{val:.2f}"`, `f"{val=}"`), escape sequences và raw strings.
- Nắm vững các toán tử đặc thù của Python: phép chia thực (`/`), phép chia sàn (`//`), lũy thừa (`**`) và modulo (`%`).

---

## 🔁 So sánh với C# / ASP.NET

Trong C#, bạn quen thuộc với sự phân định rạch ròi giữa **Value Types** (`int`, `double`, `bool`, `struct` cấp phát trên Stack) và **Reference Types** (`string`, `class` cấp phát trên Managed Heap). 

Trong Python: **Mọi thứ đều là đối tượng (Everything is an object)** và được cấp phát trên Heap của CPython. Biến trong Python chỉ đơn thuần là một cái nhãn (tên tham chiếu) trỏ vào một vùng nhớ chứa đối tượng.

| Khái niệm / Cú pháp | C# / .NET | Python 3.13+ |
|---|---|---|
| **Cơ chế lưu biến** | Value Type: ô nhớ chứa trực tiếp giá trị; Reference Type: con trỏ tham chiếu | Biến chỉ là nhãn (name binding) gắn vào đối tượng trên Heap |
| **Kiểu số nguyên** | `int` (32-bit), `long` (64-bit), có nguy cơ tràn số (overflow) | `int` (arbitrary precision – vô hạn bit, không bao giờ tràn số) |
| **Kiểu số thực** | `float` (32-bit), `double` (64-bit), `decimal` (128-bit) | `float` (tương đương `double` 64-bit IEEE 754) |
| **Kiểu logic** | `bool` (`true`, `false`) | `bool` (`True`, `False` – kế thừa từ `int`, `True == 1`) |
| **Giá trị rỗng** | `null` (cho reference types và `Nullable<T>`) | `None` (singleton thuộc kiểu `NoneType`) |
| **Kiểu chuỗi** | `string` (immutable, UTF-16) | `str` (immutable, Unicode tối ưu qua PEP 393) |
| **Dữ liệu nhị phân** | `byte[]` hoặc `ReadOnlySpan<byte>` | `bytes` (immutable) hoặc `bytearray` (mutable) |
| **Nối chuỗi nội suy** | `$"Total: {total:C2}"` | `f"Total: {total:.2f}"` (f-string) |
| **So sánh giá trị** | `a == b` hoặc `a.Equals(b)` | `a == b` (gọi hàm ngầm `__eq__`) |
| **So sánh tham chiếu** | `object.ReferenceEquals(a, b)` | `a is b` (so sánh địa chỉ bộ nhớ `id(a) == id(b)`) |
| **Phép chia nguyên** | `7 / 2` cho kết quả `3` (với hai số nguyên) | `7 / 2` ra `3.5` (chia thực); `7 // 2` ra `3` (chia sàn) |
| **Lũy thừa** | `Math.Pow(2, 10)` | `2 ** 10` |

---

## 📖 Lý thuyết

### 1. Cơ chế Name Binding: Biến là nhãn, không phải là hộp

Trong C#, khi bạn viết:
```csharp
int a = 10;
int b = a;
b = 20;
```
Hệ thống tạo ra hai ô nhớ Stack riêng biệt cho `a` và `b`. Sửa `b` hoàn toàn không ảnh hưởng tới `a`.

Trong Python:
```python
a = 10
b = a
```
Hành động `a = 10` làm hai việc:
1. CPython tạo một đối tượng số nguyên có giá trị `10` trong bộ nhớ Heap.
2. CPython gắn nhãn tên `a` trỏ tới đối tượng `10` đó.
3. Khi gán `b = a`, nhãn `b` được trỏ cùng vào đối tượng `10` mà `a` đang trỏ.
4. Khi bạn gán `b = 20`, đối tượng `10` không hề bị thay đổi (bởi vì số nguyên là bất biến - immutable). Thay vào đó, CPython tạo một đối tượng `20` mới và dán nhãn `b` vào đối tượng `20`.

Hàm `id(obj)` trả về định danh duy nhất (trong CPython chính là địa chỉ bộ nhớ) của đối tượng. Bạn có thể dùng `is` để kiểm tra hai biến có đang trỏ tới cùng một địa chỉ hay không:

```python
x = 1000
y = x
print(x is y)  # True, cùng trỏ tới một vùng nhớ
print(id(x) == id(y))  # True
```

### 2. Hệ thống kiểu dữ liệu cơ sở

#### a. Kiểu số nguyên (`int`)
Khác với C# giới hạn `int` trong khoảng $-2^{31}$ đến $2^{31}-1$, kiểu `int` trong Python có **độ chính xác tùy ý (arbitrary precision)**. Bạn có thể tính toán với những con số có hàng trăm chữ số mà không bao giờ gặp ngoại lệ `OverflowException`.

```python
huge = 10**50  # 1 theo sau bởi 50 số 0
print(huge * huge)  # Vẫn tính toán chính xác tuyệt đối
```

Python hỗ trợ phân cách hàng nghìn bằng dấu gạch dưới `_` để dễ đọc:
```python
salary = 1_500_000_000  # tương đương 1500000000
```

#### b. Kiểu số thực (`float`)
`float` trong Python tương đương với `double` 64-bit IEEE 754 của C#. Cần lưu ý sai số dấu phẩy động kinh điển:
```python
print(0.1 + 0.2)  # 0.30000000000000004
```
> [!TIP]
> Trong các ứng dụng tài chính đòi hỏi độ chính xác tuyệt đối, hãy sử dụng module `decimal.Decimal` thay vì `float`.

#### c. Kiểu logic (`bool`)
Trong Python, `bool` là lớp con của `int`. Có hai giá trị duy nhất: `True` và `False` (lưu ý viết hoa chữ cái đầu, khác với `true`/`false` của C#).
```python
print(True + True)  # 2 (vì True có giá trị số là 1)
print(isinstance(True, int))  # True
```

#### d. Kiểu chuỗi (`str`)
Chuỗi trong Python là **bất biến (immutable)**. Bạn không thể sửa đổi một ký tự của chuỗi sau khi đã tạo ra.
- Cho phép dùng nháy đơn `'...'` hoặc nháy kép `"..."` tương đương nhau.
- Chuỗi nhiều dòng dùng ba dấu nháy `"""..."""` hoặc `'''...'''`.
- Raw string `r"C:\Users\name\docs"` bỏ qua escape sequence `\`, rất tiện lợi khi làm việc với đường dẫn file hoặc Regular Expressions.

#### e. Chuỗi nhị phân (`bytes`)
`bytes` biểu diễn một chuỗi byte 8-bit thô (dải giá trị 0–255), thường dùng khi đọc file nhị phân, giao tiếp socket mạng hoặc mã hóa mật mã.
- Khai báo bằng tiền tố `b`: `data = b"Hello\x00\xff"`.
- Chuyển `str` sang `bytes`: `s.encode("utf-8")`.
- Chuyển `bytes` sang `str`: `b.decode("utf-8")`.

#### f. Kiểu `None`
`None` là đối tượng singleton duy nhất của kiểu `NoneType`, tương đương với `null` trong C#.
- Dùng để biểu thị sự vắng mặt của giá trị hoặc giá trị trả về mặc định của một hàm không có lệnh `return`.
- **Quy tắc vàng**: Luôn luôn dùng `is None` hoặc `is not None` thay vì `== None`.

### 3. Phân biệt `is` vs `==`

Đây là một trong những điểm khác biệt cốt lõi mà lập trình viên C# phải phân biệt:
- **`==` (Equality)**: So sánh về mặt **giá trị / nội dung** của hai đối tượng (tương đương gọi `a.Equals(b)` hoặc toán tử `==` đã overload trong C#).
- **`is` (Identity)**: So sánh về mặt **danh tính / địa chỉ bộ nhớ** (tương đương `object.ReferenceEquals(a, b)` trong C#).

```python
list_a = [1, 2, 3]
list_b = [1, 2, 3]

print(list_a == list_b)  # True: nội dung giống hệt nhau
print(list_a is list_b)  # False: hai danh sách độc lập ở hai vùng nhớ khác nhau
```

### 4. Định dạng chuỗi hiện đại với f-string

Từ Python 3.6, **f-strings (Formatted string literals)** trở thành tiêu chuẩn vàng nhờ cú pháp ngắn gọn và tốc độ thực thi vượt trội (nhanh hơn toán tử `%` cũ và phương thức `.format()`).

Các kỹ thuật f-string thiết yếu:
```python
name = "Alice"
score = 95.6789
ratio = 0.854

# 1. Nhúng biểu thức trực tiếp
print(f"Xin chào, {name.upper()}!")

# 2. Định dạng số thập phân và làm tròn
print(f"Điểm số: {score:.2f}")  # 95.68

# 3. Định dạng phần trăm
print(f"Tỷ lệ hoàn thành: {ratio:.1%}")  # 85.4%

# 4. Thêm số 0 ở đầu (zero-padding) hoặc căn lề
task_id = 42
print(f"ID: {task_id:05d}")  # ID: 00042
print(f"{'Title':<10} | {'Status':>10}")

# 5. Tự ghi log gỡ lỗi với cú pháp f"{var=}" (Python 3.8+)
print(f"{name=}, {score=}")  # in ra: name='Alice', score=95.6789
```

### 5. Toán tử số học đặc thù

- **`/` (Phép chia thực)**: Luôn luôn trả về kiểu `float`, ngay cả khi hai số chia hết cho nhau (`4 / 2` trả về `2.0`, không phải `2`).
- **`//` (Phép chia sàn - Floor Division)**: Chia và làm tròn xuống số nguyên nhỏ hơn hoặc bằng gần nhất.
  - `7 // 2` cho kết quả `3`.
  - `-7 // 2` cho kết quả `-4` (vì -3.5 làm tròn xuống số nguyên nhỏ hơn là -4).
- **`**` (Lũy thừa)**: `2 ** 3` = `8`.
- **`%` (Modulo)**: Trong Python, dấu của phép chia lấy dư luôn cùng dấu với số chia (divisor), khác với C#.

---

## 💻 Ví dụ thực hành

Dưới đây là một đoạn code tổng hợp xử lý giao dịch tài chính và định dạng log chuẩn:

```python
from datetime import datetime

# 1. Tính toán số học chính xác
transaction_id = 1042
user_name = "nguyen van an"
gross_amount = 15_500_000  # VNĐ
tax_rate = 0.08  # 8% VAT
discount_rate = 0.05  # 5% giảm giá

tax_amount = gross_amount * tax_rate
discount_amount = gross_amount * discount_rate
net_total = gross_amount + tax_amount - discount_amount

# 2. Định dạng chuỗi và log gỡ lỗi
formatted_name = user_name.title()
log_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

log_line = (
    f"[{log_timestamp}] [TX:{transaction_id:06d}] "
    f"Khách hàng: {formatted_name:<20} | "
    f"Tổng tiền: {net_total:12,.0f} VND"
)
print(log_line)

# 3. Chuyển đổi Unicode sang bytes để mô phỏng ghi xuống socket/file
raw_payload: bytes = log_line.encode("utf-8")
print(f"Kích thước payload: {len(raw_payload)} bytes")

# 4. Giải mã ngược lại
decoded_text: str = raw_payload.decode("utf-8")
assert decoded_text == log_line, "Nội dung giải mã phải trùng khớp hoàn toàn!"

# 5. Kiểm tra tính danh tính
optional_note: str | None = None
if optional_note is None:
    print("Ghi chú: Không có ghi chú đính kèm.")
```

---

## ⚠️ Lỗi thường gặp

### 1. Dùng `is` để so sánh giá trị số hoặc chuỗi

Trong CPython, có cơ chế tối ưu nội bộ gọi là **Small Integer Caching** (các số nguyên từ `-5` đến `256` được tạo sẵn và dùng chung ô nhớ) và **String Interning**.

```python
x = 256
y = 256
print(x is y)  # Có thể in True (do Small Integer Caching)

a = 1000
b = 1000
print(a is b)  # Sẽ in False (đối tượng độc lập trên Heap)!
print(a == b)  # Luôn in True (so sánh giá trị)
```
> [!WARNING]
> Tuyệt đối không bao giờ dùng `is` cho số và chuỗi. Chỉ dùng `is` khi kiểm tra singleton như `None`, `True`, `False` hoặc muốn kiểm tra chính xác cùng 1 đối tượng bộ nhớ.

### 2. Cố gắng thay đổi ký tự trong chuỗi (`TypeError`)

Chuỗi trong Python là bất biến (immutable). Thói quen từ C# gán vào mảng ký tự sẽ gây lỗi:
```python
msg = "hello"
# msg[0] = "H"  # LỖI: TypeError: 'str' object does not support item assignment

# Cách khắc phục: Tạo chuỗi mới bằng slicing hoặc replace
msg = "H" + msg[1:]
print(msg)  # "Hello"
```

### 3. Nhầm lẫn giữa `/` và `//`

Dev C# thường mặc định `7 / 2` sẽ ra `3`. Trong Python, `7 / 2` ra `3.5`. Nếu bạn dùng kết quả phép chia này làm index cho danh sách hoặc cần số nguyên, Python sẽ báo lỗi `TypeError: list indices must be integers or slices, not float`. Hãy dùng `7 // 2`.

---

## ✍️ Bài tập thực hành

### Bài 1: Bộ tính toán chi phí & Định dạng biên lai
Viết chương trình tính toán tiền điện tiêu thụ theo bậc thang đơn giản:
- Số điện tiêu thụ: `285` kWh.
- 50 kWh đầu giá 1,806 đ/kWh; 50 kWh tiếp theo giá 1,866 đ/kWh; 100 kWh tiếp theo giá 2,167 đ/kWh; số còn lại giá 2,729 đ/kWh.
- Thuế VAT: 8%.
- In hóa đơn ra màn hình với đầy đủ căn lề, định dạng dấu phẩy phân cách hàng nghìn và hiển thị `f"{var=}"` cho các biến quan trọng.

<details>
<summary>💡 Gợi ý</summary>

- Tính từng phần: `tier1 = min(kwh, 50)`, `kwh_left = kwh - tier1`...
- Dùng f-string định dạng số: `f"{cost:,.0f} VND"`.
- Sử dụng căn lề: `f"{'Tiền điện:':<20} {subtotal:>15,.0f} VND"`.
</details>

---

### Bài 2: Chuẩn hóa dữ liệu người dùng & Trích xuất thông tin
Cho một chuỗi dữ liệu thô từ hệ thống cũ:
`raw_data = "   nGuyen   VAN   bInH  ;   binh.nv@COMPANY.COM.VN   ;   0912345678   "`
Hãy viết script xử lý:
1. Tách chuỗi thành 3 phần: Họ tên, Email, Số điện thoại.
2. Chuẩn hóa họ tên: loại bỏ khoảng trắng thừa giữa các từ, chuyển về định dạng viết hoa đầu mỗi từ (`Title Case`).
3. Chuẩn hóa email: loại bỏ khoảng trắng, chuyển toàn bộ về chữ thường, trích xuất tên miền (domain) đứng sau ký tự `@`.
4. In thông tin đã chuẩn hóa dưới dạng bảng gọn gàng.

<details>
<summary>💡 Gợi ý</summary>

- Dùng `raw_data.split(";")` để tách các trường.
- Với họ tên, dùng `name.split()` để tách các từ rồi `" ".join(...).title()`.
- Với email, dùng `email.strip().lower()`, sau đó dùng `.split("@")` để lấy domain.
</details>

---

### Bài 3: Kiểm tra tính toán số nguyên lớn và mã hóa dữ liệu
1. Tính giá trị $2^{128} - 1$ (giá trị tối đa của `UInt128` trong C#).
2. Chuyển con số trên thành chuỗi thập phân, sau đó mã hóa (`encode`) chuỗi sang mảng byte chuẩn UTF-8.
3. In ra số lượng ký tự của chuỗi, số lượng bytes của mảng byte, và byte đầu tiên/byte cuối cùng dưới dạng số nguyên.
4. Giải mã (`decode`) ngược lại và xác minh bằng câu lệnh kiểm tra `assert`.

<details>
<summary>💡 Gợi ý</summary>

- Tính: `val = (2 ** 128) - 1`.
- Chuyển chuỗi: `s = str(val)`.
- Mã hóa: `b = s.encode("utf-8")`.
- Lấy byte đầu: `b[0]`, byte cuối: `b[-1]`.
- Giải mã: `restored = b.decode("utf-8")` và so sánh `assert restored == s`.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn có thể giải thích được cơ chế name binding trong Python và tại sao biến số nguyên là bất biến?
- [ ] Bạn phân biệt rõ khi nào dùng `==` và khi nào dùng `is`?
- [ ] Bạn hiểu rõ sự khác nhau giữa `7 / 2`, `7 // 2` và `-7 // 2`?
- [ ] Bạn thành thạo việc dùng f-string để căn lề, format số thập phân và dùng `f"{val=}"` để debug?
- [ ] Bạn nắm được cách chuyển đổi an toàn giữa chuỗi `str` và mảng byte nhị phân `bytes` qua UTF-8?

---

## 📚 Đọc thêm

- [Tài liệu chính thức Python 3 – Built-in Types](https://docs.python.org/3/library/stdtypes.html)
- [PEP 498 – Literal String Interpolation (f-strings)](https://peps.python.org/pep-0498/)
- [Python Data Model: Objects, values and types](https://docs.python.org/3/reference/datamodel.html#objects-values-and-types)

<!-- nav:bottom -->
---

[⬅️ Fresher](./README.md) | [📚 Mục lục Fresher](./README.md) | [Điều kiện & vòng lặp ➡️](./02-control-flow.md)
<!-- /nav:bottom -->
