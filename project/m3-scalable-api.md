<!-- nav:top -->
[🏠 Home](../README.md) › [Dự án TaskFlow](./README.md) › M3
<!-- /nav:top -->

# M3 – Scalable API

> ⏱️ Thời lượng ước tính: 15–20 giờ thực hành độc lập · 📌 Yêu cầu trước: Hoàn thành [Milestone M2](./m2-production-api.md) và toàn bộ 12 bài học trong [Level 04: Senior](../04-senior/README.md).

---

## 🎯 Bối cảnh

Chào mừng bạn đến với **Milestone M3: Scalable Distributed API** – đồ án tốt nghiệp đỉnh cao của toàn bộ lộ trình kỹ sư backend Python & FastAPI.

Trong [Milestone M2](./m2-production-api.md), bạn đã xây dựng thành công một dịch vụ RESTful API hoàn chỉnh đạt tiêu chuẩn doanh nghiệp với cơ sở dữ liệu quan hệ PostgreSQL 17, cơ chế xác thực JWT kết hợp Argon2, phân quyền RBAC và kiểm soát sở hữu tài nguyên (BOLA Defense).

Tuy nhiên, khi dịch vụ **TaskFlow** tăng trưởng bùng nổ từ vài trăm người dùng lên đến **hàng trăm ngàn người dùng hoạt động đồng thời (High Concurrency)**, kiến trúc máy chủ đơn lẻ (Monolith) bắt đầu bộc lộ những điểm nghẽn nghiêm trọng:
- **Nghẽn Database Connection Pool**: Các câu truy vấn phân trang truyền thống `OFFSET 200000 LIMIT 20` gây quét toàn bộ bảng (Full Table Scan), chiếm dụng CPU của database và làm độ trễ p99 vọt lên hàng nghìn mili-giây.
- **Tắc nghẽn Event Loop vì tác vụ nặng**: Các yêu cầu xuất báo cáo Excel/CSV hàng triệu dòng và gửi email thông báo hàng loạt đang chạy trực tiếp trong tiến trình API chính, gây nghẽn tiến trình xử lý request của các người dùng khác.
- **Trùng lặp dữ liệu do lỗi mạng**: Khi kết nối mạng di động chập chờn, client tự động retry các request tạo task hoặc thanh toán gói dịch vụ khiến hệ thống tạo ra các bản ghi trùng lặp (thiếu cơ chế Idempotency).
- **Hệ thống Realtime không thể mở rộng đa Pods**: Kết nối WebSocket / SSE bị giới hạn trong bộ nhớ của từng Pod riêng biệt. Người dùng kết nối vào Pod A không thể nhận được sự kiện cập nhật công việc do người dùng ở Pod B thực hiện.
- **Mù mờ thông tin vận hành (Lack of Observability)**: Khi có lỗi xảy ra trên cụm microservices hoặc khi độ trễ tăng đột biến, đội ngũ vận hành không thể xác định được nguyên nhân xuất phát từ Database, Redis, mạng nội bộ hay dịch vụ bên thứ ba.

Trong **Milestone M3**, bạn sẽ đảm nhận vai trò **Senior Backend Architect**: Tái cấu trúc toàn diện TaskFlow theo mô hình **Clean / Hexagonal Architecture (Ports & Adapters)**, tích hợp cụm bộ nhớ đệm phân tán Redis, tách rời tác vụ nặng sang cụm Worker ARQ độc lập, mở rộng kết nối thời gian thực qua Redis Pub/Sub Backplane, thiết lập hệ thống quan sát OpenTelemetry và triển khai tự động co giãn trên Kubernetes.

---

## 📋 Yêu cầu chức năng

