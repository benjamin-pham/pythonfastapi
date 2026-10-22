<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 07
<!-- /nav:top -->

# Thiết kế API nâng cao

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 06: Clean Architecture](./06-clean-architecture.md) và [Level 03: Middle](../03-middle/README.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Làm chủ cơ chế Idempotency Keys**: Triển khai giải pháp xử lý trùng lặp yêu cầu (deduplication) chuẩn xác cho các API đột biến dữ liệu (`POST`, `PATCH`), bảo vệ hệ thống thanh toán và tạo tài nguyên trước các đợt retry tự động của mạng.
- **Xây dựng hệ thống Rate Limiting phân tán (Distributed Rate Limiting)**: Nắm vững các thuật toán giới hạn tần suất (Token Bucket, Leaky Bucket, Sliding Window Counter), thực thi nguyên tử (atomic) trên cụm Redis thông qua Lua Scripts, và tuân thủ các chuẩn tiêu đề IETF (`RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`, `Retry-After`).
- **Hoạch định chiến lược API Versioning & Lifecycle**: Phân tích sâu sắc ưu và nhược điểm giữa URI Path, Custom Headers, và Content Negotiation (Accept Header); triển khai cơ chế Deprecation và Sunsetting theo chuẩn RFC 8594 để nâng cấp hệ thống mà không làm gãy kết nối của client cũ.
- **Chinh phục Keyset (Cursor-based) Pagination cho dữ liệu quy mô lớn**: Hiểu rõ tại sao `OFFSET / LIMIT` truyền thống sụp đổ khi dữ liệu lên đến hàng triệu bản ghi, từ đó làm chủ kỹ thuật Keyset Pagination với chỉ mục phức hợp (composite index) và mã hóa Opaque Cursor dạng Base64.
- **Nâng cao năng lực thiết kế API cấp độ Senior**: Tạo ra những giao diện lập trình có tính nhất quán cao, tự phục hồi trước lỗi mạng, bảo vệ tài nguyên máy chủ và mang lại trải nghiệm tối ưu cho các lập trình viên tích hợp.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET doanh nghiệp, việc thiết kế API nâng cao thường dựa vào hệ sinh thái phong phú của ASP.NET Core kết hợp với các thư viện bên thứ ba hoặc built-in middlewares:

| Khái niệm / Kỹ thuật | Hệ sinh thái C# / ASP.NET Core | Hệ sinh thái Python 3.12+ / FastAPI |
|---|---|---|
| **Idempotency** | Sử dụng ActionFilter / Middleware tự viết hoặc thư viện `IdempotentAPI` kết hợp `IDistributedCache` (Redis). Thường tích hợp vào MediatR Pipeline Behavior. | Sử dụng FastAPI Middleware hoặc `Depends()` kết hợp `redis.asyncio`. Quản lý trạng thái locking và cached response nguyên tử. |
| **Rate Limiting** | .NET 7/8 tích hợp sẵn namespace `System.Threading.RateLimiting` (`builder.Services.AddRateLimiter()`), hỗ trợ Token Bucket, Sliding Window, Partitioned Limiter. | Sử dụng `slowapi` (dựa trên limits) hoặc triển khai Redis Lua Script tùy biến trong `Depends()` để xử lý môi trường phân tán đa tiến trình. |
| **API Versioning** | Thư viện chính thức `Asp.Versioning.Mvc` hỗ trợ URL Path, Query String, Header (`api-supported-versions`, `api-deprecated-versions`). | Phân chia Routers theo prefix (`/api/v1`, `/api/v2`), hoặc xử lý header versioning qua custom Middleware / Dependency Injection. |
| **Keyset Pagination** | Thư viện `MR.EntityFrameworkCore.KeysetPagination` mở rộng IQueryable của EF Core, hỗ trợ so sánh tuple khóa chính. | Tận dụng SQLAlchemy 2.0 tuple comparison `tuple_(Model.created_at, Model.id) < (cursor_dt, cursor_id)` kết hợp `orjson` và `base64`. |
| **Xử lý Race Conditions** | `DistributedLock.Redis` (RedLock.net) hoặc `StackExchange.Redis` transactions (`ITransaction`). | Redis Lua Script (`redis.eval()`) bảo đảm thực thi nguyên tử đơn luồng trên Redis server. |

---

## 📖 Lý thuyết

### 1. Cơ chế Idempotency Keys (IETF Draft)

Trong giao thức HTTP, các phương thức như `GET`, `PUT`, `DELETE` được định nghĩa là có tính **Idempotent** (bảo toàn trạng thái: gọi 1 lần hay $N$ lần thì trạng thái cuối cùng của hệ thống vẫn giống hệt nhau). Tuy nhiên, `POST` bản chất là **Non-Idempotent** (mỗi lần gọi sẽ tạo ra một bản ghi mới).

Trong môi trường phân tán thực tế, lỗi mạng xảy ra liên tục:
```text
Client ─────────── POST /api/v1/orders ───────────► Server (Tạo đơn & Trừ tiền thành công)
   ▲                                                       │
   │                                                       ▼
Client ◄─────── Lỗi kết nối mạng (TCP Drop/Timeout) ───────┘ (Response không về được Client!)
   │
   ▼ (Client tự động thử lại do tưởng chừng server chưa nhận)
Client ─────────── POST /api/v1/orders ───────────► Server (Tạo tiếp đơn thứ 2 -> TRỪ TIỀN 2 LẦN!)
```

Để ngăn chặn thảm họa này, chuẩn **IETF Draft Idempotency-Key** đưa ra giải pháp: Client sinh ra một mã định danh duy nhất (UUID v4) và gửi kèm trong header `Idempotency-Key`.

#### Vòng đời của một Idempotency Request trên Redis
Một quy trình Idempotency an toàn bắt buộc phải giải quyết bài toán Race Condition (khi hai request cùng mang một key được bắn tới gần như đồng thời):

```text
                        Client Request (Header: Idempotency-Key: abc-123)
                                              │
                                              ▼
                             Kiểm tra Key trên Redis (Atomic SET NX)
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
            [Key chưa tồn tại]                                   [Key đã tồn tại]
                    │                                                   │
     Lưu Key với Status = "IN_PROGRESS"                                 ▼
                    │                                         Kiểm tra Status của Key
                    ▼                                                   │
         Thực thi nghiệp vụ chính                                ┌──────┴──────┐
                    │                                            ▼             ▼
       ┌────────────┴────────────┐                        "IN_PROGRESS"   "COMPLETED"
       ▼                         ▼                               │             │
   [Thành công]               [Thất bại]                         ▼             ▼
Lưu Response Body,        Xóa Key khỏi Redis            Trả về 409 Conflict    Replay lại
Headers & Status          (cho phép thử lại)             (Yêu cầu đang xử lý) Response cũ
  = "COMPLETED"                                                              ngay lập tức
```

- **Fingerprint Verification**: Hệ thống phải lưu kèm giá trị băm (SHA-256 hash) của `request.body` và `request.url`. Nếu Client gửi lại cùng một `Idempotency-Key` nhưng nội dung body khác nhau, server phải từ chối ngay lập tức với mã lỗi `422 Unprocessable Entity` hoặc `400 Bad Request` vì hành vi sử dụng sai khóa.

---

### 2. Distributed Rate Limiting & Các thuật toán

Giới hạn tần suất truy cập (Rate Limiting) là lá chắn đầu tiên bảo vệ API khỏi nguy cơ quá tải do bot, tấn công từ chối dịch vụ (DDoS), hoặc các client bị lặp vòng vô tận.

#### So sánh 4 thuật toán Rate Limiting kinh điển

```text
1. Fixed Window:
   [    Window 1: 100 requests   ][    Window 2: 100 requests   ]
   ───────────────────────────────▲───────────────────────────────
                       Nguy cơ nghẽn tại ranh giới:
             Cuối Window 1 (100 req) + Đầu Window 2 (100 req)
             ──► 200 requests chỉ trong vòng vài giây!

2. Sliding Window Counter:
   Lấy trung bình trọng số giữa cửa sổ trước và cửa sổ hiện tại:
   Current_Count = Window_Current + Window_Prev * (1 - (now - start) / window_size)

3. Token Bucket:
   Bucket chứa tối đa C tokens. Mỗi giây được bổ sung R tokens.
   Cho phép xử lý các đợt lưu lượng tăng đột biến (Bursting) trong giới hạn dung lượng bucket.

4. Leaky Bucket:
   Các request đi vào thùng chứa và rò rỉ ra ngoài với tốc độ ổn định cố định (Smooth flow).
```

| Tiêu chí | Fixed Window | Sliding Window Counter | Token Bucket | Leaky Bucket |
|---|---|---|---|---|
| **Bộ nhớ sử dụng** | Rất thấp (1 key integer) | Thấp (2 keys integer) | Thấp (2 giá trị: tokens & timestamp) | Thấp (1 queue hoặc counter) |
| **Độ chính xác** | Kém (bị đột biến tại ranh giới) | Rất cao (~99% mượt mà) | Rất cao | Rất cao |
| **Hỗ trợ Burst Traffic** | Không | Không | **Có** (rất linh hoạt) | Không (lực lượng bị ép phẳng) |
| **Phù hợp nhất cho** | API nội bộ đơn giản | Giới hạn hạn ngạch ngày/tháng | **Public REST API, Webhooks** | Video streaming, logging ingest |

#### Chuẩn tiêu đề Rate Limiting IETF
Khi trả về phản hồi, API chuyên nghiệp cần cung cấp các tiêu đề sau:
- `RateLimit-Limit`: Hạn mức tối đa được cấp trong cửa sổ thời gian (ví dụ: `100`).
- `RateLimit-Remaining`: Số lượng yêu cầu còn lại trong cửa sổ hiện tại (ví dụ: `42`).
- `RateLimit-Reset`: Số giây còn lại cho tới khi hạn mức được làm mới hoàn toàn (ví dụ: `18`).
- `Retry-After`: (Chỉ gửi khi trả về `429 Too Many Requests`) Số giây client phải chờ trước khi được phép gọi lại.

---

### 3. API Versioning & Vòng đời phiên bản (Lifecycle)

Khi hệ thống tiến hóa, các thay đổi làm gãy tính tương thích (Breaking Changes) như xóa trường, đổi tên thuộc tính, hoặc thay đổi kiểu dữ liệu là không thể tránh khỏi.

#### 3 chiến lược Versioning phổ biến
1. **URI Path Versioning** (`/api/v1/tasks` $\to$ `/api/v2/tasks`):
   - *Ưu điểm*: Cực kỳ trực quan, dễ debug qua trình duyệt, thân thiện với các hệ thống caching proxy (Nginx, Cloudflare).
   - *Nhược điểm*: Vi phạm nguyên lý REST thuần túy (URI định danh tài nguyên, không định danh phiên bản), dẫn đến nhân bản code routers.
   - *Đánh giá*: **Khuyên dùng số 1** cho các dịch vụ Web/Mobile đại chúng.
2. **Header-based Versioning** (`X-API-Version: 2` hoặc `Accept-Version: v2`):
   - *Ưu điểm*: Giữ nguyên cấu trúc URI sạch sẽ.
   - *Nhược điểm*: Khó kiểm thử qua URL thông thường, cấu hình cache proxy phức tạp hơn (bắt buộc phải cấu hình `Vary: X-API-Version`).
3. **Content Negotiation / Media Type Versioning** (`Accept: application/vnd.taskflow.v2+json`):
   - *Ưu điểm*: Chuẩn mực nhất theo kiến trúc RESTful HATEOAS.
   - *Nhược điểm*: Rất khó cấu hình cho client, code parsing trong backend phức tạp.

#### Quy trình Deprecation & Sunsetting (RFC 8594)
Tuyệt đối không xóa bỏ API cũ đột ngột. Cần thiết lập thời gian chuyển tiếp tối thiểu 3–6 tháng kèm theo các HTTP headers:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Deprecation: @1735689600
Sunset: Wed, 01 Jul 2026 00:00:00 GMT
Link: <https://api.taskflow.dev/docs/migration-v2>; rel="deprecation"; type="text/html"
```
- `Deprecation`: Thông báo API này đã lỗi thời từ timestamp quy định.
- `Sunset`: Thời điểm chính xác API sẽ bị đóng hoàn toàn (sau thời điểm này, server sẽ trả về `410 Gone`).

---

### 4. Keyset (Cursor-based) Pagination cho hệ thống dữ liệu lớn

Trong [Middle: Phân trang & Lọc](../03-middle/09-pagination-filtering.md), chúng ta đã làm quen với phân trang dựa trên vị trí:
```sql
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 20 OFFSET 500000;
```
Khi `OFFSET` lớn (ví dụ 500,000), cơ sở dữ liệu bắt buộc phải duyệt và quét qua 500,020 bản ghi trên ổ đĩa rồi vứt bỏ 500,000 bản ghi đầu tiên! Điều này khiến thời gian truy vấn tăng tuyến tính $O(N)$ từ 5ms lên đến vài giây, gây nghẽn toàn bộ Database Connection Pool.

#### Giải pháp Keyset Pagination (Cursor Pagination)
Thay vì nhảy cóc qua số lượng bản ghi, client gửi lại giá trị của bản ghi cuối cùng mà nó đã thấy (ví dụ: `created_at` và `id`):

```sql
SELECT * FROM tasks
WHERE (created_at, id) < ('2026-10-22 08:00:00+00', '0192e1b4-...')
ORDER BY created_at DESC, id DESC
LIMIT 20;
```
- **Hiệu năng $O(1)$**: Khi có Index phức hợp `CREATE INDEX idx_tasks_created_id ON tasks (created_at DESC, id DESC);`, Database nhảy thẳng trực tiếp (B-Tree Index Seek) đến đúng vị trí cần lấy! Dù bảng có 100 triệu dòng, thời gian truy vấn vẫn chỉ mất 2ms.
- **Tính nhất quán**: Không bị hiện tượng trùng lặp hoặc bỏ sót dữ liệu khi có bản ghi mới được chèn vào trong lúc người dùng đang cuộn trang.
- **Opaque Cursor**: Để bảo vệ cấu trúc nội bộ của cơ sở dữ liệu, hai giá trị `(created_at, id)` được đóng gói vào JSON và mã hóa URL-safe Base64 thành một chuỗi duy nhất: `eyJjIjogIjIwMjYtMTAtMjJUMDg6MDA6MDBaIiwgImkiOiAxMDB9`.

---

### 5. Thiết kế & Bảo mật Webhook với HMAC-SHA256

Webhook là cơ chế thông báo sự kiện bất đồng bộ giữa các máy chủ (Server-to-Server). Khi một sự kiện nghiệp vụ xảy ra (ví dụ: Task hoàn thành, thanh toán thành công qua Stripe/VNPay), hệ thống sẽ gửi một HTTP POST request chứa dữ liệu sự kiện đến URL endpoint do phía đối tác đăng ký.

#### Các rủi ro an ninh trong Webhook:
1. **Mạo danh (Spoofing)**: Kẻ tấn công gửi HTTP POST giả mạo đến webhook endpoint của người nhận để kích hoạt sai lệch nghiệp vụ.
2. **Nghe lén & Chèn sửa dữ liệu (Tampering)**: Thay đổi payload trên đường truyền nếu không dùng HTTPS và chữ ký số.
3. **Tấn công lặp lại (Replay Attacks)**: Kẻ tấn công bắt gói tin hợp lệ và gửi lại nhiều lần để ép hệ thống xử lý lặp.
4. **Timing Attacks**: Dùng toán tử `==` để so sánh chuỗi chữ ký, giúp kẻ tấn công đo lường thời gian phản hồi (tính bằng micro-giây) để dò tìm từng ký tự của chữ ký bí mật.

#### Tiêu chuẩn bảo mật cấp Senior (Chuẩn hóa theo Stripe / GitHub):
- **Secret dùng chung (Shared Secret)**: Mỗi bên nhận webhook được cấp một secret key ngẫu nhiên an toàn (`whsec_...`).
- **Chữ ký số HMAC-SHA256**: Phía gửi tạo chữ ký băm mật mã:
  $$\text{Signature} = \text{HMAC-SHA256}(\text{key}=\text{secret}, \text{msg}=f"t=\{\text{timestamp}\}.v1=\{\text{payload\_bytes}\}")$$
- **Tiêu đề đính kèm**:
  - `X-Webhook-Signature`: Mã hex của chữ ký HMAC-SHA256.
  - `X-Webhook-Timestamp`: Thời gian Unix Epoch (giây) lúc gửi.
- **Xác thực Constant-Time**: Bên nhận dùng hàm `hmac.compare_digest()` để so sánh chữ ký nhận được với chữ ký tự tính toán, loại bỏ hoàn toàn lỗ hổng Timing Attack.
- **Dung sai thời gian (Tolerance Window)**: Bên nhận từ chối bất kỳ webhook nào có $| \text{current\_time} - \text{timestamp} | > 300\text{s}$ (5 phút) để triệt tiêu Replay Attacks.

---

## 💻 Ví dụ thực hành

### 1. Triển khai Idempotency Middleware với Redis

Ví dụ dưới đây minh họa việc hiện thực Idempotency bảo vệ các request `POST`: sử dụng Redis để lưu trạng thái xử lý nguyên tử, kiểm tra fingerprint SHA-256 của request body, và trả về dữ liệu cache khi có retry.

```python
from __future__ import annotations

import hashlib
import json
from typing import Any
from fastapi import FastAPI, HTTPException, Request, Response, status
from redis.asyncio import Redis

app = FastAPI(title="Advanced API Design - Idempotency Demo")

# Khởi tạo kết nối Redis
redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=False)

