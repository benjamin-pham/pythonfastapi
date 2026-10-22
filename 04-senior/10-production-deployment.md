<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 10
<!-- /nav:top -->

# Deploy production

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 09: Observability](./09-observability.md) và [Docker & docker-compose](../03-middle/11-docker-compose.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Đóng gói Docker Container chuẩn Production cấp doanh nghiệp**: Nắm vững kỹ thuật Multi-stage Build tối ưu hóa dung lượng image (giảm từ 1.2GB xuống dưới 150MB), chạy dưới quyền Non-root User bảo mật (`UID 10001`), và sử dụng `tini` / `dumb-init` xử lý triệt để bài toán PID 1 Zombie Processes.
- **Lựa chọn và tinh chỉnh ASGI Production Server**: Hiểu sâu sắc sự khác biệt giữa Gunicorn kết hợp `UvicornWorker` và Granian (Rust-based ASGI server siêu tốc); tính toán chính xác số lượng workers dựa trên số lượng CPU Cores và đặc thù tải I/O.
- **Làm chủ quy trình Graceful Shutdown & Signal Handling**: Xử lý mượt mà tín hiệu `SIGTERM` từ Kubernetes / Docker, đảm bảo hệ thống không bao giờ ngắt ngang các request đang xử lý (in-flight requests) và giải phóng sạch sẽ tài nguyên Connection Pools.
- **Thiết kế Kubernetes Manifests chuẩn mực**: Cấu hình phân tách rạch ròi ba loại Health Checks (`startupProbe`, `livenessProbe`, `readinessProbe`), tránh thảm họa Cascading Failures khi cơ sở dữ liệu gặp sự cố; thiết lập HPA (Horizontal Pod Autoscaler) và Resource Quotas (`requests` vs `limits`).
- **Quản lý tiến trình trên máy chủ Bare-metal / Virtual Machine với Systemd**: Viết unit file chuẩn hóa với tự động khởi động lại (auto-restart), quản lý biến môi trường an toàn và bảo toàn hiệu năng.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET, quá trình đóng gói và triển khai ứng dụng lên Production có những đặc trưng rất riêng biệt nhờ sự tối ưu hóa của Microsoft:

| Khái niệm / Nhiệm vụ | Hệ sinh thái C# / ASP.NET Core | Hệ sinh thái Python 3.12+ / FastAPI |
|---|---|---|
| **Web Server Production** | Sử dụng **Kestrel** (Web server tích hợp sẵn, viết bằng C#, hiệu năng cực cao, hỗ trợ đa luồng native trong cùng 1 process). | Sử dụng **Gunicorn** làm Master Process Manager quản lý cụm **Uvicorn Workers** (đa tiến trình để vượt qua giới hạn GIL), hoặc máy chủ **Granian** viết bằng Rust. |
| **Đóng gói Container** | .NET SDK hỗ trợ `dotnet publish --os linux /t:PublishContainer` tạo image không cần Dockerfile, hoặc dùng base image `mcr.microsoft.com/dotnet/aspnet:8.0-chiseled` (distroless). | Sử dụng Multi-stage `Dockerfile` kết hợp công cụ quản lý gói siêu tốc **`uv`**, chạy trên nền base image `python:3.12-slim`. |
| **Health Checks** | Tích hợp sẵn `Microsoft.Extensions.Diagnostics.HealthChecks`: `MapHealthChecks("/healthz")`. | Xây dựng các router endpoints `/healthz/live` và `/healthz/ready` kết hợp kiểm tra trạng thái pool trong FastAPI. |
| **Xử lý Graceful Shutdown** | `IHostApplicationLifetime` cung cấp các token `ApplicationStopping` và `ApplicationStopped`. | Quản lý thông qua hàm bất đồng bộ `@asynccontextmanager` của FastAPI `lifespan` và bắt tín hiệu `SIGTERM`. |
| **Khởi động trên Linux VM** | Cấu hình Systemd Unit trỏ vào lệnh `dotnet MyApi.dll`. | Cấu hình Systemd Unit trỏ vào lệnh thực thi của virtual environment: `/app/.venv/bin/gunicorn`. |

---

## 📖 Lý thuyết

### 1. Đóng gói Container Production: Multi-Stage Build & Bảo mật Non-Root

Một Docker image sử dụng trong môi trường phát triển (Development) thường chứa đầy đủ trình biên dịch C (gcc), header files, git, test runners. Đưa toàn bộ các công cụ này lên Production là một rủi ro bảo mật nghiêm trọng (tạo điều kiện cho hacker biên dịch mã độc khi khai thác được lỗ hổng RCE) và gây lãng phí dung lượng mạng khi kéo image (Pull).

#### Kỹ thuật Multi-Stage Build với `uv`
Quy trình tối ưu hóa gồm 2 giai đoạn:
1. **Builder Stage**:
   - Sử dụng `uv` để tạo môi trường ảo độc lập (`virtualenv`).
   - Cài đặt toàn bộ dependencies vào `/app/.venv`.
   - Biên dịch các thư viện C extensions nếu cần.
2. **Runtime Stage**:
   - Khởi tạo từ `python:3.12-slim` hoàn toàn sạch sẽ, không có compiler.
   - Tạo một User không có quyền root: `adduser --system --uid 10001 appuser`.
   - Chỉ copy duy nhất thư mục `/app/.venv` và mã nguồn ứng dụng từ Builder Stage.
   - Chạy container dưới quyền `USER appuser`.

```text
┌───────────────────────────────────────────────┐
│ BUILDER STAGE (python:3.12-slim + uv)         │
│ - Cài đặt gcc, build tools                    │
│ - uv venv /app/.venv                          │
│ - uv pip install -r requirements.txt          │
└───────────────────────┬───────────────────────┘
                        │ COPY --from=builder /app/.venv /app/.venv
                        ▼
┌───────────────────────────────────────────────┐
│ RUNTIME STAGE (python:3.12-slim CLEAN)        │
│ - Không compiler, không build tools           │
│ - Tạo non-root user: appuser (UID 10001)      │
│ - Entrypoint: tini -- gunicorn                │
│ ──► Dung lượng siêu nhỏ: ~140MB               │
│ ──► Triệt tiêu bề mặt tấn công                │
└───────────────────────────────────────────────┘
```

#### Vấn đề PID 1 & Zombie Processes
Trong Linux, tiến trình có PID 1 (`init`) có nhiệm vụ đặc biệt: Thu dọn các tiến trình con mồ côi (reaping zombie processes) và chuyển tiếp tín hiệu (signals forwarding). Nếu bạn đặt trực tiếp `CMD ["uvicorn", "app.main:app"]`, Uvicorn sẽ trở thành PID 1.
Khi đó, Uvicorn không thể thu dọn các subprocesses bị chết và có thể không bắt được tín hiệu `SIGTERM` từ Docker/K8s khi muốn tắt máy. **Giải pháp**: Luôn bọc lệnh khởi động bằng **`tini`** hoặc **`dumb-init`** (`ENTRYPOINT ["/usr/bin/tini", "--"]`).

---

### 2. ASGI Production Servers: Uvicorn vs Gunicorn vs Granian

Trong kiến trúc Python ASGI, do hạn chế của Global Interpreter Lock (GIL), một tiến trình đơn lẻ chỉ có thể tận dụng tối đa 1 CPU Core. Để khai thác máy chủ đa nhân (Multi-core), ta phải áp dụng mô hình Đa tiến trình (Multi-process Architecture):

```text
                               ┌───────────────────────────┐
                               │   Gunicorn Master Process │ (PID: 10)
                               │   (Quản lý, theo dõi vòng │
                               │    đời của các worker)    │
                               └─────────────┬─────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             ▼                               ▼                               ▼
    [ Uvicorn Worker 1 ]            [ Uvicorn Worker 2 ]            [ Uvicorn Worker 3 ]
    (PID: 11 - Core 0)              (PID: 12 - Core 1)              (PID: 13 - Core 2)
    Chạy Event Loop riêng           Chạy Event Loop riêng           Chạy Event Loop riêng
```

- **Gunicorn + UvicornWorker**:
  - Gunicorn đóng vai trò Master: Không trực tiếp nhận request, chỉ giám sát sức khỏe các Worker. Nếu một Worker bị crash hoặc treo (hung), Gunicorn sẽ tự động kill và sinh ra Worker mới thay thế.
  - Mỗi Worker là một tiến trình Uvicorn độc lập chạy Event Loop bất đồng bộ của riêng mình.
  - **Công thức tính số Worker tối ưu**:
    $$\text{Số lượng Workers} = (2 \times \text{CPU Cores}) + 1$$
    *(Lưu ý: Trong môi trường Kubernetes, thường khuyến nghị chạy **1 Worker cho mỗi Pod** và scale số lượng Pods ngang hàng qua HPA để K8s kiểm soát tài nguyên chính xác nhất)*.
- **Granian**:
  - Máy chủ HTTP thế hệ mới cho Python viết hoàn toàn bằng **Rust**.
  - Sử dụng kiến trúc đa luồng native trên nền Hyper / Tokio.
  - Hiệu năng xử lý throughput (RPS) cao hơn 30%–50% so với Uvicorn và tiêu tốn ít bộ nhớ RAM hơn rõ rệt.

---

### 3. Quy trình Graceful Shutdown & Bắt tín hiệu Hệ điều hành

Khi Kubernetes muốn thu nhỏ quy mô (Scale Down) hoặc triển khai phiên bản mới (Rolling Update), nó sẽ gửi tín hiệu **`SIGTERM`** đến tiến trình trong Pod.

```text
1. K8s gửi SIGTERM đến Pod ──► 2. Pod ngừng nhận traffic mới từ Service
                                   │
                                   ▼
3. ASGI Server chờ các in-flight requests hoàn tất (tối đa 30s)
                                   │
                                   ▼
4. Kích hoạt FastAPI lifespan cleanup: Đóng DB pool, Redis connection, flush logs
                                   │
                                   ▼
5. Ứng dụng thoát sạch sẽ với Exit Code 0 (Nếu quá 30s ──► K8s gửi SIGKILL ép buộc tắt)
```

- **FastAPI Lifespan**: Toàn bộ logic dọn dẹp kết nối được đặt sau lệnh `yield` trong hàm `lifespan`:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # Startup: Khởi tạo DB pool, Redis client
      yield
      # Shutdown: await db_engine.dispose(), await redis_client.aclose()
  ```

---

### 4. Thiết kế Kubernetes Probes: Tránh thảm họa Cascading Failures

Kubernetes sử dụng 3 loại thăm dò sức khỏe (Health Probes). Việc cấu hình sai các Probes này là nguyên nhân hàng đầu gây sập toàn bộ hệ thống trên Production:

```text
┌─────────────────┬──────────────────────────────────┬──────────────────────────────────────────┐
│ Loại Probe      │ Mục đích                         │ Phản ứng của K8s khi Probe Thất bại      │
├─────────────────┼──────────────────────────────────┼──────────────────────────────────────────┤
│ startupProbe    │ Cho pod thời gian khởi động ban  │ Chờ đợi cho tới khi pass. Nếu timeout    │
│                 │ đầu (chạy migration, nạp models) │ thì mới kill và restart pod.             │
├─────────────────┼──────────────────────────────────┼──────────────────────────────────────────┤
│ livenessProbe   │ Phát hiện ứng dụng có bị treo    │ KILL TIẾN TRÌNH VÀ RESTART LẠI POD!      │
│ (/healthz/live) │ hoặc deadlock không.             │ (Tuyệt đối KHÔNG kiểm tra Database ở đây)│
├─────────────────┼──────────────────────────────────┼──────────────────────────────────────────┤
│ readinessProbe  │ Kiểm tra pod đã sẵn sàng nhận    │ TẠM THỜI TÁCH POD KHỎI SERVICE ROUTING. │
│ (/healthz/ready)│ traffic từ người dùng chưa.      │ Không restart pod!                       │
└─────────────────┴──────────────────────────────────┴──────────────────────────────────────────┘
```

> ⚠️ **QUY TẮC CỐT TỬ CỦA SENIOR**:
> **TUYỆT ĐỐI KHÔNG BAO GIỜ kiểm tra Database hoặc Redis trong `livenessProbe`!**
> Nếu cơ sở dữ liệu bị quá tải và chậm phản hồi trong 5 giây, mọi `livenessProbe` trên hàng trăm Pods sẽ đồng loạt thất bại. Kubernetes sẽ lập tức **kill và restart đồng loạt toàn bộ hệ thống Pods**. Khi các Pods mới bật lên lại, chúng lại đồng loạt gửi truy vấn khởi động tới Database $\to$ Database sụp đổ hoàn toàn (Cascading Failure / Thundering Herd).
>
> Hãy kiểm tra Database trong **`readinessProbe`**. Nếu DB nghẽn, Pod chỉ tạm thời không nhận thêm traffic mới mà không bị restart vô tội vạ.

---

## 💻 Ví dụ thực hành

### 1. Multi-Stage Dockerfile chuẩn Production với `uv` và Non-Root User

Đây là mẫu `Dockerfile` chuẩn mực cho các dự án Python 3.12 / FastAPI hiện đại:

```dockerfile
# ============================================================================
# GIAI ĐOẠN 1: BUILDER
# ============================================================================
FROM python:3.12-slim AS builder

# Cài đặt công cụ uv siêu tốc
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /bin/uv

WORKDIR /app

# Thiết lập biến môi trường biên dịch
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy file định nghĩa phụ thuộc trước để tối ưu hóa Docker Layer Cache
COPY pyproject.toml uv.lock ./

# Tạo virtualenv tại /app/.venv và cài đặt production dependencies
RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --no-install-project

# ============================================================================
# GIAI ĐOẠN 2: RUNTIME
# ============================================================================
FROM python:3.12-slim AS runtime

# Cài đặt tini để xử lý đúng vai trò PID 1 và signals
RUN apt-get update && apt-get install -y --no-install-recommends tini curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Tạo nhóm và người dùng không có quyền root (UID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false appuser

# Copy virtualenv đã build từ builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy mã nguồn dự án
COPY --chown=appuser:appgroup ./src ./src

# Đặt PATH ưu tiên môi trường ảo
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Chuyển quyền thực thi sang user appuser
USER appuser

EXPOSE 8000

# Sử dụng tini làm init system để forward signals cho Gunicorn
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["gunicorn", "src.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-"]
```

---

### 2. Thiết kế Health Endpoints & Lifespan Graceful Shutdown trong FastAPI

Mô hình triển khai endpoints phân định rõ `/healthz/live` và `/healthz/ready`:

```python
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Response, status


class InfrastructureState:
    is_shutting_down: bool = False
    is_db_connected: bool = True
    is_redis_connected: bool = True


infra = InfrastructureState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ---------------- STARTUP LOGIC ----------------
    print("🚀 [Startup] Khởi tạo kết nối cơ sở dữ liệu và bộ nhớ đệm Redis...")
    infra.is_db_connected = True
    infra.is_redis_connected = True
    infra.is_shutting_down = False

    yield

    # ---------------- SHUTDOWN LOGIC ----------------
    print("🛑 [Shutdown] Bắt được tín hiệu dừng. Bắt đầu quy trình Graceful Shutdown...")
    infra.is_shutting_down = True

    # Chờ 3 giây để Kubernetes Service kịp thời rút IP của Pod ra khỏi Endpoints
    await asyncio.sleep(3)

    print("🔌 [Shutdown] Đang giải phóng Database Connection Pool...")
    # await db_engine.dispose()
    print("🔌 [Shutdown] Đang đóng kết nối Redis...")
    # await redis_client.aclose()
    print("✅ [Shutdown] Hoàn tất tắt ứng dụng sạch sẽ.")


app = FastAPI(title="Production Deployment Demo", lifespan=lifespan)


@app.get("/healthz/live", tags=["Health"])
async def liveness_probe() -> dict[str, str]:
    """Liveness Probe: Chỉ kiểm tra xem tiến trình Python có phản hồi hay không.

    Tuyệt đối không kiểm tra external dependencies ở đây!
    """
    if infra.is_shutting_down:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ứng dụng đang trong tiến trình tắt (Shutting down).",
        )
    return {"status": "ALIVE"}


@app.get("/healthz/ready", tags=["Health"])
async def readiness_probe() -> dict[str, str]:
    """Readiness Probe: Kiểm tra xem Pod đã sẵn sàng phục vụ truy vấn hay chưa.

    Kiểm tra tính kết nối tới DB và Redis.
    """
    if infra.is_shutting_down:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ứng dụng đang tắt, từ chối nhận traffic mới.",
        )

    if not infra.is_db_connected or not infra.is_redis_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cơ sở hạ tầng (Database / Redis) chưa sẵn sàng.",
        )

    return {"status": "READY"}