Hệ thống TaskFlow M3 kế thừa toàn bộ các chức năng quản lý Người dùng (`User`), Dự án (`Project`), và Công việc (`Task`) từ Milestone M2, đồng thời mở rộng thêm 4 phân hệ cấp cao:

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           KIẾN TRÚC PHÂN TÁN TASKFLOW M3                        │
│                                                                                 │
│   [ Client Requests ] ──► [ Cloudflare / Ingress Controller ]                   │
│                                      │                                          │
│        ┌─────────────────────────────┴─────────────────────────────┐            │
│        ▼ (HTTP / REST)                                             ▼ (Realtime) │
│   ┌─────────────────────────┐                                 ┌───────────────┐ │
│   │   FastAPI API Pods      │                                 │ WebSocket/SSE │ │
│   │   - Idempotency Guard   │ ◄─── Redis Pub/Sub Backplane ──►│ Connections   │ │
│   │   - Rate Limiter Lua    │                                 └───────────────┘ │
│   │   - Keyset Paginator    │                                                   │
│   └────────────┬────────────┘                                                   │
│                │                                                                │
│        ┌───────┴───────┬───────────────────────┐                                │
│        ▼               ▼                       ▼                                │
│   [ PostgreSQL ]  [ Redis Cache ]         [ ARQ Queue ]                         │
│   Primary/Replica (Cache-Aside + Locks)        │                                │
│                                                ▼                                │
│                                       [ ARQ Worker Pods ]                       │
│                                       - Export Báo cáo                          │
│                                       - Weekly Digest Cron                      │
│                                       - Gửi Email hàng loạt                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Phân hệ Idempotency & Distributed Rate Limiting

| Method | Endpoint | Headers bắt buộc | Mô tả nghiệp vụ |
|---|---|:---:|---|
| `POST` | `/api/v1/projects` | `Idempotency-Key` (UUID) | Tạo dự án mới. Nếu client gửi lại cùng key, trả về response cũ kèm header `X-Cache-Lookup: HIT-IDEMPOTENT`. |
| `POST` | `/api/v1/tasks` | `Idempotency-Key` (UUID) | Tạo task mới. Kiểm tra SHA-256 fingerprint của body; từ chối `422` nếu cùng key nhưng khác payload. |
| `POST` | `/api/v1/billing/subscriptions` | `Idempotency-Key` (UUID) | Nâng cấp gói tài khoản doanh nghiệp. Chống thanh toán trùng lặp khi retry. |

