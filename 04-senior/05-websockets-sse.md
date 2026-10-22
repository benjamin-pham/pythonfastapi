<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 05
<!-- /nav:top -->

# WebSocket & SSE

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 03: Caching với Redis](./03-caching-redis.md) và [Bài 01: Python internals & concurrency](./01-python-internals-concurrency.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Phân định rạch ròi giữa WebSocket và Server-Sent Events (SSE)**: Hiểu rõ sự khác biệt giữa giao thức song công 2 chiều (Full-duplex) và dòng dữ liệu một chiều (Simplex HTTP streaming), biết cách chọn đúng công nghệ cho đúng bài toán.
- **Làm chủ Server-Sent Events (SSE) trong FastAPI**: Sử dụng `fastapi.responses.StreamingResponse` với định dạng chuẩn `text/event-stream` để stream tiến độ công việc và stream từng token của mô hình ngôn ngữ lớn (LLM / Generative AI).
- **Thiết kế `ConnectionManager` chuyên nghiệp cho WebSocket**: Quản lý vòng đời kết nối, phân nhóm theo phòng (rooms/channels), broadcast tin nhắn và xử lý ngắt kết nối an toàn tránh rò rỉ bộ nhớ.
- **Giải quyết bài toán Xác thực kết nối (Authentication)**: Nắm vững các chiến lược vượt qua hạn chế không gửi được header của trình duyệt: Query Token, Handshake Ticket Pattern và Sec-WebSocket-Protocol.
- **Mở rộng Realtime đa Pod (Multi-Pod Scaling) với Redis Pub/Sub**: Xây dựng kiến trúc Message Backplane phân tán (tương đương SignalR Redis Backplane), đảm bảo tin nhắn được truyền tải xuyên suốt mọi Kubernetes Pods đằng sau Load Balancer.

---

## 🔁 So sánh với C# / ASP.NET

Trong hệ sinh thái ASP.NET Core, **SignalR** là thư viện thời gian thực mạnh mẽ bậc nhất, tự động hóa hầu hết các tầng phức tạp:

| Khái niệm / Tính năng | ASP.NET Core SignalR | FastAPI Realtime (`WebSocket` / `SSE`) |
|---|---|---|
| **Mô hình lập trình** | Trừu tượng hóa cấp cao thông qua `Hub` class (`Clients.All.SendAsync(...)`). | Sử dụng trực tiếp đối tượng `WebSocket` hoặc generator async trong `StreamingResponse`. |
| **Cơ chế Fallback giao thức** | Tự động hạ cấp linh hoạt: WebSockets $\to$ Server-Sent Events $\to$ Long Polling. | Không tự động hạ cấp; nhà phát triển tự quyết định sử dụng endpoint WebSocket hoặc SSE riêng biệt. |
| **Hỗ trợ Reconnect từ Client** | Thư viện client `@microsoft/signalr` tích hợp sẵn `.withAutomaticReconnect()`. | SSE có sẵn cơ chế reconnect native của trình duyệt (`EventSource`). WebSocket phải tự viết mã retry ở client. |
| **Định dạng dữ liệu** | Hỗ trợ JSON Hub Protocol hoặc Binary MessagePack Protocol tốc độ cao. | Text UTF-8 (JSON string) hoặc Binary frames (`bytes`). |
| **Xác thực kết nối** | SignalR Client tự động truyền JWT qua query `access_token` khi handshake. | Tự thiết kế Dependency trích xuất và xác thực token qua query parameter hoặc ticket. |
| **Mở rộng nhiều máy chủ (Scale-out)** | **SignalR Redis Backplane** (`AddStackExchangeRedis()`) hoặc Azure SignalR Service. | Tự triển khai **Redis Pub/Sub** lắng nghe kênh và forward tin nhắn xuống các local WebSocket sockets. |

> [!NOTE]
> Trong ASP.NET Core, khi scale-out nhiều máy chủ, bạn thường dùng gói `Microsoft.AspNetCore.SignalR.StackExchangeRedis` hoặc dịch vụ đám mây Azure SignalR Service để đồng bộ message giữa các instance. Trong hệ sinh thái Python / FastAPI, Redis Pub/Sub đóng vai trò backplane tương đương, giúp phát sóng message đến toàn bộ các worker process / container FastAPI đang kết nối với client.

---

## 📖 Lý thuyết

### 1. Cuộc đối đầu: WebSocket vs Server-Sent Events (SSE)

Một trong những sai lầm phổ biến nhất của các kỹ sư là coi WebSocket là giải pháp duy nhất cho mọi nhu cầu thời gian thực. Bảng so sánh sau đây sẽ định hình tư duy lựa chọn kiến trúc:

| Tiêu chí | WebSocket | Server-Sent Events (SSE) |
|---|---|---|
| **Chiều truyền tin** | **Full-duplex (2 chiều đồng thời)**: Server $\leftrightarrow$ Client. | **Simplex (1 chiều duy nhất)**: Server $\to$ Client. |
| **Giao thức mạng** | Bắt đầu bằng HTTP GET (Upgrade header), sau đó chuyển sang giao thức nhị phân riêng biệt: `ws://` hoặc `wss://`. | Thuần túy là giao thức **HTTP/1.1 hoặc HTTP/2** tiêu chuẩn với header `Content-Type: text/event-stream`. |
| **Tự động kết nối lại** | ❌ Không hỗ trợ native (Phải tự viết logic reconnect trong JavaScript). | ✅ **Tích hợp sẵn trong trình duyệt**: Trình duyệt tự động thử kết nối lại nếu bị đứt mạng. |
| **Hỗ trợ Proxy / Firewall** | Có thể bị chặn hoặc ngắt kết nối bởi một số corporate proxy/firewall khắt khe. | Hoạt động mượt mà qua mọi Proxy, CDN (Cloudflare), và API Gateway vì là HTTP chuẩn. |
| **Hỗ trợ Binary** | Hỗ trợ cả văn bản (Text UTF-8) và dữ liệu nhị phân (Binary Buffers). | Chỉ hỗ trợ chuỗi văn bản mã hóa UTF-8. |
| **Trường hợp sử dụng lý tưởng** | Game nhiều người chơi thời gian thực, bảng vẽ tương tác (Figma), ứng dụng giao dịch tài chính tần suất cao, ứng dụng Chat 2 chiều liên tục. | **Bảng điều khiển (Live Dashboard metrics)**, **Thông báo đẩy (In-app Notifications)**, **Theo dõi tiến độ tác vụ nền**, **Stream từng từ của mô hình AI/LLM (ChatGPT-like)**. |

```text
WEBSOCKET (2 CHIỀU ĐỒNG THỜI)
Client ◄═════════════════════════════════════════════► Server
       (Kênh TCP riêng biệt sau khi HTTP Handshake)

SERVER-SENT EVENTS - SSE (1 CHIỀU LIÊN TỤC TRÊN HTTP)
Client ───────────────── Request HTTP ban đầu ───────► Server
Client ◄─ ─ ─ ─ ─ ─ ─ ─  data: chunk 1 \n\n ─ ─ ─ ─ ─ Server
Client ◄─ ─ ─ ─ ─ ─ ─ ─  data: chunk 2 \n\n ─ ─ ─ ─ ─ Server
```

---

### 2. Quản lý Kết nối WebSocket với `ConnectionManager`

Một tiến trình FastAPI có thể duy trì hàng chục ngàn kết nối WebSocket đồng thời nhờ kiến trúc bất đồng bộ non-blocking của `asyncio`. Để quản lý tập trung các kết nối này, mẫu thiết kế **Connection Manager** là tiêu chuẩn:

1. **`connect(websocket)`**: Chấp nhận bắt tay (`await websocket.accept()`), lưu socket vào cấu trúc dữ liệu nội bộ.
2. **`disconnect(websocket)`**: Loại bỏ socket khỏi danh sách để tránh rò rỉ bộ nhớ (Memory Leak).
3. **`broadcast(message)`**: Duyệt qua danh sách và gửi tin nhắn tới tất cả client đang kết nối.
4. **Phân nhóm theo Phòng (Rooms / Tenancy)**: Lưu trữ dưới dạng `dict[room_id, set[WebSocket]]` để chỉ phát tán tin nhắn tới những người trong cùng một không gian làm việc.

---

### 3. Vấn đề nan giải: Xác thực (Authentication) trong WebSocket

Trong giao thức REST thông thường, trình duyệt gửi token qua header: `Authorization: Bearer <token>`.
Tuy nhiên, đối tượng JavaScript tiêu chuẩn `new WebSocket(url)` trong trình duyệt **hoàn toàn không cho phép lập trình viên thêm custom headers!**

Có 3 chiến lược an toàn cấp Senior để giải quyết vấn đề này:

```text
1. QUERY PARAMETER (Phổ biến, nhanh gọn)
   ws://api.example.com/ws/chat?token=eyJhbGciOi...

2. HANDSHAKE TICKET PATTERN (Bảo mật tối đa)
   Client ──POST /auth/ws-ticket (Header Bearer)──► Server trả về ticket ngắn hạn (30s)
   Client ──ws://api.example.com/ws/chat?ticket=XYZ──► Server xác thực và hủy ticket

3. SEC-WEBSOCKET-PROTOCOL (Tận dụng subprotocol)
   new WebSocket(url, ["access_token", token])
```

- **Đánh giá chiến lược 2 (Ticket Pattern)**: Đây là mô hình bảo mật chuẩn mực nhất cho hệ sinh thái doanh nghiệp lớn. Token dài hạn không bao giờ xuất hiện trên URL (tránh bị lưu vào Access Logs của Nginx/Load Balancer). Ticket chỉ có giá trị sử dụng một lần (One-Time-Use) và tự hủy sau 30 giây trong Redis.

---

### 4. Mở rộng Realtime Đa Pod với Redis Pub/Sub Backplane

#### 4.1 Rào cản khi triển khai Kubernetes / Đa Pod
Khi ứng dụng của bạn scale lên từ 2 pods trở lên đằng sau một Load Balancer:
- Người dùng A kết nối tới **Pod 1**.
- Người dùng B kết nối tới **Pod 2**.
- Khi Người dùng A gửi một tin nhắn chat trong nhóm, Pod 1 nhận được. Nếu Pod 1 chỉ broadcast tới `self.active_connections` trong RAM của nó, **Người dùng B ở Pod 2 sẽ hoàn toàn không nhận được tin nhắn!**

```text
┌───────────────────────────────┐     ┌───────────────────────────────┐
│         K8S POD 1             │     │         K8S POD 2             │
│  WebSocket Client A (Alice)   │     │  WebSocket Client B (Bob)     │
│             ▲                 │     │             ▲                 │
│             │                 │     │             │                 │
│       RAM Manager 1           │     │       RAM Manager 2           │
│             ▲                 │     │             ▲                 │
└─────────────┼─────────────────┘     └─────────────┼─────────────────┘
              │                                     │
              │  SUBSCRIBE                          │  SUBSCRIBE
              └──────────────┐       ┌──────────────┘
                             ▼       ▼
                     ┌───────────────────────┐
                     │   REDIS PUB/SUB HUB   │
                     │  (Message Backplane)  │
                     └───────────────────────┘
```

#### 4.2 Cơ chế Redis Pub/Sub Backplane
- Mỗi Kubernetes Pod khi khởi chạy sẽ kích hoạt một background task lắng nghe (Subscribe) vào một Redis Channel chung (ví dụ `channel:chat:all`).
- Khi bất kỳ Pod nào nhận được tin nhắn từ client của mình, thay vì gửi trực tiếp, Pod đó sẽ **Publish** tin nhắn lên Redis Channel.
- Cụm Redis phân tán tin nhắn đó tới **tất cả các Pods đang subscribe**.
- Từng Pod nhận tin nhắn từ Redis và chuyển tiếp (forward) xuống các WebSocket clients đang duy trì kết nối cục bộ trên Pod đó.

---

## 💻 Ví dụ thực hành

### 1. Triển khai Server-Sent Events (SSE) Stream tiến độ công việc và Stream LLM Token

FastAPI hỗ trợ SSE một cách thanh thoát thông qua `fastapi.responses.StreamingResponse` và async generator:

```python
import asyncio
from collections.abc import AsyncGenerator
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="SSE Streaming API")


async def generate_task_progress(task_id: str) -> AsyncGenerator[str, None]:
    """Async generator stream tiến độ xử lý từ 0% đến 100% theo định dạng SSE."""
    for percent in range(0, 101, 20):
        # Định dạng chuẩn SSE bắt buộc phải có tiền tố "data: " và kết thúc bằng "\n\n"
        payload = f'{{"task_id": "{task_id}", "percent": {percent}, "timestamp": {time.time()}}}'
        yield f"data: {payload}\n\n"
        await asyncio.sleep(0.5)  # Giả lập thời gian xử lý từng giai đoạn

    # Gửi sự kiện kết thúc
    yield "event: complete\ndata: {\"status\": \"DONE\"}\n\n"


@app.get("/tasks/{task_id}/progress-stream")
async def stream_progress(task_id: str) -> StreamingResponse:
    return StreamingResponse(
        generate_task_progress(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Yêu cầu Nginx không buffer stream!
        },
    )


async def generate_llm_tokens(prompt: str) -> AsyncGenerator[str, None]:
    """Giả lập stream từng token phản hồi của mô hình trí tuệ nhân tạo (LLM)."""
    response_text = f"Xin chào! Tôi là AI trợ lý của bạn. Bạn vừa hỏi: '{prompt}'. Dưới đây là phân tích chi tiết..."
    words = response_text.split(" ")

    for word in words:
        yield f"data: {word} \n\n"
        await asyncio.sleep(0.08)  # Tốc độ stream tự nhiên như con người gõ phím


@app.get("/ai/chat-stream")
async def chat_stream(prompt: str) -> StreamingResponse:
    return StreamingResponse(
        generate_llm_tokens(prompt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

---

### 2. Thiết kế `ConnectionManager` và WebSocket Endpoint với xác thực Token

Dưới đây là một hệ thống WebSocket hoàn chỉnh có xác thực JWT qua query token và xử lý ngắt kết nối an toàn:

```python
from typing import Annotated
from fastapi import (
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)


class ConnectionManager:

    def __init__(self) -> None:
        # Lưu trữ kết nối theo phòng: room_id -> list[WebSocket]
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)
        print(f"[WS] Client kết nối vào phòng '{room_id}'. Tổng thành viên: {len(self.rooms[room_id])}")

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        if room_id in self.rooms:
            if websocket in self.rooms[room_id]:
                self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        print(f"[WS] Client đã rời khỏi phòng '{room_id}'.")

    async def broadcast_to_room(self, room_id: str, message: str) -> None:
        if room_id not in self.rooms:
            return
        # Duyệt qua bản sao của danh sách để tránh lỗi sửa list trong khi lặp
        for connection in list(self.rooms[room_id]):
            try:
                await connection.send_text(message)
            except Exception:
                # Nếu client đã ngắt kết nối âm thầm, dọn dẹp kết nối lỗi
                self.disconnect(room_id, connection)


