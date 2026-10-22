<!-- nav:top -->
[🏠 Home](../README.md) › [Dự án TaskFlow](./README.md) › M0
<!-- /nav:top -->

# M0 – CLI Task Manager

> ⏱️ Thời lượng ước tính: 4–6 giờ thực hành độc lập · 📌 Yêu cầu trước: Hoàn thành toàn bộ [Level 01: Fresher](../01-fresher/README.md) (Bài 01 đến Bài 11).

---

## 📌 Bối cảnh

Chào mừng bạn đến với **Milestone M0: CLI Task Manager** – cột mốc thực hành đầu tiên và là viên gạch nền móng cho dự án xuyên suốt hành trình **TaskFlow** (từ Fresher đến Senior).

Trong thế giới phát triển phần mềm hiện đại, trước khi bắt tay vào xây dựng các hệ thống phân tán hay REST API phức tạp, việc nắm vững cách tổ chức mã nguồn trong sáng (clean code), mô hình hóa miền nghiệp vụ (domain modeling), phân tách trách nhiệm giữa các tầng (separation of concerns), và xử lý lưu trữ bền vững (persistence) là năng lực cốt lõi phân biệt một kỹ sư phần mềm thực thụ.

Mục tiêu của Milestone M0 là xây dựng một công cụ dòng lệnh (CLI Tool) bằng **Python 3.12+ thuần túy** (chỉ dùng Standard Library: `argparse`, `dataclasses`, `json`, `pathlib`, `enum`, `datetime`), quản lý công việc cá nhân và lưu trữ dữ liệu an toàn vào file `tasks.json`. 

Mã nguồn bạn xây dựng tại đây sẽ được kế thừa và chuyển đổi thành REST API với FastAPI trong Milestone M1 (Junior)!

---

## 🎯 Yêu cầu chức năng

Ứng dụng CLI TaskFlow M0 phải hỗ trợ các lệnh tương tác chính sau từ terminal:

### 1. Thêm công việc mới (`add`)
- Cho phép tạo một task mới với tiêu đề bắt buộc và các thuộc tính tùy chọn:
  ```bash
  python -m taskflow add --title "Hoàn thiện báo cáo quý" --priority HIGH --due 2026-10-30
  ```
- **Tham số**:
  - `--title` (bắt buộc): Chuỗi ký tự không được để trống.
  - `--priority` (tùy chọn, mặc định `MEDIUM`): Một trong ba mức `LOW`, `MEDIUM`, `HIGH`.
  - `--due` (tùy chọn): Định dạng ngày `YYYY-MM-DD`.
- **Đầu ra**: In thông báo thành công kèm ID được cấp phát (ví dụ: `[ID: 1] Đã tạo công việc thành công!`).

### 2. Liệt kê công việc (`list`)
- Hiển thị danh sách công việc dưới dạng bảng hoặc danh sách trực quan có căn lề:
  ```bash
  python -m taskflow list
  python -m taskflow list --status TODO --priority HIGH
  ```
- **Bộ lọc**:
  - `--status`: Lọc theo trạng thái `TODO`, `IN_PROGRESS`, hoặc `DONE`.
  - `--priority`: Lọc theo độ ưu tiên `LOW`, `MEDIUM`, hoặc `HIGH`.
- **Thông tin hiển thị**: Cột `ID`, `Trạng thái`, `Ưu tiên`, `Tiêu đề`, `Hạn chót`.

### 3. Cập nhật trạng thái công việc (`update`)
- Chuyển đổi trạng thái của task theo ID:
  ```bash
  python -m taskflow update 1 --status IN_PROGRESS
  python -m taskflow update 1 --status DONE
  ```
- **Quy tắc**: Nếu ID không tồn tại trong hệ thống, thông báo lỗi rõ ràng và trả về mã lỗi (`exit code != 0`).

### 4. Xóa công việc (`delete`)
- Xóa vĩnh viễn một task khỏi hệ thống:
  ```bash
  python -m taskflow delete 1
  ```
- **Đầu ra**: Xác nhận xóa thành công hoặc cảnh báo nếu ID không tồn tại.

### 5. Lưu trữ bền vững (Persistence)
- Mọi dữ liệu tạo mới, cập nhật, hoặc xóa phải được đồng bộ ngay lập tức vào file `data/tasks.json`.
- Khi ứng dụng khởi động lại, toàn bộ dữ liệu trước đó phải được nạp đầy đủ và chính xác.

---

## 🛠️ Yêu cầu kỹ thuật

