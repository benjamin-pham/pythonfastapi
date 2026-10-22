<!-- nav:top -->
[🏠 Home](../README.md) › [Dự án TaskFlow](./README.md) › M2
<!-- /nav:top -->

# M2 – Production API

> ⏱️ Thời lượng ước tính: 8–12 giờ thực hành độc lập · 📌 Yêu cầu trước: Hoàn thành [Milestone M1](./m1-crud-api.md) và toàn bộ các bài học trong [Level 03: Middle](../03-middle/README.md).

---

## 🎯 Bối cảnh

Chào mừng bạn đến với **Milestone M2: Production-Ready API** – bước chuyển mình quyết định của dự án **TaskFlow**. 

Trong [Milestone M1](./m1-crud-api.md), bạn đã kiến tạo thành công một dịch vụ RESTful CRUD API hoàn chỉnh với kiến trúc phân tầng sạch (Clean Layered Architecture), Dependency Injection, và xử lý lỗi chuẩn RFC 9457. Tuy nhiên, tầng lưu trữ của M1 vẫn là bộ nhớ tạm thời (**In-Memory**) và hệ thống chưa hề có cơ chế bảo vệ danh tính hay kiểm soát truy cập người dùng.

Trong **Milestone M2**, bạn sẽ nâng cấp toàn diện TaskFlow thành một hệ thống backend doanh nghiệp thực thụ sẵn sàng vận hành trên môi trường Production:
- **Cơ sở dữ liệu Quan hệ Bất đồng bộ**: Thay thế hoàn toàn In-Memory Repositories bằng **PostgreSQL 17** kết hợp **SQLAlchemy 2.0 Async ORM** (`asyncpg`) và công cụ quản lý di chuyển lược đồ tự động **Alembic**.
- **Hệ thống Định danh & Xác thực (Authentication)**: Đăng ký, đăng nhập an toàn với chuẩn băm mật khẩu thế hệ mới **Argon2** (thông qua `pwdlib`), cấp phát và xác thực chuỗi mã **JWT Access Token & Refresh Token**.
- **Phân quyền Đa tầng (Authorization)**: Kết hợp chặt chẽ giữa **Role-Based Access Control (RBAC)** cho các chức năng quản trị hệ thống và **Resource-Based Authorization (BOLA/IDOR Defense)** để bảo vệ quyền sở hữu dữ liệu của từng người dùng.
- **Phân trang, Lọc & Sắp xếp An toàn**: Cung cấp Generic Schema `Page[T]`, bộ lọc động đa tiêu chí và sắp xếp whitelist triệt tiêu nguy cơ SQL Injection.
- **Giám sát & Xử lý Ngoại lệ**: Triển khai Structured JSON Logging gắn mã vết `request_id` xuyên suốt các async tasks qua `contextvars.ContextVar`, bọc bảo vệ hệ thống bằng Global Exception Handler RFC 9457.
- **Đóng gói & CI/CD**: Container hóa bằng Multi-stage Dockerfile tối ưu với `uv`, điều phối đa dịch vụ qua `compose.yaml`, và thiết lập pipeline GitHub Actions tự động kiểm thử toàn vẹn.

---

## 📋 Yêu cầu chức năng

Hệ thống TaskFlow M2 quản lý 3 thực thể cốt lõi: **`User`**, **`Project`**, và **`Task`**.

```text
┌─────────────────┐       1 : N        ┌──────────────────┐       1 : N        ┌─────────────────┐
│      User       ├───────────────────►│     Project      ├───────────────────►│      Task       │
│─────────────────│                    │──────────────────│                    │─────────────────│
│ id (PK)         │                    │ id (PK)          │                    │ id (PK)         │
│ email (Unique)  │                    │ name             │                    │ project_id (FK) │
│ hashed_password │                    │ description      │                    │ title           │
│ role (Enum)     │                    │ owner_id (FK)    │                    │ assignee_id(FK) │
│ is_active       │                    │ created_at       │                    │ status (Enum)   │
│ created_at      │                    │ updated_at       │                    │ priority (Enum) │
└─────────────────┘                    └──────────────────┘                    │ due_date        │
                                                                               │ created_at      │
                                                                               └─────────────────┘
```

