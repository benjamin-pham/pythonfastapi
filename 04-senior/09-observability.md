<!-- nav:top -->
[🏠 Home](../README.md) › [Senior](./README.md) › Bài 09
<!-- /nav:top -->

# Observability

> ⏱️ Thời lượng: ~4.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 08: Bảo mật: OWASP API Top 10](./08-security-owasp.md) và [Logging & xử lý lỗi toàn cục](../03-middle/10-logging-error-handling.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- **Thấu hiểu toàn diện ba trụ cột của Khả năng quan sát (The Three Pillars of Observability)**: Phân định rạch ròi vai trò của Metrics (Đo lường lượng hóa), Logs (Ghi chép sự kiện có ngữ cảnh) và Traces (Lần vết luồng phân tán), gắn kết chúng qua `trace_id` và `span_id`.
- **Làm chủ chuẩn công nghiệp OpenTelemetry (OTel)**: Nắm vững kiến trúc OTel (API vs SDK vs Collector), chuẩn truyền bá ngữ cảnh W3C Trace Context (`traceparent`), và cơ chế thu thập dữ liệu độc lập với nền tảng lưu trữ (Vendor-neutral).
- **Thiết kế Distributed Tracing cho hệ thống phân tán**: Tự động đo đạc (Auto-instrumentation) FastAPI, SQLAlchemy, Redis và HTTP client; thuần thục kỹ thuật tạo Manual Spans, gắn Span Attributes và ghi nhận ngoại lệ (Exception Recording).
- **Thu thập và thiết kế Prometheus Metrics chuẩn mực**: Triển khai các loại Metric cốt lõi (Counter, Gauge, Histogram) theo chuẩn 4 Golden Signals của Google SRE, tránh bẫy bùng nổ dữ liệu nhãn (High-Cardinality Trap).
- **Xây dựng hệ thống Structured JSON Logging có Trace Context**: Giúp đội ngũ vận hành truy vấn tức thì toàn bộ logs của một giao dịch phức tạp đi qua nhiều microservices chỉ bằng một cú nhấp chuột trên Grafana / Jaeger / Kibana.

---

## 🔁 So sánh với C# / ASP.NET

Trong hệ sinh thái .NET, Observability đã được Microsoft đầu tư đưa thẳng vào Base Class Library (BCL) và kiến trúc hosting hiện đại:

| Khái niệm / Thành phần | Hệ sinh thái C# / ASP.NET Core | Hệ sinh thái Python 3.12+ / FastAPI |
|---|---|---|
| **Distributed Tracing** | Tích hợp sẵn trong BCL qua `System.Diagnostics.Activity` và `ActivitySource`. SDK `OpenTelemetry.Extensions.Hosting` kết nối trực tiếp với ASP.NET Core pipeline. | Sử dụng gói chính thức `opentelemetry-api` và `opentelemetry-sdk`. Khởi tạo `TracerProvider` và instrument FastAPI app. |
| **Context Propagation** | Tự động truyền bá qua `AsyncLocal<T>` và `DistributedContextPropagator` (hỗ trợ chuẩn W3C TraceContext mặc định). | Truyền bá qua `contextvars.ContextVar` và W3C TraceContext Propagator trong OpenTelemetry Python SDK. |
| **Metrics Collection** | Sử dụng `System.Diagnostics.Metrics.Meter` (BCL) sinh ra Counters/Histograms, hoặc thư viện `prometheus-net`. | Sử dụng `prometheus-client` hoặc OpenTelemetry Metrics SDK xuất bản qua Prometheus Exporter (`/metrics`). |
| **Structured Logging** | `ILogger` tích hợp sẵn với Serilog: Tự động đính kèm `{TraceId}` và `{SpanId}` vào định dạng JSON. | Thư viện `structlog` hoặc module `logging` tùy biến với Processor lấy `trace_id` từ `opentelemetry.trace.get_current_span()`. |
| **APM / Tracing Tools** | Application Insights, Jaeger, OpenSearch, Datadog .NET Tracer. | Jaeger, Grafana Tempo, Prometheus, Grafana Loki, Datadog Python APM. |

---

## 📖 Lý thuyết

### 1. Ba trụ cột của Observability & Bốn tín hiệu vàng (Golden Signals)

Khi một hệ thống backend mở rộng quy mô từ một ứng dụng đơn lẻ (Monolith) sang cụm dịch vụ phân tán (Distributed Services), các phương pháp debug truyền thống như đọc log file trên máy chủ đơn lẻ hoàn toàn phá sản.

```text
                               ┌────────────────────────────────┐
                               │         OBSERVABILITY          │
                               └────────────────┬───────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
        [ METRICS ]                        [ TRACES ]                      [ LOGS ]
  "Chuyện gì đang xảy ra?"          "Vấn đề xảy ra ở đâu?"           "Tại sao nó xảy ra?"
  - Dữ liệu chuỗi thời gian          - Bản đồ đường đi của request   - Bản ghi sự kiện chi tiết
  - Định lượng (RPS, CPU, RAM)       - Đo độ trễ từng chặng (Spans)  - Ngữ cảnh lỗi (Exception)
  - Kích hoạt cảnh báo (Alert)       - Tìm điểm nghẽn hiệu năng      - Gắn kèm trace_id / span_id
```

#### Bốn tín hiệu vàng (Google SRE Golden Signals)
1. **Latency (Độ trễ)**: Thời gian hoàn thành một yêu cầu (phân tích theo phân vị p50, p95, p99; không dùng trung bình cộng).
2. **Traffic (Lưu lượng)**: Nhu cầu gửi đến hệ thống (RPS - Requests Per Second, số giao dịch đồng thời).
3. **Errors (Tỷ lệ lỗi)**: Số lượng hoặc phần trăm các yêu cầu thất bại (HTTP 5xx, kết nối DB timeout).
4. **Saturation (Độ bão hòa)**: Mức độ sử dụng tài nguyên của hệ thống (phần trăm CPU, bộ nhớ, dung lượng Database Connection Pool).

---

### 2. Kiến trúc OpenTelemetry (OTel)

OpenTelemetry là dự án mã nguồn mở trực thuộc CNCF (Cloud Native Computing Foundation), hình thành từ sự sáp nhập của OpenTracing và OpenCensus. OTel cung cấp một chuẩn giao thức duy nhất cho cả Traces, Metrics và Logs.

```text
[ FastAPI App ] ──► [ OTel API / SDK ] ──► [ OTel Collector ] ──► [ Jaeger / Tempo ] (Traces)
                           │                                  ──► [ Prometheus ]       (Metrics)
                           ▼                                  ──► [ Grafana Loki ]     (Logs)
                   [ W3C TraceContext ]
                   traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

- **OTel API**: Bộ định nghĩa giao diện (Interfaces) thuần túy. Code nghiệp vụ của bạn chỉ phụ thuộc vào API này để không bị khóa chặt vào bất kỳ nhà cung cấp nào.
- **OTel SDK**: Bản triển khai cụ thể của API (xử lý Batching, Sampling, Exporters).
- **Span**: Đơn vị công việc cơ bản trong một Trace. Mỗi span đại diện cho một khoảng thời gian thực thi (ví dụ: một câu query DB, một lời gọi Redis, một HTTP request).
- **Trace**: Một đồ thị có hướng (DAG) liên kết các Spans lại với nhau, đại diện cho toàn bộ hành trình của một request từ lúc đi vào API Gateway đến khi hoàn tất.

#### Chuẩn W3C TraceContext
Để liên kết các chặng trong hệ thống phân tán, các dịch vụ truyền cho nhau header `traceparent` theo định dạng:
```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              │                │                                │        │
           Version          Trace ID                         Span ID   Flags (01 = Sampled)
```

---

### 3. Prometheus Metrics: Các kiểu dữ liệu cốt lõi

Prometheus lưu trữ dữ liệu dưới dạng chuỗi thời gian (Time-series) với định dạng: `metric_name{label1="val1", label2="val2"} value timestamp`.

1. **Counter (Bộ đếm tăng dần)**:
   - Giá trị chỉ có thể tăng lên hoặc reset về 0 khi server restart.
   - Thích hợp đo: Tổng số HTTP requests (`http_requests_total`), tổng số lỗi (`http_errors_total`).
2. **Gauge (Thước đo biến thiên)**:
   - Giá trị có thể tăng hoặc giảm tự do tại bất kỳ thời điểm nào.
   - Thích hợp đo: Số kết nối WebSocket đang mở (`active_websocket_connections`), dung lượng RAM đang chiếm dụng, số lượng workers rảnh rỗi.
3. **Histogram (Biểu đồ phân phối theo khoảng - Buckets)**:
   - Đếm tần suất các giá trị rơi vào các khoảng định trước (buckets). Tự động sinh ra các metric con: `_bucket`, `_sum`, `_count`.
   - Thích hợp đo: Thời gian phản hồi của API (`http_request_duration_seconds`), kích thước payload.

---

## 💻 Ví dụ thực hành

### 1. Cấu hình OpenTelemetry Tracing hoàn chỉnh cho FastAPI

Minh họa việc khởi tạo `TracerProvider`, gắn `BatchSpanProcessor` xuất dữ liệu qua OTLP / Console, và tự động instrument ứng dụng FastAPI:

```python
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)


