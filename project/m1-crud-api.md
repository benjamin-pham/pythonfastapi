<!-- nav:top -->
[🏠 Home](../README.md) › [Dự án TaskFlow](./README.md) › M1
<!-- /nav:top -->

# M1 – CRUD API

> ⏱️ Thời lượng ước tính: 6–8 giờ thực hành độc lập · 📌 Yêu cầu trước: Hoàn thành toàn bộ [Level 02: Junior](../02-junior/README.md) (Bài 01 đến Bài 09).

---

## 🎯 Bối cảnh

Chào mừng bạn đến với **Milestone M1: RESTful CRUD API** – cột mốc thực hành chuyển đổi chiến lược của dự án xuyên suốt **TaskFlow**.

Trong [Milestone M0: CLI Task Manager](./m0-cli-task-manager.md), bạn đã xây dựng thành công một công cụ dòng lệnh bằng Python thuần túy với thư viện chuẩn (`argparse`, `@dataclass`, `json`). Tuy nhiên, trong môi trường doanh nghiệp thực tế, các hệ thống phần mềm hiện đại đòi hỏi khả năng phục vụ đa người dùng đồng thời, cung cấp giao diện lập trình ứng dụng (API) cho Web frontend (React/Vue/Next.js), Mobile app (Flutter/Swift), và tích hợp giữa các microservices.

Mục tiêu của **Milestone M1** là nâng cấp toàn diện TaskFlow từ ứng dụng CLI cục bộ thành một dịch vụ Web **RESTful CRUD API** chuẩn production, vận hành trên nền tảng **FastAPI**, **Pydantic v2**, và máy chủ **Uvicorn**:
- **Mở rộng mô hình nghiệp vụ**: Không chỉ quản lý công việc đơn lẻ, TaskFlow M1 bổ sung thêm tài nguyên **Dự án (`Project`)** có quan hệ 1-Nhiều với **Công việc (`Task`)**.
- **Kiến trúc phân tầng sạch (Clean Layered Architecture)**: Phân tách rạch ròi giữa Tầng định tuyến (Routers), Hợp đồng dữ liệu (Schemas/DTOs), Nghiệp vụ (Services), và Lưu trữ (Repositories).
- **Làm chủ Dependency Injection**: Mọi thành phần phụ thuộc đều được tiêm thông qua cơ chế `Depends` và `Annotated`.
- **Chuẩn hóa lỗi quốc tế**: 100% phản hồi lỗi tuân thủ đặc tả **RFC 9457 Problem Details**.
- **Kiểm thử tự động toàn diện**: Xây dựng test suite với `pytest` và `TestClient`, bao phủ toàn bộ các kịch bản thành công và ngoại lệ.

Mã nguồn bạn hoàn thiện trong M1 sẽ là nền móng trực tiếp để tích hợp Cơ sở dữ liệu quan hệ PostgreSQL với SQLAlchemy ORM, Alembic migrations, và JWT Authentication trong [Milestone M2 (Middle)](./m2-production-api.md)!

---

## 📋 Yêu cầu chức năng

Hệ thống TaskFlow API M1 quản lý hai tài nguyên chính: **`Project`** và **`Task`**.

### 1. Quản lý Dự án (`/api/v1/projects`)

| Method | Endpoint | Mô tả | Mã HTTP Thành công | Mã Lỗi Tiêu biểu |
|---|---|---|:---:|:---:|
| `POST` | `/api/v1/projects` | Tạo dự án mới | `201 Created` | `400`, `409 Conflict`, `422` |
| `GET` | `/api/v1/projects` | Lấy danh sách tất cả các dự án (kèm tổng số tasks) | `200 OK` | `500` |
| `GET` | `/api/v1/projects/{project_id}` | Lấy thông tin chi tiết một dự án theo ID | `200 OK` | `404 Not Found` |
| `DELETE` | `/api/v1/projects/{project_id}` | Xóa dự án (và xóa liên hoàn các task thuộc dự án đó) | `204 No Content` | `404 Not Found` |

