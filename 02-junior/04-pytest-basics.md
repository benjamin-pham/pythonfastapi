<!-- nav:top -->
[🏠 Home](../README.md) › [Junior](./README.md) › Bài 04
<!-- /nav:top -->

# pytest cơ bản

> ⏱️ Thời lượng: ~3.0 giờ · 📌 Yêu cầu trước: Đã hoàn thành [Bài 03: Typing nâng cao & mypy](./03-advanced-typing-mypy.md).

---

## 🎯 Mục tiêu

Sau khi hoàn thành bài học này, bạn sẽ:

- Hiểu rõ vì sao **`pytest`** trở thành tiêu chuẩn vàng vượt trội so với `unittest` truyền thống nhờ cơ chế **Assert Rewriting** thông minh.
- Nắm vững mô hình chuẩn **Arrange – Act – Assert (AAA)** khi xây dựng các ca kiểm thử đơn vị (Unit Test).
- Sử dụng thành thạo **`@pytest.fixture`**, phân biệt các phạm vi tồn tại (**fixture scopes**: `function`, `class`, `module`, `package`, `session`) và mô hình dọn dẹp tài nguyên (**teardown**) bằng từ khóa `yield`.
- Áp dụng kỹ thuật kiểm thử tham số hóa (**Parametrized Testing**) với **`@pytest.mark.parametrize`**, đối chiếu với `[Theory]` và `[InlineData]` trong xUnit của C#.
- Bắt và kiểm tra chính xác các ngoại lệ với khối ngữ cảnh **`with pytest.raises(...)`**.
- Khai thác 2 built-in fixtures quan trọng nhất: **`tmp_path`** (thao tác file tạm cô lập) và **`monkeypatch`** (giả lập biến môi trường và hàm hệ thống).

---

## 🔁 So sánh với C# / ASP.NET

Trong thế giới .NET, bạn đã quen thuộc với **xUnit**, **NUnit**, hoặc **MSTest** kết hợp với các thư viện Mocking như Moq/NSubstitute và AutoFixture. Khi chuyển sang Python, `pytest` mang lại trải nghiệm viết test tự nhiên, ngắn gọn và linh hoạt hơn rất nhiều:

| Khái niệm / Thao tác | C# (xUnit / NUnit) | Python (`pytest`) |
|---|---|---|
| **Khai báo Test Case** | `[Fact]` hoặc `[Test]` đặt trên method của Test Class | Hàm bắt đầu bằng tiền tố `test_*` (không cần Class bọc ngoài) |
| **Câu lệnh kiểm tra (Assertion)** | `Assert.Equal(expected, actual);` hoặc `actual.Should().Be(expected);` | Câu lệnh `assert actual == expected` nguyên bản của Python |
| **Thông điệp khi test fail** | Thư viện tự format theo method Assert | **Assert Rewriting**: Pytest tự dịch cú pháp AST để in chi tiết giá trị từng vế |
| **Kiểm thử tham số hóa** | `[Theory]` kết hợp `[InlineData(1, 2, 3)]` | `@pytest.mark.parametrize("a, b, expected", [...])` |
| **Chuẩn bị dữ liệu / Dependency** | Constructor của Class hoặc `[SetUp]` trong NUnit | `@pytest.fixture` (được inject tự động theo tên tham số của hàm test) |
| **Dọn dẹp sau test (Teardown)** | `IDisposable.Dispose()` hoặc `[TearDown]` | Lệnh `yield` bên trong `@pytest.fixture` |
| **Phạm vi tái sử dụng fixture** | Class Fixture / Collection Fixture (`IClassFixture<T>`) | Tham số `scope`: `"function"`, `"module"`, `"session"` |
| **Kiểm tra ngoại lệ** | `Assert.Throws<ArgumentException>(() => ...)` | `with pytest.raises(ArgumentException) as exc_info:` |
| **Thư mục tạm cô lập** | Tự tạo qua `Path.GetTempPath()` và dọn thủ công | Built-in fixture `tmp_path` (đối tượng `pathlib.Path` tự hủy) |
| **Mock biến môi trường / hàm** | Thư viện Mocking bên ngoài hoặc TestServer | Built-in fixture `monkeypatch` |

