<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 11
<!-- /nav:top -->

# Công cụ: ruff & debugging

> ⏱️ Thời lượng: ~2.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 10: Type hints cơ bản](./10-type-hints-basics.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ cuộc cách mạng công cụ hiện đại trong hệ sinh thái Python: Thay thế toàn bộ dàn công cụ rời rạc (Flake8, Black, isort, pyupgrade) bằng **Ruff** – linter & formatter siêu tốc độ viết bằng Rust.
- Cấu hình chuyên nghiệp các tập quy tắc kiểm tra (linting rules) phổ biến trong file **`pyproject.toml`**: `E`, `F`, `I`, `B`, `UP`.
- Sử dụng thành thạo các câu lệnh CLI: `ruff check`, `ruff check --fix` (tự động sửa lỗi) và `ruff format` (chuẩn hóa thụt dòng, ngắt dòng).
- Làm chủ kỹ thuật gỡ lỗi tại chỗ với hàm tích hợp sẵn **`breakpoint()`** (PEP 553) qua trình gỡ lỗi dòng lệnh PDB (Python Debugger).
- Thiết lập cấu hình **`.vscode/launch.json`** để debug giao diện trực quan trong Visual Studio Code: Đặt điểm dừng (breakpoints), Step Over (F10), Step Into (F11), Call Stack và Watch Variables.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET, quy trình kiểm tra chất lượng mã nguồn và gỡ lỗi được tích hợp rất sâu vào hệ sinh thái Microsoft qua Roslyn Analyzers, `dotnet format`, và công cụ Debugger mạnh mẽ của Visual Studio / VS Code (C# Dev Kit). Dưới đây là bảng đối chiếu tương ứng trong Python:

| Tác vụ / Khái niệm | C# / .NET | Python Hiện Đại (Ruff & PDB) |
|---|---|---|
| **Công cụ Linting & Static Analysis** | Roslyn Analyzers, StyleCop, SonarAnalyzer | **Ruff** (viết bằng Rust, tốc độ nhanh hơn Flake8 x100 lần) |
| **Công cụ Format mã nguồn** | `dotnet format` | **`ruff format`** (thay thế Black, tốc độ tính bằng mili-giây) |
| **Sắp xếp import** | C# Usings sorting (Roslyn / Rider) | Tập rule **`I` (isort)** trong Ruff |
| **Nâng cấp cú pháp cũ lên mới** | C# Language Version upgrades (C# 10 → 12) | Tập rule **`UP` (pyupgrade)** trong Ruff |
| **File cấu hình dự án** | `.editorconfig`, file `.csproj` | File chuẩn **`pyproject.toml`** (section `[tool.ruff]`) |
| **Điểm dừng gỡ lỗi trong code** | `System.Diagnostics.Debugger.Break()` | Hàm tích hợp **`breakpoint()`** |
| **Trình gỡ lỗi dòng lệnh** | `dotnet-dump`, `lldb` (ít dùng cho dev app thông thường) | **PDB / iDB** (nhanh gọn, tương tác trực tiếp trên terminal) |
| **Cấu hình Debug VS Code** | File `.vscode/launch.json` (kiểu `"coreclr"`) | File `.vscode/launch.json` (kiểu `"python"`) |

---

## 📖 Lý thuyết

### 1. Tại sao Ruff lại là "Kẻ thay đổi cuộc chơi"?

Trước năm 2023, một dự án Python chuyên nghiệp thường phải cài đặt và duy trì 4-5 công cụ khác nhau:
1. `flake8` để bắt lỗi cú pháp và biến chưa dùng.
2. `black` để format code theo quy chuẩn PEP 8.
3. `isort` để sắp xếp thứ tự các câu lệnh `import`.
4. `pyupgrade` để nâng cấp cú pháp Python cũ.
5. `flake8-bugbear` để phát hiện các lỗi thiết kế tiềm ẩn.

Việc chạy từng công cụ này bằng Python tốn nhiều giây (thậm chí hàng chục giây trên codebase lớn), cấu hình phân tán và dễ xung đột nhau.

**Ruff** (được phát triển bởi Astral – đội ngũ đứng sau trình quản lý gói `uv`) đã hợp nhất toàn bộ các công cụ trên vào một binary duy nhất viết bằng **Rust**. Ruff nhanh hơn các công cụ cũ từ **10 đến 100 lần**, cho phép kiểm tra hàng trăm ngàn dòng code chỉ trong vài chục mili-giây ngay khi bạn gõ phím!

---

### 2. Cấu hình Ruff trong `pyproject.toml`

Chuẩn đóng gói hiện đại của Python (PEP 518/PEP 621) sử dụng file **`pyproject.toml`** ở thư mục gốc của dự án để cấu hình mọi công cụ:

```toml
[tool.ruff]
# Phiên bản Python đích để Ruff áp dụng quy tắc tối ưu
target-version = "py312"

# Độ dài tối đa của một dòng code (khuyến nghị chuẩn: 88 hoặc 100 ký tự)
line-length = 100

# Các thư mục cần bỏ qua
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.lint]
# Danh sách các bộ quy tắc (rule sets) kích hoạt:
select = [
    "E",   # pycodestyle errors (lỗi cú pháp PEP 8)
    "W",   # pycodestyle warnings (cảnh báo khoảng trắng, tab)
    "F",   # Pyflakes (bắt lỗi biến chưa dùng, import thừa, name error)
    "I",   # isort (sắp xếp và nhóm import chuẩn xác)
    "B",   # flake8-bugbear (phát hiện lỗi tiềm ẩn: mutable default arg, etc.)
    "UP",  # pyupgrade (tự động nâng cấp cú pháp lên Python 3.12+)
]

# Các quy tắc cụ thể muốn bỏ qua nếu có lý do chính đáng:
ignore = [
    "E501", # Bỏ qua cảnh báo dòng dài quá line-length (nếu muốn để ruff format tự xử lý)
]

[tool.ruff.lint.isort]
# Cấu hình gom nhóm imports
known-first-party = ["taskflow"]

[tool.ruff.format]
# Quy cách format chuỗi (khuyến nghị dùng nháy kép đồng nhất)
quote-style = "double"
indent-style = "space"
```

---

### 3. Các câu lệnh thao tác với Ruff qua `uv`

Nếu dự án của bạn sử dụng `uv`, bạn có thể chạy Ruff trực tiếp mà không cần kích hoạt thủ công môi trường ảo:

```bash
# 1. Quét kiểm tra toàn bộ dự án
uv run ruff check .

# 2. Tự động sửa chữa các lỗi có thể fix tự động (import thừa, sắp xếp import, nâng cấp type hints)
uv run ruff check --fix .

# 3. Format toàn bộ mã nguồn theo chuẩn PEP 8 (thay thế hoàn toàn Black)
uv run ruff format .

# 4. Kiểm tra xem format đã chuẩn chưa (dùng cho CI pipeline)
uv run ruff format --check .
```

---

### 4. Gỡ lỗi với `breakpoint()` và PDB

Python 3.7 giới thiệu hàm tích hợp sẵn **`breakpoint()`** (PEP 553). Khi CPython thực thi đến dòng này, chương trình sẽ lập tức tạm dừng và mở ra một phiên làm việc interactive PDB ngay trong cửa sổ terminal của bạn:

```python
def calculate_task_progress(tasks: list[dict[str, object]]) -> float:
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed") is True)

    # Đặt điểm dừng để kiểm tra các giá trị biến trước khi chia:
    breakpoint()

    return (completed / total) * 100
```

Khi chạy `python script.py`, terminal sẽ dừng lại tại dòng lệnh:
```text
(Pdb) 
```

#### Các phím tắt cốt lõi trong PDB:
- **`n` (next)**: Thực hiện dòng lệnh tiếp theo (Step Over).
- **`s` (step)**: Nhảy vào bên trong hàm đang được gọi (Step Into).
- **`c` (continue)**: Cho chương trình chạy tiếp cho đến khi gặp `breakpoint()` kế tiếp hoặc kết thúc.
- **`p <biến>` (print)**: In giá trị của một biến (ví dụ `p total`, `p completed`).
- **`pp <biến>` (pretty-print)**: In dictionary hoặc list phức tạp thụt dòng dễ nhìn.
- **`l` (list)**: Xem 11 dòng mã nguồn xung quanh vị trí đang dừng.
- **`w` (where)**: In toàn bộ Stack Trace (ngăn xếp lời gọi hàm).
- **`q` (quit)**: Thoát ngay lập tức khỏi chương trình đang debug.

---

### 5. Cấu hình Debugger trong VS Code (`launch.json`)

Nếu bạn quen debug bằng giao diện chuột trực quan trong Visual Studio / C#, VS Code hỗ trợ trải nghiệm tương đương 100% với extension Python.

Tạo file **`.vscode/launch.json`** trong thư mục gốc của dự án:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Chạy file hiện tại",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "TaskFlow: Debug CLI",
      "type": "debugpy",
      "request": "launch",
      "module": "taskflow.cli",
      "args": ["list", "--status", "TODO"],
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

#### Cách sử dụng:
1. Nhấp chuột vào lề trái cạnh số dòng trong VS Code để tạo **chấm đỏ (Red Breakpoint)**.
2. Bấm phím **F5** để bắt đầu Debug.
3. Thanh công cụ debug xuất hiện trên cùng:
   - **F10**: Step Over (chạy qua dòng hiện tại).
   - **F11**: Step Into (nhảy vào thân hàm con).
   - **Shift + F11**: Step Out (thoát ra khỏi hàm con hiện tại).
   - **Ctrl + Shift + F5**: Khởi động lại phiên debug.
   - **Shift + F5**: Dừng phiên debug.
4. Bảng điều khiển bên trái hiển thị toàn bộ:
   - **Variables**: Biến cục bộ (Locals) và toàn cục (Globals).
   - **Watch**: Thêm biểu thức muốn theo dõi (ví dụ `len(tasks)`).
   - **Call Stack**: Ngăn xếp các hàm đang chờ thực thi.

---

## 💻 Ví dụ thực hành

Dưới đây là một ví dụ minh họa việc phát hiện và tự động sửa các lỗi phổ biến bằng Ruff cùng việc áp dụng `breakpoint()`:

```python
# File: demo_clean_code.py
from datetime import datetime
from typing import Any


def process_orders(
    orders: list[dict[str, Any]],
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Lọc và chuẩn hóa dữ liệu đơn hàng."""
    processed = []

    for order in orders:
        # Giả lập debug kiểm tra dữ liệu order
        current_status = order.get("status")
        if status_filter and current_status != status_filter:
            continue

        item_copy = {
            "order_id": order["id"],
            "status": str(current_status).upper(),
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        processed.append(item_copy)

    return processed


def run_demo() -> None:
    raw_orders = [
        {"id": 101, "status": "pending"},
        {"id": 102, "status": "shipped"},
        {"id": 103, "status": "pending"},
    ]

    print("=== DEMO RUN RUFF & DEBUGGING ===")
    results = process_orders(raw_orders, status_filter="pending")
    for r in results:
        print(f"Order #{r['order_id']} -> {r['status']}")


if __name__ == "__main__":
    run_demo()
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên gỡ bỏ lệnh `breakpoint()` trước khi push code lên Git
- **Hậu quả**: Khi mã được chạy trên môi trường CI/CD hoặc production, tiến trình sẽ bị "đơ" vô hạn vì chờ tương tác bàn phím từ terminal mà không ai biết!
- **Phòng chống**: Bộ rule **`T10` (flake8-debugger)** của Ruff sẽ chặn đứng lỗi này:
  Khi bạn chạy `ruff check`, Ruff sẽ báo lỗi đỏ: `T100: Traceback breakpoint call found` và cấm merge code!

### 2. Dùng nhiều formatter xung đột nhau
- Cài đồng thời cả Black, Prettier, và Autopep8 trong VS Code. Mỗi khi bấm `Ctrl + S`, file bị nhảy định dạng liên tục do mỗi công cụ có quy chuẩn khoảng trắng khác nhau.
- **Khắc phục**: Chỉ cài đặt duy nhất extension **Ruff** trong VS Code và đặt làm Formatter mặc định:
  ```json
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  }
  ```

### 3. Không đưa cấu hình Ruff vào `pyproject.toml`
- Chạy `ruff check` bằng các tham số dòng lệnh rời rạc khiến mỗi thành viên trong team chạy một kiểu quy tắc khác nhau.
- Luôn commit file `pyproject.toml` có cấu hình `[tool.ruff]` vào Git để chuẩn hóa toàn bộ dự án.

---

## ✍️ Bài tập thực hành

### Bài 1: Thiết lập cấu hình `pyproject.toml` chuẩn cho TaskFlow
Tạo một file mẫu `pyproject.toml` đáp ứng các yêu cầu:
1. Target version là Python 3.12.
2. Line length là 88 ký tự.
3. Kích hoạt đầy đủ 6 tập rule: `E`, `W`, `F`, `I`, `B`, `UP`.
4. Bỏ qua rule `B008` (cho phép function call trong argument defaults – thiết yếu cho FastAPI sau này).
5. Bật `quote-style = "double"` cho formatter.

<details>
<summary>💡 Gợi ý</summary>

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP"]
ignore = ["B008"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```
</details>

---

### Bài 2: Sửa lỗi mã nguồn tự động với Ruff
Cho đoạn mã sau chứa các lỗi: import thừa không dùng (`math`), import sai thứ tự, dùng cú pháp typing cũ `List`, `Dict`, và dùng default mutable argument:

```python
# Đoạn mã bẩn:
from typing import Dict, List
import sys
import os


def process_items(items: List[Dict[str, str]] = []) -> None:
    import math

    print(f"Tổng số phần tử: {len(items)}")
```

Hãy giải thích:
1. Những rule nào của Ruff (`F`, `I`, `UP`, `B`) sẽ phát hiện các lỗi trên?
2. Câu lệnh `ruff check --fix` sẽ tự động sửa những lỗi nào, và lỗi nào bắt buộc lập trình viên phải sửa bằng tay?

<details>
<summary>💡 Gợi ý</summary>

1. **Phân tích rule**:
   - `F401`: `import os`, `import sys`, `import math` không dùng.
   - `I001`: Thứ tự import chưa được sắp xếp theo chuẩn standard library -> third party -> local.
   - `UP006`: `List`, `Dict` từ `typing` sẽ được gợi ý chuyển thành `list`, `dict`.
   - `B006`: `items: ... = []` sử dụng mutable argument nguy hiểm.
2. **Khả năng tự fix**:
   - `ruff check --fix` sẽ tự xóa `import os, sys, math` thừa, sắp xếp lại import, và chuyển `List[Dict[...]]` thành `list[dict[...]]`.
   - Lỗi `B006` (mutable default) **không thể tự fix** vì cần lập trình viên quyết định logic (phải đổi thành `= None` rồi gán trong thân hàm `if items is None: items = []`).
</details>

---

### Bài 3: Gỡ lỗi thuật toán với `breakpoint()`
Cho hàm tìm kiếm nhị phân có lỗi logic:

```python
def binary_search(nums: list[int], target: int) -> int:
    left = 0
    right = len(nums) - 1

    while left <= right:
        mid = (left + right) // 2
        # Đặt breakpoint() tại đây để quan sát left, right, mid trong từng vòng lặp
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid  # Gợi ý: Có thể gây vòng lặp vô tận! Sửa đúng là mid + 1
        else:
            right = mid  # Sửa đúng là mid - 1
    return -1
```

Hãy chèn `breakpoint()` vào vòng lặp, chạy thử với `nums = [1, 3, 5, 7, 9]` và `target = 7`, sử dụng lệnh `p left`, `p right`, `p mid` và `n` để quan sát sự kẹt của vòng lặp vô tận và sửa lại cho đúng.

<details>
<summary>💡 Gợi ý</summary>

- Khi `left = mid`, nếu khoảng cách giữa `left` và `right` là 1, phép chia nguyên `(left + right) // 2` sẽ luôn giữ nguyên `mid == left`, khiến vòng lặp `while` không bao giờ kết thúc.
- Sửa đúng:
  ```python
  left = mid + 1
  right = mid - 1
  ```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu vì sao Ruff thay thế Flake8, Black, isort, pyupgrade và ưu thế tốc độ vượt trội của nó?
- [ ] Bạn biết cách khai báo cấu hình Ruff trong file chuẩn `pyproject.toml`?
- [ ] Bạn nắm vững ý nghĩa các bộ rule: `E`, `W`, `F`, `I`, `B`, `UP`?
- [ ] Bạn sử dụng thành thạo các lệnh `ruff check --fix` và `ruff format`?
- [ ] Bạn biết cách dùng hàm `breakpoint()` và các phím tắt cơ bản trong PDB (`n`, `s`, `c`, `p`, `q`)?
- [ ] Bạn biết cách cấu hình `.vscode/launch.json` để debug ứng dụng CLI với các tham số đầu vào?

---

## 📚 Đọc thêm

- [Ruff Official Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules Reference](https://docs.astral.sh/ruff/rules/)
- [Python Documentation – `pdb` — The Python Debugger](https://docs.python.org/3/library/pdb.html)
- [PEP 553 – Built-in `breakpoint()`](https://peps.python.org/pep-0553/)
- [VS Code Python Debugging Guide](https://code.visualstudio.com/docs/python/debugging)

<!-- nav:bottom -->
---

[⬅️ Type hints cơ bản](./10-type-hints-basics.md) | [📚 Mục lục Fresher](./README.md) | [M0 – CLI Task Manager ➡️](../project/m0-cli-task-manager.md)
<!-- /nav:bottom -->