- **Quy tắc nghiệp vụ Dự án**:
  - `name`: Bắt buộc, độ dài từ 3 đến 50 ký tự, không được trùng lặp với các dự án đã có (nếu trùng trả về `409 Conflict`).
  - `description`: Tùy chọn, tối đa 255 ký tự.
  - Khi xóa một `Project`, toàn bộ các `Task` thuộc về dự án đó phải được tự động dọn dẹp sạch sẽ (Cascade Delete in-memory).

### 2. Quản lý Công việc (`/api/v1/tasks`)

| Method | Endpoint | Mô tả | Mã HTTP Thành công | Mã Lỗi Tiêu biểu |
|---|---|---|:---:|:---:|
| `POST` | `/api/v1/tasks` | Tạo task mới thuộc một project | `201 Created` | `404 Not Found`, `422` |
| `GET` | `/api/v1/tasks` | Lấy danh sách tasks có hỗ trợ lọc và phân trang | `200 OK` | `422` |
| `GET` | `/api/v1/tasks/{task_id}` | Lấy thông tin chi tiết một task theo ID | `200 OK` | `404 Not Found` |
| `PATCH` | `/api/v1/tasks/{task_id}` | Cập nhật từng phần thông tin task (Partial Update) | `200 OK` | `404 Not Found`, `422` |
| `DELETE` | `/api/v1/tasks/{task_id}` | Xóa vĩnh viễn một task theo ID | `204 No Content` | `404 Not Found` |

- **Quy tắc nghiệp vụ Công việc**:
  - `project_id`: Bắt buộc, phải tham chiếu đến một dự án đang tồn tại (nếu project không tồn tại, trả về `404 Not Found`).
  - `title`: Bắt buộc, độ dài từ 3 đến 120 ký tự, tự động cắt khoảng trắng thừa.
  - `priority`: Enum gồm 3 mức: `LOW`, `MEDIUM`, `HIGH` (mặc định là `MEDIUM`).
  - `status`: Enum gồm 3 trạng thái: `TODO`, `IN_PROGRESS`, `DONE` (mặc định khi tạo là `TODO`).
  - `due_date`: Chuỗi ngày giờ ISO 8601 tùy chọn.
  - **Bộ lọc danh sách (`GET /api/v1/tasks`)**:
    - `project_id`: Lọc các task thuộc dự án cụ thể.
    - `status`: Lọc theo trạng thái công việc.
    - `priority`: Lọc theo độ ưu tiên.
    - `limit`: Phân trang, số lượng bản ghi tối đa (mặc định 10, tối đa 100).
    - `offset`: Phân trang, vị trí bắt đầu lấy bản ghi (mặc định 0).
  - **Cập nhật từng phần (`PATCH /api/v1/tasks/{task_id}`)**:
    - Cho phép client cập nhật độc lập một hoặc nhiều trường (`title`, `description`, `status`, `priority`, `due_date`). Các trường không gửi lên phải giữ nguyên giá trị cũ (sử dụng `exclude_unset=True`).

### 3. Chuẩn hóa Định dạng Lỗi (RFC 9457 Problem Details)

Mọi phản hồi lỗi trong hệ thống bắt buộc phải trả về theo định dạng JSON chuẩn RFC 9457 với `Content-Type: application/problem+json`:
```json
{
  "type": "https://errors.taskflow.dev/resource-not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Không tìm thấy công việc với ID = 99",
  "instance": "/api/v1/tasks/99"
}
```

---

## 🛠️ Yêu cầu kỹ thuật

Để đạt chuẩn chất lượng một sản phẩm Backend hiện đại, mã nguồn phải tuân thủ nghiêm ngặt các tiêu chuẩn sau:

1. **Phiên bản & Thư viện**:
   - Python 3.12+.
   - **FastAPI 0.110+**: Khai báo route bằng `APIRouter`, phân định rõ `tags`, `status_code`, và `response_model`.
   - **Pydantic v2**: Chỉ sử dụng API v2 (`model_dump()`, `model_validate()`, `ConfigDict`). Tuyệt đối không dùng API v1 đã bị khai tử.
   - **pydantic-settings**: Quản lý cấu hình đọc từ file `.env` qua `BaseSettings`.
