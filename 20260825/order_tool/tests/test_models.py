from dataclasses import dataclass
from decimal import Decimal

from order_tool.cleaner import parse_quantity, parse_status, clean_order
from order_tool.models import normalize_money, Order, OrderStatus


def test_normalize_money() -> None:
    result = normalize_money(
        Decimal("100.126")
    )
    assert result == Decimal("100.13")



# def test_error() -> None:
#     assert 1 + 1 == 3



import pytest
from decimal import Decimal
# pytest.mark.parametrize
@pytest.mark.parametrize(
    ("input_amount", "expected"),
    [
        (
            Decimal("100.126"),
            Decimal("100.13"),
        ),
        (
            Decimal("100.124"),
            Decimal("100.12"),
        ),
        (
            Decimal("10"),
            Decimal("10.00"),
        ),
    ],
)
def test_normalize_money(
    input_amount: Decimal,
    expected: Decimal,
) -> None:
    assert normalize_money(input_amount) == expected



@dataclass(slots=True, kw_only=True)
class OrderItem:
    sku: str
    price: Decimal
    quantity: int

def test_order_item_should_normalize_data() -> None:
    item = OrderItem(
        sku=" sku001 ",
        price=Decimal("100.126"),
        quantity=2,
    )

    assert item.sku == "SKU001"
    assert item.price == Decimal("100.13")
    assert item.quantity == 2
    assert item.amount == Decimal("200.26")



# import pytest
# def test_order_item_empty_sku_should_raise() -> None:
#     with pytest.raises(ValueError):
#         OrderItem(
#             sku="",
#             price=Decimal("100"),
#             quantity=1,
#         )



def test_order_item_empty_sku_should_raise() -> None:
    with pytest.raises(
        ValueError,
        match="SKU不能为空",
    ):
        OrderItem(
            sku="",
            price=Decimal("100"),
            quantity=1,
        )



@pytest.mark.parametrize(
    ("price", "quantity"),
    [
        (Decimal("0"), 1),
        (Decimal("-1"), 1),
        (Decimal("100"), 0),
        (Decimal("100"), -1),
    ],
)
def test_order_item_invalid_data_should_raise(
    price: Decimal,
    quantity: int,
) -> None:
    with pytest.raises(ValueError):
        OrderItem(
            sku="SKU001",
            price=price,
            quantity=quantity,
        )


# fixture 的生命周期 @pytest.fixture
# 默认：每个测试函数重新创建一次
#
# 模块级共享：@pytest.fixture(scope="module")

# 整个测试会话共享：@pytest.fixture(scope="session")

# 执行流程：
#
# pytest
#   ↓
# 发现 test_order_can_pay 需要 unpaid_order
#   ↓
# 自动执行 fixture
#   ↓
# Order.create_unpaid("A001")
#   ↓
# 创建 status=UNPAID 的订单
#   ↓
# 把订单注入 test_order_can_pay
#   ↓
# unpaid_order.pay()
#   ↓
# UNPAID → PAID
#   ↓
# assert 验证成功
import pytest
@pytest.fixture
def unpaid_order() -> Order:
    return Order.create_unpaid("A001")

def test_order_can_pay(
    unpaid_order: Order,
) -> None:
    unpaid_order.pay()

    assert unpaid_order.status == OrderStatus.PAID



# Day 6 有：
# def parse_quantity(value: object) -> int | None:
# 这是非常适合参数化测试的函数：
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (2, 2),
        ("2", 2),
        (" 3 ", 3),
        (None, None),
        ("abc", None),
        (0, None),
        (-1, None),
        ("2.5", None),
        (2.5, None),
        (True, None),
    ],
)
def test_parse_quantity(
    value: object,
    expected: int | None,
) -> None:
    assert parse_quantity(value) == expected



