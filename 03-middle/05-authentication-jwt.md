<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 05
<!-- /nav:top -->

# Authentication với JWT

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 04: Repository & Service layer](./04-repository-service-layer.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ nguyên lý xác thực phi trạng thái (**Stateless Authentication**) sử dụng **JSON Web Token (JWT)** theo chuẩn RFC 7519.
- Nắm vững giải pháp băm mật khẩu hiện đại với **`pwdlib`** (hỗ trợ thuật toán **Argon2id** và Bcrypt), hiểu lý do thư viện kinh điển `passlib` đã bị khai tử trên Python 3.13+.
- Thiết kế chiến lược quản lý phiên làm việc bảo mật cao: phân định rõ vai trò của **Access Token** (ngắn hạn: 15–30 phút) và **Refresh Token** (dài hạn: 7–30 ngày).
- Tích hợp chuẩn giao thức **`OAuth2PasswordBearer`** kết hợp với **`OAuth2PasswordRequestForm`** để tự động kích hoạt nút "Authorize" (ổ khóa xanh) tương tác trực tiếp trên Swagger UI (`/docs`).
- Xây dựng FastAPI Dependency **`get_current_user`** giải mã token, xác minh chữ ký mã hóa, kiểm tra thời hạn sống và truy vấn thông tin định danh người dùng.
- Trả về mã lỗi HTTP 401 chuẩn mực kèm theo header bắt buộc **`WWW-Authenticate: Bearer`** theo chuẩn RFC 6750.

---

## 🔁 So sánh với C# / ASP.NET Core Authentication

Trong thế giới ASP.NET Core, hệ thống xác thực thường được cấu hình tập trung thông qua Authentication Middleware và các gói thư viện chuẩn của Microsoft:

| Khái niệm / Thành phần | ASP.NET Core (C#) | FastAPI (Python 3.12+) |
|---|---|---|
| **Băm & Kiểm tra Mật khẩu** | `IPasswordHasher<TUser>` (dùng PBKDF2 mặc định trong ASP.NET Core Identity) | `pwdlib` (`PasswordHash.recommended()` sử dụng thuật toán hàng đầu **Argon2id**) |
| **Xử lý JWT Tokens** | `Microsoft.AspNetCore.Authentication.JwtBearer` & `JwtSecurityTokenHandler` | Thư viện chuẩn mực **`PyJWT`** (`jwt.encode`, `jwt.decode`) |
| **Đăng ký Middleware Xác thực** | `app.UseAuthentication()` & `builder.Services.AddAuthentication(JwtBearerDefaults...)` | Không cần middleware toàn cục: Sử dụng Dependency **`Depends(get_current_user)`** linh hoạt tại từng route |
| **Bảo vệ Endpoint** | Thuộc tính `[Authorize]` trên Controller hoặc Action method | Nhận tham số: `current_user: Annotated[User, Depends(get_current_user)]` |
| **Đối tượng Định danh người dùng** | `HttpContext.User` kiểu `ClaimsPrincipal` | Trả về trực tiếp Pydantic DTO hoặc Entity `User` từ database |
| **Swagger UI Login** | Cần cấu hình thủ công `AddSecurityDefinition("Bearer", ...)` trong Swashbuckle | **Tự động 100%**: FastAPI tự sinh giao diện Login trên Swagger khi dùng `OAuth2PasswordBearer` |
| **Trích xuất Token từ Request** | Authentication Handler đọc từ header `Authorization: Bearer <token>` | `OAuth2PasswordBearer` tự động đọc và bóc tách chuỗi token |

---

## 📖 Lý thuyết

### 1. Băm mật khẩu thời hiện đại: Tạm biệt `passlib`, chào đón `pwdlib`

Trong nhiều năm, thư viện `passlib` là lựa chọn mặc định trong các tài liệu hướng dẫn FastAPI. Tuy nhiên:
- `passlib` đã bị ngừng bảo trì (abandoned) từ năm 2020.
- Trên **Python 3.13**, module C tích hợp sẵn `crypt` đã chính thức bị gỡ bỏ khỏi Python Standard Library (PEP 594), khiến cho `passlib` bị **crash ngay khi import** với lỗi: `ImportError: cannot import name 'crypt' from 'crypt'`.

**Chuẩn khuyến nghị hiện đại: `pwdlib`**
Thư viện `pwdlib` được phát triển tương thích hoàn toàn với hệ sinh thái Python hiện đại, hỗ trợ mặc định thuật toán **Argon2id** – thuật toán đã chiến thắng cuộc thi Hashing quốc tế (Password Hashing Competition) với khả năng chống lại các cuộc tấn công vét cạn bằng phần cứng chuyên dụng (GPU, ASIC):

```bash
# Cài đặt thư viện với backend Argon2 tối ưu
pip install "pwdlib[argon2]"
```

Cách sử dụng tinh gọn:
```python
from pwdlib import PasswordHash

# Khởi tạo instance với thuật toán được khuyến nghị (Argon2id)
password_hash = PasswordHash.recommended()

# 1. Băm mật khẩu khi người dùng đăng ký
hashed = password_hash.hash("MySuperSecurePassword123!")

# 2. Kiểm tra mật khẩu khi người dùng đăng nhập
is_valid = password_hash.verify("MySuperSecurePassword123!", hashed)  # True
is_wrong = password_hash.verify("WrongPassword", hashed)  # False
```

### 2. Cấu trúc JSON Web Token (JWT) theo chuẩn RFC 7519

JWT là một chuỗi mã hóa gồm 3 phần được phân tách bởi dấu chấm (`.`):

```text
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTYiLCJleHAiOjE3MDAwMDAwMDB9.4z9X8c...
  └─────────────────┬─────────────────┘ └──────────────────────┬──────────────────────┘ └─────┬────┘
                 HEADER                                     PAYLOAD                             SIGNATURE
```

1. **Header**: Chứa thuật toán mã hóa (ví dụ: `HS256` hoặc `RS256`) và loại token (`JWT`).
2. **Payload (Claims)**: Dữ liệu JSON chứa thông tin định danh:
   - `sub` (Subject): Mã định danh duy nhất của người dùng (ID hoặc email).
   - `exp` (Expiration Time): Thời điểm token hết hạn (Unix timestamp).
   - `type`: Phân loại token (`"access"` hoặc `"refresh"`).
3. **Signature (Chữ ký điện tử)**: Được tạo ra bằng cách băm kết hợp `Header + Payload` cùng một chuỗi bí mật (`SECRET_KEY`) ở phía server. Nhờ chữ ký này, client không thể chỉnh sửa payload mà không làm hỏng token.

### 3. Chiến lược Access Token & Refresh Token

```text
┌────────┐                                          ┌────────┐
│ Client │                                          │ Server │
└────┬───┘                                          └───┬────┘
     │ 1. POST /login (username, password)              │
     ├─────────────────────────────────────────────────►│
     │ 2. Trả về Access Token (15p) + Refresh Token (7d)│
     │◄─────────────────────────────────────────────────┤
     │                                                  │
     │ 3. GET /projects (Authorization: Bearer <Access>)│
     ├─────────────────────────────────────────────────►│ (Hợp lệ -> Trả dữ liệu)
     │◄─────────────────────────────────────────────────┤
     │                                                  │
     │ ... (15 phút sau, Access Token hết hạn) ...      │
     │                                                  │
     │ 4. GET /projects (Authorization: Bearer <Access>)│
     ├─────────────────────────────────────────────────►│
     │ 5. Lỗi 401 Unauthorized (Token expired)          │
     │◄─────────────────────────────────────────────────┤
     │                                                  │
     │ 6. POST /refresh (Gửi Refresh Token)             │
     ├─────────────────────────────────────────────────►│
     │ 7. Cấp Access Token mới (kèm Refresh Token mới)  │
     │◄─────────────────────────────────────────────────┤
```

- **Access Token:** Có tuổi thọ rất ngắn (**15 đến 30 phút**). Dùng để xác thực mọi yêu cầu API. Vì tuổi thọ ngắn, nếu hacker đánh cắp được token này, thiệt hại sẽ tự động kết thúc sau vài phút.
- **Refresh Token:** Có tuổi thọ dài (**7 đến 30 ngày**). Chỉ dùng duy nhất tại endpoint `/api/v1/auth/refresh` để xin cấp Access Token mới. Refresh Token có thể được lưu trữ trong DB để có thể chủ động **thu hồi (Revoke)** khi người dùng ấn nút "Đăng xuất" hoặc khi tài khoản bị khóa.

### 4. Tích hợp `OAuth2PasswordBearer` và Swagger UI

FastAPI cung cấp lớp `OAuth2PasswordBearer` tuân thủ chuẩn OAuth2 Specification:

```python
from fastapi.security import OAuth2PasswordBearer

# Khai báo URL endpoint mà Swagger UI sẽ gửi form login đến
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
```

Khi bạn sử dụng `oauth2_scheme` làm dependency:
1. Framework tự động đọc header HTTP `Authorization: Bearer <token>`. Nếu header bị thiếu hoặc sai định dạng, FastAPI tự trả về lỗi `401 Unauthorized`.
2. Trên Swagger UI (`/docs`), một nút **"Authorize"** màu xanh lá kèm biểu tượng ổ khóa sẽ tự động xuất hiện. Khi nhấn vào, Swagger UI hiển thị form nhập `username` và `password`, tự động gửi request đến `tokenUrl` và tự động gắn Bearer Token vào tất cả các request thử nghiệm sau đó.

---

## 💻 Ví dụ thực hành

Dưới đây là mã nguồn hoàn chỉnh của một hệ thống xác thực JWT sản xuất:

### 1. Module Bảo mật Token & Hasher (`app/core/security.py`)

```python
from datetime import UTC, datetime, timedelta
from typing import Any
import jwt
from pwdlib import PasswordHash

# Cấu hình bảo mật
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION_TO_A_SUPER_LONG_RANDOM_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Khởi tạo Hasher hiện đại với Argon2id
pwd_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Băm mật khẩu sử dụng Argon2id."""
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập với bản băm trong DB."""
    return pwd_hasher.verify(plain_password, hashed_password)


def create_token(
    subject: str | int,
    expires_delta: timedelta,
    token_type: str = "access",
) -> str:
    """Tạo JWT token có chữ ký số với claim thời gian hết hạn."""
    now = datetime.now(UTC)
    expire = now + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": token_type,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str | int) -> str:
    return create_token(
        subject=subject,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(subject: str | int) -> str:
    return create_token(
        subject=subject,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Giải mã và xác minh tính toàn vẹn của token.

    Ném ngoại lệ jwt.PyJWTError nếu token không hợp lệ hoặc hết hạn.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Token type must be '{expected_type}'")
    return payload
```

### 2. Dependency Xác thực Người dùng Hiện tại (`app/api/deps.py`)

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import BaseModel
from app.core.security import decode_token

# Tích hợp OAuth2 scheme cho Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UserTokenPayload(BaseModel):
    user_id: int
    email: str


# Giả lập database người dùng trong bộ nhớ cho ví dụ
class MockUser(BaseModel):
    id: int
    email: str
    is_active: bool = True


FAKE_USERS_DB: dict[int, MockUser] = {
    1: MockUser(id=1, email="admin@taskflow.dev", is_active=True),
    2: MockUser(id=2, email="locked@taskflow.dev", is_active=False),
}


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> MockUser:
    """Dependency trích xuất và xác thực Access Token từ Request Header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Thông tin xác thực không hợp lệ hoặc đã hết hạn.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token, expected_type="access")
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        user_id = int(user_id_raw)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    # Truy vấn người dùng từ cơ sở dữ liệu
    user = FAKE_USERS_DB.get(user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[MockUser, Depends(get_current_user)],
) -> MockUser:
    """Kiểm tra bổ sung xem tài khoản có đang bị khóa hay không."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản người dùng đã bị vô hiệu hóa.",
        )
    return current_user
```

### 3. Router Đăng nhập & Cấp phát Token (`app/api/auth.py`)

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from pydantic import BaseModel
from app.api.deps import MockUser, get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@auth_router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """Endpoint đăng nhập chuẩn OAuth2 Password Flow.

    Tương thích 100% với form đăng nhập trên Swagger UI.
    """
    # Trong thực tế: Truy vấn user theo form_data.username và verify_password(form_data.password, user.hashed_password)
    if form_data.username != "admin@taskflow.dev" or form_data.password != "Secret123!":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = 1
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(payload: RefreshRequest) -> TokenResponse:
    """Đổi Refresh Token lấy một cặp Access/Refresh Token mới."""
    try:
        data = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(data["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),  # Token Rotation
    )


@auth_router.get("/me", response_model=MockUser)
async def get_my_profile(
    current_user: Annotated[MockUser, Depends(get_current_active_user)],
) -> MockUser:
    """Endpoint được bảo vệ: Xem thông tin người dùng đang đăng nhập."""
    return current_user
```

---

## ⚠️ Lỗi thường gặp

### 1. Dùng `passlib` trên môi trường Python 3.13 gây sập ứng dụng
```python
# ❌ LỖI CRASH TRÊN PYTHON 3.13:
from passlib.context import CryptContext  # Sập: ImportError: cannot import name 'crypt' from 'crypt'
```
**Cách khắc phục:** Chuyển sang sử dụng `pwdlib` (`pip install "pwdlib[argon2]"`).

### 2. Quên kiểm tra claim `type` của Token
Nếu hàm xác thực chỉ đọc `payload["sub"]` mà không kiểm tra `payload["type"] == "access"`:
- Kẻ tấn công có thể lấy **Refresh Token** (có hạn 30 ngày) và gắn trực tiếp vào header `Authorization: Bearer <refresh_token>` để gọi các API bảo vệ!
- **Cách khắc phục:** Luôn đính kèm claim `type` trong payload và kiểm tra nghiêm ngặt khi giải mã.

### 3. Trả về mã lỗi HTTP 403 thay vì 401 khi Token không hợp lệ
- Khi client gửi token sai, hết hạn, hoặc không gửi token: Phải trả về **`401 Unauthorized`** kèm header `WWW-Authenticate: Bearer`.
- Chỉ trả về **`403 Forbidden`** khi token **hoàn toàn hợp lệ** (hệ thống đã xác minh được bạn là ai), nhưng tài khoản của bạn không có đủ thẩm quyền thực hiện thao tác đó.

### 4. Hardcode `SECRET_KEY` trong mã nguồn Git
Nếu `SECRET_KEY` bị lộ, bất kỳ ai cũng có thể tự ký một JWT giả mạo với quyền Admin cao nhất (`sub: 1`) mà server không thể nào phát hiện được. Luôn đọc secret key từ biến môi trường qua `pydantic-settings`.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Viết Unit Test kiểm tra Hasher `pwdlib`
Sử dụng `pytest` để viết các test cases kiểm tra:
1. Mật khẩu khi băm ra không được trùng với mật khẩu gốc ban đầu.
2. Hai lần băm cùng một mật khẩu phải sinh ra hai chuỗi băm khác nhau (do cơ chế tự sinh salt ngẫu nhiên của Argon2).
3. Hàm `verify` trả về `True` khi đúng mật khẩu và `False` khi sai mật khẩu.

<details>
<summary>💡 Gợi ý</summary>

```python
from pwdlib import PasswordHash


def test_password_hashing():
    hasher = PasswordHash.recommended()
    raw = "MySecretPass_2026"

    h1 = hasher.hash(raw)
    h2 = hasher.hash(raw)

    assert h1 != raw
    assert h1 != h2  # Salt ngẫu nhiên
    assert hasher.verify(raw, h1) is True
    assert hasher.verify("WrongPass", h1) is False
```
</details>

---

### Bài tập 2: Cơ chế Blacklist Token trong bộ nhớ cho tính năng Logout
Viết dependency hoặc hàm `revoke_token(token: str)` và sửa hàm `get_current_user` để từ chối các token đã bị đưa vào danh sách đen sau khi người dùng bấm Đăng xuất.

<details>
<summary>💡 Gợi ý</summary>

```python
# Bộ nhớ lưu token bị thu hồi (Trong production nên dùng Redis có TTL = exp của token)
REVOKED_TOKENS: set[str] = set()


def revoke_token(token: str) -> None:
    REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS
```
Bổ sung vào `get_current_user`:
```python
if is_token_revoked(token):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập đã bị hủy. Vui lòng đăng nhập lại.",
    )
```
</details>

---

### Bài tập 3: Token Rotation trong Endpoint `/refresh`
Khi client gửi yêu cầu refresh token:
1. Xác minh refresh token hiện tại.
2. Vô hiệu hóa ngay lập tức refresh token cũ vừa dùng.
3. Cấp phát cả Access Token mới VÀ Refresh Token mới toanh trả về cho client.
Giải thích tại sao kỹ thuật Token Rotation lại giúp phát hiện kẻ trộm đánh cắp token.

<details>
<summary>💡 Gợi ý</summary>

Nếu hacker đánh cắp được Refresh Token và sử dụng nó trước người dùng thật:
- Khi người dùng thật cố gắng refresh, họ sẽ gửi token đã bị vô hiệu hóa.
- Hệ thống phát hiện có hành vi tái sử dụng token đã hết hạn / bị thu hồi -> Lập tức hủy toàn bộ các session của user đó và yêu cầu đăng nhập lại bằng mật khẩu.
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được sự khác nhau giữa Stateless Authentication (JWT) và Stateful Session Authentication.
- [ ] Tôi biết lý do thư viện `passlib` bị hỏng trên Python 3.13 và chuyển giao thành công sang `pwdlib[argon2]`.
- [ ] Tôi hiểu rõ vai trò và thời gian sống khác biệt giữa Access Token và Refresh Token.
- [ ] Tôi biết cách sử dụng `OAuth2PasswordBearer` và `OAuth2PasswordRequestForm` để kích hoạt giao diện Authorize trên Swagger UI.
- [ ] Tôi viết được dependency `get_current_user` xử lý đầy đủ các trường hợp ngoại lệ giải mã token và trả về mã lỗi 401 kèm header `WWW-Authenticate: Bearer`.

---

## 📚 Đọc thêm

- [FastAPI Security Tutorial – OAuth2 with Password and Bearer with JWT tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [RFC 7519: JSON Web Token (JWT) Specification](https://datatracker.ietf.org/doc/html/rfc7519)
- [pwdlib Documentation](https://github.com/frankie567/pwdlib)
- [Tiếp theo: Bài 06 – Authorization](./06-authorization.md)

<!-- nav:bottom -->
---

[⬅️ Repository & Service layer](./04-repository-service-layer.md) | [📚 Mục lục Middle](./README.md) | [Authorization ➡️](./06-authorization.md)
<!-- /nav:bottom -->