2. **Kiến trúc phân tách trách nhiệm (Separation of Concerns)**:
   - **Tầng Schemas**: Tách riêng biệt `ProjectBase`, `ProjectCreate`, `ProjectRead`, `TaskBase`, `TaskCreate`, `TaskUpdate`, `TaskRead`.
   - **Tầng Domain Exceptions**: Ném các ngoại lệ nghiệp vụ thuần túy (`ProjectNotFoundError`, `TaskNotFoundError`, `DuplicateProjectNameError`). Tầng Service không bao giờ được ném `HTTPException`.
   - **Tầng Repositories**: Sử dụng `typing.Protocol` để định nghĩa giao diện kho lưu trữ (Repository Interface), tạo lớp lưu trữ in-memory an toàn dữ liệu, sẵn sàng cắm rút SQLAlchemy ở Milestone M2.
   - **Tầng Services**: Xử lý toàn bộ logic nghiệp vụ (sinh ID, kiểm tra ràng buộc khóa ngoại `project_id`, validate trạng thái).
3. **Dependency Injection**:
   - Mọi Repository và Service đều được tiêm thông qua `Annotated[Service, Depends(get_service)]`.
   - Cấu hình ứng dụng được nạp qua `Annotated[Settings, Depends(get_settings)]` kết hợp `@lru_cache`.
4. **Kiểm thử tự động (Automated Testing)**:
   - Viết bộ test với `pytest` và `TestClient` (hoặc `httpx.AsyncClient`).
   - Kiểm tra cả kịch bản thành công (201, 200, 204) và các kịch bản lỗi (404, 409, 422).
   - Thiết lập fixture dọn dẹp trạng thái database in-memory giữa các bài test.
5. **Code Style & Static Analysis**:
   - 100% hàm và phương thức đều có Type Annotations.
   - Kiểm tra sạch sẽ không còn lỗi với `ruff check .` và định dạng bằng `ruff format .`.

---

## 📁 Gợi ý cấu trúc thư mục

Một cấu trúc thư mục phân tầng chuẩn mực cho dự án TaskFlow API M1:

```text
taskflow-api/
├── .env.example                # File biến môi trường mẫu
├── pyproject.toml              # Cấu hình dự án, dependencies và rules ruff/pytest
├── README.md                   # Hướng dẫn cài đặt, chạy app và test
├── app/
│   ├── __init__.py
│   ├── main.py                 # Khởi tạo FastAPI app, exception handlers, include routers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # AppSettings kế thừa BaseSettings với @lru_cache
│   │   └── exceptions.py       # Domain exceptions & RFC 9457 handlers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py            # TaskStatus, TaskPriority
│   │   └── domain.py           # ProjectDomain, TaskDomain entities
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py           # ProblemDetails, InvalidParam schemas
│   │   ├── project.py          # ProjectCreate, ProjectRead
│   │   └── task.py             # TaskCreate, TaskUpdate, TaskRead, TaskFilterParams
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # Protocol định nghĩa IProjectRepository, ITaskRepository
│   │   └── memory.py           # InMemoryProjectRepository, InMemoryTaskRepository
│   ├── services/
│   │   ├── __init__.py
│   │   ├── project_service.py  # ProjectService & dependency get_project_service
│   │   └── task_service.py     # TaskService & dependency get_task_service
│   └── routers/
│       ├── __init__.py
│       ├── api_v1.py           # Tổng hợp router v1
│       ├── projects.py         # Endpoints CRUD Projects
│       └── tasks.py            # Endpoints CRUD Tasks
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures: TestClient, in-memory repositories reset
    ├── test_projects.py        # Test cases cho Projects API
    └── test_tasks.py           # Test cases cho Tasks API
```

---

## 💡 Gợi ý triển khai

Dưới đây là mã nguồn mẫu chi tiết từng bước giúp bạn xây dựng hoàn thiện Milestone M1 theo đúng chuẩn thiết kế cao cấp nhất:

### Bước 1: Khai báo Cấu hình (`app/core/config.py`)

```python
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "TaskFlow REST API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True
    PORT: int = Field(default=8000, ge=1024, le=65535)


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Bước 2: Ngoại lệ Domain & RFC 9457 Handlers (`app/core/exceptions.py`)

```python
from typing import Any
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


