<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 04
<!-- /nav:top -->

# Task queue

> ⏱️ Thời lượng: ~4.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 03: Caching với Redis](./03-caching-redis.md) và [Middleware, lifespan & background tasks](../03-middle/08-middleware-lifespan-background.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Phân định rõ ràng giới hạn của `fastapi.BackgroundTasks`**: Thấu hiểu rủi ro mất việc khi restart Pod, thiếu cơ chế retry, và sự cần thiết phải chuyển dịch sang **Distributed Task Queue**.
- **Làm chủ ARQ (Async-native Redis Queue)**: Thiết lập kiến trúc hàng đợi bất đồng bộ hiện đại, tương thích hoàn hảo 100% với `asyncio` của FastAPI, cấu hình `WorkerSettings`, và enqueue jobs hiệu năng cao với `msgpack`.
- **Nắm vững giải pháp Enterprise Celery**: Hiểu rõ kiến trúc Celery kết hợp RabbitMQ / Redis Broker, các chế độ worker pool (prefork, solo), và kỹ thuật điều phối quy trình phức tạp bằng **Celery Canvas** (`chain`, `group`, `chord`).
- **Nằm lòng nguyên tắc thiết kế Worker chuẩn Senior**:
  - **Idempotency (Tính lũy thừa)**: Đảm bảo worker thực thi nhiều lần (at-least-once delivery) không gây ra sai lệch số dư, thanh toán trùng hoặc tạo bản ghi lặp.
  - **Exponential Backoff Retry kèm Jitter**: Xử lý lỗi tạm thời khi gọi dịch vụ bên thứ ba một cách thông minh, tránh bão retry đánh sập upstream services.
  - **Dead-Letter Queue (DLQ)**: Cô lập các job lỗi vượt ngưỡng retry, lưu vết ngữ cảnh để cảnh báo tức thời và hỗ trợ nạp chạy lại (manual replay).
- **Lên lịch tác vụ định kỳ (Scheduled Cron Jobs)**: Thiết lập các cron jobs tự động hóa dọn dẹp dữ liệu và xuất báo cáo hàng ngày với ARQ cron hoặc Celery Beat.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET, việc xử lý tác vụ nền và kiến trúc hướng sự kiện (Event-Driven / Message-Driven) đã có những thư viện tiêu chuẩn công nghiệp:

| Khái niệm / Yêu cầu | C# / .NET Ecosystem | Python Ecosystem |
|---|---|---|
| **In-process Background Tasks** | `IHostedService` / `BackgroundService` trong ASP.NET Core. | `fastapi.BackgroundTasks` (chạy trên threadpool của chính tiến trình API). |
| **Distributed Job Scheduler** | **Hangfire** (có Dashboard trực quan, lưu state vào SQL Server/Redis) hoặc **Quartz.NET**. | **ARQ** (Async-native Redis Queue) hoặc **Celery** (kèm công cụ Flower Dashboard). |
| **Message Bus / Advanced Workflows** | **MassTransit** hoặc **NServiceBus** (hỗ trợ RabbitMQ, Azure Service Bus, Saga state machines). | **Celery Canvas** (`chain`, `chord`, `group`) hoặc **Dramatiq** kết hợp RabbitMQ/Redis. |
| **Mô hình lập trình Worker** | Đa luồng native, `async/await Task` tích hợp sâu trong DI container (`IServiceScopeFactory`). | **ARQ**: Pure Async Event Loop; **Celery**: Pre-fork đa tiến trình hoặc gevent/eventlet. |
| **Idempotency Strategy** | `Outbox Pattern` hoặc `Inbox Pattern` của MassTransit; Distributed Lock. | Idempotency Key trên Redis (`SET NX`), Database Unique Constraints, Transactional Outbox. |
| **Scheduled / Cron Jobs** | Hangfire Recurring Jobs (`RecurringJob.AddOrUpdate()`) hoặc Quartz CronTrigger. | ARQ `cron(...)` hoặc `celery-beat` scheduler. |

---

## 📖 Lý thuyết

### 1. Khi nào `fastapi.BackgroundTasks` trở thành cái bẫy?

Ở Level 03, bạn đã học cách sử dụng `fastapi.BackgroundTasks` để gửi email hoặc ghi log audit. Tuy nhiên, trong môi trường Production quy mô lớn, `BackgroundTasks` bộc lộ 5 nhược điểm chí mạng:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   HẠN CHẾ CỦA FASTAPI BACKGROUND TASKS                 │
│                                                                        │
│   Web Request ──► FastAPI Pod [ Memory Queue ]                         │
│                                   │                                    │
│   Khi Kubernetes restart Pod      ▼                                    │
│   (Rolling update / OOM)  ──► [ MẤT TOÀN BỘ JOBS ĐANG CHỜ! ]           │
│                                                                        │
│   1. Không có Persistence (Dữ liệu nằm trên RAM nội bộ).               │
│   2. Không có Retry Policy (Gặp lỗi mạng là mất vĩnh viễn).            │
│   3. Không thể Scale độc lập (Tác vụ nặng đè nghẽn CPU của API).        │
│   4. Không hỗ trợ Scheduled Cron Jobs (Không hẹn giờ tương lai).       │
│   5. Thiếu Dashboard và Visibility trung tâm.                          │
└────────────────────────────────────────────────────────────────────────┘
```

**Quy tắc vàng cấp Senior**: 
- Chỉ dùng `fastapi.BackgroundTasks` cho các tác vụ *cực nhẹ*, *không quan trọng*, và *chấp nhận mất mát* (như ghi metric phụ, dọn dẹp file tạm cục bộ sau khi download).
- Mọi tác vụ liên quan đến: **Gửi Email/SMS quan trọng**, **Xử lý hóa đơn/thanh toán**, **Xử lý hình ảnh/video**, **Gọi webhook bên thứ ba**, hoặc **Đồng bộ dữ liệu sang ERP** bắt buộc phải được đẩy vào **Distributed Task Queue**.

---

### 2. ARQ: Async-Native Task Queue trên nền Redis

[ARQ](https://github.com/samuelcolvin/arq) là thư viện hàng đợi công việc hiện đại do Samuel Colvin (tác giả của Pydantic) sáng lập:
- **Async Native**: Được viết 100% bằng Python `asyncio`. Mỗi worker là một Event Loop duy nhất, có khả năng xử lý hàng trăm tác vụ I/O đồng thời mà không tốn RAM như mô hình pre-fork.
- **Tối ưu với Redis**: Tận dụng triệt để Redis ZSET và Sorted Sets để quản lý độ ưu tiên và thời gian hoãn (deferred execution).
- **Serialization siêu tốc**: Mặc định sử dụng **MessagePack (`msgpack`)** để nén dữ liệu truyền tải, nhỏ hơn và nhanh hơn JSON rất nhiều.
- **Tương thích hoàn hảo với FastAPI**: Cùng chia sẻ tư duy `async/await`, dễ dàng tích hợp qua Redis connection pool.

```text
┌──────────────┐                     ┌───────────────┐                  ┌─────────────┐
│ FastAPI Pod  │ ──enqueue_job()──►  │ Redis Broker  │ ──poll jobs──►   │ ARQ Worker  │
│ (Web API)    │                     │ (ZSET Queue)  │                  │ (Async Pod) │
└──────────────┘                     └───────────────┘                  └─────────────┘
```

---

### 3. Celery: Người khổng lồ Enterprise & Canvas Workflows

Ra đời từ năm 2009, Celery là giải pháp Task Queue kỳ cựu nhất của thế giới Python. Celery phù hợp với các hệ thống phân tán khổng lồ đòi hỏi:
- **Hỗ trợ AMQP / RabbitMQ**: Bảo đảm message durability chuẩn doanh nghiệp, routing keys linh hoạt.
- **Worker Pools đa dạng**:
  - `prefork` (mặc định): Mỗi worker là một tiến trình con, hoàn hảo cho các tác vụ CPU-bound nặng (xử lý ảnh, AI inference).
  - `gevent` / `eventlet`: Cho phép mở hàng ngàn luồng coroutine nhẹ cho I/O-bound.
- **Celery Canvas Workflows**: Xây dựng quy trình xử lý đồ thị phụ thuộc (DAG):
  - **`chain` (Chuỗi tuần tự)**: Task A chạy xong lấy kết quả làm đầu vào cho Task B, rồi đến Task C.
    `chain(download_file.s(url) | extract_text.s() | analyze_sentiment.s())()`
  - **`group` (Chạy song song)**: Chạy đồng thời N tasks độc lập.
    `group(resize_image.s(img, size) for size in SIZES)()`
  - **`chord` (Phân tán rồi gom tụ - Map/Reduce)**: Chạy song song N tasks, khi tất cả hoàn tất thì gửi toàn bộ kết quả vào một task Callback tổng hợp.

---

### 4. Bốn nguyên tắc thiết kế Worker chuẩn Senior

#### 4.1 Nguyên tắc 1: Idempotent Worker (Tính lũy thừa)
Trong hệ thống mạng phân tán, các broker chỉ có thể cam kết **At-Least-Once Delivery** (tin nhắn được chuyển giao ít nhất một lần). Do mạng giật lag hoặc worker bị OOM kill đúng lúc vừa xử lý xong nhưng chưa kịp gửi lệnh xác nhận (ACK), broker sẽ gửi lại job đó cho worker khác chạy lại!

Nếu worker của bạn là tác vụ trừ tiền trong ví:
`account.balance -= 100_000`
Chạy lại 2 lần sẽ khiến tài khoản khách hàng bị trừ 2 lần!

**Giải pháp**: Thiết kế Idempotency Key.
1. Mỗi job khi được tạo ra phải kèm theo một `idempotency_key` duy nhất (ví dụ UUID giao dịch).
2. Khi worker tiếp nhận job:
   - Sử dụng Redis `SET {idempotency_key} "PROCESSING" NX EX 3600` để khóa. Nếu key đã tồn tại hoặc trạng thái đã là `"COMPLETED"`, worker lập tức bỏ qua và trả về kết quả cũ.
   - Sử dụng Unique Constraint trong Database (`order_transactions.idempotency_key UNIQUE`).

#### 4.2 Nguyên tắc 2: Exponential Backoff Retry kèm Jitter
Khi gọi các dịch vụ bên thứ ba (Cổng thanh toán Stripe, OpenAI API, Twilio SMS), lỗi mạng tạm thời (`HTTP 502/503/504`) là chuyện thường xuyên xảy ra.
- Nếu bạn retry dồn dập ngay lập tức: Bạn sẽ làm trầm trọng thêm tình trạng nghẽn của dịch vụ đó (hoặc bị chặn IP do rate-limiting).
- **Exponential Backoff**: Thời gian chờ tăng gấp đôi sau mỗi lần thử lại: $1\text{s} \to 2\text{s} \to 4\text{s} \to 8\text{s} \to 16\text{s}$.
- **Jitter (Nhiễu ngẫu nhiên)**: Cộng thêm một vài giây ngẫu nhiên để phân tán hàng ngàn worker không cùng dội tải vào upstream service tại cùng một thời điểm.

#### 4.3 Nguyên tắc 3: Dead-Letter Queue (DLQ)
Nếu một job đã retry hết số lần tối đa (ví dụ 5 lần) mà vẫn thất bại do lỗi dữ liệu sai (Bad Data / Business Error):
- Tuyệt đối không được âm thầm vứt bỏ (drop) job!
- Hệ thống phải chuyển job đó vào một hàng đợi đặc biệt mang tên **Dead-Letter Queue (DLQ)**.
- Gửi thông báo khẩn qua Slack/Discord hoặc PagerDuty cho đội ngũ trực vận hành kèm toàn bộ stack trace và input parameters.
- Cung cấp script / API cho phép Admin xem xét và **Replay (nạp chạy lại)** job từ DLQ sau khi đã khắc phục sự cố.

#### 4.4 Nguyên tắc 4: Chỉ truyền Primitive IDs vào Task Arguments
Tuyệt đối không truyền toàn bộ SQLAlchemy Model object hoặc đối tượng dữ liệu lớn vào tham số của Task:
```python
# ❌ RẤT XẤU: Nén toàn bộ object phức tạp vào tham số
@arq_task
async def send_invoice(user: User):  # Sẽ lỗi serialization hoặc dữ liệu bị cũ (stale)!
    pass


# ✅ CHUẨN SENIOR: Chỉ truyền ID nguyên thủy
@arq_task
async def send_invoice(ctx: dict, user_id: int):
    # Worker tự mở session và truy vấn dữ liệu mới nhất từ DB
    async with get_db_session() as session:
        user = await session.get(User, user_id)
        ...
```

---

## 💻 Ví dụ thực hành

### 1. Xây dựng cụm Worker ARQ hoàn chỉnh

Dưới đây là mã nguồn của một Worker ARQ độc lập (`worker.py`) với đầy đủ logic xử lý tác vụ, context database, retry backoff, và scheduled cron job:

```python
import asyncio
from typing import Any
from arq import cron
from arq.connections import RedisSettings
import httpx


# 1. Định nghĩa các Tasks
async def send_welcome_email(ctx: dict[str, Any], user_id: int, email: str) -> str:
    """Tác vụ gửi email chào mừng người dùng mới."""
    print(f"[Worker] Đang gửi welcome email tới {email} (User #{user_id})...")
    # Giả lập gọi email provider qua HTTP
    await asyncio.sleep(1.0)
    print(f"[Worker] Đã gửi thành công email cho User #{user_id}!")
    return f"EMAIL_SENT_TO_{email}"


async def process_payment_charge(
    ctx: dict[str, Any],
    order_id: str,
    amount: float,
    idempotency_key: str,
) -> dict[str, str | float]:
    """Tác vụ xử lý thanh toán với cơ chế Idempotency."""
    redis = ctx["redis"]

    # 1. Kiểm tra tính Idempotent bằng Redis lock
    lock_key = f"idempotent:pay:{idempotency_key}"
    is_new = await redis.set(lock_key, "PROCESSING", nx=True, ex=7200)

    if not is_new:
        status = await redis.get(lock_key)
        print(f"[Worker] Phát hiện job trùng lặp {idempotency_key}, trạng thái hiện tại: {status}")
        return {"status": "SKIPPED_DUPLICATE", "order_id": order_id}

    try:
        print(f"[Worker] Đang xử lý trừ tiền ${amount} cho đơn hàng {order_id}...")
        await asyncio.sleep(1.5)  # Giả lập thanh toán qua cổng Payment Gateway
        # Đánh dấu đã xử lý thành công
        await redis.set(lock_key, "COMPLETED", ex=86400)
        return {"status": "SUCCESS", "order_id": order_id, "amount": amount}
    except Exception as exc:
        # Nếu lỗi: giải phóng key để lần retry sau có thể chạy lại
        await redis.delete(lock_key)
        raise exc


async def daily_cleanup_cron(ctx: dict[str, Any]) -> None:
    """Tác vụ định kỳ dọn dẹp dữ liệu rác chạy hàng ngày lúc 02:00 sáng."""
    print("[Cron Job] Bắt đầu dọn dẹp các tokens hết hạn và file tạm...")
    await asyncio.sleep(2.0)
    print("[Cron Job] Dọn dẹp hoàn tất!")


# 2. Quản lý vòng đời khởi tạo Worker (Startup / Shutdown context)
async def startup(ctx: dict[str, Any]) -> None:
    print("[ARQ Worker] Đang khởi động... Thiết lập kết nối HTTP Client dùng chung.")
    ctx["http_client"] = httpx.AsyncClient(timeout=10.0)


async def shutdown(ctx: dict[str, Any]) -> None:
    print("[ARQ Worker] Đang tắt máy... Giải phóng HTTP Client.")
    client: httpx.AsyncClient = ctx["http_client"]
    await client.aclose()


# 3. Cấu hình WorkerSettings của ARQ
class WorkerSettings:
    functions = [send_welcome_email, process_payment_charge]
    cron_jobs = [
        cron(daily_cleanup_cron, hour=2, minute=0),  # 02:00 sáng mỗi ngày
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn("redis://localhost:6379/1")
    max_jobs = 20  # Tối đa 20 tác vụ concurrent trên 1 worker process
    job_timeout = 60  # Timeout 60 giây cho mỗi job
```

Khởi chạy worker trên terminal:
```bash
arq worker.WorkerSettings
```

---

### 2. Tích hợp Enqueue Job từ FastAPI Endpoint

Trong ứng dụng FastAPI, chúng ta kết nối tới ARQ Redis Pool lúc startup và enqueue các tác vụ bất đồng bộ:

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    user_id: int
    email: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Khởi tạo ARQ Redis client pool
    arq_pool = await create_pool(RedisSettings.from_dsn("redis://localhost:6379/1"))
    app.state.arq_pool = arq_pool
    print("[FastAPI] Đã kết nối tới ARQ Redis Pool.")
    try:
        yield
    finally:
        await arq_pool.aclose()
        print("[FastAPI] Đã ngắt kết nối ARQ Pool.")


app = FastAPI(title="Task Queue API", lifespan=lifespan)


def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool


@app.post("/users/register")
async def register_user(
    payload: UserRegisterRequest,
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
) -> dict[str, str]:
    # 1. Lưu user vào Database (giả lập)
    print(f"Đã lưu User #{payload.user_id} vào Database.")

    # 2. Đẩy job gửi email chào mừng vào hàng đợi ARQ (hoàn toàn non-blocking)
    job = await arq_pool.enqueue_job(
        "send_welcome_email",
        user_id=payload.user_id,
        email=payload.email,
        _job_id=f"welcome_email_user_{payload.user_id}",  # Đảm bảo duy nhất
    )

    return {
        "status": "user_created",
        "job_id": job.job_id if job else "already_enqueued",
    }
```

---

### 3. Triển khai Worker Retry với Exponential Backoff & Dead-Letter Queue (DLQ)

```python
import asyncio
import random
from typing import Any
import redis.asyncio as aioredis


async def execute_task_with_dlq(
    redis_client: aioredis.Redis,
    task_name: str,
    task_payload: dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> bool:
    attempt = 0
    while attempt < max_retries:
        try:
            print(f"[Attempt {attempt + 1}/{max_retries}] Đang xử lý task '{task_name}'...")
            # Giả lập hàm gọi API bên ngoài có xác suất fail 80%
            if random.random() < 0.8:
                raise ConnectionError("Upstream API Gateway 503 Service Unavailable!")

            print(f"✅ Xử lý thành công task '{task_name}'!")
            return True
        except Exception as exc:
            attempt += 1
            if attempt >= max_retries:
                print(f"❌ Đã vượt quá {max_retries} lần thử lại! Chuyển task vào Dead-Letter Queue (DLQ)...")
                # Đưa vào DLQ trong Redis
                dlq_record = {
                    "task_name": task_name,
                    "payload": str(task_payload),
                    "error": str(exc),
                    "attempts": attempt,
                }
                # Lưu vào danh sách DLQ để admin xử lý sau
                await redis_client.rpush("dlq:failed_tasks", str(dlq_record))
                return False

            # Tính toán Exponential Backoff kèm Jitter ngẫu nhiên
            jitter = random.uniform(0.1, 0.5)
            backoff_delay = (base_delay * (2 ** (attempt - 1))) + jitter
            print(f"⚠️ Gặp lỗi: {exc}. Chờ {backoff_delay:.2f}s trước khi retry...")
            await asyncio.sleep(backoff_delay)

    return False
```

---

## ⚠️ Lỗi thường gặp

### 1. Truyền toàn bộ ORM Model Object vào Task Arguments
Nhiều người truyền nguyên thực thể `user` (SQLAlchemy instance) vào task Celery/ARQ:
```python
# ❌ LỖI NGHIÊM TRỌNG:
await arq_pool.enqueue_job("send_email", user=user_instance)
```
*Hậu quả*:
- Lỗi serialization vì SQLAlchemy model dính kèm session, state nội bộ không thể chuyển đổi qua JSON/msgpack.
- **Dữ liệu bị cũ (Stale Data)**: Giả sử task nằm chờ trong queue 5 phút mới được worker bốc chạy. Trong 5 phút đó, email của user đã được đổi trong DB nhưng worker vẫn dùng email cũ được serialize lúc enqueue!
*Giải pháp*: Luôn luôn chỉ truyền `user_id: int` và worker sẽ truy vấn lại DB khi bắt đầu xử lý.

### 2. Không giới hạn số lần Retry (Infinite Retry Loop)
Cấu hình retry vĩnh viễn (`max_retries=None`). Khi gặp một lỗi dữ liệu không thể sửa (ví dụ: thẻ tín dụng bị khóa vĩnh viễn, cú pháp email sai), worker sẽ retry liên tục hàng triệu lần, làm ngập lụt hàng đợi và tiêu thụ 100% tài nguyên CPU của toàn bộ cụm worker.

### 3. Worker chạy tác vụ chặn (Blocking I/O) trong Async Worker
Trong ARQ, nếu bạn viết:
```python
async def my_task(ctx):
    time.sleep(10)  # ❌ SAI: Đóng băng toàn bộ Event Loop của worker!
```
Nó sẽ khiến ARQ worker bị treo, tất cả các tác vụ concurrent khác đang chia sẻ worker đó đều bị đứng hình. Luôn dùng `await asyncio.sleep(10)` hoặc bọc code blocking vào `await asyncio.to_thread(...)`.

### 4. Quên xử lý ngắt kết nối an toàn (Graceful Shutdown)
Khi triển khai Kubernetes, khi Pod bị terminate, nếu worker ngay lập tức bị tắt cưỡng bức (`SIGKILL`), các task đang chạy dở dang sẽ bị đứt gãy giữa chừng (ví dụ file đang ghi dở bị corrupt). Luôn lắng nghe tín hiệu `SIGTERM` và cấu hình `terminationGracePeriodSeconds` trong Kubernetes (ví dụ 60s) để worker hoàn thành nốt các job đang chạy trước khi dừng hẳn.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng hệ thống gửi Webhook Notification bằng ARQ với Retry Backoff
Một hệ thống thanh toán cần bắn Webhook thông báo kết quả giao dịch tới URL của đối tác.
Yêu cầu:
1. Viết ARQ task `dispatch_webhook(ctx, endpoint_url: str, event_data: dict)`.
2. Sử dụng `httpx.AsyncClient` lấy từ `ctx["http_client"]` để gửi POST request.
3. Nếu đối tác trả về mã lỗi 5xx hoặc timeout, kích hoạt retry tối đa 3 lần với khoảng cách thử lại tăng dần (Exponential backoff: 2s, 4s, 8s).

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from typing import Any
from arq import Retry
import httpx


async def dispatch_webhook(
    ctx: dict[str, Any],
    endpoint_url: str,
    event_data: dict[str, Any],
) -> str:
    client: httpx.AsyncClient = ctx["http_client"]
    job_try = ctx.get("job_try", 1)  # Biến đếm lần chạy do ARQ tự cung cấp

    try:
        response = await client.post(endpoint_url, json=event_data, timeout=5.0)
        response.raise_for_status()
        return f"SUCCESS_STATUS_{response.status_code}"
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        print(f"[Webhook Fail] Lần thử {job_try} thất bại: {exc}")
        if job_try < 3:
            # Tính toán backoff: 2s cho lần 1, 4s cho lần 2
            delay = 2**job_try
            raise Retry(defer=delay)
        raise RuntimeError(f"Webhook tới {endpoint_url} thất bại sau 3 lần thử!")
```
</details>

---

### Bài tập 2: Triển khai Idempotent Order Processing Worker với Redis Lock
Viết một worker xử lý xác nhận đơn hàng `process_order(order_id: int, client_request_token: str)`.
Yêu cầu:
1. Sử dụng `client_request_token` để đảm bảo nếu client gửi trùng lặp 5 requests cùng lúc, chỉ có duy nhất 1 job được xử lý.
2. 4 jobs còn lại nhận diện được trạng thái trùng lặp và bỏ qua mà không ném lỗi sập worker.
3. Trạng thái hoàn thành được lưu trong Redis trong 24 giờ.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from typing import Any
import redis.asyncio as aioredis


async def process_order(
    ctx: dict[str, Any],
    order_id: int,
    client_request_token: str,
) -> dict[str, Any]:
    redis: aioredis.Redis = ctx["redis"]
    idempotency_key = f"order:idempotent:{client_request_token}"

    # Cố gắng chiếm lock với trạng thái 'PROCESSING'
    acquired = await redis.set(idempotency_key, "PROCESSING", nx=True, ex=3600)

    if not acquired:
        current_val = await redis.get(idempotency_key)
        print(f"-> Job trùng lặp token={client_request_token}. Bỏ qua!")
        return {"status": "DUPLICATE_IGNORED", "state": current_val}

    try:
        # Xử lý đơn hàng giả lập
        print(f"-> Đang xử lý đơn hàng #{order_id}...")
        await asyncio.sleep(1.0)

        # Cập nhật thành công
        await redis.set(idempotency_key, "COMPLETED", ex=86400)
        return {"status": "SUCCESS", "order_id": order_id}
    except Exception as e:
        await redis.delete(idempotency_key)
        raise e
```
</details>

---

### Bài tập 3: Thiết kế cơ chế Quản lý Dead-Letter Queue (DLQ) và API Replay
Xây dựng một module quản lý DLQ:
1. Hàm `push_to_dlq(redis, failed_job_data: dict)` lưu thông tin job thất bại vào Redis List `system:dlq:jobs`.
2. Endpoint FastAPI `GET /admin/dlq` trả về danh sách các jobs đang nằm trong DLQ.
3. Endpoint FastAPI `POST /admin/dlq/replay/{job_id}` lấy thông tin job từ DLQ và nạp lại vào hàng đợi chính của ARQ để chạy lại.

<details>
<summary>💡 Gợi ý</summary>

```python
from typing import Any
from fastapi import FastAPI, HTTPException
import orjson
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379/1")


@app.get("/admin/dlq")
async def list_dlq_jobs() -> list[dict[str, Any]]:
    # Đọc tối đa 50 jobs đầu tiên trong list DLQ
    raw_jobs = await redis_client.lrange("system:dlq:jobs", 0, 49)
    return [orjson.loads(j) for j in raw_jobs]


@app.post("/admin/dlq/replay")
async def replay_dlq_job(job_id: str) -> dict[str, str]:
    # Lấy job ra khỏi DLQ
    raw_jobs = await redis_client.lrange("system:dlq:jobs", 0, -1)
    target_job = None

    for raw in raw_jobs:
        data = orjson.loads(raw)
        if data.get("job_id") == job_id:
            target_job = data
            await redis_client.lrem("system:dlq:jobs", 1, raw)
            break

    if not target_job:
        raise HTTPException(status_code=404, detail="Job ID không tìm thấy trong DLQ")

    # Re-enqueue vào hàng đợi chính (giả lập)
    print(f"Đã tái nạp job {job_id} vào hàng đợi ARQ chính.")
    return {"status": "replayed", "job_id": job_id}
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được 5 lý do tại sao không nên dùng `fastapi.BackgroundTasks` cho các tác vụ quan trọng trên production.
- [ ] Tôi hiểu rõ kiến trúc async-native của ARQ và cách cấu hình `WorkerSettings` với Redis connection pool.
- [ ] Tôi biết khi nào nên chọn Celery (RabbitMQ broker, canvas complex workflows) và khi nào nên chọn ARQ (nhẹ, async native).
- [ ] Tôi hiểu tầm quan trọng của tính Idempotent trong Worker và biết cách triển khai Idempotency Key.
- [ ] Tôi nắm vững nguyên lý Exponential Backoff kèm Jitter để chống bão retry.
- [ ] Tôi biết cách thiết kế Dead-Letter Queue (DLQ) để lưu vết và replay các job lỗi.
- [ ] Tôi hiểu lý do chỉ nên truyền Primitive IDs vào tham số của task thay vì nén cả ORM model.

---

## 📚 Đọc thêm

- [ARQ Official Documentation: Fast job queuing in Python with asyncio and redis](https://arq-docs.helpmanual.io/)
- [Celery Official Documentation: Distributed Task Queue](https://docs.celeryq.dev/en/stable/)
- [Celery Canvas: Designing Workflows (Chains, Groups, Chords)](https://docs.celeryq.dev/en/stable/userguide/canvas.html)
- [Stripe Engineering: Designing robust and idempotent APIs](https://stripe.com/blog/idempotency)
- [Tiếp theo: Bài 05 – WebSocket & SSE](./05-websockets-sse.md)

<!-- nav:bottom -->
---

[⬅️ Caching với Redis](./03-caching-redis.md) | [📚 Mục lục Senior](./README.md) | [WebSocket & SSE ➡️](./05-websockets-sse.md)
<!-- /nav:bottom -->
