<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 03
<!-- /nav:top -->

# Caching với Redis

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 02: Profiling & hiệu năng](./02-profiling-performance.md) và [Middleware, lifespan & background tasks](../03-middle/08-middleware-lifespan-background.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Làm chủ thư viện `redis.asyncio` trong FastAPI**: Khởi tạo và quản lý Connection Pool tối ưu thông qua vòng đời ứng dụng `lifespan` và hệ thống Dependency Injection.
- **Phân biệt và ứng dụng thành thạo các chiến lược Caching**: Cache-Aside (Lazy Loading), Write-Through, và Write-Behind (Write-Back) phù hợp với từng kịch bản đọc/ghi của hệ thống.
- **Thiết kế chiến lược vô hiệu hóa Cache (Cache Invalidation)**: Áp dụng Key Prefixing Versioning (`v1:task:{id}`) và Tag-based Invalidation bằng Redis Sets để xóa hàng loạt cache liên quan.
- **Phòng thủ toàn diện trước các thảm họa Caching kinh điển**:
  - **Cache Stampede (Thundering Herd)**: Triển khai Distributed Lock với cờ `SET NX EX` và cơ chế giải phóng an toàn bằng Lua Script, hoặc thuật toán xác suất **XFetch (Probabilistic Early Expiration)**.
  - **Cache Penetration**: Khắc phục bằng kỹ thuật Lưu trữ giá trị rỗng (Null Cache with Short TTL) và hiểu ứng dụng của Bloom Filter.
  - **Cache Avalanche**: Triệt tiêu hiện tượng sập nguồn đồng loạt bằng kỹ thuật ngẫu nhiên hóa thời gian sống (TTL Jitter).
- **Tuần tự hóa dữ liệu hiệu năng cao**: Kết hợp Pydantic v2 schemas và `orjson` để đóng gói dữ liệu vào Redis với dung lượng nhỏ nhất và tốc độ giải mã nhanh nhất.

---

## 🔁 So sánh với C# / ASP.NET

Trong hệ sinh thái .NET, caching phân tán là một phần được trừu tượng hóa rất tốt trong thư viện `Microsoft.Extensions.Caching` cùng thư viện kết nối chuẩn `StackExchange.Redis`:

| Khái niệm / Thành phần | C# / ASP.NET Core | Python / FastAPI (`redis.asyncio`) |
|---|---|---|
| **Interface bộ nhớ đệm** | `IDistributedCache` (hỗ trợ `GetStringAsync`, `SetStringAsync`, `RefreshAsync`). | `redis.asyncio.Redis` client (gọi trực tiếp các lệnh Redis native: `get`, `set`, `delete`, `mget`). |
| **Giải pháp Caching đa tầng** | **HybridCache** (.NET 9) kết hợp L1 In-Memory (`IMemoryCache`) và L2 Distributed (`IDistributedCache`). | Tự xây dựng pattern hoặc dùng thư viện (kết hợp `cachetools` L1 in-process + `redis.asyncio` L2). |
| **Client kết nối** | `StackExchange.Redis` với cơ chế Multiplexing chia sẻ một TCP socket duy nhất cho mọi luồng. | `redis.asyncio.ConnectionPool` quản lý một nhóm kết nối socket bất đồng bộ trên Event Loop. |
| **Quản lý vòng đời Client** | Đăng ký Singleton `IConnectionMultiplexer` trong `IServiceCollection` (`Program.cs`). | Khởi tạo `ConnectionPool` trong FastAPI `@asynccontextmanager lifespan`, lưu vào `app.state.redis`. |
| **Tuần tự hóa DTO** | `System.Text.Json.JsonSerializer.SerializeToUtf8Bytes()` | `orjson.dumps()` / `model.model_dump_json()`. |
| **Distributed Lock** | `RedLock.net` (Triển khai thuật toán Redlock của Salvatore Sanfilippo). | `redis-py` Lock (`redis.lock()`) hoặc triển khai custom lock với Lua script atomicity. |

---

## 📖 Lý thuyết

### 1. Quản lý Kết nối `redis.asyncio` trong FastAPI Lifespan

Trong môi trường bất đồng bộ `asyncio`, việc khởi tạo đối tượng `redis.Redis()` mới cho từng HTTP request là một phản mẫu tai hại (anti-pattern). Nó làm cạn kiệt file descriptors của hệ điều hành và gây độ trễ handshake TCP lặp đi lặp lại.

Mô hình chuẩn Senior: Khởi tạo một **ConnectionPool** dùng chung duy nhất khi server khởi động (startup), lưu vào `app.state`, cung cấp cho các router qua `Depends()`, và giải phóng toàn bộ kết nối khi server dừng (shutdown):

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
import redis.asyncio as aioredis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Khởi tạo Connection Pool lúc startup
    pool = aioredis.ConnectionPool.from_url(
        "redis://localhost:6379/0",
        max_connections=50,
        decode_responses=False,  # Để False để nhận dữ liệu dạng bytes, tối ưu cho orjson
        socket_timeout=2.0,
        socket_connect_timeout=2.0,
    )
    redis_client = aioredis.Redis(connection_pool=pool)
    app.state.redis = redis_client
    print("[Lifespan] Đã kết nối Redis Connection Pool thành công.")
    try:
        yield
    finally:
        # Đóng pool lúc shutdown
        await redis_client.aclose()
        await pool.disconnect()
        print("[Lifespan] Đã ngắt kết nối Redis an toàn.")


def get_redis(request: Request) -> aioredis.Redis:
    """Dependency trích xuất Redis client từ application state."""
    return request.app.state.redis
```

---

### 2. Các chiến lược Caching kinh điển

Là một kiến trúc sư hệ thống, bạn cần lựa chọn chiến lược phù hợp dựa trên tỷ lệ Đọc/Ghi (Read/Write Ratio) của dữ liệu:

```text
1. CACHE-ASIDE (LAZY LOADING)
   Client ──► Cache Hit? ──Yes──► Trả về dữ liệu
                 │ No
                 ▼
              Query DB ──► Lưu vào Cache (kèm TTL) ──► Trả về

2. READ-THROUGH
   Client ──► Cache Provider ──► Cache Hit? ──Yes──► Trả về dữ liệu
                                    │ No (Provider tự query DB)
                                    ▼
                                 Query DB ──► Tự nạp Cache ──► Trả về

3. WRITE-THROUGH
   Client ──► Ghi đồng thời vào Cache VÀ Database ──► Trả về thành công

4. WRITE-BEHIND (WRITE-BACK)
   Client ──► Ghi vào Cache (Nhanh) ──► Trả về ngay
                 │
                 ▼ (Bất đồng bộ sau đó)
             Worker gom batch ghi xuống DB
```

#### 2.1 Cache-Aside (Lazy Loading)
- **Cơ chế**: Ứng dụng luôn kiểm tra cache trước. Nếu có (Cache Hit), trả về ngay. Nếu không có (Cache Miss), đọc từ Database, ghi kết quả vào Cache kèm TTL, sau đó trả về.
- **Ưu điểm**: Chỉ những dữ liệu thực sự được đọc mới nằm trong cache (tiết kiệm RAM). Khi node cache bị crash, hệ thống vẫn hoạt động (chỉ tăng tải tạm thời lên DB).
- **Nhược điểm**: Cache miss phải tốn 3 chặng mạng (Cache Read -> DB Read -> Cache Write). Dữ liệu có thể bị cũ (stale) nếu cập nhật DB mà quên xóa cache.

#### 2.2 Read-Through
- **Cơ chế**: Về bản chất vận hành tương tự Cache-Aside, nhưng trách nhiệm truy vấn DB khi miss được ủy quyền cho **Cache Provider / Thư viện Cache Adapter** thay vì mã ứng dụng phải tự viết các khối `if data is None: query_db()` lặp đi lặp lại. Ứng dụng xem Cache Provider như nguồn dữ liệu duy nhất.
- **Đối chiếu C# / .NET**: Tương đương với API `GetOrCreateAsync(key, factory)` của `HybridCache` (.NET 9) hoặc `EasyCaching`.
- **Ưu điểm**: Đóng gói code gọn gàng, tách biệt hoàn toàn tầng Web khỏi chi tiết cài đặt cache và DB.

#### 2.3 Write-Through
- **Cơ chế**: Khi ứng dụng cập nhật dữ liệu, nó sẽ ghi đồng thời vào cả Cache và Database trước khi trả về phản hồi cho client.
- **Ưu điểm**: Cache luôn luôn mới nhất (fresh), dữ liệu đọc ra không bao giờ bị trễ.
- **Nhược điểm**: Độ trễ khi ghi dữ liệu tăng gấp đôi. Nhiều dữ liệu được ghi vào cache nhưng có thể chẳng bao giờ được đọc tới (gây lãng phí tài nguyên bộ nhớ).

#### 2.4 Write-Behind (Write-Back)
- **Cơ chế**: Dữ liệu được ghi ngay vào Cache và phản hồi thành công lập tức cho client. Một tiến trình chạy ngầm định kỳ hoặc theo batch sẽ đọc dữ liệu từ cache và ghi xuống Database.
- **Trường hợp sử dụng**: Các hệ thống ghi cực nhiều và yêu cầu độ trễ dưới 2ms, chấp nhận mất mát nhỏ khi crash (ví dụ: đếm lượt xem bài viết, lượt click quảng cáo, tracking GPS tài xế).

---

### 3. Vô hiệu hóa Cache (Cache Invalidation)

> *"Có hai thứ khó nhất trong khoa học máy tính: Vô hiệu hóa bộ nhớ đệm và Đặt tên cho biến."* — Phil Karlton

#### 3.1 Quy ước đặt tên Key & Versioning
Tuyệt đối không đặt tên key tùy tiện. Hãy xây dựng một namespace có cấu trúc phân cấp ngăn cách bởi dấu hai chấm `:`:
`{app_name}:{version}:{entity}:{entity_id}:{sub_resource}`

Ví dụ:
- `taskflow:v1:task:1024`
- `taskflow:v1:user:88:profile`

Khi cấu trúc model thay đổi hoặc muốn xóa toàn bộ cache mà không muốn dùng lệnh nguy hiểm `FLUSHALL`, bạn chỉ cần nâng version prefix từ `v1` lên `v2`.

#### 3.2 Tag-Based Invalidation bằng Redis Sets
Khi người dùng cập nhật một Project, toàn bộ các cache liên quan (danh sách tasks của project, báo cáo tiến độ, thông tin thành viên) cần bị xóa.
Ta có thể dùng một Redis Set để gom nhóm các key thuộc cùng một Tag:
- Khi ghi cache key `taskflow:v1:task:1024`, ta thêm key này vào set `tag:project:50`.
- Khi Project 50 có thay đổi, ta đọc toàn bộ members trong set `tag:project:50` bằng lệnh `SMEMBERS`, gọi `UNLINK` xóa sạch các key đó trong 1 lệnh duy nhất, rồi xóa luôn set tag.

---

### 4. Phòng chống các thảm họa Caching cấp độ Production

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CÁC THẢM HỌA CACHING KINH ĐIỂN                  │
│                                                                        │
│ 1. CACHE STAMPEDE: 1 Hot Key hết hạn ──► Hàng ngàn request ập vào DB    │
│    -> Giải pháp: Distributed Lock (SET NX) hoặc XFetch                 │
│                                                                        │
│ 2. CACHE PENETRATION: Query Key không tồn tại (-999) ──► Luôn đâm DB   │
│    -> Giải pháp: Lưu Null Cache (TTL ngắn) hoặc Bloom Filter           │
│                                                                        │
│ 3. CACHE AVALANCHE: Hàng loạt Keys cùng chết tại 1 giây ──► DB sập     │
│    -> Giải pháp: TTL Jitter (Ngẫu nhiên hóa thời gian sống)            │
└────────────────────────────────────────────────────────────────────────┘
```

#### 4.1 Thảm họa 1: Cache Stampede (Thundering Herd)
- **Hiện tượng**: Một key có lượng truy vấn cực lớn (ví dụ: bảng xếp hạng trang chủ) vừa hết hạn TTL. Tại đúng phần nghìn giây đó, 5,000 requests đồng thời nhận thấy Cache Miss và cùng lúc chạy câu truy vấn SQL phức tạp đập vào Database, khiến CPU của Database vọt lên 100% và sập toàn bộ hệ thống.
- **Giải pháp 1: Distributed Lock (Khóa phân tán)**:
  Chỉ request đầu tiên nhận thấy Cache Miss mới giành được Lock (`SET lock_key uuid NX EX 10`). Request này sẽ query DB và cập nhật cache. Các request khác khi không lấy được lock sẽ tạm dừng (`asyncio.sleep(0.05)`) rồi thử đọc lại cache.
- **Giải pháp 2: Thuật toán XFetch (Probabilistic Early Expiration)**:
  Trước khi key hết hạn một khoảng thời gian ngẫu nhiên dựa trên thuật toán xác suất, request may mắn sẽ chủ động tính toán lại dữ liệu ngầm và làm mới TTL trước khi key thực sự biến mất!

#### 4.2 Thảm họa 2: Cache Penetration (Xuyên thủng Cache)
- **Hiện tượng**: Kẻ tấn công liên tục gửi yêu cầu tìm kiếm các ID không hề tồn tại trong hệ thống (ví dụ `id = -1`, `id = "invalid_uuid"`). Vì không tồn tại, Redis không có cache, Database cũng trả về rỗng. Kết quả: 100% traffic độc hại đều đi thẳng xuống Database.
- **Giải pháp**:
  - **Null Caching**: Khi Database trả về `None`, ta vẫn lưu vào Redis một giá trị rỗng đặc biệt (ví dụ `"{}"` hoặc `"__NULL__"`) nhưng kèm theo **TTL cực ngắn** (ví dụ 30s đến 60s). Các request tiếp theo với ID rác đó sẽ hit cache rỗng và không chạm tới DB.
  - **Bloom Filter**: Cấu trúc dữ liệu xác suất cho phép kiểm tra xem một phần tử "chắc chắn không tồn tại" hay "có khả năng tồn tại" với chi phí RAM siêu nhỏ.

#### 4.3 Thảm họa 3: Cache Avalanche (Tuyết lở Cache)
- **Hiện tượng**: Bạn nạp 100,000 bản ghi sản phẩm vào cache lúc 08:00 sáng với cùng một TTL cố định là 3,600 giây (1 tiếng). Đúng 09:00:00, toàn bộ 100,000 keys cùng hết hạn trong cùng một giây. Hàng triệu người dùng truy cập lập tức dội thẳng xuống Database như một cơn bão tuyết lở.
- **Giải pháp: TTL Jitter**:
  Luôn cộng thêm một giá trị ngẫu nhiên (Jitter) vào thời gian TTL:
  $$\text{Actual TTL} = \text{Base TTL} + \text{random}(0, \text{Jitter Range})$$
  Ví dụ: Base TTL là 3600s, cộng thêm ngẫu nhiên từ 0 đến 300s. Khi đó, các key sẽ phân rã rải rác từ 3600s đến 3900s, triệt tiêu hoàn toàn đỉnh nhọn truy cập.

---

## 💻 Ví dụ thực hành

### 1. Triển khai Cache-Aside Pattern hoàn chỉnh kèm Null-Cache và TTL Jitter

Dưới đây là một Service quản lý Task trong FastAPI kết hợp toàn bộ các kỹ thuật phòng thủ:

```python
import random
from typing import Any
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel
import redis.asyncio as aioredis
import orjson

app = FastAPI()


class TaskDTO(BaseModel):
    id: int
    title: str
    status: str
    assignee_id: int


NULL_CACHE_SENTINEL = b"__NULL__"


def calculate_jittered_ttl(base_ttl: int = 300, jitter_seconds: int = 60) -> int:
    """Cộng thêm jitter ngẫu nhiên để chống Cache Avalanche."""
    return base_ttl + random.randint(0, jitter_seconds)


class TaskCacheService:

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client

    def _build_key(self, task_id: int) -> str:
        return f"taskflow:v1:task:{task_id}"

    async def get_task_by_id(self, task_id: int) -> TaskDTO | None:
        cache_key = self._build_key(task_id)

        # 1. Đọc từ Redis Cache
        cached_bytes = await self.redis.get(cache_key)

        if cached_bytes is not None:
            # Kiểm tra xem có phải Null Cache chống Penetration không
            if cached_bytes == NULL_CACHE_SENTINEL:
                return None
            data_dict = orjson.loads(cached_bytes)
            return TaskDTO.model_validate(data_dict)

        # 2. Cache Miss: Truy vấn Database giả lập
        task = await self._query_database_mock(task_id)

        if task is None:
            # ✅ PHÒNG THỦ CACHE PENETRATION: Lưu sentinel rỗng với TTL ngắn (60s)
            await self.redis.set(cache_key, NULL_CACHE_SENTINEL, ex=60)
            return None

        # 3. Ghi vào Cache với TTL kèm Jitter
        ttl = calculate_jittered_ttl(base_ttl=600, jitter_seconds=120)
        payload = orjson.dumps(task.model_dump())
        await self.redis.set(cache_key, payload, ex=ttl)
        return task

    async def invalidate_task(self, task_id: int) -> None:
        """Xóa cache khi có update hoặc delete."""
        cache_key = self._build_key(task_id)
        # Sử dụng unlink thay vì delete để giải phóng bộ nhớ async trong Redis
        await self.redis.unlink(cache_key)

    async def _query_database_mock(self, task_id: int) -> TaskDTO | None:
        # Giả lập truy vấn SQL
        if task_id <= 0 or task_id > 10_000:
            return None
        return TaskDTO(
            id=task_id,
            title=f"Task #{task_id}",
            status="IN_PROGRESS",
            assignee_id=42,
        )
```

---

### 2. Triển khai Distributed Lock an toàn chống Cache Stampede

Khi nhiều tiến trình cùng muốn tính toán một tác vụ đắt đỏ, chúng ta sử dụng cơ chế Distributed Lock. 
*Lưu ý bảo mật*: Khi giải phóng lock, phải dùng **Lua script** để đảm bảo tính nguyên tử (atomic): chỉ người sở hữu lock (nắm giữ đúng `token` bí mật) mới có quyền xóa lock, tránh trường hợp lock đã hết hạn và tiến trình A vô tình xóa mất lock của tiến trình B!

```python
import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import uuid
import redis.asyncio as aioredis

# Lua script kiểm tra token trước khi xóa lock đảm bảo nguyên tử
RELEASE_LOCK_LUA_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


@asynccontextmanager
async def distributed_lock(
    redis_client: aioredis.Redis,
    lock_key: str,
    expire_seconds: int = 10,
    retry_delay: float = 0.05,
    max_retries: int = 20,
) -> AsyncGenerator[bool, None]:
    token = str(uuid.uuid4())
    acquired = False

    for attempt in range(max_retries):
        # Lệnh SET với cờ nx=True (Only set if Not Exists) và ex=expire_seconds
        ok = await redis_client.set(lock_key, token, nx=True, ex=expire_seconds)
        if ok:
            acquired = True
            break
        await asyncio.sleep(retry_delay)

    try:
        yield acquired
    finally:
        if acquired:
            # Giải phóng lock an toàn bằng Lua Script
            await redis_client.eval(RELEASE_LOCK_LUA_SCRIPT, 1, lock_key, token)


async def get_heavy_analytics_report(redis_client: aioredis.Redis, report_id: str) -> dict[str, Any]:
    cache_key = f"taskflow:v1:analytics:{report_id}"
    lock_key = f"lock:{cache_key}"

    # 1. Thử đọc từ Cache
    cached = await redis_client.get(cache_key)
    if cached:
        return orjson.loads(cached)

    # 2. Bị Cache Miss -> Giành Distributed Lock chống Stampede
    async with distributed_lock(redis_client, lock_key, expire_seconds=15) as has_lock:
        if has_lock:
            # Kiểm tra lại một lần nữa (Double-checked locking pattern)
            recheck = await redis_client.get(cache_key)
            if recheck:
                return orjson.loads(recheck)

            # Tính toán báo cáo nặng tốn nhiều CPU và SQL
            print(f"-> Đang tính toán báo cáo nặng {report_id} từ Database...")
            await asyncio.sleep(0.3)  # Giả lập query DB tốn 300ms
            computed_data = {"report_id": report_id, "total_revenue": 985000.0, "status": "FINAL"}

            # Lưu vào cache kèm TTL
            await redis_client.set(cache_key, orjson.dumps(computed_data), ex=300)
            return computed_data
        else:
            # Các requests đến sau không giành được lock -> Polling chờ tiến trình nắm lock tính toán xong
            for _ in range(30):
                await asyncio.sleep(0.1)
                fallback = await redis_client.get(cache_key)
                if fallback:
                    return orjson.loads(fallback)
            raise RuntimeError("Hệ thống đang quá tải tính toán báo cáo, vui lòng thử lại sau!")
```

---

## ⚠️ Lỗi thường gặp

### 1. Sử dụng module `pickle` để lưu dữ liệu vào Redis
Nhiều lập trình viên dùng `pickle.dumps()` để nạp trực tiếp Python objects vào Redis vì tiện lợi.
*Hậu quả nghiêm trọng*:
- **Rủi ro bảo mật thực thi mã từ xa (RCE)**: Nếu Redis bị xâm nhập hoặc kẻ xấu giả mạo chuỗi byte, việc gọi `pickle.loads()` có thể thực thi bất kỳ mã độc hại nào trên server.
- **Không tương thích đa ngôn ngữ**: Các microservice viết bằng Go, C#, Node.js không thể đọc được dữ liệu mà Python ghi vào.
*Giải pháp*: Luôn dùng chuẩn định dạng mở **JSON (qua `orjson`)** hoặc **MessagePack (`msgpack`)**.

### 2. Quên đặt TTL (Time-To-Live) cho Redis Keys
Lưu dữ liệu vào Redis mà quên tham số `ex` (expiration). Sau vài tháng hoạt động, hàng triệu keys rác tích lũy khiến dung lượng RAM của cụm Redis chạm ngưỡng `maxmemory`. Lúc này, nếu chính sách evict là `noeviction`, Redis sẽ từ chối toàn bộ lệnh ghi mới và làm sập ứng dụng!

### 3. Dùng lệnh `KEYS *` trên môi trường Production
Lệnh `KEYS *` là một lệnh chặn đồng bộ (blocking command) quét toàn bộ keyspace. Trên một máy chủ Redis chứa 10 triệu keys, việc gõ `KEYS *` sẽ làm đóng băng toàn bộ tiến trình Redis trong nhiều giây, khiến tất cả các backend services phụ thuộc đều bị timeout hàng loạt.
*Giải pháp*: Dùng `SCAN` với con trỏ cursor lặp từng đợt, hoặc tốt nhất là quản lý danh sách key qua Redis Sets.

### 4. Giải phóng Distributed Lock sai cách
Xóa lock bằng hàm `await redis.delete(lock_key)` mà không kiểm tra token sở hữu. Nếu tiến trình A chạy tác vụ quá thời gian expire của lock, lock tự động hết hạn và tiến trình B nhảy vào lấy lock mới. Khi tiến trình A chạy xong, nó gọi `delete(lock_key)`, vô tình xóa mất lock hợp lệ của tiến trình B!

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Generic Caching Decorator `@cached` cho hàm async
Viết một decorator `@cached(ttl_seconds=300, jitter=30)` áp dụng cho các hàm async trong FastAPI.
Yêu cầu:
1. Tự động sinh `cache_key` dựa trên tên module, tên hàm và các đối số truyền vào (args, kwargs).
2. Tích hợp `orjson` để serialize và deserialize kết quả.
3. Tích hợp TTL Jitter để chống Cache Avalanche.

<details>
<summary>💡 Gợi ý</summary>

```python
from functools import wraps
import inspect
import random
from typing import Any, Callable
import orjson
import redis.asyncio as aioredis


def cached(
    redis_client: aioredis.Redis,
    ttl_seconds: int = 300,
    jitter: int = 30,
) -> Callable:

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Tạo key từ tên hàm và tham số
            func_name = func.__qualname__
            params_str = f"{args}_{sorted(kwargs.items())}"
            cache_key = f"cache:{func_name}:{hash(params_str)}"

            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return orjson.loads(cached_data)

            # Thực thi hàm gốc nếu cache miss
            result = await func(*args, **kwargs)

            # Ghi cache với jitter
            actual_ttl = ttl_seconds + random.randint(0, jitter)
            await redis_client.set(cache_key, orjson.dumps(result), ex=actual_ttl)
            return result

        return wrapper

    return decorator
```
</details>

---

### Bài tập 2: Tag-Based Cache Invalidation cho E-Commerce Product Catalog
Một hệ sinh thái bán hàng có hàng ngàn sản phẩm được phân loại theo danh mục (`category_id`).
Yêu cầu:
1. Khi nạp cache chi tiết sản phẩm (`product:{id}`), thêm key đó vào một Redis Set đại diện cho danh mục (`tag:category:{cat_id}`).
2. Viết hàm `invalidate_category(cat_id: int)` sử dụng `SMEMBERS` để lấy danh sách toàn bộ các sản phẩm thuộc danh mục đó và gọi lệnh `UNLINK` xóa sạch chúng cùng một lúc.

<details>
<summary>💡 Gợi ý</summary>

```python
import redis.asyncio as aioredis
import orjson


class ProductCatalogCache:

    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    async def cache_product(self, product_id: int, category_id: int, data: dict) -> None:
        prod_key = f"store:product:{product_id}"
        tag_key = f"tag:category:{category_id}"

        # 1. Lưu thông tin sản phẩm
        await self.redis.set(prod_key, orjson.dumps(data), ex=3600)

        # 2. Đăng ký key này vào Tag Set của category
        await self.redis.sadd(tag_key, prod_key)

    async def invalidate_category(self, category_id: int) -> int:
        tag_key = f"tag:category:{category_id}"

        # Đọc tất cả các keys thuộc tag (với set cực lớn >10,000 keys, nên dùng sscan_iter để tránh nghẽn I/O)
        keys_to_delete = await self.redis.smembers(tag_key)
        if not keys_to_delete:
            return 0

        # Unlink bất đồng bộ toàn bộ keys sản phẩm và chính tag_key (UNLINK không block event loop Redis)
        deleted_count = await self.redis.unlink(*keys_to_delete, tag_key)
        return deleted_count
```
</details>

---

### Bài tập 3: Triển khai thuật toán xác suất XFetch (Probabilistic Early Expiration)
Thay vì chờ key thực sự hết hạn, thuật toán XFetch tính toán xác suất làm mới cache sớm dựa trên công thức:
$$-\beta \times \delta \times \ln(r) > \text{TTL còn lại}$$
Trong đó:
- $\delta$ (delta): Thời gian (giây) cần thiết để tính toán lại dữ liệu.
- $\beta$: Hằng số điều chỉnh (thường đặt $\ge 1.0$).
- $r$: Số ngẫu nhiên phân bổ đều trong khoảng $(0, 1]$.
Yêu cầu: Viết hàm `xfetch_get_or_compute` mô phỏng thuật toán này để ngăn chặn hoàn toàn Cache Stampede.

<details>
<summary>💡 Gợi ý</summary>

```python
import math
import random
import time
from typing import Any, Callable, Coroutine
import orjson
import redis.asyncio as aioredis


async def xfetch_get_or_compute(
    redis_client: aioredis.Redis,
    key: str,
    compute_coro_fn: Callable[[], Coroutine[Any, Any, tuple[Any, float]]],
    ttl_seconds: int = 300,
    beta: float = 1.0,
) -> Any:
    """Thuật toán XFetch làm mới sớm theo xác suất."""
    cache_entry = await redis_client.get(key)

    if cache_entry:
        data = orjson.loads(cache_entry)
        value = data["value"]
        delta = data["delta"]  # Thời gian tính toán ở lần trước (giây)

        remaining_ttl = await redis_client.ttl(key)
        r = random.random()

        # Nếu điều kiện xác suất thỏa mãn: Làm mới sớm trước khi key chết!
        if remaining_ttl > 0 and (-beta * delta * math.log(r)) > remaining_ttl:
            print(f"[XFetch] Kích hoạt early refresh cho key {key} (TTL còn: {remaining_ttl}s)")
            start = time.perf_counter()
            new_value, comp_time = await compute_coro_fn()
            payload = orjson.dumps({"value": new_value, "delta": comp_time})
            await redis_client.set(key, payload, ex=ttl_seconds)
            return new_value

        return value

    # Trường hợp Cache Miss hoàn toàn:
    new_value, comp_time = await compute_coro_fn()
    payload = orjson.dumps({"value": new_value, "delta": comp_time})
    await redis_client.set(key, payload, ex=ttl_seconds)
    return new_value
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách cấu hình `redis.asyncio` Connection Pool tối ưu trong FastAPI `lifespan` và inject qua `Depends`.
- [ ] Tôi phân biệt được ưu nhược điểm của 3 chiến lược: Cache-Aside, Write-Through, và Write-Behind.
- [ ] Tôi hiểu vì sao không nên dùng `pickle` để lưu dữ liệu vào Redis và biết cách áp dụng `orjson`.
- [ ] Tôi giải thích được nguyên nhân gây ra Cache Stampede và biết cách dùng Distributed Lock (với Lua Script release) để ngăn chặn.
- [ ] Tôi hiểu cơ chế của Cache Penetration và biết cách dùng Null Cache có TTL ngắn để bảo vệ Database.
- [ ] Tôi nắm vững nguyên lý TTL Jitter để triệt tiêu hiện tượng Cache Avalanche.
- [ ] Tôi hiểu cách thức triển khai Tag-based cache invalidation thông qua Redis Sets.

---

## 📚 Đọc thêm

- [Redis Official Documentation: Distributed Locks with Redis (Redlock)](https://redis.io/docs/latest/develop/use/patterns/distributed-locks/)
- [Optimal Probabilistic Cache Expiration (XFetch Research Paper by V. Vattani et al.)](http://www.vldb.org/pvldb/vol8/p886-vattani.pdf)
- [redis-py Official Documentation (asyncio support)](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html)
- [Tiếp theo: Bài 04 – Task queue](./04-task-queues.md)

<!-- nav:bottom -->
---

[⬅️ Profiling & hiệu năng](./02-profiling-performance.md) | [📚 Mục lục Senior](./README.md) | [Task queue ➡️](./04-task-queues.md)
<!-- /nav:bottom -->
