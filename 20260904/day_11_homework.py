"""Day 11 作业正确答案：对象协议、MRO、组合与值对象。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from functools import total_ordering
from typing import Protocol, overload


# 六十七、Day 11 作业 1
# 给 Order 实现 __len__，使 len(order) 返回商品行数。
#
# 六十八、作业 2
# 实现 __iter__，支持：for item in order: print(item.sku)
#
# 六十九、作业 3
# 实现 __contains__，支持 "SKU001" in order；忽略 SKU 前后空格和大小写，
# 因此 " sku001 " in order 也应该返回 True。
#
# 七十、作业 4
# 实现 __getitem__，支持 order[0] 和 order[0:2]，类型提示尽量正确。
#
# 七十一、作业 5
# 实现 @dataclass(frozen=True, slots=True) 的 OrderKey，字段为 site_id: int、
# order_no: str。验证 key1 == key2、hash 相等，并放入 set 去重。
#
# 七十二、作业 6：MRO
# 写 A、B(A)、C(A)、D(B, C)，每个类实现 process() 并使用
# super().process()；打印 D.mro()，观察执行顺序。这题必须亲手跑。
#
# 七十三、作业 7：组合
# 定义 OrderRepository、Cache、Notifier 三个 Protocol；OrderService 通过
# __init__ 接收 repository、cache、notifier，不要使用多继承。
#
# 七十四、加分作业：Money 值对象
# 实现 @dataclass(frozen=True, slots=True) 的 Money，字段 amount: Decimal；
# 支持 +、==、<、str、repr，并按 ROUND_HALF_UP 自动保留两位小数。


@dataclass(slots=True)
class OrderItem:
    sku: str
    price: Decimal
    quantity: int

    @property
    def amount(self) -> Decimal:
        return self.price * self.quantity


@dataclass(slots=True)
class Order:
    """让订单自然支持 len、for、in、索引和切片。"""

    site_id: int
    order_id: int
    items: list[OrderItem] = field(default_factory=list)

    def __len__(self) -> int:
        # 返回商品行数，不是所有 quantity 的总和。
        return len(self.items)

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


@dataclass(frozen=True, slots=True)
class OrderKey:
    """不可变且可哈希的订单业务唯一键。"""

    site_id: int
    order_no: str


class A:
    def process(self) -> None:
        print("A")


class B(A):
    def process(self) -> None:
        print("B")
        super().process()


class C(A):
    def process(self) -> None:
        print("C")
        super().process()


class D(B, C):
    def process(self) -> None:
        print("D")
        super().process()


class OrderRepository(Protocol):
    def get_by_id(self, site_id: int, order_id: int) -> Order | None:
        ...


class Cache(Protocol):
    def get(self, site_id: int, order_id: int) -> Order | None:
        ...

    def set(self, order: Order) -> None:
        ...


class Notifier(Protocol):
    def order_loaded(self, order: Order) -> None:
        ...


class OrderService:
    """通过组合使用仓储、缓存和通知器，不使用多继承。"""

    def __init__(
        self,
        repository: OrderRepository,
        cache: Cache,
        notifier: Notifier,
    ) -> None:
        self.repository = repository
        self.cache = cache
        self.notifier = notifier

    def get_order(self, site_id: int, order_id: int) -> Order | None:
        order = self.cache.get(site_id, order_id)
        if order is not None:
            return order

        order = self.repository.get_by_id(site_id, order_id)
        if order is None:
            return None

        self.cache.set(order)
        self.notifier.order_loaded(order)
        return order


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """自动按 ROUND_HALF_UP 保留两位小数的不可变金额值对象。"""

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


class MemoryRepository:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = {(order.site_id, order.order_id): order for order in orders}

    def get_by_id(self, site_id: int, order_id: int) -> Order | None:
        return self._orders.get((site_id, order_id))


class MemoryCache:
    def __init__(self) -> None:
        self._orders: dict[tuple[int, int], Order] = {}

    def get(self, site_id: int, order_id: int) -> Order | None:
        return self._orders.get((site_id, order_id))

    def set(self, order: Order) -> None:
        self._orders[(order.site_id, order.order_id)] = order


class RecordingNotifier:
    def __init__(self) -> None:
        self.loaded_order_ids: list[int] = []

    def order_loaded(self, order: Order) -> None:
        self.loaded_order_ids.append(order.order_id)


def run_self_check() -> None:
    order = Order(
        site_id=2,
        order_id=1,
        items=[
            OrderItem("SKU001", Decimal("1.00"), 2),
            OrderItem("SKU002", Decimal("3.00"), 4),
        ],
    )

    assert len(order) == 2
    assert [item.sku for item in order] == ["SKU001", "SKU002"]
    assert " sku001 " in order
    assert "SKU003" not in order
    assert order[0].sku == "SKU001"
    assert [item.sku for item in order[:2]] == ["SKU001", "SKU002"]

    key1 = OrderKey(2, "ORD001")
    key2 = OrderKey(2, "ORD001")
    key3 = OrderKey(2, "ORD002")
    assert key1 == key2
    assert hash(key1) == hash(key2)
    assert len({key1, key2, key3}) == 2

    assert [cls.__name__ for cls in D.mro()] == ["D", "B", "C", "A", "object"]

    cache = MemoryCache()
    notifier = RecordingNotifier()
    service = OrderService(MemoryRepository([order]), cache, notifier)
    assert service.get_order(2, 1) is order
    assert service.get_order(2, 1) is order
    assert notifier.loaded_order_ids == [1]  # 第二次命中缓存，不重复通知。

    money1 = Money(Decimal("10.125"))
    money2 = Money(Decimal("2.00"))
    assert str(money1) == "10.13"
    assert money1 + money2 == Money(Decimal("12.13"))
    assert money2 < money1
    assert hash(Money(Decimal("10.125"))) == hash(money1)

    print("MRO:", " -> ".join(cls.__name__ for cls in D.mro()))
    D().process()
    print("Day 11 作业验收通过")


if __name__ == "__main__":
    run_self_check()
