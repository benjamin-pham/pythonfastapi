<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 06
<!-- /nav:top -->

# Module & package

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 05: Hàm](./05-functions.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Thấu hiểu bản chất kiến trúc mô-đun hóa trong Python: Mỗi file `.py` là một **Module**, mỗi thư mục chứa module là một **Package**.
- Nắm vững vai trò của file **`__init__.py`** trong việc đóng gói, khởi tạo package và kiểm soát API công khai qua **`__all__`**.
- Phân biệt và sử dụng đúng đắn giữa **Absolute Import** (nhập tuyệt đối) và **Relative Import** (nhập tương đối).
- Làm chủ idiom kinh điển **`if __name__ == "__main__":`** để phân tách giữa mã dùng làm thư viện và mã dùng làm điểm vào thực thi (entrypoint).
- Hiểu rõ cơ chế tìm kiếm module qua danh sách **`sys.path`**.
- Nhận diện nguyên nhân gốc rễ của lỗi **Circular Import** (vòng lặp phụ thuộc) và áp dụng các chiến lược giải quyết chuẩn mực.

---

## 🔁 So sánh với C# / ASP.NET

Đối với lập trình viên C#, hệ thống tổ chức mã nguồn thường gắn liền với `namespace`, project file (`.csproj`) và các assembly (`.dll`). Trong Python, cơ chế này đơn giản và gắn liền trực tiếp với hệ thống tập tin (File System).

| Khái niệm / Tác vụ | C# / .NET | Python 3.13+ |
|---|---|---|
| **Đơn vị mã nguồn cơ sở** | File mã nguồn `.cs` (phải chứa class/interface) | **Module**: Một file `.py` bất kỳ |
| **Không gian tên (Namespace)** | Khai báo từ khóa `namespace MyCompany.Services` (độc lập với thư mục vật lý) | **Package**: Ánh xạ 1-1 với thư mục vật lý trên ổ đĩa |
| **Khai báo package** | Thư mục dự án chứa file `.csproj` | Thư mục chứa file `__init__.py` |
| **Nạp thư viện / mã khác** | `using MyCompany.Services;` | `import module_name` hoặc `from package import module` |
| **Bí danh (Alias)** | `using JsonObj = System.Text.Json.Nodes.JsonObject;` | `import numpy as np` hoặc `from x import y as z` |
| **Điểm vào ứng dụng (Entrypoint)** | Phương thức `static void Main(string[] args)` hoặc Top-level statements | Khối điều kiện `if __name__ == "__main__":` |
| **Đường dẫn tìm kiếm thư viện** | Assembly probing, GAC, NuGet global cache | Danh sách đường dẫn trong danh sách `sys.path` |
| **Phụ thuộc vòng tròn (Circular Dependency)** | Compiler báo lỗi khi hai project tham chiếu vòng (`.csproj` -> `.csproj`) | Runtime báo lỗi `ImportError: partially initialized module` do nạp module tuần tự |

---

## 📖 Lý thuyết

### 1. Module và Package là gì?

- **Module**: Đơn giản là một file mã nguồn có đuôi mở rộng `.py` (ví dụ `utils.py`, `models.py`). Tên của module chính là tên file (không kèm đuôi `.py`).
- **Package**: Là một thư mục chứa một hoặc nhiều module, và thường chứa một file đặc biệt tên là **`__init__.py`**. Package có thể chứa các thư mục con khác (gọi là Subpackage).

Ví dụ một cấu trúc thư mục package điển hình:
```
taskflow/
├── __init__.py          # Đánh dấu taskflow là một package
├── cli.py               # Module taskflow.cli
├── core/
│   ├── __init__.py      # Đánh dấu core là một subpackage
│   └── task.py          # Module taskflow.core.task
└── storage/
    ├── __init__.py
    └── json_storage.py  # Module taskflow.storage.json_storage
```

### 2. Vai trò của file `__init__.py`

File `__init__.py` được CPython tự động thực thi khi package được import lần đầu tiên. Nó phục vụ 3 mục đích chính:

1. **Khởi tạo Package**: Thực thi các đoạn mã thiết lập cấu hình chung hoặc kết nối ban đầu nếu cần.
2. **Đóng gói và làm sạch Public API (Re-export)**: Thay vì bắt người dùng phải viết đường dẫn import dài dòng `from taskflow.core.task import TaskItem`, bạn có thể import và re-export `TaskItem` ngay trong `taskflow/__init__.py`. Người dùng chỉ cần viết: `from taskflow import TaskItem`.
3. **Kiểm soát `__all__`**: Biến đặc biệt `__all__` là một danh sách các chuỗi (list of strings) quy định những đối tượng nào được phép export ra ngoài khi người dùng sử dụng câu lệnh `from package import *`:

```python
# taskflow/__init__.py
from taskflow.core.task import TaskItem
from taskflow.storage.json_storage import JsonStorage

__all__ = ["TaskItem", "JsonStorage"]
```

### 3. Các dạng cú pháp `import`

Python hỗ trợ các hình thức import linh hoạt:

```python
# 1. Import toàn bộ module (an toàn, rõ ràng về nguồn gốc)
import math
result = math.sqrt(16)

# 2. Import trực tiếp đối tượng từ module
from math import sqrt, pi
result = sqrt(16)

# 3. Import kèm bí danh (alias)
import datetime as dt
from collections import defaultdict as ddict

# 4. Import toàn bộ bằng dấu sao '*' (NGUY HIỂM - ANTI-PATTERN!)
# from math import *
```

> [!WARNING]
> **Tuyệt đối tránh sử dụng `from module import *`**:
> Việc này gây ra hiện tượng **ô nhiễm không gian tên (namespace pollution)**, ghi đè các hàm trùng tên một cách âm thầm, làm mất khả năng gợi ý mã nguồn của IDE và khiến các công cụ kiểm tra tĩnh như Ruff cảnh báo vi phạm quy tắc `F403`/`F405`.

### 4. Absolute Import vs Relative Import

- **Absolute Import (Nhập tuyệt đối)**: Đường dẫn import được tính từ thư mục gốc của dự án (project root). Đây là tiêu chuẩn được chuẩn PEP 8 khuyến nghị vì tính minh bạch và dễ đọc.
  ```python
  from taskflow.core.task import TaskItem
  from taskflow.storage.json_storage import JsonStorage
  ```
- **Relative Import (Nhập tương đối)**: Sử dụng các dấu chấm `.` để tham chiếu vị trí tương đối so với module hiện tại:
  - Một dấu chấm `.`: Cùng thư mục hiện tại.
  - Hai dấu chấm `..`: Thư mục cha cấp trên.
  ```python
  # Trong file taskflow/core/task.py:
  from .exceptions import TaskError      # Cùng trong package 'core'
  from ..storage.json_storage import load # Từ package anh em 'storage'
  ```

> [!IMPORTANT]
> Relative import chỉ hoạt động khi module được thực thi bên trong ngữ cảnh của một package (ví dụ chạy lệnh `python -m taskflow.cli`). Nếu bạn chạy file trực tiếp bằng lệnh `python taskflow/core/task.py`, CPython không xác định được package cha và sẽ ném lỗi: `ImportError: attempted relative import with no known parent package`.

### 5. Cơ chế `if __name__ == "__main__":`

Mỗi khi CPython nạp một file mã nguồn, nó luôn tự động gán một biến đặc biệt có tên là `__name__`:
- Nếu file đó được **chạy trực tiếp** từ dòng lệnh (ví dụ: `python app.py`): CPython sẽ gán giá trị chuỗi `"__main__"` cho biến `__name__`.
- Nếu file đó được **import bởi một file khác** (ví dụ: `import app`): Biến `__name__` sẽ nhận giá trị là tên của module đó (ví dụ `"app"` hoặc `"taskflow.app"`).

```python
def main() -> None:
    print("Ứng dụng CLI Task Manager đang chạy...")

# Đoạn mã này CHỈ chạy khi file được thực thi trực tiếp từ terminal,
# và hoàn toàn KHÔNG tự chạy khi file này được import vào các module khác hoặc file test.
if __name__ == "__main__":
    main()
```

### 6. Cách Python tìm kiếm module qua `sys.path`

Khi bạn gõ lệnh `import something`, CPython sẽ tìm kiếm `something` theo thứ tự các đường dẫn được liệt kê trong danh sách `sys.path`:

```python
import sys
for path in sys.path:
    print(path)
```

Thứ tự ưu tiên của `sys.path`:
1. Thư mục chứa file script đang thực thi trực tiếp (hoặc thư mục làm việc hiện tại).
2. Các đường dẫn được cấu hình trong biến môi trường `PYTHONPATH`.
3. Thư mục cài đặt thư viện chuẩn của Python (Standard Library).
4. Thư mục `site-packages` bên trong Virtual Environment (`.venv`), nơi chứa các thư viện bên thứ ba cài qua `uv add`.

### 7. Vấn đề Circular Import (Vòng lặp phụ thuộc)

#### Nguyên nhân
CPython là ngôn ngữ thông dịch, nó nạp và thực thi các câu lệnh từ trên xuống dưới.
- Giả sử module `user.py` có dòng lệnh: `from order import get_user_orders`.
- Module `order.py` lại có dòng lệnh: `from user import get_user_profile`.
- Khi `user.py` chạy đến dòng import, CPython tạm dừng `user.py` để nhảy sang nạp `order.py`.
- Nhưng khi `order.py` cố import `get_user_profile` từ `user.py`, hàm này **chưa hề được định nghĩa** vì `user.py` chưa chạy xong!
- Kết quả: `ImportError: cannot import name 'get_user_profile' from partially initialized module 'user' (most likely due to a circular import)`.

#### Các giải pháp khắc phục
1. **Tái cấu trúc (Cách tốt nhất)**: Tách các kiểu dữ liệu, interface hoặc hàm dùng chung ra một module thứ ba độc lập (ví dụ `types.py` hoặc `common.py`) để cả hai module cùng import từ đó.
2. **Local Import (Lazy Import)**: Chuyển câu lệnh import vào bên trong thân của hàm cần sử dụng thay vì đặt ở đầu file.
3. **Sử dụng `TYPE_CHECKING` guard**: Nếu sự phụ thuộc vòng tròn chỉ xảy ra do việc khai báo Type Hints, hãy sử dụng `from typing import TYPE_CHECKING`:
   ```python
   from __future__ import annotations  # Cho phép type hint chuỗi ngầm định lúc runtime
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from taskflow.models.user import User  # Chỉ import khi chạy công cụ kiểm tra kiểu tĩnh (mypy/pylance)
   ```
   *(Lưu ý: Luôn kèm `from __future__ import annotations` hoặc dùng kiểu chuỗi `'User'` để tránh lỗi `NameError` lúc runtime khi module không được import thật sự).*

---

## 💻 Ví dụ thực hành

Dưới đây là một ví dụ minh họa hoàn chỉnh về cách tổ chức mã nguồn cho một package mini `app_audit`:

```python
# File mô phỏng cấu trúc logic trong package app_audit
from datetime import datetime
from typing import Any

# 1. Giả lập module models (app_audit/models.py)
class AuditEntry:
    def __init__(self, action: str, performed_by: str, status: str = "SUCCESS") -> None:
        self.action = action
        self.performed_by = performed_by
        self.status = status
        self.created_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "user": self.performed_by,
            "status": self.status,
            "timestamp": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

# 2. Giả lập module service (app_audit/service.py)
class AuditService:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record_event(self, action: str, performed_by: str, status: str = "SUCCESS") -> AuditEntry:
        entry = AuditEntry(action=action, performed_by=performed_by, status=status)
        self._entries.append(entry)
        return entry

    def list_events(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self._entries]

# 3. Giả lập module __init__.py (Re-export API sạch)
# __all__ chỉ cho phép export AuditService và AuditEntry
__all__ = ["AuditService", "AuditEntry"]

# 4. Điểm vào thực thi ứng dụng (app_audit/cli.py)
def run_cli_audit_demo() -> None:
    print("=== DEMO AUDIT SERVICE PACKAGE ===")
    service = AuditService()
    service.record_event("CREATE_USER", "admin")
    service.record_event("UPDATE_ROLE", "admin")
    service.record_event("DELETE_DATABASE", "guest", status="DENIED")

    for log in service.list_events():
        print(f"[{log['timestamp']}] [{log['status']:<7}] User: {log['user']:<6} -> {log['action']}")

# Chạy trực tiếp chỉ khi gọi từ terminal
if __name__ == "__main__":
    run_cli_audit_demo()
```

---

## ⚠️ Lỗi thường gặp

### 1. Đặt tên file trùng với thư viện chuẩn (Shadowing Standard Library)
Một lỗi rất phổ biến của người mới: Tạo một file tên là `random.py`, `json.py`, hay `email.py` để thực hành.
Khi bạn viết `import json`, do thư mục hiện tại đứng đầu tiên trong `sys.path`, CPython sẽ import chính file script của bạn thay vì module `json` chuẩn của Python, dẫn đến lỗi quái đản: `AttributeError: module 'json' has no attribute 'dumps'`.

> [!CAUTION]
> Tuyệt đối không bao giờ đặt tên file mã nguồn của bạn trùng với tên các thư viện chuẩn của Python hoặc thư viện bên ngoài đã cài đặt.

### 2. Chạy sai ngữ cảnh dẫn đến lỗi Relative Import
Nếu cấu trúc là `pkg/sub/worker.py` có dòng `from ..models import Item`, và bạn đứng trong thư mục `pkg/sub` rồi gõ lệnh `python worker.py`:
`ImportError: attempted relative import with no known parent package`
**Cách khắc phục chuẩn mực**: Đứng ở thư mục gốc của project (ngoài `pkg`) và chạy bằng cờ module:
`python -m pkg.sub.worker`

### 3. Vòng lặp Circular Import giữa Service và Model
Tạo quan hệ hai chiều chặt chẽ giữa Model và Service ở đầu file. Hãy tuân thủ nguyên tắc một chiều: Model không phụ thuộc vào Service; nếu cần tham chiếu kiểu dữ liệu chỉ để type check, dùng `from typing import TYPE_CHECKING`.

---

## ✍️ Bài tập thực hành

### Bài 1: Thiết kế cấu trúc Package cho CLI Task Manager
Hãy thiết kế cấu trúc thư mục và các file cho package `taskflow` chuẩn bị cho Milestone M0:
1. Thư mục `taskflow/` chứa file `__init__.py` và module `cli.py`.
2. Thư mục con `taskflow/core/` chứa `__init__.py` và `task.py`.
3. Thư mục con `taskflow/storage/` chứa `__init__.py` và `json_store.py`.
4. Trong `taskflow/__init__.py`, viết mã để re-export class `Task` từ `core.task` và định nghĩa `__all__ = ["Task"]`.
5. Trong `taskflow/cli.py`, viết câu lệnh `if __name__ == "__main__":` in ra dòng thông báo chào mừng và phiên bản package `taskflow`.

<details>
<summary>💡 Gợi ý</summary>

- Cấu trúc thư mục: Dùng lệnh `mkdir -p taskflow/core taskflow/storage` và tạo các file rỗng `touch taskflow/__init__.py ...`.
- Trong `taskflow/__init__.py`:
  ```python
  from taskflow.core.task import Task
  __all__ = ["Task"]
  ```
- Trong `taskflow/cli.py`:
  ```python
  from taskflow import Task

  def main() -> None:
      print("Khởi động TaskFlow CLI v1.0.0")

  if __name__ == "__main__":
      main()
  ```
- Thực thi thử nghiệm từ thư mục gốc bằng lệnh: `python -m taskflow.cli`.
</details>

---

### Bài 2: Khám phá và in thông tin `sys.path`
Viết một script ngắn `inspect_env.py` thực hiện:
1. Import module `sys` và `os`.
2. In ra đường dẫn của Python runtime đang chạy (`sys.executable`).
3. In ra danh sách toàn bộ các đường dẫn trong `sys.path` với định dạng đánh số thứ tự từ 1 (dùng `enumerate`).
4. Kiểm tra xem thư mục hiện tại (`os.getcwd()`) có nằm trong danh sách `sys.path` hay không.

<details>
<summary>💡 Gợi ý</summary>

- In runtime: `print(f"Runtime: {sys.executable}")`.
- In `sys.path`: `for idx, p in enumerate(sys.path, start=1): print(f"{idx}. {p}")`.
- Kiểm tra: `os.getcwd() in sys.path`.
</details>

---

### Bài 3: Giải quyết bài toán Circular Import
Cho hai module giả định gặp lỗi phụ thuộc vòng tròn:
- `user_service.py`: Cần kiểm tra trạng thái thanh toán từ `payment_service.py`.
- `payment_service.py`: Cần lấy thông tin chi tiết người dùng từ `user_service.py`.

Hãy phân tích và viết lại cấu trúc mã sử dụng một trong hai giải pháp:
- **Cách 1**: Tách hàm lấy thông tin dữ liệu dùng chung sang module `common_data.py`.
- **Cách 2**: Chuyển câu lệnh import vào bên trong thân hàm nghiệp vụ (Local/Lazy Import).

<details>
<summary>💡 Gợi ý</summary>

- Với giải pháp Local Import:
  ```python
  # Trong user_service.py:
  def process_user_checkout(user_id: str) -> None:
      # Lazy import đặt bên trong hàm để tránh xung đột khi load module
      from payment_service import charge_card
      charge_card(user_id, 100)
  ```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ sự khác biệt giữa một module (`.py` file) và một package (thư mục chứa `__init__.py`)?
- [ ] Bạn biết cách dùng `__init__.py` và `__all__` để tạo ra một Public API tinh gọn?
- [ ] Bạn nắm vững cú pháp và lý do nên ưu tiên Absolute Import theo chuẩn PEP 8?
- [ ] Bạn giải thích được bản chất hoạt động của câu lệnh `if __name__ == "__main__":`?
- [ ] Bạn hiểu cơ chế nạp module theo danh sách `sys.path` và biết cách xử lý khi gặp lỗi Circular Import?

---

## 📚 Đọc thêm

- [Python Documentation – Modules and Packages](https://docs.python.org/3/tutorial/modules.html)
- [PEP 8 – Style Guide for Python Code (Imports)](https://peps.python.org/pep-0008/#imports)
- [PEP 420 – Implicit Namespace Packages](https://peps.python.org/pep-0420/)

<!-- nav:bottom -->
---

[⬅️ Hàm](./05-functions.md) | [📚 Mục lục Fresher](./README.md) | [Exceptions ➡️](./07-exceptions.md)
<!-- /nav:bottom -->
