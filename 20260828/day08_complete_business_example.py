from collections.abc import Iterator
from decimal import Decimal
from itertools import batched
from typing import Any


def iter_raw_orders(
    orders: list[dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    for order in orders:
        yield order


def iter_valid_orders(
    raw_orders: Iterator[dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    for order in raw_orders:
        amount = order.get("amount")

        if not isinstance(
            amount,
            Decimal,
        ):
            continue

        if amount <= Decimal("0"):
            continue

        yield order


def iter_paid_orders(
    orders: Iterator[dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    for order in orders:
        if order.get("status") == "PAID":
            yield order


def process_orders(
    orders: list[dict[str, Any]],
) -> None:
    raw_orders = iter_raw_orders(orders)

    valid_orders = iter_valid_orders(
        raw_orders
    )

    paid_orders = iter_paid_orders(
        valid_orders
    )

    for batch in batched(
        paid_orders,
        2,
    ):
        print(
            "处理批次：",
            batch,
        )


# 五十二、这里的类型为什么是 Iterator
# def iter_paid_orders(
#     orders: Iterator[dict[str, Any]],
# ) -> Iterator[dict[str, Any]]:
#
# 因为函数：
#
# yield
#
# 产生的是：
#
# Iterator
#
# 后面我们会进一步讲：
#
# Iterable
# Iterator
# Generator
# Sequence
# Collection
#
# 的类型关系。
#
# 今天先知道：
#
# 使用 yield 的函数，返回类型通常可以写 Iterator[T]。



# 五十三、生成器函数不要写 list 返回值
#
# 错误：
#
# def generate_orders() -> list[Order]:
#     yield order
#
# 类型不对。
#
# 应该：
#
# from collections.abc import Iterator
#
#
# def generate_orders() -> Iterator[Order]:
#     yield order



# 五十四、今天的编程思想
#
# 今天最重要的不是 yield 语法。
#
# 而是：
#
# 1. 惰性计算
# 需要的时候才计算
# 2. 流式处理
# 一条一条通过pipeline
# 3. 降低内存占用
#
# 不保存全部中间结果。
#
# 4. 解耦数据来源和处理逻辑
#
# 数据可以来自：
#
# list
# file
# API
# 数据库
# MQ
# generator
#
# 只要是 iterable，都可以处理。
#
# 5. pull model
#
# 消费者：
#
# next(generator)
#
# 主动向生产者要下一条数据。



# 五十五、Java 开发者最容易犯的错
#
# Java 开发者很容易：
#
# result = []
#
# for item in items:
#     ...
#     result.append(...)
#
# 所有函数都习惯：
#
# return list
#
# 但 Python 很多时候应该问：
#
# 我真的需要整个 list 吗？
#
# 如果只是顺序处理：
#
# yield
#
# 可能更合适。