IDEMPOTENCY_HEADER = "idempotency-key"
LOCK_TTL_SECONDS = 60  # Thời gian tối đa giữ lock cho một request đang xử lý
CACHE_TTL_SECONDS = 86400  # Lưu kết quả thành công trong 24 giờ


def compute_payload_fingerprint(method: str, path: str, body: bytes) -> str:
    """Tạo chữ ký SHA-256 đại diện cho dữ liệu đầu vào."""
    hasher = hashlib.sha256()
    hasher.update(method.encode("utf-8"))
    hasher.update(path.encode("utf-8"))
    hasher.update(body)
    return hasher.hexdigest()


@app.post("/api/v1/payments")
async def process_payment(request: Request) -> Response:
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Header '{IDEMPOTENCY_HEADER}' là bắt buộc đối với giao dịch này.",
        )

    body_bytes = await request.body()
    fingerprint = compute_payload_fingerprint(request.method, request.url.path, body_bytes)

    redis_data_key = f"idempotency:{idempotency_key}"

    # Dùng pipeline hoặc giao dịch để kiểm tra và xử lý
    existing_raw = await redis_client.get(redis_data_key)
    if existing_raw:
        record: dict[str, Any] = json.loads(existing_raw.decode("utf-8"))

        # 1. Kiểm tra nếu cùng key nhưng payload bị thay đổi
        if record.get("fingerprint") != fingerprint:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Idempotency-Key đã được sử dụng với nội dung payload khác!",
            )

        # 2. Kiểm tra nếu request trước đó vẫn đang chạy
        if record.get("status") == "IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Yêu cầu trước đó với khóa này đang được xử lý. Vui lòng thử lại sau.",
            )

        # 3. Request trước đã hoàn tất -> Replay lại Response đã cache
        cached_response = record["response"]
        return Response(
            content=cached_response["body"],
            status_code=cached_response["status_code"],
            headers={
                "Content-Type": "application/json",
                "X-Cache-Lookup": "HIT-IDEMPOTENT",
            },
        )

    # Đặt cờ IN_PROGRESS bằng SET NX (Not Exists) để chống race condition
    init_payload = json.dumps({"status": "IN_PROGRESS", "fingerprint": fingerprint})
    acquired = await redis_client.set(
        redis_data_key, init_payload, ex=LOCK_TTL_SECONDS, nx=True
    )
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Xung đột xử lý đồng thời. Yêu cầu đang được thực hiện.",
        )

    try:
        # Giả lập xử lý nghiệp vụ thanh toán trừ tiền
        parsed_data = json.loads(body_bytes.decode("utf-8") or "{}")
        amount = parsed_data.get("amount", 0)

        result_payload = {
            "transaction_id": "tx_998877",
            "amount": amount,
            "status": "SUCCESS",
            "message": "Thanh toán thành công.",
        }
        response_body = json.dumps(result_payload)
        response_status = status.HTTP_201_CREATED

        # Lưu kết quả COMPLETED vào Redis
        completed_record = json.dumps(
            {
                "status": "COMPLETED",
                "fingerprint": fingerprint,
                "response": {
                    "status_code": response_status,
                    "body": response_body,
                },
            }
        )
        await redis_client.set(redis_data_key, completed_record, ex=CACHE_TTL_SECONDS)

        return Response(
            content=response_body,
            status_code=response_status,
            headers={"Content-Type": "application/json"},
        )

    except Exception as exc:
        # Nếu có lỗi nghiệp vụ bất ngờ, xóa key để client có thể retry lại
        await redis_client.delete(redis_data_key)
        raise exc
