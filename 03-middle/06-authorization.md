<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 06
<!-- /nav:top -->

# Authorization

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 05: Authentication với JWT](./05-authentication-jwt.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Phân biệt rạch ròi và chính xác giữa hai khái niệm dễ nhầm lẫn nhất trong bảo mật: **Authentication** (Xác thực danh tính - HTTP 401) và **Authorization** (Phân quyền truy cập - HTTP 403).
- Triển khai hệ thống kiểm soát truy cập dựa trên vai trò (**Role-Based Access Control - RBAC**) bằng cách kết hợp kiểu liệt kê `StrEnum` với kỹ thuật **Dependency Factory** trong FastAPI.
- Hiểu rõ tại sao chỉ áp dụng RBAC là chưa đủ, và nắm vững cách phòng chống lỗ hổng bảo mật số 1 trong OWASP API Security Top 10: **BOLA / IDOR (Broken Object Level Authorization)**.
- Xây dựng cơ chế phân quyền dựa trên tài nguyên và chính sách (**Resource-Based / Policy-Based Authorization**): kiểm tra quyền sở hữu đối tượng (chỉ chủ sở hữu hoặc quản trị viên mới có quyền sửa/xóa tài nguyên).
- Nắm vững nguyên tắc thiết kế: khi nào nên đặt logic phân quyền ở **FastAPI Dependency** và khi nào nên đóng gói vào **Service Layer**.

---

## 🔁 So sánh với C# / ASP.NET Core Authorization

Trong ASP.NET Core, hệ thống phân quyền được xây dựng vô cùng hoàn chỉnh với Role-based, Claim-based và Policy-based Authorization:

| Khái niệm / Cơ chế | ASP.NET Core (C#) | FastAPI (Python 3.12+) |
|---|---|---|
| **Phân quyền theo Vai trò (RBAC)** | `[Authorize(Roles = "Admin,Manager")]` trên Controller hoặc Action | Dependency Factory: `Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))` |
| **Mã lỗi khi chưa xác thực** | Trả về `401 Unauthorized` | Ném `HTTPException(status_code=401)` |
| **Mã lỗi khi bị từ chối quyền** | Trả về `403 Forbidden` | Ném `HTTPException(status_code=403)` |
| **Phân quyền theo Chính sách (Policy)** | `services.AddAuthorization(opt => opt.AddPolicy(...))` | Định nghĩa các hàm policy checker hoặc dependency kiểm tra điều kiện |
| **Phân quyền trên Tài nguyên cụ thể** | `IAuthorizationService.AuthorizeAsync(User, resource, "EditPolicy")` | Viết Dependency nhận `resource_id` từ path hoặc kiểm tra quyền trong Service Layer |
| **Tổ chức vai trò người dùng** | IdentityRole hoặc Claims (`ClaimTypes.Role`) | Python `enum.StrEnum` (`UserRole.ADMIN`, `UserRole.MEMBER`) |

---

## 📖 Lý thuyết

### 1. Phân định cốt tử: 401 Unauthorized vs 403 Forbidden

Một trong những lỗi cơ bản nhất của các lập trình viên backend là trả về sai mã trạng thái HTTP giữa 401 và 403:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   BẢO MẬT: BẠN LÀ AI & BẠN ĐƯỢC LÀM GÌ?                │
│                                                                        │
│   HTTP 401 UNAUTHORIZED               HTTP 403 FORBIDDEN               │
│   (Authentication Failure)            (Authorization Failure)          │
│                                                                        │
│   - "Tôi không biết bạn là ai!"       - "Tôi biết rõ bạn là ai, nhưng  │
│   - Không có Token gửi kèm              bạn KHÔNG CÓ THẨM QUYỀN        │
│   - Token gửi sai chữ ký                làm việc này!"                 │
│   - Token đã hết hạn                  - Ví dụ: User thường đòi xóa     │
│   - Header: WWW-Authenticate            dự án của người khác           │
└────────────────────────────────────────────────────────────────────────┘
```

**Quy tắc:**
- Nếu client **chưa đăng nhập** hoặc token không giải mã được → Luôn trả về **`401 Unauthorized`**.
- Nếu client **đã đăng nhập hợp lệ**, danh tính đã rõ ràng, nhưng tài khoản không đủ quyền → Luôn trả về **`403 Forbidden`**.

### 2. Role-Based Access Control (RBAC) với Dependency Factory

RBAC là mô hình phân quyền phổ biến nhất, gán người dùng vào một vai trò cố định:
- **`ADMIN`**: Toàn quyền quản trị hệ thống.
- **`MEMBER`**: Tạo và quản lý công việc của mình.
- **`VIEWER`**: Chỉ có quyền đọc, không được thêm/sửa/xóa.

Trong Python 3.11+, ta định nghĩa vai trò bằng `enum.StrEnum`:
```python
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
```

Để bảo vệ các endpoint theo vai trò mà không lặp lại code, ta sử dụng mẫu thiết kế **Dependency Factory** (hàm trả về một hàm dependency):

```python
from collections.abc import Callable
from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.api.deps import get_current_active_user
from app.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """Dependency Factory sinh ra hàm kiểm tra quyền theo danh sách role được phép."""

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền truy cập bị từ chối. Thao tác này yêu cầu một trong các vai trò: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker
```

Áp dụng bảo vệ route:
```python
# Chỉ người có quyền ADMIN mới được gọi endpoint này:
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
):
    ...


# Cả ADMIN và MEMBER đều được phép gọi:
@router.post("/projects")
async def create_project(
    data: ProjectCreate,
    current_user: Annotated[
        User, Depends(require_roles(UserRole.ADMIN, UserRole.MEMBER))
    ],
):
    ...
```

### 3. Resource-Based Authorization & Hiểm họa BOLA / IDOR

#### Tại sao RBAC là chưa đủ?
Hãy xét kịch bản sau:
1. Endpoint `DELETE /api/v1/projects/{project_id}` được cấu hình: `require_roles(UserRole.MEMBER)`.
2. Lập trình viên kiểm tra: "Client là Member hợp lệ, cho phép xóa!".
3. Người dùng Alice (Member) tạo Project có `id = 10`.
4. Người dùng Bob (cũng là Member) gửi request: `DELETE /api/v1/projects/10`.
5. Hệ thống thấy Bob là Member → **Cho phép Bob xóa sạch dự án của Alice!**

Đây chính là **BOLA (Broken Object Level Authorization)** hay còn gọi là **IDOR (Insecure Direct Object Reference)** – lỗ hổng đứng **vị trí số 1** trong danh sách các mối đe dọa bảo mật API toàn cầu (OWASP API Top 10).

#### Giải pháp: Resource-Based Authorization
Bạn phải kiểm tra quyền trên chính **thực thể dữ liệu (resource instance)** mà client muốn thao tác:
- Người dùng chỉ được sửa/xóa dự án nếu họ là **Chủ sở hữu (Owner)** của dự án đó, **HOẶC** họ là **Admin**.

```text
Client gửi: DELETE /projects/10
                 │
                 ▼
      Xác thực danh tính (JWT) ──► current_user (ID: 5, Role: Member)
                 │
                 ▼
      Truy vấn Project 10 từ DB ──► project.owner_id là ai?
                 │
                 ├─► owner_id == current_user.id (5 == 5) ──► ✅ CHO PHÉP
                 ├─► current_user.role == ADMIN           ──► ✅ CHO PHÉP
                 └─► Khác chủ sở hữu & Không phải Admin   ──► ❌ 403 FORBIDDEN
```

### 4. Đặt Logic Phân quyền ở Router hay Service?

- **Phân quyền thô (Coarse-grained RBAC):** Đặt ở **Router qua `Depends`**. Giúp kiểm tra quyền ngay tại cửa ngõ HTTP, từ chối request sớm nhất có thể.
- **Phân quyền chi tiết trên tài nguyên (Fine-grained Resource Rules):**
  - Có thể đặt ở **FastAPI Dependency** nếu logic đơn giản (ví dụ: `get_project_with_owner_or_admin`).
  - Nên đặt ở **Service Layer** nếu nghiệp vụ phức tạp (ví dụ: task thuộc project, project thuộc workspace, kiểm tra user có nằm trong danh sách cộng tác viên có quyền `EDIT` của workspace hay không). Điều này đảm bảo toàn vẹn nghiệp vụ kể cả khi thao tác được gọi từ bên ngoài HTTP.

---

## 💻 Ví dụ thực hành

Dưới đây là một hệ thống phân quyền hoàn chỉnh kết hợp cả **RBAC** và **Resource-Based Authorization**:

```python
from enum import StrEnum
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import ForeignKey, String, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ==========================================
# 1. DATABASE MODELS & ENUMS
# ==========================================


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(default=True)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


# ==========================================
# 2. HẠ TẦNG KẾT NỐI & AUTH DEPENDENCY
# ==========================================

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with session_factory() as session:
        yield session


# Giả lập current user lấy từ JWT token
async def get_current_user() -> User:
    # Trong ứng dụng thật: decode JWT -> query DB
    return User(id=2, email="bob@taskflow.dev", role=UserRole.MEMBER)


# ==========================================
# 3. RBAC DEPENDENCY FACTORY
# ==========================================


def require_roles(*allowed_roles: UserRole):
    """Kiểm tra vai trò người dùng."""

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện hành động này.",
            )
        return current_user

    return role_checker


