# 五十六、今天作业 1
#
# 实现：
#
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from itertools import batched
from typing import Iterator, Iterable, Callable


def generate_order_nos(
    prefix: str,
    start: int,
    end: int,
) -> Iterator[str]:
    for order in range(start, end + 1):
        yield f"{prefix}-{order}"
#
# 调用：
#
# if __name__ == '__main__':
#     iter_rows = generate_order_nos(
#         "ORDER",
#         1,
#         3,
#     )
#     for row in iter_rows:
#         print(row)
#
# 依次产生：
#
# ORDER-1
# ORDER-2
# ORDER-3
#
# 必须使用：
#
# yield
# 五十七、作业 2：流式过滤
#
# 实现：
#
@dataclass(kw_only=True)
class Order:
    order_no: str
    status: OrderStatus
    price: Decimal
    amount: Decimal

def iter_large_orders(
    orders_rows: Iterable[Order],
    min_amount: Decimal,
) -> Iterator[Order]:
    for order in orders_rows:
        if order.amount > min_amount:
            yield order
#
# 要求：
#
# amount >= min_amount
#
# 才 yield。

# if __name__ == '__main__':
#     orders = [
#         Order(order_no = "order1", price = Decimal("1.00"), amount = Decimal("1.00")),
#         Order(order_no = "order2", price = Decimal("2.00"), amount = Decimal("2.00"))
#     ]
#
#     iter_large_order_rows = iter_large_orders(orders, min_amount = Decimal("1.00"))
#     for order in iter_large_order_rows:
#         print(order)

# 五十八、作业 3：流式状态过滤
#
# 实现：
#
class OrderStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"

def iter_orders_by_status(
    orders: Iterable[Order],
    status: OrderStatus,
) -> Iterator[Order]:
    for order in orders:
        if order["status"] == OrderStatus.PAID:
            yield order
#
# 不能返回 list。
#
# 必须：
#
# yield
# if __name__ == '__main__':
#     orders = [
#         Order(order_no = "order1", status = OrderStatus.PAID, price = Decimal("1.00"), amount = Decimal("1.00")),
#         Order(order_no = "order2", status = OrderStatus.PENDING, price = Decimal("2.00"), amount = Decimal("2.00"))
#     ]
#     iter_order_rows_by_status = iter_orders_by_status(orders, OrderStatus.PAID)
#     for order in iter_order_rows_by_status:
#         print(order)

# 五十九、作业 4：分页模拟
#
# 实现：
#
def iter_orders_by_page(
    pages: list[list[Order]],
) -> Iterator[Order]:
    for page in pages:
        yield from page

# 例如：
#
# pages = [
#     [order1, order2],
#     [order3],
#     [order4, order5],
# ]
#
# 最终：
#
# order1
# order2
# order3
# order4
# order5
#
# 加分要求：
#
# 使用：
#
# yield from

# if __name__ == '__main__':
#     pages = [
#         [
#             Order(order_no="order1", status=OrderStatus.PAID, price=Decimal("1.00"), amount=Decimal("1.00")),
#             Order(order_no="order2", status=OrderStatus.PENDING, price=Decimal("2.00"), amount=Decimal("2.00"))
#         ],
#         [
#             Order(order_no="order3", status=OrderStatus.PAID, price=Decimal("3.00"), amount=Decimal("3.00"))
#         ]
#     ]
#
#     for order in iter_orders_by_page(pages):
#         print(order.order_no)

# 六十、作业 5：批处理
#
# 使用：
#
# itertools.batched
#
# 实现：
#
def process_in_batches(
    orders: Iterable[Order],
    batch_size: int,
) -> None:
    for index, batch in enumerate(batched(orders, batch_size), start=1):
        print(f"第{index}批：{len(batch)}个")


#
# 例如：
#
# 5个订单
# batch_size=2
#
# 输出：
#
# 第1批：2个
# 第2批：2个
# 第3批：1个
# if __name__ == '__main__':
#     orders = [
#         Order(order_no="order1", status=OrderStatus.PAID, price=Decimal("1.00"), amount=Decimal("1.00")),
#         Order(order_no="order2", status=OrderStatus.PENDING, price=Decimal("2.00"), amount=Decimal("2.00")),
#         Order(order_no="order3", status=OrderStatus.PENDING, price=Decimal("3.00"), amount=Decimal("3.00"))
#     ]
#     process_in_batches(orders, 2)

# 六十一、作业 6：完整流式 pipeline
#
# 实现：
#
# 原始订单
# ↓
# 过滤非法订单
# ↓
# 过滤PAID
# ↓
# 过滤金额>=100
# ↓
# 每100条一批
# ↓
# 打印批次
#
# 要求：
#
# 中间不能写：
#
# list(...)
#
# 也不能：
#
# result = []
#
# 核心目标就是：
#
# 全链路惰性。
from collections.abc import Iterable
from itertools import batched
from decimal import Decimal

def process_order_pipeline(
    orders: Iterable[Order],
) -> None:
    # 1. 过滤非法订单
    valid_orders = (
        order
        for order in orders
        if order is not None
    )

    # 2. 过滤 PAID
    paid_orders = (
        order
        for order in valid_orders
        if order.status == OrderStatus.PAID
    )

    # 3. 过滤金额 >= 100
    high_value_orders = (
        order
        for order in paid_orders
        if order.amount >= Decimal("100")
    )

    # 4. 每 100 条一批
    batches = batched(high_value_orders, 100)

    # 5. 打印批次
    for index, batch in enumerate(batches, start=1):
        print(f"第{index}批：{len(batch)}个订单")

# 六十二、加分题
#
# 写：
#
def first_matching_order(
    orders: Iterable[Order],
    predicate: Callable[[Order], bool],
) -> Order | None:
    return next(
        (order for order in orders if predicate(order)),
        None,
    )

#
# 要求使用：
#
# next(...)
#
# 而不是手写：
#
# for
if __name__ == '__main__':
    orders = [
        Order(order_no="order1", status=OrderStatus.PAID, price=Decimal("1.00"), amount=Decimal("1.00")),
        Order(order_no="order2", status=OrderStatus.PENDING, price=Decimal("2.00"), amount=Decimal("2.00")),
        Order(order_no="order3", status=OrderStatus.PENDING, price=Decimal("3.00"), amount=Decimal("3.00"))
    ]
    result = first_matching_order(
        orders,
        lambda order: order.status == OrderStatus.PAID,
    )
    print(result)


# 六十三、今天必须记住
# Iterable：可以被for遍历
# Iterator：可以被next不断取值
# iter(obj)：把Iterable变成Iterator
# next(iterator)：取下一个值
# StopIteration：没有更多数据
# yield：返回一个值并暂停函数
# Generator：一种特殊Iterator
# Generator Expression：惰性的推导表达式
# list comprehension：立即生成全部数据
# generator通常只能消费一次
# yield from：转发另一个Iterable
# itertools：迭代器工具箱
# Day 8 最重要的 4 句话
#
# 第一句：
#
# for 本质上就是 iter() + next()。
#
# 第二句：
#
# yield 不是结束函数，而是“返回一个值并暂停”。
#
# 第三句：
#
# list 是一次性把数据装满；generator 是需要一个生成一个。
#
# 第四句：
#
# 数据量大、分页、文件、爬虫、批处理、流式清洗时，要主动想到 generator。