Để đạt chuẩn chất lượng sản phẩm mẫu, mã nguồn phải tuân thủ nghiêm ngặt các tiêu chuẩn sau:

1. **Chuẩn Type Hints 100%**:
   - Mọi hàm, phương thức, và thuộc tính phải có Type Annotations đầy đủ theo chuẩn Python 3.10+ (`str | None`, `list[Task]`, `dict[str, object]`).
   - Tuyệt đối không dùng `Any` trừ trường hợp ngoại lệ bất khả kháng có ghi chú giải thích.
2. **Domain Modeling với `@dataclass`**:
   - Sử dụng `@dataclass(slots=True, frozen=True)` cho class `Task`.
   - Sử dụng `StrEnum` cho `TaskStatus` và `TaskPriority`.
3. **Phân tách trách nhiệm (Clean Separation)**:
   - `models.py`: Khai báo Enum và Data Class nghiệp vụ.
   - `exceptions.py`: Định nghĩa hệ thống ngoại lệ phân tầng (`TaskFlowError`, `TaskNotFoundError`, `TaskValidationError`).
   - `storage.py`: Xử lý đọc/ghi file `pathlib.Path` và `json` an toàn (`encoding="utf-8"`, `ensure_ascii=False`, `indent=2`).
   - `service.py`: Tầng nghiệp vụ xử lý logic (tính ID, validate, filter danh sách).
   - `cli.py`: Tầng giao diện người dùng, phân tích tham số bằng `argparse`.
4. **Xử lý File I/O & Ngoại lệ bền bỉ**:
   - Sử dụng context manager `with open(..., encoding="utf-8")`.
   - Bắt các lỗi file hỏng (`JSONDecodeError`) và bọc bằng custom exception với `raise ... from err`.
5. **Code Style & Tooling**:
   - Định dạng bằng `ruff format .`.
   - Kiểm tra sạch 100% lỗi bằng `ruff check .` với các rule `["E", "W", "F", "I", "B", "UP"]`.

---

## 📁 Gợi ý cấu trúc thư mục

Một cấu trúc thư mục dự án chuẩn mực cho Milestone M0:

```text
taskflow-m0/
├── pyproject.toml              # Cấu hình dự án & bộ rule của Ruff
├── README.md                   # Hướng dẫn cài đặt và sử dụng CLI
├── data/
│   └── tasks.json              # File cơ sở dữ liệu JSON cục bộ
└── taskflow/
    ├── __init__.py             # Đóng gói package và định nghĩa __all__
    ├── __main__.py             # Entry point khi chạy: python -m taskflow
    ├── models.py               # Data class Task, Enum TaskStatus, TaskPriority
    ├── exceptions.py           # Domain exceptions
    ├── storage.py              # JsonTaskStorage xử lý đọc/ghi Path
    ├── service.py              # TaskService chứa toàn bộ Business Logic
    └── cli.py                  # CLI Parser với argparse & định dạng console
```

---

## 💡 Gợi ý triển khai

<details>
<summary>💡 Gợi ý triển khai từng bước chi tiết (Nhấp để mở)</summary>

### Bước 1: Khai báo models (`taskflow/models.py`)

```python
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Self


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@dataclass(slots=True, frozen=True)
class Task:
    id: int
    title: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def with_status(self, new_status: TaskStatus) -> Self:
        return Task(
            id=self.id,
            title=self.title,
            priority=self.priority,
            status=new_status,
            due_date=self.due_date,
            created_at=self.created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            priority=TaskPriority(data.get("priority", TaskPriority.MEDIUM)),
            status=TaskStatus(data.get("status", TaskStatus.TODO)),
            due_date=data.get("due_date"),
            created_at=str(data["created_at"]),
        )
```

---

### Bước 2: Định nghĩa Custom Exceptions (`taskflow/exceptions.py`)

```python
class TaskFlowError(Exception):
    """Ngoại lệ gốc của dự án TaskFlow."""


class TaskNotFoundError(TaskFlowError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"Không tìm thấy công việc mang ID = {task_id}")


class TaskValidationError(TaskFlowError):
    """Lỗi tính hợp lệ của dữ liệu đầu vào."""


class TaskStorageError(TaskFlowError):
    """Lỗi tầng đọc/ghi file lưu trữ."""
```

---

### Bước 3: Triển khai tầng lưu trữ JSON (`taskflow/storage.py`)

