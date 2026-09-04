# 可以把 Mixin 理解成：
#
# 一个“不完整的功能积木类”，它不是为了单独创建对象，而是为了给别的类“混入”一个额外能力。
#
# 你别先把它理解成复杂多继承。先用 Java 思维看最容易。
#
# 1. 先看普通继承
#
# 假设：
#
# class Animal:
#     def eat(self) -> None:
#         print("吃东西")
#
#
# class Dog(Animal):
#     pass
#
# 这里：
#
# Dog is an Animal
#
# 这是标准的 is-a 关系。
#
# 所以继承很自然。
#
# 2. Mixin 不是这种 is-a 关系
#
# 比如你有：
#
# class JsonMixin:
#     def to_json(self) -> str:
#         ...
#
# 然后：
#
# class Order(JsonMixin):
#     ...
#
# 这里绝对不能说：
#
# Order is a JsonMixin
#
# 不对。
#
# 真正意思是：
#
# Order
# 拥有“转换成 JSON”的能力
#
# 也就是说：
#
# Mixin 表示一种横向能力，而不是父子业务关系。
#
# 3. 最简单例子
# import json
#
#
# class JsonMixin:
#     def to_json(self) -> str:
#         return json.dumps(
#             self.__dict__,
#             ensure_ascii=False,
#         )
#
#
# class Order(JsonMixin):
#     def __init__(
#         self,
#         order_no: str,
#         status: str,
#     ) -> None:
#         self.order_no = order_no
#         self.status = status
#
# 现在：
#
# order = Order(
#     "A001",
#     "PAID",
# )
#
# print(order.to_json())
#
# 输出：
#
# {"order_no": "A001", "status": "PAID"}
#
# 注意：
#
# Order 自己没有写：
#
# def to_json(...)
#
# 但是因为：
#
# class Order(JsonMixin):
#
# 所以获得了：
#
# to_json()
# 4. 你可以把它理解成“能力插件”
#
# 例如：
#
# Order
# ├── 订单业务能力
# ├── JsonMixin        → JSON序列化能力
# ├── LogMixin         → 日志能力
# └── RetryMixin       → 重试能力
#
# 于是：
#
# class Order(
#     JsonMixin,
#     LogMixin,
# ):
#     ...
#
# 相当于：
#
# 给 Order 混入 JSON 能力和日志能力。
#
# 这就是名字 Mixin 的来源：
#
# mix in = 混进去。
#
# 5. Java 里最接近什么
#
# Java 最接近：
#
# interface + default method
#
# 例如 Java：
#
# public interface JsonSerializable {
#
#     default String toJson() {
#         ...
#     }
#
# }
#
# 然后：
#
# public class Order
#         implements JsonSerializable {
#
# }
#
# Order 就获得：
#
# toJson()
#
# Python：
#
# class JsonMixin:
#     def to_json(self) -> str:
#         ...
#
#
# class Order(JsonMixin):
#     ...
#
# 思想非常接近。
#
# 所以你可以先这么记：
#
# Python Mixin
# ≈
# Java interface + default method
#
# 只是 Python 用的是多继承机制。
#
# 6. 为什么不直接写工具类
#
# 你可能会想：
#
# Java 里我完全可以：
#
# JsonUtils.toJson(order);
#
# Python 也可以：
#
# to_json(order)
#
# 当然可以。
#
# 所以 Mixin 不是必须的。
#
# 区别在于：
#
# 工具函数
# to_json(order)
#
# 表达：
#
# 外部函数帮 order 做事情。
#
# Mixin
# order.to_json()
#
# 表达：
#
# order 自己拥有这个能力。
#
# 如果某种能力跟对象关系非常紧密，而且很多类都需要，Mixin 会比较自然。
#
# 7. 一个更真实的例子
#
# 假设：
#
# class CreatedAtMixin:
#     def mark_created(self) -> None:
#         print("记录创建时间")
#
#
# class AuditMixin:
#     def audit(self) -> None:
#         print("记录审计日志")
#
# 订单：
#
# class Order(
#     CreatedAtMixin,
#     AuditMixin,
# ):
#     def create(self) -> None:
#         print("创建订单")
#
#         self.mark_created()
#         self.audit()
#
# 用户：
#
# class User(
#     CreatedAtMixin,
#     AuditMixin,
# ):
#     ...
#
# 你会发现：
#
# Order
# User
#
# 业务完全不同。
#
# 但它们都有：
#
# 创建时间能力
# 审计能力
#
# 所以这些“横向公共能力”适合做 Mixin。
#
# 8. Mixin 和普通父类最大的区别
#
# 普通父类：
#
# class Animal:
#     ...
#
# 代表：
#
# 业务类型关系
#
# Mixin：
#
# class JsonMixin:
#     ...
#
# 代表：
#
# 附加能力
#
# 看名字就应该知道。
#
# 一般建议命名：
#
# JsonMixin
# LoggingMixin
# TimestampMixin
# SerializeMixin
# RetryMixin
#
# 明确告诉别人：
#
# 这个类不是完整对象，只是用来被混入的。
#
# 9. Mixin 通常不单独实例化
#
# 比如：
#
# JsonMixin()
#
# 虽然 Python 有时允许你这么干，但通常没有业务意义。
#
# 因为它只是：
#
# JSON能力
#
# 它自己没有真正数据。
#
# 真正使用：
#
# order = Order(...)
# order.to_json()
# 10. Mixin 最典型特点
#
# 一个好的 Mixin 通常满足：
#
# 功能单一
# 没有复杂业务状态
# 不代表领域对象
# 不单独实例化
# 可以被多个不同类复用
#
# 例如：
#
# class LogMixin:
#     def log(
#         self,
#         message: str,
#     ) -> None:
#         print(
#             f"[{self.__class__.__name__}] "
#             f"{message}"
#         )
#
# 然后：
#
# class OrderService(LogMixin):
#     pass
#
#
# class UserService(LogMixin):
#     pass
#
# 两者都可以：
#
# service.log(...)
# 11. 一个完整例子
# import json
#
#
# class JsonMixin:
#     """
#     JSON 序列化能力。
#
#     这是一个 Mixin：
#     - 不代表具体业务对象
#     - 不建议单独创建 JsonMixin 实例
#     - 主要用于给其他类提供 to_json 能力
#     """
#
#     def to_json(self) -> str:
#         """
#         将当前对象的实例属性转换成 JSON。
#         """
#
#         return json.dumps(
#             self.__dict__,
#             ensure_ascii=False,
#         )
#
#
# class LogMixin:
#     """
#     简单日志能力。
#     """
#
#     def log(
#         self,
#         message: str,
#     ) -> None:
#         """
#         使用当前类名作为日志来源。
#         """
#
#         print(
#             f"[{self.__class__.__name__}] "
#             f"{message}"
#         )
#
#
# class Order(
#     JsonMixin,
#     LogMixin,
# ):
#     """
#     Order 本身是业务类。
#
#     JsonMixin：
#         给它增加 JSON 能力。
#
#     LogMixin：
#         给它增加日志能力。
#     """
#
#     def __init__(
#         self,
#         order_no: str,
#         status: str,
#     ) -> None:
#         self.order_no = order_no
#         self.status = status
#
#     def pay(self) -> None:
#         """
#         支付订单。
#         """
#
#         self.status = "PAID"
#
#         # 这个方法来自 LogMixin
#         self.log(
#             f"订单 {self.order_no} 已支付"
#         )
#
#
# def main() -> None:
#     order = Order(
#         order_no="A001",
#         status="UNPAID",
#     )
#
#     order.pay()
#
#     # 这个方法来自 JsonMixin
#     print(
#         order.to_json()
#     )
#
#
# if __name__ == "__main__":
#     main()
#
# 输出：
#
# [Order] 订单 A001 已支付
# {"order_no": "A001", "status": "PAID"}
# 12. 这里发生了什么
#
# Order 自己只有：
#
# __init__()
# pay()
#
# 但它继承：
#
# JsonMixin
# LogMixin
#
# 所以最终 Order 拥有：
#
# Order自己的：
# __init__
# pay
#
# JsonMixin提供：
# to_json
#
# LogMixin提供：
# log
#
# 可以画成：
#
#       JsonMixin
#           │
#       to_json()
#           │
#           ▼
#
# LogMixin ───────→ Order
#   │               │
#  log()             ├─ __init__()
#                    └─ pay()
#
# 最后：
#
# Order = 订单业务能力
#       + JSON能力
#       + 日志能力
# 13. 那为什么不用组合？
#
# 这个问题很关键。
#
# 你前面学了：
#
# 组合优于继承。
#
# 比如：
#
# class OrderService:
#     def __init__(
#         self,
#         repository,
#         cache,
#         notifier,
#     ):
#         self.repository = repository
#         self.cache = cache
#         self.notifier = notifier
#
# 这应该用组合，而不是 Mixin。
#
# 为什么？
#
# 因为：
#
# Repository
# Cache
# Notifier
#
# 都是完整独立组件。
#
# 它们有：
#
# 自己的状态
# 自己的生命周期
# 自己的实现
#
# 所以应该：
#
# OrderService has Repository
#
# 而不是：
#
# OrderService is Repository
# 14. Mixin 和组合怎么选
#
# 你可以直接按这个表判断：
#
# 场景	推荐
# 数据库 Repository	组合
# Redis Cache	组合
# 支付网关	组合
# HTTP Client	组合
# MQ Producer	组合
# 简单序列化能力	Mixin 可以
# 日志辅助能力	Mixin 可以
# 时间戳辅助能力	Mixin 可以
# 权限辅助能力	Mixin 可以
# 小型可复用横向行为	Mixin 可以
#
# 核心判断：
#
# 如果它是一个完整依赖，用组合；如果只是给类增加一小块横向能力，可以考虑 Mixin。
#
# 15. 为什么 Python 里 Mixin 比 Java 常见一点
#
# 因为 Python 支持：
#
# class A(B, C, D):
#
# 多个父类。
#
# Java class 不能：
#
# class A extends B, C
#
# 所以 Java 往往用：
#
# interface
# default method
# 组合
# 代理
#
# Python可以直接：
#
# class Order(
#     JsonMixin,
#     LogMixin,
# ):
# 16. Mixin 会不会有坑？
#
# 会。
#
# 比如两个 Mixin 都有：
#
# def log(...)
# class A:
#     def log(self):
#         print("A")
#
#
# class B:
#     def log(self):
#         print("B")
#
#
# class Order(A, B):
#     pass
#
# 调用：
#
# Order().log()
#
# 到底调用谁？
#
# 由：
#
# MRO
#
# 决定。
#
# 这里通常先找：
#
# Order
# ↓
# A
# ↓
# B
# ↓
# object
#
# 所以调用：
#
# A.log()
#
# 这也是为什么：
#
# Mixin 应该小、职责单一、尽量避免方法名冲突。
#
# 17. Mixin 与 Protocol 不一样
#
# 这两个也容易混。
#
# Protocol
# class PaymentGateway(
#     Protocol
# ):
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 作用：
#
# 描述“你应该具有什么能力”。
#
# 它通常不负责给你实现。
#
# Mixin
# class JsonMixin:
#     def to_json(self):
#         ...
#
# 作用：
#
# 直接把能力实现给你。
#
# 所以：
#
# Protocol
# → 定义能力要求
#
# Mixin
# → 提供能力实现
#
# Java 类比：
#
# Protocol
# ≈ interface
#
# Mixin
# ≈ interface default method / 可复用实现
# 18. 什么时候不要用 Mixin
#
# 千万别把业务层写成：
#
# class OrderService(
#     MySqlMixin,
#     RedisMixin,
#     RabbitMqMixin,
#     DingTalkMixin,
#     ShopifyMixin,
# ):
#     ...
#
# 这就已经失控了。
#
# 应该：
#
# class OrderService:
#     def __init__(
#         self,
#         repository: OrderRepository,
#         cache: Cache,
#         mq: MessageQueue,
#         notifier: Notifier,
#     ) -> None:
#         self.repository = repository
#         self.cache = cache
#         self.mq = mq
#         self.notifier = notifier
#
# 原因：
#
# 这些是依赖，不是“简单能力”。
#
# 19. 你当前阶段怎么记就够了
#
# 你暂时不用深入研究 Mixin。
#
# 只要记：
#
# 普通继承：
# Dog is Animal
#
# 组合：
# OrderService has Repository
#
# Mixin：
# Order has JSON capability
# Order has Logging capability
#
# 换成一句：
#
# 普通继承解决“我是什么”；组合解决“我依赖什么”；Mixin解决“我顺便具有什么小能力”。
#
# 这句话最值得你记笔记。
#
# 20. 最后用 Java 思维总结
#
# 你以前 Java 可能这样：
#
# public interface JsonSerializable {
#
#     default String toJson() {
#         ...
#     }
#
# }
#
# public class Order
#         implements JsonSerializable {
# }
#
# Python：
#
# class JsonMixin:
#     def to_json(self) -> str:
#         ...
#
#
# class Order(JsonMixin):
#     ...
#
# 所以你现在先把 Mixin 理解成：
#
# Python 利用多继承实现的一种“默认方法能力包”。
#
# 后面当你看到：
#
# class Xxx(
#     LoggingMixin,
#     JsonMixin,
# ):
#
# 你不要理解为：
#
# Xxx 是 LoggingMixin。
#
# 而应该理解成：
#
# Xxx 混入了日志能力和 JSON 能力。