```

---

### 2. Distributed Rate Limiter với Redis Lua Script & Chuẩn IETF Headers

Dưới đây là một Rate Limiter sử dụng thuật toán **Sliding Window Counter** qua Redis Lua script để bảo đảm tính nguyên tử hoàn đối giữa các workers của FastAPI:

```python
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from redis.asyncio import Redis

app = FastAPI(title="Advanced API Design - Rate Limiting Demo")
redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Lua Script: Thực thi kiểm tra giới hạn trượt trong 1 lệnh nguyên tử duy nhất trên Redis
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local clear_before = now - window
redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)

local current_requests = redis.call('ZCARD', key)
if current_requests < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
    return {1, limit - current_requests - 1, window}
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset_after = 0
    if #oldest > 0 then
        reset_after = math.ceil((tonumber(oldest[2]) + window) - now)
    end
    return {0, 0, reset_after}
end
"""


class RateLimiter:
    """FastAPI Dependency cung cấp Rate Limiter theo client IP hoặc User ID."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, request: Request, response: Response) -> None:
        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"ratelimit:{client_ip}:{request.url.path}"
        now = time.time()

        # Gọi Lua script qua redis
        result: list[int] = await redis_client.eval(
            SLIDING_WINDOW_LUA, 1, rate_key, now, self.window_seconds, self.limit
        )  # type: ignore[assignment]

        allowed, remaining, reset_after = result[0], result[1], result[2]

        # Ghi IETF RateLimit Headers vào Response
        response.headers["RateLimit-Limit"] = str(self.limit)
        response.headers["RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["RateLimit-Reset"] = str(reset_after)

        if allowed == 0:
            response.headers["Retry-After"] = str(reset_after)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Bạn đã vượt quá giới hạn tần suất yêu cầu. Vui lòng thử lại sau.",
                headers={"Retry-After": str(reset_after)},
            )


