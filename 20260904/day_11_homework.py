# 六十七、Day 11 作业 1
#
# 给 Order 实现：
#
# __len__
#
# 要求：
#
# len(order)
#
# 返回：
#
# 商品行数
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, overload


@dataclass
class OrderItem:
    sku:str
    price: float
    quantity: int


class Order:
    site_id:int
    order_id: int
    productList: list[OrderItem]

    def __init__(self, site_id:int, order_id: int, productList: list[OrderItem]):
        self.site_id = site_id
        self.order_id = order_id
        self.productList = productList

    def __len__(self):
        return len(self.productList)

    def __iter__(self):
        return iter(self.productList)

    def __contains__(self, sku: str) -> bool:
        target = sku.strip().upper()
        return any(
            item.sku.strip().upper() == target
            for item in self.productList
        )

    @overload
    def __getitem__(self, index: int) -> OrderItem:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[OrderItem]:
        ...

    def __getitem__(
            self,
            index: int | slice,
    ) -> OrderItem | list[OrderItem]:
        return self.productList[index]

    def __hash__(self, other: Order):
        return hash(self.site_id) == hash(other.site_id) and hash(self.order_id) == hash(other.order_id)


order = Order(site_id=2, order_id=1, productList=[OrderItem(sku="SKU001",price=1, quantity=2)])
print(len(order))

# 六十八、作业 2
#
# 实现：
#
# __iter__
#
# 支持：
#
# for item in order:
#     print(item.sku)
for item in order:
    print(item.sku, item.price, item.quantity)


# 六十九、作业 3
#
# 实现：
#
# __contains__
#
# 支持：
#
# "SKU001" in order
#
# 要求忽略 SKU 前后空格和大小写：
#
# " sku001 " in order
#
# 也应该：
#
# True
print(" sku001 " in order)
print("SKU003" not in order)


# 七十、作业 4
#
# 实现：
#
# __getitem__
#
# 支持：
#
# order[0]
#
# 和：
#
# order[0:2]
#
# 类型提示尽量正确。
print(order[0])


# 七十一、作业 5
#
# 实现：
#
# OrderKey
#
# 要求：
#
# @dataclass(
#     frozen=True,
#     slots=True,
# )
#
# 字段：
#
# site_id: int
# order_no: str
#
# 测试：
#
# key1 == key2
# hash(key1) == hash(key2)
#
# 并放入：
#
# set
#
# 去重。
@dataclass(frozen=True, slots=True)
class OrderKey:
    site_id:int
    order_id: int
    productList: list[OrderItem]

order2 = OrderKey(site_id=2, order_id=1, productList=[OrderItem(sku="SKU001",price=1, quantity=2)])
print(order == order2)


# 七十二、作业 6：MRO
#
# 写：
#
# class A
# class B(A)
# class C(A)
# class D(B, C)
#
# 每个类都实现：
#
# process()
#
# 并使用：
#
# super().process()
#
# 打印：
#
# D.mro()
#
# 观察执行顺序。
#
# 这题必须亲手跑。
class A:
    def process(self):
        print("process A")

class B(A):
    def process(self):
        print("process B")
        super().process()

class C(A):
    def process(self):
        print("process C")
        super().process()

class D(B, C):
    def process(self):
        print("process D")
        super().process()

d = D()
d.process()

# 七十三、作业 7：组合
#
# 定义：
#
# class OrderRepository(Protocol):
#     ...
#
# class Cache(Protocol):
#     ...
#
# class Notifier(Protocol):
#     ...
#
# 然后：
#
# class OrderService:
#     def __init__(
#         self,
#         repository: OrderRepository,
#         cache: Cache,
#         notifier: Notifier,
#     ) -> None:
#         ...
#
# 不要使用多继承。
class OrderRepository(Protocol):
    ...

class Cache(Protocol):
    ...

class Notifier(Protocol):
    ...

class OrderService(Protocol):
    def __init__(
            self,
            orderRepository: OrderRepository,
            cache: Cache,
            notifier: Notifier,
    ) -> None:
        ...