manager = ConnectionManager()
app = FastAPI()


async def validate_ws_token(token: str | None) -> str:
    """Xác thực token giả lập (trong thực tế: giải mã JWT)."""
    if not token or token != "secret_valid_jwt_token":
        return ""
    return "user_alice_123"


@app.websocket("/ws/chat/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Annotated[str | None, Query()] = None,
) -> None:
    # 1. Xác thực bảo mật khi bắt tay (Handshake Authentication)
    username = await validate_ws_token(token)
    if not username:
        # Từ chối kết nối với mã đóng 1008 (Policy Violation)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        print("[WS Auth] Từ chối kết nối: Token không hợp lệ.")
        return

    # 2. Chấp nhận kết nối vào phòng
    await manager.connect(room_id, websocket)
    await manager.broadcast_to_room(room_id, f"Thông báo: {username} đã tham gia cuộc trò chuyện.")

    # 3. Lắng nghe tin nhắn liên tục trong vòng lặp
    try:
        while True:
            text_data = await websocket.receive_text()
            formatted_msg = f"[{username}]: {text_data}"
            await manager.broadcast_to_room(room_id, formatted_msg)
    except WebSocketDisconnect:
        # 4. Bắt buộc phải dọn dẹp khi client đóng tab hoặc mất mạng!
        manager.disconnect(room_id, websocket)
        await manager.broadcast_to_room(room_id, f"Thông báo: {username} đã rời cuộc trò chuyện.")