@app.get(
    "/api/v1/public-data",
    dependencies=[Depends(RateLimiter(limit=10, window_seconds=60))],
)
async def get_public_data() -> dict[str, str]:
    return {"message": "Dữ liệu công khai, giới hạn 10 requests / 60 giây."}
```

---

### 3. Keyset (Cursor-based) Pagination với SQLAlchemy 2.0 & Pydantic v2

Triển khai phân trang con trỏ (Cursor Pagination) bảo toàn hiệu năng cao với chỉ mục phức hợp `(created_at, id)`:

```python
from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Index, String, desc, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

T = TypeVar("T")


class Base(DeclarativeBase):
    pass


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_tasks_created_at_id", desc("created_at"), desc("id")),
    )


class TaskRead(BaseModel):
    id: str
    title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool


def encode_cursor(created_at: datetime, item_id: str) -> str:
    """Chuyển đổi tuple (created_at, id) thành chuỗi Opaque Base64 an toàn."""
    raw_str = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw_str.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str) -> tuple[datetime, str]:
    """Giải mã con trỏ Base64 thành (created_at, id)."""
    try:
        decoded_bytes = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
        parts = decoded_bytes.decode("utf-8").split("|", 1)
        created_at = datetime.fromisoformat(parts[0])
        item_id = parts[1]
        return created_at, item_id
    except Exception as exc:
        raise ValueError("Cursor không hợp lệ hoặc bị hỏng định dạng.") from exc


