<!-- nav:top -->
[🏠 Home](../README.md) › Getting Started
<!-- /nav:top -->

# Getting Started

Chào mừng bạn đến với **Level 00: Getting Started**! Đây là bước đệm quan trọng mở đầu hành trình chuyển dịch chuyên môn từ C# / .NET sang Python và FastAPI.

Đối với một kỹ sư C#, công đoạn chuẩn bị môi trường trong Python thường là nơi dễ gây bỡ ngỡ nhất: không có một file giải pháp duy nhất (`.sln`), không có file dự án XML (`.csproj`), và có rất nhiều công cụ quản lý package khác nhau trong lịch sử. Tại level này, chúng ta sẽ bỏ qua toàn bộ những công cụ cũ kỹ và tiếp cận trực tiếp với tiêu chuẩn hiện đại nhất của năm 2026: **Python 3.13+**, trình quản lý gói siêu tốc **`uv`** viết bằng Rust, cấu trúc cấu hình chuẩn hóa `pyproject.toml`, và môi trường phát triển tối ưu trên **VS Code**.

---

## 🎯 Mục tiêu đầu ra

Sau khi hoàn thành level này, bạn sẽ đạt được:

- **Làm chủ bộ công cụ hiện đại**: Cài đặt và quản lý các phiên bản Python 3.13+ hoàn toàn độc lập thông qua `uv`, không gây ô nhiễm môi trường hệ điều hành.
- **Thấu hiểu cơ chế môi trường ảo (`.venv`)**: Nắm vững bản chất cách Python nạp thư viện qua `sys.path`, hiểu lý do vì sao Python cần virtual environment riêng cho từng dự án (khác biệt cơ bản so với cơ chế global assembly cache hoặc thư mục `.nuget/packages` của .NET).
- **Quản lý dự án chuẩn hóa**: Khởi tạo cấu trúc dự án chuẩn với `pyproject.toml` (PEP 518/PEP 621), quản lý dependencies và file khóa `uv.lock` có tính tất định (deterministic).
- **Thiết lập IDE chuẩn mực**: Cấu hình Visual Studio Code với bộ ba extension cốt lõi: Python, Pylance (kiểm tra kiểu dữ liệu tĩnh) và Ruff (linter & code formatter tốc độ cực cao).
- **Chuyển đổi tư duy lập trình (Paradigm Shift)**: Nắm vững sự khác biệt triết lý giữa C# và Python: dynamic typing + static type hints, thụt đầu dòng (indentation) thay cho ngoặc nhọn `{}`, mô hình CPython VM, phong cách EAFP (*Easier to Ask for Forgiveness than Permission*) thay vì LBYL (*Look Before You Leap*), và triết lý The Zen of Python.
- ⏱️ **Thời lượng ước tính**: `2–3 ngày` (khoảng 3–4 giờ học tập và thực hành).

---

## 📚 Mục lục

Dưới đây là các bài học chi tiết trong level này:

| STT | Bài học | Thời lượng | Trọng tâm |
|:---:|---|:---:|---|
| 01 | [**Cài đặt môi trường**](./01-setup-environment.md) | ~1.5 giờ | Cài đặt Python 3.13+, `uv`, bản chất `.venv`, `pyproject.toml`, `uv.lock`, cấu hình VS Code (Ruff + Pylance). |
| 02 | [**Python cho dev C#**](./02-python-for-csharp-devs.md) | ~2.0 giờ | So sánh C# vs Python toàn diện, dynamic typing, indentation, PEP 8, The Zen of Python, Truthiness, EAFP vs LBYL. |

> 📌 **Lưu ý về dự án thực hành**: Level 00 tập trung hoàn toàn vào việc thiết lập môi trường và chuyển dịch nền tảng tư duy, do đó chưa có milestone dự án riêng. Cột mốc thực hành dự án đầu tiên của bạn sẽ là [M0 – CLI Task Manager](../project/m0-cli-task-manager.md) nằm ở cuối [Level 01: Fresher](../01-fresher/README.md).

---

## 🧭 Đánh giá năng lực

Trước khi bắt đầu hoặc sau khi hoàn thành level này, bạn có thể tham khảo [**Bảng tự đánh giá năng lực**](../appendix/self-assessment.md) để tự kiểm tra kiến thức về môi trường và tư duy Pythonic của mình.

<!-- nav:bottom -->
---

[⬅️ Lộ trình Python & FastAPI: Fresher → Senior](../README.md) | [🏠 Home](../README.md) | [Cài đặt môi trường ➡️](./01-setup-environment.md)
<!-- /nav:bottom -->