```

---

### 3. Mở rộng Realtime Đa Pod với Redis Pub/Sub Backplane

Mô hình này giúp ứng dụng của bạn scale lên 100 pods trên Kubernetes mà người dùng ở các pod khác nhau vẫn trò chuyện thời gian thực mượt mà:

```python
import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis


class DistributedPubSubManager:

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self.active_sockets: set[WebSocket] = set()
        self.pub_client: aioredis.Redis | None = None
        self.sub_client: aioredis.Redis | None = None
        self.listener_task: asyncio.Task[None] | None = None
        self.channel_name = "taskflow:realtime:events"

    async def initialize(self) -> None:
        self.pub_client = aioredis.from_url(self.redis_url)
        self.sub_client = aioredis.from_url(self.redis_url)

        # Khởi chạy background coroutine lắng nghe Redis channel
        self.listener_task = asyncio.create_task(self._redis_subscribe_loop())
        print("[PubSub] Đã khởi chạy Redis PubSub Listener.")

    async def close(self) -> None:
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        if self.pub_client:
            await self.pub_client.aclose()
        if self.sub_client:
            await self.sub_client.aclose()
        print("[PubSub] Đã giải phóng Redis PubSub.")

    async def connect_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_sockets.add(websocket)

    def disconnect_client(self, websocket: WebSocket) -> None:
        self.active_sockets.discard(websocket)

    async def publish_event(self, message: str) -> None:
        """Publish tin nhắn lên Redis Broker để tất cả các Pods cùng nhận được."""
        if self.pub_client:
            await self.pub_client.publish(self.channel_name, message)

    async def _redis_subscribe_loop(self) -> None:
        """Vòng lặp lắng nghe tin nhắn từ Redis và broadcast cho các local WebSockets."""
        assert self.sub_client is not None
        pubsub = self.sub_client.pubsub()
        await pubsub.subscribe(self.channel_name)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    content = message["data"]
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")

                    # Forward tin nhắn xuống toàn bộ sockets trên Pod này
                    for ws in list(self.active_sockets):
                        try:
                            await ws.send_text(content)
                        except Exception:
                            self.active_sockets.discard(ws)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(self.channel_name)