async def fetch_tasks_keyset(
    session: AsyncSession,
    cursor: str | None = None,
    limit: int = 20,
) -> CursorPage[TaskRead]:
    # Lấy dư 1 bản ghi (limit + 1) để xác định xem còn trang tiếp theo hay không
    stmt = select(TaskModel).order_by(desc(TaskModel.created_at), desc(TaskModel.id)).limit(limit + 1)

    if cursor:
        cursor_dt, cursor_id = decode_cursor(cursor)
        # So sánh Tuple Composite chuẩn xác
        stmt = stmt.where(
            tuple_(TaskModel.created_at, TaskModel.id) < (cursor_dt, cursor_id)
        )

    result = await session.scalars(stmt)
    rows = list(result.all())

    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        next_cursor = encode_cursor(last_item.created_at, last_item.id)

    return CursorPage(
        items=[TaskRead.model_validate(item) for item in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )
```

---

### 4. Triển khai Webhook Receiver với xác thực HMAC-SHA256 & Chống Replay

Dưới đây là một Dependency FastAPI chuẩn công nghiệp để xác thực Webhook:

```python
import hashlib
import hmac
import time
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

WEBHOOK_SECRET = "whsec_live_test_secret_key_antigravity_2026"
TOLERANCE_SECONDS = 300  # Chặn replay attack vượt quá 5 phút


class WebhookPayload(BaseModel):
    event: str
    data: dict[str, str | int]


async def verify_webhook_signature(
    request: Request,
    x_webhook_signature: Annotated[str, Header()],
    x_webhook_timestamp: Annotated[int, Header()],
) -> bytes:
    """Dependency xác thực chữ ký HMAC-SHA256 và chống Replay Attack."""
    # 1. Kiểm tra timestamp để chống Replay Attack
    current_time = int(time.time())
    if abs(current_time - x_webhook_timestamp) > TOLERANCE_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook timestamp quá cũ hoặc lệch múi giờ (vượt quá 5 phút).",
        )

    # 2. Đọc raw body bytes (bắt buộc dùng raw bytes, không dùng parsed JSON)
    raw_body = await request.body()

    # 3. Tính toán chữ ký HMAC-SHA256 theo format: t={timestamp}.v1={body}
    signed_payload = f"t={x_webhook_timestamp}.v1=".encode("utf-8") + raw_body
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    # 4. So sánh constant-time bằng hmac.compare_digest để chống Timing Attack
    if not hmac.compare_digest(expected_signature, x_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chữ ký Webhook không hợp lệ!",
        )

    return raw_body
