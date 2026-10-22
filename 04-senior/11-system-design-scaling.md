<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 11
<!-- /nav:top -->

# System design & scaling

> ⏱️ Thời lượng: ~4.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 10: Deploy production](./10-production-deployment.md) và [Clean Architecture](./06-clean-architecture.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Làm chủ tư duy Thiết kế Hệ thống Sẵn sàng Cao (High Availability - HA)**: Nhận diện và triệt tiêu mọi điểm nghẽn đơn độc (Single Point of Failure - SPOF), áp dụng định lý CAP và PACELC để đưa ra các quyết định đánh đổi kiến trúc sáng suốt giữa Tính nhất quán (Consistency) và Tính khả dụng (Availability).
- **Mở rộng Cơ sở dữ liệu quy mô lớn (Database Scaling)**: Thiết kế giải pháp phân tách Đọc/Ghi (Read/Write Splitting) với Primary và cụm Read Replicas; xử lý hiện tượng trễ nhân bản (Replication Lag) bảo đảm tính nhất quán "Read-Your-Own-Writes"; nắm vững nguyên lý Table Partitioning và Database Sharding.
- **Triển khai kiến trúc CQRS (Command Query Responsibility Segregation)**: Tách rời hoàn toàn luồng Ghi (Command) tập trung vào logic nghiệp vụ và tính toàn vẹn dữ liệu khỏi luồng Đọc (Query) được tối ưu hóa siêu tốc qua các mô hình đọc phi chuẩn hóa (Denormalized Read Models).
- **Giải quyết triệt để vấn đề Dual-Write bằng Transactional Outbox Pattern**: Thấu hiểu vì sao việc vừa ghi Database vừa bắn message sang Kafka/RabbitMQ luôn tiềm ẩn nguy cơ mất mát dữ liệu, từ đó làm chủ Transactional Outbox Pattern để bảo đảm chuyển giao tin nhắn chính xác ít nhất một lần (At-least-once delivery).
- **Bảo vệ hệ thống với Circuit Breaker Pattern**: Ngăn chặn tình trạng sập lan chuyền (Cascading Failure) khi các dịch vụ phụ thuộc của bên thứ ba bị nghẽn hoặc ngừng hoạt động.

---

## 🔁 So sánh với C# / ASP.NET

Trong các hệ thống phân tán quy mô lớn sử dụng C# / .NET, các mẫu thiết kế và công cụ sau đây thường là tiêu chuẩn vàng của giới kiến trúc sư:

| Khái niệm / Mẫu thiết kế | Hệ sinh thái C# / ASP.NET Core | Hệ sinh thái Python 3.12+ / FastAPI |
|---|---|---|
| **Resilience & Circuit Breaker** | Thư viện kinh điển **Polly** (tích hợp trực tiếp vào `HttpClientFactory` qua `AddResilienceHandler`). | Tự xây dựng State Machine đơn giản bằng Python hoặc sử dụng các thư viện như `circuitbreaker`, `tenacity`. |
| **CQRS & Messaging** | Thư viện **MediatR** chia `IRequest<T>` thành Command và Query; **MassTransit** hoặc **NServiceBus** trừu tượng hóa RabbitMQ / Azure Service Bus. | Thiết kế các Use Case classes riêng biệt (`CreateTaskCommand`, `GetTaskDetailQuery`); sử dụng `aiokafka` hoặc `aio-pika`. |
| **Read/Write Splitting** | Cấu hình 2 `DbContext` riêng biệt (`WriteDbContext` trỏ vào Master, `ReadDbContext` trỏ vào Replica với `AsNoTracking()`). | Triển khai Dynamic Routing Session trong SQLAlchemy 2.0 bằng cách override phương thức `get_bind` của `AsyncSession`. |
| **Transactional Outbox** | MassTransit tích hợp sẵn Outbox Pattern (`UseEntityFrameworkOutbox`); Debezium CDC đọc SQL Server CDC log. | Tự thiết kế bảng `outbox_events` commit chung transaction SQLAlchemy, kết hợp Background Poller hoặc Debezium đọc PostgreSQL WAL. |
| **Distributed Caching** | `IDistributedCache` tích hợp Redis hoặc NCache; hỗ trợ Cache Stampede qua `HybridCache` (.NET 9). | `redis.asyncio` kết hợp Distributed Lock (`SET NX EX`) hoặc thuật toán Probabilistic Early Expiration (XFetch). |

---

## 📖 Lý thuyết

### 1. Tính sẵn sàng cao (High Availability) & Các định lý nền tảng

Một hệ thống được xem là có Tính sẵn sàng cao (HA - thường đo bằng "số 9": 99.9% tức downtime ~8.7 giờ/năm, 99.99% tức downtime ~52 phút/năm) khi nó không có bất kỳ **Điểm nghẽn đơn độc (Single Point of Failure - SPOF)** nào:

```text
                                  [ User Requests ]
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │   Cloudflare / Layer 4 Load Balancer  │ (Dự phòng Active - Passive)
                      └───────────────────┬───────────────────┘
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
            [ API Pod 1 (K8s) ]                       [ API Pod 2 (K8s) ]
                     │                                         │
        ┌────────────┴────────────┐               ┌────────────┴────────────┐
        ▼                         ▼               ▼                         ▼
 [ Redis Primary ] ──► [ Redis Replica ]   [ DB Primary ] ──► [ DB Read Replicas ]
```

#### Định lý CAP & PACELC
- **Định lý CAP**: Trong một hệ thống phân tán có phân vùng mạng (Partition Tolerance - P là điều bắt buộc của thế giới thực), bạn chỉ có thể chọn một trong hai:
  - **CP (Consistency / Partition Tolerance)**: Hệ thống ưu tiên dữ liệu luôn luôn chính xác. Nếu mạng giữa các nút bị đứt, hệ thống thà từ chối phục vụ (trả về lỗi) chứ không trả về dữ liệu cũ (Ví dụ: Zookeeper, PostgreSQL, Etcd).
  - **AP (Availability / Partition Tolerance)**: Hệ thống ưu tiên luôn phản hồi cho người dùng, chấp nhận dữ liệu có thể tạm thời chưa được đồng bộ (Eventual Consistency - Ví dụ: Cassandra, DynamoDB).
- **Định lý PACELC**: Mở rộng từ CAP:
  - Nếu có **P**artition: Chọn giữa **A**vailability và **C**onsistency.
  - **E**lse (Khi mạng bình thường): Chọn giữa **L**atency và **C**onsistency (ví dụ: muốn đọc cực nhanh với độ trễ thấp thì chấp nhận đọc từ Cache/Replica có thể có độ trễ đồng bộ).

---

### 2. Mở rộng Cơ sở dữ liệu: Read/Write Splitting & Phân mảnh (Sharding)

Hầu hết các hệ thống trực tuyến (Web/Mobile) đều có tỷ lệ Đọc/Ghi chênh lệch rõ rệt (thường là 80%–90% lượt đọc, chỉ 10%–20% lượt ghi).

```text
                               [ FastAPI Application ]
                                    │             │
                1. INSERT/UPDATE/   │             │  2. SELECT Queries
                   DELETE (Ghi)     ▼             ▼     (Đọc dữ liệu)
                           ┌──────────────┐     ┌──────────────┐
                           │  DB PRIMARY  │     │ DB REPLICA 1 │
                           └──────┬───────┘     └──────────────┘
                                  │ Replication        ▲
                                  │ (Async / Stream)   │
                                  └────────────────────┴─── [ DB REPLICA 2 ]
```

#### Thách thức: Trễ nhân bản (Replication Lag) & Read-Your-Own-Writes
Quá trình sao chép dữ liệu từ Primary sang các Replicas thường diễn ra bất đồng bộ (Asynchronous Replication) và tốn từ vài chục đến vài trăm mili-giây.
- **Vấn đề**: Người dùng cập nhật tên của mình (`PATCH /profile` $\to$ ghi vào Primary thành công). Ngay sau đó trình duyệt tự động gọi `GET /profile` để lấy thông tin mới. Request đọc được điều hướng tới Replica đang bị trễ 200ms $\to$ Người dùng vẫn thấy tên cũ của mình!
- **Giải pháp: Nhất quán "Read-Your-Own-Writes"**:
  1. Sau khi thực hiện một lệnh Ghi, lưu vào Session/Cookie/Redis một mốc thời gian: `last_write_timestamp = now()`.
  2. Trong vòng $X$ giây tiếp theo (ví dụ 3–5 giây), mọi request đọc của người dùng đó sẽ được ưu tiên định tuyến thẳng về **Primary Database**. Hết khoảng thời gian đó, các request đọc mới được phân phối lại cho các Replicas.

#### Table Partitioning vs Database Sharding
- **Table Partitioning (Phân vùng trên cùng 1 Database Instance)**:
  - Chia một bảng khổng lồ (hàng trăm triệu dòng) thành các bảng vật lý nhỏ hơn dựa trên một tiêu chí (ví dụ: chia theo tháng `created_at` bằng PostgreSQL Declarative Partitioning).
  - Tối ưu hóa truy vấn: Database Engine tự động loại bỏ các partition không liên quan (Partition Pruning).
- **Database Sharding (Phân mảnh ngang qua nhiều Database Nodes)**:
  - Khi dữ liệu vượt quá dung lượng lưu trữ hoặc CPU/RAM của một máy chủ vật lý, dữ liệu được phân chia sang nhiều máy chủ DB hoàn toàn độc lập dựa trên một **Shard Key** (ví dụ: `hash(tenant_id) % num_shards`).

---

### 3. Kiến trúc CQRS & Tối ưu hóa luồng Đọc/Ghi

CQRS (Command Query Responsibility Segregation) phân tách rõ ràng trách nhiệm của hệ thống:

```text
                             ┌──────────────────────────────────┐
                             │       HTTP CLIENT REQUEST        │
                             └───────────────┬──────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
            [ COMMAND (Lệnh Ghi) ]                       [ QUERY (Lệnh Đọc) ]
        - CreateTask, UpdateStatus                 - GetTaskSummary, SearchDashboard
        - Thực thi nghiệp vụ phức tạp             - Không có logic nghiệp vụ
        - Bảo toàn ràng buộc toàn vẹn              - Bỏ qua các phép JOIN phức tạp
                       │                                           │
                       ▼                                           ▼
             [ RDBMS (PostgreSQL) ]                      [ Elastic / Read Model ]
              Chuẩn hóa 3NF (ACID)                      Denormalized View / Redis
                       │                                           ▲
                       │ (Domain Events / CDC)                     │
                       └─────────────────── SYNC ──────────────────┘
```

---

### 4. Vấn đề Dual-Write & Transactional Outbox Pattern

Khi kiến trúc của bạn cần phối hợp giữa Cơ sở dữ liệu và Message Broker:

```text
async def create_task(task_data):
    # 1. Lưu task vào Database
    await db.save(task)
    
    # 2. Bắn sự kiện sang Kafka / RabbitMQ
    await kafka_producer.send("task_created", task.dict())
```

#### Vì sao cách viết trên là "Bom nổ chậm"?
1. Nếu bước 1 thành công nhưng bước 2 bị sập (Kafka mất kết nối, timeout mạng) $\to$ Dữ liệu đã lưu vào DB nhưng các dịch vụ khác không hề biết để xử lý (Mất sự kiện vĩnh viễn!).
2. Nếu bạn đảo ngược: Bắn message sang Kafka trước rồi mới lưu DB. Nếu bước lưu DB bị lỗi ràng buộc Unique constraint $\to$ Sự kiện đã bắn đi khắp hệ thống trong khi dữ liệu thực tế không hề tồn tại trong DB (Dữ liệu ma / Ghost Data).

#### Giải pháp: Transactional Outbox Pattern
Tận dụng tính toàn vẹn **ACID Transaction** của Cơ sở dữ liệu quan hệ:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      MỘT DATABASE TRANSACTION DUY NHẤT                 │
│                                                                        │
│   1. INSERT INTO tasks (...) VALUES (...);                             │
│   2. INSERT INTO outbox_messages (id, event_type, payload, status)     │
│      VALUES ('evt_1', 'TASK_CREATED', '{...}', 'PENDING');             │
│                                                                        │
│   COMMIT TRANSACTION;  ◄── Cả hai CÙNG THÀNH CÔNG hoặc CÙNG THẤT BẠI!   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (Đọc dữ liệu từ bảng outbox)
                       ┌─────────────────────────┐
                       │  Outbox Poller Worker   │ (Hoặc Debezium CDC)
                       └────────────┬────────────┘
                                    │
                                    ▼
                         [ Kafka / RabbitMQ Broker ]
                                    │
                                    ▼
                   Đánh dấu status = 'PUBLISHED' trong outbox
```

---

### 5. Đánh Index PostgreSQL nâng cao & Giải mã Kế hoạch truy vấn EXPLAIN (ANALYZE, BUFFERS)

Chỉ số (Index) là vũ khí tối thượng của một Senior Backend Engineer khi tối ưu tầng dữ liệu. Đánh index bừa bãi sẽ làm chậm toàn bộ thao tác `INSERT/UPDATE` và lãng phí RAM, trong khi thiếu index sẽ khiến hệ thống bị sập vì Full Table Scan (Sequential Scan).

#### 5.1 Các loại Index trọng tâm trong PostgreSQL:
1. **B-Tree Composite Index & Leftmost Prefix Rule**:
   - Khi tạo index trên nhiều cột `CREATE INDEX idx_user_status_date ON tasks (user_id, status, created_at DESC);`, PostgreSQL chỉ có thể tận dụng index nếu câu lệnh `WHERE` lọc từ cột bên trái nhất (`user_id`).
   - Nếu bạn `SELECT ... WHERE status = 'DONE';`, index trên sẽ **hoàn toàn vô hiệu**!
2. **Partial Index (Chỉ mục một phần)**:
   - Thay vì đánh index toàn bộ 50 triệu bản ghi, chỉ đánh index các bản ghi cần truy vấn thường xuyên:
     ```sql
     CREATE INDEX idx_active_tasks ON tasks (user_id, created_at DESC)
     WHERE status = 'IN_PROGRESS';
     ```
   - Dung lượng index giảm đến 95%, toàn bộ index nằm trọn vẹn trong RAM (Shared Buffers), tốc độ đọc đạt mức tối đa.
3. **GIN Index (Generalized Inverted Index)**:
   - Dùng cho các cột `JSONB` hoặc tìm kiếm toàn văn bản (Full-text Search):
     ```sql
     CREATE INDEX idx_tasks_metadata ON tasks USING gin (metadata jsonb_path_ops);
     ```
   - Cho phép tìm kiếm thần tốc với toán tử `@>`: `WHERE metadata @> '{"priority": "URGENT"}'`.

#### 5.2 Đọc kế hoạch truy vấn với `EXPLAIN (ANALYZE, BUFFERS)`
Khi truy vấn chậm, đừng đoán mò. Hãy chạy trực tiếp `EXPLAIN (ANALYZE, BUFFERS)`:
- `Seq Scan`: Quét toàn bộ bảng $\to$ Cần xem xét thêm index phù hợp.
- `Index Scan` vs `Bitmap Index Scan`: `Index Scan` đọc trực tiếp từ Index đến Table Page; `Bitmap Index Scan` gom các con trỏ trang thành bitmap trước khi đọc, phù hợp khi số dòng khớp khá lớn.
- `Buffers: shared hit=421 read=12`: `shared hit` là số block 8KB đọc từ RAM cache; `read` là số block phải đọc từ ổ đĩa SSD. Mục tiêu của việc tối ưu là tăng tỷ lệ `shared hit` lên sát 100%!

---

### 6. Quản trị Connection Pooling quy mô lớn với PgBouncer

Mỗi kết nối vào PostgreSQL tương ứng với một tiến trình OS riêng biệt (`postgres: user db client`), tiêu tốn từ 5MB đến 10MB RAM và gây chi phí chuyển ngữ cảnh (Context Switching) đắt đỏ cho CPU.
- Một cụm Kubernetes gồm 50 API Pods $\times$ 10 workers = 500 connections $\to$ PostgreSQL bị nghẽn CPU và cạn RAM.
- **Giải pháp**: Đặt **PgBouncer** làm middleware gom kết nối (Connection Pooler) đứng trước PostgreSQL.

#### So sánh các chế độ Pooling của PgBouncer:
| Chế độ Pooling | Cơ chế hoạt động | Khuyến nghị sử dụng |
|---|---|---|
| **Session Pooling** | Gán chặt 1 PostgreSQL connection cho 1 client connection suốt thời gian client kết nối. | Không giải quyết được bài toán scale nhiều pods. |
| **Transaction Pooling** | Connection thực tế chỉ được mượn từ pool trong thời gian một Transaction (`BEGIN ... COMMIT`) diễn ra. Khi transaction kết thúc, connection được nhả lại ngay lập tức cho client khác! | **Khuyến nghị chuẩn cho REST API**. 2,000 client connections chỉ cần 50 PostgreSQL connections! |
| **Statement Pooling** | Mỗi câu lệnh SQL mượn một connection khác nhau. | Cấm dùng (không hỗ trợ multi-statement transaction). |

---

## 💻 Ví dụ thực hành

### 1. Phân tách Read/Write Replica Routing trong SQLAlchemy 2.0

Dưới đây là mô hình định tuyến truy vấn động (Dynamic Routing) trong SQLAlchemy 2.0: Tự động điều hướng các câu lệnh `SELECT` sang Replica và các lệnh `INSERT / UPDATE / DELETE` sang Primary:

```python
from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]


