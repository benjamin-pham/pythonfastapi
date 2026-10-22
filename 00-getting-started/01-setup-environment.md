<!-- nav:top -->
[🏠 Home](../README.md) › [Getting Started](./README.md) › Bài 01
<!-- /nav:top -->

# Cài đặt môi trường

> ⏱️ Thời lượng: ~1.5 giờ · 📌 Yêu cầu trước: Máy tính có kết nối Internet và terminal (bash, zsh hoặc PowerShell), đã cài đặt Git.

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Cài đặt và quản lý các phiên bản Python 3.13+ thông qua **`uv`** — bộ công cụ quản lý package và project thế hệ mới viết bằng Rust từ Astral.
- Thấu hiểu bản chất kỹ thuật của **Virtual Environment (`.venv`)**: cơ chế hoạt động, tại sao Python cần môi trường ảo cô lập cho từng dự án, và sự khác biệt căn bản so với cơ chế dependency của .NET.
- Sử dụng thành thạo chuẩn **`pyproject.toml`** (PEP 518/PEP 621) kết hợp với file khóa **`uv.lock`** để quản lý dependencies tất định (deterministic).
- Thiết lập môi trường lập trình tối ưu trên **Visual Studio Code** với bộ ba công cụ: extension Python, Pylance (kiểm tra kiểu tĩnh) và Ruff (linter & code formatter siêu tốc).

---

## 🔁 So sánh với C# / ASP.NET

Là một lập trình viên C#, bạn đã quen thuộc với hệ sinh thái `.NET SDK` vô cùng đồng nhất. Bảng dưới đây sẽ giúp bạn ánh xạ nhanh các khái niệm tương đương:

| Khái niệm / Tác vụ | Hệ sinh thái C# / .NET | Hệ sinh thái Python hiện đại (2026) |
|---|---|---|
| **Bộ công cụ dòng lệnh (CLI)** | `dotnet` CLI (`dotnet new`, `dotnet run`...) | `uv` CLI (`uv init`, `uv run`...) |
| **Khai báo dự án & cấu hình** | File XML: `*.csproj` hoặc `Directory.Build.props` | File TOML: `pyproject.toml` (chuẩn PEP 621) |
| **Kho lưu trữ package (Package Registry)** | NuGet (`nuget.org`) | PyPI (`pypi.org` - Python Package Index) |
| **File khóa phiên bản (Lockfile)** | `packages.lock.json` (nếu bật `RestoreLockedMode`) | `uv.lock` (mặc định được sinh tự động) |
| **Quản lý SDK / Runtime** | .NET Global SDK + `global.json` | `uv python install 3.13` + `.python-version` |
| **Cơ chế cô lập gói (Isolation)** | Global Cache (`~/.nuget/packages`) + tham chiếu DLL trực tiếp | Thư mục cục bộ `.venv` cho từng dự án |
| **IDE & Môi trường kiểm tra mã** | Visual Studio / JetBrains Rider + Roslyn Analyzers | VS Code + Extension Pylance + Linter/Formatter Ruff |
| **Cài đặt thư viện** | `dotnet add package <PackageName>` | `uv add <package-name>` |
| **Chạy ứng dụng** | `dotnet run` | `uv run <script.py>` hoặc `uv run <module>` |
| **Khôi phục phụ thuộc (Restore)** | `dotnet restore` | `uv sync` |

### Vì sao .NET không cần `.venv` nhưng Python lại bắt buộc?