# 1. Schemas định dạng lỗi RFC 9457
class InvalidParam(BaseModel):
    name: str = Field(description="Tên tham số hoặc trường bị lỗi")
    reason: str = Field(description="Lý do không hợp lệ")


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str
    instance: str
    invalid_params: list[InvalidParam] | None = None


# 2. Hệ thống Ngoại lệ Domain thuần túy
class DomainError(Exception):
    """Lớp cha cho mọi lỗi nghiệp vụ."""


class ProjectNotFoundError(DomainError):
    def __init__(self, project_id: int) -> None:
        super().__init__(f"Không tìm thấy dự án với ID: {project_id}")
        self.project_id = project_id


class DuplicateProjectNameError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Dự án với tên '{name}' đã tồn tại trong hệ thống!")
        self.name = name


class TaskNotFoundError(DomainError):
    def __init__(self, task_id: int) -> None:
        super().__init__(f"Không tìm thấy công việc với ID: {task_id}")
        self.task_id = task_id


# 3. Exception Handlers
def create_problem_response(
    status_code: int,
    title: str,
    detail: str,
    instance: str,
    type_uri: str = "about:blank",
    invalid_params: list[InvalidParam] | None = None,
) -> JSONResponse:
    problem = ProblemDetails(
        type=type_uri,
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
        invalid_params=invalid_params,
    )
    return JSONResponse(
        status_code=status_code,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def domain_error_handler(
    request: Request, exc: DomainError
) -> JSONResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    title = "Bad Request"

    if isinstance(exc, (ProjectNotFoundError, TaskNotFoundError)):
        status_code = status.HTTP_404_NOT_FOUND
        title = "Resource Not Found"
    elif isinstance(exc, DuplicateProjectNameError):
        status_code = status.HTTP_409_CONFLICT
        title = "Resource Conflict"

    return create_problem_response(
        status_code=status_code,
        title=title,
        detail=str(exc),
        instance=request.url.path,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    params = [
        InvalidParam(
            name=" -> ".join(str(loc) for loc in err["loc"]),
            reason=err["msg"],
        )
        for err in exc.errors()
    ]
    return create_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        title="Validation Failed",
        detail="Dữ liệu payload gửi lên không đáp ứng các ràng buộc kiểm tra.",
        instance=request.url.path,
        invalid_params=params,
    )
```

### Bước 3: Schemas Pydantic v2 (`app/schemas/`)

> [!NOTE]
> **Tổ chức file Schemas:** Trong cấu trúc thư mục của dự án, bạn có thể tách nhỏ thành `app/schemas/common.py`, `app/schemas/project.py`, `app/schemas/task.py` hoặc gom chung vào `app/schemas.py`. Dưới đây là định nghĩa đầy đủ của các schemas được sử dụng trong toàn bộ hệ thống.

```python
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


# --- Schemas Project ---
class ProjectBase(BaseModel):
    name: str = Field(min_length=3, max_length=50, description="Tên dự án")
    description: str | None = Field(default=None, max_length=255)


class ProjectCreate(ProjectBase):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_count: int = Field(default=0, description="Tổng số task của dự án")
    created_at: datetime


# --- Schemas Task ---
class TaskBase(BaseModel):
    title: str = Field(
        min_length=3, max_length=120, description="Tiêu đề công việc"
    )
    description: str | None = Field(default=None, max_length=500)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)