```

---

### 3. Kubernetes Deployment & Service Manifests Hoàn chỉnh

Tệp YAML triển khai ứng dụng trên cụm Kubernetes với đầy đủ cấu hình Probes và HPA:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taskflow-api
  labels:
    app: taskflow-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: taskflow-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: taskflow-api
    spec:
      terminationGracePeriodSeconds: 45
      containers:
        - name: api
          image: ghcr.io/organization/taskflow-api:v1.2.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          # Nạp biến môi trường từ ConfigMap và Secret an toàn
          envFrom:
            - configMapRef:
                name: taskflow-api-config
            - secretRef:
                name: taskflow-api-secret
          # Khởi động ứng dụng
          startupProbe:
            httpGet:
              path: /healthz/live
              port: 8000
            initialDelaySeconds: 2
            periodSeconds: 3
            failureThreshold: 10
          # Kiểm tra tiến trình có bị treo hay không
          livenessProbe:
            httpGet:
              path: /healthz/live
              port: 8000
            periodSeconds: 10
            failureThreshold: 3
          # Kiểm tra sẵn sàng phục vụ traffic
          readinessProbe:
            httpGet:
              path: /healthz/ready
              port: 8000
            periodSeconds: 5
            failureThreshold: 2
---
apiVersion: v1
kind: Service
metadata:
  name: taskflow-api-service
spec:
  type: ClusterIP
  selector:
    app: taskflow-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: taskflow-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: taskflow-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: taskflow-api-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  PORT: "8000"
  ALLOWED_HOSTS: "taskflow.company.com,api.taskflow.com"
---
apiVersion: v1
kind: Secret
metadata:
  name: taskflow-api-secret
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://app_user:StrongPassword2026!@postgres-ha.database:5432/taskflow_prod"
  REDIS_URL: "redis://:RedisAuthPass2026@redis-cluster.database:6379/0"
  SECRET_KEY: "super_secret_jwt_encryption_key_change_in_vault"
```