# 七十四、加分作业：Money 值对象
#
# 实现：
#
# @dataclass(
#     frozen=True,
#     slots=True,
# )
# class Money:
#     amount: Decimal
#
# 要求支持：
#
# money1 + money2
# money1 == money2
# money1 < money2
# str(money)
# repr(money)
#
# 并保证金额自动：
#
# 两位小数
# ROUND_HALF_UP
#
# 这个非常适合训练今天所有内容。
@dataclass
class Money:
    amount: Decimal

    def __add__(self, other):
        return self.amount + other.amount

    def __sub__(self, other):
        return self.amount - other.amount

    def __eq__(self, other):
        return self.amount == other.amount

    def __gt__(self, other):
        return self.amount > other.amount

    def __lt__(self, other):
        return self.amount < other.amount

    def __str__(self):
        return str(self.amount)

    def __repr__(self):
        return str(self.amount)


# Day 11 必须记住
# __repr__
# → 开发者表达
#
# __str__
# → 用户表达
#
# __eq__
# → ==
#
# __hash__
# → hash / set / dict key
#
# __len__
# → len()
#
# __bool__
# → bool / if
#
# __contains__
# → in
#
# __iter__
# → for
#
# __getitem__
# → []
#
# __add__
# → +
#
# 以及：
#
# super()
# ≠ 简单的父类调用
#
# super()
# = MRO 中继续向后找
#
# 最后一句最重要：
#
# 高级 Python 面向对象，不是“多写 class”，而是让对象通过协议自然融入 Python 语言，同时用组合控制复杂度、用继承表达真正的 is-a 关系。


from dataclasses import dataclass
from typing import Iterator, overload


@dataclass
class OrderItem:
    sku: str
    price: float
    quantity: int


class Order:
    def __init__(
        self,
        site_id: int,
        order_id: int,
        productList: list[OrderItem],
    ) -> None:
        self.site_id = site_id
        self.order_id = order_id
        self.productList = productList

    def __len__(self) -> int:
        # 商品行数，不是 quantity 之和
        return len(self.productList)

    def __iter__(self) -> Iterator[OrderItem]:
        # 直接复用 list 已经实现好的迭代能力
        return iter(self.productList)

    def __contains__(self, sku: str) -> bool:
        # 先统一查询条件，避免每次循环重复处理
        target = sku.strip().upper()

        return any(
            item.sku.strip().upper() == target
            for item in self.productList
        )

    @overload
    def __getitem__(self, index: int) -> OrderItem:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[OrderItem]:
        ...

    def __getitem__(
        self,
        index: int | slice,
    ) -> OrderItem | list[OrderItem]:
        return self.productList[index]


order = Order(
    site_id=2,
    order_id=1,
    productList=[
        OrderItem(sku="SKU001", price=1, quantity=2),
        OrderItem(sku="SKU002", price=3, quantity=4),
    ],
)

assert len(order) == 2
assert " sku001 " in order
assert "SKU003" not in order

assert order[0].sku == "SKU001"
assert [item.sku for item in order[0:2]] == ["SKU001", "SKU002"]

for item in order:
    print(item.sku, item.price, item.quantity)






from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderKey:
    site_id: int
    order_no: str


key1 = OrderKey(site_id=2, order_no="ORD001")
key2 = OrderKey(site_id=2, order_no="ORD001")
key3 = OrderKey(site_id=2, order_no="ORD002")

assert key1 == key2
assert hash(key1) == hash(key2)

keys = {key1, key2, key3}
assert len(keys) == 2

print(keys)



from typing import Protocol


class OrderRepository(Protocol):
    def get_by_id(
        self,
        site_id: int,
        order_id: int,
    ) -> Order | None:
        ...


class Cache(Protocol):
    def get(
        self,
        site_id: int,
        order_id: int,
    ) -> Order | None:
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

    def get_order(
        self,
        site_id: int,
        order_id: int,
    ) -> Order | None:
        # 1. 优先查询缓存
        order = self.cache.get(site_id, order_id)
        if order is not None:
            return order

        # 2. 缓存未命中，查询数据库
        order = self.repository.get_by_id(site_id, order_id)
        if order is None:
            return None

        # 3. 写入缓存并通知
        self.cache.set(order)
        self.notifier.order_loaded(order)

        return order