# ==========================================
# 4. RESOURCE-BASED POLICY CHECKER DEPENDENCY
# ==========================================


async def get_project_with_owner_permission(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Project:
    """Resource-Based Authorization Dependency.

    Chỉ cho phép tiếp tục nếu người dùng là CHỦ SỞ HỮU hoặc là ADMIN.
    """
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dự án với ID {project_id} không tồn tại.",
        )

    # Kiểm tra quyền trên bản ghi:
    is_owner = project.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_owner or is_admin):
        # ⚠️ CHỐNG LỖ HỔNG BOLA / IDOR TẠI ĐÂY
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không phải chủ sở hữu của dự án này và không có quyền sửa/xóa.",
        )

    return project


# ==========================================
# 5. API ROUTER ÁP DỤNG CÁC TẦNG PHÂN QUYỀN
# ==========================================

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


class ProjectUpdate(BaseModel):
    name: str


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Annotated[Project, Depends(get_project_with_owner_permission)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint xóa dự án: Được bảo vệ bởi Resource-Based Authorization.

    Nếu Bob (id=2) gọi xóa project của Alice (owner_id=1) -> Lập tức nhận 403 Forbidden!
    """
    await session.delete(project)
    await session.commit()


@router.get("/admin/all-system-projects")
async def list_all_system_projects(
    admin_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint quản trị tối cao: Chỉ duy nhất ADMIN mới có thể truy cập."""
    stmt = select(Project)
    return (await session.scalars(stmt)).all()
```

---

## ⚠️ Lỗi thường gặp

### 1. Trả về mã lỗi HTTP 401 khi người dùng không đủ quyền hạn
Nhiều backend developer có thói quen trả về `401 Unauthorized` cho mọi trường hợp bị chặn.
- Client đã gửi token JWT hoàn toàn hợp lệ, token chưa hết hạn.
- Nhưng tài khoản chỉ là `MEMBER`, trong khi thao tác yêu cầu `ADMIN`.
- **Hậu quả:** Nếu bạn trả về `401`, các thư viện HTTP ở frontend (như Axios) sẽ tưởng rằng token đã hết hạn và tự động kích hoạt luồng đăng xuất người dùng hoặc gửi yêu cầu refresh token một cách vô ích!
- **Chuẩn mực:** Luôn trả về **`403 Forbidden`** khi token hợp lệ nhưng thiếu quyền hạn.

### 2. Bỏ qua Resource-Based Check dẫn đến lỗ hổng IDOR/BOLA
Chỉ kiểm tra quyền chung của người dùng mà không kiểm tra quyền sở hữu ID trên URL:
```python
# ❌ LỖ HỔNG BẢO MẬT NGHIÊM TRỌNG:
@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, user: Annotated[User, Depends(get_current_user)]):
    # Ai đăng nhập cũng xóa được task của người khác chỉ bằng cách đổi task_id trên URL!
    await task_repo.delete(task_id)