---

## 📖 Lý thuyết

### 1. Triết lý của pytest: Sức mạnh của Assert Rewriting

Trong thư viện `unittest` tiêu chuẩn (vốn được mô phỏng theo JUnit của Java những năm 2000), bạn phải tạo class kế thừa `unittest.TestCase` và gọi hàng chục phương thức cồng kềnh: `self.assertEqual()`, `self.assertTrue()`, `self.assertIn()`.

Với `pytest`:
1. Bạn chỉ cần viết các hàm thuần túy với tiền tố `test_`.
2. Bạn chỉ cần dùng đúng một từ khóa duy nhất: **`assert <biểu_thức_boolean>`**.

#### Cơ chế Assert Rewriting hoạt động thế nào?
Khi pytest phát hiện các tệp test, nó không chạy bytecode thông thường mà can thiệp vào cây cú pháp trừu tượng (**Abstract Syntax Tree - AST**) của file test trước khi thực thi. Nếu câu lệnh `assert` bị sai, pytest tự động bóc tách giá trị cụ thể của từng biến trong biểu thức và hiển thị trực quan:

```python
def test_user_filtering():
    users = ["alice", "bob", "charlie"]
    # Nếu assert thất bại, pytest sẽ in rõ:
    # E   AssertionError: assert 'david' in ['alice', 'bob', 'charlie']
    assert "david" in users
```

### 2. Cấu trúc Arrange – Act – Assert (AAA)

Tương tự như trong kiểm thử phần mềm chuyên nghiệp với C#, mọi bài test trong `pytest` đều nên tuân thủ nghiêm ngặt 3 bước:
1. **Arrange (Chuẩn bị)**: Khởi tạo dữ liệu mẫu, thiết lập mock, tạo đối tượng cần test.
2. **Act (Hành động)**: Gọi phương thức hoặc hàm cần kiểm thử.
3. **Assert (Kiểm tra)**: Khẳng định kết quả trả về hoặc trạng thái hệ thống phải khớp với kỳ vọng.

```python
def test_calculate_discount_price():
    # 1. Arrange: Chuẩn bị giá ban đầu và % chiết khấu
    original_price = 200_000.0
    discount_rate = 0.15  # 15%

    # 2. Act: Thực hiện tính toán
    final_price = original_price * (1 - discount_rate)

    # 3. Assert: Kiểm tra kết quả
    assert final_price == 170_000.0
```

### 3. `@pytest.fixture`: Cơ chế Dependency Injection trong Testing

Trong xUnit / NUnit, bạn phải khởi tạo đối tượng trong Constructor hoặc viết các class `Fixture` khá nặng nề. Trong pytest, **Fixture** là trái tim của toàn bộ hệ thống test.

Một fixture là một hàm được đánh dấu bởi `@pytest.fixture`. Khi một hàm test khai báo tham số trùng tên với fixture, pytest sẽ:
1. Thực thi hàm fixture trước.
2. Lấy giá trị trả về của fixture và truyền trực tiếp vào hàm test.

```python
import pytest


@pytest.fixture
def default_user() -> dict[str, str]:
    """Fixture cung cấp đối tượng user mẫu cho các test."""
    return {"id": "usr_01", "name": "Nguyen Van A", "role": "admin"}


def test_user_has_admin_role(default_user: dict[str, str]):
    # default_user được tự động inject vào hàm test
    assert default_user["role"] == "admin"
    assert default_user["name"] == "Nguyen Van A"
```

#### Fixture Scopes (Phạm vi hoạt động)
Mặc định, mỗi hàm fixture được chạy lại một lần cho mỗi hàm test (**`scope="function"`**). Bạn có thể thay đổi phạm vi tồn tại của fixture để tiết kiệm thời gian khởi tạo (ví dụ: kết nối Database test hoặc nạp file dữ liệu lớn):