```python
from pathlib import Path
from typing import Any
import json

from taskflow.exceptions import TaskStorageError


class JsonTaskStorage:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []

        try:
            content = self.file_path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            data = json.loads(content)
            if not isinstance(data, list):
                raise TaskStorageError("Dữ liệu JSON trong file phải là một danh sách.")
            return data
        except (json.JSONDecodeError, OSError) as err:
            raise TaskStorageError(f"Lỗi khi đọc file '{self.file_path}': {err}") from err

    def write_all(self, raw_tasks: list[dict[str, Any]]) -> None:
        temp_file = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file, mode="w", encoding="utf-8") as f:
                json.dump(raw_tasks, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.file_path)
        except OSError as err:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            raise TaskStorageError(f"Lỗi khi lưu dữ liệu vào '{self.file_path}': {err}") from err
```

---

### Bước 4: Triển khai Service Layer (`taskflow/service.py`)

```python
from taskflow.exceptions import TaskNotFoundError, TaskValidationError
from taskflow.models import Task, TaskPriority, TaskStatus
from taskflow.storage import JsonTaskStorage


class TaskService:
    def __init__(self, storage: JsonTaskStorage) -> None:
        self.storage = storage
        self._tasks: list[Task] = []
        self._load()

    def _load(self) -> None:
        raw_list = self.storage.read_all()
        self._tasks = [Task.from_dict(item) for item in raw_list]

    def _save(self) -> None:
        raw_list = [t.to_dict() for t in self._tasks]
        self.storage.write_all(raw_list)

    def add_task(
        self,
        title: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: str | None = None,
    ) -> Task:
        clean_title = title.strip()
        if not clean_title:
            raise TaskValidationError("Tiêu đề công việc không được để trống!")

        next_id = max((t.id for t in self._tasks), default=0) + 1
        new_task = Task(
            id=next_id,
            title=clean_title,
            priority=priority,
            status=TaskStatus.TODO,
            due_date=due_date,
        )
        self._tasks.append(new_task)
        self._save()
        return new_task

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task]:
        results = self._tasks
        if status is not None:
            results = [t for t in results if t.status == status]
        if priority is not None:
            results = [t for t in results if t.priority == priority]
        return results

    def update_status(self, task_id: int, new_status: TaskStatus) -> Task:
        for idx, t in enumerate(self._tasks):
            if t.id == task_id:
                updated = t.with_status(new_status)
                self._tasks[idx] = updated
                self._save()
                return updated
        raise TaskNotFoundError(task_id)

    def delete_task(self, task_id: int) -> None:
        initial_len = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.id != task_id]
        if len(self._tasks) == initial_len:
            raise TaskNotFoundError(task_id)
        self._save()
```

---

### Bước 5: Giao diện CLI với `argparse` (`taskflow/cli.py`)

```python
from pathlib import Path
import argparse
import sys

from taskflow.exceptions import TaskFlowError
from taskflow.models import TaskPriority, TaskStatus
from taskflow.service import TaskService
from taskflow.storage import JsonTaskStorage


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taskflow",
        description="TaskFlow CLI - Quản lý công việc cá nhân thông minh",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: add
    add_parser = subparsers.add_parser("add", help="Thêm công việc mới")
    add_parser.add_argument("--title", required=True, help="Tiêu đề công việc")
    add_parser.add_argument(
        "--priority",
        choices=[p.value for p in TaskPriority],
        default=TaskPriority.MEDIUM.value,
        help="Độ ưu tiên (LOW, MEDIUM, HIGH)",
    )
    add_parser.add_argument("--due", help="Hạn chót (YYYY-MM-DD)")

    # Sub-command: list
    list_parser = subparsers.add_parser("list", help="Liệt kê danh sách công việc")
    list_parser.add_argument(
        "--status",
        choices=[s.value for s in TaskStatus],
        help="Lọc theo trạng thái",
    )
    list_parser.add_argument(
        "--priority",
        choices=[p.value for p in TaskPriority],
        help="Lọc theo độ ưu tiên",
    )

    # Sub-command: update
    update_parser = subparsers.add_parser("update", help="Cập nhật trạng thái công việc")
    update_parser.add_argument("id", type=int, help="Mã ID của công việc")
    update_parser.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in TaskStatus],
        help="Trạng thái mới",
    )

    # Sub-command: delete
    delete_parser = subparsers.add_parser("delete", help="Xóa công việc")
    delete_parser.add_argument("id", type=int, help="Mã ID của công việc cần xóa")

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    db_path = Path("data/tasks.json")
    service = TaskService(JsonTaskStorage(db_path))

    try:
        if args.command == "add":
            task = service.add_task(
                title=args.title,
                priority=TaskPriority(args.priority),
                due_date=args.due,
            )
            print(f"✅ Đã thêm công việc [#{task.id}]: '{task.title}'")

        elif args.command == "list":
            status_filter = TaskStatus(args.status) if args.status else None
            prio_filter = TaskPriority(args.priority) if args.priority else None
            tasks = service.list_tasks(status=status_filter, priority=prio_filter)

            if not tasks:
                print("📭 Danh sách công việc đang trống.")
                return 0

            print(f"{'ID':<4} {'Trạng thái':<13} {'Ưu tiên':<10} {'Hạn chót':<12} {'Tiêu đề'}")
            print("-" * 65)
            for t in tasks:
                due = t.due_date or "—"
                print(f"{t.id:<4} {t.status:<13} {t.priority:<10} {due:<12} {t.title}")

        elif args.command == "update":
            updated = service.update_status(args.id, TaskStatus(args.status))
            print(f"🔄 Đã cập nhật task [#{updated.id}] sang trạng thái: {updated.status}")

        elif args.command == "delete":
            service.delete_task(args.id)
            print(f"🗑️ Đã xóa vĩnh viễn task [#{args.id}]")

        return 0

    except TaskFlowError as err:
        print(f"❌ Lỗi nghiệp vụ: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"💥 Lỗi hệ thống ngoài dự kiến: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

---

### Bước 6: File thực thi điểm vào (`taskflow/__main__.py`)

```python
import sys
from taskflow.cli import main