### 1. Phân hệ Xác thực & Người dùng (`/api/v1/auth` & `/api/v1/admin/users`)

| Method | Endpoint | Quyền hạn | Mô tả |
|---|---|:---:|---|
| `POST` | `/api/v1/auth/register` | Public | Đăng ký tài khoản mới (mặc định nhận role `MEMBER`). |
| `POST` | `/api/v1/auth/login` | Public | Đăng nhập bằng email/password, trả về Access & Refresh Token. |
| `POST` | `/api/v1/auth/refresh` | Public | Đổi Refresh Token lấy Access Token mới. |
| `GET` | `/api/v1/auth/me` | Authenticated | Lấy thông tin cá nhân của tài khoản hiện tại. |
| `GET` | `/api/v1/admin/users` | `ADMIN` only | Danh sách toàn bộ người dùng trong hệ thống (có phân trang). |
| `PATCH` | `/api/v1/admin/users/{user_id}/role` | `ADMIN` only | Nâng/hạ vai trò người dùng (`ADMIN`, `MEMBER`, `VIEWER`). |

- **Quy tắc nghiệp vụ Xác thực**:
  - `email`: Phải là địa chỉ email hợp lệ, duy nhất trên toàn hệ thống (trả về `409 Conflict` nếu trùng).
  - `password`: Tối thiểu 8 ký tự, có ít nhất 1 chữ hoa, 1 số và 1 ký tự đặc biệt. Mật khẩu phải được băm bằng thuật toán **Argon2** trước khi lưu vào DB.
  - `Access Token`: Thời hạn sống 30 phút, mã hóa các claims: `sub` (User ID), `role`, `email`, `exp`.
  - `Refresh Token`: Thời hạn sống 7 ngày.

### 2. Phân hệ Quản lý Dự án (`/api/v1/projects`)

| Method | Endpoint | Quyền hạn | Mô tả |
|---|---|:---:|---|
| `POST` | `/api/v1/projects` | `ADMIN`, `MEMBER` | Tạo dự án mới (gán `owner_id = current_user.id`). |
| `GET` | `/api/v1/projects` | Authenticated | Danh sách dự án (User chỉ thấy dự án của mình; Admin thấy tất cả). |
| `GET` | `/api/v1/projects/{id}` | Owner or `ADMIN` | Xem thông tin chi tiết dự án. |
| `PATCH` | `/api/v1/projects/{id}` | Owner or `ADMIN` | Cập nhật tên hoặc mô tả dự án. |
| `DELETE` | `/api/v1/projects/{id}` | Owner or `ADMIN` | Xóa dự án (và tự động xóa liên hoàn toàn bộ tasks thuộc về nó). |

### 3. Phân hệ Quản lý Công việc (`/api/v1/tasks`)

| Method | Endpoint | Quyền hạn | Mô tả |
|---|---|:---:|---|
| `POST` | `/api/v1/tasks` | Project Owner/Assignee | Tạo task mới thuộc project (phải có quyền truy cập project cha). |
| `GET` | `/api/v1/tasks` | Authenticated | Danh sách tasks hỗ trợ phân trang `Page[TaskRead]`, lọc & sắp xếp. |
| `GET` | `/api/v1/tasks/{id}` | Permitted User | Xem chi tiết công việc. |
| `PATCH` | `/api/v1/tasks/{id}` | Permitted User | Cập nhật thông tin công việc (status, priority, assignee...). |
| `DELETE` | `/api/v1/tasks/{id}` | Project Owner or `ADMIN`| Xóa công việc. |

- **Quy tắc phân quyền tài nguyên (Resource Authorization)**:
  - Một người dùng được phép chỉnh sửa task khi và chỉ khi thỏa mãn **ít nhất một** điều kiện:
    1. Là `ADMIN` của hệ thống.
    2. Là `owner_id` của Project sở hữu task đó.
    3. Là `assignee_id` (người được giao phụ trách task).
  - Người dùng có role `VIEWER` chỉ được phép đọc (`GET`), mọi thao tác ghi/sửa/xóa đều bị từ chối với mã lỗi `403 Forbidden`.