- **`function`** (Mặc định): Chạy lại trước mỗi bài test riêng lẻ. Đảm bảo tính cô lập tuyệt đối giữa các test.
- **`class`**: Chạy một lần duy nhất cho toàn bộ các test method trong cùng một class.
- **`module`**: Chạy một lần duy nhất cho toàn bộ các test nằm trong cùng một tệp `.py`.
- **`package`**: Chạy một lần cho toàn bộ package.
- **`session`**: Chạy đúng một lần duy nhất trong toàn bộ chu kỳ chạy `pytest` từ đầu đến cuối. Thích hợp cho việc khởi động Docker TestContainer hoặc chạy migrations.

```python
@pytest.fixture(scope="session")
def database_engine():
    """Khởi tạo một lần cho cả phiên test."""
    engine = create_test_engine()
    return engine
```

### 4. Quản lý vòng đời Teardown với `yield` trong Fixture

Một fixture có thể vừa làm nhiệm vụ chuẩn bị (**Setup**), vừa làm nhiệm vụ dọn dẹp (**Teardown**) bằng cách sử dụng từ khóa **`yield`**:
- Mọi đoạn code **trước `yield`** chạy trước khi test bắt đầu.
- Giá trị nằm sau **`yield`** được inject vào hàm test.
- Mọi đoạn code **sau `yield`** sẽ được pytest tự động chạy sau khi hàm test hoàn tất (ngay cả khi test đó bị FAIL!).

```python
@pytest.fixture
def temp_database_table():
    print("\n🟢 [SETUP] Tạo bảng tạm trong Database test...")
    table_name = "test_orders_temp"

    yield table_name  # Truyền table_name vào hàm test

    print(f"\n🔴 [TEARDOWN] Xóa bảng tạm '{table_name}' để dọn dẹp...")
```

### 5. Tham số hóa bài test với `@pytest.mark.parametrize`

Thay vì sao chép 5 bài test giống hệt nhau chỉ khác dữ liệu đầu vào và kết quả đầu ra, bạn hãy dùng `@pytest.mark.parametrize` (tương đương `[Theory]` + `[InlineData]` trong xUnit):

```python
import pytest


def is_valid_vietnam_phone(phone: str) -> bool:
    """Kiểm tra số điện thoại di động Việt Nam hợp lệ (10 chữ số, bắt đầu bằng 0)."""
    return len(phone) == 10 and phone.isdigit() and phone.startswith("0")


@pytest.mark.parametrize(
    "phone_input, expected",
    [
        ("0912345678", True),  # Số hợp lệ
        ("0987654321", True),  # Số hợp lệ
        ("012345678", False),  # Thiếu chữ số (9 số)
        ("1912345678", False),  # Không bắt đầu bằng 0
        ("091234567a", False),  # Chứa ký tự chữ
    ],
)
def test_phone_validation(phone_input: str, expected: bool):
    assert is_valid_vietnam_phone(phone_input) == expected
```

Khi chạy, pytest sẽ coi mỗi cặp tham số là một test case độc lập, hiển thị rõ ca nào PASS, ca nào FAIL!

### 6. Kiểm tra ngoại lệ với `pytest.raises`

Tương đương với `Assert.Throws<TException>()` trong C#, bạn sử dụng khối ngữ cảnh `with pytest.raises(ExceptionClass) as exc_info:`:

```python
import pytest


def withdraw_money(balance: float, amount: float) -> float:
    if amount <= 0:
        raise ValueError("Số tiền rút phải lớn hơn 0!")
    if amount > balance:
        raise InsufficientFundsError("Số dư tài khoản không đủ để thực hiện giao dịch!")
    return balance - amount


class InsufficientFundsError(Exception):
    pass


def test_withdraw_insufficient_funds():
    with pytest.raises(InsufficientFundsError) as exc_info:
        withdraw_money(balance=100_000, amount=500_000)

    # Kiểm tra thông điệp lỗi nếu cần
    assert "Số dư tài khoản không đủ" in str(exc_info.value)


def test_withdraw_negative_amount_matching():
    # Sử dụng tham số match để kiểm tra chuỗi regex trong exception message
    with pytest.raises(ValueError, match="phải lớn hơn 0"):
        withdraw_money(balance=100_000, amount=-50_000)
```

