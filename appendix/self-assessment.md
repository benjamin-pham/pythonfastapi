<!-- nav:top -->
[🏠 Home](../README.md) › Phụ lục › Tự đánh giá
<!-- /nav:top -->

# Khung Tự Đánh Giá Năng Lực Kỹ Sư Backend (Self-Assessment Matrix)

> **Mục tiêu tài liệu**: Cung cấp một ma trận đánh giá năng lực minh bạch, đa chiều qua 5 cấp độ (từ người mới chuyển đổi đến kỹ sư cấp cao) và lộ trình tự vấn (Self-Assessment Checklist). Tài liệu này đóng vai trò thước đo giúp bạn xác định vị trí hiện tại của bản thân, lấp đầy các lỗ hổng kiến thức và chuẩn bị tốt nhất cho các vòng phỏng vấn kỹ thuật Backend cấp cao.

---

## 🗺️ Bản Đồ Năng Lực 5 Cấp Độ (Skill Levels Matrix)

Hành trình trưởng thành kỹ thuật được chia thành 5 chặng phát triển rõ rệt, kết nối trực tiếp với từng học phần trong lộ trình:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MA TRẬN TIẾN TRÌNH NĂNG LỰC KỸ SƯ                     │
│                                                                             │
│  [ Level 00: Khởi Đầu ] ──► Chuyển đổi tư duy C# -> Pythonic, làm chủ uv    │
│            │                                                                │
│            ▼                                                                │
│  [ Level 01: Fresher ]  ──► Nền tảng Python 3.12+, OOP, CLI Tool (M0)       │
│            │                                                                │
│            ▼                                                                │
│  [ Level 02: Junior ]   ──► FastAPI, Pydantic v2, DI, Pytest, REST API (M1) │
│            │                                                                │
│            ▼                                                                │
│  [ Level 03: Middle ]   ──► Async SQLAlchemy 2.0, JWT, Docker, CI/CD (M2)   │
│            │                                                                │
│            ▼                                                                │
│  [ Level 04: Senior ]   ──► Clean Arch, Redis, Queues, OTel, Scaling (M3)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Cấp Độ 00: Khởi Đầu (Getting Started)

> 📍 **Mục lục học phần chi tiết**: 👉 **[Level 00: Getting Started](../00-getting-started/README.md)**

Cấp độ này dành cho kỹ sư bắt đầu làm quen với hệ sinh thái Python hiện đại, thiết lập không gian làm việc chuẩn mực và gỡ bỏ các rào cản tư duy giữa thế giới .NET tĩnh và Python động.

### Checklist Tự Đánh Giá Năng Lực:
- [ ] **Môi trường & Công cụ**: Sử dụng thành thạo `uv` để quản lý phiên bản Python (`uv python install`), khởi tạo dự án (`uv init`), quản lý phụ thuộc (`uv add`), và cấu hình file `pyproject.toml` đạt chuẩn PEP 517/621.
- [ ] **IDE & Debugging**: Thiết lập VS Code với các extension hiện đại (*Python*, *Ruff*, *Mypy*), biết cấu hình `launch.json` để debug ứng dụng từng bước (step-over, step-into, inspect call stack).
- [ ] **Tư duy Chuyển đổi**: Phân biệt được cơ chế thực thi của CPython VM so với .NET CoreCLR; hiểu rõ sự khác biệt giữa `is None` và `== None`.
- [ ] **Quy ước Định dạng**: Thuần thục quy ước đặt tên PEP 8 (`snake_case` cho hàm/biến, `PascalCase` cho class, `SCREAMING_SNAKE_CASE` cho hằng số) và tự động định dạng mã nguồn với `ruff format`.

### Câu Hỏi Phỏng Vấn Tự Kiểm Tra:
1. *Tại sao việc dùng `== None` trong Python lại bị coi là Bad Practice so với `is None`? Hãy giải thích dưới góc độ dunder method `__eq__` và so sánh tham chiếu ô nhớ.*
2. *Công cụ `uv` giải quyết bài toán quản lý môi trường và tốc độ cài đặt gói tin như thế nào so với bộ đôi truyền thống `pip` + `virtualenv`?*

---

## 2. Cấp Độ 01: Kỹ Sư Mới Vào Nghề (Fresher)

