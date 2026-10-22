<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 03
<!-- /nav:top -->

# Alembic migrations

> ⏱️ Thời lượng: ~3.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 02: SQLAlchemy 2.0 ORM](./02-sqlalchemy-orm.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ nguyên lý tiến hóa cơ sở dữ liệu (Database Schema Evolution) và vai trò của **Alembic** như một hệ thống kiểm soát phiên bản (Version Control) cho cấu trúc bảng dữ liệu.
- Khởi tạo thành công cấu trúc Alembic chuyên dụng cho môi trường bất đồng bộ bằng lệnh **`alembic init -t async migrations`**.
- Cấu hình file **`env.py`** chuẩn Production: nạp biến môi trường an toàn từ **`pydantic-settings`** (loại bỏ hoàn toàn việc hardcode credentials trong `alembic.ini`), liên kết **`target_metadata = Base.metadata`**, và thiết lập hàm **`run_async_migrations()`**.
- Tự động phát hiện thay đổi schema và sinh mã migration bằng lệnh **`alembic revision --autogenerate -m "..."`**.
- Nắm vững các **giới hạn chết người của `--autogenerate`** (không tự nhận diện đổi tên cột/bảng, hạn chế với PostgreSQL Enums và constraints) và hình thành phản xạ bắt buộc phải review code migration trước khi áp dụng.
- Thực thi nâng cấp database (**`alembic upgrade head`**) và rollback hạ cấp (**`alembic downgrade -1`**) một cách tự tin.

---

## 🔁 So sánh với C# / ASP.NET

Đối với các lập trình viên C# đã quen thuộc với bộ công cụ `dotnet ef`, Alembic mang lại trải nghiệm tương đồng gần như hoàn toàn về mặt tư duy và quy trình làm việc:

| Khái niệm / Tác vụ | EF Core Migrations (C#) | Alembic Migrations (Python) |
|---|---|---|
| **Công cụ dòng lệnh (CLI)** | `dotnet ef migrations` | `alembic` |
| **Khởi tạo hạ tầng migration** | Tích hợp sẵn trong EF Core Tools | `alembic init -t async migrations` |
| **Cấu hình chuỗi kết nối** | Đọc từ `appsettings.json` qua `DbContext` | Đọc từ file cấu hình / `pydantic-settings` trong `env.py` |
| **Nguồn đối chiếu Schema (Metadata)** | `DbContextModelSnapshot.cs` | `Base.metadata` (quét từ các lớp kế thừa `DeclarativeBase`) |
| **Tạo bản ghi migration mới** | `dotnet ef migrations add AddUserTable` | `alembic revision --autogenerate -m "add user table"` |
| **File sinh ra** | File C# với hai hàm `Up()` và `Down()` | File Python trong `versions/` với hai hàm `upgrade()` và `downgrade()` |
| **Áp dụng migration lên DB** | `dotnet ef database update` | `alembic upgrade head` |
| **Hạ cấp / Rollback** | `dotnet ef database update <PreviousMigrationName>` | `alembic downgrade -1` (hoặc `downgrade <revision_id>`) |
| **Bảng theo dõi phiên bản trong DB** | Bảng `__EFMigrationsHistory` | Bảng `alembic_version` (lưu mã hash `version_num`) |
| **Kiểm tra trạng thái hiện tại** | `dotnet ef migrations list` | `alembic current` và `alembic history --verbose` |

---

## 📖 Lý thuyết

### 1. Tại sao không dùng `Base.metadata.create_all()` trên Production?

Trong các bài hướng dẫn nhập môn hoặc môi trường kiểm thử unit test, bạn thường thấy lệnh:
```python
await conn.run_sync(Base.metadata.create_all)
```
**Tại sao điều này bị nghiêm cấm trên môi trường Production?**
- `create_all()` chỉ tạo các bảng chưa từng tồn tại.
- Nếu bạn thêm một cột mới, đổi kiểu dữ liệu cột, thêm chỉ mục (index) hoặc xóa một bảng cũ, `create_all()` **hoàn toàn bất lực và bỏ qua**.
- Bạn không có nhật ký lịch sử thay đổi, không thể quay ngược trạng thái (rollback) khi release gặp sự cố, và không thể đồng bộ cấu trúc database giữa các thành viên trong nhóm hoặc giữa môi trường Dev - Staging - Prod.

Alembic ra đời để giải quyết bài toán này: mỗi thay đổi schema được ghi lại dưới dạng một file mã nguồn Python (gọi là một **Revision**), được gán mã nhận diện duy nhất và lưu vết trong bảng `alembic_version`.

### 2. Khởi tạo Alembic với Async Template

Khi làm việc với SQLAlchemy 2.0 async (driver `asyncpg` hoặc `aiosqlite`), bạn cần khởi tạo Alembic với template bất đồng bộ:

```bash
# Cú pháp: alembic init -t async <tên_thư_mục>
alembic init -t async migrations
```

Cấu trúc thư mục được tạo ra:
```text
my_project/
├── alembic.ini              # File cấu hình chung của Alembic CLI
└── migrations/
    ├── README
    ├── script.py.mako       # File template mẫu dùng để sinh các file revision
    ├── env.py               # ⚠️ TRÁI TIM CỦA ALEMBIC: kịch bản cấu hình migration
    └── versions/            # Thư mục chứa các file migration (ban đầu rỗng)
```

### 3. Cấu hình `env.py` chuẩn Production với `pydantic-settings`

Mặc định, `alembic.ini` chứa một chuỗi kết nối mẫu `sqlalchemy.url = driver://user:pass@localhost/dbname`.
**Quy tắc bảo mật:** TUYỆT ĐỐI KHÔNG lưu thông tin tài khoản cơ sở dữ liệu nhạy cảm trong `alembic.ini` vì file này thường được đẩy lên Git repository.

Thay vào đó, ta sẽ chỉnh sửa file `migrations/env.py` để đọc chuỗi kết nối động từ module settings của dự án (ví dụ `app.core.config` sử dụng `pydantic-settings`):

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 1. Import cài đặt dự án và Base ORM Model
from app.core.config import settings
from app.models.base import Base
# BẮT BUỘC: Import toàn bộ models để Base.metadata nạp đầy đủ thông tin bảng
import app.models  # noqa: F401

config = context.config

# 2. Cấu hình logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Gán chuỗi kết nối từ settings (bỏ qua giá trị trong alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 4. Gán metadata của ORM để alembic --autogenerate quét và so sánh
target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    """Hàm chạy migration đồng bộ bên trong connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Bật kiểm tra thay đổi kiểu dữ liệu cột
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Tạo Async Engine và kết nối để chạy migration."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Dùng NullPool vì migration chạy xong là thoát
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_offline() -> None:
    """Chế độ offline: sinh câu lệnh raw SQL mà không cần kết nối DB thực tế."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chế độ online thông thường: kết nối trực tiếp vào DB."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 4. Quy trình làm việc với Migrations

```text
┌─────────────────────────┐
│ Sửa đổi SQLAlchemy ORM  │ (Thêm trường, tạo bảng mới trong models)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  alembic revision       │ Sinh file revision tự động trong migrations/versions/
│   --autogenerate -m "…" │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ ⚠️ CODE REVIEW BẮT BUỘC │ Mở file migration vừa sinh, kiểm tra kỹ lưỡng
│ (Human in the loop)     │ trước khi commit vào git!
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│   alembic upgrade head  │ Áp dụng các thay đổi lên cơ sở dữ liệu
└─────────────────────────┘
```

Các câu lệnh thường dùng:
- `alembic revision --autogenerate -m "create users and tasks tables"`: Tự động so sánh `Base.metadata` với schema hiện tại của DB và sinh file migration.
- `alembic upgrade head`: Áp dụng tất cả các migration mới nhất lên cơ sở dữ liệu.
- `alembic downgrade -1`: Rollback lùi lại đúng 1 bước migration gần nhất.
- `alembic current`: Hiển thị revision hash đang được áp dụng trên cơ sở dữ liệu.
- `alembic history`: Xem toàn bộ danh sách các revision theo thứ tự thời gian.

### 5. Những giới hạn chết người của `--autogenerate`

Mặc dù cờ `--autogenerate` rất thông minh, **nó không phải là chiếc đũa thần**. Có những tình huống Alembic hiểu sai hoàn toàn ý định của bạn:

#### Vấn đề 1: Đổi tên cột hoặc đổi tên bảng (Rename Column / Table)
Nếu bạn đổi tên thuộc tính `full_name` thành `display_name` trong Model:
- Alembic **KHÔNG THỂ BIẾT** bạn vừa đổi tên.
- Alembic sẽ phân tích thấy: thiếu cột `full_name` và xuất hiện cột `display_name` mới tinh.
- Kết quả trong file migration tự sinh:
  ```python
  # ❌ HẬU QUẢ: MẤT SẠCH DỮ LIỆU CỦA TOÀN BỘ NGƯỜI DÙNG TRONG CỘT ĐÓ!
  op.drop_column('users', 'full_name')
  op.add_column('users', sa.Column('display_name', sa.String(), nullable=False))
  ```
- **Cách khắc phục:** Bạn phải vào sửa tay file migration, thay thế bằng hàm `alter_column`:
  ```python
  # ✅ ĐÚNG: Giữ nguyên dữ liệu cũ, chỉ đổi tên cột
  op.alter_column('users', 'full_name', new_column_name='display_name')
  ```

#### Vấn đề 2: Kiểu Enum tùy chỉnh trong PostgreSQL
Khi thêm một cột kiểu Enum mới trên PostgreSQL, Alembic đôi khi quên sinh câu lệnh tạo kiểu `CREATE TYPE` trước khi tạo cột, dẫn đến lỗi `type "taskstatus" does not exist`. Bạn cần khai báo rõ `postgresql.ENUM` hoặc tạo type bằng `sa.Enum(..., name="taskstatus").create(op.get_bind())`.

#### Vấn đề 3: Check Constraints và tên Index
Alembic mặc định có thể không phát hiện một số thay đổi trong biểu thức check constraint hoặc không nhận biết được việc đổi tên index nếu index đó không có tên tường minh.

👉 **KẾT LUẬN:** File do `--autogenerate` sinh ra chỉ là **bản nháp gợi ý**. Trách nhiệm của kỹ sư là phải mở file đó ra, đọc từng dòng của cả hai hàm `upgrade()` và `downgrade()`, chỉnh sửa cho chuẩn xác rồi mới commit!

---

## 💻 Ví dụ thực hành

### 1. File cấu hình Settings tối giản (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./taskflow.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
```

### 2. Cấu trúc một file Migration thực tế (`versions/4f8a1b2c3d4e_create_users_table.py`)

Dưới đây là một file migration hoàn chỉnh do Alembic sinh ra và đã được kỹ sư tối ưu hóa:

```python
"""create users table

Revision ID: 4f8a1b2c3d4e
Revises:
Create Date: 2026-10-22 10:00:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

# Định danh revision được quản lý bởi Alembic
revision: str = '4f8a1b2c3d4e'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tạo bảng users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    # 2. Tạo chỉ mục tìm kiếm duy nhất cho email
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    # Thứ tự downgrade phải ngược lại với upgrade (xóa index trước, xóa bảng sau)
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên import các models vào `env.py`
Nếu bạn tạo model mới `Project` trong file `app/models/project.py`, nhưng trong `env.py` bạn chỉ `from app.models.base import Base` mà không import file `project.py`:
- `Base.metadata` hoàn toàn không hề biết đến sự tồn tại của bảng `projects`!
- Khi chạy `alembic revision --autogenerate`, Alembic sẽ nghĩ rằng bảng `projects` trong database là bảng thừa và sinh ra lệnh... `op.drop_table('projects')`!
**Cách khắc phục:** Tạo file `app/models/__init__.py` và import toàn bộ models tại đó (`from app.models.user import User`, `from app.models.project import Project`), sau đó trong `env.py` chỉ cần `import app.models`.

### 2. Xung đột nhánh "Multiple Heads" khi làm việc nhóm
Kịch bản:
- Dev A ở branch `feature/auth` sinh migration có revision `1111` trỏ về gốc `0000`.
- Dev B ở branch `feature/tasks` cũng sinh migration có revision `2222` trỏ về gốc `0000`.
- Khi cả hai merge code vào `main`, Alembic phát hiện có 2 revision cùng trỏ về 1 cha (2 heads) và từ chối chạy:
  `CommandError: Multiple head revisions are present for given argument 'head'`.

**Cách khắc phục:** Sử dụng lệnh `alembic merge` để tạo một revision hợp nhất:
```bash
alembic merge -m "merge auth and tasks branches" 1111 2222
alembic upgrade head
```

### 3. Hardcode mật khẩu cơ sở dữ liệu trong `alembic.ini`
File `alembic.ini` thường nằm ở thư mục gốc của dự án. Nếu bạn điền thẳng:
`sqlalchemy.url = postgresql+asyncpg://admin:super_secret_password@db.prod.com/prod_db`
Mật khẩu sản xuất sẽ bị lộ khi commit lên GitHub/GitLab.
**Cách khắc phục:** Để trống `sqlalchemy.url` trong `alembic.ini` và ghi đè giá trị này trong `env.py` bằng `config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)`.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Cấu hình `env.py` liên kết với Settings
Hãy viết hàm `get_database_url()` trong `env.py` để:
1. Đọc URL từ biến môi trường `DATABASE_URL`.
2. Nếu driver là `postgresql://` (thường được cấp bởi các nhà cung cấp như Heroku/Neon/Supabase mặc định), tự động chuyển đổi thành `postgresql+asyncpg://` để tương thích với async engine của SQLAlchemy 2.0.

<details>
<summary>💡 Gợi ý</summary>

```python
import os


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url
```
</details>

---

### Bài tập 2: Viết migration thêm cột `phone_number` an toàn
Viết hai hàm `upgrade()` và `downgrade()` của một file migration thủ công để:
1. Thêm cột `phone_number` (kiểu `String(20)`, có thể `NULL`) vào bảng `users`.
2. Tạo chỉ mục `ix_users_phone_number` cho cột vừa thêm.
3. Trong hàm `downgrade()`, xóa index trước rồi xóa cột.

<details>
<summary>💡 Gợi ý</summary>

```python
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(length=20), nullable=True))
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_column("users", "phone_number")
```
</details>

---

### Bài tập 3: Chỉnh sửa Migration Rename Column chống mất dữ liệu
Alembic vừa sinh ra một migration như sau khi bạn đổi tên trường `desc` thành `description` trong bảng `tasks`:
```python
# Đoạn code nguy hiểm do autogenerate sinh ra:
def upgrade():
    op.drop_column('tasks', 'desc')
    op.add_column('tasks', sa.Column('description', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('tasks', 'description')
    op.add_column('tasks', sa.Column('desc', sa.Text(), nullable=True))
```
Hãy viết lại hai hàm trên bằng `op.alter_column` để bảo toàn 100% dữ liệu đang có trong cơ sở dữ liệu.

<details>
<summary>💡 Gợi ý</summary>

```python
from alembic import op


def upgrade() -> None:
    # Đổi tên cột desc -> description an toàn
    op.alter_column("tasks", "desc", new_column_name="description")


def downgrade() -> None:
    # Đổi ngược lại khi rollback
    op.alter_column("tasks", "description", new_column_name="desc")
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi hiểu tại sao không được dùng `Base.metadata.create_all()` trên môi trường Production.
- [ ] Tôi biết cách khởi tạo Alembic với template async bằng `alembic init -t async migrations`.
- [ ] Tôi biết cách cấu hình `env.py` để lấy chuỗi kết nối an toàn từ `pydantic-settings` và gắn kết `Base.metadata`.
- [ ] Tôi nắm vững chu trình sinh migration bằng `alembic revision --autogenerate`, áp dụng bằng `upgrade head`, và rollback bằng `downgrade -1`.
- [ ] Tôi nhận thức rõ các giới hạn nguy hiểm của `--autogenerate` (đặc biệt là đổi tên cột/bảng) và luôn chủ động review code trước khi commit.
- [ ] Tôi biết cách xử lý xung đột Multiple Heads khi merge code bằng `alembic merge`.

---

## 📚 Đọc thêm

- [Alembic Official Documentation – Async Migration Tutorial](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)
- [Alembic Autogenerate: What does it detect and what does it NOT detect?](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Tiếp theo: Bài 04 – Repository & Service layer](./04-repository-service-layer.md)

<!-- nav:bottom -->
---

[⬅️ SQLAlchemy 2.0 ORM](./02-sqlalchemy-orm.md) | [📚 Mục lục Middle](./README.md) | [Repository & Service layer ➡️](./04-repository-service-layer.md)
<!-- /nav:bottom -->
