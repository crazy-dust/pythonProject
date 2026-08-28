# 五十六、今天作业 1
#
# 实现：
#
# def generate_order_nos(
#     prefix: str,
#     start: int,
#     end: int,
# ) -> Iterator[str]:
#     ...
#
# 调用：
#
# generate_order_nos(
#     "ORDER",
#     1,
#     3,
# )
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
# def iter_large_orders(
#     orders: Iterable[Order],
#     min_amount: Decimal,
# ) -> Iterator[Order]:
#     ...
#
# 要求：
#
# amount >= min_amount
#
# 才 yield。
#
# 五十八、作业 3：流式状态过滤
#
# 实现：
#
# def iter_orders_by_status(
#     orders: Iterable[Order],
#     status: OrderStatus,
# ) -> Iterator[Order]:
#     ...
#
# 不能返回 list。
#
# 必须：
#
# yield
# 五十九、作业 4：分页模拟
#
# 实现：
#
# def iter_orders_by_page(
#     pages: list[list[Order]],
# ) -> Iterator[Order]:
#     ...
#
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
# 六十、作业 5：批处理
#
# 使用：
#
# itertools.batched
#
# 实现：
#
# def process_in_batches(
#     orders: Iterable[Order],
#     batch_size: int,
# ) -> None:
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
#
# 六十二、加分题
#
# 写：
#
# def first_matching_order(
#     orders: Iterable[Order],
#     predicate: Callable[[Order], bool],
# ) -> Order | None:
#
# 要求使用：
#
# next(...)
#
# 而不是手写：
#
# for



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