def setup_telemetry() -> TracerProvider:
    # 1. Định nghĩa Resource: Tên service và môi trường triển khai
    resource = Resource.create(
        {
            "service.name": "taskflow-api",
            "service.version": "1.0.0",
            "deployment.environment": "production",
        }
    )

    # 2. Khởi tạo TracerProvider
    provider = TracerProvider(resource=resource)

    # 3. Sử dụng BatchSpanProcessor để gửi spans ngầm (không block request)
    # Trong môi trường thực tế, thay ConsoleSpanExporter bằng OTLPSpanExporter
    exporter = ConsoleSpanExporter()
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # 4. Đặt làm Global Tracer Provider
    trace.set_tracer_provider(provider)
    return provider


tracer_provider = setup_telemetry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Khởi tạo tài nguyên
    yield
    # Dọn dẹp và đẩy toàn bộ spans còn đọng lại trước khi ứng dụng tắt
    tracer_provider.shutdown()


app = FastAPI(title="TaskFlow Observability API", lifespan=lifespan)

# Tự động đo đạc toàn bộ requests của FastAPI
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)


@app.get("/api/v1/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}
```

---

### 2. Tạo Manual Spans, Gán Attributes & Ghi nhận Exception

Khi triển khai nghiệp vụ phức tạp, bạn cần tạo các spans tùy biến để đo đạc chính xác từng phân đoạn:

```python
from __future__ import annotations

import asyncio
from typing import Any
from fastapi import FastAPI, HTTPException, status
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

app = FastAPI(title="Manual Spans Demo")
tracer = trace.get_tracer("taskflow.order_service")


async def simulate_external_credit_check(customer_id: str) -> bool:
    await asyncio.sleep(0.05)
    if customer_id == "bad_credit":
        return False
    return True


@app.post("/api/v1/orders")
async def create_order(customer_id: str, amount: float) -> dict[str, Any]:
    # Tạo một child span bao bọc nghiệp vụ tạo đơn hàng
    with tracer.start_as_current_span("order.process") as span:
        # Gán các thuộc tính quan trọng (Attributes) cho span
        span.set_attribute("customer.id", customer_id)
        span.set_attribute("order.amount", amount)

        # Thêm sự kiện (Event) ghi dấu mốc thời gian
        span.add_event("credit_check_started", {"timestamp_stage": "validation"})

        try:
            # Đo lường đoạn kiểm tra tín dụng
            with tracer.start_as_current_span("order.verify_credit") as credit_span:
                credit_ok = await simulate_external_credit_check(customer_id)
                credit_span.set_attribute("credit.approved", credit_ok)

                if not credit_ok:
                    raise ValueError("Khách hàng không đủ điều kiện tín dụng.")

            span.set_status(Status(StatusCode.OK))
            return {"status": "SUCCESS", "order_id": "ord_9999"}

        except Exception as exc:
            # Ghi nhận ngoại lệ vào span và chuyển trạng thái sang ERROR
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, description=str(exc)))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
```

---

### 3. Thu thập và Xuất bản Prometheus Metrics với `/metrics`

Dưới đây là mô hình thu thập Prometheus metrics chuẩn mực cho FastAPI: đo lường số lượng requests, đếm mã lỗi và biểu đồ phân vị độ trễ (Histogram):

```python
from __future__ import annotations