> 📍 **Mục lục học phần chi tiết**: 👉 **[Level 01: Fresher](../01-fresher/README.md)**  
> 🎯 **Đồ án cột mốc tương ứng**: 👉 **[Milestone M0: CLI Task Manager](../project/m0-cli-task-manager.md)**

Cấp độ này đòi hỏi sự vững vàng tuyệt đối về cú pháp, cấu trúc dữ liệu cốt lõi, xử lý tập tin an toàn và khả năng mô hình hóa hướng đối tượng cơ bản bằng Standard Library.

### Checklist Tự Đánh Giá Năng Lực:
- [ ] **Cấu trúc Dữ liệu & Giải thuật cơ bản**: Nắm vững độ phức tạp thời gian ($O(1)$ vs $O(n)$) của các thao tác trên `list`, `dict`, `set`, và `tuple`. Biết khi nào nên dùng `set` để tra cứu nhanh hoặc lọc trùng lặp.
- [ ] **Comprehensions**: Viết thành thạo List, Dict, Set Comprehension thay thế các vòng lặp `for` lồng nhau phức tạp mà vẫn duy trì tính dễ đọc.
- [ ] **Hàm & Tham số**: Phân biệt rạch ròi giữa Positional-only arguments (`/`), Keyword-only arguments (`*`), `*args`, và `**kwargs`. Hiểu tại sao **không bao giờ** được dùng đối tượng khả biến (như `list` hay `dict`) làm giá trị mặc định cho tham số hàm.
- [ ] **Mô hình Hướng đối tượng**: Sử dụng `@dataclass(slots=True)` để đóng gói thực thể dữ liệu, định nghĩa dunder methods cơ bản (`__repr__`, `__eq__`, `__len__`).
- [ ] **Xử lý File & Ngoại lệ**: Thao tác an toàn với đĩa cứng thông qua `pathlib.Path`, áp dụng kỹ thuật Atomic Write (ghi ra file tạm `.tmp` rồi đổi tên `replace()`) để chống hỏng file khi gặp crash.
- [ ] **Hoàn thành Đồ án M0**: Tự tay xây dựng hoàn chỉnh công cụ CLI Task Manager bằng `argparse`, hỗ trợ đầy đủ các lệnh `add`, `list`, `update`, `delete` lưu trữ vào `tasks.json`.

### Câu Hỏi Phỏng Vấn Tự Kiểm Tra:
1. *Giải thích điều gì sẽ xảy ra khi thực thi hàm `def append_item(x, items=[]): items.append(x); return items` qua 3 lần gọi liên tiếp? Cách sửa chuẩn Pythonic là gì?*
2. *Sự khác nhau về mặt lưu trữ bộ nhớ và tốc độ truy cập giữa `@dataclass` thông thường và `@dataclass(slots=True)` là gì?*

---

## 3. Cấp Độ 02: Kỹ Sư Sơ Cấp (Junior)

> 📍 **Mục lục học phần chi tiết**: 👉 **[Level 02: Junior](../02-junior/README.md)**  
> 🎯 **Đồ án cột mốc tương ứng**: 👉 **[Milestone M1: RESTful CRUD API](../project/m1-crud-api.md)**

Kỹ sư cấp độ Junior đã có khả năng xây dựng các dịch vụ Web RESTful hoàn chỉnh, làm chủ framework FastAPI, áp dụng kiểm thực dữ liệu Pydantic v2 và viết kiểm thử tự động toàn diện.

### Checklist Tự Đánh Giá Năng Lực:
- [ ] **FastAPI & ASGI**: Hiểu rõ vòng đời của một HTTP Request đi qua các router của FastAPI; phân biệt được cách Uvicorn và FastAPI phối hợp xử lý request.
- [ ] **Pydantic v2**: Xây dựng các Schema phức tạp kế thừa `BaseModel`, viết các hàm validation tùy biến bằng `@field_validator` và `@model_validator(mode="after")`, nắm vững cơ chế `exclude_unset=True` khi xử lý Partial Update (`PATCH`).
- [ ] **Dependency Injection**: Vận dụng thành thạo `Depends` để tiêm các dịch vụ (Services), cấu hình (Settings) hoặc phiên kết nối cơ sở dữ liệu.
- [ ] **Chuẩn hóa Phản hồi Lỗi**: Không trả về lỗi dạng text thô; 100% các phản hồi ngoại lệ đều tuân thủ cấu trúc chuẩn quốc tế **RFC 9457 Problem Details**.
- [ ] **Kiểm thử Tự động với Pytest**: Xây dựng test suite sử dụng `pytest` và `TestClient`, tận dụng Fixtures linh hoạt và `@pytest.mark.parametrize` để kiểm thử nhiều tập dữ liệu đầu vào.
- [ ] **Hoàn thành Đồ án M1**: Xây dựng RESTful API quản lý `Project` và `Task` theo kiến trúc phân tầng sạch (Clean Layered Architecture), in-memory persistence, bao phủ test đạt độ tin cậy cao.