- **Quy tắc Rate Limiting phân tán (Redis Sliding Window)**:
  - Khách vãng lai (`Anonymous`): Giới hạn 30 requests / phút (theo IP).
  - Thành viên chuẩn (`MEMBER`): Giới hạn 150 requests / phút (theo User ID).
  - Quản trị viên / Doanh nghiệp (`ADMIN`): Giới hạn 1,000 requests / phút.
  - Phản hồi bắt buộc phải trả về các tiêu đề chuẩn IETF: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`. Khi vi phạm trả về `429 Too Many Requests` kèm `Retry-After`.

---

### 2. Phân hệ Phân trang Keyset Cursor cho Dữ liệu Lớn

| Method | Endpoint | Query Parameters | Mô tả |
|---|---|---|---|
| `GET` | `/api/v1/tasks` | `limit=20`, `cursor=<opaque_base64>` | Lấy danh sách công việc theo phân trang con trỏ (Keyset Cursor). Hỗ trợ tải vô hạn (Infinite Scroll) với độ phức tạp $O(1)$. |

- **Cấu trúc Con trỏ Opaque**:
  - Mã hóa Base64 an toàn URL từ tuple `(created_at, id)`: `base64(created_at_iso + "|" + task_id)`.
  - Phản hồi trả về `CursorPage[TaskRead]` gồm: `items: list[TaskRead]`, `next_cursor: str | None`, `has_more: bool`.
  - Tối ưu hóa Database: Đánh chỉ mục phức hợp `CREATE INDEX idx_tasks_created_id ON tasks (created_at DESC, id DESC);`.

---

### 3. Phân hệ Tác vụ ngầm Phân tán (Distributed Queue với ARQ)

| Method | Endpoint | Quyền hạn | Mô tả |
|---|---|:---:|---|
| `POST` | `/api/v1/projects/{id}/export` | Project Owner or `ADMIN` | Yêu cầu xuất toàn bộ dữ liệu công việc ra file nén zip chứa CSV/Excel. Đẩy job vào hàng đợi ARQ, trả về `job_id` và mã `202 Accepted`. |
| `GET` | `/api/v1/jobs/{job_id}` | Authenticated | Kiểm tra trạng thái xử lý của tác vụ nền (`QUEUED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`). Khi hoàn tất, cung cấp đường dẫn tải file an toàn. |

- **Yêu cầu đối với ARQ Worker**:
  - Tách thành tiến trình riêng biệt chạy độc lập với API Server.
  - Đảm bảo tính Idempotent cho Worker: Nếu một job bị ngắt giữa chừng và chạy lại, không phát sinh file rác hoặc ghi trùng dữ liệu.
  - Tự động thử lại với Exponential Backoff kèm Jitter khi gặp sự cố mạng (tối đa 3 lần).
  - Hỗ trợ Scheduled Cron Job: Tự động chạy vào lúc 08:00 sáng Thứ Hai hàng tuần để tổng hợp và gửi email báo cáo công việc (Weekly Digest) cho người dùng.

---

### 4. Phân hệ Thời gian thực Đa Pods (Realtime Backplane)

| Giao thức | Endpoint | Mô tả |
|---|---|---|
| **WebSocket** | `/ws/projects/{project_id}` | Kết nối 2 chiều phục vụ các thao tác tương tác thời gian thực trên Kanban Board. Xác thực kết nối qua Handshake Ticket hoặc Query Token. |
| **SSE** | `/api/v1/projects/{project_id}/events` | Kênh truyền 1 chiều (HTTP Streaming) phát tín hiệu thông báo công việc (Task Created, Task Updated, Task Assigned). |

- **Mở rộng đa Pods với Redis Pub/Sub**:
  - Khi một người dùng ở Pod 1 cập nhật trạng thái của Task, Pod 1 sẽ phát (Publish) thông điệp vào Redis Channel `project:{project_id}:events`.
  - Mọi Pod khác (Pod 2, Pod 3...) đang lắng nghe channel này sẽ lập tức nhận được message và đẩy (Broadcast) xuống các kết nối WebSocket/SSE đang mở tương ứng.

---

### 5. Phân hệ Bình luận (Comment) & Thông báo Tương tác

| Method | Endpoint | Quyền hạn | Mô tả |
|---|---|:---:|---|
| `POST` | `/api/v1/tasks/{task_id}/comments` | Project Member | Thêm bình luận vào công việc. Lưu `CommentEntity` vào database, đồng thời phát sự kiện `task.comment_created` lên Redis Pub/Sub để các thành viên đang mở board nhận cập nhật ngay lập tức, và enqueue job thông báo email qua ARQ. |
| `GET` | `/api/v1/tasks/{task_id}/comments` | Project Member | Lấy danh sách bình luận của task theo thứ tự thời gian tăng dần (`created_at ASC`). |
| `DELETE` | `/api/v1/comments/{comment_id}` | Comment Author / `ADMIN` | Xóa bình luận. |

---

## ⚙️ Yêu cầu kỹ thuật

Để hoàn thành xuất sắc Milestone M3, dự án bắt buộc phải thỏa mãn các tiêu chuẩn kiến trúc cấp Senior sau:

1. **Kiến trúc Clean / Hexagonal Architecture (Ports & Adapters)**:
   - **Tầng Domain Core**: Tinh khiết 100%, chỉ sử dụng `@dataclass(slots=True)` hoặc Pydantic BaseModel độc lập. Không import bất kỳ thư viện nào từ FastAPI, SQLAlchemy, Redis hay HTTPX.
   - **Tầng Ports**: Định nghĩa giao ước trừu tượng bằng **`typing.Protocol`** (Structural Subtyping):
     - `TaskRepositoryPort`, `ProjectRepositoryPort`, `CommentRepositoryPort`
     - `CachePort`
     - `JobQueuePort`
     - `NotificationPort`
   - **Tầng Adapters**: Hiện thực cụ thể các Ports:
     - Inbound: FastAPI Routers, WebSocket Endpoints.
     - Outbound: SQLAlchemy 2.0 Async Repositories, Redis Cache Adapter, ARQ Adapter.
2. **Hệ thống Caching Phân tán Bền bỉ**:
   - Triển khai chiến lược Cache-Aside cho chi tiết Task và Project Summary.
   - **Chống Cache Stampede**: Áp dụng Redis Distributed Lock (`SET NX EX`) khi nạp cache rỗng.
   - **Chống Cache Avalanche**: Bổ sung TTL Jitter ngẫu nhiên (dao động $\pm 10\%$).
   - **Chống Cache Penetration**: Lưu trữ giá trị rỗng (Null Caching) với TTL ngắn (60 giây) cho các ID không tồn tại.
3. **Bảo mật OWASP API Top 10 Toàn diện**:
   - Triệt tiêu lỗ hổng BOLA (API1:2023) ở mức Service/Repository.
   - Chống Mass Assignment (API3:2023) với `ConfigDict(extra="forbid")`.
   - Chống SSRF (API7:2023) cho tính năng Webhook: Phân giải DNS, cấm các dải IP nội bộ (`ip.is_private`, `ip.is_loopback`, `169.254.169.254`), timeout nghiêm ngặt và không tự động chuyển hướng (`follow_redirects=False`).
   - Cấu hình Middleware chèn Security Headers (HSTS, CSP, X-Frame-Options: DENY, nosniff).
4. **Khả năng quan sát (Observability)**:
   - Tích hợp **OpenTelemetry (OTel)** tự động đo đạc FastAPI, SQLAlchemy, Redis, và HTTPX.
   - Xuất bản Prometheus Metrics qua `/metrics`: Đo đạc Latency Histogram, Requests Counter, Active Connections Gauge.
   - Structured JSON Logging tự động đính kèm `trace_id` và `span_id`.
5. **Đóng gói & Kiểm thử tải**:
   - Multi-stage Dockerfile tối ưu kích thước bằng `uv`, chạy dưới quyền `appuser` (UID 10001) với `tini`.
   - Kubernetes manifests đầy đủ: `Deployment`, `Service`, `HPA`, `ConfigMap`, `Secret`, phân tách rõ ràng `livenessProbe` và `readinessProbe`.
   - Kịch bản kiểm thử tải với **Locust** chứng minh hệ thống đạt tối thiểu **1,000 RPS** với p99 latency dưới 150ms.

---

## 📁 Gợi ý cấu trúc thư mục

Dự án TaskFlow M3 được tổ chức chuẩn hóa theo phong cách Pythonic Clean Architecture:

```text
taskflow-scalable/
├── .github/
│   └── workflows/
│       └── ci.yaml                       # CI Pipeline: Lint (ruff), Typecheck (mypy), Tests (pytest)
├── k8s/
│   ├── deployment.yaml                   # Kubernetes Deployment & Pod specs
│   ├── service.yaml                      # K8s ClusterIP Service
│   ├── hpa.yaml                          # Horizontal Pod Autoscaler (3 -> 20 pods)
│   └── configmap-secret.yaml             # Cấu hình môi trường & Secret credentials
├── locustfile.py                         # Kịch bản kiểm thử tải High-Concurrency Locust
├── Dockerfile                            # Multi-stage Dockerfile tối ưu hóa với uv & tini
├── pyproject.toml                        # Quản lý phụ thuộc và công cụ (uv, ruff, mypy, pytest)
├── src/
│   ├── domain/                           # [CORE] Tầng Domain tinh khiết (Pure Python)
│   │   ├── exceptions.py                 # Domain Exceptions (EntityNotFound, RuleViolation)
│   │   ├── models.py                     # Domain Entities & Value Objects (Dataclasses)
│   │   └── services.py                   # Domain Services (Xử lý quy tắc nghiệp vụ phức tạp)
│   ├── application/                      # [USE CASES] Điều phối quy trình nghiệp vụ
│   │   ├── ports/                        # Giao ước trừu tượng (typing.Protocol)
│   │   │   ├── repository.py             # TaskRepositoryPort, ProjectRepositoryPort
│   │   │   ├── cache.py                  # CachePort
│   │   │   ├── queue.py                  # JobQueuePort
│   │   │   └── notification.py           # NotificationPort
│   │   └── use_cases/                    # Use Cases độc lập
│   │       ├── create_task.py
│   │       ├── get_tasks_keyset.py
│   │       └── export_project_report.py
│   ├── infrastructure/                   # [OUTBOUND ADAPTERS] Hiện thực cụ thể
│   │   ├── database/                     # SQLAlchemy 2.0 Async ORM Models & Repositories
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── task_repository.py
│   │   ├── cache/                        # Redis Cache Adapter (Locking, Stampede defense)
│   │   │   └── redis_cache.py
│   │   ├── queue/                        # ARQ Worker & Enqueue Adapter
│   │   │   ├── arq_adapter.py
│   │   │   └── worker.py
│   │   ├── realtime/                     # Redis Pub/Sub Message Backplane
│   │   │   └── pubsub_manager.py
│   │   └── telemetry/                    # OpenTelemetry & Prometheus Configuration
│   │       └── setup.py
│   └── presentation/                     # [INBOUND ADAPTERS] Giao diện người dùng / API
│       ├── api/
│       │   ├── dependencies.py           # Depends providers (Auth, RateLimiter, Idempotency)
│       │   ├── middleware.py             # Security Headers, Metrics & Logging Context
│       │   ├── schemas/                  # Pydantic v2 Input/Output Schemas (extra="forbid")
│       │   └── routers/                  # FastAPI APIRouters (Auth, Tasks, Projects, Jobs)
│       ├── websocket/                    # WebSocket Connection Manager & Handlers
│       └── main.py                       # FastAPI App Initialization & Lifespan
└── tests/
    ├── unit/                             # Kiểm thử Unit nhanh với Mock Repositories
    ├── integration/                      # Kiểm thử Tích hợp với Testcontainers (PostgreSQL, Redis)
    └── e2e/                              # Kiểm thử Toàn trình End-to-End API