import time
from collections.abc import Callable
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="Prometheus Metrics API")

# Định nghĩa các Metrics cốt lõi
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Tổng số HTTP requests được phục vụ",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Phân phối độ trễ của các HTTP requests",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next: Callable) -> Response:
    # Bỏ qua endpoint /metrics để tránh vòng lặp tự đo chính mình
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    endpoint = request.url.path
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
        status_code = str(response.status_code)
    except Exception as exc:
        status_code = "500"
        raise exc from None
    finally:
        duration = time.perf_counter() - start_time
        # Cập nhật số liệu vào Prometheus Collector
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    return response


@app.get("/metrics")
async def get_prometheus_metrics() -> Response:
    """Endpoint nội bộ cho Prometheus Server cào dữ liệu (Scraping)."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/items")
async def get_items() -> list[str]:
    return ["Task A", "Task B", "Task C"]
```

---

## ⚠️ Lỗi thường gặp

### 1. Bẫy dữ liệu nhãn bùng nổ (High-Cardinality Metric Trap)
Đây là sai lầm phổ biến nhất khi cấu hình Prometheus: Lập trình viên gắn các giá trị biến động vô hạn (như `user_id`, `order_id`, `email`, hoặc full request URL có path parameters `/tasks/12345`) vào nhãn của Metric:
```python
# TAI HỌA: Mỗi user tạo ra một time-series độc lập trên Prometheus RAM!
REQUEST_COUNT.labels(user_id=user.id).inc()
```
Khi có 500,000 users, Prometheus sẽ phải lưu trữ 500,000 chuỗi dữ liệu thời gian riêng biệt, khiến hệ thống giám sát lập tức bị cạn kiệt RAM và sập (OOM Crash). **Nhãn Prometheus chỉ được chứa các giá trị có tập hữu hạn nhỏ (Low-Cardinality: HTTP Method, Status Code, Route Template)**.

### 2. Sử dụng `SimpleSpanProcessor` trên Production
`SimpleSpanProcessor` gửi từng span qua mạng ngay lập tức đồng bộ khi span kết thúc. Nếu mạng bị lag hoặc collector bị nghẽn, mọi HTTP request của người dùng sẽ bị đóng băng theo! **Trên Production, luôn luôn bắt buộc dùng `BatchSpanProcessor`** để gom spans vào hàng đợi trong bộ nhớ và gửi theo lô (batch) bất đồng bộ dưới background.

### 3. Đánh mất Trace Context khi gọi External Services
Khi dịch vụ Service A gọi sang Service B qua HTTP hoặc gửi message vào hàng đợi (RabbitMQ/Redis), nhiều người chỉ gửi payload thuần mà quên chèn header `traceparent`. Hậu quả là Trace bị đứt gãy thành hai trace riêng biệt, mất hoàn toàn khả năng quan sát luồng liên dịch vụ. Hãy sử dụng `TraceContextTextMapPropagator().inject(headers)` hoặc dùng HTTPX auto-instrumentation.

### 4. Bỏ ngỏ Endpoint `/metrics` ra ngoài Internet
Dữ liệu trong `/metrics` chứa rất nhiều thông tin nhạy cảm về kiến trúc, lưu lượng và các endpoint nội bộ của hệ thống. Nếu không giới hạn truy cập (qua Nginx cấu hình chỉ cho IP của Prometheus server cào, hoặc yêu cầu Basic Auth), kẻ tấn công có thể nghiên cứu toàn bộ hệ thống của bạn một cách dễ dàng.

---

## ✍️ Bài tập thực hành

### Bài tập 1: Tự động đính kèm `trace_id` vào Structured JSON Logger
Viết một hàm định dạng log (Log Formatter) hoặc Context Processor:
1. Trích xuất active span từ OpenTelemetry: `span = trace.get_current_span()`.
2. Nếu span đang hoạt động, lấy `trace_id` và `span_id` (chuyển sang chuỗi hex 32 ký tự và 16 ký tự).
3. Đính kèm chúng vào mọi log record JSON được ghi ra `stdout`.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

import json
import logging
from typing import Any
from opentelemetry import trace


class JsonTraceFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": record.created,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Lấy TraceContext từ OTel
        span = trace.get_current_span()
        span_ctx = span.get_span_context()

        if span_ctx.is_valid:
            log_payload["trace_id"] = format(span_ctx.trace_id, "032x")
            log_payload["span_id"] = format(span_ctx.span_id, "016x")
        else:
            log_payload["trace_id"] = None
            log_payload["span_id"] = None

        return json.dumps(log_payload)
```
</details>

---

### Bài tập 2: Decorator `@trace_operation(name)` cho Service Layer
Xây dựng một async decorator `@trace_operation(operation_name: str)`:
1. Mở một span mới với tên được chỉ định.
2. Tự động ghi nhận thời gian bắt đầu và kết thúc.
3. Nếu hàm ném ngoại lệ, ghi nhận lỗi bằng `span.record_exception(exc)` và set span status thành `ERROR` trước khi re-raise ngoại lệ.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

from collections.abc import Callable
import functools
from typing import Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("taskflow.custom_decorator")


def trace_operation(name: str) -> Callable:

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                    raise exc

        return wrapper

    return decorator
```
</details>

---

### Bài tập 3: Custom Prometheus Gauge đo lường Active Database Connections
Tạo một Prometheus Gauge `db_pool_active_connections` và tích hợp hàm cập nhật số lượng kết nối đang được mượn từ SQLAlchemy Connection Pool mỗi khi có request vào và ra.

<details>
<summary>💡 Gợi ý</summary>

```python
from __future__ import annotations

from prometheus_client import Gauge

DB_ACTIVE_CONNS = Gauge(
    "db_pool_active_connections",
    "Số lượng kết nối cơ sở dữ liệu hiện đang được sử dụng",
)


class TrackedConnectionContext:

    async def __aenter__(self):
        DB_ACTIVE_CONNS.inc()
        # Giả lập mở kết nối
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        DB_ACTIVE_CONNS.dec()
```
</details>

---

## ✅ Checklist tự đánh giá

- [ ] Tôi giải thích được vai trò của 3 trụ cột Observability: Metrics, Traces, Logs và cách gắn kết chúng bằng `trace_id`.
- [ ] Tôi hiểu rõ chuẩn W3C TraceContext và định dạng header `traceparent`.
- [ ] Tôi biết cách phân biệt OTel API, OTel SDK và OTel Collector.
- [ ] Tôi nắm vững nguyên lý hoạt động của `BatchSpanProcessor` và vì sao không dùng `SimpleSpanProcessor` trên production.
- [ ] Tôi phân biệt được 3 loại Prometheus Metrics: Counter, Gauge, Histogram và biết khi nào nên dùng loại nào.
- [ ] Tôi nhận diện và phòng tránh được lỗi High-Cardinality làm tràn bộ nhớ Prometheus.
- [ ] Tôi biết cách cấu hình bảo vệ endpoint `/metrics` an toàn.

---

## 📚 Đọc thêm

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/languages/python/)
- [W3C Recommendation: Trace Context](https://www.w3.org/TR/trace-context/)
- [Prometheus Best Practices: Metric and Label Naming](https://prometheus.io/docs/practices/naming/)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Tiếp theo: Bài 10 – Deploy production](./10-production-deployment.md)

<!-- nav:bottom -->
---

[⬅️ Bảo mật: OWASP API Top 10](./08-security-owasp.md) | [📚 Mục lục Senior](./README.md) | [Deploy production ➡️](./10-production-deployment.md)
<!-- /nav:bottom -->
