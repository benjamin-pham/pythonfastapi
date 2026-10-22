<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 09
<!-- /nav:top -->

# Cấu trúc project & settings

> ⏱️ Thời lượng: ~3.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 08: Dependency Injection](./08-dependency-injection.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Nắm vững cách phân rã một ứng dụng FastAPI đơn lẻ (monolith single-file) thành một cấu trúc dự án đa mô-đun chuyên nghiệp, sẵn sàng mở rộng quy mô khi dự án phát triển lớn.
- Sử dụng thành thạo **`APIRouter(prefix=..., tags=...)`** để module hóa các nhóm endpoint, quản lý tiền tố URL và phân loại tài liệu OpenAPI nhất quán.
- Hiểu rõ ưu và nhược điểm của hai trường phái kiến trúc tổ chức mã nguồn phổ biến nhất: **Package theo tầng kỹ thuật (Layered Architecture)** vs **Package theo miền nghiệp vụ (Domain / Feature-based)**.
- Làm chủ phương pháp quản lý cấu hình theo nguyên tắc **12-Factor App** sử dụng thư viện chuyên dụng **`pydantic-settings`**.
- Khai báo biến môi trường an toàn, định kiểu nghiêm ngặt (strongly-typed) với **`BaseSettings`** và **`SettingsConfigDict`**, tự động nạp dữ liệu từ file `.env`.
- Tối ưu hóa hiệu năng nạp cấu hình bằng kỹ thuật caching **`@lru_cache`** và inject cấu hình an toàn qua hệ thống Dependency Injection (tương đương với mẫu `IOptions<T>` trong ASP.NET Core).

---

## 🔁 So sánh với C# / ASP.NET

Trong các dự án ASP.NET Core tiêu chuẩn, cấu trúc thư mục thường được định hình bởi Visual Studio Solution (.sln) với các dự án con (Core, Infrastructure, WebAPI). Cấu hình ứng dụng được chia thành các file JSON phân tầng (`appsettings.json`, `appsettings.Development.json`) kết hợp với `IOptions<T>` và `builder.Configuration`.

Trong FastAPI và Python hiện đại, việc tổ chức cấu trúc mang lại sự linh hoạt tối đa nhưng đòi hỏi kỷ luật kiến trúc cao:

| Khái niệm / Nghiệp vụ | C# / ASP.NET Core | Python / FastAPI |
|---|---|---|
| **Module hóa Routing** | `app.MapGroup("/api/v1/tasks").WithTags("Tasks")` hoặc `[Route("api/v1/[controller]")]` | `router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])` |
| **Gắn route vào App** | `app.MapControllers()` hoặc đăng ký Endpoint Groups | `app.include_router(tasks_router)` |
| **Tập tin cấu hình** | `appsettings.json`, `appsettings.{Environment}.json` | File biến môi trường `.env`, `.env.test`, `.env.production` |
| **Định kiểu cấu hình (Options)** | Tạo POCO class: `public class DatabaseSettings { ... }` | Kế thừa `pydantic_settings.BaseSettings` |
| **Nạp & Validate cấu hình** | `builder.Services.Configure<DatabaseSettings>(...)` + DataAnnotations | Tự động 100% khi khởi tạo `Settings()` nhờ Pydantic v2 core |
| **Tiêm cấu hình qua DI** | Inject `IOptions<DatabaseSettings>` hoặc `IOptionsSnapshot<T>` | Inject `Annotated[Settings, Depends(get_settings)]` |
| **Tối ưu đọc cấu hình** | ASP.NET Core tự cache `IConfiguration` thành Singleton | Dùng decorator `@lru_cache` trên hàm `get_settings()` |

---

## 📖 Lý thuyết

### 1. Tại sao cần tổ chức dự án đa mô-đun?

Khi mới tiếp cận FastAPI, việc viết toàn bộ model, logic, và router trong một file `main.py` 500–1000 dòng là rất cám dỗ. Tuy nhiên, khi dự án bước vào thực tế với hàng chục bảng và hàng trăm API, cách làm này dẫn tới:
- Xung đột git triền miên (Merge Conflicts) khi nhiều lập trình viên cùng sửa một file.
- Lẫn lộn trách nhiệm giữa tầng Web (HTTP parameters, status code) và tầng Nghiệp vụ (Business logic, Database queries).
- Hiện tượng **Circular Import (Nhập vòng lặp)** đặc trưng của Python khiến server không thể khởi động.

### 2. Hai trường phái tổ chức mã nguồn phổ biến

#### Phong cách 1: Layered Architecture (Tổ chức theo tầng kỹ thuật)
Đây là phong cách quen thuộc nhất với các kỹ sư backend, rất phù hợp cho các dự án vừa và nhỏ, microservices, hoặc các API CRUD tiêu chuẩn:

```text
app/
├── core/              # Cấu hình toàn cục, bảo mật, exceptions, utils
│   ├── config.py
│   ├── exceptions.py
│   └── security.py
├── schemas/           # Pydantic Schemas / DTOs (Request & Response)
│   ├── project.py
│   └── task.py
├── repositories/      # Thao tác cơ sở dữ liệu / Database queries
│   ├── base.py
│   ├── project_repo.py
│   └── task_repo.py
├── services/          # Business logic thuần túy (Domain logic)
│   ├── project_service.py
│   └── task_service.py
├── routers/           # Web API Endpoints (APIRouter)
│   ├── api_v1.py
│   ├── projects.py
│   └── tasks.py
└── main.py            # Entry point khởi tạo FastAPI application
```

#### Phong cách 2: Feature-based / Domain-driven (Tổ chức theo nghiệp vụ)
Thích hợp cho các hệ thống lớn (Modular Monolith), nơi mỗi domain là một đơn vị độc lập:

```text
app/
├── core/              # Thành phần dùng chung toàn app
├── modules/
│   ├── tasks/         # Gói trọn vẹn của nghiệp vụ Task
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── router.py
│   └── projects/      # Gói trọn vẹn của nghiệp vụ Project
│       ├── models.py
│       ├── schemas.py
│       ├── services.py
│       └── router.py
└── main.py
```

### 3. Module hóa Routing với `APIRouter`

`APIRouter` là một mini-app trong FastAPI, cho phép định nghĩa các route độc lập và sau đó gom nhóm lại vào ứng dụng chính:

```python
# app/routers/tasks.py
from fastapi import APIRouter, status

# Khởi tạo router với tiền tố và tag tài liệu
router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Không tìm thấy"}},
)


@router.get("/")
def list_tasks():
    return [{"id": 1, "title": "Học APIRouter"}]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task():
    return {"message": "Đã tạo task"}
```

Sau đó, trong file tổng hợp hoặc `main.py`, bạn gắn router vào app bằng `include_router`:

```python
# app/main.py
from fastapi import FastAPI
from app.routers import tasks

app = FastAPI(title="TaskFlow Modular API")

# Gắn toàn bộ router của tasks vào đường dẫn gốc /api/v1
# Kết quả URL sẽ là: /api/v1/tasks và /api/v1/tasks/
app.include_router(tasks.router, prefix="/api/v1")
```

### 4. Quản lý cấu hình 12-Factor App với `pydantic-settings`

Theo nguyên tắc số 3 của phương pháp luận **12-Factor App (Config)**: Toàn bộ cấu hình hệ thống (Database URL, Redis port, API keys, Environment) phải được lưu trữ trong môi trường (Environment Variables) chứ không bao giờ được hardcode vào mã nguồn.

Từ Pydantic v2, tính năng quản lý cấu hình được tách thành gói độc lập: **`pydantic-settings`**.

```bash
# Cài đặt thư viện
pip install pydantic-settings
```

#### Khai báo lớp Settings
Kế thừa từ `BaseSettings` và sử dụng `SettingsConfigDict`:

```python
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Cấu hình đọc file .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Bỏ qua nếu trong file .env có các biến lạ
        case_sensitive=False,  # Không phân biệt chữ hoa thường khi map biến
    )

    # Khai báo các thông số kèm giá trị mặc định & validation
    PROJECT_NAME: str = "TaskFlow API"
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = (
        "development"
    )
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = Field(default=8000, ge=1024, le=65535)

    # Thông số bảo mật nhạy cảm (không có default -> Bắt buộc phải có trong .env)
    SECRET_KEY: str = Field(
        min_length=32, description="Khóa bí mật dùng để ký JWT"
    )
    DATABASE_URL: str = Field(
        default="sqlite:///./data/taskflow.db",
        description="Chuỗi kết nối cơ sở dữ liệu",
    )
```

#### Quy tắc ưu tiên nạp biến môi trường
Pydantic-Settings đọc cấu hình theo thứ tự ưu tiên từ cao xuống thấp:
1. **Biến môi trường hệ điều hành (OS Environment Variables)**: Được truyền qua shell hoặc Docker container (ví dụ `export SECRET_KEY=...`).
2. **File `.env`**: Được đọc từ đường dẫn chỉ định.
3. **Giá trị mặc định (Default values)**: Khai báo trực tiếp trong code Python.

### 5. Tối ưu hiệu năng với `@lru_cache` và Dependency Injection

Mỗi khi bạn gọi `Settings()`, Pydantic phải đọc file `.env` từ ổ đĩa cứng, parse các chuỗi văn bản, và chạy toàn bộ pipeline validation. Việc làm này trong từng HTTP Request là cực kỳ lãng phí tài nguyên!

Giải pháp chuẩn mực của cộng đồng FastAPI là kết hợp hàm decorator **`@functools.lru_cache`** (Least Recently Used Cache) với **`Depends()`**:

```python
from functools import lru_cache
from typing import Annotated
from fastapi import Depends


@lru_cache
def get_settings() -> Settings:
    """Khởi tạo Settings một lần duy nhất và lưu vào cache (Singleton)."""
    return Settings()


# Inject vào route bất kỳ:
@router.get("/info")
def get_info(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "app": settings.PROJECT_NAME,
        "env": settings.ENVIRONMENT,
    }
```

**Lợi ích vượt trội khi viết Unit Test:**
Khi viết test case, bạn có thể dễ dàng làm mới hoặc thay đổi cấu hình bằng cách xóa cache:
```python
get_settings.cache_clear()  # Xóa cache để nạp lại settings mới cho bài test
```

---

## 💻 Ví dụ thực hành

Dưới đây là một dự án mẫu hoàn chỉnh thể hiện cách phối hợp ăn ý giữa `pydantic-settings`, `@lru_cache`, `APIRouter`, và cấu trúc phân tầng:

### File 1: `config.py` (Quản lý cấu hình)
```python
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "TaskFlow Enterprise"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./taskflow.db"


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
```

### File 2: `schemas.py` (Hợp đồng dữ liệu)
```python
from pydantic import BaseModel, ConfigDict, Field


class TaskItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=3, max_length=100)
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH)$")


class TaskItemRead(TaskItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
```

### File 3: `service.py` (Tầng nghiệp vụ & Repository)
```python
from typing import Annotated
from fastapi import Depends


class TaskRepository:
    def __init__(self) -> None:
        self._store: dict[int, dict[str, object]] = {
            1: {"id": 1, "title": "Thiết lập cấu trúc thư mục", "priority": "HIGH"},
        }
        self._counter = 2

    def get_all(self) -> list[dict[str, object]]:
        return list(self._store.values())

    def add(self, title: str, priority: str) -> dict[str, object]:
        item = {"id": self._counter, "title": title, "priority": priority}
        self._store[self._counter] = item
        self._counter += 1
        return item


# Singleton repository in-memory cho ví dụ này
_repo_instance = TaskRepository()


def get_task_repository() -> TaskRepository:
    return _repo_instance
```

### File 4: `router.py` (Tầng định tuyến HTTP)
```python
from typing import Annotated
from fastapi import APIRouter, Depends, status

tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])


@tasks_router.get("/", response_model=list[TaskItemRead])
def list_all_tasks(
    repo: Annotated[TaskRepository, Depends(get_task_repository)],
) -> list[dict[str, object]]:
    return repo.get_all()


@tasks_router.post(
    "/", response_model=TaskItemRead, status_code=status.HTTP_201_CREATED
)
def create_new_task(
    payload: TaskItemCreate,
    repo: Annotated[TaskRepository, Depends(get_task_repository)],
) -> dict[str, object]:
    return repo.add(title=payload.title, priority=payload.priority)
```

### File 5: `main.py` (Điểm khởi tạo ứng dụng)
```python
from typing import Annotated
from fastapi import Depends, FastAPI

# Khởi tạo instance ứng dụng
settings = get_app_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Gắn router con với tiền tố /api/v1
app.include_router(tasks_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check(
    cfg: Annotated[AppSettings, Depends(get_app_settings)],
) -> dict[str, str]:
    return {
        "status": "HEALTHY",
        "env": cfg.ENVIRONMENT,
        "app": cfg.APP_NAME,
    }
```

---

## ⚠️ Lỗi thường gặp

### 1. Trùng lặp tiền tố URL (Prefix Duplication)
Nếu bạn đã đặt `prefix="/tasks"` trong `APIRouter`, nhưng khi gọi `app.include_router()` bạn lại viết `app.include_router(tasks_router, prefix="/api/v1/tasks")`, thì URL thực tế sẽ bị nhân đôi thành `/api/v1/tasks/tasks`!
> [!TIP]
> Quy ước chuẩn: Router con đặt `prefix="/tasks"`, còn `include_router` chỉ đặt prefix chung của phiên bản API `prefix="/api/v1"`.

### 2. Nhập biến cấu hình từ thư viện cũ
Trong Pydantic v1, class `BaseSettings` nằm trong `pydantic`. Nhưng trong Pydantic v2, nó đã được chuyển sang `pydantic_settings`.
```python
# ❌ SAI (Pydantic v1 cũ):
# from pydantic import BaseSettings

#  ĐÚNG (Pydantic v2):
# from pydantic_settings import BaseSettings, SettingsConfigDict
```

### 3. Vô tình đưa file `.env` chứa mật khẩu thật vào Git
File `.env` thường chứa Database Password, JWT Secret Key, AWS Access Keys. Nếu bạn commit file này lên GitHub/GitLab, hệ thống của bạn có nguy cơ bị tấn công ngay lập tức!
> [!CAUTION]
> Luôn thêm `.env` và `.env.*` vào file `.gitignore`. Chỉ commit file mẫu `.env.example` chứa các biến không có giá trị nhạy cảm!

### 4. Quên gọi `cache_clear()` khi kiểm thử môi trường
Nếu trong bài test Pytest, bạn dùng `monkeypatch.setenv("ENVIRONMENT", "testing")` nhưng quên gọi `get_app_settings.cache_clear()`, ứng dụng sẽ tiếp tục đọc giá trị cũ đã được lưu trong `@lru_cache` từ lần gọi trước đó!

---

## ✍️ Bài tập thực hành

### Bài 1: Xây dựng Module Cấu hình Hoàn chỉnh với Validation
Tạo class `Settings(BaseSettings)`:
- `DATABASE_URL`: Bắt buộc, chuỗi không được để trống.
- `JWT_SECRET`: Chuỗi ký tự có độ dài tối thiểu 32 ký tự (`min_length=32`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Số nguyên từ 5 đến 1440 phút (`ge=5, le=1440`).
- `ALLOWED_ORIGINS`: Danh sách các domain được phép truy cập CORS (`list[str]`, mặc định `["*"]`).
- Viết file `.env.example` mẫu đi kèm.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng `Field(min_length=32)` cho `JWT_SECRET`.
- Khai báo `SettingsConfigDict(env_file=".env", extra="ignore")`.
</details>

---

### Bài 2: Tách Router và Gom Nhóm Đa Tầng (Nested Routers)
Một ứng dụng thương mại điện tử cần phân chia hệ thống route:
1. `products_router`: Quản lý `/products` (GET, POST).
2. `orders_router`: Quản lý `/orders` (GET, POST).
3. Tạo file `api_v1.py` gom cả hai router trên lại với `api_router = APIRouter(prefix="/api/v1")`.
4. Gắn `api_router` vào `main.py` và kiểm tra giao diện Swagger UI để đảm bảo các tag `Products` và `Orders` xuất hiện tách bạch.

<details>
<summary>💡 Gợi ý</summary>

- Trong `api_v1.py`:
```python
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(products_router)
api_router.include_router(orders_router)
```
- Trong `main.py`: `app.include_router(api_router)`.
</details>

---

### Bài 3: Unit Test Chuyển Đổi Môi Trường Cấu Hình với `monkeypatch`
Viết bộ test với `pytest`:
- Bài test 1: Thiết lập biến môi trường `ENVIRONMENT="production"`, `DEBUG="false"`, gọi `get_app_settings.cache_clear()`, xác nhận ứng dụng đọc đúng giá trị production và `debug is False`.
- Bài test 2: Thiết lập `ENVIRONMENT="development"`, `DEBUG="true"`, gọi `cache_clear()`, kiểm tra endpoint `/health` phản hồi chính xác thông tin môi trường.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng fixture `monkeypatch`:
```python
def test_production_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "false")
    get_app_settings.cache_clear()
    settings = get_app_settings()
    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False
```
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các tiêu chí sau:

- [ ] Bạn hiểu rõ lý do cần module hóa dự án và phân biệt được 2 trường phái: Layered vs Feature-based?
- [ ] Bạn biết cách khai báo và kết nối các `APIRouter` lại với nhau bằng `include_router`?
- [ ] Bạn nắm vững nguyên tắc 12-Factor App trong việc quản lý cấu hình qua biến môi trường?
- [ ] Bạn sử dụng thành thạo `pydantic-settings` với `BaseSettings` và `SettingsConfigDict`?
- [ ] Bạn biết cách kết hợp `@lru_cache` để tối ưu hiệu năng đọc cấu hình và inject qua `Depends()`?
- [ ] Bạn hiểu tầm quan trọng của việc đưa `.env` vào `.gitignore` và tạo `.env.example`?

---

## 📚 Đọc thêm

- [FastAPI Official Documentation – Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Settings Official Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [The Twelve-Factor App – III. Config](https://12factor.net/config)
- [Microsoft Learn – Configuration in ASP.NET Core](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/)

<!-- nav:bottom -->
---

[⬅️ Dependency Injection](./08-dependency-injection.md) | [📚 Mục lục Junior](./README.md) | [M1 – CRUD API ➡️](../project/m1-crud-api.md)
<!-- /nav:bottom -->