```
**Cách khắc phục:** Luôn nạp entity lên trước, so sánh `task.creator_id == user.id` (hoặc kiểm tra quyền của user trong project cha) trước khi thực hiện xóa.

### 3. Sử dụng chuỗi string phân tán rải rác thay vì Enum
Viết `"admin"`, `"Admin"`, `"ADMIN"` rải rác trong các route handlers dẫn đến nguy cơ sai chính tả mà trình biên dịch hoặc IDE không phát hiện được. Luôn định nghĩa một enum tập trung: `UserRole.ADMIN`.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Cài đặt Dependency Factory kiểm tra nhiều quyền kết hợp
Xây dựng dependency factory `require_permissions(*required_permissions: str)`:
Biết rằng người dùng có một danh sách quyền dạng chuỗi (ví dụ: `user.permissions = ["project:read", "project:write", "task:delete"]`).
Yêu cầu:
1. Người dùng phải sở hữu **toàn bộ** các quyền nằm trong `required_permissions` (AND logic) thì mới được đi tiếp.
2. Nếu thiếu bất kỳ quyền nào, ném `HTTPException(403)` thông báo cụ thể quyền còn thiếu.

<details>
<summary>💡 Gợi ý</summary>

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status


def require_permissions(*required_perms: str):
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_perms = set(getattr(current_user, "permissions", []))
        missing = [p for p in required_perms if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bạn còn thiếu các quyền sau: {missing}",
            )
        return current_user

    return permission_checker
```
</details>