# Lifespan khởi tạo Manager
distributed_manager = DistributedPubSubManager("redis://localhost:6379/2")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await distributed_manager.initialize()
    try:
        yield
    finally:
        await distributed_manager.close()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/global-feed")
async def global_realtime_feed(websocket: WebSocket) -> None:
    await distributed_manager.connect_client(websocket)
    try:
        while True:
            # Nhận tin nhắn từ client và phát tán qua Redis Pub/Sub
            msg = await websocket.receive_text()
            await distributed_manager.publish_event(f"User nói: {msg}")
    except WebSocketDisconnect:
        distributed_manager.disconnect_client(websocket)
```

---

## ⚠️ Lỗi thường gặp

### 1. Rò rỉ bộ nhớ (Memory Leak) do không xóa WebSocket khi disconnect
Nếu bạn quên khối `except WebSocketDisconnect:` và không xóa socket khỏi tập hợp `active_connections`, các socket đã chết vẫn nằm mãi trong RAM. Khi gọi `broadcast()`, chương trình sẽ liên tục văng exception và tiêu tốn CPU/RAM để gửi tin nhắn vào hư vô.

### 2. Nginx hoặc Cloudflare tự động ngắt kết nối sau 60 giây
Theo mặc định, các reverse proxy như Nginx có cấu hình `proxy_read_timeout 60s;`. Nếu trong vòng 60 giây không có dữ liệu nào được truyền qua socket, proxy sẽ đơn phương đóng kết nối TCP.
*Giải pháp*:
- Tăng timeout trong Nginx: `proxy_read_timeout 3600s;`.
- Triển khai cơ chế **Ping/Pong Heartbeat**: Định kỳ mỗi 30 giây, server hoặc client gửi một frame ping nhẹ để duy trì kết nối (Keep-Alive).

### 3. Quên cấu hình `X-Accel-Buffering: no` khi dùng SSE qua Nginx
Khi bạn stream SSE qua Nginx, Nginx có thể lưu đệm (buffer) toàn bộ stream cho tới khi đủ 4KB hoặc 8KB mới gửi về client một lần! Kết quả là phía client không thấy stream từng từ mà màn hình bị đơ một lúc rồi hiện ra toàn bộ. Luôn đính kèm header `X-Accel-Buffering: no` trong `StreamingResponse`.

### 4. Đặt Token bí mật dài hạn lên Query Param của WebSocket
Việc truyền Access Token có thời hạn 30 ngày vào URL `wss://host/ws?token=...` sẽ khiến token bị lưu vào lịch sử duyệt web của browser, server access logs, và hệ thống theo dõi APM. Hãy dùng Token ngắn hạn (1–2 phút) hoặc áp dụng **Handshake Ticket Pattern**.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng Endpoint SSE Stream Báo cáo xuất dữ liệu định dạng CSV
Viết một endpoint `GET /export-csv-stream` xuất file báo cáo 1,000 dòng:
1. Trả về dưới dạng `StreamingResponse(media_type="text/event-stream")`.
2. Cứ mỗi 100 dòng được xuất, stream một sự kiện JSON báo phần trăm hoàn thành.
3. Dòng cuối cùng gửi sự kiện `event: done` chứa đường dẫn tải file hoàn chỉnh.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def export_data_generator() -> AsyncGenerator[str, None]:
    total_rows = 1000
    for current_row in range(1, total_rows + 1):
        # Giả lập ghi dòng dữ liệu
        await asyncio.sleep(0.002)

        if current_row % 100 == 0:
            percent = (current_row / total_rows) * 100
            yield f'data: {{"processed": {current_row}, "percent": {percent:.1f}}}\n\n'

    yield "event: done\ndata: {\"download_url\": \"/downloads/report-final.csv\"}\n\n"