```

---

## 💡 Gợi ý triển khai

### Bước 1: Khởi tạo Tầng Domain & Khai báo Ports bằng `typing.Protocol`

Xây dựng tầng Domain tinh khiết không phụ thuộc vào bất kỳ framework bên ngoài nào:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@dataclass(slots=True)
class TaskEntity:
    id: str | None
    project_id: str
    title: str
    owner_id: str
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def complete(self) -> None:
        if self.status == TaskStatus.DONE:
            raise ValueError("Task đã ở trạng thái hoàn thành!")
        self.status = TaskStatus.DONE


@dataclass(slots=True)
class CommentEntity:
    id: str | None
    task_id: str
    author_id: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class TaskRepositoryPort(Protocol):

    async def get_by_id(self, task_id: str) -> TaskEntity | None:
        ...

    async def save(self, task: TaskEntity) -> TaskEntity:
        ...

    async def list_by_cursor(
        self,
        project_id: str,
        cursor_dt: datetime | None,
        cursor_id: str | None,
        limit: int,
    ) -> tuple[list[TaskEntity], bool]:
        ...


class CommentRepositoryPort(Protocol):

    async def create(self, comment: CommentEntity) -> CommentEntity:
        ...

    async def list_by_task(self, task_id: str) -> list[CommentEntity]:
        ...
```

