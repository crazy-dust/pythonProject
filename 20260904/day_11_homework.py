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