---

## 🛠️ Yêu cầu kỹ thuật

Để hoàn thành xuất sắc Milestone M2, dự án cần tuân thủ nghiêm ngặt các tiêu chuẩn kỹ thuật sau:

1. **Ngôn ngữ & Thư viện cốt lõi**:
   - Python 3.12+ với Type Annotations đầy đủ.
   - **FastAPI 0.115+** & **Pydantic v2**.
   - **SQLAlchemy 2.0+** hoàn toàn ở chế độ `async` với driver **`asyncpg`**.
   - **Alembic** để tự động sinh và thực thi database migrations (`alembic revision --autogenerate`, `alembic upgrade head`).
   - **`pwdlib[argon2]`** cho việc băm và kiểm tra mật khẩu; **`pyjwt`** để mã hóa/giải mã token JWT.
   - **`python-multipart`** để xử lý `application/x-www-form-urlencoded` cho `OAuth2PasswordRequestForm`.
2. **Kiến trúc Phân tầng Clean Architecture**:
   - `models/`: Định nghĩa các bảng database sử dụng cú pháp `Mapped[...]` và `mapped_column(...)`.
   - `schemas/`: Hợp đồng dữ liệu request/response rõ ràng.
   - `repositories/`: Đóng gói các câu truy vấn SQLAlchemy vào lớp Repository.
   - `services/`: Chứa 100% logic nghiệp vụ miền, ném các `DomainException` thuần túy.
   - `api/deps.py`: Quản lý tiêm phụ thuộc (`get_db`, `get_current_user`, `require_roles`).
3. **Cơ chế Giám sát & Xử lý Ngoại lệ**:
   - Structured JSON Logging xuất ra stdout.
   - Sử dụng `contextvars.ContextVar` để gắn `request_id` tự động vào mọi câu log của request.
   - Global Exception Handlers che giấu stack trace và trả về lỗi chuẩn **RFC 9457 Problem Details**.
4. **Kiểm thử Tự động (Automated Testing)**:
   - Sử dụng `pytest` kết hợp `pytest-asyncio` (`asyncio_mode = "auto"`).
   - Sử dụng `httpx.AsyncClient` với `ASGITransport(app=app)`.
   - Áp dụng kỹ thuật **Transaction Rollback & Nested Savepoint** để cô lập database trong từng test case.
5. **Đóng gói & CI/CD**:
   - Multi-stage `Dockerfile` non-root user tối ưu bằng `uv`.
   - `compose.yaml` chạy `api` và `postgres:17` có healthcheck tự động chạy `alembic upgrade head`.
   - File workflow GitHub Actions `.github/workflows/ci.yml` kiểm tra Linting, Formatting, Typing, Migration và Tests.

---

## 📁 Gợi ý cấu trúc thư mục

