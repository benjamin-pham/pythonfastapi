<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 08
<!-- /nav:top -->

# File I/O & JSON

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 07: Exceptions](./07-exceptions.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Làm chủ cơ chế giải phóng tài nguyên tự động với context manager **`with open(..., encoding="utf-8") as f:`** tương đương câu lệnh `using` và interface `IDisposable` trong C#.
- Thao tác với hệ thống tập tin và đường dẫn hiện đại theo chuẩn hướng đối tượng bằng **`pathlib.Path`** (toán tử `/`, `.read_text()`, `.write_text()`, `.glob()`, `.mkdir()`) thay thế hoàn toàn module `os.path` cũ kỹ.
- Nắm vững các hàm chuyển đổi trong thư viện chuẩn **`json`**: Phân biệt rành mạch giữa `loads`/`dumps` (xử lý chuỗi) và `load`/`dump` (thao tác trực tiếp với stream file).
- Hiểu rõ ý nghĩa các tham số cốt lõi: **`indent`** (định dạng thụt dòng dễ đọc) và **`ensure_ascii=False`** (bảo toàn ký tự Unicode tiếng Việt có dấu).
- Giải quyết bài toán mở rộng tuần tự hóa (custom serialization) cho các kiểu dữ liệu nâng cao như **`datetime`**, **`date`** và **`UUID`** sang định dạng JSON chuẩn.

---

## 🔁 So sánh với C# / ASP.NET

Đối với lập trình viên C#, thao tác file và JSON thường gắn liền với `System.IO` (`File`, `FileInfo`, `Path`, `StreamReader`) và thư viện `System.Text.Json` hoặc `Newtonsoft.Json`. Dưới đây là bảng đối chiếu chi tiết tương ứng trong Python:

| Tác vụ / Khái niệm | C# / .NET | Python 3.10+ |
|---|---|---|
| **Quản lý tài nguyên an toàn** | `using (var stream = ...)` | `with open(...) as f:` (Context Manager) |
| **Đường dẫn tập tin (OOP)** | `System.IO.Path` / `FileInfo` | `pathlib.Path` |
| **Ghép đường dẫn (Path combining)** | `Path.Combine(folder, "data.json")` | `folder / "data.json"` (Toán tử `/` nạp chồng) |
| **Đọc toàn bộ file văn bản** | `File.ReadAllText("data.txt")` | `Path("data.txt").read_text(encoding="utf-8")` |
| **Ghi toàn bộ file văn bản** | `File.WriteAllText("data.txt", content)` | `Path("data.txt").write_text(content, encoding="utf-8")` |
| **Đọc từng dòng tránh tràn RAM** | `File.ReadLines("huge.log")` (IEnumerable) | `for line in f:` (File object là một iterator) |
| **Deserialize JSON từ string** | `JsonSerializer.Deserialize<T>(jsonStr)` | `json.loads(json_str)` (trả về `dict` / `list`) |
| **Serialize object sang JSON string** | `JsonSerializer.Serialize(obj, options)` | `json.dumps(data, indent=2, ensure_ascii=False)` |
| **Đọc / Ghi JSON trực tiếp từ Stream** | `JsonSerializer.DeserializeAsync(stream)` | `json.load(file_obj)` / `json.dump(data, file_obj)` |
| **Hỗ trợ Unicode tiếng Việt** | Mặc định hoặc cấu hình `JavaScriptEncoder` | `ensure_ascii=False` |
| **Tùy biến serializer cho Datetime** | `JsonConverter<DateTime>` | Tham số `default=custom_serializer` |

---

## 📖 Lý thuyết

### 1. Quản lý tài nguyên với `with open(...) as f:`

Trong hệ điều hành, file descriptor (bộ mô tả tập tin) là một tài nguyên giới hạn. Nếu mở file mà quên đóng (`f.close()`), hệ điều hành có thể cạn kiệt handle (lỗi `Too many open files`) hoặc dữ liệu đang nằm trên buffer chưa kịp flush xuống đĩa cứng khi chương trình gặp sự cố.

Python cung cấp câu lệnh **`with`** (Context Manager). Khi khối mã bên trong `with` kết thúc (kể cả khi bị ngắt bởi `return`, `break`, hay một ngoại lệ bất ngờ), Python luôn tự động gọi phương thức `__exit__()` để đóng file an toàn:

```python
# Cú pháp chuẩn mực để đọc file văn bản:
with open("tasks.txt", mode="r", encoding="utf-8") as f:
    content = f.read()
# Ra khỏi khối with, file chắc chắn đã được đóng (f.closed == True)
```

#### Các chế độ mở file (`mode`):
- `"r"`: Mở để đọc (mặc định). Ném lỗi `FileNotFoundError` nếu file chưa tồn tại.
- `"w"`: Mở để ghi mới. Nếu file đã tồn tại, toàn bộ nội dung cũ sẽ bị xóa trắng (truncate)!
- `"a"`: Mở để ghi nối tiếp (append). Dữ liệu mới được thêm vào cuối file.
- `"x"`: Mở để tạo mới độc quyền (exclusive creation). Ném `FileExistsError` nếu file đã có từ trước.
- Thêm hậu tố `"b"` (như `"rb"`, `"wb"`): Mở ở chế độ nhị phân (binary mode) để xử lý hình ảnh, PDF, audio (`bytes`).

> [!IMPORTANT]
> **Luôn chỉ định tường minh `encoding="utf-8"`**:
> Nếu không chỉ định `encoding`, Python sẽ lấy giá trị mặc định của hệ điều hành (`locale.getencoding()`). Trên Windows tiếng Việt/Anh, giá trị này thường là `cp1252` (ANSI). Khi file của bạn có tiếng Việt có dấu, chương trình sẽ crash ngay lập tức với lỗi `UnicodeDecodeError: 'charmap' codec can't decode byte...`.

---

### 2. Thao tác đường dẫn hiện đại với `pathlib.Path`

Từ Python 3.4+, module **`pathlib`** đã trở thành tiêu chuẩn vàng thay thế hoàn toàn các hàm chuỗi rời rạc trong `os.path`. Một đối tượng `Path` đại diện cho một đường dẫn trừu tượng trên filesystem với đầy đủ phương thức tiện ích:

```python
from pathlib import Path

# 1. Khởi tạo đường dẫn
base_dir = Path("data")
file_path = base_dir / "tasks" / "today.json"  # Toán tử / ghép đường dẫn rất thanh lịch!

# 2. Tạo thư mục cha nếu chưa có (tương đương mkdir -p trong Linux)
file_path.parent.mkdir(parents=True, exist_ok=True)

# 3. Ghi và đọc nhanh (tự động mở và đóng file ngầm bên dưới)
file_path.write_text('{"status": "ok"}', encoding="utf-8")
text = file_path.read_text(encoding="utf-8")

# 4. Kiểm tra trạng thái tập tin
if file_path.exists() and file_path.is_file():
    print(f"Kích thước file: {file_path.stat().st_size} bytes")

# 5. Các thuộc tính trích xuất tên file
print(file_path.name)    # "today.json"
print(file_path.stem)    # "today" (không kèm đuôi)
print(file_path.suffix)  # ".json"
```

#### Tìm kiếm file với `.glob()` và `.rglob()`:
```python
current_dir = Path(".")

# Quét tất cả file .json trong thư mục hiện tại:
for path in current_dir.glob("*.json"):
    print(path.name)

# Quét đệ quy (recursive) xuyên qua tất cả thư mục con:
for path in current_dir.rglob("*.py"):
    print(path)
```

---

### 3. Đọc và ghi JSON với module `json`

JSON (JavaScript Object Notation) là định dạng trao đổi dữ liệu phổ biến nhất hiện nay trong các ứng dụng web và API. Module thư viện chuẩn `json` của Python ánh xạ trực tiếp giữa các kiểu dữ liệu JSON và Python:

| JSON Type | Python Type |
|---|---|
| `object` (`{}`) | `dict` |
| `array` (`[]`) | `list` |
| `string` | `str` |
| `number` (integer) | `int` |
| `number` (real) | `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

#### Quy tắc nhớ: Có chữ `s` (String) vs Không có chữ `s` (Stream/File)

- **`json.loads(s)`** (Load String): Giải mã một chuỗi JSON thành Python object (`dict` hoặc `list`).
- **`json.dumps(obj)`** (Dump String): Mã hóa một Python object thành chuỗi JSON.
- **`json.load(fp)`** (Load File Pointer): Đọc trực tiếp từ một file object đang mở.
- **`json.dump(obj, fp)`** (Dump File Pointer): Ghi trực tiếp Python object ra một file object đang mở.

```python
import json

data = {
    "project": "TaskFlow CLI",
    "version": 1,
    "completed": False,
    "tags": ["python", "fastapi", "cli"],
}

# 1. Chuyển đổi sang JSON String (dumps)
json_str = json.dumps(data, indent=2, ensure_ascii=False)
print(json_str)

# 2. Ghi trực tiếp ra file (dump)
with open("taskflow.json", mode="w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# 3. Đọc trực tiếp từ file (load)
with open("taskflow.json", mode="r", encoding="utf-8") as f:
    loaded_data = json.load(f)
```

#### Hai tham số "bắt buộc phải nhớ" khi làm việc với JSON:
1. **`indent=2`** (hoặc `indent=4`): Format JSON dạng cây phân cấp dễ đọc (pretty-print) thay vì dồn tất cả trên 1 dòng.
2. **`ensure_ascii=False`**: Mặc định là `True`, khiến mọi ký tự ngoài dải ASCII (như tiếng Việt: "Học lập trình") bị escape thành mã Unicode `\u0048\u1ecdc...`. Đặt `ensure_ascii=False` để giữ nguyên chữ tiếng Việt rõ ràng, giúp kích thước file nhỏ hơn và dễ đọc.

---

### 4. Xử lý kiểu dữ liệu nâng cao khi serialize (`datetime`, `UUID`)

Thư viện chuẩn `json` mặc định **không biết** cách chuyển đổi các đối tượng `datetime`, `date`, hay `UUID` sang chuỗi JSON và sẽ ném lỗi:
`TypeError: Object of type datetime is not JSON serializable`.

Để khắc phục, bạn có thể truyền hàm xử lý vào tham số **`default`** của `json.dump`/`json.dumps`:

```python
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4
import json


def json_serializer_helper(obj: Any) -> Any:
    """Hàm xử lý chuyển đổi các kiểu dữ liệu mà json chuẩn không hỗ trợ."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Kiểu dữ liệu {type(obj).__name__} không được hỗ trợ serialize!")


task_record = {
    "id": uuid4(),
    "title": "Hoàn thiện Milestone M0",
    "due_date": datetime(2026, 10, 25, 17, 30, 0),
    "is_active": True,
}

# Sử dụng tham số default:
serialized_json = json.dumps(
    task_record,
    indent=2,
    ensure_ascii=False,
    default=json_serializer_helper,
)
print(serialized_json)
```

---

## 💻 Ví dụ thực hành

Dưới đây là một repository lưu trữ dữ liệu hoàn chỉnh `task_repository.py` thao tác với file JSON, tích hợp đầy đủ xử lý ngoại lệ, đường dẫn `pathlib.Path` và hỗ trợ tiếng Việt:

```python
from datetime import datetime
from pathlib import Path
from typing import Any
import json


class TaskStorageError(Exception):
    """Ngoại lệ khi xảy ra lỗi ở tầng lưu trữ file."""


class JsonTaskRepository:
    """Repository quản lý danh sách công việc lưu trong file JSON."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        # Đảm bảo thư mục cha tồn tại
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _json_default(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Đối tượng kiểu {type(obj)} không thể serialize sang JSON.")

    def load_tasks(self) -> list[dict[str, Any]]:
        """Đọc danh sách công việc từ file. Nếu file chưa có, trả về danh sách rỗng."""
        if not self.file_path.exists():
            return []

        try:
            content = self.file_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            data = json.loads(content)
            if not isinstance(data, list):
                raise TaskStorageError("Nội dung file JSON phải là một mảng (List) các task.")
            return data
        except json.JSONDecodeError as err:
            raise TaskStorageError(f"File dữ liệu '{self.file_path}' bị lỗi cấu trúc JSON!") from err
        except OSError as err:
            raise TaskStorageError(f"Không thể đọc file từ ổ đĩa: {err}") from err

    def save_tasks(self, tasks: list[dict[str, Any]]) -> None:
        """Ghi danh sách công việc an toàn xuống file JSON."""
        # Sử dụng kỹ thuật ghi vào file tạm thời rồi đổi tên (Atomic Write)
        # để đảm bảo file chính không bị mất dữ liệu nếu máy tính bị sập nguồn đột ngột.
        temp_file = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file, mode="w", encoding="utf-8") as f:
                json.dump(
                    tasks,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=self._json_default,
                )
            # Thay thế file cũ bằng file tạm (thao tác nguyên tử trong POSIX)
            temp_file.replace(self.file_path)
        except OSError as err:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise TaskStorageError(f"Lỗi khi lưu dữ liệu vào đĩa: {err}") from err


def run_demo() -> None:
    db_path = Path("./temp_data/tasks.json")
    repo = JsonTaskRepository(db_path)

    sample_tasks = [
        {
            "id": 1,
            "title": "Thiết lập môi trường UV & Python 3.13",
            "priority": "HIGH",
            "completed": True,
            "created_at": datetime.now(),
        },
        {
            "id": 2,
            "title": "Viết tài liệu File I/O & JSON tiếng Việt có dấu",
            "priority": "CRITICAL",
            "completed": False,
            "created_at": datetime.now(),
        },
    ]

    print(f"Đang lưu {len(sample_tasks)} công việc vào '{db_path}'...")
    repo.save_tasks(sample_tasks)
    print("✅ Đã lưu thành công!")

    print("\nĐang đọc lại dữ liệu từ file...")
    loaded = repo.load_tasks()
    for task in loaded:
        status = "Xong" if task["completed"] else "Chưa"
        print(f" - [{task['id']}] [{status}] {task['title']} (Ưu tiên: {task['priority']})")

    # Dọn dẹp sau khi demo
    if db_path.exists():
        db_path.unlink()
        db_path.parent.rmdir()
        print("\nĐã dọn dẹp file tạm demo thành công.")


if __name__ == "__main__":
    run_demo()
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên `encoding="utf-8"` khi mở file
- **Triệu chứng**: Chạy code trên máy macOS hoặc Linux thì mượt mà, nhưng chuyển sang Windows của khách hàng hoặc CI runner Windows thì ném lỗi:
  `UnicodeDecodeError: 'charmap' codec can't decode byte 0x... in position ...`
- **Cách khắc phục**: Luôn luôn truyền `encoding="utf-8"` trong mọi lệnh `open(...)`, `Path.read_text(...)`, và `Path.write_text(...)`.

### 2. Quên `ensure_ascii=False` khi xuất dữ liệu tiếng Việt
- **Triệu chứng**: File JSON sau khi lưu hiển thị các ký tự khó hiểu:
  `"title": "H\u1ecdc l\u1eadp tr\u00ecnh Python"`
- **Cách khắc phục**: Thêm `ensure_ascii=False` vào `json.dump()` hoặc `json.dumps()`.

### 3. Nhầm lẫn giữa `load` vs `loads`, `dump` vs `dumps`
- Nhớ quy tắc: `json.loads(chuỗi_string)` và `json.dumps(đối_tượng)` (chữ **s** = String).
- Còn `json.load(file_object)` và `json.dump(đối_tượng, file_object)` nhận file handle trực tiếp. Truyền nhầm chuỗi vào `json.load("data.json")` sẽ ném lỗi: `AttributeError: 'str' object has no attribute 'read'`.

### 4. Đọc toàn bộ file khổng lồ vào bộ nhớ bằng `.read()`
- **Triệu chứng**: Khi đọc một file log dung lượng 5GB, việc gọi `f.read()` hoặc `f.readlines()` sẽ tải toàn bộ 5GB dữ liệu vào RAM, gây ra lỗi `MemoryError` hoặc làm ứng dụng bị hệ điều hành OOM Killer tiêu diệt.
- **Cách khắc phục**: Tận dụng tính chất iterator của file object để duyệt theo từng dòng một (dòng nào xử lý xong sẽ được garbage-collected):
  ```python
  with open("huge_system.log", mode="r", encoding="utf-8") as f:
      for line in f:
          if "ERROR" in line:
              print(line.strip())
  ```

---

## ✍️ Bài tập thực hành

### Bài 1: Quét và thống kê thư mục với `pathlib.Path`
Viết một script `folder_stats.py`:
1. Nhận vào một đường dẫn thư mục bất kỳ.
2. Quét đệ quy toàn bộ các file `.json` và `.py` trong thư mục đó bằng phương thức `.rglob()`.
3. In ra danh sách tên file, số lượng dòng code và kích thước file tính theo KB.
4. Xử lý ngoại lệ nếu thư mục được cung cấp không tồn tại.

<details>
<summary>💡 Gợi ý</summary>

```python
from pathlib import Path


def summarize_code_directory(target_dir: str) -> None:
    folder = Path(target_dir)
    if not folder.exists() or not folder.is_dir():
        print(f"Lỗi: Thư mục '{target_dir}' không tồn tại hoặc không phải là thư mục.")
        return

    print(f"=== Thống kê thư mục: {folder.resolve()} ===")
    patterns = ["*.py", "*.json"]
    total_files = 0
    total_size_bytes = 0

    for pattern in patterns:
        for file_path in folder.rglob(pattern):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_files += 1
                total_size_bytes += size
                print(f"[{file_path.suffix:<5}] {file_path.name:<30} ({size / 1024:.2f} KB)")

    print(f"Tổng số file: {total_files} | Tổng dung lượng: {total_size_bytes / 1024:.2f} KB")
```
</details>

---

### Bài 2: Đọc, cập nhật và lưu danh sách công việc vào JSON
Viết module quản lý file `task_store.py` thực hiện:
1. Hàm `add_task_to_file(file_path: Path, title: str, priority: str) -> dict[str, Any]`:
   - Nếu file chưa có hoặc rỗng, khởi tạo danh sách mới.
   - Tạo task mới với `id` tự tăng (bằng độ dài danh sách hiện tại + 1).
   - Ghi dữ liệu trở lại file với `indent=2`, `ensure_ascii=False`, và `encoding="utf-8"`.
2. Hàm `mark_task_done(file_path: Path, task_id: int) -> bool`:
   - Tìm task có `id` tương ứng, đổi trường `completed` thành `True`.
   - Nếu tìm thấy và sửa đổi thành công trả về `True`, nếu không thấy trả về `False`.

<details>
<summary>💡 Gợi ý</summary>

```python
from pathlib import Path
from typing import Any
import json


def add_task_to_file(file_path: Path, title: str, priority: str = "MEDIUM") -> dict[str, Any]:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tasks: list[dict[str, Any]] = []

    if file_path.exists() and file_path.stat().st_size > 0:
        tasks = json.loads(file_path.read_text(encoding="utf-8"))

    new_id = len(tasks) + 1
    new_task = {
        "id": new_id,
        "title": title,
        "priority": priority.upper(),
        "completed": False,
    }
    tasks.append(new_task)

    file_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
    return new_task


def mark_task_done(file_path: Path, task_id: int) -> bool:
    if not file_path.exists():
        return False

    tasks: list[dict[str, Any]] = json.loads(file_path.read_text(encoding="utf-8"))
    found = False
    for task in tasks:
        if task.get("id") == task_id:
            task["completed"] = True
            found = True
            break

    if found:
        file_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
    return found
```
</details>

---

### Bài 3: Bộ tuần tự hóa JSON tùy biến đa kiểu dữ liệu
Tạo một hàm `custom_json_dumps(data: Any) -> str`:
1. Chuyển đổi an toàn đối tượng `datetime` và `date` thành định dạng chuẩn ISO 8601 (`obj.isoformat()`).
2. Chuyển đổi đối tượng `UUID` thành chuỗi UUID (`str(obj)`).
3. Chuyển đổi đối tượng `set` thành danh sách đã sắp xếp (`sorted(list(obj))`).
4. Nếu gặp kiểu dữ liệu khác không hỗ trợ, ném `TypeError`.
5. Đảm bảo kết quả trả về thụt dòng `indent=2` và giữ nguyên tiếng Việt.

<details>
<summary>💡 Gợi ý</summary>

```python
from datetime import date, datetime
from typing import Any
from uuid import UUID
import json


def _extended_encoder(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, set):
        return sorted(list(obj))
    raise TypeError(f"Kiểu {type(obj).__name__} không được hỗ trợ để encode JSON!")


def custom_json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=_extended_encoder)
```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ nguyên lý hoạt động của context manager `with open(...)` và vì sao không nên đóng file thủ công bằng `close()`?
- [ ] Bạn luôn nhớ đặt `encoding="utf-8"` trong mọi hàm đọc/ghi file?
- [ ] Bạn thành thạo việc tạo, ghép đường dẫn với toán tử `/` và đọc/ghi file nhanh bằng `pathlib.Path`?
- [ ] Bạn phân biệt rành rẽ giữa 4 hàm `loads`, `dumps`, `load`, `dump` trong module `json`?
- [ ] Bạn hiểu rõ tác dụng của tham số `indent` và `ensure_ascii=False` khi xuất dữ liệu tiếng Việt?
- [ ] Bạn biết cách sử dụng tham số `default` để tuần tự hóa các kiểu dữ liệu như `datetime` và `UUID`?

---

## 📚 Đọc thêm

- [Python Documentation – Reading and Writing Files](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files)
- [Python Documentation – `pathlib` — Object-oriented filesystem paths](https://docs.python.org/3/library/pathlib.html)
- [Python Documentation – `json` — JSON encoder and decoder](https://docs.python.org/3/library/json.html)
- [PEP 519 – Adding a file system path protocol](https://peps.python.org/pep-0519/)

<!-- nav:bottom -->
---

[⬅️ Exceptions](./07-exceptions.md) | [📚 Mục lục Fresher](./README.md) | [OOP & dataclass ➡️](./09-oop-dataclasses.md)
<!-- /nav:bottom -->