### 7. Hai Built-in Fixtures thiết yếu: `tmp_path` và `monkeypatch`

#### a. `tmp_path`: Tạo thư mục và file tạm cô lập
`tmp_path` cung cấp một đối tượng `pathlib.Path` trỏ tới một thư mục tạm độc nhất được tạo riêng cho bài test đó. Bạn không bao giờ phải lo lắng về việc tạo file rác đè lên nhau hay phải viết code dọn dẹp thủ công:

```python
from pathlib import Path
import json


def save_user_profile(directory: Path, profile: dict) -> Path:
    file_path = directory / "profile.json"
    file_path.write_text(json.dumps(profile), encoding="utf-8")
    return file_path


def test_save_user_profile(tmp_path: Path):
    # tmp_path là thư mục tạm tự sinh
    data = {"username": "linh_dev", "score": 100}
    created_file = save_user_profile(tmp_path, data)

    assert created_file.exists()
    assert json.loads(created_file.read_text(encoding="utf-8")) == data
```

#### b. `monkeypatch`: Giả lập biến môi trường và thuộc tính động
`monkeypatch` cho phép bạn tạm thời sửa đổi biến môi trường, thuộc tính của module hoặc phương thức của class chỉ trong phạm vi bài test:

```python
import os
import pytest


def get_database_url() -> str:
    """Đọc URL kết nối từ biến môi trường."""
    return os.getenv("DATABASE_URL", "sqlite:///default.db")


def test_custom_database_url(monkeypatch: pytest.MonkeyPatch):
    # Ghi đè biến môi trường DATABASE_URL chỉ cho bài test này
    test_db_url = "postgresql://test_user:pass@localhost:5432/test_db"
    monkeypatch.setenv("DATABASE_URL", test_db_url)

    assert get_database_url() == test_db_url
```

---

## 💻 Ví dụ thực hành

Dưới đây là một bộ kiểm thử hoàn chỉnh cho một dịch vụ đặt hàng trực tuyến (**Order Processing Service**), áp dụng đầy đủ Fixture, Teardown, Parametrize, `tmp_path`, và `monkeypatch`:

```python
from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path
import pytest


# 1. Domain Entities & Business Logic
@dataclass
class OrderItem:
    sku: str
    quantity: int
    unit_price: Decimal


class OrderService:

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir

    def calculate_total(
        self, items: list[OrderItem], discount_percent: Decimal = Decimal("0.0")
    ) -> Decimal:
        if discount_percent < Decimal("0") or discount_percent > Decimal("100"):
            raise ValueError("Chiết khấu phải nằm trong khoảng 0% - 100%!")
        subtotal = sum((item.unit_price * item.quantity for item in items), Decimal("0"))
        discount_amount = subtotal * (discount_percent / Decimal("100"))
        return subtotal - discount_amount

    def export_order_receipt(self, order_id: str, total: Decimal) -> Path:
        out_file = self.storage_dir / f"{order_id}.json"
        out_file.write_text(
            json.dumps({"order_id": order_id, "total": str(total)}), encoding="utf-8"
        )
        return out_file


# 2. Test Fixtures
@pytest.fixture
def sample_items() -> list[OrderItem]:
    """Cung cấp danh sách mặt hàng mẫu."""
    return [
        OrderItem(sku="SKU-KEYBOARD", quantity=2, unit_price=Decimal("1500000")),
        OrderItem(sku="SKU-MOUSE", quantity=1, unit_price=Decimal("800000")),
    ]


@pytest.fixture
def order_service(tmp_path: Path):
    """Khởi tạo service với thư mục lưu trữ cô lập."""
    print("\n[SETUP] Khởi tạo OrderService với tmp_path")
    service = OrderService(storage_dir=tmp_path)
    yield service
    print("\n[TEARDOWN] Test kết thúc.")


# 3. Test Cases
def test_calculate_total_without_discount(
    order_service: OrderService, sample_items: list[OrderItem]
):
    # Arrange & Act
    total = order_service.calculate_total(sample_items)

    # Assert: 2 * 1,500,000 + 1 * 800,000 = 3,800,000
    assert total == Decimal("3800000")


@pytest.mark.parametrize(
    "discount, expected_total",
    [
        (Decimal("10"), Decimal("3420000")),  # Giảm 10%
        (Decimal("50"), Decimal("1900000")),  # Giảm 50%
        (Decimal("0"), Decimal("3800000")),  # Giảm 0%
    ],
)
def test_calculate_total_with_various_discounts(
    order_service: OrderService,
    sample_items: list[OrderItem],
    discount: Decimal,
    expected_total: Decimal,
):
    total = order_service.calculate_total(sample_items, discount_percent=discount)
    assert total == expected_total


def test_invalid_discount_raises_error(order_service: OrderService):
    with pytest.raises(ValueError, match="khoảng 0% - 100%"):
        order_service.calculate_total([], discount_percent=Decimal("150"))


def test_export_order_receipt_creates_valid_file(order_service: OrderService):
    order_id = "ORD-99881"
    receipt_path = order_service.export_order_receipt(order_id, Decimal("500000"))

    assert receipt_path.exists()
    content = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert content["order_id"] == order_id
    assert content["total"] == "500000"
```

