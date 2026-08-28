# # 推导式IF的顺序分辨解析
#
# valid_orders = (
#     order
#     for order in clean_orders
#     if order is not None
# )
#
# 我不太理解这个if为什么出现在后面  之前的不都是在for前面嘛
#
# 这个地方你卡住得很正常，因为 Python 里有两种完全不同的 if 写法，长得很像，但作用不一样。
#
# 你这段：
#
# valid_orders = (
#     order
#     for order in clean_orders
#     if order is not None
# )
#
# 这里的 if 是：
#
# 过滤条件
#
# 所以它必须放在 for 后面。
#
# 你可以直接把它还原成普通 for：
#
# result = []
#
# for order in clean_orders:
#     if order is not None:
#         result.append(order)
#
# 生成器表达式只是把这段压缩成：
#
# (
#     order
#     for order in clean_orders
#     if order is not None
# )
#
# 所以阅读顺序不要按代码位置机械读，应该按这个逻辑读：
#
# for order in clean_orders
#     ↓
# 拿到一个 order
#     ↓
# if order is not None
#     ↓
# 条件成立
#     ↓
# 产出 order
#
# 也就是：
#
# 从 clean_orders 里逐个拿订单，只保留不是 None 的订单。
#
# 你之前看到的“if 在前面”，大概率是这种：
#
# status = "PAID" if paid else "UNPAID"
#
# 这个不是过滤。
#
# 这是：
#
# 条件表达式 / 三元表达式
#
# 等价：
#
# if paid:
#     status = "PAID"
# else:
#     status = "UNPAID"
#
# 所以它的语法是：
#
# 真值 if 条件 else 假值
#
# 例如：
#
# "成年" if age >= 18 else "未成年"
#
# 而生成器 / 列表推导式里的过滤语法是：
#
# 表达式
# for 变量 in 数据
# if 条件
#
# 例如：
#
# numbers = [
#     number
#     for number in range(10)
#     if number % 2 == 0
# ]
#
# 等价：
#
# numbers = []
#
# for number in range(10):
#     if number % 2 == 0:
#         numbers.append(number)
#
# 这两个 if 一定要分开记。
#
# 1. if 在 for 后面：过滤
# [
#     order
#     for order in orders
#     if order.status == "PAID"
# ]
#
# 意思：
#
# 只要 PAID 的。
#
# Java Stream 类比：
#
# orders.stream()
#     .filter(order -> order.getStatus().equals("PAID"))
#     .toList();
#
# 这里的：
#
# if order.status == "PAID"
#
# 就相当于 Java 的：
#
# .filter(...)
# 2. if ... else ... 在 for 前面：转换
#
# 例如：
#
# statuses = [
#     "已支付" if order.status == "PAID" else "未支付"
#     for order in orders
# ]
#
# 等价：
#
# statuses = []
#
# for order in orders:
#     if order.status == "PAID":
#         statuses.append("已支付")
#     else:
#         statuses.append("未支付")
#
# 这里不是过滤订单。
#
# 而是：
#
# 每个订单都保留，但是根据条件决定生成什么值。
#
# Java 类比更像：
#
# orders.stream()
#     .map(order ->
#         order.getStatus().equals("PAID")
#             ? "已支付"
#             : "未支付"
#     )
#     .toList();
#
# 也就是：
#
# for 后面的 if
# ≈ filter
#
# for 前面的 if...else
# ≈ map 里的三元表达式
#
# 甚至两种可以同时出现：
#
# result = [
#     "大单" if order.amount >= 500 else "普通单"
#     for order in orders
#     if order.status == "PAID"
# ]
#
# 这个要拆成两部分看。
#
# 后面的：
#
# if order.status == "PAID"
#
# 负责：
#
# 过滤，只要 PAID。
#
# 前面的：
#
# "大单" if order.amount >= 500 else "普通单"
#
# 负责：
#
# 转换，决定输出“大单”还是“普通单”。
#
# 等价普通代码：
#
# result = []
#
# for order in orders:
#     if order.status == "PAID":
#         if order.amount >= 500:
#             result.append("大单")
#         else:
#             result.append("普通单")
#
# Java Stream 就是：
#
# orders.stream()
#     .filter(order ->
#         order.getStatus().equals("PAID")
#     )
#     .map(order ->
#         order.getAmount() >= 500
#             ? "大单"
#             : "普通单"
#     )
#     .toList();
#
# 你把这个映射记住就非常清楚了：
#
# Python	Java Stream
# for order in orders	.stream()
# if 条件 放 for 后	.filter(...)
# 前面的表达式	.map(...)
# ( ... )	惰性 Stream / Generator
# [ ... ]	.toList()
#
# 所以你原代码：
#
# valid_orders = (
#     order
#     for order in clean_orders
#     if order is not None
# )
#
# 直接翻译成你熟悉的 Java 思维就是：
#
# cleanOrders.stream()
#     .filter(Objects::nonNull)
#
# 而且 Python 这里还是 generator，所以是惰性的，不会立即生成整个结果列表。
#
# 最简单的记忆法：
#
# 推导式里，for 后面的 if 是“要不要这个元素”；前面的 if...else 是“这个元素要变成什么”。