```

---

## ⚠️ Lỗi thường gặp

### 1. Không kiểm tra Request Fingerprint trong Idempotency Key
Nhiều kỹ sư chỉ lưu `Idempotency-Key` mà không kiểm tra hash của request payload. Hậu quả là client vô tình gửi cùng một key cho 2 đơn hàng có số tiền khác nhau (ví dụ: gửi thanh toán 100k, sau đó gọi lại cùng key với số tiền 500k), server lập tức trả về kết quả 100k cũ, gây sai lệch nghiêm trọng về tài chính và kế toán.

### 2. Race Condition khi nhiều Worker cùng xử lý một Idempotency Key
Nếu dùng 2 bước riêng biệt: `await redis.get(key)` sau đó `await redis.set(key)`, hai request gửi đến cùng một mili-giây trên 2 workers khác nhau sẽ đều thấy key chưa tồn tại và cùng tiến hành thực thi nghiệp vụ kép. Luôn bắt buộc sử dụng **`SET key value EX seconds NX`** (Atomic Set if Not Exists) để thiết lập khóa phân tán ngay từ bước đầu tiên!

### 3. Keyset Pagination thiếu cột Unique dự phòng (Tie-breaker)
Nếu chỉ phân trang dựa trên `created_at`:
```sql
WHERE created_at < :last_created_at ORDER BY created_at DESC
```
Khi có 5 bản ghi được tạo ra trong cùng một microsecond (`created_at` bằng hệt nhau), câu lệnh sẽ bỏ qua hoàn toàn 4 bản ghi còn lại khi chuyển trang! Do đó, **luôn luôn phải kết hợp thêm khóa chính `id` làm tie-breaker**: `(created_at, id) < (:dt, :id)`.

### 4. Bỏ qua cấu hình `Vary` Header khi dùng Versioning qua Header
Nếu bạn triển khai API Versioning qua Header (`X-API-Version` hoặc `Accept`) nhưng không bổ sung `Vary: X-API-Version` trong HTTP response, các CDN hoặc Caching Proxy ở tầng trung gian (Cloudflare, Varnish) sẽ cache kết quả của Client gọi v1 và trả nhầm cho Client gọi v2.

### 5. So sánh chữ ký Webhook bằng toán tử `==` và bỏ qua Timestamp
Sai lầm phổ biến khi tích hợp Webhook là so sánh `if signature == expected:` và không kiểm tra header timestamp.
- *Hậu quả*: Toán tử `==` trả về `False` ngay khi gặp ký tự sai đầu tiên, khiến thời gian so sánh phụ thuộc vào số ký tự khớp, tạo điều kiện cho hacker thực hiện tấn công **Side-channel Timing Attack**. Đồng thời, kẻ nghe lén có thể bắt gói tin cũ và gửi lại (Replay Attack) vô hạn lần.
- *Khắc phục*: Luôn dùng **`hmac.compare_digest()`** để so sánh constant-time và giới hạn độ trễ timestamp trong vòng 300 giây.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Idempotency Guard với SHA-256 Fingerprint
Viết một hàm tiện ích `verify_and_lock_idempotency(redis, key, body, ttl)`:
1. Tạo mã hash SHA-256 của `body`.
2. Kiểm tra trên Redis: Nếu đang xử lý (`IN_PROGRESS`), ném lỗi HTTP 409. Nếu đã xong (`COMPLETED`), kiểm tra xem hash có khớp không; nếu không khớp ném HTTP 422, nếu khớp trả về kết quả đã cache.
3. Nếu chưa tồn tại: Đặt cờ `IN_PROGRESS` với TTL 60 giây và trả về cờ cho phép tiếp tục.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import hashlib
import json
from typing import Any
from fastapi import HTTPException, status
from redis.asyncio import Redis


async def verify_and_lock(
    redis: Redis,
    key: str,
    payload_bytes: bytes,
    ttl_seconds: int = 60,
) -> dict[str, Any] | None:
    hasher = hashlib.sha256(payload_bytes)
    fingerprint = hasher.hexdigest()
    redis_key = f"idem:{key}"

    raw = await redis.get(redis_key)
    if raw:
        data = json.loads(raw)
        if data.get("fingerprint") != fingerprint:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Payload không khớp với Idempotency-Key ban đầu.",
            )
        if data.get("status") == "IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Yêu cầu đang được xử lý song song.",
            )
        return data.get("response")

    # Lock mới
    record = json.dumps({"status": "IN_PROGRESS", "fingerprint": fingerprint})
    acquired = await redis.set(redis_key, record, ex=ttl_seconds, nx=True)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Xung đột khóa phân tán.",
        )
    return None
```
</details>

