<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 02
<!-- /nav:top -->

# SQLAlchemy 2.0 ORM

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 01: Async & asyncio](./01-async-asyncio.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Nắm vững 100% cú pháp hiện đại của **SQLAlchemy 2.0**: định nghĩa models bằng `DeclarativeBase`, `Mapped[...]`, và `mapped_column()`, loại bỏ hoàn toàn cú pháp cũ thời 1.x.
- Thiết lập hạ tầng kết nối cơ sở dữ liệu bất đồng bộ với **Async Engine** (`postgresql+asyncpg` / `sqlite+aiosqlite`) và **`AsyncSession`**.
- Hiểu thấu đáo nguyên nhân gốc rễ và tầm quan trọng sống còn của cờ **`expire_on_commit=False`** trong môi trường async để triệt tiêu hoàn toàn lỗi kinh điển `MissingGreenlet`.
- Soạn thảo và thực thi câu truy vấn 2.0 bằng câu lệnh **`select()`**, điều phối kết quả với **`session.scalars()`** và **`session.execute()`**.
- Giải quyết triệt để vấn nạn hiệu năng **N+1 Queries** trong môi trường async thông qua các chiến lược Eager Loading chuyên dụng: **`selectinload()`** (cho quan hệ 1-N / collections) và **`joinedload()`** (cho quan hệ N-1 / scalar objects).
- Tích hợp vòng đời `AsyncSession` chuẩn mực vào FastAPI bằng Dependency Injection với cú pháp `yield`.

---

## 🔁 So sánh với C# / ASP.NET

Nếu bạn đã từng làm việc với **Entity Framework Core (EF Core)** trong ASP.NET Core, bạn sẽ nhanh chóng nhận ra sự tương đồng đáng kinh ngạc giữa SQLAlchemy 2.0 và EF Core. Cả hai đều đi theo mô hình **Data Mapper Pattern** kết hợp **Unit of Work**:

| Khái niệm / Thành phần | Entity Framework Core (C#) | SQLAlchemy 2.0 Async (Python 3.12+) |
|---|---|---|
| **Phiên làm việc & Quản lý giao dịch** | `DbContext` (ví dụ: `AppDbContext`) | `AsyncSession` (tạo từ `async_sessionmaker`) |
| **Khai báo bảng / Model** | Lớp C# kế thừa POCO hoặc cấu hình qua `EntityTypeConfiguration<T>` | Lớp kế thừa `DeclarativeBase` với các thuộc tính `Mapped[T]` |
| **Cột cơ sở dữ liệu** | Thuộc tính C# (`public int Id { get; set; }`) | `id: Mapped[int] = mapped_column(primary_key=True)` |
| **Quan hệ giữa các bảng (Navigation)** | Thuộc tính navigation: `public List<Task> Tasks { get; set; }` | `tasks: Mapped[list["Task"]] = relationship(back_populates="project")` |
| **Xây dựng câu truy vấn** | LINQ to Entities: `context.Projects.Where(p => p.IsActive)` | Cú pháp `select()` 2.0: `select(Project).where(Project.is_active.is_(True))` |
| **Thực thi truy vấn** | `.ToListAsync()`, `.FirstOrDefaultAsync()` | `(await session.scalars(stmt)).all()`, `.first()` |
| **Chống N+1 / Eager Loading** | `.Include(p => p.Tasks)` | `.options(selectinload(Project.tasks))` |
| **Tracking đối tượng** | Change Tracker & Snapshot | Identity Map & Unit of Work bên trong `AsyncSession` |
| **Vòng đời trong Web Request** | `services.AddDbContext<AppDbContext>(ServiceLifetime.Scoped)` | `async def get_db() -> AsyncGenerator[AsyncSession, None]` inject qua `Depends()` |

---

## 📖 Lý thuyết

### 1. Cú pháp SQLAlchemy 2.0: Bước nhảy vọt về Type Safety

Trước phiên bản 2.0, SQLAlchemy sử dụng cú pháp 1.x với `Column()`, `Integer`, `String` thiếu hỗ trợ Type Hinting tĩnh, khiến IDE và `mypy` không thể phát hiện lỗi chính tả tên trường hay xung đột kiểu.

Trong SQLAlchemy 2.0, toàn bộ hệ thống được tái cấu trúc dựa trên **`typing.Mapped`** và **`mapped_column`**:

```python
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 1. Khai báo lớp Base kế thừa DeclarativeBase
class Base(DeclarativeBase):
    pass


# 2. Khai báo Model với Mapped[...]
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Quan hệ 1-N: 1 Project có nhiều Task
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    is_completed: Mapped[bool] = mapped_column(default=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    # Quan hệ N-1: Mỗi Task thuộc về 1 Project
    project: Mapped["Project"] = relationship(back_populates="tasks")
```

**Ưu điểm vượt trội của cú pháp 2.0:**
1. Kiểu dữ liệu Python (`int`, `str`, `datetime`, `bool`) tự động map sang kiểu cột SQL tương ứng (`INTEGER`, `VARCHAR`, `TIMESTAMP`, `BOOLEAN`).
2. `str | None` tự động đánh dấu cột SQL là `NULL` (`nullable=True`), trong khi `str` thuần túy mặc định là `NOT NULL` (`nullable=False`).
3. Khả năng tương thích 100% với Static Type Checking (`mypy`, `pyright`, Pylance trong VS Code).

### 2. Async Engine & AsyncSession: Vai trò sống còn của `expire_on_commit=False`

Để làm việc bất đồng bộ với cơ sở dữ liệu (ví dụ PostgreSQL), bạn cần cài SQLAlchemy kèm module `asyncio` (chứa thư viện `greenlet`) và driver async tương ứng (phổ biến nhất là `asyncpg`):

```bash
pip install "sqlalchemy[asyncio]" asyncpg
```

Sau đó khởi tạo engine và session maker:

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = "postgresql+asyncpg://postgres:secret@localhost:5432/taskflow_db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Bật True khi dev để debug log câu SQL sinh ra
    pool_size=10,  # Số kết nối duy trì trong pool
    max_overflow=20,  # Số kết nối tối đa mở thêm khi lưu lượng tăng đột biến
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # ⚠️ QUY TẮC SỐNG CÒN TRONG ASYNC!
)
```

#### Tại sao `expire_on_commit=False` lại quan trọng đến vậy?

Trong SQLAlchemy đồng bộ truyền thống:
- Khi bạn gọi `session.commit()`, SQLAlchemy mặc định đánh dấu toàn bộ các thuộc tính của instance là "hết hạn" (expired).
- Lần tiếp theo khi bạn đọc một thuộc tính (ví dụ: `print(task.title)` hoặc FastAPI serialize `task` trả về JSON), SQLAlchemy sẽ **ngầm phát ra một câu lệnh `SELECT` mới** để nạp dữ liệu tươi mới nhất từ DB.

Tuy nhiên, trong môi trường **Async**:
- Việc truy cập một thuộc tính Python (`task.title`) là một **phép toán đồng bộ thuần túy** (không có từ khóa `await`).
- Một hàm đồng bộ không thể kích hoạt lệnh I/O bất đồng bộ qua mạng. Khi SQLAlchemy cố gắng thực thi truy vấn ngầm này mà không có cơ chế chuyển đổi ngữ cảnh, hệ thống sẽ ném ngay ngoại lệ:
  `sqlalchemy.exc.MissingGreenlet: await_only() can only be called in the greenlet context`.
- **Giải pháp:** Thiết lập `expire_on_commit=False`. Khi đó, sau khi commit, các giá trị thuộc tính vừa lưu vẫn được giữ nguyên vẹn trong bộ nhớ Python, cho phép FastAPI serialize trả về client an toàn tuyệt đối mà không cần query lại.

### 3. Cú pháp truy vấn chuẩn 2.0: `select()` + `session.scalars()`

Trong SQLAlchemy 1.x, bạn dùng cú pháp `session.query(Project).filter(...)`. Cú pháp này đã chính thức bị khai tử trong môi trường async 2.0.

Cú pháp chuẩn 2.0 xây dựng câu lệnh SQL trừu tượng bằng hàm `select()`:

```python
from sqlalchemy import select

# 1. Khởi tạo câu lệnh truy vấn (Statement)
stmt = (
    select(Project)
    .where(Project.name.ilike("%fastapi%"))
    .order_by(Project.created_at.desc())
    .limit(10)
)

# 2. Thực thi bất đồng bộ qua AsyncSession
result = await session.scalars(stmt)

# 3. Lấy kết quả
projects: list[Project] = list(result.all())  # Lấy toàn bộ danh sách
# hoặc: project: Project | None = result.first()   # Lấy bản ghi đầu tiên
```

**Phân biệt `scalars()` vs `execute()`:**
- `session.execute(stmt)`: Trả về các dòng bản ghi dạng tuple (`Row[tuple[Project]]`). Phù hợp khi bạn `select(Project.id, Project.name, func.count(Task.id))` (chọn nhiều cột riêng lẻ).
- `session.scalars(stmt)`: Tự động trích xuất phần tử đầu tiên của mỗi Row tuple, trả về trực tiếp danh sách ORM entities (`Project`). Đây là phương thức bạn sử dụng 95% thời gian trong các API CRUD.

### 4. Vấn đề N+1 Query & Eager Loading trong Async

Xét tình huống bạn muốn lấy danh sách 10 dự án kèm theo toàn bộ công việc (Tasks) của từng dự án:

```python
stmt = select(Project).limit(10)
projects = (await session.scalars(stmt)).all()

for p in projects:
    # ❌ N+1 PROBLEM & MISSING GREENLET CRASH:
    print(f"Project: {p.name}, Số tasks: {len(p.tasks)}")
```

Trong async context, đoạn code trên sẽ sập ngay lập tức với lỗi `MissingGreenlet` vì `p.tasks` là quan hệ lazy-load ngầm.

Để giải quyết, bạn **bắt buộc phải sử dụng Eager Loading** thông qua các loading options của SQLAlchemy:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHIẾN LƯỢC EAGER LOADING                              │
│                                                                             │
│  1. selectinload (Khuyến nghị cho quan hệ 1-N, N-N / Collections)           │
│     - Phát 1 query lấy danh sách Projects:                                  │
│       SELECT * FROM projects LIMIT 10;                                      │
│     - Phát thêm 1 query duy nhất gom toàn bộ Tasks bằng IN:                 │
│       SELECT * FROM tasks WHERE project_id IN (1, 2, 3, ...);               │
│     -> Cực kỳ nhanh, không nhân bản dữ liệu, không làm phình RAM.           │
│                                                                             │
│  2. joinedload (Khuyến nghị cho quan hệ N-1, 1-1 / Scalar Parent)           │
│     - Phát 1 query duy nhất kết hợp LEFT OUTER JOIN:                         │
│       SELECT tasks.*, projects.* FROM tasks                                 │
│       LEFT OUTER JOIN projects ON projects.id = tasks.project_id;           │
│     -> Tối ưu khi query từ con lên cha (mỗi con chỉ có 1 cha).              │
└─────────────────────────────────────────────────────────────────────────────┘
```

Áp dụng trong code 2.0:

```python
from sqlalchemy.orm import joinedload, selectinload

# Eager load quan hệ 1-N (Tasks bên trong Project): DÙNG selectinload
stmt_projects = select(Project).options(selectinload(Project.tasks))
projects = (await session.scalars(stmt_projects)).all()

# Eager load quan hệ N-1 (Project của từng Task): DÙNG joinedload
stmt_tasks = select(Task).options(joinedload(Task.project))
tasks = (await session.scalars(stmt_tasks)).all()
```

---

## 💻 Ví dụ thực hành

Dưới đây là một mô-đun hoàn chỉnh kết nối cơ sở dữ liệu SQLite Async (tiện lợi cho dev/test không cần cài PostgreSQL) và thực hiện các thao tác CRUD chuẩn SQLAlchemy 2.0:

```python
import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import ForeignKey, String, func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

# 1. Khởi tạo Base và Models
class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    is_completed: Mapped[bool] = mapped_column(default=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    project: Mapped["Project"] = relationship(back_populates="tasks")


# 2. Cấu hình Async Engine & Sessionmaker
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Quan trọng!
)


# 3. Hàm tạo bảng cho môi trường demo / test
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 4. FastAPI Dependency cung cấp AsyncSession
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# 5. Các hàm thao tác dữ liệu chuẩn 2.0
async def create_project_with_tasks(session: AsyncSession) -> Project:
    project = Project(
        name="Lộ trình FastAPI Senior",
        tasks=[
            Task(title="Học Async/await"),
            Task(title="Làm chủ SQLAlchemy 2.0"),
            Task(title="Tích hợp JWT Auth"),
        ],
    )
    session.add(project)
    await session.flush()  # Đẩy dữ liệu để DB cấp ID nhưng chưa commit transaction
    return project


async def get_project_with_tasks(session: AsyncSession, project_id: int) -> Project | None:
    # Truy vấn kết hợp eager loading giải quyết N+1
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.tasks))
    )
    result = await session.scalars(stmt)
    return result.first()


async def main() -> None:
    await init_db()

    async with session_factory() as session:
        # Thêm mới
        created_p = await create_project_with_tasks(session)
        await session.commit()
        p_id = created_p.id

    async with session_factory() as session:
        # Đọc kèm eager load
        project = await get_project_with_tasks(session, p_id)
        if project:
            print(f"Dự án: {project.name}")
            print(f"Danh sách công việc ({len(project.tasks)} tasks):")
            for t in project.tasks:
                print(f"  - [{ 'x' if t.is_completed else ' ' }] {t.title}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## ⚠️ Lỗi thường gặp

### 1. Ngoại lệ `MissingGreenlet: await_only() can only be called in the greenlet context`
Đây là lỗi phổ biến số 1 của lập trình viên chuyển từ sync sang async ORM.
**Nguyên nhân:**
- Chưa cấu hình `expire_on_commit=False` trên `async_sessionmaker`, sau đó truy cập thuộc tính của model sau lệnh `await session.commit()`.
- Hoặc truy cập một thuộc tính relationship (như `project.tasks`) mà **quên không eager load** bằng `selectinload()` hoặc `joinedload()`.

**Cách khắc phục:**
1. Thêm `expire_on_commit=False` vào sessionmaker.
2. Luôn nạp sẵn dữ liệu quan hệ bằng `.options(selectinload(...))` ngay trong câu lệnh `select()`.

### 2. Sử dụng cú pháp legacy 1.x `session.query()` trong async
```python
# ❌ SAI: session.query không được hỗ trợ trên AsyncSession!
stmt = session.query(Project).filter(Project.id == 1)
```
**Cách khắc phục:** Luôn sử dụng cú pháp 2.0 `select()`:
```python
# ✅ ĐÚNG:
stmt = select(Project).where(Project.id == 1)
project = (await session.scalars(stmt)).first()
```

### 3. Dùng `joinedload` cho quan hệ Collection (1-N) gây nhân bản dữ liệu
Khi dùng `joinedload` trên bảng cha có 100 bảng con, câu lệnh `LEFT OUTER JOIN` sẽ nhân bản thông tin bảng cha thành 100 dòng trong kết quả mạng gửi về, làm lãng phí băng thông và CPU để parse dữ liệu.
**Quy tắc:**
- Quan hệ 1-N, N-N: Luôn dùng **`selectinload()`**.
- Quan hệ N-1, 1-1: Dùng **`joinedload()`**.

### 4. Quên gọi `await` trên các thao tác của `AsyncSession`
```python
# ❌ SAI:
session.commit()  # Trả về Coroutine Object, chưa commit thực sự!
# ✅ ĐÚNG:
await session.commit()
await session.rollback()
await session.flush()
await session.refresh(entity)
```

---

## ✍️ Bài tập thực hành

### Bài tập 1: Khai báo Model Quan hệ N-N giữa `Task` và `Tag`
Định nghĩa hai model `Task` và `Tag` cùng bảng trung gian `task_tags` theo chuẩn SQLAlchemy 2.0:
- Bảng `tasks`: `id` (int, PK), `title` (str, 200).
- Bảng `tags`: `id` (int, PK), `name` (str, 50, unique).
- Bảng trung gian `task_tags`: `task_id` (FK tới `tasks.id`, composite PK), `tag_id` (FK tới `tags.id`, composite PK).
- Thiết lập `relationship` `secondary` hai chiều giữa `Task` và `Tag`.

<details>
<summary>💡 Gợi ý</summary>

```python
from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


task_tag_association = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    tags: Mapped[list["Tag"]] = relationship(
        secondary=task_tag_association,
        back_populates="tasks",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    tasks: Mapped[list[Task]] = relationship(
        secondary=task_tag_association,
        back_populates="tags",
    )
```
</details>

---

### Bài tập 2: Viết truy vấn đếm số lượng công việc theo dự án
Viết hàm bất đồng bộ `get_projects_with_task_count(session: AsyncSession)`:
Yêu cầu:
1. Sử dụng `select()` kết hợp `func.count(Task.id)` và `outerjoin(Project.tasks)`.
2. Group by theo `Project.id`.
3. Trả về danh sách các tuple gồm `(Project, int)` đại diện cho Dự án và Số lượng Task tương ứng.

<details>
<summary>💡 Gợi ý</summary>

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_projects_with_task_count(
    session: AsyncSession,
) -> list[tuple[Project, int]]:
    stmt = (
        select(Project, func.count(Task.id).label("task_count"))
        .outerjoin(Project.tasks)
        .group_by(Project.id)
    )
    result = await session.execute(stmt)
    # Vì select nhiều cột/thực thể, dùng execute() rồi duyệt các dòng (row):
    return [(row[0], row[1]) for row in result.all()]
```
</details>

---

### Bài tập 3: Sửa lỗi `MissingGreenlet` và giải quyết N+1 trong mã nguồn
Cho đoạn code lỗi sau:
```python
# Đoạn code lỗi ban đầu:
async def get_all_completed_tasks_summary(session: AsyncSession):
    stmt = select(Task).where(Task.is_completed.is_(True))
    tasks = (await session.scalars(stmt)).all()
    # Truy cập task.project gây lỗi MissingGreenlet!
    return [{"task": t.title, "project": t.project.name} for t in tasks]
```
Hãy sửa lại hàm trên để:
1. Không bị lỗi `MissingGreenlet`.
2. Truy vấn dữ liệu hiệu quả chỉ trong 1 câu SQL duy nhất bằng phương pháp eager loading thích hợp.

<details>
<summary>💡 Gợi ý</summary>

Vì quan hệ từ `Task` tới `Project` là quan hệ N-1 (mỗi task chỉ có một project cha - scalar object), ta sử dụng chiến lược `joinedload()`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


async def get_all_completed_tasks_summary(
    session: AsyncSession,
) -> list[dict[str, str]]:
    stmt = (
        select(Task)
        .where(Task.is_completed.is_(True))
        .options(joinedload(Task.project))  # ✅ Eager load N-1 bằng LEFT JOIN
    )
    tasks = (await session.scalars(stmt)).all()
    return [{"task": t.title, "project": t.project.name} for t in tasks]
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách định nghĩa models 100% chuẩn cú pháp SQLAlchemy 2.0 bằng `DeclarativeBase`, `Mapped[...]`, và `mapped_column()`.
- [ ] Tôi giải thích được lý do tại sao phải cấu hình `expire_on_commit=False` trên `async_sessionmaker` và cách nó ngăn chặn ngoại lệ `MissingGreenlet`.
- [ ] Tôi sử dụng thành thạo câu lệnh `select()` kết hợp `session.scalars()` để thực hiện các truy vấn CRUD async.
- [ ] Tôi phân biệt được khi nào nên dùng `selectinload()` (quan hệ 1-N / collection) và khi nào nên dùng `joinedload()` (quan hệ N-1 / scalar object).
- [ ] Tôi biết cách thiết lập FastAPI dependency với `yield` để tự động quản lý commit/rollback và đóng `AsyncSession`.

---

## 📚 Đọc thêm

- [SQLAlchemy 2.0 Documentation – Unified Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [SQLAlchemy 2.0 – Asynchronous I/O Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Relationship Loading Techniques: Joined vs Select IN](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [Tiếp theo: Bài 03 – Alembic migrations](./03-alembic-migrations.md)

<!-- nav:bottom -->
---

[⬅️ Async & asyncio](./01-async-asyncio.md) | [📚 Mục lục Middle](./README.md) | [Alembic migrations ➡️](./03-alembic-migrations.md)
<!-- /nav:bottom -->