```text
taskflow-api/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI Workflow
├── alembic/
│   ├── env.py                  # Cấu hình async database migration
│   ├── script.py.mako
│   └── versions/               # Các migration files đã sinh
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py             # Khởi tạo FastAPI app, lifespan, middleware & exception handlers
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py       # Pydantic BaseSettings đọc biến môi trường
│       │   ├── context.py      # contextvars ContextVar lưu trữ request_id
│       │   ├── database.py     # async_engine & async_sessionmaker
│       │   ├── exceptions.py   # Domain Exceptions & RFC 9457 Handlers
│       │   ├── logging.py      # Structured JSON Formatter
│       │   └── security.py     # Argon2 hashing & JWT utilities
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py         # Declarative Base chung
│       │   ├── user.py         # Model User & UserRole Enum
│       │   ├── project.py      # Model Project
│       │   └── task.py         # Model Task, TaskStatus, TaskPriority
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── common.py       # Page[T], SortOrder, RFC 9457 ProblemDetails
│       │   ├── user.py         # UserCreate, UserRead, TokenResponse
│       │   ├── project.py      # ProjectCreate, ProjectUpdate, ProjectRead
│       │   └── task.py         # TaskCreate, TaskUpdate, TaskRead, TaskFilterParams
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py         # BaseRepository Protocol / Abstract
│       │   ├── user_repo.py    # UserRepository thực hiện truy vấn User
│       │   ├── project_repo.py # ProjectRepository
│       │   └── task_repo.py    # TaskRepository với phân trang, lọc & sort
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py # Xử lý đăng ký, đăng nhập, cấp token
│       │   ├── project_service.py # Nghiệp vụ Project & kiểm tra quyền
│       │   └── task_service.py    # Nghiệp vụ Task & kiểm tra quyền
│       └── api/
│           ├── __init__.py
│           ├── deps.py         # get_db, get_current_user, require_roles
│           └── v1/
│               ├── __init__.py
│               ├── router.py   # Gom nhóm toàn bộ router v1
│               └── endpoints/
│                   ├── __init__.py
│                   ├── auth.py
│                   ├── users.py
│                   ├── projects.py
│                   └── tasks.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures: async engine, db_session savepoint rollback, AsyncClient
│   ├── test_auth.py            # Test case đăng ký, đăng nhập, token expired
│   ├── test_projects.py        # Test case CRUD projects và RBAC
│   └── test_tasks.py           # Test case phân trang, lọc, sort và IDOR
├── .dockerignore
├── .gitignore
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

---

## 🚀 Gợi ý triển khai

Dưới đây là mã nguồn mẫu chi tiết từng module để bạn tham khảo và ghép nối hoàn chỉnh.

### Bước 1: Cấu hình Hệ thống (`app/core/config.py`)

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

    PROJECT_NAME: str = "TaskFlow Enterprise API"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = False

    # Cơ sở dữ liệu PostgreSQL Async
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://taskflow_user:supersecretpassword123@localhost:5432/taskflow_db"
    )

    # Bảo mật JWT
    SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### Bước 2: Quản lý Phiên Cơ sở Dữ liệu (`app/core/database.py`)

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Alias tương thích
get_db_session = get_db
```

### Bước 3: Bảo mật Mật khẩu & JWT Token (`app/core/security.py`)

```python
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from app.core.config import settings

# Sử dụng Argon2 để băm mật khẩu
password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_jwt_token(
    subject: str | int,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_jwt_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

### Bước 4: Định nghĩa Thực thể Cơ sở dữ liệu (`app/models/`)

#### Model Cơ sở (`app/models/base.py`):
```python
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

#### Model Người dùng (`app/models/user.py`):
```python
from enum import StrEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    projects: Mapped[list["Project"]] = relationship(  # type: ignore[name-defined]
        back_populates="owner", cascade="all, delete-orphan"
    )
```

#### Model Dự án & Công việc (`app/models/project.py` & `app/models/task.py`):
```python
from enum import StrEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.user import User


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner: Mapped[User] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.TODO, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(default=TaskPriority.MEDIUM, nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    project: Mapped[Project] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship()
```

### Bước 5: Hợp đồng Dữ liệu Pydantic (`app/schemas/`)

#### Generic Pagination & Lỗi (`app/schemas/common.py`):
```python
import math
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "Page[T]":
        total_pages = math.ceil(total / size) if total > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=total_pages)


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str
    request_id: str | None = None
```

#### Schemas Người dùng & Token (`app/schemas/user.py`):
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

### Bước 6: Tầng Tiêm Phụ thuộc & Phân quyền (`app/api/deps.py`)

```python
from collections.abc import Callable
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_jwt_token
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token xác thực không hợp lệ hoặc đã hết hạn.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    stmt = select(User).where(User.id == int(user_id))
    user = (await session.scalars(stmt)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Thao tác này yêu cầu một trong các quyền: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker
```

### Bước 7: Router Xác thực (`app/api/v1/endpoints/auth.py`)

