<!-- nav:top -->
[🏠 Home](../README.md) › [Fresher](./README.md) › Bài 07
<!-- /nav:top -->

# Exceptions & Xử lý ngoại lệ

> ⏱️ Thời lượng: ~2.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 06: Module & package](./06-modules-packages.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ cây phân cấp ngoại lệ của Python: Sự khác biệt bản chất giữa `BaseException` và `Exception`, lý do không bao giờ dùng `except:` trần.
- Làm chủ cú pháp đầy đủ của cấu trúc xử lý ngoại lệ: `try`, `except`, `else` và `finally` (đặc biệt là vai trò độc đáo của khối `else`).
- Thành thạo kỹ thuật **Exception Chaining** (`raise ... from e`) tương đương thuộc tính `InnerException` trong C#/.NET để bảo toàn toàn bộ dấu vết lỗi (stack trace).
- Biết cách thiết kế hệ thống **Custom Exceptions** chuẩn mực kế thừa từ `Exception` cho tầng nghiệp vụ (Domain-driven exceptions).
- Nắm bắt tính năng hiện đại **`add_note()`** (Python 3.11+) để đính kèm thông tin ngữ cảnh chẩn đoán vào ngoại lệ mà không làm biến dạng chuỗi thông điệp lỗi gốc.
- Thấu hiểu và áp dụng triệt để triết lý thiết kế mã nguồn **EAFP** (*Easier to ask for forgiveness than permission*) đặc trưng của Python đối trọng với **LBYL** (*Look before you leap*) thường thấy trong C#.

---

## 🔁 So sánh với C# / ASP.NET

Là lập trình viên C#, bạn đã quen thuộc với khối `try-catch-finally`, từ khóa `throw`, và các lớp ngoại lệ bắt nguồn từ `System.Exception`. Trong Python, cơ chế xử lý ngoại lệ có cú pháp tương tự nhưng sở hữu những điểm nhấn tư duy rất khác biệt:

| Khái niệm / Cú pháp | C# / .NET | Python 3.11+ |
|---|---|---|
| **Bắt ngoại lệ** | `catch (ArgumentException ex)` | `except ArgumentException as ex:` |
| **Ném ngoại lệ** | `throw new InvalidOperationException("lỗi");` | `raise InvalidOperationException("lỗi")` |
| **Ném lại ngoại lệ hiện tại** | `throw;` | `raise` (không đối số) |
| **Exception Chaining (lồng ngoại lệ)** | `throw new AppError("msg", innerEx);` (gán vào `InnerException`) | `raise AppError("msg") from inner_ex` (gán vào `__cause__`) |
| **Chặn chuỗi ngoại lệ** | Không có cú pháp trực tiếp | `raise AppError("msg") from None` (ẩn `__context__`) |
| **Khối code chạy khi KHÔNG có lỗi** | Không có từ khóa tương đương (thường phải đặt biến cờ hoặc viết trong cuối `try`) | Khối **`else:`** chạy khi khối `try` kết thúc thành công mỹ mãn |
| **Dọn dẹp tài nguyên** | `finally` block | `finally` block |
| **Gắn ghi chú chẩn đoán** | `ex.Data["Key"] = "Value"` | `ex.add_note("Context details")` (Python 3.11+) |
| **Lớp gốc của mọi lỗi thông thường** | `System.Exception` | `Exception` |
| **Lớp gốc của các tín hiệu hệ thống** | Thường là ngắt luồng ngoài tầm kiểm soát (`ThreadAbortException`) | `BaseException` (cha của `KeyboardInterrupt`, `SystemExit`) |
| **Bộ lọc ngoại lệ (Exception filter)** | `catch (SqlException ex) when (ex.Number == 1205)` | Bắt kiểu lỗi rồi dùng `if` bên trong `except`, hoặc ném lại nếu không thỏa |
| **Triết lý kiểm tra lỗi** | **LBYL**: `if (dict.ContainsKey(k)) { ... }` | **EAFP**: `try: val = dict[k] except KeyError: ...` |

---

## 📖 Lý thuyết

### 1. Cây phân cấp ngoại lệ: `BaseException` vs `Exception`

Trong Python, mọi lỗi và ngoại lệ đều là các class kế thừa từ một gốc chung duy nhất: **`BaseException`**. Tuy nhiên, phân cấp này được chia thành hai nhóm hoàn toàn khác biệt:

```
BaseException
├── SystemExit                  # Được ném khi gọi sys.exit()
├── KeyboardInterrupt           # Ném khi người dùng bấm Ctrl + C trong terminal
├── GeneratorExit               # Ném khi generator bị đóng lại
└── Exception                   # LỚP CHA CỦA MỌI NGOẠI LỆ NGHIỆP VỤ & LỖI RUNTIME
    ├── ArithmeticError
    │   └── ZeroDivisionError
    ├── LookupError
    │   ├── IndexError
    │   └── KeyError
    ├── ValueError
    ├── TypeError
    ├── OSError
    │   ├── FileNotFoundError
    │   └── PermissionError
    └── [Custom Exceptions của bạn]
```

#### Vì sao TUYỆT ĐỐI KHÔNG dùng `except:` trần hay `except BaseException:`?

Khi bạn viết `except:` (bare except) hoặc `except BaseException:`, bạn đang bắt **TẤT CẢ MỌI THỨ**, bao gồm cả:
- **`KeyboardInterrupt`**: Khi bạn hoặc hệ điều hành gửi tín hiệu `SIGINT` (Ctrl+C) để dừng ứng dụng đang treo, khối `except` này sẽ nuốt mất tín hiệu, khiến chương trình trở nên "bất tử" và không thể tắt được từ terminal.
- **`SystemExit`**: Khi ứng dụng chủ động gọi `sys.exit(0)` để dừng tiến trình, câu lệnh này cũng bị chặn đứng lại.

> [!CAUTION]
> **Quy tắc vàng**:
> Luôn bắt cụ thể loại ngoại lệ bạn dự kiến xử lý (ví dụ `except ValueError:`). Nếu bạn muốn bắt toàn bộ các lỗi nghiệp vụ hoặc lỗi chương trình thông thường, lớp rộng nhất bạn được phép dùng là **`except Exception as e:`**.

```python
# SAI LẦM NGUY HIỂM:
try:
    process_background_jobs()
except:  # Nuốt cả Ctrl + C (KeyboardInterrupt) và sys.exit()!
    print("Có lỗi xảy ra!")

# ĐÚNG CHUẨN:
try:
    process_background_jobs()
except Exception as e:
    print(f"Xử lý lỗi runtime: {e}")
```

---

### 2. Cú pháp đầy đủ: `try / except / else / finally`

Một khối xử lý lỗi đầy đủ trong Python bao gồm 4 phần với thứ tự nghiêm ngặt:

```python
try:
    # 1. Khối mã nguy hiểm: Chỉ đặt những dòng có nguy cơ ném ra ngoại lệ dự kiến.
    file = open("config.json", "r", encoding="utf-8")
    data = file.read()
except FileNotFoundError as err:
    # 2. Khối xử lý: Chỉ chạy khi ngoại lệ tương ứng xuất hiện trong `try`.
    print(f"Không tìm thấy file: {err}")
else:
    # 3. Khối thành công: CHỈ chạy khi khối `try` thực thi THÀNH CÔNG (không ném ngoại lệ).
    # Đặt logic tiếp theo ở đây giúp thu hẹp phạm vi khối try, tránh bắt nhầm lỗi.
    print(f"Đọc file thành công! Kích thước: {len(data)} ký tự.")
finally:
    # 4. Khối dọn dẹp: LUÔN LUÔN CHẠY dù có exception hay không, kể cả khi có return/break/continue.
    print("Hoàn tất quy trình đọc dữ liệu.")
```

#### Vai trò tối quan trọng của khối `else:`
Nhiều lập trình viên từ ngôn ngữ khác thường bỏ qua khối `else`. Hãy xem sự khác biệt:

```python
# Không dùng else (Code có mùi - Bad Practice):
try:
    raw_id = input_data["user_id"]
    user = query_user_from_db(raw_id)  # Nếu hàm này ném KeyError, khối except bên dưới sẽ bắt nhầm!
except KeyError:
    print("Dữ liệu đầu vào thiếu trường user_id")

# Dùng else đúng chuẩn (Clean & Safe):
try:
    raw_id = input_data["user_id"]
except KeyError:
    print("Dữ liệu đầu vào thiếu trường user_id")
else:
    # Chỉ thực hiện logic này khi việc lấy key thành công!
    user = query_user_from_db(raw_id)
```

---

### 3. Exception Chaining: `raise ... from e` (↔ `InnerException`)

Khi xây dựng các tầng dịch vụ (Service Layer, Repository), bạn thường muốn bắt các lỗi cấp thấp (như `sqlite3.OperationalError` hay `json.JSONDecodeError`) và biến đổi thành một ngoại lệ nghiệp vụ cấp cao hơn (như `DatabaseConnectionError` hay `ConfigParseError`).

Nếu bạn chỉ viết:
```python
try:
    load_json()
except json.JSONDecodeError as err:
    raise ConfigParseError("Không thể đọc file cấu hình")  # Mất ngữ cảnh lỗi gốc!
```
Python hỗ trợ cú pháp tường minh **`raise NewException from original_exception`** (PEP 3134):

```python
try:
    load_json()
except json.JSONDecodeError as err:
    # Biến 'err' sẽ được gán vào thuộc tính __cause__ của ConfigParseError
    raise ConfigParseError("Không thể nạp cấu hình hệ thống") from err
```

Khi in traceback ra terminal, Python sẽ hiển thị:
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  ...
ConfigParseError: Không thể nạp cấu hình hệ thống
```

Nếu bạn muốn triệt tiêu hoàn toàn traceback của lỗi gốc (ví dụ để bảo mật, không để lộ cấu trúc bên dưới), hãy dùng `from None`:
```python
try:
    task = tasks[task_id]
except KeyError:
    # Ẩn hoàn toàn thông tin chi tiết của KeyError
    raise TaskNotFoundError(f"Không tìm thấy task với ID: {task_id}") from None
```

---

### 4. Thiết kế Custom Exceptions chuẩn mực

Để mã nguồn rõ ràng và dễ bảo trì, hãy định nghĩa một hệ thống ngoại lệ có phân tầng cho dự án của bạn bằng cách kế thừa từ class `Exception`:

```python
class TaskFlowError(Exception):
    """Ngoại lệ gốc của toàn bộ dự án TaskFlow."""
    pass


class TaskNotFoundError(TaskFlowError):
    """Ném ra khi không tìm thấy công việc theo mã định danh."""
    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Công việc với mã ID={task_id} không tồn tại.")


class TaskValidationError(TaskFlowError):
    """Ném ra khi dữ liệu đầu vào của task không hợp lệ."""
    def __init__(self, field_name: str, message: str) -> None:
        self.field_name = field_name
        self.message = message
        super().__init__(f"Lỗi kiểm tra tính hợp lệ tại trường '{field_name}': {message}")
```

Lợi ích: Tầng trên có thể bắt gọn toàn bộ lỗi của hệ thống qua lớp cha `except TaskFlowError:`, hoặc bắt riêng từng trường hợp đặc thù như `except TaskNotFoundError:`.

---

### 5. Tính năng `add_note()` (Python 3.11+)

Trước Python 3.11, nếu bạn muốn bổ sung thông tin vào exception mà không muốn ném exception mới, bạn buộc phải sửa chuỗi thông báo ban đầu. Python 3.11 giới thiệu phương thức **`add_note(note_str)`** (PEP 678), cho phép đính kèm nhiều dòng ghi chú vào một instance ngoại lệ:

```python
def fetch_remote_task(task_id: int, api_url: str) -> None:
    try:
        # Giả lập lỗi kết nối mạng
        raise ConnectionResetError("Mạng bị ngắt đột ngột bởi máy chủ từ xa")
    except ConnectionResetError as err:
        # Bổ sung thông tin ngữ cảnh chẩn đoán (request id, timestamp, url)
        err.add_note(f"API Endpoint: {api_url}")
        err.add_note(f"Target Task ID: {task_id}")
        err.add_note("Gợi ý: Kiểm tra lại VPN hoặc proxy máy chủ.")
        raise
```

Các dòng ghi chú này sẽ hiển thị trang trọng ngay dưới traceback khi ứng dụng ghi log hoặc in lỗi ra console.

---

### 6. Tư duy EAFP vs LBYL trong Python

Một khác biệt kinh điển giữa các lập trình viên C# và Python là cách tiếp cận với các tình huống có thể phát sinh lỗi:

- **LBYL (Look Before You Leap)**: Kiểm tra điều kiện cẩn thận trước khi thực hiện hành động.
- **EAFP (Easier to Ask for Forgiveness than Permission)**: Cứ thử thực hiện hành động, nếu thất bại thì bắt ngoại lệ xử lý.

```python
# Phong cách LBYL (Thường gặp trong C#):
if key in my_dict:
    value = my_dict[key]
else:
    value = default_value

# Phong cách EAFP (Chuẩn Pythonic):
try:
    value = my_dict[key]
except KeyError:
    value = default_value
```

**Tại sao Python chuộng EAFP?**
1. **Hiệu năng**: Khối `try/except` trong Python hiện đại gần như có chi phí bằng 0 ("zero-cost exceptions" khi không có lỗi xảy ra). Nếu key thường xuyên tồn tại, EAFP chạy nhanh hơn vì không mất 2 lần tra cứu bảng băm (`key in dict` rồi lại `dict[key]`).
2. **Tránh lỗi tranh chấp (Race Condition / TOCTOU)**: Trong hệ thống đa tiến trình hoặc File I/O:
   - Với LBYL: Bạn kiểm tra `if os.path.exists(file_path):`, sau đó gọi `open(file_path)`. Ngay giữa hai thao tác này, một tiến trình khác có thể đã xóa file đó!
   - Với EAFP: Bạn gọi trực tiếp `open(file_path)` trong `try...except FileNotFoundError:`. Luồng mã an toàn tuyệt đối trước xung đột.

---

## 💻 Ví dụ thực hành

Dưới đây là module quản lý dịch vụ tác vụ `task_service.py` minh họa đầy đủ các nguyên tắc trên:

```python
from datetime import datetime
from typing import Any


class TaskFlowError(Exception):
    """Exception cơ sở của dịch vụ TaskFlow."""


class TaskNotFoundError(TaskFlowError):
    """Lỗi không tìm thấy Task."""
    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Không tìm thấy công việc mang ID={task_id}")


class TaskValidationError(TaskFlowError):
    """Lỗi dữ liệu đầu vào của Task không hợp lệ."""


class TaskService:
    def __init__(self) -> None:
        self._database: dict[int, dict[str, Any]] = {}
        self._next_id: int = 1

    def create_task(self, title: str, priority: str = "MEDIUM") -> dict[str, Any]:
        """Tạo task mới với dữ liệu đã kiểm tra."""
        clean_title = title.strip()
        if not clean_title:
            raise TaskValidationError("Tiêu đề công việc không được để trống!")

        valid_priorities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        clean_priority = priority.upper()
        if clean_priority not in valid_priorities:
            raise TaskValidationError(
                f"Độ ưu tiên '{priority}' không hợp lệ. Cho phép: {valid_priorities}"
            )

        task_id = self._next_id
        self._next_id += 1

        record = {
            "id": task_id,
            "title": clean_title,
            "priority": clean_priority,
            "status": "TODO",
            "created_at": datetime.now().isoformat(),
        }
        self._database[task_id] = record
        return record

    def get_task(self, task_id: int) -> dict[str, Any]:
        """Lấy task bằng tư duy EAFP."""
        try:
            return self._database[task_id]
        except KeyError as err:
            # Exception Chaining: Bọc KeyError cấp thấp thành TaskNotFoundError cấp cao
            custom_err = TaskNotFoundError(task_id)
            custom_err.add_note(f"Truy vấn vào lúc: {datetime.now().isoformat()}")
            raise custom_err from err


def run_demo() -> None:
    service = TaskService()

    # 1. Thao tác hợp lệ
    try:
        t1 = service.create_task("Viết tài liệu hướng dẫn Exception", "HIGH")
        print(f"✅ Đã tạo task thành công: ID={t1['id']}, Title='{t1['title']}'")
    except TaskValidationError as e:
        print(f"❌ Lỗi dữ liệu: {e}")

    # 2. Thao tác gây lỗi validation
    try:
        service.create_task("   ", "SUPER_URGENT")
    except TaskValidationError as e:
        print(f"⚠️ Bắt lỗi hợp lệ: {e}")

    # 3. Thao tác tìm kiếm task không tồn tại (Minh họa Exception Chaining và add_note)
    try:
        service.get_task(999)
    except TaskNotFoundError as e:
        print(f"⚠️ Bắt lỗi TaskNotFoundError: {e}")
        if hasattr(e, "__notes__"):
            print(f"   Ghi chú đính kèm: {e.__notes__}")


if __name__ == "__main__":
    run_demo()
```

---

## ⚠️ Lỗi thường gặp

### 1. Bắt ngoại lệ bằng `except:` trần hoặc `except BaseException:`
- **Hậu quả**: Khiến ứng dụng không thể ngắt bằng tổ hợp phím `Ctrl + C` và nuốt luôn lệnh thoát tiến trình `sys.exit()`.
- **Cách khắc phục**: Chỉ bắt ngoại lệ cụ thể, hoặc tối đa là `except Exception:`.

### 2. Nuốt ngoại lệ âm thầm (`except Exception: pass`)
- **Hậu quả**: Ẩn giấu mọi lỗi logic, khiến chương trình chạy sai kết quả hoặc rơi vào trạng thái dữ liệu rác mà không ai biết nguồn cơn.
- **Cách khắc phục**: Luôn ghi log (hoặc in thông tin) tối thiểu bằng `logging.exception("Thông báo lỗi")`.

### 3. Ném lại ngoại lệ sai cách làm mất Traceback
- **Lỗi**:
  ```python
  try:
      do_something()
  except ValueError as e:
      raise e  # SAI! CPython coi đây là một điểm ném mới, làm biến dạng vị trí dòng gây lỗi ban đầu!
  ```
- **Cách khắc phục**: Dùng từ khóa `raise` độc lập để re-raise nguyên vẹn:
  ```python
  try:
      do_something()
  except ValueError:
      logger.warning("Đã ghi nhận ValueError, đang ném tiếp...")
      raise  # ĐÚNG CHUẨN! Bảo toàn 100% stack trace ban đầu.
  ```

### 4. Đặt quá nhiều dòng mã vào trong khối `try`
- **Hậu quả**: Nếu khối `try` dài 50 dòng chứa đủ loại logic, một lỗi `KeyError` phát sinh ngẫu nhiên từ thư viện phụ có thể bị khối `except KeyError:` bắt nhầm, dẫn đến chuẩn đoán sai lệch.
- **Cách khắc phục**: Thu gọn khối `try` về đúng dòng mã có nguy cơ. Chuyển toàn bộ các bước xử lý dữ liệu tiếp theo sang khối `else:`.

---

## ✍️ Bài tập thực hành

### Bài 1: Xây dựng hệ thống Exception nghiệp vụ cho ứng dụng Task Manager
Thiết kế hệ thống phân cấp ngoại lệ cho module quản lý tác vụ:
1. Tạo class gốc `TaskManagerError(Exception)`.
2. Tạo 3 class con kế thừa:
   - `TaskNotFoundError`: Nhận vào `task_id`, thông báo mã task không tồn tại.
   - `TaskStatusTransitionError`: Nhận vào `current_status` và `new_status`, ném ra khi cố tình chuyển trạng thái không hợp lệ (ví dụ từ `DONE` quay về `TODO`).
   - `TaskStorageError`: Ném ra khi gặp lỗi đọc/ghi dữ liệu ở tầng lưu trữ.
3. Viết hàm `transition_task_status(current_status: str, new_status: str)` kiểm tra: Chỉ cho phép chuyển từ `TODO` sang `IN_PROGRESS`, và từ `IN_PROGRESS` sang `DONE`. Mọi trường hợp khác đều ném `TaskStatusTransitionError`.

<details>
<summary>💡 Gợi ý</summary>

```python
class TaskManagerError(Exception):
    """Gốc ngoại lệ cho Task Manager."""


class TaskNotFoundError(TaskManagerError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"Không tìm thấy công việc mã {task_id}")


class TaskStatusTransitionError(TaskManagerError):
    def __init__(self, current_status: str, new_status: str) -> None:
        super().__init__(
            f"Không thể chuyển đổi trạng thái từ '{current_status}' sang '{new_status}'."
        )


def transition_task_status(current_status: str, new_status: str) -> str:
    valid_transitions = {
        "TODO": {"IN_PROGRESS"},
        "IN_PROGRESS": {"DONE"},
    }
    allowed = valid_transitions.get(current_status, set())
    if new_status not in allowed:
        raise TaskStatusTransitionError(current_status, new_status)
    return new_status
```
</details>

---

### Bài 2: Triển khai hàm chuyển đổi chuỗi sang số an toàn theo triết lý EAFP
Viết hàm `safe_parse_int(value: str, default: int = 0) -> int`:
1. Sử dụng triết lý EAFP với cấu trúc `try...except ValueError`.
2. Trả về số nguyên tương ứng nếu parse thành công.
3. Nếu người dùng truyền vào chuỗi không hợp lệ (ví dụ `"abc"`, `"12.34"`), bắt lỗi và trả về giá trị `default`.
4. Không dùng hàm `str.isdigit()` (vì `isdigit()` sẽ thất bại với số nguyên âm như `"-15"`).

<details>
<summary>💡 Gợi ý</summary>

```python
def safe_parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default
```
</details>

---

### Bài 3: Bọc lỗi cấu hình với Exception Chaining và `add_note()`
Viết hàm `parse_task_config(raw_json: str) -> dict[str, str]`:
1. Gọi `json.loads(raw_json)`.
2. Nếu gặp lỗi `json.JSONDecodeError`:
   - Bắt lỗi và ném ra ngoại lệ tự định nghĩa `ConfigCorruptedError("Dữ liệu JSON cấu hình bị hỏng")`.
   - Sử dụng cú pháp `raise ... from err` để giữ lại dấu vết của `JSONDecodeError`.
   - Sử dụng phương thức `add_note(...)` để gắn thêm thông tin chuỗi gốc bị lỗi và độ dài chuỗi trước khi ném.

<details>
<summary>💡 Gợi ý</summary>

```python
import json


class ConfigCorruptedError(Exception):
    """Ngoại lệ khi chuỗi cấu hình bị hỏng."""


def parse_task_config(raw_json: str) -> dict[str, str]:
    try:
        data = json.loads(raw_json)
        if not isinstance(data, dict):
            raise TypeError("Nội dung JSON phải là một Object / Dict.")
        return data
    except (json.JSONDecodeError, TypeError) as err:
        ex = ConfigCorruptedError("Dữ liệu JSON cấu hình không hợp lệ!")
        ex.add_note(f"Kích thước chuỗi đầu vào: {len(raw_json)} ký tự")
        ex.add_note(f"Đoạn trích chuỗi: {raw_json[:50]!r}")
        raise ex from err
```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn giải thích được vì sao cây phân cấp tách biệt `BaseException` và `Exception`, và vì sao không được dùng bare except `except:`?
- [ ] Bạn hiểu rõ thứ tự và vai trò của cả 4 khối: `try`, `except`, `else`, `finally`?
- [ ] Bạn biết cách dùng `raise ... from e` để chain exception tương đương `InnerException` trong C#?
- [ ] Bạn biết cách tạo lớp Custom Exception kế thừa `Exception` cho tầng domain/service?
- [ ] Bạn hiểu cách dùng `add_note()` trong Python 3.11+ để đính kèm metadata chẩn đoán lỗi?
- [ ] Bạn phân biệt được sự khác nhau giữa triết lý EAFP và LBYL, và biết khi nào nên áp dụng EAFP?

---

## 📚 Đọc thêm

- [Python Documentation – Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)
- [Python Documentation – Built-in Exceptions Hierarchy](https://docs.python.org/3/library/exceptions.html#exception-hierarchy)
- [PEP 3134 – Exception Chaining and Embedded Tracebacks](https://peps.python.org/pep-3134/)
- [PEP 678 – Enriching Exceptions with Notes](https://peps.python.org/pep-0678/)

<!-- nav:bottom -->
---

[⬅️ Module & package](./06-modules-packages.md) | [📚 Mục lục Fresher](./README.md) | [File I/O & JSON ➡️](./08-file-io-json.md)
<!-- /nav:bottom -->
