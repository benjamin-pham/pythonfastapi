<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 12
<!-- /nav:top -->

# Kỹ năng senior

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Hoàn thành toàn bộ các bài học kỹ thuật trong [Level 04: Senior](./README.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Định hình tư duy Kỹ sư Cấp cao (The Senior Mindset)**: Chuyển dịch căn bản từ một lập trình viên chỉ thuần túy nhận vé công việc (Code Monkey) sang một chuyên gia giải quyết vấn đề kinh doanh (Business Problem Solver), luôn cân nhắc bài toán chi phí, thời gian và giá trị thực tế.
- **Thành thạo kỹ năng soạn thảo RFC và ADR**: Biết cách chuyển hóa các ý tưởng kiến trúc phức tạp thành tài liệu kỹ thuật có cấu trúc chuẩn mực (Request for Comments & Architecture Decision Records), thuyết phục các bên liên quan và lưu giữ tri thức cho tổ chức.
- **Làm chủ nghệ thuật Code Review đa chiều**: Nâng tầm buổi duyệt code thành không gian trao đổi học thuật và bảo vệ chất lượng hệ thống; phân loại phản hồi minh bạch (`[NIT]`, `[SUGGESTION]`, `[BLOCKER]`) và loại bỏ hoàn toàn các tranh cãi vô bổ về cú pháp đã được tự động hóa.
- **Nắm vững khung phân tích đánh đổi (Trade-off Analysis Framework)**: Nằm lòng triết lý *"Không có giải pháp hoàn hảo, chỉ có sự đánh đổi phù hợp nhất"*; biết cách cân bằng giữa Tốc độ phát triển (Time-to-market), Độ phức tạp kiến trúc, Chi phí hạ tầng và Tính khả dụng.
- **Phát triển năng lực Dẫn dắt Kỹ thuật (Technical Leadership) & Mentoring**: Dẫn dắt đồng đội bằng uy tín chuyên môn và sự thấu cảm (Lead by Influence); tổ chức phân tích sự cố không chỉ trích (Blameless Post-mortem) để xây dựng văn hóa kỹ thuật lành mạnh, bền vững.

---

## 🔁 So sánh với C# / ASP.NET

Văn hóa kỹ thuật và quy trình quản trị dự án giữa các doanh nghiệp truyền thống (thường sử dụng C# / .NET) và các tổ chức công nghệ linh hoạt (thường sử dụng Python / FastAPI) có những điểm khác biệt đáng lưu ý:

| Khía cạnh Kỹ năng | Môi trường Doanh nghiệp C# / .NET | Môi trường Linh hoạt Python / FastAPI |
|---|---|---|
| **Quy trình Quản trị Thay đổi** | Thường qua nhiều tầng phê duyệt: Architecture Review Board (ARB), Change Advisory Board (CAB) với tài liệu Solution Architecture Document (SAD) dày đặc. | Nhẹ nhàng và linh hoạt hơn: Sử dụng quy trình **RFC (Request for Comments)** và lưu trữ các tệp **ADR (Markdown)** trực tiếp trong Git repository. |
| **Văn hóa Thực thi** | Chú trọng tính tuân thủ tiêu chuẩn doanh nghiệp (Enterprise Standards), mô hình quản trị theo quy tắc chặt chẽ (Top-down Governance). | Chú trọng tính tự chủ và trách nhiệm toàn diện (Autonomy & Full Ownership: "You build it, you run it"). |
| **Phong cách Code Review** | Thường dựa vào các công cụ tĩnh khắt khe của Visual Studio / SonarQube Enterprise, quy định nghiêm ngặt về phân tầng và mẫu thiết kế. | Tự động hóa hoàn toàn style check qua `ruff` trong CI; Senior tập trung 100% thời gian review vào tính đúng đắn của logic nghiệp vụ, bảo mật, và điểm nghẽn hiệu năng. |
| **Đánh giá Đánh đổi Kỹ thuật** | Thường ưu tiên sự đồng nhất trong hệ sinh thái Microsoft (Azure, SQL Server, .NET Core) để giảm thiểu rủi ro tích hợp. | Sẵn sàng kết hợp các công cụ chuyên biệt tốt nhất (Best-of-Breed: PostgreSQL, Redis, Kafka, ClickHouse, Rust extensions). |

---

## 📖 Lý thuyết

### 1. Tư duy Kỹ sư Cấp cao (The Senior Mindset)

Sự khác biệt lớn nhất giữa một Middle Engineer giỏi và một Senior Engineer thực thụ không nằm ở số lượng thư viện họ thuộc lòng, mà nằm ở **cách họ tiếp cận bài toán**:

```text
┌─────────────────────────────────┬─────────────────────────────────┐
│     TƯ DUY JUNIOR / MIDDLE      │          TƯ DUY SENIOR          │
├─────────────────────────────────┼─────────────────────────────────┤
│ "Công nghệ này mới và ngầu quá, │ "Công nghệ này giải quyết vấn   │
│ mình phải áp dụng vào dự án!"   │ đề gì của doanh nghiệp? Chi phí │
│ (Resume-Driven Development)     │ vận hành và rủi ro ra sao?"     │
├─────────────────────────────────┼─────────────────────────────────┤
│ Cố gắng xây dựng hệ thống hoàn  │ Tuân thủ nguyên lý KISS & YAGNI:│
│ hảo, hỗ trợ scale 10 triệu users│ Giải pháp tối giản đáp ứng đúng │
│ dù hiện tại mới có 1,000 users. │ quy mô hiện tại và dễ mở rộng.  │
├─────────────────────────────────┼─────────────────────────────────┤
│ Coi Code Review là nơi thể hiện │ Coi Code Review là nơi san sẻ tri│
│ cái tôi và bắt bẻ đồng nghiệp.  │ thức và bảo đảm tính bền vững.  │
├─────────────────────────────────┼─────────────────────────────────┤
│ Im lặng ôm đồm mọi việc phức tạp│ Chủ động hướng dẫn, trao quyền  │
│ vì sợ người khác làm hỏng.      │ và nâng đỡ thế hệ kế cận.       │
└─────────────────────────────────┴─────────────────────────────────┘
```

#### Nguyên tắc Thực dụng (Pragmatism)
Kỹ sư Senior hiểu rằng: **Code tốt nhất là dòng code không cần phải viết**. Nếu một bài toán có thể giải quyết bằng cách thay đổi quy trình nghiệp vụ, tận dụng tính năng có sẵn của cơ sở dữ liệu, hoặc tích hợp một dịch vụ SaaS uy tín với chi phí hợp lý, Senior sẽ không bao giờ tốn 2 tháng để tự viết lại một "bánh xe bò" mới trong codebase.

---

### 2. Soạn thảo Tài liệu Kỹ thuật: RFC & ADR

Khi một quyết định kỹ thuật có tầm ảnh hưởng lớn tới toàn hệ thống, nó không bao giờ được phép đưa ra chỉ qua vài tin nhắn chat thoáng qua.

#### Architecture Decision Records (ADR)
ADR là một văn bản ngắn gọn (thường dưới 2 trang Markdown), được lưu trực tiếp trong thư mục `docs/adr/` của repository để lưu lại: *Tại sao chúng ta lại quyết định làm như vậy?*.

Cấu trúc chuẩn mực của một ADR (MADR Format):
1. **Title**: Định danh quyết định (ví dụ: `ADR-004: Sử dụng Redis làm Caching và Distributed Lock`).
2. **Status**: Trạng thái (`PROPOSED`, `ACCEPTED`, `DEPRECATED`, `SUPERSEDED`).
3. **Context**: Bối cảnh thực tế và vấn đề cần giải quyết.
4. **Decision**: Quyết định kỹ thuật được chọn.
5. **Consequences**: Hệ quả sau quyết định: Những điểm tích cực (Pros) và những gánh nặng kỹ thuật phải chấp nhận đánh đổi (Cons).

#### Request for Comments (RFC)
RFC là bản đề xuất chi tiết được gửi cho toàn bộ đội ngũ kỹ thuật thảo luận **trước khi** tiến hành triển khai một tính năng hoặc thay đổi kiến trúc lớn:
- **Problem Statement**: Mô tả nỗi đau hiện tại kèm số liệu đo đạc cụ thể.
- **Proposed Solution**: Thiết kế chi tiết (API contracts, database schema, sequence diagram).
- **Alternatives Considered**: Các giải pháp đã được cân nhắc nhưng bị loại bỏ và lý do vì sao.
- **Security, Performance & Operational Impact**: Đánh giá tác động tới an ninh, hiệu năng và quy trình trực vận hành (On-call).
- **Rollout & Rollback Plan**: Kế hoạch triển khai từng bước và phương án rút lui an toàn nếu có sự cố.

---

### 3. Nghệ thuật Code Review Đa chiều

Code Review là tuyến phòng thủ quan trọng cuối cùng trước khi code đi vào môi trường Production.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        THÁP ƯU TIÊN CODE REVIEW                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. TÍNH ĐÚNG ĐẮN VỀ NGHIỆP VỤ & TOÀN VẸN DỮ LIỆU (Business Logic)      │
│ 2. LỖ HỔNG BẢO MẬT & PHÂN QUYỀN (OWASP Top 10, BOLA, Mass Assignment)   │
│ 3. HIỆU NĂNG & ĐỘ PHỨC TẠP (N+1 queries, Memory leak, Race condition)  │
│ 4. KHẢ NĂNG KIỂM THỬ (Unit / Integration Tests có bao phủ edge cases?) │
│ 5. THIẾT KẾ & ĐẶT TÊN (Clean Architecture, Naming conventions)         │
│ ────────────────────────────────────────────────────────────────────── │
│ [ĐÃ TỰ ĐỘNG HÓA QUA CI: Ruff, Black, Flake8, Mypy - KHÔNG REVIEW BẰNG TAY]
└────────────────────────────────────────────────────────────────────────┘
```

#### Tiêu chuẩn Gắn nhãn Phản hồi (Conventional Comments)
Để tránh gây hiểu lầm hoặc tạo cảm giác nặng nề cho người nhận review, hãy sử dụng các tiền tố rõ ràng:
- **`[BLOCKER]`**: Lỗi nghiêm trọng ảnh hưởng đến logic, an ninh hoặc hiệu năng. Bắt buộc phải sửa trước khi merge.
  - *Ví dụ*: `"[BLOCKER]: Endpoint này đang nhận trực tiếp user_id từ query param mà không kiểm tra quyền sở hữu. Cần bổ sung guard BOLA."`
- **`[SUGGESTION]`**: Ý tưởng cải tiến, không bắt buộc nhưng khuyên dùng để code thanh thoát hơn.
  - *Ví dụ*: `"[SUGGESTION]: Có thể dùng list comprehension ở đây thay cho vòng lặp for để code gọn và nhanh hơn."`
- **`[QUESTION]`**: Thắc mắc để hiểu rõ hơn về ý đồ của tác giả.
  - *Ví dụ*: `"[QUESTION]: Vì sao ở đây chúng ta lại chọn timeout là 30s thay vì 5s tiêu chuẩn?"`
- **`[NIT]` (Nitpick)**: Góp ý rất nhỏ mang tính sở thích cá nhân, tác giả có thể sửa hoặc bỏ qua tùy ý.
  - *Ví dụ*: `"[NIT]: Tên biến total_sum hơi lặp từ, có thể đổi thành total là đủ rõ nghĩa."`

---

### 4. Khung Đánh giá Đánh đổi Kỹ thuật (Trade-off Matrix)

Khi đứng trước hai hay nhiều lựa chọn kiến trúc, một Senior không bao giờ tuyên bố: *"Công nghệ A xịn hơn công nghệ B"*. Thay vào đó, Senior lập bảng phân tích các yếu tố đánh đổi:

```text
               (Tốc độ phát triển: Time-to-Market)
                                ▲
                                │   ★ ĐIỂM CÂN BẰNG TỐI ƯU
                                │      (Pragmatic Engineering)
                                │
(Độ phức tạp thấp / ◄───────────┼───────────► (Khả năng mở rộng
 Chi phí vận hành rẻ)           │              siêu cấp: Scale)
                                │
                                ▼
                     (Sự hoàn hảo kiến trúc)
```

| Tiêu chí | Lựa chọn 1: Giữ nguyên Monolith + PostgreSQL | Lựa chọn 2: Tách Microservices + Kafka |
|---|---|---|
| **Tốc độ ra mắt tính năng** | **Rất nhanh**: Đội ngũ chỉ cần tập trung vào 1 codebase. | Chậm: Tốn thời gian định nghĩa contracts, RPC, CI/CD riêng. |
| **Độ phức tạp vận hành** | **Rất thấp**: 1 cụm DB, backup đơn giản, dễ debug. | Rất cao: Cần k8s, distributed tracing, service mesh. |
| **Tính nhất quán dữ liệu** | **Mạnh mẽ (ACID)**: Dễ dàng dùng giao dịch CSDL. | Yếu (Eventual Consistency): Phải dùng Outbox, Saga. |
| **Khả năng mở rộng nhóm** | Bị giới hạn khi team vượt quá 25–30 lập trình viên. | **Rất cao**: Các nhóm tự chủ phát triển độc lập. |
| **Kết luận của Senior** | **Chọn Lựa chọn 1** cho giai đoạn hiện tại (10k DAU). Khi nào lưu lượng tăng gấp 20 lần và team mở rộng sẽ đánh giá lại. |

---

### 5. Văn hóa Phân tích Sự cố Không Chỉ trích (Blameless Post-Mortem)

Khi môi trường Production gặp sự cố sập nguồn (Outage), phản xạ của một tổ chức non trẻ là tìm ra **"Ai là người đã làm hỏng hệ thống?"** để quy trách nhiệm. Đây là con đường ngắn nhất dẫn đến việc nhân viên che giấu lỗi lầm và sợ hãi không dám đổi mới.

Một Senior Engineer hiểu rằng: **Con người luôn luôn có thể mắc sai lầm**. Nếu một lỗi của lập trình viên có thể làm sập toàn bộ hệ thống production, thì **lỗi nằm ở quy trình, ở bộ công cụ kiểm thử tự động, và ở kiến trúc hệ thống thiếu lá chắn bảo vệ**, chứ không phải do cá nhân đó!

#### Cấu trúc buổi họp Blameless Post-Mortem
1. **Dòng thời gian sự cố (Timeline)**: Ghi lại chính xác từng mốc giờ (Sự cố bắt đầu lúc nào, hệ thống cảnh báo lúc mấy giờ, rollback hoàn tất khi nào).
2. **Nguyên nhân gốc rễ (Root Cause Analysis - 5 Whys)**: Sử dụng phương pháp 5 câu hỏi "Tại sao" để đào sâu vào gốc rễ quy trình.
3. **Bài học rút ra (Lessons Learned)**: Điều gì đã hoạt động tốt? Điều gì chưa tốt? Chúng ta đã gặp may ở điểm nào?
4. **Hành động khắc phục (Action Items)**: Các đầu việc cụ thể có người phụ trách (Owner) và thời hạn hoàn thành (Deadline) rõ ràng nhằm ngăn chặn sự cố tương tự tái diễn (ví dụ: Bổ sung circuit breaker, thêm test case CI, cấu hình thêm metric alert).

---

### 6. Quản trị & Trả nợ Kỹ thuật (Technical Debt Management)

Mọi hệ thống phần mềm sống đều tích lũy Nợ kỹ thuật (Technical Debt). Tương tự như vay nợ tài chính, một khoản nợ kỹ thuật có chủ đích giúp bạn release sản phẩm nhanh hơn để chiếm lĩnh thị trường, nhưng bạn bắt buộc phải trả lãi suất (thời gian maintain code lâu hơn, bug xuất hiện thường xuyên hơn, chi phí onboarding nhân viên mới tăng cao).

#### 6.1 Ma trận Nợ Kỹ thuật (Martin Fowler's Tech Debt Quadrant)
| Phân loại | Thận trọng (Prudent) | Cẩu thả (Reckless) |
|---|---|---|
| **Cố ý (Deliberate)** | *"Chúng ta phải ship tính năng này ngay hôm nay, và đã tạo sẵn 2 backlog tickets để refactor lại tầng Data Layer trong sprint tới."* $\to$ **Nợ tốt, có kiểm soát.** | *"Không có thời gian viết test hay thiết kế kiến trúc đâu, cứ copy-paste code chạy được là được!"* $\to$ **Tội đồ công nghệ.** |
| **Vô tình (Inadvertent)** | *"Bây giờ khi hệ thống đạt 100k người dùng, chúng ta mới nhận ra cấu trúc database trước đây chưa tối ưu cho read-heavy."* $\to$ **Sự tiến hóa tự nhiên của phần mềm.** | *"Nhóm không biết design pattern là gì nên viết 1 file route dài 3,000 dòng code."* $\to$ **Thiếu năng lực chuyên môn.** |

#### 6.2 Chiến lược đàm phán với Product Owner & Stakeholders
1. **Quy tắc ngân sách 20% (The 20% Budget Rule)**: Luôn dành cố định 15%–20% capacity của mỗi sprint cho các đầu việc refactor, nâng cấp thư viện, viết thêm test, và tối ưu hiệu năng.
2. **Nói bằng ngôn ngữ Kinh doanh (Business Language)**: Đừng bao giờ nói *"Tôi muốn refactor code cho đẹp"*. Hãy nói: *"Nếu chúng ta dành 3 ngày để tách nhỏ module này, tốc độ phát triển các tính năng thanh toán tiếp theo sẽ tăng 30% và giảm 80% rủi ro lỗi giao dịch trên production"*.
3. **Định kỳ dọn dẹp (Boy Scout Rule)**: Mỗi lần sửa một file, hãy để lại file đó sạch đẹp và gọn gàng hơn một chút so với lúc bạn mở nó ra.

---

### 7. Nghệ thuật Kèm cặp & Phát triển Đội ngũ (Mentoring & Team Enablement)

Thước đo giá trị của một Senior Engineer không nằm ở số dòng code bạn viết, mà nằm ở **năng lực của cả đội ngũ mà bạn đã nâng tầm (Multiplying Effect)**.

#### 7.1 Nguyên tắc Kèm cặp Hiệu quả:
- **Dẫn dắt bằng Tầm ảnh hưởng (Lead by Influence, not Authority)**: Thuyết phục đồng nghiệp bằng dữ liệu, benchmark, tài liệu ADR rõ ràng và sự kiên nhẫn, thay vì áp đặt quyền lực cấp bậc.
- **Pair Programming có mục đích (Driver - Navigator)**:
  - Khi pair với Junior/Middle, để họ cầm bàn phím (Driver - người gõ code), còn bạn đóng vai trò định hướng kiến trúc (Navigator - người quan sát và đặt câu hỏi gợi mở).
  - Đừng bao giờ giật lấy bàn phím để gõ hộ! Hãy để họ tự trải nghiệm và tư duy giải quyết vấn đề.
- **Trao quyền kèm Mạng an toàn (Empowerment with Safety Nets)**: Giao các bài toán thiết kế khó cho Middle Developer, nhưng thiết lập sẵn các chốt chặn an toàn: CI linting, pytest automated coverage, staging environment, và code review đa chiều.
- **Hỗ trợ đồng nghiệp C# / .NET chuyển ngữ sang Python**:
  - Tôn trọng và tận dụng nền tảng OOP và tư duy thiết kế bài bản của họ từ hệ sinh thái .NET.
  - Hướng dẫn họ gỡ bỏ các nghi thức dư thừa (như tạo `interface` cho mọi class dù chỉ có 1 implementation), chuyển sang sử dụng `typing.Protocol` (Duck Typing có type checking), và cảnh báo các cạm bẫy đặc thù của Python (GIL, mutable default arguments, dynamic binding).

---

## 💻 Ví dụ thực hành

### 1. Bản mẫu ADR hoàn chỉnh (Architecture Decision Record)

Dưới đây là một tệp tài liệu ADR mẫu lưu tại `docs/adr/0005-use-arq-for-distributed-tasks.md`:

```markdown
# ADR 0005: Chuyển đổi từ FastAPI BackgroundTasks sang Distributed Queue với ARQ

* **Trạng thái**: ACCEPTED
* **Người đề xuất**: Senior Backend Lead
* **Ngày phê duyệt**: 2026-10-22
* **Người tham gia review**: Backend Team, DevOps Lead

## 1. Bối cảnh (Context)
Hiện tại, hệ thống TaskFlow đang sử dụng `fastapi.BackgroundTasks` để thực hiện gửi email chào mừng và xuất báo cáo CSV. Khi lưu lượng người dùng tăng cao:
- Các tác vụ nặng (tạo file zip báo cáo) ngốn CPU và RAM ngay trong chính tiến trình FastAPI, làm nghẽn Event Loop và tăng p99 latency của các API endpoints.
- Khi Kubernetes thực hiện rolling update hoặc scale down Pods, các background tasks đang chạy dở bị huỷ ngang giữa chừng mà không có cơ chế retry hay lưu vết, gây mất mát dữ liệu của người dùng.

## 2. Quyết định (Decision)
Chúng tôi quyết định tách toàn bộ các tác vụ ngầm ra khỏi tiến trình API chính và triển khai hệ thống hàng đợi phân tán sử dụng **ARQ** kết hợp với **Redis**.

Lý do chọn ARQ thay vì Celery:
- ARQ được thiết kế thuần `asyncio` hiện đại, tương thích hoàn hảo với cú pháp async/await của Python 3.12+ và FastAPI.
- Codebase cực kỳ nhẹ và đơn giản, không mang gánh nặng lịch sử như Celery.
- Hạ tầng hiện tại của chúng tôi đã có sẵn cụm Redis Cluster được vận hành ổn định.

## 3. Hệ quả (Consequences)

### Tích cực (Pros):
- **Bảo vệ API Server**: Giải phóng hoàn toàn tiến trình FastAPI khỏi các tác vụ I/O và CPU nặng.
- **Khả năng tự phục hồi**: ARQ hỗ trợ retry tự động với Exponential Backoff khi tác vụ gặp sự cố mạng tạm thời.
- **Mở rộng độc lập**: Có thể scale riêng số lượng Worker Pods tùy theo độ dài của hàng đợi Redis mà không cần scale API Pods.

### Tiêu cực & Đánh đổi (Cons):
- **Tăng độ phức tạp hạ tầng**: Cần duy trì thêm deployment riêng cho cụm ARQ Workers trên Kubernetes.
- **Giám sát**: Cần cấu hình thêm Prometheus Exporter để theo dõi độ dài hàng đợi (Queue Length) và tỷ lệ thất bại của jobs.
```

---

### 2. Kịch bản Code Review Đa chiều Chuẩn mực

Đoạn hội thoại mẫu minh họa cách một Senior Engineer review Pull Request một cách chuyên nghiệp, khéo léo và mang tính xây dựng cao:

```markdown
### Reviewer: @senior_dev
Chào @junior_dev, cảm ơn em đã hoàn thiện tính năng xuất báo cáo danh sách công việc! Logic tổng thể nhìn rất rõ ràng. Anh có một vài góp ý để hoàn thiện PR này trước khi lên Production nhé:

---

**File: `src/services/report_service.py` (Line 45)**
```python
tasks = await session.scalars(select(TaskModel))
for task in tasks:
    owner_email = task.owner.email  # <--- Dòng này
```
**`[BLOCKER]`**: Ở đây em đang lặp qua danh sách tasks và truy cập vào `task.owner.email`. Do quan hệ `owner` chưa được load sẵn, điều này sẽ kích hoạt lỗi **N+1 queries** (nếu dùng lazy load) hoặc gây lỗi `DetachedInstanceError` trong SQLAlchemy Async. 
👉 **Khuyến nghị**: Hãy bổ sung `options(joinedload(TaskModel.owner))` vào câu lệnh `select()` ban đầu để nạp dữ liệu người dùng trong một câu query duy nhất nhé.

---

**File: `src/routers/reports.py` (Line 28)**
```python
@router.post("/export")
async def export_report(user_id: str):
    ...
```
**`[BLOCKER]`**: Endpoint nhận `user_id` trực tiếp từ query parameter mà không kiểm tra xem nó có khớp với người dùng đang đăng nhập hay không. Điều này tạo ra lỗ hổng **BOLA (Broken Object Level Authorization)**, cho phép bất kỳ ai cũng có thể xuất báo cáo bí mật của người khác.
👉 **Khuyến nghị**: Hãy thay thế bằng `current_user: Annotated[User, Depends(get_current_user)]` và chỉ cho phép xuất dữ liệu của chính `current_user.id` (trừ khi user có vai trò `ADMIN`).

---

**File: `src/utils/exporter.py` (Line 80)**
**`[SUGGESTION]`**: Đoạn ghi file tạm thời này em có thể dùng `tempfile.NamedTemporaryFile` với context manager `with` để hệ điều hành tự động dọn dẹp file rác nếu quá trình xuất file bị lỗi giữa chừng nhé.

---

**File: `src/routers/reports.py` (Line 35)**
**`[NIT]`**: Tên biến `data_list` có thể đổi thành `report_items` cho sát nghĩa nghiệp vụ hơn một chút.
```

---

### 3. Bộ Quy tắc Hướng dẫn Kỹ thuật (Technical Guidelines)

Một đoạn mã Python mẫu thể hiện cách Senior thiết kế cấu trúc một Exception Hierarchy chuẩn mực cho toàn đội ngũ tuân theo:

```python
from __future__ import annotations

from typing import Any


class DomainException(Exception):
    """Lớp gốc cho toàn bộ các ngoại lệ nghiệp vụ của hệ thống."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class EntityNotFoundException(DomainException):
    """Ném ra khi không tìm thấy tài nguyên theo định danh."""

    def __init__(self, entity_name: str, entity_id: str | int) -> None:
        super().__init__(
            message=f"Không tìm thấy thực thể {entity_name} với ID: {entity_id}",
            context={"entity": entity_name, "id": entity_id},
        )


class BusinessRuleViolationException(DomainException):
    """Ném ra khi hành động vi phạm quy tắc ràng buộc của miền nghiệp vụ."""

    def __init__(self, rule_name: str, reason: str) -> None:
        super().__init__(
            message=f"Vi phạm quy tắc [{rule_name}]: {reason}",
            context={"rule": rule_name, "reason": reason},
        )


class UnauthorizedResourceAccessException(DomainException):
    """Ném ra khi người dùng cố tình truy cập tài nguyên không thuộc sở hữu (BOLA)."""

    def __init__(self, resource_type: str, resource_id: str | int) -> None:
        super().__init__(
            message="Bạn không có quyền thao tác trên tài nguyên này.",
            context={"resource": resource_type, "id": resource_id},
        )
```

---

## ⚠️ Lỗi thường gặp

### 1. Bệnh sùng bái công nghệ (Resume-Driven Development - RDD)
Lập trình viên muốn thử nghiệm một công nghệ mới (ví dụ: gRPC, Rust extension, Event Sourcing, Kubernetes Keda) chỉ để làm đẹp hồ sơ cá nhân (CV), bất chấp việc hệ thống hiện tại chỉ là một ứng dụng CRUD nội bộ đơn giản phục vụ 50 nhân viên. Senior luôn đặt lợi ích lâu dài của doanh nghiệp và sự đơn giản của hệ thống lên hàng đầu.

### 2. Trở thành "Kẻ gác cổng độc hại" (Toxic Gatekeeper) trong Code Review
Sử dụng quyền duyệt code để bắt bẻ sở thích cá nhân, dùng từ ngữ mang tính chỉ trích xúc phạm ("Code như thế này mà cũng viết được à?"), hoặc trì hoãn không duyệt PR hàng tuần liền làm tắc nghẽn công việc của đồng đội. Code Review là văn hóa đồng hành, không phải kỳ thi sát hạch quyền lực.

### 3. Đưa ra các quyết định kiến trúc âm thầm (Silent Architectural Changes)
Tự ý thay đổi cấu trúc thư mục, đổi thư viện ORM, hoặc áp dụng mẫu thiết kế mới vào dự án mà không có thảo luận, không viết RFC, và không thông báo cho đồng đội. Khiến các thành viên khác trong nhóm bị bỡ ngỡ, xung đột merge code triền miên và mất đi tính nhất quán của dự án.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Soạn thảo ADR cho việc lựa chọn cơ chế Realtime
Hãy đóng vai trò Senior Backend Architect và soạn thảo một bản ADR hoàn chỉnh theo định dạng Markdown:
- **Đề tài**: Lựa chọn giữa **WebSocket** và **Server-Sent Events (SSE)** cho tính năng nhận thông báo trạng thái cập nhật công việc trong TaskFlow.
- Yêu cầu: Phân tích bối cảnh, quyết định lựa chọn, liệt kê tối thiểu 3 ưu điểm và 2 nhược điểm/đánh đổi của giải pháp được chọn.

<details>
<summary>💡 Gợi ý</summary>

```markdown
# ADR 0006: Sử dụng Server-Sent Events (SSE) cho hệ thống thông báo trạng thái TaskFlow

* **Trạng thái**: ACCEPTED
* **Người đề xuất**: Senior Architect
* **Ngày**: 2026-10-22

## 1. Bối cảnh
Người dùng cần nhận cập nhật trạng thái công việc (to-do -> in-progress -> done) ngay lập tức khi thành viên khác chỉnh sửa. Lưu lượng là một chiều: Server gửi sự kiện đẩy về cho Client (Browser/Mobile).

## 2. Quyết định
Chọn **Server-Sent Events (SSE)** thay vì WebSocket.
Lý do:
- Luồng dữ liệu hoàn toàn là 1 chiều (Server-to-Client).
- SSE hoạt động trên giao thức HTTP tiêu chuẩn, không gặp vấn đề với firewall, proxy hoặc load balancer HTTP/2.
- Trình duyệt tích hợp sẵn cơ chế tự động kết nối lại (`EventSource` reconnection) và quản lý ID sự kiện cuối cùng (`Last-Event-ID`).
- Cài đặt backend bằng `StreamingResponse` trong FastAPI cực kỳ nhẹ nhàng, không cần duy trì kết nối TCP 2 chiều phức tạp.

## 3. Hệ quả
- **Ưu điểm**: Triển khai nhanh, tiết kiệm tài nguyên kết nối, tương thích 100% với hạ tầng Nginx/Cloudflare hiện có.
- **Đánh đổi**: Nếu tương lai cần tính năng chat 2 chiều giữa các thành viên, chúng ta sẽ cần bổ sung thêm WebSocket cho module chat.
```
</details>

---

### Bài tập 2: Xây dựng Kịch bản Họp Blameless Post-Mortem
Xây dựng một bản kế hoạch điều phối cuộc họp Post-Mortem cho sự cố: *"Cơ sở dữ liệu Production bị treo 30 phút vào lúc 14:00 do một câu lệnh truy vấn phân trang không đánh index lọt vào sản phẩm"*:
1. Quy tắc mở đầu cuộc họp để xóa bỏ tâm lý sợ hãi của kỹ sư gây lỗi.
2. Áp dụng kỹ thuật 5 Whys tìm nguyên nhân gốc rễ (Root Cause).
3. Xác định ít nhất 3 Action Items phòng ngừa tái diễn.

<details>
<summary>💡 Gợi ý</summary>

```markdown
# Kịch bản Điều phối Blameless Post-Mortem

## 1. Tuyên bố Mở đầu (The Prime Directive)
"Bất kể chúng ta phát hiện ra điều gì hôm nay, chúng ta thực sự thấu hiểu và tin tưởng rằng tất cả mọi người đều đã làm tốt nhất công việc của mình trong khả năng và điều kiện thông tin họ có tại thời điểm đó."

## 2. Kỹ thuật 5 Whys
- Tại sao DB bị treo? -> Vì có nhiều câu query quét toàn bộ bảng (Full Table Scan) chiếm 100% CPU.
- Tại sao có query Full Table Scan? -> Vì tính năng tìm kiếm mới được release không có Index trên cột `status`.
- Tại sao không có Index? -> Vì lập trình viên kiểm thử trên môi trường dev (vốn chỉ có 20 bản ghi) nên không nhận ra câu query bị chậm.
- Tại sao PR đó lại được duyệt? -> Vì Code Review chỉ kiểm tra syntax và logic trả về, không có quy trình kiểm tra câu query SQL thực tế sinh ra bởi ORM.
- Tại sao hệ thống cảnh báo không báo sớm? -> Vì ngưỡng cảnh báo CPU DB đang đặt quá cao (95% trong 15 phút).

## 3. Action Items:
1. [DevOps]: Hạ ngưỡng cảnh báo CPU Database xuống 80% trong 3 phút (Deadline: Thứ 6).
2. [Backend Lead]: Bổ sung công cụ phân tích truy vấn `EXPLAIN ANALYZE` vào quy trình review các tính năng tìm kiếm (Deadline: Tuần tới).
3. [QA]: Thiết lập môi trường Staging với dữ liệu mô phỏng quy mô lớn (1 triệu dòng) để test tải trước khi release (Deadline: Tháng 11).
```
</details>

---

### Bài tập 3: Thiết kế Ma trận Quyết định Lựa chọn Công nghệ (Trade-off Matrix)
Lập bảng ma trận đánh giá cho việc lưu trữ Session / Cache giữa 3 giải pháp: In-Memory (Dict trong tiến trình), Redis Cluster, và Memcached. Đưa ra điểm số từ 1 đến 5 theo các tiêu chí: Hiệu năng, Độ phức tạp, Tính phân tán, Khả năng chịu lỗi và đưa ra đề xuất cuối cùng.

<details>
<summary>💡 Gợi ý</summary>

```markdown
| Tiêu chí (Trọng số) | Python In-Memory Dict | Memcached | Redis Cluster |
|---|:---:|:---:|:---:|
| **Độ trễ truy xuất (x2)** | 5 (0.01ms - Cực đại) | 4 (0.5ms) | 4 (0.6ms) |
| **Tính nhất quán đa Pods (x3)** | 1 (Mỗi pod 1 kiểu) | 5 (Chia sẻ chung) | 5 (Chia sẻ chung) |
| **Tính đa dạng cấu trúc dữ liệu (x2)** | 5 (Mọi kiểu Python) | 2 (Chỉ lưu Key-Value) | 5 (List, Set, Hash, ZSet) |
| **Khả năng lưu trữ bền vững & HA (x2)** | 1 (Mất khi restart) | 1 (Mất khi restart) | 5 (RDB, AOF, Sentinel) |
| **Độ phức tạp vận hành (x1)** | 5 (Không cần cài đặt) | 4 (Rất đơn giản) | 3 (Cần cấu hình quản trị) |
| **TỔNG ĐIỂM CÓ TRỌNG SỐ** | 30 | 38 | **46** |

👉 **Quyết định**: Chọn **Redis Cluster** vì hệ thống của chúng ta triển khai đa Pods trên Kubernetes và cần các cấu trúc dữ liệu phong phú (ZSet cho Rate Limiting, Hash cho Session).
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi hiểu rõ sự khác biệt giữa tư duy kỹ thuật thuần túy và tư duy giải quyết bài toán kinh doanh của Senior.
- [ ] Tôi biết cách viết một bản ADR chuẩn MADR format để lưu lại các quyết định kiến trúc quan trọng trong repository.
- [ ] Tôi biết cách soạn thảo tài liệu RFC để đề xuất các thay đổi kiến trúc lớn và lắng nghe phản hồi từ đội ngũ.
- [ ] Tôi thành thạo quy tắc gắn nhãn Code Review (`[BLOCKER]`, `[SUGGESTION]`, `[QUESTION]`, `[NIT]`) và tập trung vào các vấn đề cốt lõi.
- [ ] Tôi biết cách áp dụng khung phân tích đánh đổi (Trade-off Analysis) để đưa ra các lựa chọn công nghệ thực dụng.
- [ ] Tôi thấu hiểu giá trị của văn hóa Blameless Post-mortem và biết cách điều phối phân tích sự cố production qua kỹ thuật 5 Whys.

---

## 📚 Đọc thêm

- [The Pragmatic Programmer - David Thomas & Andrew Hunt](https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/)
- [Staff Engineer: Leadership beyond the management track - Will Larson](https://staffeng.com/)
- [Architecture Decision Records (MADR Template)](https://adr.github.io/madr/)
- [Google SRE: Postmortem Culture - Learning from Failure](https://sre.google/sre-book/postmortem-culture/)
- [Tiếp theo: Hoàn thành đồ án tốt nghiệp Milestone M3 – Scalable API](../project/m3-scalable-api.md)

<!-- nav:bottom -->
---

[⬅️ System design & scaling](./11-system-design-scaling.md) | [📚 Mục lục Senior](./README.md) | [M3 – Scalable API ➡️](../project/m3-scalable-api.md)
<!-- /nav:bottom -->
