<!-- nav:top -->
[🏠 Home](../README.md) › Fresher
<!-- /nav:top -->

# Level 01: Fresher – Nền tảng Python Core

Chào mừng bạn đến với **Level 01: Fresher**. Đây là giai đoạn nền tảng quan trọng nhất trong toàn bộ lộ trình, giúp các kỹ sư C# / .NET chuyển dịch tư duy và làm chủ ngôn ngữ Python ở tầng cốt lõi (Python Core) theo chuẩn hiện đại nhất (Python 3.13+).

Tại level này, bạn không học cú pháp một cách hời hợt, mà sẽ đi sâu vào bản chất runtime của CPython: cơ chế quản lý bộ nhớ qua tham chiếu đối tượng (name binding), hệ sinh thái kiểu dữ liệu tích hợp phong phú, phong cách xử lý danh sách mạnh mẽ với comprehension, cách thiết kế hàm linh hoạt, kiến trúc module/package và mô hình hướng đối tượng tinh gọn với `@dataclass`.

---

## 🎯 Mục tiêu đầu ra

Sau khi hoàn thành Level 01 (dự kiến thời lượng: **`3–4 tuần`**, tương đương khoảng 30–40 giờ học tập và thực hành), bạn sẽ đạt được các năng lực cốt lõi sau:

- **Nắm vững Python Core**: Sử dụng thành thạo toàn bộ cú pháp hiện đại, cấu trúc điều khiển (`match/case`, `for...else`), 4 kiểu collections nền tảng (`list`, `tuple`, `dict`, `set`) và các biểu thức comprehension thay thế LINQ.
- **Tư duy hàm & thiết kế API sạch**: Nắm vững cơ chế truyền tham số (`*args`, `**kwargs`, positional-only `/`, keyword-only `*`), closure, scope LEGB và tránh hoàn toàn bẫy kinh điển mutable default argument.
- **Cấu trúc mã nguồn chuẩn module & package**: Biết cách tổ chức dự án nhiều file, hiểu rõ cơ chế tìm kiếm `sys.path`, xử lý triệt để circular import và điều khiển điểm vào bằng `if __name__ == "__main__"`.
- **Xử lý ngoại lệ & File I/O bền bỉ**: Áp dụng triệt để tư duy EAFP, xử lý ngoại lệ theo phân tầng và thao tác đọc/ghi file text, file JSON an toàn với context manager `with`.
- **Lập trình hướng đối tượng với `@dataclass`**: Thiết kế các class dữ liệu bất biến hoặc có xác thực cơ bản, so sánh trực tiếp với C# `record` và `class`.
- **Type Hints & Static Analysis**: Gắn type hints cơ bản theo chuẩn PEP 484/PEP 585/PEP 604, sử dụng linter siêu tốc **`ruff`** để kiểm tra và định dạng code, cùng kỹ năng debug chuyên nghiệp.
- **Xây dựng ứng dụng CLI hoàn chỉnh**: Tự tay triển khai toàn bộ dự án cột mốc [**M0 – CLI Task Manager**](../project/m0-cli-task-manager.md) có lưu trữ dữ liệu JSON, tách tầng module rõ ràng và quản lý bằng `uv`.

---

## 📚 Mục lục

Dưới đây là lộ trình 11 bài học chi tiết của Level 01:

| STT | Bài học | Thời lượng | Trọng tâm kiến thức |
|:---:|---|:---:|---|
| 01 | [**Cú pháp, biến & kiểu dữ liệu**](./01-syntax-variables-types.md) | ~2.5 giờ | Name binding, kiểu số vô hạn bit `int`, `float`, `bool`, `str`, f-strings, `bytes`, `None`, so sánh `is` vs `==`. |
| 02 | [**Điều kiện & vòng lặp**](./02-control-flow.md) | ~2.5 giờ | `if/elif/else`, ternary operator, Structural Pattern Matching `match/case`, `for...in`, `range`, `enumerate`, `zip`, `for...else`. |
| 03 | [**Collections: list, tuple, dict, set**](./03-collections.md) | ~3.5 giờ | `list` (slicing), `tuple` (unpacking), `dict` (ordered hash map, merge operator `\|`), `set` (set operations), hashable rules. |
| 04 | [**Comprehension**](./04-comprehensions.md) | ~2.5 giờ | List, dict, set comprehension, generator expressions, đối chiếu trực tiếp từng mẫu C# LINQ, giới hạn sử dụng. |
| 05 | [**Hàm**](./05-functions.md) | ~3.0 giờ | `def`, tuple return, `*args`, `**kwargs`, positional/keyword-only, LEGB scope, bẫy mutable default argument. |
| 06 | [**Module & package**](./06-modules-packages.md) | ~2.5 giờ | Tổ chức file module, vai trò `__init__.py`, `sys.path`, absolute vs relative import, `__name__ == "__main__"`, circular import. |
| 07 | [**Exceptions**](./07-exceptions.md) | ~2.5 giờ | Phân tầng exception, `try/except/else/finally`, custom exception, tư duy EAFP vs LBYL. |
| 08 | [**File I/O & JSON**](./08-file-io-json.md) | ~2.5 giờ | Context manager `with`, `pathlib.Path`, serialize/deserialize JSON, xử lý encoding UTF-8. |
| 09 | [**OOP & dataclass**](./09-oop-dataclasses.md) | ~3.5 giờ | Class, `__init__`, `@dataclass` (↔ C# `record`), dunder methods (`__str__`, `__repr__`, `__eq__`), kế thừa và composition. |
| 10 | [**Type hints cơ bản**](./10-type-hints-basics.md) | ~2.0 giờ | Type annotations: `int`, `str`, `list[T]`, `dict[K, V]`, `Optional` (`T \| None`), static analysis với Pylance/mypy. |
| 11 | [**Công cụ: ruff & debugging**](./11-tooling-ruff-debugging.md) | ~2.0 giờ | Cấu hình linter và formatter Ruff trong `pyproject.toml`, breakpoint debugging trong VS Code và pdb. |

---

## 🏆 Cột mốc thực hành: Milestone M0

Sau khi học xong 11 bài học trên, bạn sẽ bắt tay vào thực hiện dự án thực chiến đầu tiên:

👉 [**M0 – CLI Task Manager**](../project/m0-cli-task-manager.md)

Dự án này yêu cầu bạn xây dựng một ứng dụng quản lý công việc qua giao diện dòng lệnh (CLI), áp dụng toàn bộ kiến thức: phân tách module `taskflow`, lưu trữ dữ liệu bền vững vào file JSON, đóng gói model công việc bằng `@dataclass`, kiểm soát đầu vào, gõ type hint đầy đủ và kiểm tra sạch sẽ bằng `ruff`.

---

## 🧭 Đánh giá năng lực

Sau khi hoàn tất cả 11 bài học và Milestone M0, hãy đối chiếu kỹ năng của bạn với [**Bảng tự đánh giá năng lực**](../appendix/self-assessment.md) để khẳng định bạn đã sẵn sàng bước tiếp lên Level 02: Junior!

<!-- nav:bottom -->
---

[⬅️ Python cho dev C#](../00-getting-started/02-python-for-csharp-devs.md) | [🏠 Home](../README.md) | [Cú pháp, biến & kiểu dữ liệu ➡️](./01-syntax-variables-types.md)
<!-- /nav:bottom -->