class TaskCreate(TaskBase):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    project_id: int = Field(ge=1, description="ID dự án mà task trực thuộc")
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: int
    project_id: int
    status: TaskStatus
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TaskListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TaskRead]
```

### Bước 4: In-Memory Repositories (`app/repositories/memory.py`)

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ProjectRecord:
    id: int
    name: str
    description: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskRecord:
    id: int
    project_id: int
    title: str
    description: str | None
    priority: str
    status: str
    due_date: datetime | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self._projects: dict[int, ProjectRecord] = {}
        self._counter: int = 1

    def create(self, name: str, description: str | None) -> ProjectRecord:
        record = ProjectRecord(
            id=self._counter, name=name, description=description
        )
        self._projects[self._counter] = record
        self._counter += 1
        return record

    def get_by_id(self, project_id: int) -> ProjectRecord | None:
        return self._projects.get(project_id)

    def get_by_name(self, name: str) -> ProjectRecord | None:
        for p in self._projects.values():
            if p.name.lower() == name.lower():
                return p
        return None

    def list_all(self) -> list[ProjectRecord]:
        return list(self._projects.values())

    def delete(self, project_id: int) -> bool:
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False

    def clear(self) -> None:
        self._projects.clear()
        self._counter = 1


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[int, TaskRecord] = {}
        self._counter: int = 1

    def create(
        self,
        project_id: int,
        title: str,
        description: str | None,
        priority: str,
        due_date: datetime | None,
    ) -> TaskRecord:
        record = TaskRecord(
            id=self._counter,
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            status="TODO",
            due_date=due_date,
        )
        self._tasks[self._counter] = record
        self._counter += 1
        return record

    def get_by_id(self, task_id: int) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        project_id: int | None = None,
        status_filter: str | None = None,
        priority: str | None = None,
    ) -> list[TaskRecord]:
        items = list(self._tasks.values())
        if project_id is not None:
            items = [t for t in items if t.project_id == project_id]
        if status_filter is not None:
            items = [t for t in items if t.status == status_filter]
        if priority is not None:
            items = [t for t in items if t.priority == priority]
        return items

    def update(
        self, task_id: int, update_fields: dict[str, object]
    ) -> TaskRecord | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for key, value in update_fields.items():
            setattr(task, key, value)
        task.updated_at = datetime.now(UTC)
        return task

    def delete(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def delete_by_project_id(self, project_id: int) -> int:
        to_delete = [
            t.id for t in self._tasks.values() if t.project_id == project_id
        ]
        for tid in to_delete:
            del self._tasks[tid]
        return len(to_delete)

    def count_by_project_id(self, project_id: int) -> int:
        return sum(
            1 for t in self._tasks.values() if t.project_id == project_id
        )

    def clear(self) -> None:
        self._tasks.clear()
        self._counter = 1


# Singletons cho toàn bộ vòng đời ứng dụng
project_repo = InMemoryProjectRepository()
task_repo = InMemoryTaskRepository()


def get_project_repository() -> InMemoryProjectRepository:
    return project_repo


def get_task_repository() -> InMemoryTaskRepository:
    return task_repo
```

### Bước 5: Tầng Dịch Vụ Nghiệp Vụ (`app/services/`)

