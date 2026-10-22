<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 04
<!-- /nav:top -->

# Repository & Service layer

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 02: SQLAlchemy 2.0 ORM](./02-sqlalchemy-orm.md) và [Bài 03: Alembic migrations](./03-alembic-migrations.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Thấu hiểu sự nguy hại của kiến trúc nguyên khối thiếu phân tầng (**Fat Controller / Anemic Domain**) khiến mã nguồn khó kiểm thử, vi phạm nguyên lý Trách nhiệm đơn lẻ (Single Responsibility Principle) và khó bảo trì khi dự án phát triển.
- Nắm vững kiến trúc 4 tầng chuẩn mực cho Backend FastAPI: **Router** (Presentation), **Service** (Business Logic), **Repository** (Data Access), và **Unit of Work** (Transaction Coordination).
- Nằm lòng **Nguyên tắc vàng về Transaction**: Tuyệt đối không gọi `session.commit()` bừa bãi trong từng hàm của Repository; trao quyền kiểm soát ranh giới giao dịch (Transaction Boundary) cho Unit of Work hoặc Service layer.
- Triển khai thành thạo **Generic Repository** trong Python 3.12+ tận dụng cú pháp Generic mới (PEP 695).
- Tách rời hoàn toàn ngoại lệ HTTP (`HTTPException`) khỏi tầng nghiệp vụ bằng cách sử dụng **Domain Exceptions**.
- Lắp ráp cây phụ thuộc nhiều tầng một cách thanh thoát thông qua hệ thống **Dependency Injection (`Depends`)** của FastAPI.

---

## 🔁 So sánh với C# / ASP.NET

Trong hệ sinh thái .NET doanh nghiệp, kiến trúc phân tầng (N-Tier Architecture) kết hợp với mẫu thiết kế **Repository & Unit of Work** là một tiêu chuẩn gần như bắt buộc:

| Thành phần kiến trúc | ASP.NET Core (C#) | FastAPI (Python 3.12+) |
|---|---|---|
| **Presentation Layer (Web/API)** | `TaskController : ControllerBase` hoặc Minimal API routes | `APIRouter` với các hàm route handlers |
| **Data Transfer Objects (DTO)** | ViewModels / Record Request-Response DTOs | Pydantic v2 `BaseModel` Schemas (`TaskCreate`, `TaskResponse`) |
| **Business Logic Layer** | `TaskService : ITaskService` | `TaskService` class độc lập với HTTP |
| **Data Access Layer** | `TaskRepository : IRepository<Task>` | `TaskRepository` kế thừa `BaseRepository[Task]` |
| **Quản lý Transaction** | `IUnitOfWork.SaveChangesAsync()` | `UnitOfWork` async context manager (`async with uow:`) |
| **Cơ chế Tiêm phụ thuộc** | Đăng ký `AddScoped<ITaskService, TaskService>()` trong `Program.cs` | Kết nối các tầng tự nhiên qua `Depends()` của FastAPI |
| **Xử lý Ngoại lệ nghiệp vụ** | Ném Custom Domain Exception, bắt bằng Middleware hoặc Exception Filters | Ném Domain Exception trong Service, Router map sang `HTTPException` |

---

## 📖 Lý thuyết

### 1. Vấn nạn "Fat Router" trong các dự án nghiệp dư

Khi mới làm quen với FastAPI, nhiều người thường viết toàn bộ logic vào hàm xử lý route:

```python
# ❌ PHONG CÁCH "FAT ROUTER" - RẤT KHÓ DUY TRÌ & TEST:
@app.post("/projects")
async def create_project(data: ProjectCreate, session: Annotated[AsyncSession, Depends(get_db)]):
    # 1. Trực tiếp truy vấn SQL kiểm tra trùng lặp
    stmt = select(Project).where(Project.name == data.name)
    if (await session.scalars(stmt)).first():
        raise HTTPException(status_code=400, detail="Tên đã tồn tại")

    # 2. Tạo entity ORM
    project = Project(name=data.name)
    session.add(project)

    # 3. Logic nghiệp vụ phụ trợ: gửi email thông báo
    # 4. Commit session
    await session.commit()
    return project
```

**Hậu quả:**
- **Không thể Unit Test độc lập:** Muốn test một điều kiện nghiệp vụ đơn giản, bạn buộc phải khởi tạo HTTP Client và kết nối cơ sở dữ liệu thật.
- **Không tái sử dụng được:** Nếu sau này bạn cần tạo Project từ một Background Worker (Celery/ARQ), một CLI script hoặc một hàng đợi RabbitMQ, bạn không thể gọi lại route handler này được.
- **Vi phạm SRP:** Route vừa phải lo giải mã HTTP, vừa lo kiểm tra business rules, vừa quản lý transaction SQL.

### 2. Kiến trúc 4 tầng chuẩn mực

```text
┌────────────────────────────────────────────────────────┐
│              ROUTER (Presentation Layer)               │
│  - Nhận HTTP Request, Parse Body/Query qua Pydantic    │
│  - Ủy quyền xử lý cho Service                          │
│  - Map Domain Exception -> HTTP Status Code (400, 404) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              SERVICE (Business Logic Layer)            │
│  - Kiểm tra quy tắc nghiệp vụ (Domain Rules)           │
│  - Phối hợp giữa nhiều Repositories & External APIs    │
│  - Tuyệt đối không import Request hay HTTPException    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│          UNIT OF WORK (Transaction Coordinator)        │
│  - Quản lý vòng đời AsyncSession duy nhất              │
│  - async with uow: await uow.commit()                  │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
               ▼                          ▼
    ┌─────────────────────┐    ┌─────────────────────┐
    │ ProjectRepository   │    │ TaskRepository      │
    │ (Data Access Layer) │    │ (Data Access Layer) │
    │ - Chỉ CRUD Entity   │    │ - Chỉ CRUD Entity   │
    │ - CẤM commit()!     │    │ - CẤM commit()!     │
    └─────────────────────┘    └─────────────────────┘
```

1. **Router Layer**: Bộ điều phối giao tiếp mạng. Nhận JSON từ client, gọi Service, nhận kết quả và bọc vào Response Schema.
2. **Service Layer**: Trái tim của ứng dụng. Chứa toàn bộ "bí quyết kinh doanh" (business logic). Tầng này **hoàn toàn mù tịt về HTTP**: không biết request đến từ đâu, chỉ nhận dữ liệu thuần túy (Python objects / DTOs).
3. **Repository Layer**: Trừu tượng hóa việc lưu trữ. Chuyển đổi giữa Entity ORM và cơ sở dữ liệu. Nó đóng vai trò như một tập hợp đối tượng trong bộ nhớ (`collection-like interface`).
4. **Unit of Work (UoW)**: Đảm bảo nguyên tắc ACID. Duy trì một danh sách các đối tượng bị thay đổi trong một transaction và ghi xuống DB trong một lần commit duy nhất.

### 3. NGUYÊN TẮC VÀNG: Không gọi `session.commit()` trong Repository

Hãy hình dung một kịch bản thanh toán:
1. Trừ 100$ từ tài khoản A (`AccountRepository.update_balance`).
2. Cộng 100$ vào tài khoản B (`AccountRepository.update_balance`).

Nếu `AccountRepository` tự động gọi `await session.commit()` sau mỗi hàm:
- Bước 1 trừ tiền A thành công và **đã commit xuống DB**.
- Bước 2 bị mất mạng hoặc DB crash.
- **Hậu quả thảm họa:** Tài khoản A mất 100$, nhưng tài khoản B chưa nhận được tiền, và hệ thống **không thể rollback** bước 1 được nữa vì nó đã được commit vĩnh viễn!

👉 **QUY TẮC BẤT DI BẤT DỊCH:**
- Repository chỉ được dùng: `session.add()`, `session.delete()`, `await session.flush()`.
- **Chỉ có Unit of Work hoặc Service mới có quyền quyết định khi nào gọi `await session.commit()`** khi tất cả mọi thao tác nghiệp vụ thành công trọn vẹn!

### 4. Triển khai Generic Repository với Python 3.12+ (PEP 695)

Từ Python 3.12, bạn có thể khai báo Generic Class ngắn gọn bằng cú pháp `class BaseRepository[ModelT: Base]`:

```python
from collections.abc import Sequence
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base


class BaseRepository[ModelT: Base]:
    """Generic Repository cung cấp các thao tác CRUD cơ bản."""

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id_: Any) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelT]:
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.scalars(stmt)
        return result.all()

    def add(self, entity: ModelT) -> None:
        # Chỉ add vào session, KHÔNG COMMIT!
        self.session.add(entity)

    async def delete_by_id(self, id_: Any) -> bool:
        entity = await self.get_by_id(id_)
        if entity:
            await self.session.delete(entity)
            return True
        return False
```

---

## 💻 Ví dụ thực hành

Dưới đây là một ứng dụng quản lý dự án hoàn chỉnh, áp dụng trọn vẹn mô hình Router - Service - Repository - Unit of Work:

### 1. Định nghĩa Models và Domain Exceptions

```python
from datetime import datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="tasks")


# Domain Exceptions (Độc lập với HTTP)
class DomainError(Exception):
    """Lớp cha của mọi lỗi nghiệp vụ."""


class ProjectNameAlreadyExistsError(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Dự án với tên '{name}' đã tồn tại trong hệ thống.")


class ProjectNotFoundError(DomainError):
    def __init__(self, project_id: int) -> None:
        super().__init__(f"Không tìm thấy dự án với ID {project_id}.")
```

### 2. Tầng Data Access: Repositories & Unit of Work

> [!TIP]
> **Dịch chuyển ranh giới Transaction:** Trong bài học trước ([02. SQLAlchemy 2.0 ORM](./02-sqlalchemy-orm.md)), hàm `get_db()` tự động commit cuối mỗi request. Khi áp dụng kiến trúc phân tầng với Unit of Work, `get_db_session()` sẽ **không** commit tự động nữa — ranh giới commit thuộc về `UnitOfWork` để bảo toàn tính toàn vẹn nghiệp vụ (ACID) qua nhiều thao tác.

```python
from types import TracebackType
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, project_id: int) -> Project | None:
        return await self.session.get(Project, project_id)

    async def get_by_name(self, name: str) -> Project | None:
        stmt = select(Project).where(Project.name == name)
        result = await self.session.scalars(stmt)
        return result.first()

    def add(self, project: Project) -> None:
        self.session.add(project)


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, task: Task) -> None:
        self.session.add(task)


class UnitOfWork:
    """Điều phối transaction qua async context manager."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.projects = ProjectRepository(session)
        self.tasks = TaskRepository(session)
        self._committed = False

    async def __aenter__(self) -> Self:
        self._committed = False
        return self

    async def commit(self) -> None:
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self.session.rollback()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None or not self._committed:
            # Nếu có lỗi hoặc không gọi commit tường minh, tự động rollback để bảo toàn ACID
            await self.rollback()
```

### 3. Tầng Business Logic: Service Layer

```python
class ProjectService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create_project_with_starter_tasks(self, name: str) -> Project:
        """Nghiệp vụ: Tạo dự án mới và tự động tạo 1 task khởi động.

        Đảm bảo tính nguyên tử (Atomicity) qua Unit of Work.
        """
        async with self.uow:
            # 1. Kiểm tra quy tắc nghiệp vụ: Không được trùng tên
            existing = await self.uow.projects.get_by_name(name)
            if existing is not None:
                raise ProjectNameAlreadyExistsError(name)

            # 2. Tạo Project
            project = Project(name=name)
            self.uow.projects.add(project)
            # Flush để database cấp ID cho project trước khi tạo task con
            await self.uow.session.flush()

            # 3. Tạo Task mặc định thuộc về Project vừa tạo
            starter_task = Task(title="Khởi tạo tài liệu dự án", project_id=project.id)
            self.uow.tasks.add(starter_task)

            # 4. Khi tất cả các bước thành công -> COMMIT DUY NHẤT 1 LẦN
            await self.uow.commit()
            return project
```

### 4. Tầng Presentation: FastAPI Router & Dependency Injection

```python
from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Thiết lập engine & sessionmaker demo
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


def get_uow(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UnitOfWork:
    return UnitOfWork(session)


def get_project_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ProjectService:
    return ProjectService(uow)


# Schemas DTO
class ProjectCreateRequest(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# Router
router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_endpoint(
    payload: ProjectCreateRequest,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    try:
        project = await service.create_project_with_starter_tasks(payload.name)
        return ProjectResponse.model_validate(project)
    except ProjectNameAlreadyExistsError as exc:
        # Map Domain Exception sang HTTP 400 Bad Request
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
```

---

## ⚠️ Lỗi thường gặp

### 1. Gọi `session.commit()` bên trong Repository
```python
# ❌ LỖI NGHIÊM TRỌNG:
class UserRepository:
    async def create_user(self, user: User):
        self.session.add(user)
        await self.session.commit()  # ❌ Phá hủy khả năng phối hợp transaction của Service!
        return user
```
Nếu bạn cần tạo `User` và cấp phát một `UserProfile` hoặc tạo bản ghi audit log trong cùng một transaction, việc `UserRepository` tự ý commit sẽ khiến bạn không thể rollback nếu bước tiếp theo bị lỗi.

### 2. Ném `HTTPException` trực tiếp bên trong Service Layer
```python
# ❌ KHÔNG NÊN:
class ProjectService:
    async def get_project(self, project_id: int):
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Not found")  # Dính chặt vào Web!
```
**Lý do:** Tầng Service nên là mã nguồn Python thuần túy. Nếu bạn muốn sử dụng `ProjectService` bên trong một Celery background worker hoặc một script CLI terminal, mã nguồn sẽ phụ thuộc vô lý vào framework HTTP FastAPI. Hãy ném `ProjectNotFoundError` và để tầng Router xử lý mã HTTP.

### 3. Service rỗng (Anemic Passthrough Service)
Nhiều người tạo tầng Service chỉ để viết các hàm chuyển tiếp 1:1 vô nghĩa:
```python
# ❌ ANTI-PATTERN: Passthrough Service vô dụng
class TaskService:
    async def get_task(self, id: int):
        return await self.repo.get_by_id(id)
```
Nếu một thao tác chỉ đơn thuần là đọc dữ liệu theo ID mà không có bất kỳ logic kiểm tra quyền, transform dữ liệu hay quy tắc nghiệp vụ nào, việc tạo một hàm passthrough rỗng chỉ làm tăng số dòng code thừa (boilerplate). Hãy đảm bảo Service chỉ sinh ra khi có logic nghiệp vụ cần bảo vệ.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Generic Repository có phân trang
Cài đặt lớp `GenericRepository[T: Base]` trong Python 3.12+ hỗ trợ các phương thức:
- `get(id: int) -> T | None`
- `paginate(skip: int, limit: int) -> tuple[Sequence[T], int]`: Trả về một tuple gồm `(danh sách bản ghi, tổng số bản ghi)`.

<details>
<summary>💡 Gợi ý</summary>

```python
from collections.abc import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base


class GenericRepository[T: Base]:
    def __init__(self, model_cls: type[T], session: AsyncSession) -> None:
        self.model_cls = model_cls
        self.session = session

    async def get(self, id_: int) -> T | None:
        return await self.session.get(self.model_cls, id_)

    async def paginate(self, skip: int, limit: int) -> tuple[Sequence[T], int]:
        # 1. Đếm tổng số bản ghi
        count_stmt = select(func.count()).select_from(self.model_cls)
        total = (await self.session.scalar(count_stmt)) or 0

        # 2. Lấy dữ liệu trang hiện tại
        items_stmt = select(self.model_cls).offset(skip).limit(limit)
        items = (await self.session.scalars(items_stmt)).all()

        return items, total
```
</details>

---

### Bài tập 2: Xây dựng Unit of Work quản lý Repository đăng ký động
Viết lớp `AppUnitOfWork` cho phép truy cập các repositories theo dạng thuộc tính lazy: khi nào gọi tới `uow.users` thì mới khởi tạo `UserRepository(self.session)`.

<details>
<summary>💡 Gợi ý</summary>

```python
from functools import cached_property
from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession


class AppUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @cached_property
    def users(self) -> UserRepository:
        return UserRepository(self.session)

    @cached_property
    def projects(self) -> ProjectRepository:
        return ProjectRepository(self.session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.session.rollback()

    async def commit(self) -> None:
        await self.session.commit()
```
</details>

---

### Bài tập 3: Cài đặt Nghiệp vụ Hoàn thành Task có kiểm tra ràng buộc
Viết hàm `complete_task(task_id: int)` trong `TaskService`:
Quy tắc nghiệp vụ:
1. Tìm task theo `task_id`, nếu không có ném `TaskNotFoundError`.
2. Kiểm tra xem Project cha của task có còn hoạt động không (`project.is_active`). Nếu project đã bị vô hiệu hóa (`is_active == False`), ném `ProjectInactiveError("Không thể hoàn thành task của dự án đã đóng.")`.
3. Nếu hợp lệ, gán `task.is_completed = True` và commit qua Unit of Work.

<details>
<summary>💡 Gợi ý</summary>

```python
class TaskService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def complete_task(self, task_id: int) -> Task:
        async with self.uow:
            task = await self.uow.tasks.get_by_id(task_id)
            if task is None:
                raise TaskNotFoundError(task_id)

            project = await self.uow.projects.get_by_id(task.project_id)
            if project is None or not getattr(project, "is_active", True):
                raise ProjectInactiveError("Dự án chứa task này đã bị đóng.")

            task.is_completed = True
            await self.uow.commit()
            return task
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi hiểu rõ tác hại của kiến trúc "Fat Controller" và lợi ích khi phân chia 4 tầng Router - Service - Repository - Unit of Work.
- [ ] Tôi giải thích được tại sao TUYỆT ĐỐI KHÔNG được gọi `session.commit()` bên trong Repository.
- [ ] Tôi biết cách định nghĩa Domain Exceptions độc lập với HTTP để tầng Service không bị phụ thuộc vào framework Web.
- [ ] Tôi sử dụng thành thạo cú pháp Generic mới của Python 3.12 (`[T: Base]`) để xây dựng Base Repository.
- [ ] Tôi biết cách tổ chức Unit of Work dưới dạng Async Context Manager (`async with uow:`) để tự động rollback khi gặp sự cố.
- [ ] Tôi hiểu cách kết nối toàn bộ các tầng bằng Dependency Injection (`Depends`) của FastAPI.

---

## 📚 Đọc thêm

- [Cosmic Python: Architecture Patterns with Python (Repository & Unit of Work)](https://www.cosmicpython.com/book/chapter_02_repository.html)
- [Martin Fowler: Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/)
- [Tiếp theo: Bài 05 – Authentication với JWT](./05-authentication-jwt.md)

<!-- nav:bottom -->
---

[⬅️ Alembic migrations](./03-alembic-migrations.md) | [📚 Mục lục Middle](./README.md) | [Authentication với JWT ➡️](./05-authentication-jwt.md)
<!-- /nav:bottom -->
