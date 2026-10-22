<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 09
<!-- /nav:top -->

# Phân trang, lọc & sắp xếp

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 08: Middleware, lifespan & background tasks](./08-middleware-lifespan-background.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Thiết kế mô hình phản hồi phân trang tổng quát kiểu **Generic Schema `Page[T]`** bằng Pydantic v2, tái sử dụng cho mọi thực thể trong hệ thống và tự động sinh OpenAPI Documentation chuẩn mực.
- So sánh toàn diện và chuyên sâu giữa hai kỹ thuật phân trang cốt lõi: **Offset-based Pagination** (truyền thống, nhảy trang tùy ý) và **Cursor / Keyset-based Pagination** (hiệu năng cao, chống trôi dữ liệu cho Infinite Scroll).
- Làm chủ kỹ thuật đếm tổng số bản ghi tối ưu bằng **`func.count()`** trong SQLAlchemy 2.0 mà không làm quá tải bộ nhớ RAM hay gây nghẽn CPU của Database Server.
- Xây dựng các câu truy vấn động an toàn bằng cách ghép nối linh hoạt các mệnh đề **`.where()`** trong SQLAlchemy 2.0 để xử lý bộ lọc đa tiêu chí (tìm kiếm từ khóa, lọc theo trạng thái, lọc theo khoảng thời gian).
- Triển khai cơ chế sắp xếp động an toàn tuyệt đối, triệt tiêu 100% nguy cơ **SQL Injection** trong mệnh đề `ORDER BY` bằng cách kết hợp `Literal`, `StrEnum` và bảng ánh xạ Whitelist.

---

## 🔁 So sánh với C# / ASP.NET

Trong các dự án ASP.NET Core sử dụng Entity Framework Core, việc xây dựng Extension Method cho `IQueryable<T>` để phân trang và sắp xếp là mẫu thiết kế rất quen thuộc. Dưới đây là bảng so sánh trực quan:

| Khái niệm / Thao tác | ASP.NET Core & EF Core (C#) | FastAPI & SQLAlchemy 2.0 (Python 3.12+) |
|---|---|---|
| **Generic Paged DTO** | `public class PagedResult<T> { public List<T> Items { get; set; } ... }` | Pydantic v2 Generic: `class Page[T](BaseModel): items: list[T] ...` |
| **Bỏ qua & Lấy số dòng** | `query.Skip(offset).Take(limit)` | `stmt.offset(offset).limit(limit)` |
| **Đếm tổng số dòng** | `await query.CountAsync()` | `await session.scalar(select(func.count()).select_from(subq))` |
| **Nối điều kiện lọc động** | `if (status.HasValue) query = query.Where(x => x.Status == status);` | `if status is not None: stmt = stmt.where(Task.status == status)` |
| **Tìm kiếm chuỗi không phân biệt hoa thường** | `EF.Functions.ILike(x.Title, $"%{keyword}%")` | `Task.title.ilike(f"%{keyword}%")` |
| **Chống SQL Injection khi Order By** | Sử dụng whitelist ánh xạ chuỗi sang Expression Selector (tránh dùng thư viện LINQ Dynamic không kiểm soát) | Định nghĩa tham số kiểu `Literal` và ánh xạ qua `dict[str, InstrumentedAttribute]` |
| **Cursor / Keyset Pagination** | `query.Where(x => x.Id > lastId).Take(limit)` | `stmt.where(Task.id > last_id).limit(limit)` |

---

## 📖 Lý thuyết

### 1. Thiết kế Schema phân trang Generic `Page[T]` với Pydantic v2

Thay vì tạo riêng `TaskPage`, `ProjectPage`, `UserPage`, chúng ta tận dụng tính năng Generic của Pydantic v2 kết hợp cú pháp Type Parameter hiện đại của Python 3.12 (PEP 695):

```python
import math
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T] = Field(description="Danh sách dữ liệu của trang hiện tại")
    total: int = Field(ge=0, description="Tổng số bản ghi thỏa mãn điều kiện")
    page: int = Field(ge=1, description="Chỉ số trang hiện tại (bắt đầu từ 1)")
    size: int = Field(ge=1, description="Số lượng bản ghi trên mỗi trang")
    pages: int = Field(ge=0, description="Tổng số trang khả dụng")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "Page[T]":
        total_pages = math.ceil(total / size) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )
```

Khi được khai báo làm `response_model=Page[TaskRead]`, FastAPI sẽ tự động sinh OpenAPI Schema riêng biệt mang tên `Page_TaskRead_` trong Swagger UI mà bạn không cần cấu hình thêm bất cứ điều gì.

### 2. So sánh Offset Pagination vs Keyset (Cursor) Pagination

```text
┌────────────────────────────────────────────────────────────────────────┐
│               OFFSET PAGINATION vs KEYSET (CURSOR) PAGINATION          │
│                                                                        │
│ 1. Offset Pagination: LIMIT 10 OFFSET 1000000                          │
│    - Cơ chế DB: Duyệt qua 1.000.010 dòng -> Vứt bỏ 1.000.000 dòng đầu │
│    - Độ phức tạp: O(N) theo giá trị Offset! Offset càng sâu càng chậm  │
│    - Rủi ro Trôi dữ liệu (Data Drift):                                 │
│      [Trang 1: xem 10 task]                                            │
│            │ (Có 2 task mới được chèn vào đầu bảng)                   │
│      [Trang 2: LIMIT 10 OFFSET 10]                                     │
│            ▼                                                           │
│      ⚠️ Người dùng bị thấy lại 2 task cuối cùng của Trang 1!           │
│                                                                        │
│ 2. Keyset / Cursor Pagination: WHERE id > 1000000 LIMIT 10            │
│    - Cơ chế DB: Nhảy thẳng đến B-Tree Index Seek tại id = 1000000      │
│    - Độ phức tạp: O(1) hoặc O(log N), tốc độ bất biến dù bảng 100 triệu │
│    - Không bao giờ bị trôi hoặc trùng lặp bản ghi                      │
│    - Nhược điểm: Không thể nhảy tùy ý đến "Trang số 50"                │
└────────────────────────────────────────────────────────────────────────┘
```

**Bảng so sánh lựa chọn kỹ thuật:**

| Tiêu chí | Offset Pagination (`page` & `size`) | Keyset / Cursor Pagination (`cursor` & `limit`) |
|---|---|---|
| **Trường hợp sử dụng lý tưởng** | Bảng quản trị nội bộ (Admin Dashboard), dữ liệu ít (< 100.000 dòng), người dùng cần nhảy trang tùy ý. | Bảng tin mạng xã hội, tin nhắn chat, Infinite Scroll trên Mobile app, bảng dữ liệu cực lớn. |
| **Độ phức tạp truy vấn** | $O(N)$ – Suy giảm nghiêm trọng ở các trang cuối. | $O(\log N)$ – B-Tree Index seek, tốc độ siêu nhanh và ổn định. |
| **Tính nhất quán khi có thêm/xóa** | Dễ bị trùng lặp hoặc sót bản ghi khi dữ liệu biến động liên tục. | Hoàn toàn nhất quán, không bao giờ bị lệch. |
| **Khả năng nhảy trang bất kỳ** | Hỗ trợ tự nhiên (`offset = (page - 1) * size`). | Khó hỗ trợ (chỉ có thể đi tới trang kế tiếp hoặc lùi lại). |

### 3. Xây dựng Query động an toàn trong SQLAlchemy 2.0

Trong SQLAlchemy 2.0, câu lệnh `select(Entity)` trả về một đối tượng `Select` bất biến (immutable-like builder). Chúng ta có thể dễ dàng ghép nối các điều kiện lọc thông qua phương thức `.where()`:

```python
from collections.abc import Sequence
from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskPriority, TaskStatus


async def filter_tasks(
    session: AsyncSession,
    *,
    project_id: int | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    search: str | None = None,
    created_after: datetime | None = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[Sequence[Task], int]:
    # 1. Khởi tạo câu lệnh gốc
    base_stmt = select(Task)

    # 2. Ghép nối điều kiện động
    if project_id is not None:
        base_stmt = base_stmt.where(Task.project_id == project_id)
    if status is not None:
        base_stmt = base_stmt.where(Task.status == status)
    if priority is not None:
        base_stmt = base_stmt.where(Task.priority == priority)
    if search:
        # Tìm kiếm theo từ khóa trong tiêu đề
        base_stmt = base_stmt.where(Task.title.ilike(f"%{search.strip()}%"))
    if created_after is not None:
        base_stmt = base_stmt.where(Task.created_at >= created_after)

    # 3. Đếm tổng số bản ghi tối ưu (chỉ đếm trên các điều kiện lọc, bỏ qua order/limit)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = await session.scalar(count_stmt) or 0

    # 4. Áp dụng phân trang và thực thi lấy dữ liệu
    paged_stmt = (
        base_stmt.order_by(Task.id.desc()).offset(offset).limit(limit)
    )
    items = (await session.scalars(paged_stmt)).all()

    return items, total
```

### 4. Sắp xếp động an toàn và phòng chống SQL Injection trong `ORDER BY`

Trong cơ sở dữ liệu quan hệ, **tên cột trong mệnh đề `ORDER BY` không thể truyền qua tham số bind parameter (Prepared Statement)**. Do đó, nếu lập trình viên nối chuỗi trực tiếp:
```python
# ❌ LỖ HỔNG SQL INJECTION CỰC KỲ NGUY HIỂM:
stmt = stmt.order_by(text(f"{sort_by} {order}"))
```
Kẻ tấn công có thể truyền `sort_by = "id; DROP TABLE tasks; --"` để phá hủy toàn bộ hệ thống!

**Giải pháp an toàn chuẩn doanh nghiệp (Whitelist Mapping):**
1. Dùng `Literal` hoặc `StrEnum` trong FastAPI để kiểm soát giá trị đầu vào hợp lệ ngay tại tầng OpenAPI Validation.
2. Dùng một bảng từ điển (`dict`) cố định để ánh xạ chuỗi đầu vào sang thuộc tính cột thực tế của SQLAlchemy:

```python
from enum import StrEnum
from typing import Literal
from sqlalchemy import asc, desc
from sqlalchemy.orm import InstrumentedAttribute
from app.models.task import Task


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


AllowedTaskSortFields = Literal["id", "title", "priority", "created_at"]

# Bảng Whitelist ánh xạ tuyệt đối an toàn
TASK_SORT_MAP: dict[AllowedTaskSortFields, InstrumentedAttribute] = {
    "id": Task.id,
    "title": Task.title,
    "priority": Task.priority,
    "created_at": Task.created_at,
}


def apply_sorting(
    stmt, sort_by: AllowedTaskSortFields, order: SortOrder
):
    column = TASK_SORT_MAP[sort_by]
    return stmt.order_by(asc(column) if order == SortOrder.ASC else desc(column))
```

---

## 💻 Ví dụ thực hành

Dưới đây là một mô-đun Router và Service hoàn chỉnh triển khai đầy đủ Phân trang, Lọc đa tiêu chí và Sắp xếp an toàn.

### 1. Định nghĩa Schemas: `app/schemas/common.py` & `app/schemas/task.py`

```python
from datetime import datetime
from enum import StrEnum
import math
from typing import Annotated, Generic, Literal, TypeVar
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field
from app.models.task import TaskPriority, TaskStatus

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "Page[T]":
        pages = math.ceil(total / size) if total > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


TaskSortField = Literal["id", "title", "priority", "status", "created_at"]


class TaskFilterParams(BaseModel):
    page: Annotated[int, Query(ge=1, description="Số thứ tự trang")] = 1
    size: Annotated[int, Query(ge=1, le=100, description="Kích thước trang")] = 10
    status: Annotated[TaskStatus | None, Query(description="Lọc theo trạng thái")] = None
    priority: Annotated[TaskPriority | None, Query(description="Lọc theo mức ưu tiên")] = None
    search: Annotated[str | None, Query(max_length=50, description="Tìm kiếm từ khóa")] = None
    sort_by: Annotated[TaskSortField, Query(description="Trường cần sắp xếp")] = "created_at"
    order: Annotated[SortOrder, Query(description="Thứ tự tăng/giảm dần")] = SortOrder.DESC


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
```

### 2. Triển khai Router: `app/api/v1/endpoints/tasks.py`

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.task import Task
from app.schemas.common import Page, SortOrder
from app.schemas.task import TaskFilterParams, TaskRead, TaskSortField

router = APIRouter(prefix="/tasks", tags=["Tasks"])

TASK_SORT_COLUMNS = {
    "id": Task.id,
    "title": Task.title,
    "priority": Task.priority,
    "status": Task.status,
    "created_at": Task.created_at,
}


@router.get("", response_model=Page[TaskRead])
async def list_tasks(
    params: Annotated[TaskFilterParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Page[TaskRead]:
    # 1. Xây dựng điều kiện lọc
    stmt = select(Task)
    if params.status is not None:
        stmt = stmt.where(Task.status == params.status)
    if params.priority is not None:
        stmt = stmt.where(Task.priority == params.priority)
    if params.search:
        stmt = stmt.where(Task.title.ilike(f"%{params.search.strip()}%"))

    # 2. Đếm tổng số bản ghi thỏa mãn
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await session.scalar(count_stmt) or 0

    # 3. Áp dụng sắp xếp an toàn
    sort_col = TASK_SORT_COLUMNS[params.sort_by]
    stmt = stmt.order_by(
        asc(sort_col) if params.order == SortOrder.ASC else desc(sort_col)
    )

    # 4. Phân trang
    offset = (params.page - 1) * params.size
    stmt = stmt.offset(offset).limit(params.size)

    # 5. Thực thi truy vấn
    result = await session.scalars(stmt)
    tasks = list(result.all())

    # 6. Chuyển đổi thành DTO và trả về cấu trúc Page
    task_dtos = [TaskRead.model_validate(t) for t in tasks]
    return Page.create(
        items=task_dtos,
        total=total,
        page=params.page,
        size=params.size,
    )
```

---

## ⚠️ Lỗi thường gặp

### 1. Dùng `len(items)` để tính tổng bản ghi thay vì `func.count()`

**Triệu chứng:** Khi dữ liệu tăng lên 50.000 dòng, API phản hồi cực kỳ chậm và tiến trình FastAPI bị máy chủ giết vì tràn bộ nhớ RAM (OOM Killer).

❌ **Sai lầm chết người:**
```python
# Tải toàn bộ 50.000 dòng từ Postgres lên RAM Python chỉ để lấy độ dài!
all_tasks = (await session.scalars(select(Task))).all()
total = len(all_tasks)
items = all_tasks[offset : offset + limit]
```

✅ **Giải pháp:** Luôn ủy thác việc đếm bản ghi cho Database Engine xử lý bằng `func.count()`:
```python
total = await session.scalar(select(func.count(Task.id)).where(...))
```

---

### 2. Quên xóa mệnh đề `ORDER BY` khi đếm số dòng (`subquery count`)

Nếu câu lệnh gốc chứa các phép sắp xếp phức tạp hoặc tốn kém:
```python
stmt = select(Task).order_by(Task.complex_computed_field)
count_stmt = select(func.count()).select_from(stmt.subquery())
```
PostgreSQL sẽ buộc phải thực hiện phép sắp xếp toàn bộ dữ liệu trước khi đếm, gây lãng phí tài nguyên CPU nghiêm trọng.
Luôn thực hiện đếm trước khi áp dụng `order_by` hoặc gọi `stmt.order_by(None)` trước khi tạo `subquery`.

---

### 3. Không đánh Index trên các cột thường xuyên được Lọc và Sắp xếp

Khi viết truy vấn `.where(Task.status == status).order_by(Task.created_at.desc())`, nếu bảng có hàng triệu dòng mà không có **Composite Index** trên `(status, created_at DESC)`, PostgreSQL buộc phải thực hiện quét toàn bộ bảng (**Sequential Scan**), biến API thành "rùa bò".

Định nghĩa Index trong SQLAlchemy Model:
```python
from sqlalchemy import Index


class Task(Base):
    __tablename__ = "tasks"
    # ...
    __table_args__ = (
        Index("ix_tasks_status_created_at", "status", "created_at"),
    )
```

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Endpoint Cursor / Keyset Pagination
Hãy viết một endpoint `GET /api/v1/tasks/cursor` hỗ trợ Keyset Pagination:
- Nhận vào `cursor: int | None = None` (chính là ID của bản ghi cuối cùng của trang trước) và `limit: int = 10`.
- Truy vấn lấy danh sách Task có `id > cursor` sắp xếp theo `id ASC`.
- Trả về cấu trúc:
  ```json
  {
    "items": [...],
    "next_cursor": 45,
    "has_more": true
  }
  ```

<details>
<summary>💡 Gợi ý</summary>

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.task import Task
from app.schemas.task import TaskRead


class CursorPageResponse(BaseModel):
    items: list[TaskRead]
    next_cursor: int | None
    has_more: bool


router = APIRouter()


@router.get("/tasks/cursor", response_model=CursorPageResponse)
async def list_tasks_cursor(
    session: Annotated[AsyncSession, Depends(get_db)],
    cursor: Annotated[int | None, Query(description="ID cuối của trang trước")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> CursorPageResponse:
    # Lấy dư thêm 1 bản ghi để kiểm tra xem có còn trang tiếp theo không
    stmt = select(Task)
    if cursor is not None:
        stmt = stmt.where(Task.id > cursor)

    stmt = stmt.order_by(Task.id.asc()).limit(limit + 1)
    results = list((await session.scalars(stmt)).all())

    has_more = len(results) > limit
    items = results[:limit]
    next_cursor = items[-1].id if items and has_more else None

    return CursorPageResponse(
        items=[TaskRead.model_validate(t) for t in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )
```
</details>

---

### Bài tập 2: Lọc dữ liệu theo khoảng thời gian (`date_from`, `date_to`)
Mở rộng `TaskFilterParams` để nhận thêm 2 trường tùy chọn: `created_from: datetime | None` và `created_to: datetime | None`.
- Kiểm tra logic: Nếu cả 2 cùng được truyền lên thì `created_from` phải nhỏ hơn hoặc bằng `created_to`. Nếu vi phạm, ném mã lỗi `422 Unprocessable Entity`.
- Áp dụng vào truy vấn SQLAlchemy để lọc chính xác các bản ghi trong khoảng ngày đó.

<details>
<summary>💡 Gợi ý</summary>

```python
from datetime import datetime
from typing import Self
from pydantic import BaseModel, model_validator


class DateRangeFilter(BaseModel):
    created_from: datetime | None = None
    created_to: datetime | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if (
            self.created_from
            and self.created_to
            and self.created_from > self.created_to
        ):
            raise ValueError(
                "Thời điểm bắt đầu (created_from) không được lớn hơn thời điểm kết thúc (created_to)."
            )
        return self
```
</details>

---

### Bài tập 3: Hỗ trợ sắp xếp đa tiêu chí (Multi-column Sorting)
Trong thực tế, người dùng có thể muốn sắp xếp: Ưu tiên Task theo độ khẩn cấp trước (`priority:desc`), nếu cùng độ ưu tiên thì sắp xếp theo ngày tạo mới nhất (`created_at:desc`).
Hãy sửa đổi logic sắp xếp để nhận một chuỗi `sort: str = "priority:desc,created_at:desc"` và sinh ra các mệnh đề `ORDER BY` tương ứng trong SQLAlchemy một cách an toàn.

<details>
<summary>💡 Gợi ý</summary>

```python
from fastapi import HTTPException
from sqlalchemy import asc, desc
from app.models.task import Task

ALLOWED_SORT_FIELDS = {
    "id": Task.id,
    "title": Task.title,
    "priority": Task.priority,
    "created_at": Task.created_at,
}


def parse_multi_sort(sort_query: str):
    order_clauses = []
    # Ví dụ format: "priority:desc,created_at:asc"
    parts = sort_query.split(",")
    for part in parts:
        segment = part.strip().split(":")
        field_name = segment[0].strip()
        direction = segment[1].strip().lower() if len(segment) > 1 else "asc"

        if field_name not in ALLOWED_SORT_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Trường sắp xếp '{field_name}' không hợp lệ. Cho phép: {list(ALLOWED_SORT_FIELDS.keys())}",
            )
        if direction not in ("asc", "desc"):
            raise HTTPException(
                status_code=400,
                detail=f"Thứ tự sắp xếp '{direction}' không hợp lệ. Chỉ cho phép 'asc' hoặc 'desc'.",
            )

        col = ALLOWED_SORT_FIELDS[field_name]
        order_clauses.append(asc(col) if direction == "asc" else desc(col))

    return order_clauses
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách định nghĩa Generic Schema `Page[T]` trong Pydantic v2 tái sử dụng cho toàn bộ API.
- [ ] Tôi phân biệt được ưu nhược điểm giữa Offset-based Pagination và Keyset Cursor Pagination.
- [ ] Tôi biết cách đếm số dòng tối ưu bằng `func.count()` kết hợp `subquery` trong SQLAlchemy 2.0.
- [ ] Tôi nắm vững kỹ thuật ghép nối mệnh đề `.where()` động an toàn cho các bộ lọc đa tiêu chí.
- [ ] Tôi giải thích được tại sao `ORDER BY` dễ bị SQL Injection và cách triệt tiêu bằng bảng ánh xạ Whitelist.

---

## 📚 Đọc thêm

- [Pydantic v2 Documentation – Generic Models](https://docs.pydantic.dev/latest/concepts/models/#generic-models)
- [SQLAlchemy 2.0 – Select Statements and Where Clauses](https://docs.sqlalchemy.org/en/20/core/selectable.html)
- [Use The Index, Luke! – No Offset: Keyset Pagination](https://use-the-index-luke.com/no-offset)
- [Tiếp theo: Bài 10 – Logging & xử lý lỗi toàn cục](./10-logging-error-handling.md)

<!-- nav:bottom -->
---

[⬅️ Middleware, lifespan & background tasks](./08-middleware-lifespan-background.md) | [📚 Mục lục Middle](./README.md) | [Logging & xử lý lỗi toàn cục ➡️](./10-logging-error-handling.md)
<!-- /nav:bottom -->