---

## ⚠️ Lỗi thường gặp

### 1. Gọi trực tiếp hàm fixture thay vì inject qua tham số
Lập trình viên C# quen gọi hàm factory nên thường viết:
```python
@pytest.fixture
def my_data():
    return {"status": "ok"}


# ❌ LỖI: Tự gọi hàm fixture như hàm thông thường
# def test_something():
#     data = my_data()  # Lỗi! pytest fixture không thể gọi trực tiếp theo cách này

#  ĐÚNG: Khai báo tên fixture như một tham số của hàm test
def test_something(my_data):
    assert my_data["status"] == "ok"
```

### 2. Dùng `scope="session"` hoặc `"module"` cho fixture có trạng thái biến đổi (Mutable State)
Nếu fixture trả về một `list` hoặc `dict` và bạn sửa đổi dữ liệu bên trong bài test thứ nhất, bài test thứ hai chạy sau sẽ nhận dữ liệu đã bị biến dạng!
> [!WARNING]
> Chỉ dùng `scope="session"` hoặc `"module"` cho các tài nguyên chỉ đọc (read-only) hoặc các kết nối dùng chung đã có cơ chế reset transaction!

### 3. Dùng `return` thay vì `yield` khi cần teardown
Nếu bạn viết `return resource` rồi viết code dọn dẹp ở dưới, code dọn dẹp sẽ không bao giờ được chạm tới:
```python
@pytest.fixture
def managed_resource():
    res = create_resource()
    # ❌ SAI:
    # return res
    # cleanup_resource(res)  # Unreachable code!

    #  ĐÚNG:
    yield res
    cleanup_resource(res)
```

### 4. Quên đặt tên file test bắt đầu bằng `test_*.py`
pytest mặc định tìm kiếm các file có tên dạng `test_*.py` hoặc `*_test.py`, và các hàm dạng `test_*()`. Nếu bạn đặt tên file là `user_tests.py`, pytest sẽ bỏ qua toàn bộ và thông báo `collected 0 items`.

---

## ✍️ Bài tập thực hành

### Bài 1: Viết Unit Test cho thuật toán kiểm tra mật khẩu
Viết một hàm `validate_password(password: str) -> tuple[bool, str]` kiểm tra độ mạnh của mật khẩu:
- Độ dài tối thiểu 8 ký tự.
- Chứa ít nhất một chữ in hoa, một chữ thường, và một chữ số.
- Trả về `(True, "OK")` nếu hợp lệ, hoặc `(False, "<Lý do>")` nếu không đạt.
Sử dụng `@pytest.mark.parametrize` để viết bộ kiểm thử bao quát toàn bộ các trường hợp biên: mật khẩu quá ngắn, thiếu hoa, thiếu thường, thiếu số, và mật khẩu đạt chuẩn.

