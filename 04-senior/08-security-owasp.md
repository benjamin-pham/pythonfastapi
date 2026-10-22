<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 08
<!-- /nav:top -->

# Bảo mật: OWASP API Top 10

> ⏱️ Thời lượng: ~4.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 07: Thiết kế API nâng cao](./07-advanced-api-design.md) và [Phân quyền Authorization](../03-middle/06-authorization.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Làm chủ chuẩn mực bảo mật OWASP API Security Top 10 (Phiên bản 2023)**: Thấu hiểu bản chất, cơ chế khai thác và phương pháp phòng thủ 10 lỗ hổng bảo mật phổ biến và nguy hiểm nhất đối với RESTful APIs hiện đại.
- **Triệt tiêu lỗ hổng BOLA (Broken Object Level Authorization / IDOR)**: Thiết kế tầng xác thực quyền sở hữu tài nguyên (Resource-Based Authorization) ở mức Service và Database query, không bao giờ tin tưởng định danh ID do client gửi lên.
- **Ngăn chặn Mass Assignment & Data Exposure với Pydantic v2**: Khai thác triệt để cấu hình `ConfigDict(extra="forbid")`, phân tách tuyệt đối các schemas đầu vào (Input DTOs) và đầu ra (Output Models), không để lộ các thuộc tính nhạy cảm.
- **Phòng thủ toàn diện trước tấn công Server-Side Request Forgery (SSRF)**: Xây dựng cơ chế gọi Webhooks an toàn với xác thực địa chỉ IP sau khi phân giải DNS, ngăn chặn truy cập vào dải mạng nội bộ (Private CIDR, Loopback, Cloud Metadata Service `169.254.169.254`).
- **Thiết lập cấu hình bảo mật chuẩn Production**: Triển khai Security Response Headers (HSTS, CSP, X-Frame-Options), cấu hình CORS chặt chẽ, và loại bỏ nguy cơ rò rỉ stack trace khi xảy ra lỗi hệ thống.

---

## 🔁 So sánh với C# / ASP.NET

Bảo mật ứng dụng web và API trong .NET và Python có nhiều điểm tương đồng về mặt khái niệm nhưng khác biệt lớn về công cụ và cơ chế triển khai:

| Khái niệm Bảo mật | Hệ sinh thái C# / ASP.NET Core | Hệ sinh thái Python 3.12+ / FastAPI |
|---|---|---|
| **Resource Authorization (BOLA)** | Sử dụng `IAuthorizationService.AuthorizeAsync()` kết hợp các `AuthorizationHandler<TRequirement, TResource>`. | Sử dụng FastAPI `Depends()` kết hợp Service Layer kiểm tra quyền sở hữu đối tượng hoặc filter trực tiếp trong ORM Query. |
| **Phòng chống Mass Assignment** | Sử dụng thuộc tính `[BindNever]`, `[Bind("prop1,prop2")]` hoặc tạo ViewModel/InputDTO riêng biệt. | Định nghĩa Pydantic v2 schemas với cấu hình `model_config = ConfigDict(extra="forbid")`. Mọi trường lạ sẽ bị từ chối với lỗi 422. |
| **Security Headers** | Sử dụng middleware `app.UseHsts()`, hoặc gói NuGet `NetEscapades.AspNetCore.SecurityHeaders`. | Tự viết custom Starlette Middleware hoặc sử dụng thư viện `secure` chèn các HTTP headers bảo mật vào response. |
| **Bảo vệ Cấu hình Bí mật** | `UserSecrets` cho dev, Azure Key Vault / AWS Secrets Manager tích hợp qua `IConfiguration`. | Tận dụng `pydantic-settings` đọc từ biến môi trường, kết hợp HashiCorp Vault hoặc AWS Parameter Store. |
| **Phòng chống SSRF** | Tùy biến `SocketsHttpHandler.ConnectCallback` trong `HttpClient` để validate IP phân giải được trước khi kết nối TCP. | Custom transport trong `httpx` hoặc thực hiện DNS resolving kiểm tra `ipaddress.ip_address(ip).is_private` trước khi gửi request. |
| **Băm mật khẩu** | `IPasswordHasher<TUser>` tích hợp sẵn thuật toán PBKDF2 của ASP.NET Core Identity. | Thư viện `pwdlib` với thuật toán hiện đại **Argon2id** (được OWASP khuyến nghị cao nhất hiện nay). |

---

## 📖 Lý thuyết

### 1. Bức tranh toàn cảnh OWASP API Security Top 10 (2023)

Dự án OWASP (Open Web Application Security Project) định kỳ cập nhật danh sách các hiểm họa bảo mật nghiêm trọng nhất dành riêng cho giao diện lập trình ứng dụng (APIs):

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   OWASP API SECURITY TOP 10 (2023)                    │
├──────┬───────────────────────────────────────────┬─────────────────────┤
│ Thứ  │ Tên lỗ hổng                               │ Mức độ nguy hiểm    │
├──────┼───────────────────────────────────────────┼─────────────────────┤
│ API1 │ Broken Object Level Authorization (BOLA)  │ Cực kỳ nghiêm trọng │
│ API2 │ Broken Authentication                     │ Cực kỳ nghiêm trọng │
│ API3 │ Broken Object Property Level Auth         │ Rất nghiêm trọng    │
│ API4 │ Unrestricted Resource Consumption         │ Cao                 │
│ API5 │ Broken Function Level Authorization (BFLA)│ Cao                 │
│ API6 │ Unrestricted Access to Sensitive Flows    │ Trung bình - Cao    │
│ API7 │ Server-Side Request Forgery (SSRF)        │ Nghiêm trọng        │
│ API8 │ Security Misconfiguration                 │ Cao                 │
│ API9 │ Improper Inventory Management             │ Trung bình          │
│ API10│ Unsafe Consumption of APIs                │ Cao                 │
└──────┴───────────────────────────────────────────┴─────────────────────┘
```

---

### 2. Phân tích chi tiết các lỗ hổng trọng tâm

#### 2.1 API1:2023 – Broken Object Level Authorization (BOLA / IDOR)
- **Bản chất**: Xảy ra khi một endpoint nhận ID của tài nguyên từ client (ví dụ: `GET /api/v1/projects/{project_id}`) nhưng server chỉ kiểm tra xem người dùng *đã đăng nhập hay chưa*, mà **không kiểm tra xem người dùng có quyền truy cập vào chính tài nguyên đó hay không**.
- **Kịch bản tấn công**: Kẻ tấn công đăng nhập tài khoản User A (nhận token hợp lệ), sau đó thay đổi `project_id` trên URL thành `project_id` của User B và xem trọn vẹn toàn bộ dữ liệu bí mật của đối thủ.
- **Giải pháp triệt để**:
  1. Luôn truy vấn tài nguyên kèm theo điều kiện lọc quyền sở hữu:
     ```python
     # Thay vì: select(Task).where(Task.id == task_id)
     # Hãy dùng: select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
     ```
  2. Nếu người dùng không có quyền truy cập, trả về `404 Not Found` (để không làm lộ sự tồn tại của ID) hoặc `403 Forbidden`.

#### 2.2 API2:2023 – Broken Authentication
- **Bản chất**: Cơ chế định danh và cấp phát token bị khiếm khuyết:
  - Khóa bí mật JWT (`JWT_SECRET_KEY`) quá ngắn hoặc để lộ trên repository công khai.
  - Sử dụng thuật toán băm mật khẩu lỗi thời (MD5, SHA-1, hoặc Plain SHA-256 không có salt).
  - Không thiết lập thời hạn hết hạn (`exp` claim) cho Access Token, hoặc không có cơ chế thu hồi (Revocation / Blacklist) khi người dùng đổi mật khẩu hoặc đăng xuất.
- **Giải pháp**:
  - Bắt buộc băm mật khẩu bằng **Argon2id** với salt ngẫu nhiên.
  - Sử dụng khóa bí mật JWT tối thiểu 256 bits (32 ký tự ngẫu nhiên cao).
  - Giữ thời hạn Access Token ngắn (15–30 phút) và lưu Refresh Token an toàn trong Redis kèm cơ chế xoay vòng token (Token Rotation).

#### 2.3 API3:2023 – Broken Object Property Level Authorization (Mass Assignment & Excessive Data Exposure)
- **Mass Assignment**: Client gửi lên các trường mà nó không được phép sửa (ví dụ: `{"is_admin": true, "balance": 1000000}`). Nếu backend gán trực tiếp dữ liệu từ request vào ORM Model:
  ```python
  # NGUY HIỂM:
  user = User(**request_payload)  # Kẻ tấn công tự thăng hạng thành Admin!
  ```
- **Excessive Data Exposure**: Endpoint trả về toàn bộ model cơ sở dữ liệu thay vì một DTO thu gọn, làm lộ mật khẩu băm, mã số thuế hoặc thông tin nhạy cảm của người dùng.
- **Giải pháp**:
  - Cấu hình Pydantic v2: `model_config = ConfigDict(extra="forbid")`. Mọi trường ngoài danh sách khai báo sẽ lập tức bị ném lỗi `422 Unprocessable Entity`.
  - Luôn sử dụng Schemas phản hồi tường minh: `response_model=UserRead`.

#### 2.4 API7:2023 – Server-Side Request Forgery (SSRF)
- **Bản chất**: Khi ứng dụng cho phép người dùng cung cấp một URL để hệ thống gọi tới (ví dụ: tính năng Webhook thông báo sự kiện, import avatar từ URL bên ngoài). Kẻ tấn công cung cấp URL trỏ vào:
  - Dịch vụ Cloud Metadata: `http://169.254.169.254/latest/meta-data/iam/security-credentials/` để lấy trộm AWS IAM role credentials!
  - Địa chỉ loopback: `http://127.0.0.1:6379` (Redis nội bộ không cần mật khẩu) hoặc `http://10.0.0.5:9200` (Elasticsearch nội bộ).
- **Cơ chế phòng thủ chuẩn Senior**:
  1. Phân giải tên miền (DNS Resolution) ra danh sách các địa chỉ IP.
  2. Kiểm tra xem các IP này có thuộc dải mạng riêng tư (`ip.is_private`), loopback (`ip.is_loopback`), link-local (`ip.is_link_local`) hay multicast hay không bằng module `ipaddress`. Nếu có $\to$ Từ chối kết nối ngay lập tức!
  3. Cấm tuyệt đối việc theo dõi chuyển hướng tự động (Disable HTTP Redirects: `follow_redirects=False`) để tránh kỹ thuật chuyển hướng DNS sau bước kiểm tra (DNS Rebinding Attack).

#### 2.5 API8:2023 – Security Misconfiguration
- **CORS lỏng lẻo**: Cấu hình `allow_origins=["*"]` kết hợp `allow_credentials=True`. Đây là cấu hình vô hiệu hóa lớp phòng thủ của trình duyệt, cho phép bất kỳ website độc hại nào cũng có thể gửi request đánh cắp dữ liệu người dùng.
- **Debug Mode trên Production**: Đặt `debug=True` trong FastAPI hoặc Uvicorn khiến framework in toàn bộ Traceback ra HTML/JSON khi có ngoại lệ, làm lộ mã nguồn, đường dẫn thư mục và biến môi trường.
- **Thiếu Security Headers**: Cần bổ sung các header bảo vệ tiêu chuẩn:
  - `Strict-Transport-Security` (HSTS): Ép buộc trình duyệt chỉ kết nối qua HTTPS.
  - `X-Content-Type-Options: nosniff`: Ngăn chặn trình duyệt tự ý đoán kiểu MIME.
  - `X-Frame-Options: DENY`: Chống tấn công Clickjacking.

---

### 3. Tự động hóa kiểm tra an ninh trong CI/CD: Bandit (SAST) & pip-audit (SCA)

Là một Senior Engineer, bạn không thể trông chờ vào việc rà soát thủ công (Manual Code Review) để bắt mọi lỗ hổng bảo mật. Quy trình CI/CD phải được trang bị hai công cụ phòng thủ tự động (Shift-Left Security):

#### 3.1 Static Application Security Testing (SAST) với `bandit`
- **Nguyên lý hoạt động**: `bandit` duyệt cây cú pháp trừu tượng (Abstract Syntax Tree - AST) của mã nguồn Python để tìm kiếm các mẫu mã độc hại hoặc tiềm ẩn nguy cơ an ninh:
  - B101: Dùng lệnh `assert` trong mã nguồn production (bị bỏ qua khi chạy với flag `-O`).
  - B105 / B106: Hardcode mật khẩu hoặc token bí mật trong mã nguồn.
  - B301 / B303: Dùng module không an toàn như `pickle`, `MD5`, `SHA1`.
  - B608: Ghép chuỗi SQL thô (SQL Injection).
  - B310: Mở URL tùy tiện không an toàn (nguy cơ SSRF).
- **Lệnh chạy chuẩn**: `uv run bandit -r app/ -ll -ii` (quét toàn bộ thư mục `app/`, lọc mức độ nghiêm trọng từ Medium/High trở lên).

#### 3.2 Software Composition Analysis (SCA) với `pip-audit`
- **Nguyên lý hoạt động**: `pip-audit` phân tích cây phụ thuộc trong môi trường hoặc lockfile (`pyproject.toml`, `requirements.txt`), đối chiếu với cơ sở dữ liệu lỗ hổng an ninh đã công bố (PyPI Advisory Database / OSV / CVE).
- **Lợi ích**: Phát hiện ngay lập tức các phiên bản thư viện bên thứ ba đang dính lỗ hổng đã được công bố (RCE, DoS, Memory Corruption).
- **Lệnh chạy chuẩn**: `uv run pip-audit --strict` (trả mã thoát khác 0 và chặn merge PR nếu phát hiện lỗ hổng đã biết).

---

## 💻 Ví dụ thực hành

### 1. Phòng thủ BOLA với Resource-Level Authorization & Service Layer

Ví dụ dưới đây thể hiện cơ chế kiểm soát quyền sở hữu tài nguyên: Một user chỉ được xem hoặc chỉnh sửa Project/Task nếu họ là Chủ sở hữu (`owner_id`) hoặc có vai trò Quản trị viên (`ADMIN`).

```python
from __future__ import annotations

from enum import StrEnum
from typing import Annotated
from pydantic import BaseModel, ConfigDict
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Role(StrEnum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class CurrentUser(BaseModel):
    id: str
    email: str
    role: Role


class Base(DeclarativeBase):
    pass


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)


class ProjectRead(BaseModel):
    id: str
    name: str
    owner_id: str
    model_config = ConfigDict(from_attributes=True)


app = FastAPI(title="OWASP BOLA Defense Demo")


# Giả lập dependency xác thực lấy thông tin người dùng từ JWT
async def get_current_user() -> CurrentUser:
    return CurrentUser(id="user_123", email="user@example.com", role=Role.MEMBER)


# Fake AsyncSession provider để code mẫu hoàn chỉnh độc lập
async def get_db_session():
    # Trong ứng dụng thực tế, yield session từ async_sessionmaker
    return None


class ProjectService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_project_securely(self, project_id: str, user: CurrentUser) -> ProjectModel:
        """Truy vấn dự án kèm kiểm tra quyền sở hữu đối tượng (BOLA Defense)."""
        stmt = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.session.scalars(stmt)
        project = result.first()

        if not project:
            # Trả về 404 để không làm lộ sự tồn tại của ID
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy dự án #{project_id}",
            )

        # Kiểm tra quyền: Chỉ cho phép OWNER hoặc ADMIN
        if project.owner_id != user.id and user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập vào tài nguyên này.",
            )

        return project


@app.get("/api/v1/projects/{project_id}", response_model=ProjectRead)
async def read_project(
    project_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProjectRead:
    # Minh họa luồng kiểm soát quyền hạn
    fake_project = ProjectModel(
        id=project_id,
        name="Dự án tuyệt mật",
        owner_id="user_123",  # Khớp với current_user.id
    )

    if fake_project.owner_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập vào dự án này.",
        )

    return ProjectRead.model_validate(fake_project)
```

---

### 2. Phòng thủ SSRF khi gọi Webhooks: Chặn Private IP & Link-Local

Mô-đun kiểm tra và gọi Webhook an toàn: Kiểm tra trước DNS resolution để loại bỏ dải IP nội bộ và ngăn chặn DNS Rebinding:

```python
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException, status
import httpx


def validate_public_url(target_url: str) -> None:
    """Xác thực URL đích không trỏ vào mạng nội bộ, loopback hoặc AWS metadata."""
    parsed = urlparse(target_url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ giao thức HTTP hoặc HTTPS.",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL không chứa hostname hợp lệ.",
        )

    try:
        # 1. Phân giải DNS lấy danh sách toàn bộ IP tương ứng
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể phân giải tên miền webhook.",
        ) from exc

    for item in addr_info:
        ip_str = item[4][0]
        ip = ipaddress.ip_address(ip_str)

        # 2. Kiểm tra IP an toàn: Cấm private, loopback, link-local, multicast
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"URL trỏ vào địa chỉ IP nội bộ không được phép: {ip_str}",
            )


async def send_secure_webhook(webhook_url: str, payload: dict[str, str]) -> int:
    """Gửi webhook bảo vệ khỏi SSRF và DNS Rebinding."""
    # Bước 1: Validate IP
    validate_public_url(webhook_url)

    # Bước 2: Gọi HTTP với timeout nghiêm ngặt và cấm follow redirects
    # Lưu ý kiến trúc Senior: Để chống triệt để tấn công DNS Rebinding (TOCTOU - Time Of Check to Time Of Use)
    # khi hacker cấu hình DNS server với TTL=0 (trả về IP public lúc validate nhưng trả về 169.254.169.254
    # lúc gọi HTTP), giải pháp triệt để là sử dụng Custom HTTP Transport thực hiện DNS Pinning
    # (kết nối trực tiếp tới IP đã được thẩm định qua socket và truyền hostname gốc vào header 'Host').
    async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
        try:
            response = await client.post(webhook_url, json=payload)
            return response.status_code
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Lỗi khi gửi webhook tới đối tác: {str(exc)}",
            ) from exc
```

---

### 3. Phòng thủ Mass Assignment & Thiết lập Security Headers Middleware

Minh họa cấu hình Pydantic v2 chống Mass Assignment và Middleware tự động chèn Security Headers theo khuyến cáo của OWASP:

```python
from __future__ import annotations

from collections.abc import Callable
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="OWASP API3 & Headers Defense")


# ============================================================================
# 1. Phòng thủ Mass Assignment với extra="forbid"
# ============================================================================
class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    # Nghiêm cấm nhận bất kỳ trường lạ nào (như is_admin, role, owner_id)
    model_config = ConfigDict(extra="forbid")


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    owner_id: str
    model_config = ConfigDict(from_attributes=True)


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(payload: TaskCreateRequest) -> TaskResponse:
    # payload được bảo đảm 100% không chứa các thuộc tính can thiệp trái phép
    return TaskResponse(
        id="task_001",
        title=payload.title,
        description=payload.description,
        owner_id="current_user_id",
    )


# ============================================================================
# 2. Middleware chèn Security Response Headers chuẩn OWASP
# ============================================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    response: Response = await call_next(request)

    # Ép buộc HTTPS trong 1 năm
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Chống MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Chống Clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Giới hạn thông tin gửi qua Referer header
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Bảo vệ XSS cơ bản
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response
```

---

### 4. Tự động hóa kiểm định an ninh với Bandit và Pip-Audit trong CI/CD Pipeline

Dưới đây là một cấu hình GitHub Actions Workflow hoàn chỉnh (`.github/workflows/security.yml`) để tích hợp quét SAST và SCA tự động:

```yaml
name: Security Audit & SAST Scan

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  security-audit:
    name: Run Bandit SAST & Pip-Audit SCA
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Quét lỗ hổng mã nguồn (SAST với Bandit)
        run: |
          uv run --with bandit bandit -r app/ -ll -ii --format screen

      - name: Quét lỗ hổng thư viện phụ thuộc (SCA với pip-audit)
        run: |
          uv run --with pip-audit pip-audit --desc on
```

---

## ⚠️ Lỗi thường gặp

### 1. Đồng nhất Authentication với Authorization
Nhiều kỹ sư chỉ viết `@app.get("/tasks/{id}", dependencies=[Depends(get_current_user)])` và cho rằng API đã an toàn. Đây là sai lầm chết người dẫn đến lỗ hổng BOLA (API1:2023). Token JWT chỉ chứng minh *người dùng là ai*, chứ không chứng minh *người dùng có quyền thao tác trên Task #{id} hay không*.

### 2. Thiết lập CORS quá phóng khoáng
Cấu hình thường thấy khi lập trình viên gặp lỗi CORS ở môi trường phát triển:
```python
# NGUY HIỂM TỘT ĐỘ TRÊN PRODUCTION:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Trình duyệt sẽ chặn, nhưng nếu origin phản xạ động thì hacker sẽ khai thác được!
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Luôn khai báo danh sách tên miền cụ thể của Frontend: `allow_origins=["https://app.taskflow.dev"]`.

### 3. Tái sử dụng Model của Database làm Schema API
Dùng trực tiếp class SQLAlchemy làm schema nhận dữ liệu hoặc trả về trực tiếp model ORM ra response:
- Khi nhận dữ liệu: Dễ bị Mass Assignment (hacker sửa các trường nội bộ như `is_active`, `role`, `verified`).
- Khi trả về dữ liệu: Dễ bị rò rỉ `hashed_password`, `two_factor_secret`, `internal_notes`.

### 4. Kiểm tra SSRF bằng String Matching ngây thơ
Chỉ kiểm tra `if "127.0.0.1" in url or "localhost" in url:` là hoàn toàn vô dụng. Kẻ tấn công có thể qua mặt bằng:
- Số nguyên thập phân: `http://2130706433` (tương đương `127.0.0.1`).
- Hệ thập lục phân: `http://0x7f000001`.
- Tên miền trỏ về IP nội bộ: Tạo domain `attacker.com` có bản ghi A trỏ về `127.0.0.1` hoặc `169.254.169.254`.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Xây dựng SafeWebhookDispatcher phòng chống SSRF
Viết class `SafeWebhookDispatcher`:
1. Nhận vào `url: str`, kiểm tra phân giải DNS và từ chối các dải IP `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.0.0/16`.
2. Tạo request HTTP POST gửi kèm header chữ ký HMAC-SHA256 (`X-Hub-Signature-256`) của payload với một shared secret để bên nhận xác minh tính toàn vẹn.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import hmac
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse
import httpx


class SafeWebhookDispatcher:

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def is_safe_ip(self, hostname: str) -> bool:
        try:
            for item in socket.getaddrinfo(hostname, None):
                ip = ipaddress.ip_address(item[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            return True
        except socket.gaierror:
            return False

    async def dispatch(self, url: str, payload_bytes: bytes) -> bool:
        hostname = urlparse(url).hostname
        if not hostname or not self.is_safe_ip(hostname):
            raise ValueError("Địa chỉ Webhook không an toàn hoặc nằm trong mạng nội bộ.")

        signature = hmac.new(self.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={signature}",
        }

        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            resp = await client.post(url, content=payload_bytes, headers=headers)
            return resp.status_code < 400
```
</details>

---

### Bài tập 2: Resource Ownership Validator Dependency
Viết một FastAPI dependency factory `check_task_access(required_permission: str)`:
1. Đọc `task_id` từ path parameter.
2. Kiểm tra nếu user là `ADMIN` $\to$ Cho phép mọi quyền (`read`, `write`, `delete`).
3. Nếu user là `MEMBER`, truy vấn Task: Nếu `owner_id == user.id` $\to$ Cho phép; nếu không $\to$ Ném `403 Forbidden`.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

from typing import Any
from fastapi import HTTPException, Path, Request, status


def require_task_ownership(action: str):

    async def dependency(request: Request, task_id: str = Path(...)) -> dict[str, Any]:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập.")

        if user.get("role") == "ADMIN":
            return {"task_id": task_id, "authorized_as": "ADMIN"}

        # Giả lập lấy task từ db
        task_owner_id = "user_abc"  # Ví dụ ID người tạo task

        if user.get("id") != task_owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn không có quyền thực hiện '{action}' trên công việc này.",
            )

        return {"task_id": task_id, "authorized_as": "OWNER"}

    return dependency
```
</details>

---

### Bài tập 3: Cấu hình Pydantic v2 Strict Input Schema chống Mass Assignment
Tạo schema `UserProfileUpdateRequest`:
1. Cho phép cập nhật `full_name`, `bio`.
2. Nghiêm cấm nhận các trường `email`, `role`, `is_active`, `id`.
3. Kiểm tra nếu người dùng cố tình gửi `role: "ADMIN"` trong JSON body thì Pydantic phải ném lỗi từ chối ngay ở tầng parsing validation.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=500)

    # Chống Mass Assignment: Nghiêm cấm mọi trường không được định nghĩa rõ ràng
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được bản chất lỗ hổng BOLA (API1:2023) và phân biệt được Authentication vs Resource Authorization.
- [ ] Tôi biết cách sử dụng Pydantic v2 `ConfigDict(extra="forbid")` để triệt tiêu nguy cơ Mass Assignment (API3:2023).
- [ ] Tôi hiểu tại sao Argon2id là thuật toán băm mật khẩu được OWASP khuyến cáo hàng đầu hiện nay.
- [ ] Tôi biết cách phòng thủ tấn công SSRF (API7:2023) bằng kỹ thuật phân giải DNS IP và cấm các dải IP nội bộ, loopback và AWS metadata.
- [ ] Tôi hiểu vì sao không được phép cấu hình CORS `allow_origins=["*"]` cùng với `allow_credentials=True`.
- [ ] Tôi biết cách cấu hình Security Response Headers (HSTS, nosniff, X-Frame-Options) trong FastAPI middleware.

---

## 📚 Đọc thêm

- [OWASP API Security Top 10 (2023 Official)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [Pydantic V2 Documentation: Model Configuration](https://docs.pydantic.dev/latest/concepts/config/)
- [RFC 9110: HTTP Semantics - Security Considerations](https://www.rfc-editor.org/rfc/rfc9110.html)
- [Tiếp theo: Bài 09 – Observability](./09-observability.md)

<!-- nav:bottom -->
---

[⬅️ Thiết kế API nâng cao](./07-advanced-api-design.md) | [📚 Mục lục Senior](./README.md) | [Observability ➡️](./09-observability.md)
<!-- /nav:bottom -->