### Câu Hỏi Phỏng Vấn Tự Kiểm Tra:
1. *Tại sao Pydantic v2 lại đạt được tốc độ kiểm thực nhanh hơn Pydantic v1 từ 5 đến 20 lần? Kiến trúc lõi `pydantic-core` được xây dựng bằng công nghệ gì?*
2. *Trong FastAPI, cơ chế Dependency Injection qua generator function (`yield`) quản lý việc khởi tạo và giải phóng tài nguyên sau khi trả response về client như thế nào?*

---

## 4. Cấp Độ 03: Kỹ Sư Trung Cấp (Middle)

> 📍 **Mục lục học phần chi tiết**: 👉 **[Level 03: Middle](../03-middle/README.md)**  
> 🎯 **Đồ án cột mốc tương ứng**: 👉 **[Milestone M2: Production-Ready API](../project/m2-production-api.md)**

Ở cấp độ Middle, kỹ sư làm chủ các kỹ thuật cốt lõi để đưa ứng dụng vào môi trường Production: Cơ sở dữ liệu quan hệ bất đồng bộ, di chuyển lược đồ, xác thực & phân quyền đa tầng, container hóa Docker và tự động hóa CI/CD.

### Checklist Tự Đánh Giá Năng Lực:
- [ ] **Lập trình Bất đồng bộ Thực chiến**: Hiểu sâu cơ chế Event Loop; nhận diện và triệt tiêu hoàn toàn các lỗi nghẽn Event Loop (Event Loop Starvation do blocking sync calls).
- [ ] **SQLAlchemy 2.0 Async ORM**: Sử dụng thành thạo `AsyncSession`, viết câu truy vấn bằng cú pháp `select()`, nắm rõ các chiến lược nạp dữ liệu quan hệ (`selectinload`, `joinedload`) để triệt tiêu bài toán **N+1 Query Problem**.
- [ ] **Alembic Migrations**: Quản lý lịch sử di chuyển database an toàn, viết các script migration tùy biến cho dữ liệu lớn mà không gây khóa chết bảng (Table Lock).
- [ ] **Xác thực & Phân quyền Toàn diện**: Cài đặt quy trình đăng nhập/đăng ký bằng thuật toán băm mật khẩu **Argon2id**, cấp phát và giải mã cặp mã **JWT Access/Refresh Tokens**, kết hợp kiểm soát quyền RBAC và phòng vệ triệt để lỗ hổng **BOLA / IDOR**.
- [ ] **Phân trang & Lọc Dữ liệu**: Xây dựng Generic Response Schema `Page[T]`, bộ lọc động đa tiêu chí và sắp xếp an toàn chống SQL Injection.
- [ ] **Container & CI/CD**: Viết Dockerfile Multi-stage tối ưu dung lượng và tốc độ build bằng `uv`, thiết lập cụm `compose.yaml` (FastAPI + PostgreSQL + pgAdmin), và cấu hình pipeline GitHub Actions tự động lint và test.
- [ ] **Hoàn thành Đồ án M2**: Triển khai hoàn chỉnh hệ thống TaskFlow Production API với PostgreSQL 17 và bảo vệ danh tính toàn diện.

### Câu Hỏi Phỏng Vấn Tự Kiểm Tra:
1. *Hãy giải thích bản chất của bài toán N+1 Query trong SQLAlchemy ORM. Khi nào nên dùng `selectinload` và khi nào nên dùng `joinedload`?*
2. *Lỗ hổng BOLA (Broken Object Level Authorization) trong OWASP API Security Top 10 là gì? Tại sao chỉ kiểm tra Role của người dùng (`Role == "MEMBER"`) là chưa đủ để ngăn chặn BOLA?*

