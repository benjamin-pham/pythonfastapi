<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 11
<!-- /nav:top -->

# Docker & docker-compose

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 10: Logging & xử lý lỗi toàn cục](./10-logging-error-handling.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Đóng gói ứng dụng FastAPI chuyên nghiệp bằng kỹ thuật **Multi-stage Dockerfile** kết hợp công cụ quản lý gói siêu tốc **`uv`**, tạo ra Image siêu nhẹ (< 150MB) và tốc độ build chỉ vài giây.
- Tận dụng tối đa cơ chế **Docker Layer Caching**: Tách rời việc cài đặt thư viện dependencies khỏi việc sao chép mã nguồn thay đổi hàng ngày.
- Nâng cao tính bảo mật theo chuẩn quốc tế CIS Docker Benchmark: Chạy ứng dụng dưới quyền **Non-root User (`appuser`)**, loại bỏ hoàn toàn mã độc tiềm tàng khi container bị xâm nhập.
- Thiết lập tệp **`.dockerignore`** chuẩn chỉ, ngăn chặn rò rỉ biến môi trường bí mật (`.env`), cache Python (`__pycache__`), và môi trường ảo cục bộ (`.venv`).
- Sử dụng cú pháp **`compose.yaml`** hiện đại (Compose Specification – loại bỏ trường `version:` đã lỗi thời) để điều phối đa dịch vụ: `api` và `postgres:17`.
- Làm chủ cơ chế **`healthcheck`** với `pg_isready` và tự động thực thi di chuyển lược đồ dữ liệu **`alembic upgrade head`** an toàn trước khi khởi chạy Web Server.

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET, việc container hóa ứng dụng ASP.NET Core sử dụng .NET SDK image và ASPNET runtime image là một quy trình rất quen thuộc. Dưới đây là bảng đối chiếu giữa hai nền tảng:

| Khái niệm / Thao tác | ASP.NET Core & Docker (C#) | FastAPI & Docker (Python 3.12+) |
|---|---|---|
| **Multi-stage Build: Giai đoạn Build** | Dùng SDK Image nặng: `mcr.microsoft.com/dotnet/sdk:8.0` | Dùng Image tích hợp sẵn `uv`: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` |
| **Multi-stage Build: Giai đoạn Runtime** | Dùng Runtime Image tối giản: `mcr.microsoft.com/dotnet/aspnet:8.0-alpine` | Dùng Base Python tối giản: `python:3.13-slim-bookworm` |
| **Khôi phục gói & Layer Caching** | `COPY *.csproj . && dotnet restore` trước khi copy toàn bộ code | `COPY pyproject.toml uv.lock . && uv sync --frozen --no-dev` |
| **Bảo mật Non-root User** | Khai báo `USER app` (tích hợp sẵn từ .NET 8) | Tạo user: `RUN useradd -m -u 1000 appuser && USER appuser` |
| **Cấu hình Đa Dịch vụ (Orchestration)** | `docker-compose.yml` hoặc .NET Aspire AppHost | `compose.yaml` (Chuẩn Docker Compose hiện đại) |
| **Chạy Database Migrations khi khởi động** | `dotnet ef database update` hoặc chạy trong `Program.cs` | Chạy lệnh `alembic upgrade head` trong Entrypoint của container |
| **Kiểm tra trạng thái DB sẵn sàng** | `condition: service_healthy` với healthcheck | `test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]` |

---

## 📖 Lý thuyết

### 1. Multi-stage Build và Tối ưu hóa Layer Caching với `uv`

Một trong những sai lầm phổ biến nhất khi viết Dockerfile cho Python là dùng `pip install -r requirements.txt` trực tiếp trong một Image duy nhất. Cách làm này mang theo các công cụ biên dịch (C-compiler, gcc, build tools), làm dung lượng Image phình to lên tới 1GB và tốc độ build chậm như rùa.

**Chiến lược Multi-stage hiện đại với `uv`:**
1. **Stage 1 (`builder`)**: Sử dụng Image `ghcr.io/astral-sh/uv`. Copy `pyproject.toml` và `uv.lock`. Chạy `uv sync --frozen --no-dev` để tạo môi trường ảo `.venv` hoàn chỉnh chỉ chứa các production packages.
2. **Stage 2 (`runtime`)**: Sử dụng Image `python:3.13-slim-bookworm` sạch sẽ. Copy toàn bộ thư mục `/app/.venv` và mã nguồn từ Stage 1 sang. Image cuối cùng hoàn toàn **không chứa công cụ build thừa thãi**, nhẹ và khởi động tức thì.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   MULTI-STAGE DOCKER BUILD VỚI UV                      │
│                                                                        │
│   STAGE 1: BUILDER (ghcr.io/astral-sh/uv)                              │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ 1. COPY pyproject.toml uv.lock ./                            │    │
│   │ 2. RUN uv sync --frozen --no-dev --no-install-project        │    │
│   │    -> Cài đặt toàn bộ dependencies vào /app/.venv            │    │
│   │    (Tận dụng Docker Cache 100% nếu không đổi thư viện!)     │    │
│   └──────────────────────────────────────────────────────────────┘    │
│                                  │                                     │
│                     Chỉ sao chép /app/.venv                            │
│                                  ▼                                     │
│   STAGE 2: RUNTIME (python:3.13-slim-bookworm)                         │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ 1. Tạo người dùng an toàn `appuser` (UID=1000)               │    │
│   │ 2. COPY --from=builder /app/.venv /app/.venv                 │    │
│   │ 3. COPY ./app ./app                                          │    │
│   │ 4. USER appuser (Không chạy root)                            │    │
│   │ 5. CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]      │    │
│   └──────────────────────────────────────────────────────────────┘    │
│         Dung lượng Image: ~120MB (Nhẹ gấp 8 lần Dockerfile cũ)        │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. Nguyên tắc bảo mật Non-root User

Mặc định, Docker container chạy với quyền người dùng **`root`** (UID = 0). Nếu ứng dụng của bạn gặp phải lỗ hổng Remote Code Execution (RCE) hoặc Container Breakout, kẻ tấn công sẽ sở hữu toàn quyền `root` và có thể chiếm quyền điều khiển của máy chủ vật lý (Host OS).

Do đó, các tiêu chuẩn bảo mật đám mây (Kubernetes, AWS ECS, CIS Benchmark) luôn yêu cầu:
- Tạo một người dùng hệ thống không có quyền root (`appuser`).
- Phân quyền sở hữu thư mục ứng dụng cho người dùng đó (`chown -R appuser:appuser /app`).
- Chuyển sang người dùng này trước khi khởi chạy lệnh thực thi: `USER appuser`.

### 3. Tệp `.dockerignore`

Tệp `.dockerignore` đóng vai trò tương tự như `.gitignore`. Nếu không có file này, lệnh `COPY . .` sẽ sao chép toàn bộ mã rác từ máy lập trình viên vào Image:
- Thư mục `.venv` của máy Mac/Windows (chứa binary không tương thích với Linux trong container).
- Tệp bí mật `.env` chứa mật khẩu production bị lộ vào image.
- Các thư mục `.git`, `.pytest_cache`, `__pycache__` làm phình to dung lượng build context.

### 4. Điều phối dịch vụ với `compose.yaml` hiện đại

Kể từ khi Docker Compose v2 ra đời và trở thành chuẩn chính thức, Docker đã công bố đặc tả **Compose Specification**:
- Tên tệp tiêu chuẩn hiện nay là **`compose.yaml`** (thay cho `docker-compose.yml`).
- Bỏ hoàn toàn dòng khai báo `version: '3.8'` ở đầu tệp (Compose v2 tự động suy diễn cú pháp mới nhất).
- Cơ chế khởi động tuần tự chuẩn: Dùng `depends_on` kết hợp `condition: service_healthy` để đảm bảo cơ sở dữ liệu PostgreSQL đã hoàn toàn sẵn sàng nhận kết nối trước khi khởi động tiến trình Web API.

---

## 💻 Ví dụ thực hành

Dưới đây là bộ ba tệp cấu hình triển khai hoàn chỉnh chuẩn doanh nghiệp cho dự án TaskFlow API.

### 1. Tệp `.dockerignore`

```text
# Git & Tooling
.git
.gitignore
.github

# Python Bytecode & Cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual Environments
.venv/
venv/
ENV/

# Testing & Coverage
.pytest_cache/
.coverage
htmlcov/
tests/

# Sensitive Files & Secrets
.env
.env.*
*.pem
*.key

# IDE Configs
.vscode/
.idea/
*.swp
```

### 2. Tệp `Dockerfile` tối ưu Multi-stage

```dockerfile
# ==============================================================================
# STAGE 1: Builder - Cài đặt dependencies bằng uv
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Bật tính năng biên dịch bytecode để tăng tốc độ khởi động Python
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# 1. Tận dụng Docker Cache: Chỉ copy file khai báo dependencies trước
COPY pyproject.toml uv.lock ./

# 2. Cài đặt dependencies vào thư mục .venv (không cài đặt chính package app)
RUN uv sync --frozen --no-dev --no-install-project

# 3. Copy toàn bộ mã nguồn vào và hoàn thiện cài đặt
COPY . .
RUN uv sync --frozen --no-dev


# ==============================================================================
# STAGE 2: Runtime - Chạy ứng dụng dưới quyền Non-root User
# ==============================================================================
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# Thiết lập biến môi trường runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app \
    PATH="/app/.venv/bin:$PATH"

# 1. Tạo nhóm và người dùng không có quyền root (UID=1000)
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser

# 2. Copy virtualenv và mã nguồn từ Stage builder sang
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app /app

# 3. Chuyển sang người dùng an toàn
USER appuser

# 4. Mở cổng mạng
EXPOSE 8000

# 5. Khởi chạy Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Tệp điều phối `compose.yaml`

```yaml
services:
  # ----------------------------------------------------------------------------
  # Dịch vụ Cơ sở dữ liệu PostgreSQL 17
  # ----------------------------------------------------------------------------
  db:
    image: postgres:17-alpine
    container_name: taskflow_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: taskflow_db
      POSTGRES_USER: taskflow_user
      POSTGRES_PASSWORD: supersecretpassword123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - taskflow_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskflow_user -d taskflow_db"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  # ----------------------------------------------------------------------------
  # Dịch vụ FastAPI Application
  # ----------------------------------------------------------------------------
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: taskflow_api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+asyncpg://taskflow_user:supersecretpassword123@db:5432/taskflow_db
      ENVIRONMENT: production
      LOG_LEVEL: INFO
      SECRET_KEY: dev_super_secret_jwt_key_should_be_changed_in_prod
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - taskflow_network
    # Tự động chạy migration Alembic lên bản mới nhất trước khi start web server
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

volumes:
  postgres_data:
    driver: local

networks:
  taskflow_network:
    driver: bridge
```

---

## ⚠️ Lỗi thường gặp

### 1. Lắng nghe trên `127.0.0.1` thay vì `0.0.0.0`

**Hiện tượng:** Container khởi động thành công, log ghi `Uvicorn running on http://127.0.0.1:8000`. Tuy nhiên khi bạn dùng trình duyệt gõ `http://localhost:8000` từ máy Host thì nhận được lỗi `ERR_CONNECTION_REFUSED`.

❌ **Sai lầm:**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
```
Địa chỉ `127.0.0.1` (loopback) bên trong Docker container chỉ cho phép các tiến trình nằm trong chính container đó kết nối. Mạng máy ảo Docker bên ngoài không thể chạm tới!

✅ **Giải pháp:** Luôn sử dụng `--host 0.0.0.0` (lắng nghe trên mọi giao diện mạng của container):
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 2. Copy toàn bộ mã nguồn trước khi cài đặt dependencies

Nếu bạn viết:
```dockerfile
COPY . .
RUN uv sync
```
Mỗi lần bạn sửa một chữ trong `main.py` hay một comment trong code, Docker sẽ phát hiện layer `COPY . .` bị thay đổi. Kết quả là toàn bộ layer cài đặt dependencies phía sau đều bị vô hiệu hóa cache, buộc Docker phải tải lại toàn bộ packages từ đầu!

✅ **Giải pháp:** Luôn copy riêng `pyproject.toml` và `uv.lock` trước, chạy cài đặt dependencies, sau đó mới copy mã nguồn dự án.

---

### 3. Bỏ quên `.dockerignore` làm rò rỉ `.venv` máy Host

Khi lập trình viên gõ lệnh `docker compose build`, nếu không có `.dockerignore`, thư mục `.venv` cục bộ (thường được tạo trên macOS chip Apple Silicon hoặc Windows x64) sẽ bị copy đè vào bên trong Linux container. 
Khi chạy ứng dụng, Python sẽ ném các lỗi kỳ lạ như:
`invalid ELF header`, `module not found`, hoặc không thể nạp các thư viện C-extension (`pydantic_core`, `asyncpg`).

---

## ✍️ Bài tập thực hành

### Bài tập 1: Cấu hình `compose.override.yaml` cho môi trường Development
Trong thực tế, bạn không muốn mỗi lần sửa code lại phải chạy `docker compose build`.
Hãy tạo tệp `compose.override.yaml` để ghi đè dịch vụ `api`:
- Mount thư mục mã nguồn hiện tại trên máy Host vào thư mục `/app` trong container (`volumes: - .:/app`).
- Bật tính năng live reload của Uvicorn (`--reload`).

<details>
<summary>💡 Gợi ý</summary>

```yaml
# compose.override.yaml (Tự động được nạp khi chạy `docker compose up`)
services:
  api:
    volumes:
      - .:/app
    environment:
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
```
</details>

---

### Bài tập 2: Tách biệt Migration thành Init Container
Thay vì gộp lệnh `alembic upgrade head` chung với lệnh chạy Uvicorn trong cùng một container `api`, hãy tách việc chạy migration thành một service riêng tên là `migration` trong `compose.yaml`.
- Dịch vụ `migration` chỉ chạy 1 lần lúc khởi động (`restart: "no"`), phụ thuộc vào `db` sẵn sàng.
- Dịch vụ `api` chỉ khởi động sau khi dịch vụ `migration` hoàn tất thành công (`condition: service_completed_successfully`).

<details>
<summary>💡 Gợi ý</summary>

```yaml
services:
  migration:
    build: .
    restart: "no"
    environment:
      DATABASE_URL: postgresql+asyncpg://taskflow_user:supersecretpassword123@db:5432/taskflow_db
    depends_on:
      db:
        condition: service_healthy
    networks:
      - taskflow_network
    command: alembic upgrade head

  api:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      migration:
        condition: service_completed_successfully
    networks:
      - taskflow_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```
</details>

---

### Bài tập 3: Tích hợp Redis Caching Service vào Docker Compose
Hãy bổ sung dịch vụ `redis` phiên bản `7-alpine` vào `compose.yaml`:
- Thiết lập giới hạn bộ nhớ tối đa 256MB (`maxmemory 256mb`) và chính sách loại trừ cache `allkeys-lru`.
- Cấu hình healthcheck cho Redis bằng lệnh `redis-cli ping`.
- Để dịch vụ `api` kết nối tới Redis qua biến môi trường `REDIS_URL: redis://redis:6379/0`.

<details>
<summary>💡 Gợi ý</summary>

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: taskflow_redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    networks:
      - taskflow_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách viết Multi-stage Dockerfile tối ưu kích thước và tốc độ build bằng `uv`.
- [ ] Tôi nắm vững nguyên lý Docker Layer Caching và thứ tự copy tệp hợp lý.
- [ ] Tôi hiểu tầm quan trọng của việc cấu hình `USER appuser` (Non-root user) để bảo vệ container.
- [ ] Tôi biết cấu hình tệp `.dockerignore` đầy đủ để tránh lộ bí mật `.env` và thư mục `.venv`.
- [ ] Tôi làm chủ cú pháp `compose.yaml` hiện đại và biết cách dùng `healthcheck` để đồng bộ DB với migration Alembic.

---

## 📚 Đọc thêm

- [Docker Documentation – Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Astral uv Documentation – Docker Integration Guide](https://docs.astral.sh/uv/guides/docker/)
- [Compose Specification Official Reference](https://docs.docker.com/compose/compose-file/)
- [CIS Docker Benchmark Security Guide](https://www.cisecurity.org/benchmark/docker)
- [Tiếp theo: Bài 12 – CI với GitHub Actions](./12-ci-github-actions.md)

<!-- nav:bottom -->
---

[⬅️ Logging & xử lý lỗi toàn cục](./10-logging-error-handling.md) | [📚 Mục lục Middle](./README.md) | [CI với GitHub Actions ➡️](./12-ci-github-actions.md)
<!-- /nav:bottom -->