class RoutingAsyncSession(AsyncSession):
    """Session thông minh: Điều hướng SELECT sang Read Engine, các lệnh Ghi sang Write Engine."""

    def __init__(
        self,
        write_engine: AsyncEngine,
        read_engine: AsyncEngine,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Loại bỏ bind do async_sessionmaker tự động inject để tránh TypeError multiple values
        kwargs.pop("bind", None)
        super().__init__(bind=write_engine, *args, **kwargs)
        self.write_engine = write_engine
        self.read_engine = read_engine

    def get_bind(self, mapper=None, clause=None, **kw):  # type: ignore[override]
        # Nếu là câu lệnh SELECT thuần túy, định tuyến sang Read Replica
        if self._is_clean() and clause is not None and clause.is_select:
            return self.read_engine
        # Mọi thao tác có thay đổi trạng thái (Ghi/Xóa/Sửa) gửi về Primary
        return self.write_engine


# Khởi tạo 2 Engines độc lập
primary_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
replica_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

# Session Factory cung cấp Routing Session
session_factory = async_sessionmaker(
    class_=RoutingAsyncSession,
    sync_session_class=None,
    expire_on_commit=False,
    write_engine=primary_engine,
    read_engine=replica_engine,
)


async def example_usage() -> None:
    async with session_factory() as session:
        # Câu lệnh này sẽ tự động gắn vào Read Engine
        stmt = select(Task).where(Task.id == 1)
        _ = await session.scalars(stmt)
```

---

### 2. Triển khai Circuit Breaker Pattern bảo vệ dịch vụ bên ngoài

Mô hình State Machine chuẩn mực với 3 trạng thái: `CLOSED` (Bình thường), `OPEN` (Đang ngắt kết nối do lỗi liên tiếp), và `HALF_OPEN` (Thử nghiệm phục hồi):

```python
from __future__ import annotations

import time
from enum import StrEnum
from typing import Any


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Ném ra khi mạch đang mở để ngắt cuộc gọi ngay lập tức."""
    pass


class CircuitBreaker:

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def before_call(self) -> None:
        now = time.time()
        if self.state == CircuitState.OPEN:
            # Kiểm tra xem đã hết thời gian chờ phục hồi chưa
            if now - self.last_state_change > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
            else:
                raise CircuitBreakerOpenException(
                    "Circuit Breaker đang mở (OPEN). Lời gọi bị chặn để bảo vệ hệ thống."
                )

    def on_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def on_failure(self) -> None:
        self.failure_count += 1
        now = time.time()
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = now

    async def call(self, async_func, *args: Any, **kwargs: Any) -> Any:
        self.before_call()
        try:
            result = await async_func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as exc:
            self.on_failure()
            raise exc
```

---

### 3. Triển khai Transactional Outbox Pattern với SQLAlchemy 2.0

Bảo đảm tính nhất quán 100% giữa việc ghi dữ liệu nghiệp vụ và lưu vết sự kiện miền cần phát tán:

```python
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)


class OutboxMessage(Base):
    """Bảng lưu trữ các sự kiện cần gửi sang Message Broker."""
    __tablename__ = "outbox_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, PUBLISHED, FAILED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


async def create_task_with_outbox(
    session: AsyncSession,
    title: str,
    event_id: str,
) -> Task:
    """Tạo Task và ghi sự kiện vào Outbox trong CÙNG MỘT TRANSACTION."""
    async with session.begin():
        # 1. Thao tác nghiệp vụ chính
        new_task = Task(title=title)
        session.add(new_task)
        await session.flush()  # Sinh new_task.id

        # 2. Tạo sự kiện Outbox tương ứng
        domain_event = {
            "task_id": new_task.id,
            "title": new_task.title,
            "occurred_at": datetime.now(UTC).isoformat(),
        }
        outbox_entry = OutboxMessage(
            id=event_id,
            event_type="TASK_CREATED",
            payload=json.dumps(domain_event),
            status="PENDING",
        )
        session.add(outbox_entry)

        # Cả Task và OutboxMessage sẽ được COMMIT đồng thời tại đây!
    return new_task
```

---

## ⚠️ Lỗi thường gặp

### 1. Bẫy Dual-Write mà không dùng Outbox Pattern
Cố tình ghi CSDL rồi gọi trực tiếp `producer.send()`. Khi mạng bị ngắt giữa 2 bước, dữ liệu của bạn sẽ bị bất đồng bộ vĩnh viễn giữa các microservices. Không bao giờ tin tưởng vào mạng máy tính; luôn dùng **Transactional Outbox** hoặc Saga Pattern khi có sự tham gia của CSDL và Message Broker.

### 2. Vi phạm Read-Your-Own-Writes do Replication Lag
Sau khi user đổi mật khẩu hoặc cập nhật hồ sơ, trang web tự động refresh và gọi lệnh GET. Nếu request đọc bị gửi sang Read Replica đang bị lag, user sẽ thấy thông tin cũ và tưởng rằng thao tác của mình thất bại. Hãy điều hướng các request đọc ngay sau lệnh ghi về Primary DB trong một khoảng thời gian ngắn (ví dụ 3 giây).

### 3. Phân mảnh CSDL (Sharding) quá sớm
Nhiều kỹ sư vội vã triển khai Sharding khi dữ liệu mới chỉ có vài chục gigabytes. Sharding làm mất khả năng thực hiện phép `JOIN`, phá hủy tính toàn vẹn khóa ngoại (Foreign Keys) và làm phức tạp hóa các thao tác tổng hợp dữ liệu (Aggregations). Một máy chủ PostgreSQL được tinh chỉnh cấu hình tốt và đánh chỉ mục chuẩn xác hoàn toàn có thể phục vụ 1–2 Terabytes dữ liệu mà không cần Sharding!

### 4. Circuit Breaker thiếu trạng thái Half-Open
Nếu Circuit Breaker chỉ có 2 trạng thái `OPEN` và `CLOSED`, một khi đã mở (OPEN), nó sẽ không bao giờ biết khi nào dịch vụ bên ngoài đã khỏe lại để tự đóng mạch. Bắt buộc phải có trạng thái `HALF_OPEN` để cho phép một vài request thử nghiệm đi qua sau khoảng thời gian `recovery_timeout`.

### 5. Sử dụng Prepared Statements mặc định của asyncpg khi đi qua PgBouncer Transaction Mode
Driver `asyncpg` mặc định tự động chuẩn bị (prepare) và lưu cache câu lệnh SQL ở cấp kết nối. Khi kết nối qua PgBouncer ở chế độ Transaction Pooling, câu lệnh `PREPARE` ở transaction 1 được thực thi trên backend connection A, nhưng transaction tiếp theo có thể bị gán cho backend connection B (nơi chưa từng chạy prepare câu lệnh đó), gây lỗi nghiêm trọng `InvalidSqlStatementNameError: prepared statement "__asyncpg_stmt_1__" does not exist`.
- *Khắc phục*: Trong connection string hoặc `connect_args` của SQLAlchemy / asyncpg, bắt buộc phải tắt cache prepared statement:
  ```python
  engine = create_async_engine(
      DATABASE_URL,
      connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
  )
  ```

---

## ✍️ Bài tập thực hành

### Bài tập 1: Outbox Poller Worker với cơ chế Khóa bi quan (Pessimistic Locking)
Viết một hàm worker bất đồng bộ `poll_and_publish_outbox(session, message_broker)`:
1. Đọc tối đa 50 bản ghi `outbox_messages` có trạng thái `PENDING`.
2. Sử dụng khóa `with_for_update(skip_locked=True)` để nhiều workers có thể chạy song song mà không tranh chấp cùng một bản ghi.
3. Giả lập gửi message sang broker, sau đó cập nhật trạng thái bản ghi thành `PUBLISHED`.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def process_outbox_batch(session: AsyncSession, publisher_func) -> int:
    async with session.begin():
        # Lấy các messages đang chờ, bỏ qua các dòng đang bị worker khác khóa
        stmt = (
            select(OutboxMessage)
            .where(OutboxMessage.status == "PENDING")
            .order_by(OutboxMessage.created_at)
            .limit(50)
            .with_for_update(skip_locked=True)
        )
        result = await session.scalars(stmt)
        messages = list(result.all())

        if not messages:
            return 0

        # Mẹo Senior: Trong hệ thống throughput cực cao, việc giữ row-lock trong DB
        # xuyên suốt quá trình gọi mạng (publisher_func) có thể gây nghẽn Connection Pool
        # nếu broker bị lag. Khi đó, nên chia nhỏ thành 2 giai đoạn: lock và đánh dấu 'PROCESSING',
        # commit ngay, sau đó bắn mạng và cập nhật 'PUBLISHED' ở transaction thứ hai.
        for msg in messages:
            await publisher_func(msg.event_type, msg.payload)
            msg.status = "PUBLISHED"

        return len(messages)
```
</details>

---

### Bài tập 2: Cơ chế gắn cờ Session "Read-Your-Own-Writes"
Thiết kế một dependency `get_database_engine(request: Request)`:
1. Kiểm tra cookie hoặc header `X-Last-Write-Timestamp`.
2. Nếu thời gian ghi gần nhất cách thời điểm hiện tại dưới 5 giây $\to$ Buộc sử dụng `primary_engine` cho câu truy vấn đọc.
3. Nếu không $\to$ Sử dụng `replica_engine`.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import time
from fastapi import Request


def select_engine_for_request(
    request: Request,
    primary_engine: Any,
    replica_engine: Any,
    cooldown_seconds: float = 5.0,
) -> Any:
    last_write = request.cookies.get("last_write_at")
    if last_write:
        try:
            elapsed = time.time() - float(last_write)
            if elapsed < cooldown_seconds:
                return primary_engine
        except ValueError:
            pass
    return replica_engine
```
</details>

---

### Bài tập 3: Khung triển khai CQRS Handlers
Xây dựng cấu trúc tách rời cho 2 Use Cases:
1. `CreateTaskCommandHandler`: Nhận `CreateTaskCommand(title, user_id)`, kiểm tra nghiệp vụ, ghi vào bảng dữ liệu quan hệ, phát sinh Domain Event.
2. `GetTaskSummaryQueryHandler`: Nhận `GetTaskSummaryQuery(user_id)`, truy vấn trực tiếp từ bộ nhớ đệm Redis Read Model trả về JSON ngay lập tức mà không đụng tới RDBMS.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from redis.asyncio import Redis


@dataclass(frozen=True, slots=True)
class CreateTaskCommand:
    title: str
    user_id: str


@dataclass(frozen=True, slots=True)
class GetTaskSummaryQuery:
    user_id: str


class TaskQueryHandler:

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def handle(self, query: GetTaskSummaryQuery) -> dict[str, Any] | None:
        # Đọc trực tiếp mô hình phi chuẩn hóa từ Cache
        cached = await self.redis.get(f"view:user_tasks:{query.user_id}")
        if cached:
            return json.loads(cached)
        return {"tasks": [], "count": 0}
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi hiểu rõ bản chất định lý CAP và PACELC và biết cách giải thích các đánh đổi trong hệ thống phân tán.
- [ ] Tôi giải thích được nguyên nhân gây ra Replication Lag và cách thiết kế tính nhất quán Read-Your-Own-Writes.
- [ ] Tôi biết cách cấu hình Dynamic Routing Engine trong SQLAlchemy 2.0 để phân tách truy vấn Đọc và Ghi.
- [ ] Tôi hiểu vì sao Dual-Write trực tiếp vào Database và Message Broker là phản mẫu kiến trúc nguy hiểm.
- [ ] Tôi làm chủ mẫu thiết kế Transactional Outbox Pattern để bảo đảm chuyển giao tin nhắn tin cậy.
- [ ] Tôi hiểu nguyên lý hoạt động của 3 trạng thái trong Circuit Breaker Pattern (CLOSED, OPEN, HALF_OPEN).

---

## 📚 Đọc thêm

- [Designing Data-Intensive Applications (DDIA) - Martin Kleppmann](https://dataintensive.net/)
- [Microservices Patterns: With examples in Java - Chris Richardson (Transactional Outbox Pattern)](https://microservices.io/patterns/data/transactional-outbox.html)
- [PostgreSQL Documentation: Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [SQLAlchemy 2.0: Custom Session Routing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Tiếp theo: Bài 12 – Kỹ năng senior](./12-senior-soft-skills.md)

<!-- nav:bottom -->
---

[⬅️ Deploy production](./10-production-deployment.md) | [📚 Mục lục Senior](./README.md) | [Kỹ năng senior ➡️](./12-senior-soft-skills.md)
<!-- /nav:bottom -->