# 测试 parse_status
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("PAID", OrderStatus.PAID),
        (" paid ", OrderStatus.PAID),
        ("Unpaid", OrderStatus.UNPAID),
        ("UNKNOWN", None),
        (None, None),
        ("", None),
    ],
)
def test_parse_status(
    value: object,
    expected: OrderStatus | None,
) -> None:
    assert parse_status(value) == expected



# 测试 clean_order
def test_clean_order_should_create_order() -> None:
    raw_order = {
        "order_no": " a001 ",
        "sku": " sku001 ",
        "price": "100.126",
        "quantity": "2",
        "status": " paid ",
    }

    result = clean_order(raw_order)

    assert result is not None
    assert result.order_no == "A001"
    assert result.sku == "SKU001"
    assert result.price == Decimal("100.13")
    assert result.quantity == 2
    assert result.status == OrderStatus.PAID
    assert result.amount == Decimal("200.26")



# 什么时候测试返回 None，什么时候测试 raise，这个问题非常重要。

# 比如：
# parse_quantity("abc")

# 设计上非法外部输入属于正常可预期情况：
#
# return None
#
# 所以测试：
#
# assert result is None
#
# 但领域对象：
#
# OrderItem(
#     sku="",
#     ...
# )
#
# 说明代码已经试图创建非法领域对象。
#
# 应该：
#
# raise ValueError
#
# 所以测试：
#
# with pytest.raises(ValueError):



# 可以形成一个边界：
#
# 外部输入解析层：
# 容忍错误 → None / 错误结果
#
# 核心领域层：
# 不允许非法状态存在 → raise
#
# 这个思想非常重要。



# 你的项目应该形成这条数据链
# 外部 JSON
#    ↓
# dict[str, Any]
#    ↓
# parse / clean
#    ↓
# Order / OrderItem
#    ↓
# 领域逻辑
#    ↓
# CSV / API / DB
#
# 原则：
#
# 越靠近外部边界，越需要容错；越进入核心领域，类型和约束越应该严格。
#
# 这就是你以后做 FastAPI、RAG、Agent、数据平台都能复用的思想。


# conftest.py
# 当 fixture 很多时，不要都放在每个测试文件里。
#
# pytest 特殊文件：
#
# tests/conftest.py
#
# 例如：
#
# import pytest
#
# from order_tool.models import Order
#
#
# @pytest.fixture
# def unpaid_order() -> Order:
#     return Order.create_unpaid("A001")
#
# 其他测试文件可以直接：
#
# def test_order_can_pay(
#     unpaid_order: Order,
# ) -> None:
#     ...
#
# 不需要 import fixture。
#
# pytest 会自动发现。



# 测试文件命名
#
# 推荐：
#
# src/order_tool/models.py
# ↓
# tests/test_models.py
# src/order_tool/cleaner.py
# ↓
# tests/test_cleaner.py
#
# 结构形成对应关系：
#
# 源代码模块
# ↕
# 测试模块



# 运行部分测试
#
# 全部：
#
# pytest
#
# 详细：
#
# pytest -v
#
# 只测一个文件：
#
# pytest tests/test_cleaner.py
#
# 只测一个函数：
#
# pytest tests/test_cleaner.py::test_parse_quantity
#
# 失败时显示更详细输出：
#
# pytest -vv



# -s 是什么
#
# pytest 默认会捕获 print() 输出。
#
# 如果你想看到：
#
# print(...)
#
# 可以：
#
# pytest -s
#
# 或者：
#
# pytest -v -s
#
# 不过真正测试里不要依赖 print。



# 测试覆盖率是什么
#
# 假设：
#
# def parse_quantity(...):
#
# 有：
#
# 10 条代码路径
#
# 测试只执行了其中 3 条。
#
# 覆盖率大约说明：
#
# 有多少代码被测试执行过。
#
# 但注意：
#
# 100% 覆盖率 ≠ 代码一定正确。
#
# 覆盖率只是辅助指标。
#
# 后面会学：
#
# pytest-cov
#
# 现在先知道概念。