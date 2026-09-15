"""Day 11：面向对象进阶、魔术方法、MRO 与对象协议。

学习目标
========
1. 理解 Python 语法与特殊方法之间的对应关系。
2. 正确实现字符串表示、相等、哈希、容器协议和运算符重载。
3. 理解 ``super()`` 按 MRO（方法解析顺序）继续查找，而不是固定调用直接父类。
4. 区分普通继承、Mixin、Protocol 与组合。

一、对象协议
------------
很多 Python 语法会转而调用对象的特殊方法：

* ``str(obj)`` -> ``obj.__str__()``
* ``repr(obj)`` -> ``obj.__repr__()``
* ``len(obj)`` -> ``obj.__len__()``
* ``x in obj`` -> ``obj.__contains__(x)``
* ``for x in obj`` -> ``obj.__iter__()``
* ``obj[index]`` -> ``obj.__getitem__(index)``
* ``left + right`` -> ``left.__add__(right)``

实现这些方法的目的不是炫技，而是让对象的行为符合语言直觉。例如，
``len(order)`` 表示订单的商品行数、``"SKU001" in order`` 表示订单是否包含
该 SKU，都属于自然且清晰的语义。

二、相等与哈希
--------------
如果 ``a == b``，就必须保证 ``hash(a) == hash(b)``。哈希值依赖的字段在对象
进入 set 或成为 dict key 后不应再变化，因此业务唯一键适合设计成
``@dataclass(frozen=True, slots=True)`` 的不可变值对象。

三、MRO 与 super
----------------
Python 支持多继承。``super().method()`` 表示沿当前类的 MRO 查找下一个实现。
在菱形继承 ``D(B, C)`` 中，下面示例的顺序是 ``D -> B -> C -> A -> object``；
只要各层合作式地调用 ``super()``，共同祖先 A 就只会执行一次。

四、继承、Mixin、Protocol 与组合
--------------------------------
* 普通继承表达 is-a，例如 ``OrderNotFoundError is an OrderError``。
* Mixin 提供可复用的横向小能力，例如 JSON 序列化或日志；它通常不单独实例化。
* Protocol 描述对象“需要具备什么能力”，通常不提供具体业务实现。
* 组合表达 has-a 或依赖关系，例如 ``OrderService has a Repository``。

完整组件（数据库仓储、缓存、HTTP 客户端、通知器）应优先通过组合注入。Mixin
应保持职责单一，避免复杂状态和方法名冲突。

复习重点
--------
* ``__repr__`` 面向开发者和调试，``__str__`` 面向用户展示。
* 不支持的比较或运算类型应返回 ``NotImplemented``。
* ``dataclass`` 默认生成 init、repr 和 eq；frozen、slots、order 会改变更多协议。
* 没有 ``__bool__`` 时，Python 可以退回使用 ``__len__`` 判断真假。
* 只有语义稳定、自然时才实现比较和运算符重载。
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from functools import total_ordering
from typing import Protocol, overload


# ---------------------------------------------------------------------------
# 1. 容器协议：让 Order 支持 len、for、in、索引和切片
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrderItem:
    sku: str
    price: Decimal
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity 必须是正整数")

    @property
    def amount(self) -> Decimal:
        return self.price * self.quantity


@dataclass(slots=True)
class Order:
    order_no: str
    items: list[OrderItem] = field(default_factory=list)

    def __len__(self) -> int:
        """返回商品行数，而不是 quantity 之和。"""
        return len(self.items)

    def __bool__(self) -> bool:
        """订单有商品时为真。只有业务语义明确时才应这样定义。"""
        return bool(self.items)

    def __iter__(self) -> Iterator[OrderItem]:
        return iter(self.items)

    def __contains__(self, sku: object) -> bool:
        if not isinstance(sku, str):
            return False
        target = sku.strip().upper()
        return any(item.sku.strip().upper() == target for item in self.items)

    @overload
    def __getitem__(self, index: int) -> OrderItem:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[OrderItem]:
        ...

    def __getitem__(self, index: int | slice) -> OrderItem | list[OrderItem]:
        return self.items[index]

    @property
    def total_amount(self) -> Decimal:
        return sum((item.amount for item in self.items), Decimal("0.00"))

    def __str__(self) -> str:
        return f"订单 {self.order_no}（{len(self)} 个商品行）"


# ---------------------------------------------------------------------------
# 2. 不可变业务键与金额值对象
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OrderKey:
    site_id: int
    order_no: str


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """按 ROUND_HALF_UP 规则保留两位小数的金额值对象。"""

    amount: Decimal

    def __post_init__(self) -> None:
        normalized = Decimal(str(self.amount)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        if not normalized.is_finite():
            raise ValueError("金额必须是有限数值")
        object.__setattr__(self, "amount", normalized)

    def __add__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __str__(self) -> str:
        return f"{self.amount:.2f}"

    def __repr__(self) -> str:
        return f"Money(amount=Decimal('{self.amount:.2f}'))"


# ---------------------------------------------------------------------------
# 3. MRO：super() 沿方法解析顺序继续查找
# ---------------------------------------------------------------------------


class A:
    def process(self) -> list[str]:
        return ["A"]


class B(A):
    def process(self) -> list[str]:
        return ["B", *super().process()]


class C(A):
    def process(self) -> list[str]:
        return ["C", *super().process()]


class D(B, C):
    def process(self) -> list[str]:
        return ["D", *super().process()]


# ---------------------------------------------------------------------------
# 4. Mixin：提供小而可复用的横向能力
# ---------------------------------------------------------------------------


class JsonMixin:
    """为 dataclass 提供 JSON 序列化能力，不代表独立业务对象。"""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


@dataclass(slots=True)
class OrderSnapshot(JsonMixin):
    order_no: str
    status: str


# ---------------------------------------------------------------------------
# 5. Protocol + 组合：把完整依赖注入 OrderService
# ---------------------------------------------------------------------------


class OrderRepository(Protocol):
    def get_by_no(self, order_no: str) -> Order | None:
        ...


class Cache(Protocol):
    def get(self, order_no: str) -> Order | None:
        ...

    def set(self, order: Order) -> None:
        ...


class Notifier(Protocol):
    def order_loaded(self, order: Order) -> None:
        ...


class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        cache: Cache,
        notifier: Notifier,
    ) -> None:
        self.repository = repository
        self.cache = cache
        self.notifier = notifier

    def get_order(self, order_no: str) -> Order | None:
        cached = self.cache.get(order_no)
        if cached is not None:
            return cached

        order = self.repository.get_by_no(order_no)
        if order is None:
            return None

        self.cache.set(order)
        self.notifier.order_loaded(order)
        return order


class MemoryRepository:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = {order.order_no: order for order in orders}

    def get_by_no(self, order_no: str) -> Order | None:
        return self._orders.get(order_no)


class MemoryCache:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def get(self, order_no: str) -> Order | None:
        return self._orders.get(order_no)

    def set(self, order: Order) -> None:
        self._orders[order.order_no] = order


class RecordingNotifier:
    def __init__(self) -> None:
        self.loaded: list[str] = []

    def order_loaded(self, order: Order) -> None:
        self.loaded.append(order.order_no)


def main() -> None:
    """运行关键示例和断言，便于复查讲义是否仍然正确。"""
    order = Order(
        order_no="A001",
        items=[
            OrderItem("SKU001", Decimal("100.00"), 2),
            OrderItem("SKU002", Decimal("50.00"), 1),
        ],
    )
    assert len(order) == 2
    assert bool(order)
    assert " sku001 " in order
    assert order[0].sku == "SKU001"
    assert len(order[:2]) == 2
    assert order.total_amount == Decimal("250.00")

    key1 = OrderKey(1, "A001")
    key2 = OrderKey(1, "A001")
    assert key1 == key2 and hash(key1) == hash(key2)
    assert len({key1, key2}) == 1

    assert Money(Decimal("10.125")) == Money(Decimal("10.13"))
    assert Money(Decimal("1.00")) + Money(Decimal("2.00")) == Money(Decimal("3.00"))
    assert Money(Decimal("1.00")) < Money(Decimal("2.00"))

    assert [cls.__name__ for cls in D.mro()] == ["D", "B", "C", "A", "object"]
    assert D().process() == ["D", "B", "C", "A"]

    snapshot = OrderSnapshot("A001", "PAID")
    assert snapshot.to_json() == '{"order_no": "A001", "status": "PAID"}'

    notifier = RecordingNotifier()
    service = OrderService(MemoryRepository([order]), MemoryCache(), notifier)
    assert service.get_order("A001") is order
    assert service.get_order("A001") is order
    assert notifier.loaded == ["A001"]

    print(order)
    print("MRO:", " -> ".join(cls.__name__ for cls in D.mro()))
    print("Day 11 示例检查通过")


if __name__ == "__main__":
    main()