<details>
<summary>💡 Gợi ý</summary>

- Sử dụng `any(c.isupper() for c in password)`, `any(c.islower() ...)`, `any(c.isdigit() ...)`.
- Viết test với `@pytest.mark.parametrize("pwd, expected_valid", [("Abc12345", True), ("short", False), ...])`.
</details>

---

### Bài 2: Fixture quản lý Transaction cô lập với `yield`
Viết một fixture `in_memory_db` giả lập một cơ sở dữ liệu dạng từ điển:
- Trong phần Setup: Khởi tạo từ điển với 2 bản ghi người dùng mẫu: `{"u1": "Alice", "u2": "Bob"}`.
- `yield` từ điển cho bài test.
- Trong phần Teardown: Xóa sạch toàn bộ từ điển bằng `.clear()` và in log `"Đã dọn dẹp Database test"`.
- Viết 2 bài test:
  1. Test kiểm tra người dùng `u1` tồn tại.
  2. Test thêm người dùng `u3` và xóa người dùng `u2`, xác nhận từ điển thay đổi chính xác.

<details>
<summary>💡 Gợi ý</summary>

- Cấu trúc fixture:
```python
@pytest.fixture
def in_memory_db():
    db = {"u1": "Alice", "u2": "Bob"}
    yield db
    db.clear()
```
- Khai báo `in_memory_db` trong tham số của 2 hàm test `test_read_user` và `test_mutate_db`.
</details>

---

### Bài 3: Kiểm thử đọc file cấu hình với `tmp_path` và `monkeypatch`
Viết một hàm `load_application_config(config_path: Path) -> dict`:
- Đọc nội dung JSON từ `config_path`.
- Nếu biến môi trường `ENV` có giá trị `"production"`, kiểm tra xem trường `"debug"` trong config có phải là `False` hay không; nếu là `True`, ném ngoại lệ `RuntimeError("Production không được bật debug!")`.
- Viết 2 test case sử dụng kết hợp `tmp_path` (để ghi file json cấu hình mẫu) và `monkeypatch` (để thiết lập biến môi trường `ENV`):
  1. Test trường hợp config hợp lệ ở môi trường `"development"`.
  2. Test trường hợp ném `RuntimeError` khi bật debug ở môi trường `"production"`.

<details>
<summary>💡 Gợi ý</summary>

- Dùng `tmp_path / "config.json"` để tạo file test.
- Dùng `monkeypatch.setenv("ENV", "production")`.
- Dùng `with pytest.raises(RuntimeError, match="Production không được bật debug"):` để kiểm tra ngoại lệ.
</details>

---

## ✅ Checklist tự đánh giá

Sau khi hoàn thành bài này, bạn cần tự tin trả lời "Có" cho các câu hỏi sau:

- [ ] Bạn hiểu rõ nguyên lý Assert Rewriting của pytest và tại sao không cần các class/method Assert phức tạp?
- [ ] Bạn áp dụng thành thạo mô hình Arrange – Act – Assert trong mọi bài test?
- [ ] Bạn biết cách tạo fixture với `@pytest.fixture` và phân biệt rõ các scope (`function`, `module`, `session`)?
- [ ] Bạn thành thạo cơ chế Teardown dọn dẹp tài nguyên với `yield` trong fixture?
- [ ] Bạn biết cách dùng `@pytest.mark.parametrize` để rút gọn hàng loạt test case?
- [ ] Bạn sử dụng thành thạo `with pytest.raises(...)`, `tmp_path`, và `monkeypatch`?

---

## 📚 Đọc thêm

- [pytest Official Documentation – Getting Started](https://docs.pytest.org/en/stable/getting-started.html)
- [pytest Documentation – How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest Documentation – Parametrize fixtures and test functions](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [pytest Documentation – Monkeypatching and mocking](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)

<!-- nav:bottom -->
---

[⬅️ Typing nâng cao & mypy](./03-advanced-typing-mypy.md) | [📚 Mục lục Junior](./README.md) | [FastAPI đầu tiên ➡️](./05-fastapi-first-app.md)
<!-- /nav:bottom -->