---

### Bài tập 2: Resource Policy Checker cho Task
Viết dependency `get_task_with_edit_permission(task_id: int, current_user, session)`:
Một người dùng được phép chỉnh sửa một Task khi và chỉ khi thỏa mãn **ít nhất một trong các điều kiện** sau:
1. Người dùng là Quản trị viên (`current_user.role == UserRole.ADMIN`).
2. Người dùng là người được giao việc (`task.assignee_id == current_user.id`).
3. Người dùng là Chủ sở hữu của Project cha chứa task đó (`project.owner_id == current_user.id`).

<details>
<summary>💡 Gợi ý</summary>

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


async def get_task_with_edit_permission(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Task:
    # Eager load project cha để kiểm tra project.owner_id
    stmt = select(Task).where(Task.id == task_id).options(joinedload(Task.project))
    task = (await session.scalars(stmt)).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task không tồn tại.")

    is_admin = current_user.role == UserRole.ADMIN
    is_assignee = task.assignee_id == current_user.id
    is_project_owner = task.project and task.project.owner_id == current_user.id

    if not (is_admin or is_assignee or is_project_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa công việc này.",
        )

    return task
```
</details>

---

### Bài tập 3: Phòng chống rò rỉ thông tin qua mã lỗi 403 vs 404
Trong một số ứng dụng nhạy cảm cao (ví dụ: tài liệu mật doanh nghiệp), khi một người dùng truy cập một tài nguyên mà họ không có quyền xem:
- Nếu bạn trả về `403 Forbidden`, kẻ tấn công biết chắc chắn tài nguyên bí mật đó **thực sự tồn tại** trên hệ thống (chỉ là họ chưa có quyền vào).
- Hãy giải thích kỹ thuật trả về `404 Not Found` thay cho `403 Forbidden` và cài đặt một flag `hide_existence: bool = True` trong policy checker.

<details>
<summary>💡 Gợi ý</summary>

```python
if not has_permission:
    if hide_existence:
        # Giả vờ như tài nguyên không hề tồn tại để chống scan ID
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài nguyên.")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền truy cập.")
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi phân biệt chính xác 100% khi nào trả về mã `401 Unauthorized` và khi nào trả về `403 Forbidden`.
- [ ] Tôi biết cách định nghĩa enum vai trò người dùng bằng `StrEnum` và xây dựng Dependency Factory `require_roles`.
- [ ] Tôi giải thích được nguyên nhân của lỗ hổng bảo mật IDOR / BOLA và biết cách phòng chống bằng Resource-Based Authorization.
- [ ] Tôi biết cách viết dependency kiểm tra quyền sở hữu đối tượng kết hợp nạp eager load entity từ database.
- [ ] Tôi hiểu rõ ranh giới kiến trúc: khi nào nên đặt phân quyền tại Router và khi nào nên đặt tại Service Layer.

---

## 📚 Đọc thêm

- [OWASP Top 10 API Security Risks: API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- [FastAPI Security – Advanced Dependencies](https://fastapi.tiangolo.com/tutorial/security/)
- [ASP.NET Core Policy-based Authorization Comparison](https://learn.microsoft.com/en-us/aspnet/core/security/authorization/policies)
- [Tiếp theo: Bài 07 – Testing FastAPI](./07-testing-fastapi.md)

<!-- nav:bottom -->
---

[⬅️ Authentication với JWT](./05-authentication-jwt.md) | [📚 Mục lục Middle](./README.md) | [Testing FastAPI ➡️](./07-testing-fastapi.md)
<!-- /nav:bottom -->