```python
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import (
    create_jwt_token,
    decode_jwt_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.user import TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    # 1. Kiểm tra email trùng
    stmt = select(User).where(User.email == payload.email)
    existing_user = (await session.scalars(stmt)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được sử dụng trên hệ thống.",
        )

    # 2. Tạo người dùng mới với mật khẩu đã băm
    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.MEMBER,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    # form_data.username chính là email đăng nhập
    stmt = select(User).where(User.email == form_data.username)
    user = (await session.scalars(stmt)).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_jwt_token(
        subject=user.id,
        expires_delta=access_delta,
        additional_claims={"type": "access", "role": user.role.value, "email": user.email},
    )
    refresh_token = create_jwt_token(
        subject=user.id,
        expires_delta=refresh_delta,
        additional_claims={"type": "refresh"},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserRead)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
```

---

## ✅ Definition of Done

Milestone M2 được nghiệm thu đạt chuẩn khi dự án vượt qua 100% các tiêu chí sau:

1. **Cơ sở dữ liệu & Migrations**:
   - PostgreSQL 17 lưu trữ dữ liệu an toàn, các quan hệ `users`, `projects`, `tasks` thiết lập khóa ngoại chuẩn xác.
   - Lệnh `alembic upgrade head` chạy thành công tạo đầy đủ các bảng và index mà không phát sinh lỗi.
2. **Xác thực & Bảo mật**:
   - Mật khẩu lưu trong bảng `users` được băm bằng Argon2, không bao giờ lộ mật khẩu gốc.
   - Endpoint `/api/v1/auth/login` cấp Access Token hợp lệ; bảo vệ các route riêng tư bằng HTTP 401 khi không gửi token hoặc token sai.
   - Kiểm tra phân quyền RBAC: User thường không gọi được route Admin (trả về HTTP 403).
   - Kiểm tra BOLA/IDOR: User A không thể cập nhật hoặc xóa task của User B.
3. **Phân trang, Lọc & Sắp xếp**:
   - `GET /api/v1/tasks` trả về đúng cấu trúc `Page[TaskRead]`.
   - Lọc đa tiêu chí hoạt động trơn tru; sắp xếp cột chống SQL injection tuyệt đối.
4. **Kiểm thử tự động**:
   - 100% test cases trong `tests/` vượt qua màu xanh khi chạy `pytest`.
   - Độ bao phủ mã nguồn (**Coverage**) đạt từ **85% trở lên**.
   - Toàn bộ integration test chạy độc lập với cơ chế Nested Savepoint Rollback mà không gây ô nhiễm DB.
5. **Container & CI Pipeline**:
   - Chạy lệnh `docker compose up -d` khởi động thành công dịch vụ `api` và `postgres`, tự động hoàn thành migration và sẵn sàng phục vụ.
   - Pipeline GitHub Actions `.github/workflows/ci.yml` kiểm tra thành công cả 4 khâu: `ruff check`, `ruff format --check`, `mypy --strict`, và `pytest`.

---

## 🌟 Thử thách thêm

Sau khi hoàn thành Milestone M2, hãy thử sức với các bài toán kiến trúc nâng cao:

1. **Thu hồi Token tức thì với Redis Blacklist**:
   - Thiết lập một container Redis và viết endpoint `POST /api/v1/auth/logout`.
   - Lưu trữ `jti` (JWT ID) của token bị đăng xuất vào Redis với TTL đúng bằng thời gian sống còn lại của token. Kiểm tra blacklist tại dependency `get_current_user`.
2. **PostgreSQL Full-Text Search**:
   - Nâng cấp bộ lọc tìm kiếm công việc bằng tính năng tìm kiếm toàn văn bản (Full-Text Search) của Postgres thông qua hàm `to_tsvector('vietnamese', Task.title)` kết hợp GIN Index.
3. **Soft Delete (Xóa mềm)**:
   - Thêm cột `is_deleted: bool` và `deleted_at: datetime | None` vào các entity.
   - Tự động lọc bỏ các bản ghi đã xóa mềm trong mọi câu truy vấn `select` thông qua cơ chế SQLAlchemy Execution Events.

<!-- nav:bottom -->
---

[⬅️ CI với GitHub Actions](../03-middle/12-ci-github-actions.md) | [📚 Dự án TaskFlow](./README.md) | [Senior ➡️](../04-senior/README.md)
<!-- /nav:bottom -->