---

## 5. Cấp Độ 04: Kỹ Sư Cao Cấp & Kiến Trúc Sư (Senior / Architect)

> 📍 **Mục lục học phần chi tiết**: 👉 **[Level 04: Senior](../04-senior/README.md)**  
> 🎯 **Đồ án cột mốc tương ứng**: 👉 **[Milestone M3: Scalable Distributed API](../project/m3-scalable-api.md)**

Kỹ sư cấp cao không chỉ viết mã tốt mà còn chịu trách nhiệm về kiến trúc tổng thể, khả năng co giãn quy mô lớn, tính sẵn sàng cao, bảo mật chuyên sâu, khả năng giám sát vận hành và dẫn dắt đội ngũ kỹ thuật.

### Checklist Tự Đánh Giá Năng Lực:
- [ ] **Kiến trúc Phần mềm Cao cấp**: Nắm vững và áp dụng thuần thục **Clean Architecture / Hexagonal Architecture** (Ports & Adapters), phân tách hoàn toàn Domain Entities khỏi Database Models và Web Frameworks.
- [ ] **Bộ nhớ đệm & Chống Sập Hệ thống**: Thiết kế chiến lược Caching với Redis theo mô hình Cache-Aside, xử lý triệt để hiện tượng **Cache Stampede (Thundering Herd)** bằng Khóa Phân Tán (Distributed Mutex Locks / Redlock).
- [ ] **Xử lý Tác vụ Nền Phân tán**: Tách rời các tác vụ nặng (báo cáo, gửi email hàng loạt) sang cụm Worker **ARQ** độc lập, quản lý hàng đợi an toàn trên Redis.
- [ ] **Tính năng Thời Gian Thực (Realtime)**: Xây dựng cổng giao tiếp hai chiều **WebSockets / SSE**, sử dụng Redis Pub/Sub Backplane để phát sóng sự kiện xuyên suốt nhiều Pods máy chủ.
- [ ] **Độ Tin Cậy & Chống Trùng Lặp**: Triển khai cơ chế **Idempotency** với kiểm tra dấu vân tay (Fingerprint Hashing), và giới hạn tần suất phân tán (Distributed Sliding Window Rate Limiting bằng Redis Lua Scripts).
- [ ] **Phân trang Con trỏ (Keyset Cursor)**: Thay thế phân trang Offset truyền thống bằng Keyset Cursor Pagination với độ phức tạp $O(1)$, tối ưu hóa truy vấn cho tập dữ liệu hàng triệu bản ghi.
- [ ] **Khả năng Giám sát (Full-stack Observability)**: Tích hợp chuẩn mực **OpenTelemetry**, phân bổ Distributed Tracing với W3C TraceContext xuyên suốt API và Background Workers, thu thập Prometheus Metrics và Structured JSON Logging.
- [ ] **Vận hành & Mở rộng**: Triển khai và điều phối ứng dụng trên Kubernetes, cấu hình Horizontal Pod Autoscaler (HPA), Readiness/Liveness Probes, và Graceful Shutdown an toàn.
- [ ] **Hoàn thành Đồ án M3**: Xây dựng thành công toàn bộ hệ thống phân tán TaskFlow Scalable API.

---

## 🧠 Lời Khuyên Phỏng Vấn & Chuyển Đổi Tư Duy Dành Cho Senior

### 1. Tư Duy Quyết Định Kiến Trúc: Đừng Chọn "Tốt Nhất", Hãy Chọn "Phù Hợp Nhất"
Trong các buổi phỏng vấn kỹ thuật cấp cao (System Design Interview), các câu hỏi thường không có một đáp án duy nhất đúng. Người phỏng vấn không tìm kiếm câu trả lời "Tôi sẽ dùng Kafka và Microservices", mà họ đánh giá **năng lực phân tích đánh đổi (Trade-offs Analysis)**:
- *Tại sao dùng PostgreSQL kết hợp ARQ và Redis thay vì dựng một cụm Kafka phức tạp ngay từ đầu?*
- *Khi nào nên dùng Cache-Aside, và khi nào nên chấp nhận đọc trực tiếp từ Read-Replica Database để tránh độ trễ đồng bộ cache?*
- *Chi phí vận hành và rủi ro quản lý dữ liệu phân tán (Distributed Transactions / 2PC) so với giải pháp Transactional Outbox Pattern là gì?*

