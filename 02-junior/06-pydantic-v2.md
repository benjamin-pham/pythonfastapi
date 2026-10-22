<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 06
<!-- /nav:top -->

# Pydantic v2

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 05: FastAPI đầu tiên](./05-fastapi-first-app.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ cuộc cách mạng kiến trúc của **Pydantic v2**: nhân xử lý lõi bằng Rust (**`pydantic-core`**) mang lại tốc độ validation và parsing nhanh gấp **5–50 lần** so với thế hệ v1.
- Tuyệt đối loại bỏ các API Pydantic v1 đã lỗi thời (`.dict()`, `.parse_obj()`, `@validator`, `class Config:`), chuyển đổi 100% sang API v2 chuẩn mực.
- Định nghĩa các Schema dữ liệu mạnh mẽ với **`BaseModel`** và khai thác toàn diện các thuộc tính của **`Field(...)`**.
- Làm chủ cấu hình model hiện đại với **`ConfigDict`** (`from_attributes=True` thay thế cho `orm_mode = True`, `str_strip_whitespace=True`, `extra='forbid'`).
- Xây dựng các quy tắc kiểm tra logic nghiệp vụ tùy biến với **`@field_validator`** (kiểm tra đơn trường) và **`@model_validator(mode="after")`** (kiểm tra quan hệ đa trường).
- Tạo các trường tính toán động trong chu kỳ serialization với **`@computed_field`**.
- Tuần hoàn và phân tích dữ liệu hai chiều chuẩn xác bằng **`model_validate()`**, **`model_validate_json()`**, **`model_dump()`**, và **`model_dump_json()`**.
- Áp dụng triệt để mẫu thiết kế DTO (Data Transfer Object) phân tách rõ ràng: `TaskBase`, `TaskCreate`, `TaskUpdate`, `TaskRead`, kết hợp với `response_model` trong FastAPI (tương đương bộ ba DTO + FluentValidation + AutoMapper trong C#).

---

## 🔁 So sánh với C# / ASP.NET

Trong thế sinh thái .NET, việc xây dựng một API chuẩn thường đòi hỏi bạn phải phối hợp 3 đến 4 thư viện riêng biệt: C# Records/POCOs làm DTO, **FluentValidation** để viết rule kiểm tra dữ liệu, **AutoMapper** hoặc **Mapster** để chuyển đổi Entity sang DTO, và **System.Text.Json** để serialize/deserialize.

Trong Python & FastAPI, **Pydantic v2** đảm nhận toàn bộ các vai trò này một cách liền mạch, thanh lịch và đạt hiệu năng tối ưu nhờ nhân Rust:

| Nghiệp vụ / Khái niệm | C# / ASP.NET Core | Python / Pydantic v2 |
|---|---|---|
| **Data Container / DTO** | `public record TaskDto(int Id, string Title);` | `class TaskRead(BaseModel): id: int; title: str` |
| **Data Validation** | `AbstractValidator<T>` (FluentValidation) hoặc DataAnnotations (`[Required]`, `[MaxLength]`) | `Field(min_length=1, max_length=100)`, `@field_validator`, `@model_validator` |
| **Multi-field Validation** | `RuleFor(x => x.EndDate).GreaterThan(x => x.StartDate)` | `@model_validator(mode="after")` kiểm tra `self.end_date > self.start_date` |
| **Object Mapping** | `_mapper.Map<TaskRead>(taskEntity)` (AutoMapper / Mapster) | `TaskRead.model_validate(db_entity)` với `ConfigDict(from_attributes=True)` |
| **Chuyển đổi sang JSON** | `JsonSerializer.Serialize(taskDto)` | `task.model_dump_json()` hoặc `task.model_dump()` sang `dict` |
| **Bỏ qua trường chưa set** | `[JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]` | `task.model_dump(exclude_unset=True)` (cực kỳ quan trọng cho PATCH) |
| **Thuộc tính tính toán** | `public bool IsOverdue => DateTime.UtcNow > DueDate;` | `@computed_field` `@property def is_overdue(self) -> bool:` |
| **Cắt khoảng trắng chuỗi** | Viết custom converter hoặc trim thủ công trong setter | `ConfigDict(str_strip_whitespace=True)` (tự động 100%) |
| **Chống Mass Assignment** | Sử dụng ViewModel riêng biệt hoặc `[Bind("Title,Status")]` | `TaskCreate` schema chuyên biệt kết hợp `ConfigDict(extra="forbid")` |

---

## 📖 Lý thuyết

### 1. Pydantic v2: Bước nhảy vọt hiệu năng với Rust

Pydantic v1 được sáng lập bởi Samuel Colvin vào năm 2017, viết hoàn toàn bằng Python. Dù cú pháp rất được yêu thích, việc validate hàng triệu object lớn bằng Python thuần gặp nút thắt cổ chai về CPU.

Năm 2023, Pydantic v2 ra đời như một cuộc đại phẫu toàn diện:
- Lõi thực thi (validation, coercion, parsing) được viết lại 100% bằng ngôn ngữ **Rust** (`pydantic-core`).
- Hiệu năng tăng tốc từ **5 đến 50 lần** tùy thuộc vào độ phức tạp của dữ liệu.
- Định nghĩa lại toàn bộ hệ thống API nhằm nhất quán, chặt chẽ và tương thích hoàn hảo với Static Typing của Python 3.12+.

#### 🛑 Bảng quy chiếu: Tuyệt đối không dùng API v1 đã deprecated!

| Tính năng | API Pydantic v1 (❌ CẤM DÙNG) | API Pydantic v2 ( CHUẨN) |
|---|---|---|
| Chuyển model thành `dict` | `model.dict()` | `model.model_dump()` |
| Chuyển model thành chuỗi JSON | `model.json()` | `model.model_dump_json()` |
| Parse dữ liệu từ `dict` | `Model.parse_obj(data)` | `Model.model_validate(data)` |
| Parse dữ liệu từ chuỗi JSON | `Model.parse_raw(json_str)` | `Model.model_validate_json(json_str)` |
| Xuất JSON Schema | `Model.schema()` | `Model.model_json_schema()` |
| Validate từng trường | `@validator("title")` | `@field_validator("title")` |
| Validate toàn model | `@root_validator` | `@model_validator(mode="after")` hoặc `(mode="before")` |
| Cấu hình Model | `class Config:` | `model_config = ConfigDict(...)` |
| Map từ ORM object | `orm_mode = True` | `from_attributes = True` |

### 2. Định nghĩa Schema với `BaseModel` và `Field`

Mọi schema trong Pydantic đều kế thừa từ `BaseModel`. Mỗi trường dữ liệu được khai báo kèm Type Hint rõ ràng và có thể tùy biến chi tiết bằng `Field(...)`:

```python
from datetime import datetime
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=120,
        description="Tiêu đề công việc, không được để trống",
        examples=["Hoàn thiện tài liệu kiến trúc"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Mô tả chi tiết nội dung công việc",
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Độ ưu tiên từ 1 (Thấp) đến 5 (Khẩn cấp)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Danh sách các nhãn phân loại",
    )
```

> [!TIP]
> Luôn dùng `default_factory=list` hoặc `default_factory=dict` thay vì gán giá trị mặc định mutable `tags: list[str] = []` để đảm bảo mỗi instance sở hữu một bản sao độc lập.

### 3. Tinh chỉnh hành vi Model với `ConfigDict`

Trong Pydantic v2, bạn không khai báo `class Config:` lồng bên trong nữa mà sử dụng biến lớp `model_config = ConfigDict(...)`:

```python
from pydantic import BaseModel, ConfigDict


class StrictSchema(BaseModel):
    model_config = ConfigDict(
        # Đọc dữ liệu từ thuộc tính của Object (ORM/Dataclass) thay vì chỉ dict
        from_attributes=True,
        # Tự động cắt bỏ khoảng trắng thừa ở hai đầu chuỗi ký tự
        str_strip_whitespace=True,
        # Nghiêm cấm client truyền các trường lạ không có trong schema (chống Mass Assignment)
        extra="forbid",
        # Cho phép serialize các kiểu dữ liệu đặc biệt như Enum về giá trị thô
        use_enum_values=True,
    )

    username: str
    email: str
```

- **`from_attributes=True`** (thay thế cho `orm_mode = True` của v1): Cho phép Pydantic đọc dữ liệu từ các đối tượng không phải dictionary (như SQLAlchemy ORM models hay standard library `@dataclass`) qua cú pháp `getattr(obj, "field")`.
- **`str_strip_whitespace=True`**: Nếu client gửi `"   nguyen van a   "`, Pydantic tự động làm sạch thành `"nguyen van a"`.
- **`extra="forbid"`**: Nếu client gửi thêm trường ngoài schema (ví dụ cố tình gửi `is_admin: true`), Pydantic sẽ ném lỗi `422 Unprocessable Content` ngay lập tức!

### 4. Custom Validators trong Pydantic v2

Khi các điều kiện của `Field` (như `min_length`, `ge`) không đủ đáp ứng nghiệp vụ, bạn sử dụng Decorator Validator.

#### a. `@field_validator`: Kiểm tra đơn trường
`@field_validator` là một `classmethod`. Tham số nhận vào gồm `cls`, giá trị của trường `v`, và đối tượng `info: ValidationInfo` (chứa ngữ cảnh validation).

```python
from pydantic import BaseModel, ValidationInfo, field_validator


class UserRegistration(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str, info: ValidationInfo) -> str:
        cleaned = value.strip().lower()
        if not cleaned.isalnum():
            raise ValueError(
                "Username chỉ được chứa các ký tự chữ cái và chữ số!"
            )
        if cleaned in {"admin", "root", "system"}:
            raise ValueError(f"Không được phép sử dụng username '{cleaned}'!")
        # BẮT BUỘC phải return giá trị đã xử lý
        return cleaned
```

#### b. `@model_validator(mode="after")`: Kiểm tra đa trường (Toàn bộ Model)
Khi bạn cần so sánh giá trị giữa 2 hoặc nhiều trường với nhau (ví dụ: `due_date` phải sau `start_date`, hoặc `if status == 'DONE'` thì bắt buộc phải có `completed_at`), sử dụng `@model_validator(mode="after")`. Lúc này, validator nhận tham số là `self` (model đã được khởi tạo và các trường đơn lẻ đã được validate xong):

```python
from datetime import date
from typing import Self
from pydantic import BaseModel, model_validator


class ProjectSchedule(BaseModel):
    start_date: date
    due_date: date

    @model_validator(mode="after")
    def check_dates_order(self) -> Self:
        if self.due_date < self.start_date:
            raise ValueError("Hạn chót (due_date) không thể trước ngày bắt đầu (start_date)!")
        return self
```

### 5. Thuộc tính tính toán động với `@computed_field`

Trong nhiều trường hợp, bạn muốn API trả về một trường được tính toán từ các trường khác (ví dụ: `full_name` từ `first_name` và `last_name`, hoặc `is_overdue` từ `due_date`) và trường này phải xuất hiện tự động trong schema OpenAPI lẫn JSON output:

```python
from datetime import date
from pydantic import BaseModel, computed_field


class TaskItem(BaseModel):
    title: str
    due_date: date

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Tự động kiểm tra task đã quá hạn so với ngày hôm nay hay chưa."""
        return date.today() > self.due_date
```
Khi gọi `task.model_dump()`, trường `is_overdue` sẽ tự động có mặt trong dictionary kết quả!

### 6. Quá trình Tuần hoàn (Serialization) & Phân tích (Deserialization)

- **Deserialization (Nạp dữ liệu vào model)**:
  - `Model.model_validate(data_dict)`: Nạp từ dictionary Python.
  - `Model.model_validate_json(raw_json_str_or_bytes)`: Nạp trực tiếp từ chuỗi/byte JSON (nhân Rust parse cực nhanh, không cần qua `json.loads`).
- **Serialization (Xuất dữ liệu từ model ra ngoài)**:
  - `model.model_dump()`: Chuyển model thành dictionary chuẩn của Python.
  - `model.model_dump(exclude_unset=True)`: **Vô cùng quan trọng cho PATCH request** — chỉ xuất ra các trường mà client thực sự truyền vào trong payload, bỏ qua các trường mang giá trị mặc định chưa được set!
  - `model.model_dump_json(indent=2)`: Chuyển trực tiếp thành chuỗi JSON.

### 7. Phân tách Schemas theo mẫu DTO trong FastAPI

Tuyệt đối không dùng chung một Schema duy nhất cho toàn bộ chu trình sống của một thực thể. Việc phân tách DTO mang lại 3 lợi ích cốt tử:
1. **Bảo mật**: Không bao giờ để lộ các trường nhạy cảm (như mật khẩu băm `password_hash`).
2. **Linh hoạt**: Client khi tạo mới (`Create`) không được phép truyền `id` hay `created_at`, còn khi cập nhật (`Update`) thì mọi trường đều là tùy chọn (`Optional`).
3. **Hiệu năng & Tài liệu**: FastAPI tự động sinh hợp đồng OpenAPI chính xác cho từng phương thức HTTP.

```text
               ┌───────────────────────┐
               │       TaskBase        │
               │ - title: str          │
               │ - description: str?   │
               │ - priority: Priority  │
               └───────────┬───────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌──────────────────┐               ┌──────────────────┐
│    TaskCreate    │               │     TaskRead     │
│ (kế thừa Base)   │               │ (kế thừa Base)   │
│ - title: str (req)               │ - id: int        │
└──────────────────┘               │ - created_at: dt │
                                   │ - is_overdue     │
┌──────────────────┐               └──────────────────┘
│    TaskUpdate    │
│ (BaseModel độc lập)
│ - title: str?    │
│ - desc: str?     │
│ - priority: Prio?│
└──────────────────┘
```

---

## 💻 Ví dụ thực hành

Dưới đây là một bộ Schemas hoàn chỉnh chuẩn DTO Pattern, tích hợp đầy đủ `Field`, `ConfigDict`, `@field_validator`, `@model_validator`, `@computed_field`, và tích hợp trực tiếp vào các endpoint CRUD của FastAPI:

```python
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Self
from fastapi import FastAPI, HTTPException, Path, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


# 1. Base Schema: Chứa các thuộc tính chung
class TaskBase(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=100,
        description="Tiêu đề công việc",
        examples=["Viết unit test cho TaskService"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Mô tả chi tiết",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Độ ưu tiên của công việc",
    )


# 2. Create Schema: Dùng khi nhận request POST
class TaskCreate(TaskBase):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Hạn hoàn thành công việc",
    )

    @field_validator("title")
    @classmethod
    def validate_title_content(cls, v: str) -> str:
        # Không cho phép tiêu đề chỉ toàn số hoặc ký tự vô nghĩa
        if v.isdigit():
            raise ValueError("Tiêu đề không thể chỉ chứa toàn số!")
        return v


# 3. Update Schema: Dùng cho request PATCH (mọi trường đều là Optional)
class TaskUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None


# 4. Read Schema: Dùng làm response_model trả về cho Client
class TaskRead(TaskBase):
    model_config = ConfigDict(
        from_attributes=True,  # Cho phép parse từ ORM model / Dataclass
        use_enum_values=True,
    )

    id: int = Field(description="ID định danh duy nhất của task")
    status: TaskStatus = Field(description="Trạng thái hiện tại của task")
    due_date: datetime | None = None
    created_at: datetime = Field(description="Thời điểm tạo task")
    updated_at: datetime | None = Field(
        default=None,
        description="Thời điểm cập nhật lần cuối",
    )

    @computed_field
    @property
    def is_urgent(self) -> bool:
        """Thuộc tính tính toán: task có phải là khẩn cấp và chưa xong không."""
        return self.priority == TaskPriority.HIGH and self.status != TaskStatus.DONE


# Ứng dụng FastAPI tích hợp các Schemas
app = FastAPI(title="Task Management API với Pydantic v2")

# Database giả lập
fake_db: dict[int, dict[str, object]] = {}
id_counter = 1


@app.post(
    "/api/v1/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo task mới với dữ liệu được validate chặt chẽ",
)
def create_task(payload: TaskCreate) -> dict[str, object]:
    global id_counter
    task_dict = payload.model_dump()
    task_dict["id"] = id_counter
    task_dict["status"] = TaskStatus.TODO
    task_dict["created_at"] = datetime.now(UTC)
    task_dict["updated_at"] = None

    fake_db[id_counter] = task_dict
    id_counter += 1
    return task_dict


@app.get(
    "/api/v1/tasks/{task_id}",
    response_model=TaskRead,
    summary="Lấy chi tiết task theo ID",
)
def get_task(
    task_id: Annotated[int, Path(ge=1)],
) -> dict[str, object]:
    task = fake_db.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task với ID {task_id} không tồn tại!",
        )
    return task


@app.patch(
    "/api/v1/tasks/{task_id}",
    response_model=TaskRead,
    summary="Cập nhật từng phần (Partial Update) cho task",
)
def update_task_partial(
    task_id: Annotated[int, Path(ge=1)],
    payload: TaskUpdate,
) -> dict[str, object]:
    task = fake_db.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task với ID {task_id} không tồn tại!",
        )

    # Dùng exclude_unset=True để CHỈ lấy các trường client thực sự gửi lên
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        task.update(update_data)
        task["updated_at"] = datetime.now(UTC)

    return task
```

---

## ⚠️ Lỗi thường gặp

### 1. Sử dụng nhầm các phương thức Pydantic v1 đã bị khai tử

Khi tra cứu code trên StackOverflow hoặc các bài viết cũ, bạn rất dễ bắt gặp các phương thức của v1. Hãy nhớ:

```python
# ❌ LỖI V1:
# data = model.dict()
# obj = MyModel.parse_obj(payload)

#  ĐÚNG V2:
# data = model.model_dump()
# obj = MyModel.model_validate(payload)
```

### 2. Quên return giá trị trong `@field_validator`

Khác với một số thư viện validator chỉ raise exception khi sai, `@field_validator` của Pydantic là một bộ **biến đổi dữ liệu (data transformation pipeline)**. Nếu bạn quên câu lệnh `return`, trường đó sẽ nhận giá trị `None`!

```python
from pydantic import BaseModel, field_validator


class UserModel(BaseModel):
    name: str

    # ❌ SAI: Quên return giá trị
    @field_validator("name")
    @classmethod
    def validate_name_wrong(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError("Tên quá ngắn")
        # Không có return -> name sẽ bị gán thành None!

    #  ĐÚNG:
    @field_validator("name")
    @classmethod
    def validate_name_correct(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError("Tên quá ngắn")
        return v.title()  # Chuẩn hóa viết hoa chữ cái đầu
```

### 3. Không dùng `exclude_unset=True` khi xử lý HTTP PATCH

Trong HTTP RESTful convention, phương thức PATCH dùng để cập nhật một vài trường thay vì toàn bộ entity. Nếu bạn dùng `payload.model_dump()` thông thường, các trường không được client gửi sẽ mang giá trị mặc định là `None`, và vô tình ghi đè làm mất sạch dữ liệu cũ trong cơ sở dữ liệu!

```python
# Giả sử TaskUpdate có title: str | None = None, priority: Priority | None = None
# Client chỉ muốn đổi priority: {"priority": "HIGH"}

# ❌ SAI:
# update_data = payload.model_dump()
# -> {"title": None, "priority": "HIGH", "description": None}
# db_task.update(update_data)  # Toàn bộ title và description cũ biến thành None!

#  ĐÚNG:
# update_data = payload.model_dump(exclude_unset=True)
# -> {"priority": "HIGH"}
# db_task.update(update_data)  # Chỉ cập nhật priority, giữ nguyên title cũ!
```

### 4. Quên `from_attributes=True` khi ánh xạ ORM / Dataclass

Khi bạn tích hợp SQLAlchemy hoặc dùng `@dataclass`, đối tượng là một Class Instance chứ không phải `dict`. Nếu Schema trả về của bạn không bật `from_attributes=True`, Pydantic sẽ ném ngoại lệ validation error: `Input should be a valid dictionary or instance to extract fields from`.

---

## ✍️ Bài tập thực hành

### Bài 1: Schema Đăng ký Tài khoản (User Register DTO)
Xây dựng model `UserRegisterRequest`:
- `username`: Chuỗi 4–20 ký tự, tự động cắt khoảng trắng, chỉ gồm ký tự chữ cái và số, chuyển thành chữ thường qua `@field_validator`.
- `email`: Chuỗi email hợp lệ.
- `password`: Chuỗi tối thiểu 8 ký tự, phải chứa ít nhất 1 chữ in hoa và 1 chữ số.
- `confirm_password`: Chuỗi.
- Sử dụng `@model_validator(mode="after")` để đảm bảo `password == confirm_password`. Nếu không khớp, ném `ValueError("Mật khẩu xác nhận không khớp!")`.

<details>
<summary>💡 Gợi ý</summary>

- Dùng `info: ValidationInfo` nếu cần, hoặc kiểm tra regex trong `@field_validator("password")`.
- Trong `@model_validator(mode="after")`:
  ```python
  if self.password != self.confirm_password:
      raise ValueError("Mật khẩu xác nhận không khớp!")
  return self
  ```
</details>

---

### Bài 2: Schema Quản lý Sự kiện (Event Booking) với `@computed_field`
Xây dựng model `EventSchedule`:
- `title`: Chuỗi tiêu đề sự kiện (3–100 ký tự).
- `start_time`: Thời điểm bắt đầu (`datetime`).
- `end_time`: Thời điểm kết thúc (`datetime`).
- `max_participants`: Số lượng người tham gia tối đa (`ge=1, le=500`).
- `registered_count`: Số người đã đăng ký thực tế (`default=0, ge=0`).
- Sử dụng `@model_validator(mode="after")` để đảm bảo `end_time > start_time` và `registered_count <= max_participants`.
- Thêm thuộc tính tính toán `@computed_field` `@property def seats_available(self) -> int:` trả về số chỗ còn trống (`max_participants - registered_count`).

<details>
<summary>💡 Gợi ý</summary>

- Kiểm tra: `if self.end_time <= self.start_time: raise ValueError(...)`.
- Kiểm tra: `if self.registered_count > self.max_participants: raise ValueError(...)`.
- Khai báo `@computed_field` ngay trên phương thức `@property`.
</details>

---

### Bài 3: Bộ Schemas CRUD Sản phẩm Thương Mại Điện Tử (E-Commerce DTO)
Thiết kế bộ 4 schemas hoàn chỉnh cho sản phẩm (`Product`):
1. `ProductBase`: `name` (3-150 ký tự), `sku` (chuỗi dạng `SKU-XXXX-XXXX`), `price` (float > 0), `stock` (int >= 0).
2. `ProductCreate`: Kế thừa `ProductBase`, cấu hình `extra="forbid"`, `str_strip_whitespace=True`.
3. `ProductUpdate`: Tất cả các trường của `ProductBase` đều chuyển thành `Optional` (mặc định `= None`).
4. `ProductRead`: Kế thừa `ProductBase`, bổ sung `id: int`, `created_at: datetime`, `model_config = ConfigDict(from_attributes=True)`.
5. Viết một endpoint FastAPI `PATCH /api/v1/products/{product_id}` sử dụng `payload.model_dump(exclude_unset=True)` để cập nhật dữ liệu mẫu.

<details>
<summary>💡 Gợi ý</summary>

- Với trường `sku`, có thể dùng `pattern=r"^SKU-[A-Z0-9]{4}-[A-Z0-9]{4}$"`.
- Trong endpoint PATCH, đọc `update_data = payload.model_dump(exclude_unset=True)` và cập nhật vào dictionary in-memory.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các tiêu chí sau:

- [ ] Bạn hiểu rõ sự khác biệt giữa Pydantic v1 và Pydantic v2 (nhân Rust `pydantic-core`)?
- [ ] Bạn đã xóa bỏ hoàn toàn thói quen dùng `.dict()`, `.parse_obj()`, `class Config:` và thay thế bằng `model_dump()`, `model_validate()`, `ConfigDict`?
- [ ] Bạn nắm vững cách dùng `Field(...)` với các tham số ràng buộc giá trị và metadata OpenAPI?
- [ ] Bạn phân biệt rõ khi nào dùng `@field_validator` (đơn trường) và khi nào dùng `@model_validator(mode="after")` (đa trường)?
- [ ] Bạn biết cách tạo thuộc tính tính toán xuất hiện trong JSON bằng `@computed_field`?
- [ ] Bạn hiểu tầm quan trọng sống còn của `exclude_unset=True` trong các endpoint HTTP PATCH?
- [ ] Bạn áp dụng thành thạo mô hình phân tách DTO (`Base`, `Create`, `Update`, `Read`) cho các tài nguyên trong FastAPI?

---

## 📚 Đọc thêm

- [Pydantic Official Documentation – Migration from V1 to V2](https://docs.pydantic.dev/latest/migration/)
- [Pydantic Official Documentation – Models](https://docs.pydantic.dev/latest/concepts/models/)
- [Pydantic Official Documentation – Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Pydantic Official Documentation – Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
- [FastAPI Official Documentation – Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/)

<!-- nav:bottom -->
---

[⬅️ FastAPI đầu tiên](./05-fastapi-first-app.md) | [📚 Mục lục Junior](./README.md) | [Xử lý lỗi trong FastAPI ➡️](./07-error-handling.md)
<!-- /nav:bottom -->
