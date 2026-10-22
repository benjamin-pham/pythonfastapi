<!-- nav:top -->
[🏠 Home](../README.md) › [Middle](./README.md) › Bài 12
<!-- /nav:top -->

# CI với GitHub Actions

> ⏱️ Thời lượng: ~3.5 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 11: Docker & docker-compose](./11-docker-compose.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Xây dựng một quy trình **Tích hợp liên tục (Continuous Integration - CI)** tự động hóa toàn diện cho dự án FastAPI trên nền tảng **GitHub Actions**.
- Tối ưu hóa tốc độ thực thi pipeline xuống dưới 60 giây bằng cách ứng dụng **`astral-sh/setup-uv@v5`** kết hợp cơ chế lưu trữ bộ nhớ đệm tự động (**Dependency Caching** dựa trên `uv.lock`).
- Khởi tạo và liên kết **PostgreSQL Service Container** trực tiếp trong môi trường GitHub Actions Runner với cấu hình kiểm tra sức khỏe (**Healthcheck**) chuẩn mực.
- Thiết lập hàng rào chất lượng mã nguồn đa tầng (**Quality Gates**): Kiểm tra lỗi logic và cú pháp bằng **`ruff check`**, kiểm tra định dạng bằng **`ruff format --check`**, kiểm tra an toàn kiểu tĩnh ở mức tối đa bằng **`mypy --strict`**.
- Tự động hóa kiểm thử tính tương thích của lược đồ cơ sở dữ liệu thực tế bằng lệnh **`alembic upgrade head`** trên cơ sở dữ liệu thật.
- Đo lường và kiểm soát độ bao phủ mã nguồn (**Test Coverage**) với `pytest-cov`, thiết lập ngưỡng tối thiểu để ngăn chặn việc merge các PR thiếu bài kiểm thử.

---

## 🔁 So sánh với C# / ASP.NET

Trong các dự án doanh nghiệp .NET, việc thiết lập CI/CD qua GitHub Actions hoặc Azure DevOps Pipelines với `dotnet restore`, `dotnet format`, `dotnet build`, và `dotnet test` là quy chuẩn bắt buộc. Dưới đây là bảng đối chiếu chi tiết:

| Bước quy trình CI | ASP.NET Core (.NET 8) | FastAPI (Python 3.12+) |
|---|---|---|
| **Cài đặt môi trường SDK** | `actions/setup-dotnet@v4` | `actions/setup-python@v5` kết hợp `astral-sh/setup-uv@v5` |
| **Khôi phục gói & Caching** | `dotnet restore` lưu cache vào `~/.nuget/packages` | `uv sync --frozen` với `enable-cache: true` |
| **Kiểm tra Style & Linter** | `dotnet format --verify-no-changes` hoặc Roslyn Analyzers | `ruff check` và `ruff format --check` |
| **Kiểm tra kiểu dữ liệu tĩnh** | Trình biên dịch `csc` (tự động kiểm tra kiểu tĩnh lúc build) | `mypy --strict` (Static Type Checker cho Python) |
| **Database Container cho Test** | Docker Service Container: `postgres:17` | GitHub Actions Service Container: `postgres:17` |
| **Kiểm thử Migration DB** | `dotnet ef database update` | `alembic upgrade head` |
| **Thực thi Unit/Integration Test** | `dotnet test --collect:"XPlat Code Coverage"` | `pytest --cov=app --cov-fail-under=85` |
| **Chính sách khóa nhánh (Quality Gate)** | GitHub Branch Protection: Require status checks to pass | GitHub Branch Protection: Require status checks to pass |

---

## 📖 Lý thuyết

### 1. Kiến trúc một Pipeline CI chuẩn mực

Một đường ống CI chuyên nghiệp phải tuân thủ nguyên lý **"Fail Fast" (Thất bại sớm)**: Những bước nhẹ nhàng, tốn ít tài nguyên và phát hiện lỗi nhanh (Linting, Formatting, Type checking) phải được thực thi trước. Nếu mã nguồn không đạt chuẩn định dạng, pipeline lập tức dừng lại mà không tốn chi phí khởi động Database và chạy test suite.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   LUỒNG PIPELINE CI CHUẨN DOANH NGHIỆP                 │
│                                                                        │
│   [Developer Push / Pull Request]                                      │
│                 │                                                      │
│                 ▼                                                      │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ 1. CODE QUALITY GATE (Siêu tốc: ~5-10s)                       │    │
│   │    - ruff check (Bắt lỗi logic, unused import, security)     │    │
│   │    - ruff format --check (Bảo đảm chuẩn format đồng nhất)    │    │
│   │    - mypy --strict (Bảo đảm an toàn kiểu dữ liệu 100%)       │    │
│   └──────────────────────────────────────────────────────────────┘    │
│                 │ (Pass)                                               │
│                 ▼                                                      │
│   ┌──────────────────────────────────────────────────────────────┐    │
│   │ 2. DATABASE INTEGRATION & TESTS (~20-40s)                    │    │
│   │    - Khởi động PostgreSQL 17 Service Container (pg_isready)  │    │
│   │    - alembic upgrade head (Xác thực toàn vẹn Migration)      │    │
│   │    - pytest --cov=app (Chạy integration tests trên DB thật)  │    │
│   │    - Kiểm tra ngưỡng Coverage: fail nếu dưới 85%             │    │
│   └──────────────────────────────────────────────────────────────┘    │
│                 │ (Pass)                                               │
│                 ▼                                                      │
│      [Xanh rì - Cho phép Merge Pull Request vào main]                  │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. Tăng tốc đột phá với `astral-sh/setup-uv@v5`

Trước khi `uv` ra đời, các bước cài đặt môi trường Python trong CI bằng `pip install` thường tốn từ 45 đến 90 giây cho mỗi lần chạy. 

Khi sử dụng action chính thức **`astral-sh/setup-uv@v5`**:
- `uv` được cài đặt nhị phân cực nhanh viết bằng Rust.
- Tự động tích hợp cơ chế cache của GitHub Actions thông qua cờ `enable-cache: true`.
- Khi `uv.lock` không thay đổi, lệnh `uv sync --frozen` chỉ mất vỏn vẹn **1 đến 2 giây** để hoàn thành việc chuẩn bị môi trường ảo!

### 3. PostgreSQL Service Container trong GitHub Actions

Để chạy Integration Test thực thụ (thay vì mock Database), GitHub Actions hỗ trợ **Service Containers** — các container Docker chạy nền bên cạnh máy ảo runner và cùng chia sẻ mạng localhost:

```yaml
services:
  postgres:
    image: postgres:17-alpine
    env:
      POSTGRES_DB: taskflow_test_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgrespassword
    ports:
      - 5432:5432
    # Cực kỳ quan trọng: Phải kiểm tra pg_isready trước khi runner bắt đầu step tiếp theo
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### 4. Bốn chốt chặn chất lượng (Quality Gates)

1. **`ruff check`**: Thay thế Flake8, isort, pyupgrade, autoflake. Bắt lỗi import thừa, biến chưa dùng, code smell tiềm ẩn.
2. **`ruff format --check`**: Thay thế Black. Đảm bảo mọi lập trình viên trong dự án đều tuân theo một quy tắc xuống dòng, dấu phẩy, khoảng trắng duy nhất mà không mất thời gian tranh cãi trong lúc Review Code.
3. **`mypy --strict`**: Đảm bảo toàn bộ hàm, tham số, biến số đều được định kiểu tường minh, ngăn chặn lỗi kinh điển `AttributeError: 'NoneType' object has no attribute '...'`.
4. **`pytest --cov=app --cov-report=term-missing --cov-fail-under=85`**: Bảo đảm mã nguồn mới luôn có bài kiểm thử đi kèm, ngăn chặn suy giảm chất lượng phần mềm theo thời gian (Regression).

---

## 💻 Ví dụ thực hành

Dưới đây là tệp cấu hình hoàn chỉnh của GitHub Actions Pipeline: `.github/workflows/ci.yml`.

```yaml
name: CI Pipeline

on:
  push:
    branches:
      - main
      - master
  pull_request:
    branches:
      - main
      - master

# Hủy các workflow cũ đang chạy nếu người dùng push commit mới vào cùng PR (tiết kiệm tài nguyên)
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ============================================================================
  # JOB 1: Kiểm tra Linting, Format & Kiểu dữ liệu tĩnh
  # ============================================================================
  code-quality:
    name: Code Quality & Type Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout mã nguồn
        uses: actions/checkout@v4

      - name: Cài đặt uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "latest"
          enable-cache: true

      - name: Cài đặt Python 3.13
        run: uv python install 3.13

      - name: Cài đặt dependencies (bao gồm nhóm dev)
        run: uv sync --frozen

      - name: Kiểm tra Linter với Ruff
        run: uv run ruff check .

      - name: Kiểm tra Code Formatting với Ruff
        run: uv run ruff format --check .

      - name: Kiểm tra Static Type với Mypy
        run: uv run mypy --strict src/app

  # ============================================================================
  # JOB 2: Chạy Database Migration & Integration Test Suite
  # ============================================================================
  integration-tests:
    name: Database Migrations & Pytest
    runs-on: ubuntu-latest
    needs: [code-quality] # Chỉ chạy khi Job 1 đã thành công!

    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_DB: taskflow_test
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U testuser -d taskflow_test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: postgresql+asyncpg://testuser:testpassword@localhost:5432/taskflow_test
      SECRET_KEY: test_secret_key_for_ci_pipeline_only
      ENVIRONMENT: testing

    steps:
      - name: Checkout mã nguồn
        uses: actions/checkout@v4

      - name: Cài đặt uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "latest"
          enable-cache: true

      - name: Cài đặt Python 3.13
        run: uv python install 3.13

      - name: Cài đặt dependencies
        run: uv sync --frozen

      - name: Chạy Database Migrations với Alembic
        run: uv run alembic upgrade head

      - name: Chạy bộ kiểm thử tự động với Pytest & Đo Coverage
        run: >
          uv run pytest
          --cov=app
          --cov-report=term-missing
          --cov-report=xml
          --cov-fail-under=80

      - name: Lưu trữ báo cáo Coverage làm Artifact (Tùy chọn)
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage.xml
```

---

## ⚠️ Lỗi thường gặp

### 1. Quên cờ `--frozen` khi chạy `uv sync` trên CI

**Hiện tượng:** Pipeline CI tự ý cập nhật `uv.lock` hoặc ném ra lỗi xung đột phiên bản mà không khớp với môi trường local của bạn.

❌ **Sai lầm:**
```bash
uv sync  # Có thể tự động giải quyết lại dependency và sửa file lock!
```

✅ **Giải pháp:** Luôn sử dụng cờ `--frozen`:
```bash
uv sync --frozen
```
Cờ `--frozen` đảm bảo `uv` chỉ cài đặt chính xác các phiên bản đã được chốt cứng trong `uv.lock`. Nếu có sự sai lệch giữa `pyproject.toml` và `uv.lock`, pipeline sẽ lập tức báo lỗi đỏ, buộc lập trình viên phải cập nhật lockfile ở máy cục bộ trước khi push lên.

---

### 2. Thiếu cấu hình `options: --health-cmd pg_isready` cho Service Container

Nếu bạn chỉ khai báo `postgres` container mà không cấu hình healthcheck, máy ảo runner sẽ thực thi step kế tiếp ngay khi container vừa được tạo. 
Tuy nhiên, PostgreSQL cần 2 đến 5 giây để khởi tạo database cluster. Khi step `alembic upgrade head` chạy, Postgres vẫn chưa mở cổng 5432, dẫn đến lỗi:
`asyncpg.exceptions.CannotConnectNowError: the database system is starting up` hoặc `ConnectionRefusedError`.

---

### 3. Không commit tệp `uv.lock` vào Git Repository

Nhiều lập trình viên có thói quen đưa các file lock vào `.gitignore`. Đây là một sai lầm chết người đối với ứng dụng Web / API:
- `pyproject.toml` chỉ chứa dải phiên bản lỏng lẻo (ví dụ `fastapi>=0.110.0`).
- Nếu không có `uv.lock`, mỗi lần CI chạy nó có thể tải về một phiên bản thư viện con mới hơn có chứa lỗi vặt (breaking bug), dẫn đến hiện tượng bí ẩn: *"Hôm qua code chạy bình thường, hôm nay không sửa gì cả mà CI lại đỏ rực!"*.
- **Quy tắc:** Luôn commit `uv.lock` vào Git đối với các dự án Application (chỉ các thư viện mã nguồn mở Library mới cân nhắc bỏ qua lock file).

---

## ✍️ Bài tập thực hành

### Bài tập 1: Tối ưu hóa hủy Job dư thừa với `concurrency`
Khi bạn liên tục push 3 commit liên tiếp vào một Pull Request, theo mặc định GitHub Actions sẽ chạy cả 3 pipeline cùng lúc, gây lãng phí runner credits và làm chậm các tiến trình khác.
Hãy tìm hiểu và giải thích cách hoạt động của khối lệnh:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

<details>
<summary>💡 Gợi ý</summary>

Khối lệnh này gom nhóm các lần kích hoạt workflow theo tên workflow (`github.workflow`) và định danh nhánh/PR (`github.ref`). 
Khi một commit mới được push lên cùng nhánh/PR đó, cờ `cancel-in-progress: true` sẽ lập tức hủy bỏ các lượt chạy trước đó đang diễn ra dở dang, chỉ ưu tiên chạy phiên bản code mới nhất. Điều này giúp tiết kiệm 100% thời gian chờ đợi và chi phí runner!
</details>

---

### Bài tập 2: Ma trận kiểm thử đa phiên bản Python (Matrix Strategy)
Hãy viết một job `matrix-tests` sử dụng tính năng **Matrix Strategy** của GitHub Actions để chạy song song bộ kiểm thử trên hai phiên bản Python khác nhau: `3.12` và `3.13`.

<details>
<summary>💡 Gợi ý</summary>

```yaml
jobs:
  matrix-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Cài đặt Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Cài đặt dependencies
        run: uv sync --frozen

      - name: Chạy Pytest trên Python ${{ matrix.python-version }}
        run: uv run pytest
```
</details>

---

### Bài tập 3: Cấu hình Báo cáo Kiểm thử trên giao diện Pull Request
Tìm hiểu cách tích hợp action `dorny/test-reporter@v1` hoặc `codecov/codecov-action@v4` để tải file `coverage.xml` lên và hiển thị trực tiếp đồ thị % bao phủ mã nguồn ngay dưới phần bình luận của Pull Request.

<details>
<summary>💡 Gợi ý</summary>

```yaml
      - name: Đẩy báo cáo Coverage lên Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage.xml
          flags: unittests
          fail_ci_if_error: true
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi biết cách cấu hình workflow GitHub Actions tự động kích hoạt trên các sự kiện `push` và `pull_request`.
- [ ] Tôi hiểu cách sử dụng `astral-sh/setup-uv@v5` với `enable-cache: true` để tối ưu hóa thời gian chạy pipeline.
- [ ] Tôi cấu hình được PostgreSQL Service Container có `health-cmd pg_isready` để chạy integration test an toàn.
- [ ] Tôi nắm vững các lệnh kiểm tra chất lượng mã nguồn: `ruff check`, `ruff format --check`, và `mypy --strict`.
- [ ] Tôi giải thích được lý do bắt buộc phải commit `uv.lock` vào Git và sử dụng cờ `--frozen` trong CI.

---

## 📚 Đọc thêm

- [GitHub Actions Documentation – Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Astral setup-uv GitHub Action](https://github.com/astral-sh/setup-uv)
- [GitHub Actions – Creating PostgreSQL Service Containers](https://docs.github.com/en/actions/using-containerized-services/about-service-containers)
- [Ruff Official Documentation](https://docs.astral.sh/ruff/)
- [Tiếp theo: Milestone M2 – Production API](../project/m2-production-api.md)

<!-- nav:bottom -->
---

[⬅️ Docker & docker-compose](./11-docker-compose.md) | [📚 Mục lục Middle](./README.md) | [M2 – Production API ➡️](../project/m2-production-api.md)
<!-- /nav:bottom -->