### 2. Phát Huy Lợi Thế Xuất Phát Điểm từ C# / .NET
Là một kỹ sư có nền tảng C# / .NET chuyển sang Python, bạn sở hữu những vũ khí rất mạnh mà nhiều lập trình viên chỉ học Python thuần túy thường thiếu hụt:
- **Tư duy hướng đối tượng và kiểu dữ liệu chặt chẽ**: Bạn biết cách mô hình hóa miền nghiệp vụ mạch lạc, không lạm dụng dynamic typing để viết mã cẩu thả.
- **Hiểu sâu về Concurrency và Hệ điều hành**: Bạn hiểu rõ luồng OS, Context Switching, Memory Pointers, Garbage Collection, giúp bạn dễ dàng làm chủ mô hình Asyncio và tránh các lỗi tắc nghẽn Event Loop.
- **Kỷ luật kiến trúc doanh nghiệp**: Bạn quen thuộc với các mẫu thiết kế lớn (Dependency Injection, Unit of Work, Repository, CQRS), giúp mã nguồn Python của bạn có tính module hóa cao và sẵn sàng scale lớn.

### 3. Kỹ Năng Mềm & Văn Hóa Lãnh Đạo Kỹ Thuật (Technical Leadership)
Ở đẳng cấp Senior và Staff Engineer, giá trị của bạn được đo lường qua sự thành công của cả tập thể:
- **Viết Architecture Decision Records (ADR)**: Mọi quyết định kỹ thuật quan trọng (chọn thư viện, đổi cấu trúc DB, thiết lập cache) đều được ghi chép lý do, các phương án thay thế đã cân nhắc và hệ quả kỹ thuật dự kiến.
- **Code Review mang tính xây dựng**: Không chỉ bắt lỗi cú pháp (đó là việc của Ruff và Mypy), hãy tập trung vào tính đúng đắn của nghiệp vụ, an ninh bảo mật, các điểm nghẽn hiệu năng tiềm ẩn và tính dễ bảo trì.
- **Tạo điều kiện và cố vấn (Mentoring)**: Dành thời gian hướng dẫn các bạn Fresher và Junior, biến các sự cố kỹ thuật (Incidents) thành các buổi mổ xẻ học tập (Blameless Post-mortem) để cải thiện quy trình của toàn đội ngũ.

---

## 🎯 Bảng Tóm Tắt Tự Xếp Hạng Bản Thân

Hãy tự đánh dấu mức độ tự tin của bạn (từ 1 đến 5 sao) cho từng phân khúc chuyên môn:

| Phân Vùng Chuyên Môn | 1 ⭐ (Biết Khái Niệm) | 3 ⭐ (Làm Được Độc Lập) | 5 ⭐ (Làm Chủ & Cố Vấn Được) |
|---|:---:|:---:|:---:|
| **Pythonic & Ngôn ngữ Hiện đại** | ☐ | ☐ | ☐ |
| **FastAPI, Pydantic & API Design** | ☐ | ☐ | ☐ |
| **Cơ sở dữ liệu & SQLAlchemy 2.0 Async** | ☐ | ☐ | ☐ |
| **Bảo mật, Xác thực & OWASP Top 10** | ☐ | ☐ | ☐ |
| **Hệ thống Phân tán (Redis, Queue, Workers)** | ☐ | ☐ | ☐ |
| **Observability (OTel, Tracing, Metrics)** | ☐ | ☐ | ☐ |
| **DevOps, Docker, CI/CD & Kubernetes** | ☐ | ☐ | ☐ |
| **System Design & Đánh đổi Kiến trúc** | ☐ | ☐ | ☐ |

Chúc bạn luôn giữ vững ngọn lửa đam mê, không ngừng học hỏi và chinh phục đỉnh cao sự nghiệp kỹ sư phần mềm!

<!-- nav:bottom -->
---

[🏠 Về trang chủ](../README.md)
<!-- /nav:bottom -->