---

### Bài tập 2: Dynamic Rate Limiter theo vai trò người dùng (User Role Tiers)
Thiết kế một dependency `TieredRateLimiter`:
- Khách vãng lai (`Anonymous`): 20 requests / phút.
- Người dùng chuẩn (`MEMBER`): 120 requests / phút.
- Quản trị viên (`ADMIN`): 1000 requests / phút.
Tích hợp trả về đầy đủ các headers: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import time
from typing import Any
from fastapi import HTTPException, Request, Response, status
from redis.asyncio import Redis


class TieredRateLimiter:

    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.tiers = {
            "ANONYMOUS": 20,
            "MEMBER": 120,
            "ADMIN": 1000,
        }

    async def __call__(self, request: Request, response: Response) -> None:
        user: dict[str, Any] | None = getattr(request.state, "user", None)
        role = user.get("role", "ANONYMOUS") if user else "ANONYMOUS"
        identifier = user.get("id", request.client.host if request.client else "unknown")

        limit = self.tiers.get(role, 20)
        window = 60
        now = int(time.time())
        key = f"ratelimit:{role}:{identifier}:{now // window}"

        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, window)

        remaining = max(0, limit - count)
        reset = window - (now % window)

        response.headers["RateLimit-Limit"] = str(limit)
        response.headers["RateLimit-Remaining"] = str(remaining)
        response.headers["RateLimit-Reset"] = str(reset)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Vượt quá hạn mức yêu cầu của vai trò hiện tại.",
                headers={"Retry-After": str(reset)},
            )