if __name__ == "__main__":
    sys.exit(main())
```
</details>

---

## ✅ Definition of Done

Dự án Milestone M0 của bạn được coi là hoàn thành xuất sắc khi vượt qua toàn bộ các tiêu chí nghiệm thu sau:

- [ ] Lệnh `python -m taskflow add --title "..."` tạo task mới thành công và sinh mã ID tự tăng.
- [ ] Lệnh `python -m taskflow list` hiển thị đầy đủ thông tin dạng bảng căn hàng thẳng lối.
- [ ] Lệnh `python -m taskflow list --status ... --priority ...` lọc kết quả chính xác theo cả 2 tiêu chí.
- [ ] Lệnh `python -m taskflow update <id> --status ...` chuyển trạng thái và lưu ngay lập tức.
- [ ] Lệnh `python -m taskflow delete <id>` xóa đúng task và báo lỗi khi xóa ID không tồn tại.
- [ ] File dữ liệu `data/tasks.json` lưu đúng định dạng UTF-8, có thụt dòng `indent=2`, bảo toàn tiếng Việt (`ensure_ascii=False`).
- [ ] Đạt 100% Type Hints trên toàn bộ các file `.py` trong package.
- [ ] Toàn bộ model chính được cài đặt bằng `@dataclass(slots=True, frozen=True)` và `StrEnum`.
- [ ] Kiểm tra linter bằng lệnh `uv run ruff check .` và formatter `uv run ruff format --check .` báo không có bất kỳ lỗi nào (`0 errors`).

---

## 🚀 Thử thách thêm

Nếu bạn đã hoàn thành xong các yêu cầu bắt buộc trên và muốn nâng tầm kỹ năng lập trình Python, hãy thử sức với các tính năng nâng cao sau:

1. **Tìm kiếm theo từ khóa (`search`)**:
   - Bổ sung lệnh: `python -m taskflow search <từ khóa>`.
   - Tìm kiếm không phân biệt chữ hoa/thường (case-insensitive) trong tiêu đề task.
2. **Cảnh báo công việc quá hạn (`overdue`)**:
   - Bổ sung lệnh: `python -m taskflow overdue`.
   - So sánh `due_date` với ngày hiện tại (`date.today()`), lọc ra các task có `status != DONE` và `due_date < today`.
3. **Xuất báo cáo định dạng Markdown (`export`)**:
   - Bổ sung lệnh: `python -m taskflow export --format md --output report.md`.
   - Tạo file Markdown có chứa bảng danh sách công việc cùng biểu đồ tóm tắt tỷ lệ hoàn thành (Task Completion Rate).

<!-- nav:bottom -->
---

[⬅️ Công cụ: ruff & debugging](../01-fresher/11-tooling-ruff-debugging.md) | [📚 Dự án TaskFlow](./README.md) | [Junior ➡️](../02-junior/README.md)
<!-- /nav:bottom -->