---

### Bước 2: Tầng Infrastructure – Keyset Cursor Repository với SQLAlchemy 2.0

Hiện thực `TaskRepositoryPort` tối ưu hóa câu truy vấn bằng cách so sánh composite tuple:

```python
from __future__ import annotations

from datetime import datetime
from sqlalchemy import desc, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import TaskEntity, TaskStatus
# Giả sử TaskOrmModel đã được định nghĩa trong infrastructure/database/models.py
from src.infrastructure.database.models import TaskOrmModel


class SqlAlchemyTaskRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_cursor(
        self,
        project_id: str,
        cursor_dt: datetime | None,
        cursor_id: str | None,
        limit: int = 20,
    ) -> tuple[list[TaskEntity], bool]:
        stmt = (
            select(TaskOrmModel)
            .where(TaskOrmModel.project_id == project_id)
            .order_by(desc(TaskOrmModel.created_at), desc(TaskOrmModel.id))
            .limit(limit + 1)
        )

        if cursor_dt and cursor_id:
            # So sánh bộ giá trị khóa chính (created_at, id) < (:dt, :id)
            stmt = stmt.where(
                tuple_(TaskOrmModel.created_at, TaskOrmModel.id) < (cursor_dt, cursor_id)
            )

        result = await self.session.scalars(stmt)
        rows = list(result.all())

        has_more = len(rows) > limit
        items = rows[:limit]

        # Chuyển đổi ORM Model sang Domain Entity
        domain_entities = [
            TaskEntity(
                id=item.id,
                project_id=item.project_id,
                title=item.title,
                owner_id=item.owner_id,
                status=TaskStatus(item.status),
                created_at=item.created_at,
            )
            for item in items
        ]
        return domain_entities, has_more
```

