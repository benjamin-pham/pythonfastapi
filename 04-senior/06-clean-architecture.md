<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 06
<!-- /nav:top -->

# Clean Architecture

> ⏱️ Thời lượng: ~4.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Repository & Service layer](../03-middle/04-repository-service-layer.md) và [Bài 01: Python internals & concurrency](./01-python-internals-concurrency.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Thấu hiểu triết lý Clean / Hexagonal Architecture (Ports & Adapters)**: Nắm vững Quy tắc phụ thuộc (The Dependency Rule) và cách cô lập hoàn toàn logic nghiệp vụ cốt lõi (Domain) khỏi các chi tiết kỹ thuật bên ngoài (Framework, Database, Third-party SDKs).
- **Triển khai kiến trúc theo phong cách Pythonic**: Tránh bẫy rập khuôn máy móc từ Java / C# (Over-engineering), tận dụng sức mạnh của dataclasses, Pydantic v2 và **`typing.Protocol`** (Structural Subtyping) để tạo nên kiến trúc vừa chặt chẽ vừa thanh thoát.
- **Xây dựng tầng Domain tinh khiết (Pure Python Domain)**: Thiết kế Entities, Immutable Value Objects, Domain Exceptions và Domain Services không bị ô nhiễm bởi bất kỳ decorator hay model của ORM nào.
- **Thiết kế Ports & Adapters chuẩn mực**: Phân tách rạch ròi Inbound Adapters (FastAPI Routers, CLI) và Outbound Adapters (SQLAlchemy Repositories, Redis Adapters, External Gateways) thông qua các giao ước Ports trừu tượng.
- **Nắm vững ranh giới đánh đổi (Trade-off Analysis)**: Phân định sáng suốt khi nào hệ thống thực sự cần Clean Architecture và khi nào kiến trúc 3 tầng (Router – Service – Repository) là đủ tốt, tuân thủ nghiêm ngặt nguyên lý **YAGNI** và **KISS**.

---

## 🔁 So sánh với C# / ASP.NET

Trong cộng đồng .NET, các mẫu kiến trúc Clean Architecture của Uncle Bob, Onion Architecture của Jeffrey Palermo, hay template chuẩn mực của Jason Taylor và Steve Smith (Ardalis) đã trở thành kim chỉ nam cho các dự án quy mô lớn:

| Khái niệm / Thành phần | .NET Clean Architecture (C#) | Clean Architecture Pythonic (Python 3.12+) |
|---|---|---|
| **Cấu trúc Projects / Folders** | Chia thành 4 Projects riêng biệt: `Domain.csproj`, `Application.csproj`, `Infrastructure.csproj`, `WebApi.csproj`. | Chia thành các packages bên trong một codebase: `domain/`, `application/`, `infrastructure/`, `presentation/`. |
| **Tầng Domain Core** | C# POCO classes, Rich Domain Models, Value Objects kế thừa `ValueObject` base class. | Pure Python `@dataclass(slots=True)` hoặc `BaseModel` không phụ thuộc framework, Value Objects bất biến (`frozen=True`). |
| **Định nghĩa Hợp đồng (Ports)** | Sử dụng C# `interface` tường minh (`ITaskRepository`, `IEmailSender`). | Sử dụng **`typing.Protocol`** (Duck typing kiểu tĩnh). Lớp adapter không cần kế thừa tường minh interface! |
| **Tầng Application / Use Cases** | MediatR Commands & Queries (`IRequest<T>`, `IRequestHandler<T>`), CQRS pattern. | Các hàm hoặc Use Case classes độc lập (`CreateTaskUseCase.execute(...)`). |
| **Tầng Infrastructure (Adapters)** | Entity Framework Core `DbContext`, cấu hình Fluent API, Repository implementations. | SQLAlchemy 2.0 ORM Mapped models, mapper chuyển đổi qua lại giữa ORM model và Domain entity. |
| **Cơ chế Tiêm phụ thuộc** | `IServiceCollection` đăng ký Scoped/Transient trong `Program.cs`. | FastAPI `Depends()` kết hợp Factory Functions lắp ráp Adapter vào Use Case. |
| **Nguy cơ Over-engineering** | Viết quá nhiều DTO, mapping 5 lần (Request $\to$ Command $\to$ Entity $\to$ ViewModel $\to$ Response). | Cố tình sao chép nguyên mẫu C# khiến code Python bị phình to, chậm chạp và mất đi tính biểu cảm vốn có. |

---

## 📖 Lý thuyết

### 1. Quy tắc phụ thuộc cốt tử (The Dependency Rule)

Trong cuốn sách Clean Architecture kinh điển của Robert C. Martin (Uncle Bob), mọi tầng của hệ thống được sắp xếp theo các vòng tròn đồng tâm:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CLEAN ARCHITECTURE CONCENTRIC                   │
│                                                                        │
│   [ Presentation / Inbound Adapters ] (FastAPI Routers, CLI)           │
│         │                                                              │
│         ▼                                                              │
│   [ Application / Use Cases ] (Điều phối quy trình nghiệp vụ)          │
│         │                                                              │
│         ▼                                                              │
│   [ Domain Layer ] (Entities, Value Objects, Domain Rules) ◄── CORE    │
│         ▲                                                              │
│         │ (Triển khai Ports)                                           │
│   [ Infrastructure / Outbound Adapters ] (SQLAlchemy, Redis, Stripe)   │
│                                                                        │
│   QUY TẮC BẤT DI BẤT DỊCH:                                            │
│   Mọi sự phụ thuộc (Source Code Dependencies) CHỈ ĐƯỢC PHÉP            │
│   HƯỚNG VÀO TRONG! Tầng bên trong KHÔNG BAO GIỜ biết tới tầng ngoài.   │
└────────────────────────────────────────────────────────────────────────┘
```

- **Domain** là hạt nhân trung tâm của vũ trụ: Nó không biết PostgreSQL là gì, không biết HTTP JSON là gì, và không import bất kỳ dòng nào từ FastAPI, SQLAlchemy hay Pydantic settings.
- **Infrastructure** và **Presentation** chỉ là các chi tiết kỹ thuật ở vòng ngoài cùng: Chúng có thể bị thay thế (ví dụ chuyển từ PostgreSQL sang DynamoDB, chuyển từ REST sang gRPC) mà không làm thay đổi dù chỉ một dòng code nghiệp vụ trong Domain!

---

### 2. Hexagonal Architecture: Ports & Adapters trong Python

Kiến trúc Lục giác (Hexagonal Architecture) của Alistair Cockburn diễn giải khái niệm này rất trực quan qua cặp đôi **Ports (Cổng)** và **Adapters (Bộ chuyển đổi)**:

```text
                      ┌─────────────────────────────────┐
                      │          APPLICATION            │
  FastAPI Router  ──► │ [Port Vào]                      │
  (Inbound Adapter)   │      Use Case (Execute)         │
                      │               │                 │
                      │               ▼                 │
                      │          DOMAIN CORE            │
                      │               │                 │
                      │ [Port Ra] ◄───┘                 │
                      └───────┬─────────────────────────┘
                              │
                              ▼
                      SQLAlchemy Repository
                      (Outbound Adapter)
```

1. **Ports (Cổng giao tiếp)**:
   - Là các bản hợp đồng trừu tượng (Contracts) do tầng Application hoặc Domain sở hữu.
   - Nó quy định: *"Để phục vụ nghiệp vụ này, tôi cần một cơ chế có khả năng lưu Task (`TaskRepositoryPort`) và một cơ chế gửi thông báo (`NotificationPort`)"*.
2. **Adapters (Bộ chuyển đổi)**:
   - Là các linh kiện hiện thực cụ thể cắm vào các Ports.
   - *Inbound Adapter*: Lắng nghe HTTP request từ người dùng, parse dữ liệu và gọi Use Case.
   - *Outbound Adapter*: Cắm vào `TaskRepositoryPort`, sử dụng SQLAlchemy AsyncSession để lưu dữ liệu xuống bảng `tasks` của PostgreSQL.

#### Sức mạnh của `typing.Protocol` trong Python
Nếu trong C# bạn bắt buộc phải dùng từ khóa `interface` và class phải khai báo kế thừa tường minh:
```csharp
public class SqlTaskRepository : ITaskRepository // Bắt buộc implements tường minh
```
Thì trong Python hiện đại (PEP 544), chúng ta sử dụng **`typing.Protocol`** (Structural Subtyping):
- Class adapter chỉ cần hiện thực đầy đủ các hàm có signature khớp với `Protocol`.
- **Không cần kế thừa tường minh!** Trình kiểm tra kiểu tĩnh (`mypy` / `pyright`) sẽ tự động xác nhận tính hợp lệ. Điều này giúp mã nguồn lỏng khớp (loosely coupled) tối đa và cực kỳ dễ viết Mock / In-Memory Adapter khi chạy Unit Tests.

---

### 3. Tầng Domain tinh khiết: Entities, Value Objects & Domain Exceptions

#### 3.1 Entities vs Value Objects
- **Value Object (Đối tượng giá trị)**:
  - Được định danh hoàn toàn bằng giá trị của các thuộc tính, **không có ID riêng**.
  - **Bắt buộc phải bất biến (Immutable)**: Sau khi tạo ra, không bao giờ được phép sửa đổi giá trị. Mọi phép toán phải trả về một Value Object mới.
  - Ví dụ: `Money(amount=100, currency="VND")`, `Address`, `DateRange`, `Email`.
  - Trong Python: Hiện thực hoàn hảo bằng `@dataclass(frozen=True, slots=True)`.
- **Entity (Thực thể)**:
  - Có một định danh duy nhất (`id`) theo suốt vòng đời, ngay cả khi các thuộc tính khác thay đổi.
  - Mang theo hành vi và các quy tắc nghiệp vụ (Business Invariants).
  - Ví dụ: Thực thể `Task` có hàm `assign_to(user_id)`, `complete()`.

#### 3.2 Tách biệt ORM Model khỏi Domain Entity
Đây là ranh giới phân biệt giữa kỹ sư Middle và Senior:
- Kỹ sư Middle thường dùng trực tiếp SQLAlchemy Model làm Domain Model (`class Task(Base): ...`). Khi đó, Domain Model bị trói chặt vào session state, lazy loading, greenlet context, và các kiểu cột của database.
- Kỹ sư Senior thiết kế:
  - **`domain.entities.Task`**: Pure Python dataclass chứa logic nghiệp vụ.
  - **`infrastructure.orm.models.TaskModel`**: SQLAlchemy declarative model chuyên trách việc map với bảng DB.
  - Repository Adapter làm nhiệm vụ chuyển đổi (mapping) qua lại giữa 2 đối tượng này.

---

### 4. Khi nào cần Clean Architecture vs 3-Tier Architecture?

Áp dụng Clean Architecture cho mọi dự án là một sai lầm chết người của sự cứng nhắc (Dogmatism). Hãy luôn phân tích bài toán dựa trên nguyên lý **YAGNI (You Aren't Gonna Need It)**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        MA TRẬN LỰA CHỌN KIẾN TRÚC                      │
│                                                                        │
│   Độ phức tạp Nghiệp vụ (Business Complexity)                          │
│        ▲                                                               │
│   Cao  │                             [ CLEAN / HEXAGONAL ]             │
│        │                             - Vòng đời dài (> 3-5 năm)        │
│        │                             - Logic nghiệp vụ phức tạp        │
│        │                             - Đội ngũ kỹ sư lớn (> 10 devs)   │
│        │                             - Độc lập Database / Third-party  │
│        │                                                               │
│   Thấp │  [ 3-TIER ARCHITECTURE ]                                      │
│        │  - CRUD APIs tiêu chuẩn                                       │
│        │  - MVP / Startups cần time-to-market nhanh                     │
│        │  - Đội ngũ nhỏ (1-5 devs)                                     │
│        └─────────────────────────────────────────────────────────►     │
│           Thấp                                              Cao        │
│                         Quy mô & Vòng đời Dự án                        │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Chọn 3-Tier (Router – Service – Repository)** khi:
   - Dự án là các API quản lý thông thường, 80% nghiệp vụ là CRUD (Create, Read, Update, Delete).
   - Database đã được chốt và gần như 100% không bao giờ thay đổi.
   - Cần hoàn thành tính năng nhanh chóng để kiểm chứng thị trường.
2. **Chọn Clean Architecture** khi:
   - Core Domain có các quy tắc tính toán phức tạp, nhiều ràng buộc chéo (ví dụ: Hệ thống bảo hiểm tính phí, Sàn giao dịch tài chính, Hệ thống Logistics định tuyến giao hàng).
   - Dự án có tuổi thọ nhiều năm, cần được bảo vệ trước sự lỗi thời của các thư viện bên thứ ba.
   - Cần tốc độ chạy Unit Test siêu tốc (chạy 1,000 tests trong 1 giây vì Domain không cần kết nối database).

---

## 💻 Ví dụ thực hành

Dưới đây là một dự án mẫu hoàn chỉnh thu nhỏ áp dụng Clean Architecture theo chuẩn Python 3.12+:

### 1. Tầng Domain: Entities, Value Objects & Exceptions

```python
# File: domain/exceptions.py
class DomainException(Exception):
    """Ngoại lệ gốc của Domain."""


class InvalidMoneyError(DomainException):
    pass


class TaskAlreadyCompletedError(DomainException):
    pass


# File: domain/value_objects.py
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Money:
    amount: float
    currency: str = "VND"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidMoneyError("Số tiền không được phép là số âm!")

    def add(self, other: Self) -> Self:
        if self.currency != other.currency:
            raise InvalidMoneyError(f"Không thể cộng 2 loại tiền tệ khác nhau: {self.currency} vs {other.currency}")
        return self.__class__(amount=self.amount + other.amount, currency=self.currency)


# File: domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@dataclass(slots=True)
class Task:
    id: int | None
    title: str
    budget: Money
    assignee_id: int | None = None
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def assign_to(self, user_id: int) -> None:
        """Quy tắc nghiệp vụ: Không được giao việc cho task đã hoàn thành."""
        if self.status == TaskStatus.DONE:
            raise TaskAlreadyCompletedError("Không thể giao một công việc đã hoàn thành!")
        self.assignee_id = user_id
        self.status = TaskStatus.IN_PROGRESS

    def mark_done(self) -> None:
        self.status = TaskStatus.DONE
```

---

### 2. Tầng Ports: Hợp đồng trừu tượng với `typing.Protocol`

```python
# File: application/ports.py
from typing import Protocol
from domain.entities import Task


class TaskRepositoryPort(Protocol):
    """Port trừu tượng cho thao tác lưu trữ Task."""

    async def get_by_id(self, task_id: int) -> Task | None:
        ...

    async def save(self, task: Task) -> Task:
        ...


class NotificationPort(Protocol):
    """Port trừu tượng cho việc thông báo tới người dùng."""

    async def notify_assignment(self, user_id: int, task_title: str) -> None:
        ...
```

---

### 3. Tầng Application: Use Cases điều phối quy trình

```python
# File: application/use_cases.py
from dataclasses import dataclass
from application.ports import NotificationPort, TaskRepositoryPort
from domain.entities import Task
from domain.exceptions import DomainException


class TaskNotFoundError(DomainException):
    pass


@dataclass(slots=True)
class AssignTaskCommand:
    task_id: int
    assignee_id: int


class AssignTaskUseCase:

    def __init__(
        self,
        task_repo: TaskRepositoryPort,
        notifier: NotificationPort,
    ) -> None:
        self.task_repo = task_repo
        self.notifier = notifier

    async def execute(self, cmd: AssignTaskCommand) -> Task:
        # 1. Truy xuất Task từ Repository Port
        task = await self.task_repo.get_by_id(cmd.task_id)
        if not task:
            raise TaskNotFoundError(f"Không tìm thấy công việc mang ID #{cmd.task_id}")

        # 2. Thực thi quy tắc nghiệp vụ trong Domain Entity
        task.assign_to(cmd.assignee_id)

        # 3. Lưu trạng thái mới qua Repository Port
        updated_task = await self.task_repo.save(task)

        # 4. Gửi thông báo qua Notification Port
        await self.notifier.notify_assignment(cmd.assignee_id, task.title)

        return updated_task
```

---

### 4. Tầng Adapters: Inbound (FastAPI) & Outbound (SQLAlchemy & Email)

```python
# File: infrastructure/adapters.py
import asyncio
from application.ports import NotificationPort, TaskRepositoryPort
from domain.entities import Money, Task, TaskStatus


# 1. Outbound Adapter: InMemory Repo (hoặc SQLAlchemy Repo)
class InMemoryTaskRepository(TaskRepositoryPort):

    def __init__(self) -> None:
        self._storage: dict[int, Task] = {}
        self._seq = 1

    async def get_by_id(self, task_id: int) -> Task | None:
        return self._storage.get(task_id)

    async def save(self, task: Task) -> Task:
        if task.id is None:
            task.id = self._seq
            self._seq += 1
        self._storage[task.id] = task
        return task


class EmailNotificationAdapter(NotificationPort):

    async def notify_assignment(self, user_id: int, task_title: str) -> None:
        print(f"[Email Adapter] Đang gửi email cho User #{user_id}: Bạn vừa được giao việc '{task_title}'.")
        await asyncio.sleep(0.01)


# 2. Inbound Adapter: FastAPI Router
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Container lắp ráp Dependency Injection
in_memory_repo_instance = InMemoryTaskRepository()


def get_task_repository() -> TaskRepositoryPort:
    # Ở production, bạn return SqlAlchemyTaskRepository(session)
    return in_memory_repo_instance


def get_notifier() -> NotificationPort:
    return EmailNotificationAdapter()


def get_assign_task_use_case(
    repo: Annotated[TaskRepositoryPort, Depends(get_task_repository)],
    notifier: Annotated[NotificationPort, Depends(get_notifier)],
) -> AssignTaskUseCase:
    return AssignTaskUseCase(task_repo=repo, notifier=notifier)


class AssignTaskRequest(BaseModel):
    assignee_id: int


class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    assignee_id: int | None
    budget_amount: float
    budget_currency: str


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task_endpoint(
    task_id: int,
    payload: AssignTaskRequest,
    use_case: Annotated[AssignTaskUseCase, Depends(get_assign_task_use_case)],
) -> TaskResponse:
    try:
        cmd = AssignTaskCommand(task_id=task_id, assignee_id=payload.assignee_id)
        task = await use_case.execute(cmd)
        return TaskResponse(
            id=task.id or 0,
            title=task.title,
            status=task.status.value,
            assignee_id=task.assignee_id,
            budget_amount=task.budget.amount,
            budget_currency=task.budget.currency,
        )
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TaskAlreadyCompletedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
```

---

## ⚠️ Lỗi thường gặp

### 1. Bê nguyên xi Boilerplate của Java/C# vào Python
Tạo hàng loạt các lớp không cần thiết: `ITaskService`, `TaskServiceImpl`, `TaskFactory`, `TaskBuilder`, `TaskDtoAssembler`. Trong Python, các hàm module, dataclasses, và default arguments đã giải quyết 90% các nhu cầu này. Hãy giữ cho code Python luôn thanh thoát, tự nhiên và dễ đọc.

### 2. Để lọt ORM Model hoặc Pydantic Request Model vào Tầng Domain
Một lỗi vi phạm Dependency Rule nghiêm trọng:
```python
# ❌ Ô NHIỄM DOMAIN:
from sqlalchemy.orm import DeclarativeBase


class Task(DeclarativeBase):  # Tầng Domain lại đi import thư viện ORM ở tầng ngoài!
    pass
```
Hoặc dùng `TaskCreateRequest` của FastAPI làm tham số truyền vào Domain Entity. Khi đó, nếu bạn đổi framework API hoặc đổi thư viện database, toàn bộ Domain Core sẽ bị vỡ vụn.

### 3. Gọi trực tiếp I/O hoặc HTTP Client trong Domain Entity / Value Object
Domain Entity chỉ được phép chứa các phép toán thuần túy (In-Memory Logic). Tuyệt đối không viết `await http_client.get(...)` hay `await session.execute(...)` bên trong hàm của Domain Entity. Mọi thao tác I/O phải được ủy thác cho tầng Application thông qua các Ports.

### 4. Áp dụng Clean Architecture cho ứng dụng CRUD nhỏ
Dựng đủ 4 tầng và hàng chục file Ports/Adapters chỉ cho một ứng dụng đọc ghi bảng cấu hình đơn giản. Hậu quả là đội ngũ kỹ sư mất gấp 3 lần thời gian phát triển chỉ để viết code chuyển đổi (boilerplate mapping) mà không thu lại được bất kỳ lợi ích nào.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Value Object bất biến `Money` có kiểm soát quy tắc kinh doanh
Thiết kế Value Object `Money` bằng `@dataclass(frozen=True, slots=True)`:
1. Thuộc tính: `amount: float`, `currency: str = "VND"`.
2. Kiểm tra `amount >= 0`, nếu âm ném ngoại lệ `InvalidMoneyError`.
3. Viết phương thức `multiply(factor: float) -> Money`: nhân số tiền với một hệ số (ví dụ tính thuế/chiết khấu).
4. Chứng minh tính bất biến (Immutable): Gán `m.amount = 500` sẽ ném ngoại lệ `FrozenInstanceError`.

<details>
<summary>💡 Gợi ý</summary>

```python
from dataclasses import FrozenInstanceError, dataclass


class InvalidMoneyError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    amount: float
    currency: str = "VND"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidMoneyError("Số tiền không thể âm!")

    def multiply(self, factor: float) -> "Money":
        if factor < 0:
            raise InvalidMoneyError("Hệ số nhân không thể âm!")
        return Money(amount=round(self.amount * factor, 2), currency=self.currency)


if __name__ == "__main__":
    m1 = Money(100_000, "VND")
    m2 = m1.multiply(1.1)  # Thêm 10% VAT
    print(f"Tiền gốc: {m1.amount}, Sau nhân: {m2.amount}")

    try:
        m1.amount = 200_000  # type: ignore
    except FrozenInstanceError:
        print("✅ Thành công: Value Object bất biến hoàn hảo!")
```
</details>

---

### Bài tập 2: Định nghĩa Repository Port bằng `typing.Protocol` và viết Unit Test siêu tốc
1. Định nghĩa `UserRepositoryPort` với 2 hàm `get_by_email(email: str)` và `save(user: User)`.
2. Triển khai `FakeInMemoryUserRepository` thỏa mãn Protocol trên bằng một dictionary in-memory.
3. Viết Unit Test cho Use Case `RegisterUserUseCase` mà không cần bất kỳ Docker container, SQLite hay mock framework nào, thời gian chạy dưới 10ms.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from dataclasses import dataclass
from typing import Protocol


@dataclass
class User:
    id: int | None
    email: str
    is_active: bool = True


class UserRepositoryPort(Protocol):

    async def get_by_email(self, email: str) -> User | None:
        ...

    async def save(self, user: User) -> User:
        ...


class FakeInMemoryUserRepository:

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.next_id = 1

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def save(self, user: User) -> User:
        if user.id is None:
            user.id = self.next_id
            self.next_id += 1
        self.users[user.email] = user
        return user


class RegisterUserUseCase:

    def __init__(self, repo: UserRepositoryPort) -> None:
        self.repo = repo

    async def execute(self, email: str) -> User:
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValueError("Email đã tồn tại trong hệ thống!")
        new_user = User(id=None, email=email)
        return await self.repo.save(new_user)


async def test_register_flow():
    fake_repo = FakeInMemoryUserRepository()
    use_case = RegisterUserUseCase(repo=fake_repo)

    user = await use_case.execute("senior@python.org")
    assert user.id == 1
    assert user.email == "senior@python.org"
    print("✅ Unit Test Clean Architecture chạy siêu tốc thành công!")


if __name__ == "__main__":
    asyncio.run(test_register_flow())
```
</details>

---

### Bài tập 3: Tách rời nghiệp vụ duyệt đơn thanh toán (ApproveOrderUseCase)
Xây dựng Use Case `ApproveOrderUseCase`:
1. Domain Entity `Order`: Trạng thái `PENDING`, `APPROVED`, `REJECTED`. Tổng giá trị `Money`.
2. Quy tắc nghiệp vụ trong Entity: Chỉ cho phép duyệt các đơn hàng ở trạng thái `PENDING` và có giá trị lớn hơn 0.
3. Use Case nhận `order_id`, gọi `OrderRepositoryPort.get_by_id`, thực thi hàm `order.approve()`, lưu lại qua repository và kích hoạt `PaymentGatewayPort.capture_funds(order_id, amount)`.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class OrderState(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"


@dataclass
class Order:
    id: int
    amount: float
    state: OrderState = OrderState.PENDING

    def approve(self) -> None:
        if self.state != OrderState.PENDING:
            raise ValueError("Chỉ có thể duyệt đơn hàng đang ở trạng thái chờ (PENDING)!")
        if self.amount <= 0:
            raise ValueError("Đơn hàng không có giá trị hợp lệ để duyệt!")
        self.state = OrderState.APPROVED


class OrderRepoPort(Protocol):

    async def get_order(self, order_id: int) -> Order | None:
        ...

    async def update_order(self, order: Order) -> None:
        ...


class PaymentGatewayPort(Protocol):

    async def capture_funds(self, order_id: int, amount: float) -> bool:
        ...


class ApproveOrderUseCase:

    def __init__(self, repo: OrderRepoPort, payment: PaymentGatewayPort) -> None:
        self.repo = repo
        self.payment = payment

    async def execute(self, order_id: int) -> Order:
        order = await self.repo.get_order(order_id)
        if not order:
            raise LookupError(f"Không tìm thấy Order #{order_id}")

        order.approve()
        await self.payment.capture_funds(order.id, order.amount)
        await self.repo.update_order(order)
        return order
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được Quy tắc phụ thuộc (The Dependency Rule) và vì sao tầng Domain phải hoàn toàn tinh khiết.
- [ ] Tôi biết cách dùng `typing.Protocol` để định nghĩa Ports mà không cần ép các Adapters kế thừa tường minh.
- [ ] Tôi phân biệt được Entity và Immutable Value Object (`@dataclass(frozen=True)`).
- [ ] Tôi hiểu vì sao không nên dùng trực tiếp SQLAlchemy Model làm Domain Model trong Clean Architecture.
- [ ] Tôi biết cách phân tích đánh đổi (Trade-off Analysis) để quyết định khi nào dùng Clean Architecture và khi nào kiến trúc 3-Tier là tối ưu.
- [ ] Tôi tránh được các phản mẫu Over-engineering sao chép rập khuôn từ Java/C# sang Python.

---

## 📚 Đọc thêm

- [Clean Architecture: A Craftsman's Guide to Software Structure and Design - Robert C. Martin](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/)
- [Architecture Patterns with Python (Cosmic Python) - Harry Percival & Bob Gregory](https://www.cosmicpython.com/)
- [PEP 544 – Protocols: Structural subtyping (static duck typing)](https://peps.python.org/pep-0544/)
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Tiếp theo: Bài 07 – Thiết kế API nâng cao](./07-advanced-api-design.md)

<!-- nav:bottom -->
---

[⬅️ WebSocket & SSE](./05-websockets-sse.md) | [📚 Mục lục Senior](./README.md) | [Thiết kế API nâng cao ➡️](./07-advanced-api-design.md)
<!-- /nav:bottom -->