```python
from typing import Annotated

from fastapi import Depends

from app.core.exceptions import (
    DuplicateProjectNameError,
    ProjectNotFoundError,
    TaskNotFoundError,
)
from app.repositories.memory import (
    InMemoryProjectRepository,
    InMemoryTaskRepository,
    get_project_repository,
    get_task_repository,
)
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.task import TaskCreate, TaskListResponse, TaskRead, TaskUpdate


class ProjectService:
    def __init__(
        self,
        repo: InMemoryProjectRepository,
        task_repo_inst: InMemoryTaskRepository,
    ) -> None:
        self.repo = repo
        self.task_repo = task_repo_inst

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
        if self.repo.get_by_name(payload.name):
            raise DuplicateProjectNameError(payload.name)
        record = self.repo.create(
            name=payload.name, description=payload.description
        )
        return ProjectRead(
            id=record.id,
            name=record.name,
            description=record.description,
            task_count=0,
            created_at=record.created_at,
        )

    def get_project_by_id(self, project_id: int) -> ProjectRead:
        record = self.repo.get_by_id(project_id)
        if not record:
            raise ProjectNotFoundError(project_id)
        count = self.task_repo.count_by_project_id(project_id)
        return ProjectRead(
            id=record.id,
            name=record.name,
            description=record.description,
            task_count=count,
            created_at=record.created_at,
        )

    def list_projects(self) -> list[ProjectRead]:
        records = self.repo.list_all()
        return [
            ProjectRead(
                id=r.id,
                name=r.name,
                description=r.description,
                task_count=self.task_repo.count_by_project_id(r.id),
                created_at=r.created_at,
            )
            for r in records
        ]

    def delete_project(self, project_id: int) -> None:
        if not self.repo.get_by_id(project_id):
            raise ProjectNotFoundError(project_id)
        # Xóa liên hoàn các task con thuộc dự án
        self.task_repo.delete_by_project_id(project_id)
        self.repo.delete(project_id)


def get_project_service(
    repo: Annotated[InMemoryProjectRepository, Depends(get_project_repository)],
    task_repo_dep: Annotated[
        InMemoryTaskRepository, Depends(get_task_repository)
    ],
) -> ProjectService:
    return ProjectService(repo=repo, task_repo_inst=task_repo_dep)


class TaskService:
    def __init__(
        self,
        task_repo_inst: InMemoryTaskRepository,
        proj_repo: InMemoryProjectRepository,
    ) -> None:
        self.task_repo = task_repo_inst
        self.project_repo = proj_repo

    def create_task(self, payload: TaskCreate) -> TaskRead:
        # Kiểm tra tính tồn tại của Project
        if not self.project_repo.get_by_id(payload.project_id):
            raise ProjectNotFoundError(payload.project_id)

        record = self.task_repo.create(
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority.value,
            due_date=payload.due_date,
        )
        return TaskRead.model_validate(record)

    def get_task_by_id(self, task_id: int) -> TaskRead:
        record = self.task_repo.get_by_id(task_id)
        if not record:
            raise TaskNotFoundError(task_id)
        return TaskRead.model_validate(record)

    def list_tasks(
        self,
        project_id: int | None = None,
        status_filter: str | None = None,
        priority: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> TaskListResponse:
        records = self.task_repo.list_tasks(
            project_id=project_id,
            status_filter=status_filter,
            priority=priority,
        )
        total = len(records)
        paged = records[offset : offset + limit]
        return TaskListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[TaskRead.model_validate(r) for r in paged],
        )

    def update_task(self, task_id: int, payload: TaskUpdate) -> TaskRead:
        if not self.task_repo.get_by_id(task_id):
            raise TaskNotFoundError(task_id)

        update_data = payload.model_dump(exclude_unset=True)
        # Chuyển đổi enum thành giá trị thô nếu có
        for field in ("priority", "status"):
            if field in update_data and hasattr(update_data[field], "value"):
                update_data[field] = getattr(update_data[field], "value")

        updated = self.task_repo.update(task_id, update_data)
        return TaskRead.model_validate(updated)

    def delete_task(self, task_id: int) -> None:
        if not self.task_repo.get_by_id(task_id):
            raise TaskNotFoundError(task_id)
        self.task_repo.delete(task_id)


def get_task_service(
    task_repo_dep: Annotated[
        InMemoryTaskRepository, Depends(get_task_repository)
    ],
    proj_repo: Annotated[
        InMemoryProjectRepository, Depends(get_project_repository)
    ],
) -> TaskService:
    return TaskService(task_repo_inst=task_repo_dep, proj_repo=proj_repo)
```

### Bước 6: Khởi tạo Ứng dụng & Routers (`app/main.py`)

```python
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Path, Query, status
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.exceptions import (
    DomainError,
    domain_error_handler,
    validation_error_handler,
)
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)
from app.services.project import ProjectService, get_project_service
from app.services.task import TaskService, get_task_service

# Khởi tạo Routers
projects_router = APIRouter(prefix="/projects", tags=["Projects"])
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])


# --- Endpoints Projects ---
@projects_router.post(
    "/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
def create_project(
    payload: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    return service.create_project(payload)


@projects_router.get("/", response_model=list[ProjectRead])
def list_projects(
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectRead]:
    return service.list_projects()


@projects_router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: Annotated[int, Path(ge=1)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    return service.get_project_by_id(project_id)


@projects_router.delete(
    "/{project_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_project(
    project_id: Annotated[int, Path(ge=1)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    service.delete_project(project_id)


# --- Endpoints Tasks ---
@tasks_router.post(
    "/", response_model=TaskRead, status_code=status.HTTP_201_CREATED
)
def create_task(
    payload: TaskCreate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskRead:
    return service.create_task(payload)


@tasks_router.get("/", response_model=TaskListResponse)
def list_tasks(
    service: Annotated[TaskService, Depends(get_task_service)],
    project_id: Annotated[int | None, Query(ge=1)] = None,
    status_filter: Annotated[
        TaskStatus | None, Query(alias="status")
    ] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListResponse:
    status_str = status_filter.value if status_filter else None
    priority_str = priority.value if priority else None
    return service.list_tasks(
        project_id=project_id,
        status_filter=status_str,
        priority=priority_str,
        limit=limit,
        offset=offset,
    )


@tasks_router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: Annotated[int, Path(ge=1)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskRead:
    return service.get_task_by_id(task_id)


@tasks_router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: Annotated[int, Path(ge=1)],
    payload: TaskUpdate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskRead:
    return service.update_task(task_id, payload)


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: Annotated[int, Path(ge=1)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    service.delete_task(task_id)


# Khởi tạo App FastAPI
settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
)

# Đăng ký Exception Handlers chuẩn RFC 9457
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Gắn Routers vào app
api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(tasks_router)
app.include_router(api_v1_router)
```