@app.get("/export-csv-stream")
async def export_stream():
    return StreamingResponse(
        export_data_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```
</details>

---

### Bài tập 2: Cơ chế Ping/Pong Heartbeat tự động trong WebSocket ConnectionManager
Bổ sung cơ chế Heartbeat vào `ConnectionManager`:
1. Viết phương thức `heartbeat_loop()` chạy ngầm mỗi 25 giây gửi frame `ping` hoặc text `{"type": "ping"}` tới tất cả các clients.
2. Nếu gửi thất bại tới socket nào, tự động đánh dấu và loại bỏ socket đó khỏi danh sách active.

<details>
<summary>💡 Gợi ý</summary>

```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class HeartbeatConnectionManager:

    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.connections.discard(ws)

    async def send_heartbeat_pings(self) -> None:
        dead_sockets: set[WebSocket] = set()
        # Sao chép danh sách để tránh RuntimeError: Set changed size during iteration
        for ws in list(self.connections):
            try:
                # Gửi bản tin ping
                await ws.send_json({"type": "ping"})
            except Exception:
                dead_sockets.add(ws)

        # Dọn dẹp các socket đã chết
        for dead in dead_sockets:
            self.disconnect(dead)


manager = HeartbeatConnectionManager()


@app.websocket("/ws/heartbeat")
async def heartbeat_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # Chờ phản hồi pong từ client
            msg = await websocket.receive_text()
            if msg == "pong":
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```
</details>

---

### Bài tập 3: Handshake Ticket Authentication Pattern với Redis
Xây dựng luồng xác thực bảo mật chuẩn Enterprise:
1. Endpoint HTTP POST `/api/v1/auth/ws-ticket` (yêu cầu header xác thực) sinh ra một chuỗi ticket UUID ngẫu nhiên, lưu vào Redis với TTL = 30 giây kèm `user_id`, rồi trả về ticket cho client.
2. Endpoint WebSocket `/ws/secure` nhận `ticket` qua query param.
3. Khi handshake, server kiểm tra ticket trong Redis bằng lệnh `GETDEL` (lấy và xóa ngay lập tức để đảm bảo ticket chỉ dùng 1 lần). Nếu không hợp lệ hoặc hết hạn, ngắt kết nối với mã 1008.

<details>
<summary>💡 Gợi ý</summary>

```python
import uuid
from fastapi import FastAPI, HTTPException, WebSocket, status
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379/3")


@app.post("/api/v1/auth/ws-ticket")
async def generate_ws_ticket() -> dict[str, str]:
    # Giả lập đã qua xác thực JWT và có user_id = 100
    user_id = 100
    ticket_id = str(uuid.uuid4())

    # Lưu vào Redis với TTL 30 giây
    await redis_client.set(f"ws:ticket:{ticket_id}", user_id, ex=30)
    return {"ticket": ticket_id, "expires_in": "30s"}


@app.websocket("/ws/secure")
async def secure_websocket(websocket: WebSocket, ticket: str | None = None) -> None:
    if not ticket:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Lệnh GETDEL: Đọc giá trị và xóa ngay lập tức (Atomic One-Time-Use)
    ticket_key = f"ws:ticket:{ticket}"
    user_id = await redis_client.getdel(ticket_key)

    if not user_id:
        print("[Security] Ticket không hợp lệ hoặc đã bị sử dụng!")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await websocket.send_text(f"Xác thực thành công! Chào mừng User #{user_id.decode() if isinstance(user_id, bytes) else user_id}")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        pass
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi phân biệt được bản chất và trường hợp sử dụng tối ưu giữa WebSocket (2 chiều) và SSE (1 chiều HTTP stream).
- [ ] Tôi biết cách dùng `StreamingResponse` để stream dữ liệu tiến độ và token LLM theo chuẩn `text/event-stream`.
- [ ] Tôi hiểu vì sao cần có `X-Accel-Buffering: no` khi triển khai SSE đằng sau Nginx.
- [ ] Tôi biết cách thiết kế `ConnectionManager` phân chia theo phòng và xử lý ngắt kết nối tránh rò rỉ RAM.
- [ ] Tôi giải thích được vì sao trình duyệt không gửi được custom header khi mở WebSocket và biết cách dùng Ticket Pattern.
- [ ] Tôi hiểu cách thức vận hành của Redis Pub/Sub Backplane để mở rộng WebSocket xuyên suốt nhiều Kubernetes Pods.
- [ ] Tôi nắm vững cơ chế Heartbeat Ping/Pong để ngăn Reverse Proxy ngắt kết nối ngầm.

---

## 📚 Đọc thêm

- [MDN Web Docs: Server-sent events API](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI Official Documentation: WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [RFC 6455: The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Microsoft Learn: SignalR Scaleout with Redis](https://learn.microsoft.com/en-us/aspnet/core/signalr/redis-backplane)
- [Tiếp theo: Bài 06 – Clean Architecture](./06-clean-architecture.md)

<!-- nav:bottom -->
---

[⬅️ Task queue](./04-task-queues.md) | [📚 Mục lục Senior](./README.md) | [Clean Architecture ➡️](./06-clean-architecture.md)
<!-- /nav:bottom -->