```
</details>

---

### Bài tập 3: Keyset Cursor Paginator 2 chiều (Previous & Next Cursor)
Mở rộng bộ phân trang Keyset Cursor ở phần ví dụ thực hành:
1. Cho phép client truyền cả `before_cursor` để lùi lại trang trước hoặc `after_cursor` để tiến tới trang sau.
2. Xử lý câu truy vấn đảo chiều `ORDER BY created_at ASC, id ASC` khi truy vấn lùi trang và đảo ngược mảng kết quả trả về để người dùng luôn nhận được danh sách theo thứ tự thời gian giảm dần.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import base64
from datetime import datetime
from typing import Any
from sqlalchemy import asc, desc, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession


def build_keyset_query(
    model: Any,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    limit: int = 20,
) -> tuple[Any, bool]:
    is_backward = before_cursor is not None
    cursor = before_cursor if is_backward else after_cursor

    stmt = select(model)

    if cursor:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        dt_str, item_id = raw.split("|", 1)
        cur_dt = datetime.fromisoformat(dt_str)

        if is_backward:
            # Lùi trang: Lấy các bản ghi lớn hơn cursor
            stmt = stmt.where(tuple_(model.created_at, model.id) > (cur_dt, item_id)).order_by(
                asc(model.created_at), asc(model.id)
            )
        else:
            # Tiến trang: Lấy các bản ghi nhỏ hơn cursor
            stmt = stmt.where(tuple_(model.created_at, model.id) < (cur_dt, item_id)).order_by(
                desc(model.created_at), desc(model.id)
            )
    else:
        stmt = stmt.order_by(desc(model.created_at), desc(model.id))

    return stmt.limit(limit + 1), is_backward
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được nguyên lý IETF Idempotency-Key và cách chống Race Condition khi có 2 request retry song song.
- [ ] Tôi biết cách băm SHA-256 Payload Fingerprint để phát hiện hành vi tái sử dụng nhầm Idempotency Key.
- [ ] Tôi phân biệt được 4 thuật toán Rate Limiting: Fixed Window, Sliding Window, Token Bucket, Leaky Bucket và biết khi nào nên dùng thuật toán nào.
- [ ] Tôi biết cách viết Redis Lua Script để kiểm tra giới hạn tần suất một cách nguyên tử (atomic).
- [ ] Tôi nắm vững các tiêu đề IETF: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`, `Retry-After`.
- [ ] Tôi giải thích được vì sao `OFFSET` lớn làm suy sụp hiệu năng cơ sở dữ liệu và cách Keyset Pagination giải quyết triệt để với độ phức tạp $O(1)$.
- [ ] Tôi biết cách triển khai Deprecation và Sunset headers (RFC 8594) khi phát hành phiên bản API mới.

---

## 📚 Đọc thêm

- [IETF Draft: The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)
- [IETF Draft: RateLimit Header Fields for HTTP](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
- [RFC 8594: The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594.html)
- [Stripe Engineering: Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- [Tiếp theo: Bài 08 – Bảo mật: OWASP API Top 10](./08-security-owasp.md)

<!-- nav:bottom -->
---

[⬅️ Clean Architecture](./06-clean-architecture.md) | [📚 Mục lục Senior](./README.md) | [Bảo mật: OWASP API Top 10 ➡️](./08-security-owasp.md)
<!-- /nav:bottom -->
