<!-- nav:top -->
[🏠 Home](../README.md) › Phụ lục › Thuật ngữ
<!-- /nav:top -->

# Từ Điển Thuật Ngữ Kỹ Thuật (Technical Glossary)

> **Mục tiêu**: Bảng tra cứu chuyên sâu hơn 40 thuật ngữ kỹ thuật cốt lõi trong hệ sinh thái **Python, FastAPI, Kiến trúc Hệ thống Phân tán** và đối chiếu trực tiếp với các khái niệm tương đương trong **C# / .NET**. Giúp kỹ sư xóa bỏ rào cản ngôn ngữ và nắm bắt chính xác bản chất vận hành của hệ thống backend hiện đại.

---

## 📑 Danh Mục Nhóm Thuật Ngữ

- [1. Ngôn Ngữ & Máy Ảo Runtime (Language & Runtime Internals)](#1-ngôn-ngữ--máy-ảo-runtime-language--runtime-internals)
- [2. Cú Pháp & Lập Trình Hướng Đối Tượng (Syntax & OOP Patterns)](#2-cú-pháp--lập-trình-hướng-đối-tượng-syntax--oop-patterns)
- [3. Lập Trình Bất Đồng Bộ & Concurrency (Async & Concurrency)](#3-lập-trình-bất-đồng-bộ--concurrency-async--concurrency)
- [4. Web API & Framework (FastAPI & Web Ecosystem)](#4-web-api--framework-fastapi--web-ecosystem)
- [5. Cơ Sở Dữ Liệu & Bộ Nhớ Đệm (Database & Caching)](#5-cơ-sở-dữ-liệu--bộ-nhớ-đệm-database--caching)
- [6. Kiến Trúc Hệ Thống Phân Tán (Distributed Systems & Architecture)](#6-kiến-trúc-hệ-thống-phân-tán-distributed-systems--architecture)
- [7. Bảo Mật & Giám Sát Vận Hành (Security & Observability)](#7-bảo-mật--giám-sát-vận-hành-security--observability)

---

## 1. Ngôn Ngữ & Máy Ảo Runtime (Language & Runtime Internals)

### 1.1. CPython
- **Định nghĩa**: Bản cài đặt chuẩn mực và phổ biến nhất của ngôn ngữ Python, được viết bằng ngôn ngữ C. CPython biên dịch mã nguồn `.py` thành bytecode (`.pyc`) và thực thi chúng trên máy ảo dựa trên ngăn xếp (Stack-based Virtual Machine).
- **Cơ chế**: Sử dụng cơ chế đếm tham chiếu (Reference Counting) kết hợp với bộ thu gom rác chu trình tuần hoàn (Cyclic Garbage Collector) để quản lý vòng đời bộ nhớ.
- **Đối chiếu .NET**: Tương đương với **CoreCLR** (Common Language Runtime của .NET Core / .NET 8), nơi thông dịch Intermediate Language (IL) và biên dịch Just-In-Time (JIT) sang mã máy.

### 1.2. GIL (Global Interpreter Lock)
- **Định nghĩa**: Cơ chế khóa tương hỗ (Mutual Exclusion Lock) bên trong CPython nhằm ngăn chặn nhiều luồng hệ điều hành (OS Threads) cùng lúc thực thi bytecode Python. GIL đảm bảo việc quản lý bộ nhớ của CPython là an toàn luồng (thread-safe).
- **Hệ quả kỹ thuật**: Các tác vụ nặng về tính toán CPU (CPU-bound) không thể tăng tốc khi chạy đa luồng trên một tiến trình Python đơn lẻ; cần dùng đa tiến trình (`multiprocessing`). Ngược lại, tác vụ I/O-bound tự động nhả GIL khi chờ mạng hoặc đĩa.
- **Đối chiếu .NET**: **Không có tương đương trực tiếp trong .NET**. .NET CLR là môi trường Free-threading thực sự ngay từ đầu, cho phép hàng trăm luồng của ThreadPool chạy song song hoàn toàn trên đa nhân CPU.

### 1.3. Free-threaded Python (PEP 703)
- **Định nghĩa**: Tính năng mang tính bước ngoặt bắt đầu thử nghiệm từ Python 3.13, cho phép vô hiệu hóa GIL lúc biên dịch (`--disable-gil`).
- **Cơ chế**: Thay thế GIL bằng cơ chế đồng bộ khóa hạt mịn (Fine-grained Locking), đếm tham chiếu thiên vị (Biased Reference Counting) và dọn dẹp an toàn đa luồng theo chuẩn mimalloc.
- **Đối chiếu .NET**: Đưa mô hình đa luồng của Python tiệm cận với **.NET CLR / Java JVM**, cho phép xử lý đa luồng CPU-bound thực sự mà không cần phân tách đa tiến trình.

### 1.4. PEP (Python Enhancement Proposal)
- **Định nghĩa**: Tài liệu thiết kế kỹ thuật cung cấp thông tin cho cộng đồng Python, mô tả tính năng mới, quy chuẩn hoặc quy trình cho ngôn ngữ (ví dụ: PEP 8 cho quy ước code, PEP 484 cho Type Hints, PEP 703 cho Free-threading).
- **Đối chiếu .NET**: Tương đương với các **C# Language Design Notes / Proposals** trên kho lưu trữ `dotnet/csharplang` hoặc các tài liệu kiến trúc RFC của Microsoft.

### 1.5. UV
- **Định nghĩa**: Công cụ đóng gói và quản lý dự án Python thế hệ mới được viết bằng Rust bởi Astral. `uv` thay thế hoàn toàn `pip`, `virtualenv`, `poetry`, `pyenv` với tốc độ cài đặt và giải quyết phụ thuộc nhanh gấp 10–100 lần.
- **Đối chiếu .NET**: Đóng vai trò thống nhất tương tự như **`dotnet CLI`** và trình quản lý gói **NuGet**, cung cấp quản lý SDK, dependency resolution, lockfile và script running trong một nhị phân duy nhất.

---

## 2. Cú Pháp & Lập Trình Hướng Đối Tượng (Syntax & OOP Patterns)

### 2.1. Type Hints (PEP 484)
- **Định nghĩa**: Cú pháp chú thích kiểu dữ liệu được bổ sung vào Python từ phiên bản 3.5+. Type hints chỉ phục vụ cho các công cụ phân tích tĩnh (`mypy`, `pyright`, IDE) và tài liệu hóa, hoàn toàn bị bỏ qua ở runtime (kiểu vẫn mang tính dynamic trừ khi dùng thư viện kiểm thực như Pydantic).
- **Đối chiếu .NET**: Khác với C# (nơi kiểu dữ liệu được thực thi nghiêm ngặt bởi trình biên dịch Roslyn và CLR), Type Hints trong Python giống với **TypeScript**: cung cấp an toàn kiểu lúc viết mã nhưng biến mất sau khi chạy.

### 2.2. Duck Typing
- **Định nghĩa**: Triết lý thiết kế ngôn ngữ: *"Nếu nó đi như một con vịt và kêu như một con vịt, nó chính là một con vịt"*. Nghĩa là tính hợp lệ của một đối tượng được quyết định bởi sự hiện diện của các thuộc tính và phương thức tại thời điểm gọi, chứ không phải bởi việc nó kế thừa từ một class cụ thể.
- **Đối chiếu .NET**: Tương đương với kiểu `dynamic` trong C# hoặc cơ chế **Duck Typing ngầm định** trong một số cú pháp của C# (ví dụ: một class chỉ cần có phương thức `GetEnumerator()` là dùng được trong `foreach`, không bắt buộc phải kế thừa `IEnumerable`).

### 2.3. Structural Typing / Protocol (PEP 544)
- **Định nghĩa**: Mô hình kiểm tra kiểu cấu trúc tĩnh. Khi một class định nghĩa đầy đủ các phương thức được khai báo trong một `typing.Protocol`, trình kiểm tra kiểu tĩnh (`mypy`) sẽ coi class đó là một kiểu con hợp lệ mà không cần class đó phải kế thừa tường minh từ Protocol.
- **Đối chiếu .NET**: Tương tự như **Interface trong C#**, nhưng ở C# bạn bắt buộc phải khai báo `: IRepository` (Nominal Subtyping), còn Python Protocol tự động nhận diện dựa trên chữ ký hàm (Shape matching).

### 2.4. Dataclass (PEP 557)
- **Định nghĩa**: Decorator `@dataclass` tự động sinh các phương thức đặc biệt (`__init__`, `__repr__`, `__eq__`, `__hash__`) dựa trên các thuộc tính được khai báo kiểu. Thường dùng tham số `slots=True` để tối ưu bộ nhớ RAM và `frozen=True` để tạo đối tượng bất biến.
- **Đối chiếu .NET**: Tương đương trực tiếp với **`record class`** hoặc **`record struct`** trong C# 9+.

### 2.5. Dunder Method (Magic Method)
- **Định nghĩa**: Các phương thức đặc biệt có tên bắt đầu và kết thúc bằng hai dấu gạch dưới (Double Underscore, viết tắt là *Dunder*), ví dụ: `__init__`, `__str__`, `__eq__`, `__len__`, `__enter__`. Chúng cho phép tùy biến hành vi của đối tượng khi tương tác với các toán tử hoặc hàm dựng sẵn của Python.
- **Đối chiếu .NET**: Tương đương với **Operator Overloading** (`operator +`), phương thức ảo nền tảng của `System.Object` (`ToString()`, `Equals()`, `GetHashCode()`) và bộ lập chỉ mục **Indexer** (`this[int index]`).

### 2.6. Comprehension (List / Dict / Set)
- **Định nghĩa**: Cú pháp biểu thức cô đọng để khởi tạo một danh sách, từ điển hoặc tập hợp mới từ một tập hợp có sẵn thông qua việc lặp và áp dụng bộ lọc điều kiện trong một dòng lệnh.
- **Đối chiếu .NET**: Tương đương trực tiếp với cú pháp truy vấn **LINQ Query Syntax** (`from x in list where condition select transform`) hoặc các hàm mở rộng `.Select().Where().ToList()`.

### 2.7. Generator & `yield`
- **Định nghĩa**: Hàm đặc biệt trả về một iterator lười biếng (Lazy Evaluation). Mỗi khi gặp từ khóa `yield`, hàm tạm dừng trạng thái thực thi và nhả giá trị về cho caller, chỉ tính toán phần tử tiếp theo khi được yêu cầu. Tiết kiệm bộ nhớ tối đa với tập dữ liệu vô hạn.
- **Đối chiếu .NET**: Tương đương hoàn toàn với từ khóa **`yield return`** kết hợp với kiểu trả về **`IEnumerable<T>`** hoặc **`IAsyncEnumerable<T>`** trong C#.

### 2.8. Context Manager (`with` statement)
- **Định nghĩa**: Đối tượng kiểm soát việc phân bổ và giải phóng tài nguyên (file, kết nối cơ sở dữ liệu, lock) thông qua hai dunder method `__enter__` và `__exit__`, đảm bảo việc dọn dẹp luôn được thực thi ngay cả khi có ngoại lệ xảy ra.
- **Đối chiếu .NET**: Tương đương trực tiếp với khối lệnh **`using (...)`** kết hợp với giao diện **`IDisposable`** hoặc **`IAsyncDisposable`** (`DisposeAsync`).

### 2.9. Decorator
- **Định nghĩa**: Một hàm nhận đầu vào là một hàm (hoặc class) khác và trả về một hàm bao bọc (wrapper function), nhằm mở rộng hoặc thay đổi hành vi của hàm đó mà không can thiệp vào mã nguồn gốc (thực thi theo mẫu thiết kế Decorator Pattern).
- **Đối chiếu .NET**: Vừa giống **Attributes** (`[Authorize]`, `[HttpGet]`) khi dùng để đánh dấu metadata, vừa giống **ActionFilter / Middleware / AOP DispatchProxy** khi can thiệp vào luồng thực thi trước và sau của method.

---

## 3. Lập Trình Bất Đồng Bộ & Concurrency (Async & Concurrency)

### 3.1. Coroutine
- **Định nghĩa**: Một hàm được định nghĩa bằng cú pháp `async def`. Khi được gọi, nó không thực thi ngay mà trả về một đối tượng coroutine. Việc thực thi chỉ diễn ra khi được đưa vào Event Loop và được kích hoạt qua từ khóa `await`.
- **Đối chiếu .NET**: Tương đương với một phương thức bất đồng bộ trả về **`Task`** hoặc **`Task<T>`** được trình biên dịch C# phân rã thành một máy trạng thái (State Machine).

### 3.2. Event Loop
- **Định nghĩa**: Vòng lặp điều phối trung tâm của mô hình bất đồng bộ trong Python (`asyncio`). Nó quản lý danh sách các coroutines, lắng nghe các sự kiện I/O hệ thống (thông qua `epoll`, `kqueue` hoặc `IOCP`), và đánh thức coroutine tương ứng khi dữ liệu mạng/đĩa đã sẵn sàng.
- **Đối chiếu .NET**: Tương tự như **`SynchronizationContext`** trong ứng dụng UI hoặc cấu trúc **`ThreadPool TaskScheduler`** điều phối việc kích hoạt lại các continuation task của .NET.

### 3.3. `asyncio.Task`
- **Định nghĩa**: Một đối tượng bao bọc coroutine để lên lịch thực thi song song trên Event Loop thông qua `asyncio.create_task()`. Nó cung cấp các phương thức để kiểm tra trạng thái, lấy kết quả hoặc hủy bỏ tác vụ.
- **Đối chiếu .NET**: Tương đương với đối tượng **`System.Threading.Tasks.Task`** được kích hoạt thông qua **`Task.Run()`**.

### 3.4. Structured Concurrency (`asyncio.TaskGroup`)
- **Định nghĩa**: Triết lý quản lý các tác vụ đồng thời có cấu trúc (bổ sung từ Python 3.11). Khi khởi chạy nhiều tasks bên trong một `TaskGroup`, nếu một task phát sinh lỗi thì toàn bộ các tasks còn lại sẽ tự động bị hủy bỏ, ngăn ngừa triệt để tình trạng task bị bỏ rơi (Leaked Tasks).
- **Đối chiếu .NET**: Tương đương với việc quản lý một nhóm tác vụ bằng `Task.WhenAll` kết hợp với liên kết chung một **`CancellationTokenSource`**.

---

## 4. Web API & Framework (FastAPI & Web Ecosystem)

### 4.1. ASGI (Asynchronous Server Gateway Interface)
- **Định nghĩa**: Giao chuẩn kết nối chuẩn mực giữa máy chủ Web bất đồng bộ (như Uvicorn, Hypercorn) và các ứng dụng Python (như FastAPI, Starlette). ASGI hỗ trợ các giao thức HTTP/1.1, HTTP/2, và kết nối hai chiều thời gian thực WebSockets.
- **Đối chiếu .NET**: Đóng vai trò tương tự như tầng **Kestrel Hosting Pipeline** và giao diện trừu tượng `RequestDelegate` / `HttpContext` trong ASP.NET Core.

### 4.2. WSGI (Web Server Gateway Interface)
- **Định nghĩa**: Tiêu chuẩn tiền nhiệm đồng bộ (PEP 3333) dành cho các framework truyền thống như Flask hay Django Classic (chạy trên Gunicorn, uWSGI). Mỗi request chiếm dụng một luồng hoặc tiến trình riêng biệt cho đến khi hoàn thành.
- **Đối chiếu .NET**: Tương đương với kiến trúc **Classic ASP.NET trên IIS** hoặc đặc tả **OWIN** trước kỷ nguyên ASP.NET Core.

### 4.3. Pydantic
- **Định nghĩa**: Thư viện mô hình hóa và kiểm thực dữ liệu (Data Validation) nhanh nhất trong hệ sinh thái Python. Pydantic v2 được viết lại hoàn toàn phần lõi bằng Rust (`pydantic-core`), thực hiện ép kiểu an toàn và serialize dữ liệu cực nhanh.
- **Đối chiếu .NET**: Đóng vai trò kết hợp giữa **`FluentValidation`**, **`DataAnnotations`**, và bộ tuần tự hóa **`System.Text.Json`** của .NET.

### 4.4. BaseModel
- **Định nghĩa**: Lớp cơ sở của Pydantic mà các DTOs (Data Transfer Objects) hoặc View Models kế thừa để thừa hưởng khả năng tự động phân tích JSON, kiểm tra định dạng và sinh OpenAPI Schema tự động.
- **Đối chiếu .NET**: Tương đương với một **DTO Class** hoặc **Command/Query Model** trong C# có gắn các thuộc tính kiểm thực.

### 4.5. Dependency Injection (FastAPI `Depends`)
- **Định nghĩa**: Hệ thống tiêm phụ thuộc dạng hàm (Function-based DI) của FastAPI. Thông qua `Depends(get_db)`, framework tự động phân giải cây phụ thuộc, khởi tạo tài nguyên trước khi vào router và tự động dọn dẹp sau khi phản hồi trả về (thông qua generator function).
- **Đối chiếu .NET**: Tương đương với bộ chứa DI **`Microsoft.Extensions.DependencyInjection`** với vòng đời **Scoped Lifetime** (`builder.Services.AddScoped<T>()`) và thuộc tính `[FromServices]`.

### 4.6. RFC 9457 (Problem Details)
- **Định nghĩa**: Chuẩn đặc tả định dạng JSON phản hồi lỗi của các dịch vụ Web HTTP (thay thế RFC 7807), bao gồm các trường chuẩn mực: `type`, `title`, `status`, `detail`, `instance`.
- **Đối chiếu .NET**: Được hỗ trợ gốc trong ASP.NET Core 7/8 thông qua lớp **`ProblemDetails`** và phương thức `Results.Problem()`.

---

## 5. Cơ Sở Dữ Liệu & Bộ Nhớ Đệm (Database & Caching)

### 5.1. SQLAlchemy 2.0
- **Định nghĩa**: Bộ công cụ SQL và hệ thống Object-Relational Mapping (ORM) công nghiệp hàng đầu cho Python. Phiên bản 2.0 chuẩn hóa cú pháp hướng truy vấn bất đồng bộ (`select()`), tách biệt rõ ràng giữa Core và ORM.
- **Đối chiếu .NET**: Tương đương trực tiếp với **Microsoft Entity Framework Core (EF Core 8/9)**.

### 5.2. AsyncSession
- **Định nghĩa**: Phiên làm việc bất đồng bộ của SQLAlchemy 2.0, đóng vai trò là mẫu thiết kế Unit of Work, theo dõi các thay đổi của thực thể (Change Tracking) và thực thi các lệnh xuống cơ sở dữ liệu qua driver bất đồng bộ như `asyncpg`.
- **Đối chiếu .NET**: Tương đương trực tiếp với lớp **`DbContext`** trong EF Core khi sử dụng các phương thức `SaveChangesAsync()`, `ToListAsync()`.

### 5.3. Alembic
- **Định nghĩa**: Công cụ quản lý di chuyển lược đồ dữ liệu (Database Migration) chính thức của tác giả SQLAlchemy. Hỗ trợ tự động dò tìm khác biệt giữa mã nguồn Python và cơ sở dữ liệu thực tế (`--autogenerate`).
- **Đối chiếu .NET**: Tương đương với công cụ **EF Core Migrations** (`dotnet ef migrations add` và `dotnet ef database update`).

### 5.4. N+1 Query Problem
- **Định nghĩa**: Vấn đề hiệu năng nghiêm trọng khi ORM thực hiện 1 câu truy vấn lấy danh sách cha, sau đó thực hiện thêm N câu truy vấn đơn lẻ để lấy dữ liệu con trong vòng lặp. Khắc phục bằng cơ chế Eager Loading (`selectinload` hoặc `joinedload`).
- **Đối chiếu .NET**: Vấn đề hoàn toàn giống hệt trong EF Core khi quên gọi phương thức `.Include(x => x.Children)`.

### 5.5. Cache-Aside Pattern
- **Định nghĩa**: Mẫu thiết kế bộ nhớ đệm: Ứng dụng luôn kiểm tra Cache trước (Cache Hit -> trả về ngay). Nếu không có (Cache Miss), đọc từ Database, nạp vào Cache với hạn sống TTL, rồi trả về cho client.
- **Đối chiếu .NET**: Mẫu kiến trúc phổ biến nhất khi dùng `IDistributedCache` hoặc thư viện `HybridCache` trong ASP.NET Core.

### 5.6. Cache Stampede (Thundering Herd)
- **Định nghĩa**: Hiện tượng xảy ra khi một key trong Cache chứa dữ liệu được truy vấn cực lớn vừa hết hạn TTL, dẫn đến hàng ngàn request cùng lúc lao thẳng xuống Database để tính toán lại, làm sập Database. Giải quyết bằng khóa phân tán (Distributed Lock) hoặc tính toán ngầm trước hạn (Probabilistic Early Expiration / XFetch).
- **Đối chiếu .NET**: Vấn đề tương tự trong hệ thống .NET quy mô lớn, được giải quyết bằng các thư viện như `FusionCache` hoặc `HybridCache` (.NET 9).

### 5.7. Distributed Lock (Redlock)
- **Định nghĩa**: Cơ chế khóa loại trừ tương hỗ trên môi trường phân tán gồm nhiều máy chủ, đảm bảo tại một thời điểm chỉ có duy nhất một tiến trình được thực thi một khối lệnh nghiệp vụ quan trọng. Thường được triển khai bằng lệnh `SET key val NX PX` trên Redis hoặc thuật toán Redlock.
- **Đối chiếu .NET**: Tương đương với việc sử dụng thư viện **`Medallion.Threading.Redis`** hoặc **`RedLock.net`**.

---

## 6. Kiến Trúc Hệ Thống Phân Tán (Distributed Systems & Architecture)

### 6.1. Idempotency (Tính Bất Biến)
- **Định nghĩa**: Tính chất của một thao tác API mà khi thực thi lặp lại nhiều lần với cùng một đầu vào thì trạng thái của hệ thống và kết quả trả về vẫn hoàn toàn không thay đổi so với lần gọi đầu tiên. Thường áp dụng cho `POST /orders` thông qua tiêu đề `Idempotency-Key`.
- **Đối chiếu .NET**: Các middleware xử lý Idempotency tùy biến hoặc tính năng Idempotent Consumer trong các bus tin nhắn như **MassTransit** / **NServiceBus**.

### 6.2. Distributed Rate Limiting
- **Định nghĩa**: Cơ chế giới hạn số lượng yêu cầu mà một người dùng hoặc địa chỉ IP có thể gửi tới API trong một khoảng thời gian nhất định (ví dụ: 100 req/min) trên toàn bộ cụm máy chủ, thường sử dụng thuật toán Cửa sổ trượt (Sliding Window Log / Sliding Window Counter) viết bằng Redis Lua Script.
- **Đối chiếu .NET**: Tương đương với **`System.Threading.RateLimiting`** và built-in Rate Limiting Middleware xuất hiện từ ASP.NET Core 7.

### 6.3. Transactional Outbox Pattern
- **Định nghĩa**: Mẫu thiết kế kiến trúc phân tán nhằm đảm bảo tính nhất quán cuối cùng (Eventual Consistency): Thay vì vừa lưu DB vừa publish event trực tiếp lên Message Broker (dễ mất event nếu broker lỗi), ta lưu cả entity và event vào cùng một Database Transaction (bảng `outbox_events`). Một tiến trình Worker riêng sẽ đọc bảng này và đẩy lên Broker.
- **Đối chiếu .NET**: Mẫu thiết kế kinh điển được hỗ trợ sẵn trong **MassTransit Transactional Outbox** kết hợp với EF Core.

### 6.4. Circuit Breaker Pattern
- **Định nghĩa**: Cơ chế "Cầu dao điện" ngắt kết nối tạm thời tới một dịch vụ phụ thuộc bên ngoài khi dịch vụ đó liên tục gặp lỗi hoặc phản hồi chậm quá ngưỡng cho phép, tránh làm cạn kiệt tài nguyên của hệ thống gọi (Fail Fast). Gồm 3 trạng thái: Closed, Open, Half-Open.
- **Đối chiếu .NET**: Thư viện huyền thoại **`Polly`** (`Policy.Handle<Exception>().CircuitBreakerAsync(...)`) trong .NET.

### 6.5. Keyset Cursor Pagination
- **Định nghĩa**: Kỹ thuật phân trang dựa trên giá trị cột sắp xếp có gắn index (như `id` hoặc `created_at`) thay vì dùng lệnh `OFFSET n LIMIT m`. Giúp tốc độ truy vấn luôn giữ mức độ phức tạp $O(1)$ bất kể người dùng đang lướt tới trang thứ bao nhiêu, triệt tiêu hiện tượng quét toàn bộ bảng (Full Table Scan).
- **Đối chiếu .NET**: Kỹ thuật Keyset Pagination được khuyến nghị chính thức trong tài liệu tối ưu hiệu năng truy vấn của **EF Core**.

### 6.6. Graceful Shutdown
- **Định nghĩa**: Quy trình đóng ứng dụng an toàn khi nhận tín hiệu từ hệ điều hành (`SIGTERM` / `SIGINT`): Ứng dụng ngừng nhận request mới, hoàn tất nốt các request và background task đang chạy dở, giải phóng kết nối Database/Redis an toàn trước khi tiến trình chính thức dừng hẳn.
- **Đối chiếu .NET**: Được điều phối bởi **`IHostApplicationLifetime`** (`ApplicationStopping` token) trong generic host ASP.NET Core.

---

## 7. Bảo Mật & Giám Sát Vận Hành (Security & Observability)

### 7.1. BOLA (Broken Object Level Authorization / IDOR)
- **Định nghĩa**: Lỗ hổng bảo mật số 1 trong danh mục OWASP API Security Top 10: Xảy ra khi API nhận ID của một tài nguyên (ví dụ: `GET /tasks/123`) nhưng không xác minh người dùng hiện tại có quyền sở hữu hoặc quyền truy cập vào tài nguyên đó hay không, cho phép kẻ tấn công sửa ID để xem trộm dữ liệu người khác.
- **Đối chiếu .NET**: Giải quyết bằng **Resource-Based Authorization** (`IAuthorizationService.AuthorizeAsync`) trong ASP.NET Core.

### 7.2. SSRF (Server-Side Request Forgery)
- **Định nghĩa**: Lỗ hổng bảo mật cho phép kẻ tấn công lợi dụng máy chủ backend để gửi các HTTP request độc hại tới các tài nguyên nội bộ mà bên ngoài không truy cập được (như `http://169.254.169.254` Cloud Metadata hoặc mạng Private IP `10.0.0.0/8`, `192.168.0.0/16`).
- **Đối chiếu .NET**: Nguy cơ xuất phát từ việc khởi tạo tùy tiện `HttpClient` từ URL do người dùng cung cấp mà không thẩm tra IP sau khi phân giải DNS (DNS Rebinding Defense).

### 7.3. Argon2id
- **Định nghĩa**: Thuật toán băm mật khẩu hiện đại, an toàn và tối tân nhất hiện nay, chiến thắng cuộc thi Password Hashing Competition (PHC). Argon2id có khả năng chống lại cả tấn công bạo lực qua GPU/ASIC và tấn công kênh kề (Side-channel attacks) nhờ cấu hình ép buộc bộ nhớ RAM và độ phức tạp tính toán.
- **Đối chiếu .NET**: Thay thế cho thuật toán `PBKDF2` truyền thống của `PasswordHasher<TUser>` trong ASP.NET Core Identity.

### 7.4. JWT (JSON Web Token - RFC 7519)
- **Định nghĩa**: Chuỗi mã định danh chuẩn mở nhỏ gọn và khép kín, được dùng để truyền tải thông tin định danh (claims) an toàn giữa các bên dưới dạng chuỗi JSON có chữ ký số (JWS). Trong FastAPI thường dùng cặp Access Token (thời hạn ngắn) và Refresh Token (thời hạn dài).
- **Đối chiếu .NET**: Thư viện chuẩn mực **`Microsoft.AspNetCore.Authentication.JwtBearer`** trong ASP.NET Core.

### 7.5. OpenTelemetry (OTel)
- **Định nghĩa**: Khung chuẩn mực công nghiệp mã nguồn mở hợp nhất dành cho việc thu thập và xuất dữ liệu quan sát hệ thống (Observability), bao gồm **Traces** (mã vết luồng đi qua các dịch vụ), **Metrics** (chỉ số đo lường hiệu năng) và **Logs** (nhật ký có cấu trúc).
- **Đối chiếu .NET**: Được tích hợp sâu vào hạ tầng .NET thông qua lớp **`System.Diagnostics.Activity`**, thư viện `OpenTelemetry .NET SDK` và bảng điều khiển .NET Aspire Dashboard.

---

## 🎯 Bảng Tổng Kết Đối Chiếu Nhanh (Cheat Sheet)

| Thuật ngữ | Trọng tâm Ý nghĩa | Tương đương trong Thế giới C# / .NET |
|---|---|---|
| **ASGI** | Chuẩn máy chủ Web bất đồng bộ | Kestrel Hosting Pipeline |
| **GIL** | Khóa phiên dịch toàn cục CPython | *Không có (.NET là Free-threading)* |
| **Type Hints** | Chú thích kiểu tĩnh (xóa lúc chạy) | TypeScript / C# Type System (Compile-time) |
| **Protocol** | Đa hình cấu trúc không cần kế thừa | Interface (Structural Duck-typing) |
| **Dataclass** | Cấu trúc dữ liệu tự sinh hàm cơ bản | `record class` / `record struct` |
| **Comprehension** | Biểu thức biến đổi và lọc dữ liệu | LINQ (`.Select().Where().ToList()`) |
| **Generator** | Hàm sinh giá trị lười biếng (Lazy) | `yield return` & `IEnumerable<T>` |
| **AsyncSession** | Phiên làm việc ORM bất đồng bộ | EF Core `DbContext` |
| **Alembic** | Quản lý thay đổi cấu trúc bảng DB | EF Core Migrations |
| **Pydantic** | Kiểm thực và serialize dữ liệu DTO | FluentValidation + System.Text.Json |
| **FastAPI Depends** | Tiêm phụ thuộc theo hàm request | `IServiceCollection` Scoped Service |
| **OpenTelemetry** | Chuẩn quan sát vết và chỉ số phân tán | `System.Diagnostics.Activity` + OTel .NET |

<!-- nav:bottom -->
---

[🏠 Về trang chủ](../README.md)
<!-- /nav:bottom -->