### Bước 7: Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_api.py`)

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.memory import project_repo, task_repo


@pytest.fixture(autouse=True)
def clean_repositories():
    """Fixture tự động dọn sạch cơ sở dữ liệu in-memory trước mỗi bài test."""
    project_repo.clear()
    task_repo.clear()
    yield
    project_repo.clear()
    task_repo.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_project_success(client: TestClient):
    response = client.post(
        "/api/v1/projects/",
        json={"name": "Hạ tầng Cloud", "description": "Dự án AWS & K8s"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Hạ tầng Cloud"
    assert data["task_count"] == 0


def test_create_duplicate_project_returns_409(client: TestClient):
    client.post("/api/v1/projects/", json={"name": "Dự án Trùng"})
    response = client.post("/api/v1/projects/", json={"name": "Dự án Trùng"})
    assert response.status_code == 409
    data = response.json()
    assert data["title"] == "Resource Conflict"
    assert "đã tồn tại" in data["detail"]


def test_create_task_under_project_success(client: TestClient):
    # 1. Tạo project
    proj_res = client.post(
        "/api/v1/projects/", json={"name": "Backend Development"}
    )
    proj_id = proj_res.json()["id"]

    # 2. Tạo task thuộc project đó
    task_res = client.post(
        "/api/v1/tasks/",
        json={
            "project_id": proj_id,
            "title": "Thiết lập CI/CD Pipeline",
            "priority": "HIGH",
        },
    )
    assert task_res.status_code == 201
    task_data = task_res.json()
    assert task_data["id"] == 1
    assert task_data["status"] == "TODO"
    assert task_data["priority"] == "HIGH"

    # 3. Kiểm tra project task_count được cập nhật lên 1
    get_proj = client.get(f"/api/v1/projects/{proj_id}")
    assert get_proj.json()["task_count"] == 1


def test_create_task_with_nonexistent_project_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/tasks/",
        json={"project_id": 9999, "title": "Task mồ côi"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["title"] == "Resource Not Found"


def test_partial_update_task_patch(client: TestClient):
    # Tạo project & task ban đầu
    p = client.post("/api/v1/projects/", json={"name": "Mobile Dev"}).json()
    t = client.post(
        "/api/v1/tasks/",
        json={"project_id": p["id"], "title": "Thiết kế UI", "priority": "LOW"},
    ).json()

    # Cập nhật status sang IN_PROGRESS và priority sang HIGH
    patch_res = client.patch(
        f"/api/v1/tasks/{t['id']}",
        json={"status": "IN_PROGRESS", "priority": "HIGH"},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["title"] == "Thiết kế UI"  # Giữ nguyên
    assert updated["status"] == "IN_PROGRESS"
    assert updated["priority"] == "HIGH"
    assert updated["updated_at"] is not None


def test_validation_error_returns_rfc9457(client: TestClient):
    # Tiêu đề quá ngắn (< 3 ký tự)
    response = client.post(
        "/api/v1/projects/",
        json={"name": "AB"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["title"] == "Validation Failed"
    assert "invalid_params" in data
    assert any("name" in p["name"] for p in data["invalid_params"])


def test_cascade_delete_project_removes_tasks(client: TestClient):
    p = client.post("/api/v1/projects/", json={"name": "Dự án Hủy"}).json()
    t = client.post(
        "/api/v1/tasks/",
        json={"project_id": p["id"], "title": "Task sẽ bị xóa"},
    ).json()

    # Xóa project
    del_res = client.delete(f"/api/v1/projects/{p['id']}")
    assert del_res.status_code == 204

    # Xác nhận task con cũng bị xóa mất
    task_check = client.get(f"/api/v1/tasks/{t['id']}")
    assert task_check.status_code == 404
```

---

## ✅ Definition of Done

Dự án TaskFlow M1 được coi là hoàn thành xuất sắc khi bạn tự tay kiểm tra và thỏa mãn toàn bộ các tiêu chí sau:

| Hạng mục | Tiêu chuẩn nghiệm thu | Đạt |
|---|---|:---:|
| **RESTful CRUD Projects** | Đầy đủ 4 endpoint: `POST`, `GET`, `GET /{id}`, `DELETE /{id}` hoạt động trơn tru | [ ] |
| **RESTful CRUD Tasks** | Đầy đủ 5 endpoint: `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` | [ ] |
| **Lọc & Phân trang** | Endpoint `GET /api/v1/tasks` lọc chính xác theo `project_id`, `status`, `priority`, `limit`, `offset` | [ ] |
| **DTO & Pydantic v2** | 100% Schemas dùng Pydantic v2 (`model_dump`, `ConfigDict`), phân tách rõ `Create`, `Update`, `Read` | [ ] |
| **Cascade Delete** | Khi xóa một Project, toàn bộ Tasks thuộc dự án đó biến mất khỏi hệ thống | [ ] |
| **RFC 9457 Errors** | Toàn bộ lỗi 400, 404, 409, 422 trả về cấu trúc Problem Details (`application/problem+json`) | [ ] |
| **Dependency Injection** | Tầng Routers chỉ phụ thuộc vào Services; Services phụ thuộc vào Repositories qua `Depends()` | [ ] |
| **Settings 12-Factor** | Quản lý cấu hình qua `pydantic-settings` và `.env`, tối ưu bằng `@lru_cache` | [ ] |
| **Automated Tests** | Bộ test `pytest` bao phủ tối thiểu 7 ca kiểm thử chính, pass 100% với tốc độ dưới 1 giây | [ ] |
| **OpenAPI Docs** | Truy cập `http://localhost:8000/docs`, toàn bộ endpoints hiển thị đầy đủ tags, summary, response model | [ ] |

---

## 🚀 Thử thách thêm

Nếu bạn đã hoàn thành các yêu cầu cơ bản và muốn nâng cao năng lực như một kỹ sư Middle thực thụ, hãy thử sức với các bài toán mở rộng sau:

1. **Middleware Đo Thời Gian Phản Hồi (`X-Process-Time`)**:
   - Viết một middleware đo chính xác thời gian server xử lý request tính bằng mili-giây và gắn vào header phản hồi:
     `X-Process-Time: 1.45ms`.
2. **Endpoint Xuất Dữ Liệu (`Export Endpoint`)**:
   - Xây dựng endpoint `GET /api/v1/export/tasks`: Trả về file định dạng CSV hoặc JSON chứa toàn bộ dữ liệu công việc kèm header `Content-Disposition: attachment; filename="tasks_backup.json"`.
3. **Tìm Kiếm Mờ (Fuzzy Search)**:
   - Bổ sung tham số query `q: str | None = None` cho `GET /api/v1/tasks` cho phép tìm kiếm gần đúng (case-insensitive) đồng thời trên cả `title` và `description`.
4. **Rate Limiting Đơn Giản bằng Dependency**:
   - Viết một dependency kiểm tra tần suất gửi request của Client IP (sử dụng một dictionary in-memory lưu timestamp). Nếu một IP gửi quá 10 requests trong vòng 5 giây, trả về `429 Too Many Requests` chuẩn RFC 9457.

<!-- nav:bottom -->
---

[⬅️ Cấu trúc project & settings](../02-junior/09-project-structure-settings.md) | [📚 Dự án TaskFlow](./README.md) | [Middle ➡️](../03-middle/README.md)
<!-- /nav:bottom -->