---

## ⚠️ Lỗi thường gặp

### 1. Chạy Container dưới quyền Root
Nhiều lập trình viên bỏ qua lệnh `USER appuser` trong Dockerfile. Khi container chạy bằng root, nếu có lỗ hổng bảo mật dạng Remote Code Execution hoặc Container Escape, kẻ tấn công sẽ chiếm trọn quyền điều khiển máy chủ Host của bạn.

### 2. Thiết lập `terminationGracePeriodSeconds` ngắn hơn thời gian ứng dụng tắt
Kubernetes mặc định cho tiến trình 30 giây để hoàn tất việc dọn dẹp trước khi cưỡng chế gửi tín hiệu `SIGKILL`. Nếu Gunicorn của bạn cấu hình `--graceful-timeout 40` mà K8s lại để `terminationGracePeriodSeconds: 20`, K8s sẽ thẳng tay chém chết tiến trình khi nó chưa kịp commit dữ liệu hoặc đóng kết nối. Luôn đảm bảo:
$$\text{terminationGracePeriodSeconds} > \text{Gunicorn graceful timeout} + 10s$$

### 3. Đặt Resource Limits CPU quá thấp dẫn đến CPU Throttling
Linux CFS (Completely Fair Scheduler) dùng để thực thi CPU limits. Nếu bạn cấu hình `cpu: "200m"`, khi ứng dụng cần CPU để serialize một JSON response lớn, CFS Quota sẽ đóng băng tiến trình của bạn trong từng chu kỳ 100ms, khiến p99 latency của API vọt lên hàng nghìn mili-giây một cách khó hiểu. Hãy cấp `requests.cpu` dựa trên mức sử dụng trung bình, nhưng đặt `limits.cpu` hào phóng hoặc cân nhắc bỏ hẳn `limits.cpu` nếu môi trường hỗ trợ.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Viết Multi-stage Dockerfile cho ứng dụng FastAPI + SQLAlchemy
Viết một file `Dockerfile`:
1. Stage 1 (Builder): Dùng image `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, cài đặt dependencies từ file `requirements.txt` vào `/install`.
2. Stage 2 (Runner): Dùng image `python:3.12-slim`, sao chép `/install` sang, cấu hình `PYTHONPATH`, chạy dưới quyền `appuser` (UID 2000), tích hợp lệnh chạy Uvicorn.

<details>
<summary>💡 Gợi ý</summary>

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN uv pip install --no-cache --target=/install -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app
RUN useradd -u 2000 -s /bin/sh appuser

COPY --from=builder /install /app/packages
COPY ./src /app/src

ENV PYTHONPATH="/app/packages:/app"
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
</details>

---

### Bài tập 2: Viết Systemd Service Unit cho máy chủ Ubuntu / Debian
Soạn thảo tệp cấu hình `/etc/systemd/system/taskflow.service`:
1. Đảm bảo dịch vụ chỉ khởi động sau khi mạng đã sẵn sàng (`network.target`).
2. Chạy dưới quyền `www-data`.
3. Tự động khởi động lại nếu bị crash (`Restart=always`, thời gian chờ 5s).
4. Sử dụng Gunicorn với 4 Uvicorn workers.

<details>
<summary>💡 Gợi ý</summary>

```ini
[Unit]
Description=TaskFlow FastAPI Production Service
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/taskflow
EnvironmentFile=/var/www/taskflow/.env
ExecStart=/var/www/taskflow/.venv/bin/gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --graceful-timeout 30 \
    --access-logfile /var/log/taskflow/access.log \
    --error-logfile /var/log/taskflow/error.log
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=40
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```
</details>

---

### Bài tập 3: Cơ chế mô phỏng Graceful Shutdown Drainage trong FastAPI
Xây dựng một dependency `request_tracker` ghi nhận số lượng requests đang thực thi (In-flight requests) và một hàm xử lý tín hiệu `SIGTERM` ngăn nhận request mới và chờ đợi đến khi toàn bộ requests hiện tại hoàn thành trước khi thoát chương trình.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import asyncio
from collections.abc import Callable
from fastapi import FastAPI, Request, Response

app = FastAPI(title="Drainage Demo")

active_requests: int = 0
is_draining: bool = False


@app.middleware("http")
async def track_in_flight_requests(request: Request, call_next: Callable) -> Response:
    global active_requests, is_draining

    if is_draining and request.url.path not in ("/healthz/live", "/healthz/ready"):
        return Response(status_code=503, content="Máy chủ đang giải phóng tải.")

    active_requests += 1
    try:
        response: Response = await call_next(request)
        return response
    finally:
        active_requests -= 1


async def drain_and_exit(timeout_seconds: int = 30) -> None:
    global is_draining
    is_draining = True
    for _ in range(timeout_seconds):
        if active_requests == 0:
            break
        await asyncio.sleep(1)
    print("Toàn bộ in-flight requests đã được xử lý xong.")
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách viết Multi-stage Dockerfile tối ưu kích thước và chạy an toàn dưới quyền Non-root user.
- [ ] Tôi hiểu vai trò của `tini` / `dumb-init` trong việc xử lý tín hiệu hệ điều hành và thu dọn Zombie process (PID 1).
- [ ] Tôi phân biệt được mô hình Gunicorn + UvicornWorker và máy chủ Granian viết bằng Rust.
- [ ] Tôi phân biệt rạch ròi mục đích và cơ chế của 3 loại Probes trong Kubernetes (`startupProbe`, `livenessProbe`, `readinessProbe`).
- [ ] Tôi hiểu vì sao không bao giờ được kiểm tra Database trong `livenessProbe`.
- [ ] Tôi cấu hình được thời gian Graceful Shutdown đồng bộ giữa ASGI Server và Kubernetes Pod.
- [ ] Tôi biết cách viết Systemd Service unit file để quản lý tiến trình API trên máy chủ ảo / bare-metal.

---

## 📚 Đọc thêm

- [FastAPI Deployment in Docker: Official Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Kubernetes Documentation: Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Astral uv: Docker Container Best Practices](https://docs.astral.sh/uv/guides/docker/)
- [Granian: A Rust HTTP server for Python applications](https://github.com/emmett-framework/granian)
- [Tiếp theo: Bài 11 – System design & scaling](./11-system-design-scaling.md)

<!-- nav:bottom -->
---

[⬅️ Observability](./09-observability.md) | [📚 Mục lục Senior](./README.md) | [System design & scaling ➡️](./11-system-design-scaling.md)
<!-- /nav:bottom -->