Trong .NET (C#), trình biên dịch Roslyn biên dịch mã nguồn thành file nhị phân IL (`*.dll`). Khi bạn cài thư viện qua NuGet, các file DLL được tải về một thư mục cache tập trung trên máy (`~/.nuget/packages`). Khi build dự án, MSBuild sẽ trỏ trực tiếp đến đường dẫn cụ thể của các file DLL tương ứng. Hai dự án C# khác nhau trên cùng một máy có thể dùng hai phiên bản thư viện khác nhau (ví dụ: một project dùng `Newtonsoft.Json 12.0` và một project dùng `13.0`) mà hoàn toàn không xung đột.

Ngược lại, **Python là ngôn ngữ thông dịch (interpreted language)**. Khi bạn viết `import requests`, trình thông dịch CPython sẽ duyệt qua danh sách các đường dẫn trong danh sách `sys.path`. Nếu bạn cài đặt thư viện vào Python toàn cục của hệ thống (`global site-packages`), toàn bộ máy tính chỉ có **duy nhất một phiên bản** của thư viện đó. Khi Dự án A yêu cầu `requests==2.28.0` và Dự án B yêu cầu `requests==2.32.0`, cài đè phiên bản này sẽ lập tức làm gãy vỡ dự án kia (hiện tượng *Dependency Hell*).

> [!IMPORTANT]
> **Quy tắc vàng của Python**: Tuyệt đối không bao giờ cài đặt thư viện vào Python toàn cục của hệ điều hành. Mỗi dự án Python phải luôn luôn sở hữu một môi trường ảo (`.venv`) riêng biệt.

---

## 📖 Lý thuyết

### 1. Lịch sử đóng gói Python và sự trỗi dậy của `uv`

Trong hơn hai thập kỷ, quản lý môi trường và package trong Python từng là một "cơn ác mộng" với sự phân mảnh của hàng loạt công cụ:

1. **Giai đoạn sơ khai (`distutils`, `setup.py`, `easy_install`)**: Đóng gói phức tạp, yêu cầu thực thi mã Python tùy biến ngay trong quá trình cài đặt, tiềm ẩn rủi ro bảo mật.
2. **Giai đoạn chuẩn hóa ban đầu (`pip` + `requirements.txt`)**: `pip` giúp cài đặt dễ dàng hơn nhưng `requirements.txt` không có cơ chế lockfile phân tầng (transitive dependencies) đáng tin cậy. Nếu chỉ ghi `requests>=2.0`, hai máy tính khác nhau chạy `pip install -r requirements.txt` vào hai thời điểm khác nhau có thể nhận về các phiên bản thư viện con khác nhau.
3. **Giai đoạn công cụ wrapper (`virtualenv`, `pipenv`, `poetry`)**: `poetry` là bước tiến lớn khi tiên phong áp dụng `pyproject.toml` và file khóa `poetry.lock`. Tuy nhiên, resolver của Poetry được viết bằng Python thuần, xử lý thuật toán giải quyết xung đột dependency rất chậm (có thể mất từ 2 đến 10 phút trên các dự án lớn).
4. **Kỷ nguyên hiện đại (2024–2026): Cuộc cách mạng mang tên `uv`**:
   - Được phát triển bởi **Astral** (nhóm tác giả đứng sau Ruff), `uv` được viết hoàn toàn bằng **Rust**.
   - `uv` nhanh gấp **10 đến 100 lần** so với `pip` và `poetry` nhờ khả năng song song hóa tối đa, caching thông minh dựa trên Content-Addressable Storage (CAS), và giải quyết thuật toán SAT solver bằng Rust.
   - Hợp nhất tất cả trong một (*All-in-one toolchain*): `uv` không chỉ thay thế `pip`, mà thay thế cả `virtualenv`, `pyenv` (quản lý phiên bản Python), `pip-tools`, và `poetry`.

### 2. Cấu trúc nội bộ của Virtual Environment (`.venv`)

Khi bạn khởi tạo hoặc để `uv` tự động tạo một virtual environment, một thư mục `.venv` được tạo ra ở gốc dự án với cấu trúc:

```
.venv/
├── bin/ (hoặc Scripts/ trên Windows)
│   ├── python -> /path/to/real/python3.13  (symlink tới runtime gốc)
│   ├── python3 -> python
│   ├── activate                           (script shell để đổi biến môi trường)
│   └── ruff, pytest...                    (các script CLI của package cài đặt)
├── lib/
│   └── python3.13/
│       └── site-packages/                 (toàn bộ source code thư viện cài thêm)
└── pyvenv.cfg                             (file cấu hình định danh venv)
```

- **`pyvenv.cfg`**: Chứa đường dẫn `home` trỏ về Python runtime gốc và cờ `include-system-site-packages = false` (ngăn không cho code trong venv nhìn thấy thư viện cài ngoài hệ thống).
- **Lệnh `activate` làm gì?**: Khi bạn chạy `source .venv/bin/activate` (Linux/macOS) hoặc `.venv\Scripts\Activate.ps1` (Windows), shell script này chỉ làm hai việc chính:
  1. Đặt biến môi trường `VIRTUAL_ENV` trỏ vào thư mục `.venv`.
  2. Ghi đè biến môi trường `PATH`, đưa `.venv/bin` lên đầu danh sách tìm kiếm nhị phân.
- **Tiện ích vượt trội của `uv run`**: Bạn **không cần phải gõ `source .venv/bin/activate`** mỗi khi mở terminal. Lệnh `uv run <script.py>` sẽ tự động tìm kiếm thư mục `.venv` gần nhất, thiết lập biến môi trường nội bộ trong sub-process và thực thi ngay lập tức.

### 3. Chuẩn cấu hình `pyproject.toml` và `uv.lock`

`pyproject.toml` là file cấu hình khai báo tiêu chuẩn theo PEP 621, thay thế toàn bộ các file rời rạc cũ như `setup.cfg`, `requirements.txt`, `.flake8`.

Một file `pyproject.toml` điển hình gồm:
- **`[project]`**: Khai báo metadata cơ bản (`name`, `version`, `description`, `requires-python = ">=3.13"`).
- **`dependencies`**: Danh sách thư viện production mà ứng dụng phụ thuộc trực tiếp.
- **`[dependency-groups]`**: Khai báo các nhóm thư viện phát triển (ví dụ: nhóm `dev` gồm `pytest`, `ruff`, `mypy`).
- **`[tool.*]`**: Cấu hình các công cụ phụ trợ (Ruff, Mypy, Pytest) tập trung tại một nơi.

File `uv.lock` lưu trữ chính xác mã băm SHA256 và phiên bản cụ thể của toàn bộ cây phụ thuộc (bao gồm cả các thư viện gián tiếp). Bạn **phải luôn commit `uv.lock` vào Git** để đảm bảo môi trường ở máy local, staging, production, và CI/CD giống hệt nhau 100%.

### 4. Các lệnh `uv` thiết yếu hàng ngày

| Lệnh | Ý nghĩa kỹ thuật |
|---|---|
| `uv python install 3.13` | Tải và cài đặt bản Python 3.13 độc lập (không cần quyền root/admin) |
| `uv init <project-name>` | Tạo một project Python mới chuẩn hóa với `pyproject.toml` và `.venv` |
| `uv add <package>` | Thêm thư viện vào `dependencies` và tự động cập nhật `uv.lock` |
| `uv add --dev <package>` | Thêm thư viện vào nhóm `dev` trong `pyproject.toml` |
| `uv remove <package>` | Gỡ bỏ thư viện khỏi project |
| `uv run <command/file>` | Thực thi command/file trong ngữ cảnh môi trường ảo `.venv` |
| `uv sync` | Đồng bộ hóa `.venv` khớp chính xác với `uv.lock` (xóa package thừa, tải package thiếu) |

---

## 💻 Ví dụ

Hãy cùng thực hành tạo một project Python 3.13 hoàn chỉnh từ đầu bằng `uv` và cấu hình VS Code.

### Bước 1: Cài đặt `uv`

Mở terminal và chạy lệnh cài đặt chính thức:

- **Linux / macOS**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

Kiểm tra cài đặt:
```bash
uv --version
```

### Bước 2: Khởi tạo project `hello-python`

```bash
uv init hello-python
cd hello-python
uv python pin 3.13
```

Thêm thư viện hiển thị giao diện console đẹp mắt `rich` và thư viện kiểm thử `pytest`:

```bash
uv add rich
uv add --dev pytest
```

### Bước 3: Xem xét file `pyproject.toml` được tạo ra

File `pyproject.toml` sẽ có nội dung tương tự như sau:

```toml
[project]
name = "hello-python"
version = "0.1.0"
description = "Project khởi đầu làm quen với hệ sinh thái Python hiện đại"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "rich>=13.9.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

### Bước 4: Viết mã nguồn kiểm tra môi trường `main.py`

Tạo hoặc cập nhật file `main.py` với nội dung sau:

```python
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def get_runtime_details() -> dict[str, str]:
    """Thu thập thông tin chi tiết về Python runtime và Virtual Environment."""
    prefix = sys.prefix
    base_prefix = getattr(sys, "base_prefix", prefix)
    is_virtualenv = prefix != base_prefix

    return {
        "version": sys.version.split()[0],
        "executable": sys.executable,
        "prefix": prefix,
        "base_prefix": base_prefix,
        "is_venv": "Đang chạy trong .venv ✅" if is_virtualenv else "Chạy ngoài venv ❌",
    }


def main() -> None:
    console = Console()
    details = get_runtime_details()

    table = Table(title="Thông tin Python Runtime", show_header=True, header_style="bold magenta")
    table.add_column("Thuộc tính", style="cyan", width=22)
    table.add_column("Giá trị", style="green")

    table.add_row("Phiên bản Python", details["version"])
    table.add_row("Trình thực thi (Path)", details["executable"])
    table.add_row("Prefix (.venv)", details["prefix"])
    table.add_row("Base Prefix (System)", details["base_prefix"])
    table.add_row("Trạng thái cách ly", details["is_venv"])

    console.print(table)

    summary_panel = Panel(
        "[bold yellow]Môi trường Python 3.13 và uv đã được cấu hình hoàn hảo![/bold yellow]\n"
        "Sẵn sàng bước vào các bài học tiếp theo.",
        title="[bold green]Sẵn sàng[/bold green]",
        border_style="green",
    )
    console.print(summary_panel)


if __name__ == "__main__":
    main()
```

Chạy chương trình bằng lệnh `uv run`:

```bash
uv run main.py
```

`uv` sẽ tự động kích hoạt môi trường ảo cục bộ, kiểm tra dependency `rich`, và in ra bảng thông tin trực quan mà bạn không cần phải tự cấu hình path phức tạp.

### Bước 5: Cấu hình VS Code Workspace chuẩn mực

Tạo thư mục `.vscode/` và file `.vscode/settings.json` tại thư mục gốc của project:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },
  "python.analysis.typeCheckingMode": "standard"
}
```

> [!TIP]
> Trên Windows, đường dẫn interpreter trong settings là `${workspaceFolder}/.venv/Scripts/python.exe`. Hãy cài đặt hai extension chính thức trên VS Code Marketplace: **Python** (của Microsoft, đi kèm Pylance) và **Ruff** (của Astral Software). Khi bật `formatOnSave`, mỗi lần bạn bấm `Ctrl+S`, Ruff sẽ tự động format code và sắp xếp lại toàn bộ câu lệnh import theo chuẩn PEP 8 với tốc độ dưới 10ms.

---

## ⚠️ Lỗi thường gặp

### 1. Cài đặt package vào global Python (`pip install` bên ngoài `.venv`)
- **Hiện tượng**: Bạn mở terminal mới, chạy lệnh `pip install requests`, nhưng khi chạy code trong VS Code thì bị báo lỗi `ModuleNotFoundError: No module named 'requests'`.
- **Nguyên nhân**: Package bị cài vào Python hệ thống, trong khi VS Code đang sử dụng Python nằm trong `.venv`.
- **Khắc phục**: Luôn sử dụng lệnh `uv add <package>` từ thư mục dự án. `uv` sẽ ghi nhận dependency vào `pyproject.toml` và cài đặt thẳng vào `.venv`.

### 2. VS Code nhận diện nhầm Python Interpreter
- **Hiện tượng**: VS Code báo gạch chân đỏ các import dù bạn đã chạy `uv add`, thanh trạng thái góc dưới bên phải hiện `Python 3.10.x` của hệ điều hành thay vì `3.13.x (.venv)`.
- **Nguyên nhân**: VS Code chưa quét được thư mục `.venv` vừa tạo hoặc chưa reload window.
- **Khắc phục**:
  1. Nhấn tổ hợp phím `Ctrl + Shift + P` (hoặc `Cmd + Shift + P` trên macOS).
  2. Gõ `Python: Select Interpreter`.
  3. Chọn mục có nhãn `('.venv': venv) ./.venv/bin/python`.

### 3. Quên commit file `uv.lock` vào Git
- **Hiện tượng**: Ứng dụng chạy tốt ở máy bạn nhưng khi đồng đội clone về hoặc khi chạy trên GitHub Actions CI/CD thì bị lỗi do phiên bản package con không tương thích.
- **Nguyên nhân**: Bỏ sót file `uv.lock` hoặc vô tình đưa nó vào `.gitignore`.
- **Khắc phục**: Giữ `uv.lock` trong Git repository. File `.gitignore` chỉ nên bỏ qua thư mục chứa mã nhị phân/thư viện đã tải là `.venv/`, `.ruff_cache/`, `__pycache__/`.

---

## 🏋️ Bài tập

### Bài tập 1: Khởi tạo cấu trúc dự án `taskflow-starter`
Khởi tạo một dự án mới tên là `taskflow-starter` bằng `uv`.
- Thiết lập phiên bản Python tối thiểu là `3.13`.
- Thêm hai dependencies production: `rich` (hiển thị terminal) và `pydantic>=2.10.0` (thư viện data validation).
- Thêm hai dependencies development: `pytest` và `ruff`.
- Kiểm tra file `pyproject.toml` và xác nhận file `uv.lock` đã được tạo ra.

<details>
<summary>💡 Gợi ý</summary>

Chạy chuỗi lệnh sau trong terminal:
```bash
uv init taskflow-starter
cd taskflow-starter
uv python pin 3.13
uv add rich "pydantic>=2.10.0"
uv add --dev pytest ruff
uv sync
```
Kiểm tra cấu trúc file: mở `pyproject.toml` để xem các mục `[project.dependencies]` và `[dependency-groups.dev]`.
</details>

---

### Bài tập 2: Viết script `inspect_runtime.py` kiểm tra `sys.path`
Trong dự án `taskflow-starter`, hãy tạo file `inspect_runtime.py`. Sử dụng `sys.path` và thư viện `rich.table.Table` để in ra danh sách các thư mục mà Python sẽ tìm kiếm khi thực hiện lệnh `import`. Hãy đánh dấu rõ ràng thư mục nào thuộc về `.venv/lib/.../site-packages`.

<details>
<summary>💡 Gợi ý</summary>

```python
import sys
from rich.console import Console
from rich.table import Table


def main() -> None:
    console = Console()
    table = Table(title="Danh sách đường dẫn tìm kiếm Module (sys.path)", show_lines=True)
    table.add_column("STT", justify="right", style="cyan", no_wrap=True)
    table.add_column("Đường dẫn (Path)", style="white")
    table.add_column("Phân loại", style="green")

    for idx, path in enumerate(sys.path, start=1):
        if "site-packages" in path:
            category = "[bold green]Virtualenv Packages[/bold green]"
        elif ".venv" in path:
            category = "[bold blue]Virtualenv Core[/bold blue]"
        else:
            category = "[dim]Standard Library / System[/dim]"
        table.add_row(str(idx), path, category)

    console.print(table)


if __name__ == "__main__":
    main()
```
Chạy thử bằng lệnh: `uv run inspect_runtime.py`.
</details>

---

### Bài tập 3: Cấu hình VS Code Workspace và kiểm tra tự động Format
Tạo file `.vscode/settings.json` trong project của bạn. Viết một đoạn code Python cố tình vi phạm chuẩn formatting (ví dụ: dòng code quá dài, thụt lề lộn xộn, imports không theo thứ tự bảng chữ cái). Nhấn `Ctrl + S` để lưu và quan sát Ruff tự động căn chỉnh code trong nháy mắt.

<details>
<summary>💡 Gợi ý</summary>

Tạo file `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```
Tạo file thử nghiệm `messy.py`:
```python
import sys
import os
from pydantic import BaseModel
import json

def calculate_something(x:int,y:int)->int:
    return x+y
```
Khi bạn nhấn lưu file (`Ctrl + S`), Ruff sẽ tự động sắp xếp lại thứ tự import (stdlib trước, third-party sau) và thêm khoảng trắng chuẩn PEP 8: `def calculate_something(x: int, y: int) -> int: return x + y`.
</details>

---

## ✅ Checklist tự đánh giá

Hãy rà soát lại các mục dưới đây trước khi chuyển sang bài tiếp theo:

- [ ] Tôi đã cài đặt thành công `uv` trên máy và kiểm tra được phiên bản bằng lệnh `uv --version`.
- [ ] Tôi hiểu tại sao Python cần Virtual Environment (`.venv`) và sự khác biệt về cơ chế nạp thư viện giữa .NET (Global assembly/MSBuild) và Python (`sys.path`).
- [ ] Tôi biết cách khởi tạo project bằng `uv init`, thêm dependency bằng `uv add`, và chạy script bằng `uv run`.
- [ ] Tôi hiểu rõ vai trò của `pyproject.toml` và sự quan trọng của việc commit `uv.lock` vào kho mã nguồn Git.
- [ ] Tôi đã cài đặt các extension Python, Pylance, Ruff trên VS Code và cấu hình tính năng tự động format-on-save.

---

## 🔗 Đọc thêm

- [Tài liệu chính thức của Astral uv](https://docs.astral.sh/uv/): Hướng dẫn toàn diện về CLI, quản lý dự án, dependency resolution và build toolchain.
- [Tài liệu chính thức của Ruff](https://docs.astral.sh/ruff/): Danh sách toàn bộ các rules linter và quy tắc format của Ruff.
- [Hướng dẫn cấu hình Python trong VS Code](https://code.visualstudio.com/docs/python/python-tutorial): Tài liệu chính thức từ Microsoft về cách làm việc với Python trên VS Code.
- [PEP 621 – Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/): Quy chuẩn cấu trúc metadata cho dự án Python hiện đại.
- [PEP 405 – Python Virtual Environments](https://peps.python.org/pep-0405/): Đặc tả kỹ thuật về cơ chế hoạt động của Virtual Environment.

<!-- nav:bottom -->
---

[⬅️ Getting Started](./README.md) | [📚 Mục lục Getting Started](./README.md) | [Python cho dev C# ➡️](./02-python-for-csharp-devs.md)
<!-- /nav:bottom -->