---

### Bước 3: Redis Pub/Sub Realtime Backplane cho Đa Pods

Hệ thống quản lý phát tán sự kiện thời gian thực xuyên suốt các Pods Kubernetes:

```python
from __future__ import annotations

import asyncio
import json
from typing import Any
from redis.asyncio import Redis


class RealtimePubSubBackplane:

    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client
        self.local_subscribers: dict[str, set[Any]] = {}

    def subscribe(self, project_id: str, ws: Any) -> None:
        """Đăng ký WebSocket client vào phòng project của Pod hiện tại."""
        self.local_subscribers.setdefault(project_id, set()).add(ws)

    def unsubscribe(self, project_id: str, ws: Any) -> None:
        """Hủy đăng ký WebSocket client khi ngắt kết nối."""
        if project_id in self.local_subscribers:
            self.local_subscribers[project_id].discard(ws)
            if not self.local_subscribers[project_id]:
                del self.local_subscribers[project_id]

    async def broadcast_event(self, project_id: str, event_data: dict[str, Any]) -> None:
        """Phát tán sự kiện vào Redis Channel dùng chung cho mọi Pods."""
        channel_name = f"channel:project:{project_id}"
        message = json.dumps(event_data)
        await self.redis.publish(channel_name, message)

    async def listen_to_channel(self, project_id: str) -> None:
        """Lắng nghe sự kiện từ Redis và chuyển tiếp tới các WebSockets của Pod hiện tại."""
        channel_name = f"channel:project:{project_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel_name)

        try:
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    payload = json.loads(msg["data"])
                    # Gửi tới các WebSocket connections đang mở tại Pod hiện tại
                    sockets = self.local_subscribers.get(project_id, set())
                    for ws in list(sockets):
                        await ws.send_json(payload)
        finally:
            await pubsub.unsubscribe(channel_name)
```

---

### Bước 4: ARQ Worker xử lý Tác vụ xuất Báo cáo ngầm

Định nghĩa Worker ARQ độc lập và cron jobs:

```python
from __future__ import annotations

import asyncio
from typing import Any
from arq.connections import RedisSettings


async def export_project_tasks_job(ctx: dict[Any, Any], project_id: str, user_id: str) -> str:
    """Tác vụ ngầm: Truy vấn toàn bộ tasks, tạo file zip CSV và lưu vào storage."""
    print(f"📦 [ARQ Worker] Đang xuất báo cáo cho dự án {project_id}...")
    await asyncio.sleep(3.0)  # Giả lập xử lý nặng
    download_url = f"https://storage.taskflow.dev/exports/{project_id}-export.zip"
    print(f"✅ [ARQ Worker] Hoàn tất xuất file: {download_url}")
    return download_url


async def weekly_digest_cron_job(ctx: dict[Any, Any]) -> None:
    """Tác vụ định kỳ: Tổng hợp năng suất tuần."""
    print("⏰ [Cron Job] Đang tổng hợp báo cáo Weekly Digest cho toàn bộ thành viên...")


class WorkerSettings:
    functions = [export_project_tasks_job]
    cron_jobs = []  # Có thể đăng ký cron bằng arq.cron
    redis_settings = RedisSettings(host="localhost", port=6379)
```

---

## 🏆 Definition of Done

Dự án TaskFlow M3 chỉ được nghiệm thu khi thỏa mãn toàn bộ các điều kiện khắt khe sau:

| STT | Tiêu chí Nghiệm thu | Phương pháp Kiểm chứng |
|:---:|---|---|
| 1 | **Clean Architecture** | Kiểm tra Dependency Rule: Thư mục `src/domain/` không import bất kỳ package nào từ FastAPI, SQLAlchemy, Redis hay HTTPX. Tầng Application giao tiếp qua `typing.Protocol`. |
| 2 | **Idempotency Keys** | Gửi 5 requests song song với cùng một `Idempotency-Key`: Chỉ có 1 request thực thi, 4 requests còn lại trả về kết quả cache (hoặc `409 Conflict`). Thay đổi body với cùng key trả về `422`. |
| 3 | **Distributed Rate Limiting** | Sử dụng công cụ bắn tải: Quá 150 req/phút của Member lập tức nhận HTTP 429 kèm tiêu đề `RateLimit-Reset` và `Retry-After`. |
| 4 | **Keyset Pagination** | Kiểm thử với bảng `tasks` chứa 500,000 bản ghi: Thời gian truy vấn với `cursor` luôn giữ mức ổn định dưới **5ms** ($O(1)$) bất kể trang đầu hay trang thứ 10,000. |
| 5 | **Distributed Task Queue** | Gọi API `POST /api/v1/projects/{id}/export` phản hồi ngay lập tức sau `< 50ms` với status 202; Worker ARQ xử lý file ngầm và cập nhật trạng thái `COMPLETED`. |
| 6 | **Realtime Multi-Pod** | Chạy 2 Pods API độc lập: Người dùng kết nối WebSocket ở Pod 1 nhận được tin nhắn tức thì (độ trễ `< 50ms`) khi người dùng ở Pod 2 cập nhật công việc. |
| 7 | **Bảo mật OWASP Top 10** | Vượt qua bài kiểm tra phòng thủ: Thử nghiệm sửa ID (BOLA test) bị từ chối 403; thử nghiệm SSRF với URL `http://169.254.169.254` hoặc `http://127.0.0.1` bị chặn ngay lập tức. |
| 8 | **Observability** | Endpoint `/metrics` xuất bản đúng định dạng Prometheus. Log files hiển thị định dạng JSON có đính kèm `trace_id` và `span_id`. |
| 9 | **Load Testing Benchmark** | Chạy Locust với 1,000 người dùng ảo đồng thời trong 5 phút: Throughput đạt $\ge 1,000$ RPS, tỷ lệ lỗi $< 0.1\%$, p99 latency $< 150\text{ms}$. |
| 10 | **Kiểm thử tự động** | Bộ test suite (Unit & Integration với Testcontainers) đạt độ bao phủ dòng (Code Coverage) $\ge 90\%$. `ruff` và `mypy --strict` không báo bất kỳ lỗi nào. |

---

## 🚀 Thử thách thêm

Nếu bạn muốn bứt phá giới hạn để trở thành một Kiến trúc sư Hệ thống (Principal / Lead Architect):

1. **SQLAlchemy Dynamic Read/Write Database Replicas**:
   - Thiết lập cấu hình 1 Primary PostgreSQL (cho lệnh Ghi) và 2 Read Replicas (cho lệnh Đọc).
   - Tự động hóa cơ chế "Read-Your-Own-Writes" dựa trên cookie thời gian ghi gần nhất để tránh lỗi đọc phải dữ liệu trễ do replication lag.
2. **Transactional Outbox Pattern với Change Data Capture (CDC)**:
   - Thay thế việc dispatch event trực tiếp bằng cách ghi vào bảng `outbox_messages` trong cùng transaction với nghiệp vụ.
   - Sử dụng **Debezium** kết nối với PostgreSQL Logical Replication Log để tự động bắt và phát tán sự kiện sang Apache Kafka với cam kết không bao giờ mất tin nhắn.
3. **Thử nghiệm Free-threaded Python (Python 3.13t+)**:
   - Chạy dịch vụ TaskFlow trên môi trường Python 3.13t vô hiệu hóa GIL (`--disable-gil`).
   - Đo đạc và so sánh hiệu năng CPU Multi-threading so với mô hình Multi-process truyền thống.

<!-- nav:bottom -->
---

[⬅️ Kỹ năng senior](../04-senior/12-senior-soft-skills.md) | [📚 Dự án TaskFlow](./README.md) | [🏁 Hoàn thành – về Home](../README.md)
<!-- /nav:bottom -->
