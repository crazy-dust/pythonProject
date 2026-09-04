# Day 11：面向对象进阶、魔术方法、MRO 与对象协议
#
# 前面 Day 5 你已经会：
#
# class
# self
# classmethod
# staticmethod
# property
# dataclass
# StrEnum
# Protocol
# ABC
#
# 今天开始往更深一层走：
#
# Python 的对象为什么可以被 len()、str()、==、<、+、for、with 这些语法直接操作？
#
# 核心答案就是：
#
# Python 很多语法，本质都是在调用对象的特殊方法。
#
# 也就是：
#
# __xxx__
#
# 通常叫：
#
# special method
# magic method
# dunder method
# 一、今天学什么
#
# 今天重点：
#
# __init__
# __repr__
# __str__
# __eq__
# __lt__
# __hash__
# __len__
# __bool__
# __contains__
# __iter__
# __getitem__
# 运算符重载
# super()
# MRO
# 多继承
# mixin
# 组合优于继承
# dataclass 和魔术方法的关系
# 二、先建立一个核心认知
#
# 比如：
#
# len(order)
#
# 你以为 len() 是一个普通函数。
#
# 其实它背后会调用：
#
# order.__len__()
#
# 类似：
#
# str(order)
#
# 背后：
#
# order.__str__()
#
# 还有：
#
# order1 == order2
#
# 背后：
#
# order1.__eq__(order2)
#
# 所以很多 Python 语法都是：
#
# 语言语法
# ↓
# 调用特殊方法
# ↓
# 对象决定行为
# 三、Java 类比
#
# Java：
#
# order.toString();
# order.equals(other);
# order.hashCode();
#
# Python：
#
# str(order)
# order == other
# hash(order)
#
# 而 Python 更进一步，把大量语言操作都映射成特殊方法。
#
# 例如：
#
# Python语法	特殊方法
# str(obj)	__str__
# repr(obj)	__repr__
# obj1 == obj2	__eq__
# obj1 < obj2	__lt__
# len(obj)	__len__
# bool(obj)	__bool__
# x in obj	__contains__
# for x in obj	__iter__
# obj[key]	__getitem__
# obj + other	__add__
# 四、__init__ 你已经见过
# class Order:
#     def __init__(
#         self,
#         order_no: str,
#     ) -> None:
#         self.order_no = order_no
#
# 它不是严格意义上的“构造对象方法”。
#
# 更准确地说：
#
# __init__ 是对象创建完成后的初始化方法。
#
# Python 对象创建更底层其实还有：
#
# __new__
#
# 执行大致是：
#
# __new__
# ↓
# 创建实例
# ↓
# __init__
# ↓
# 初始化实例
#
# 当前阶段先知道：
#
# __new__ = 创建对象
# __init__ = 初始化对象
#
# 普通业务代码几乎总是只写 __init__。
#
# 五、__repr__
#
# 先看：
#
# class Order:
#     def __init__(
#         self,
#         order_no: str,
#     ) -> None:
#         self.order_no = order_no
#
# 然后：
#
# order = Order("A001")
#
# print(order)
#
# 可能看到：
#
# <__main__.Order object at 0x...>
#
# 不方便调试。
#
# 定义：
#
# class Order:
#     def __init__(
#         self,
#         order_no: str,
#     ) -> None:
#         self.order_no = order_no
#
#     def __repr__(self) -> str:
#         return (
#             f"Order("
#             f"order_no={self.order_no!r}"
#             f")"
#         )
#
# 现在：
#
# print(repr(order))
#
# 得到：
#
# Order(order_no='A001')
# 六、repr 是给谁看的
#
# 一般理解：
#
# __repr__
# → 给开发者、调试器、日志看的
#
# 目标是：
#
# 尽量准确表达对象状态。
#
# 例如：
#
# Order(
#     order_no='A001',
#     status='PAID'
# )
# 七、__str__
# def __str__(self) -> str:
#     return f"订单 {self.order_no}"
#
# 那么：
#
# print(order)
#
# 输出：
#
# 订单 A001
#
# 通常：
#
# __str__
# → 给用户看
# __repr__
# → 给开发者看
# 八、如果只实现 __repr__
#
# 如果没有：
#
# __str__
#
# Python 在很多情况下会退回使用：
#
# __repr__
#
# 所以实际工程里：
#
# 如果只想实现一个，通常优先 __repr__。
#
# 九、!r 是什么
#
# 你看到：
#
# f"{self.order_no!r}"
#
# 表示：
#
# repr(self.order_no)
#
# 比如：
#
# order_no = "A001"
#
# 普通：
#
# f"{order_no}"
#
# 得到：
#
# A001
#
# 而：
#
# f"{order_no!r}"
#
# 得到：
#
# 'A001'
#
# 调试信息更准确。
#
# 十、dataclass 自动帮你写 repr
#
# 你写：
#
# @dataclass
# class Order:
#     order_no: str
#     status: str
#
# Python 自动生成类似：
#
# __init__
# __repr__
# __eq__
#
# 所以：
#
# print(order)
#
# 可能直接得到：
#
# Order(order_no='A001', status='PAID')
#
# 这就是 dataclass 非常实用的原因之一。
#
# 十一、__eq__：对象相等
#
# 普通类：
#
# class Order:
#     def __init__(
#         self,
#         order_no: str,
#     ) -> None:
#         self.order_no = order_no
#
# 创建：
#
# order1 = Order("A001")
# order2 = Order("A001")
#
# 如果没有自定义：
#
# order1 == order2
#
# 通常比较的是对象身份语义。
#
# 两个不同实例一般：
#
# False
#
# 你可以定义：
#
# def __eq__(
#     self,
#     other: object,
# ) -> bool:
#     if not isinstance(
#         other,
#         Order,
#     ):
#         return NotImplemented
#
#     return (
#         self.order_no
#         == other.order_no
#     )
#
# 现在：
#
# order1 == order2
#
# 就是：
#
# True
# 十二、为什么参数写 object
#
# 这里：
#
# def __eq__(
#     self,
#     other: object,
# ) -> bool:
#
# 因为别人可能拿你的对象和任意东西比较：
#
# order == "A001"
# order == 123
# order == None
#
# 所以不能假设：
#
# other: Order
#
# 更安全：
#
# other: object
#
# 然后：
#
# isinstance(other, Order)
#
# 做类型收窄。
#
# 十三、为什么返回 NotImplemented
#
# 这是特殊值：
#
# NotImplemented
#
# 注意不是：
#
# None
# False
#
# 它表示：
#
# 我这个对象不知道怎么和对方比较，请 Python 尝试其他比较逻辑。
#
# 所以：
#
# return NotImplemented
#
# 比粗暴：
#
# return False
#
# 更符合特殊方法协议。
#
# 十四、Java 对比
#
# Java：
#
# @Override
# public boolean equals(Object other) {
#     ...
# }
#
# Python：
#
# def __eq__(
#     self,
#     other: object,
# ) -> bool:
#     ...
#
# 思想几乎一样。
#
# 十五、__hash__
#
# 如果对象参与：
#
# set
# dict key
#
# 就涉及：
#
# __hash__()
#
# 例如：
#
# hash(order)
#
# Java 类比：
#
# hashCode()
# 十六、为什么 eq 和 hash 必须一致
#
# 原则：
#
# 如果 a == b
# 那么 hash(a) 必须 == hash(b)
#
# 否则：
#
# set
# dict
#
# 行为会混乱。
#
# Java 也是同样原则：
#
# equals 一致
# → hashCode 必须一致
# 十七、dataclass 和 hash
#
# 例如：
#
# @dataclass(frozen=True)
# class OrderKey:
#     site_id: int
#     order_no: str
#
# 因为：
#
# frozen=True
#
# 对象不可变语义比较强。
#
# 通常就很适合作为：
#
# dict key
# set element
#
# 例如：
#
# keys = {
#     OrderKey(
#         site_id=1001,
#         order_no="A001",
#     )
# }
# 十八、为什么可变对象不适合作为 hash key
#
# 假设：
#
# order.order_no = "A002"
#
# 但它已经放进：
#
# set
#
# 如果 hash 依赖 order_no，修改以后 hash 变化。
#
# 集合内部位置就乱了。
#
# 所以：
#
# 可哈希对象通常应该保持不可变。
#
# 这也是为什么：
#
# frozen=True
#
# 常和 hash 场景一起出现。
#
# 十九、__lt__：小于比较
#
# 例如你希望订单按照金额比较：
#
# def __lt__(
#     self,
#     other: object,
# ) -> bool:
#     if not isinstance(
#         other,
#         Order,
#     ):
#         return NotImplemented
#
#     return (
#         self.amount
#         < other.amount
#     )
#
# 现在：
#
# order1 < order2
#
# 可以运行。
#
# 二十、sort 会用比较规则
#
# 例如：
#
# orders.sort()
#
# 如果对象实现：
#
# __lt__
#
# 就可以排序。
#
# 不过业务代码更推荐显式：
#
# orders.sort(
#     key=lambda order: order.amount
# )
#
# 原因：
#
# “订单天然按照金额比较”这种语义未必稳定。
#
# 所以：
#
# __lt__
#
# 不要为了方便随便加。
#
# 二十一、__len__
#
# 比如一个订单有多个商品：
#
# class Order:
#     def __init__(
#         self,
#         items: list[OrderItem],
#     ) -> None:
#         self.items = items
#
#     def __len__(self) -> int:
#         return len(self.items)
#
# 那么：
#
# len(order)
#
# 返回商品行数。
#
# 二十二、Java 类比
#
# Java 可能：
#
# order.getItemCount();
#
# Python 可以设计成：
#
# len(order)
#
# 前提是这个语义自然。
#
# 比如：
#
# len(cart)
# len(order.items)
# len(batch)
#
# 都比较自然。
#
# 二十三、__bool__
#
# 对象放进：
#
# if order:
#
# Python需要判断真假。
#
# 可以定义：
#
# def __bool__(self) -> bool:
#     return bool(self.items)
#
# 那么：
#
# if order:
#
# 表示：
#
# 订单是否有商品。
#
# 二十四、如果没写 __bool__
#
# Python会尝试：
#
# __len__
#
# 如果：
#
# len(obj) == 0
#
# 视为 False。
#
# 如果大于 0：
#
# True
#
# 所以：
#
# __bool__
# 优先
#
# 没有 __bool__
# ↓
# 看 __len__
# 二十五、别滥用 __bool__
#
# 例如：
#
# if order:
#
# 到底是什么意思？
#
# 可能是：
#
# 订单存在？
# 订单有效？
# 订单已支付？
# 订单有商品？
#
# 如果语义不明确，就不要重载。
#
# 明确写：
#
# if order.is_paid:
#
# 通常更好。
#
# 二十六、__contains__
#
# 比如：
#
# "SKU001" in order
#
# 可以通过：
#
# def __contains__(
#     self,
#     sku: object,
# ) -> bool:
#     if not isinstance(
#         sku,
#         str,
#     ):
#         return False
#
#     return any(
#         item.sku == sku
#         for item in self.items
#     )
#
# 现在：
#
# "SKU001" in order
#
# 就有意义了。
#
# 二十七、Java 类比
#
# Java：
#
# order.containsSku("SKU001");
#
# Python：
#
# "SKU001" in order
#
# 只要这个语义自然，就非常 Pythonic。
#
# 二十八、__iter__
#
# 你 Day 8 学过：
#
# for item in order:
#
# 如果 Order 实现：
#
# def __iter__(self):
#     return iter(self.items)
#
# 那么：
#
# for item in order:
#     print(item)
#
# 就能直接遍历订单商品。
#
# 二十九、类型标注
# from collections.abc import Iterator
#
#
# def __iter__(
#     self,
# ) -> Iterator[OrderItem]:
#     return iter(self.items)
#
# 现在 Order 自己就是：
#
# Iterable[OrderItem]
# 三十、__getitem__
#
# 如果想：
#
# order[0]
#
# 返回第一个商品。
#
# 可以：
#
# def __getitem__(
#     self,
#     index: int,
# ) -> OrderItem:
#     return self.items[index]
#
# 于是：
#
# order[0]
# order[1]
#
# 都能用。
#
# 三十一、还可以支持切片
#
# 如果写得完整一点：
#
# def __getitem__(
#     self,
#     index: int | slice,
# ) -> OrderItem | list[OrderItem]:
#     return self.items[index]
#
# 那么：
#
# order[0]
#
# 返回单个。
#
# order[0:2]
#
# 返回 list。
#
# 三十二、对象协议思想
#
# 现在你应该开始看到：
#
# Python不是要求：
#
# 必须继承某个接口
#
# 而是：
#
# 只要对象实现对应特殊方法，就能参与对应语法。
#
# 例如：
#
# __iter__
# → 可迭代
#
# __len__
# → 支持 len
#
# __contains__
# → 支持 in
#
# __enter__ / __exit__
# → 支持 with
#
# 这其实和 Day 10 的：
#
# Protocol
# 鸭子类型
#
# 是一脉相承的。
#
# 三十三、运算符重载
#
# 比如金额对象：
#
# class Money:
#     def __init__(
#         self,
#         amount: Decimal,
#     ) -> None:
#         self.amount = amount
#
# 希望：
#
# money1 + money2
#
# 可以：
#
# def __add__(
#     self,
#     other: object,
# ):
#     if not isinstance(
#         other,
#         Money,
#     ):
#         return NotImplemented
#
#     return Money(
#         self.amount
#         + other.amount
#     )
# 三十四、调用
# money1 = Money(
#     Decimal("100.00")
# )
#
# money2 = Money(
#     Decimal("50.00")
# )
#
# total = money1 + money2
#
# 底层：
#
# money1.__add__(money2)
# 三十五、常见运算符
# 运算	方法
# +	__add__
# -	__sub__
# *	__mul__
# /	__truediv__
# //	__floordiv__
# %	__mod__
# ==	__eq__
# <	__lt__
# <=	__le__
# >	__gt__
# >=	__ge__
# 三十六、不要为了炫技重载运算符
#
# 比如：
#
# order1 + order2
#
# 到底什么意思？
#
# 合并订单？
# 金额相加？
# 商品合并？
#
# 语义不清楚。
#
# 这种就别做。
#
# 好的运算符重载应该：
#
# 一眼就符合直觉。
#
# 例如：
#
# Money + Money
# Vector + Vector
# Duration + Duration
#
# 比较合理。
#
# 三十七、super()
#
# 进入继承部分。
#
# class BaseService:
#     def __init__(
#         self,
#         name: str,
#     ) -> None:
#         self.name = name
#
# 子类：
#
# class OrderService(
#     BaseService
# ):
#     def __init__(
#         self,
#         name: str,
#         repository: object,
#     ) -> None:
#         super().__init__(
#             name
#         )
#
#         self.repository = (
#             repository
#         )
# 三十八、Java 类比
#
# Java：
#
# super(name);
#
# Python：
#
# super().__init__(name)
#
# 很像。
#
# 但 Python 的 super() 比 Java 更复杂。
#
# 因为 Python 支持：
#
# 多继承。
#
# 三十九、MRO 是什么
#
# MRO：
#
# Method Resolution Order
#
# 翻译：
#
# 方法解析顺序。
#
# 就是：
#
# 一个方法到底去哪一层找。
#
# 例如：
#
# class A:
#     def hello(self):
#         print("A")
#
#
# class B(A):
#     pass
#
#
# class C(B):
#     pass
#
# 调用：
#
# C().hello()
#
# 查找：
#
# C
# ↓
# B
# ↓
# A
# ↓
# object
#
# 这就是 MRO。
#
# 四十、查看 MRO
# print(
#     C.__mro__
# )
#
# 或者：
#
# print(
#     C.mro()
# )
#
# 会看到类似：
#
# C
# B
# A
# object
# 四十一、多继承
#
# Python支持：
#
# class A:
#     ...
#
#
# class B:
#     ...
#
#
# class C(A, B):
#     ...
#
# Java 普通类不支持多继承。
#
# Java：
#
# 一个 class 只能 extends 一个父类
# 多个 interface 可以 implements
#
# Python：
#
# class 可以继承多个 class
#
# 所以 MRO 很重要。
#
# 四十二、一个多继承例子
# class A:
#     def hello(self):
#         print("A")
#
#
# class B:
#     def hello(self):
#         print("B")
#
#
# class C(A, B):
#     pass
#
# 调用：
#
# C().hello()
#
# 输出：
#
# A
#
# 因为：
#
# C
# ↓
# A
# ↓
# B
# ↓
# object
# 四十三、换顺序
# class C(B, A):
#     pass
#
# 现在：
#
# C().hello()
#
# 输出：
#
# B
#
# 所以继承顺序会影响方法解析。
#
# 四十四、super 不是简单等于“父类”
#
# 这是一个很重要的点。
#
# 很多 Java 开发者误以为：
#
# super()
#
# 就是：
#
# 调当前类的直接父类。
#
# 不完全对。
#
# 更准确：
#
# super() 是沿着 MRO 找下一个实现。
#
# 这在多继承中特别关键。
#
# 四十五、合作式多继承
#
# 看：
#
# class A:
#     def process(self):
#         print("A")
#         super().process()
#
#
# class B:
#     def process(self):
#         print("B")
#         super().process()
#
#
# class C:
#     def process(self):
#         print("C")
#
#
# class D(A, B, C):
#     pass
#
# 执行：
#
# D().process()
#
# MRO：
#
# D
# A
# B
# C
# object
#
# 所以：
#
# A
# ↓
# super
# ↓
# B
# ↓
# super
# ↓
# C
#
# 输出：
#
# A
# B
# C
# 四十六、这里和 Java 最大区别
#
# Java：
#
# super.method()
#
# 基本就是调用明确父类逻辑。
#
# Python：
#
# super().method()
#
# 是：
#
# 按 MRO 向后继续找。
#
# 所以 Python 多继承能实现：
#
# cooperative multiple inheritance
#
# 合作式多继承。
#
# 四十七、菱形继承
#
# 经典问题：
#
#     A
#    / \
#   B   C
#    \ /
#     D
#
# Python：
#
# class A:
#     ...
#
#
# class B(A):
#     ...
#
#
# class C(A):
#     ...
#
#
# class D(B, C):
#     ...
#
# 如果设计不好，可能担心：
#
# A 被调用两次？
#
# Python 的 MRO 会给出一致顺序：
#
# D
# B
# C
# A
# object
#
# 正常使用 super() 可以避免重复调用。
#
# 四十八、MRO 用的是 C3 linearization
#
# 你当前不需要背算法。
#
# 知道：
#
# Python 会根据继承关系计算一个稳定、单调、无冲突的方法解析顺序。
#
# 即可。
#
# 以后看复杂框架时很有用。
#
# 四十九、Mixin
#
# Python 多继承最常见、最安全的用途之一：
#
# Mixin。
#
# Mixin 不是完整业务对象。
#
# 它只提供某个能力。
#
# 例如：
#
# class JsonMixin:
#     def to_dict(
#         self,
#     ) -> dict[str, object]:
#         return self.__dict__
#
# 然后：
#
# class Order(
#     JsonMixin
# ):
#     ...
#
# Order 获得：
#
# to_dict()
#
# 能力。
#
# 五十、常见 Mixin
#
# 比如：
#
# JsonMixin
# LoggingMixin
# TimestampMixin
# RetryMixin
# SerializationMixin
#
# 特点：
#
# 功能单一
# 通常不独立实例化
# 只提供一个横向能力
# 五十一、Java 类比 Mixin
#
# Java 没有 class 多继承。
#
# 比较接近：
#
# interface default method
#
# 或者：
#
# 组合 + 工具类
#
# Python Mixin 更自然。
#
# 五十二、Mixin 命名建议
#
# 通常名字明确带：
#
# Mixin
#
# 例如：
#
# class JsonSerializableMixin:
#     ...
#
# 让别人知道：
#
# 这是能力类，不是完整领域模型。
#
# 五十三、组合优于继承
#
# 这个原则在 Python 特别重要。
#
# 不推荐：
#
# class OrderService(
#     MySqlRepository,
#     RedisCache,
#     DingTalkSender,
# ):
#     ...
#
# 这会把：
#
# 数据库
# 缓存
# 通知
#
# 全部塞进继承关系。
#
# 更合理：
#
# class OrderService:
#     def __init__(
#         self,
#         repository: OrderRepository,
#         cache: Cache,
#         notifier: Notifier,
#     ) -> None:
#         self.repository = repository
#         self.cache = cache
#         self.notifier = notifier
#
# 这就是：
#
# Composition over inheritance
#
# 组合优于继承。
#
# 五十四、Java 类比
#
# Java Spring 里你其实天天在这么做：
#
# @Service
# public class OrderService {
#
#     private final OrderRepository repository;
#     private final RedisService redisService;
#     private final DingTalkService dingTalkService;
#
# }
#
# Python同样推荐：
#
# self.repository
# self.cache
# self.notifier
#
# 而不是靠多继承。
#
# 五十五、什么时候适合继承
#
# 适合：
#
# 确实存在 is-a 关系
#
# 例如：
#
# Dog is an Animal
#
# 或者框架要求：
#
# BaseModel
# Exception
# ABC
# 五十六、什么时候适合组合
#
# 如果是：
#
# has-a 关系
#
# 例如：
#
# OrderService has Repository
# OrderService has Cache
# OrderService has Notifier
#
# 就应该组合。
#
# 五十七、异常类就是很合理的继承
#
# 例如：
#
# class OrderError(Exception):
#     pass
#
#
# class OrderNotFoundError(
#     OrderError
# ):
#     pass
#
#
# class InvalidOrderStatusError(
#     OrderError
# ):
#     pass
#
# 这是合理继承：
#
# OrderNotFoundError
# is an
# OrderError
# 五十八、一个完整 Order 示例
# from collections.abc import Iterator
# from dataclasses import dataclass, field
# from decimal import Decimal
#
#
# @dataclass(slots=True)
# class OrderItem:
#     sku: str
#     price: Decimal
#     quantity: int
#
#     @property
#     def amount(self) -> Decimal:
#         return (
#             self.price
#             * self.quantity
#         )
#
#
# @dataclass(slots=True)
# class Order:
#     order_no: str
#     items: list[OrderItem] = field(
#         default_factory=list
#     )
#
#     def __len__(self) -> int:
#         return len(
#             self.items
#         )
#
#     def __iter__(
#         self,
#     ) -> Iterator[OrderItem]:
#         return iter(
#             self.items
#         )
#
#     def __contains__(
#         self,
#         sku: object,
#     ) -> bool:
#         if not isinstance(
#             sku,
#             str,
#         ):
#             return False
#
#         return any(
#             item.sku == sku
#             for item in self.items
#         )
#
#     def __getitem__(
#         self,
#         index: int,
#     ) -> OrderItem:
#         return self.items[
#             index
#         ]
#
#     @property
#     def total_amount(
#         self,
#     ) -> Decimal:
#         return sum(
#             (
#                 item.amount
#                 for item in self.items
#             ),
#             Decimal("0.00"),
#         )
# 五十九、现在 Order 可以这么用
# order = Order(
#     order_no="A001",
#     items=[
#         OrderItem(
#             sku="SKU001",
#             price=Decimal("100"),
#             quantity=2,
#         ),
#         OrderItem(
#             sku="SKU002",
#             price=Decimal("50"),
#             quantity=1,
#         ),
#     ],
# )
#
# 然后：
#
# len(order)
#
# 返回：
#
# 2
#
# 可以：
#
# for item in order:
#     print(item.sku)
#
# 可以：
#
# "SKU001" in order
#
# 返回：
#
# True
#
# 可以：
#
# order[0]
#
# 返回第一个商品。
#
# 这就是：
#
# 让领域对象遵守 Python 语言协议。
#
# 六十、什么时候应该实现这些魔术方法
#
# 原则：
#
# 只有当语义非常自然时才实现。
#
# 例如：
#
# len(order)
#
# 如果你定义成：
#
# 订单商品行数
#
# 很自然。
#
# "SKU001" in order
#
# 也很自然：
#
# SKU 是否存在于订单中。
#
# 但：
#
# order1 + order2
#
# 语义很模糊。
#
# 就不要硬实现。
#
# 六十一、Pythonic 不是“魔术越多越好”
#
# 真正 Pythonic 是：
#
# 让对象行为符合语言直觉。
#
# 而不是：
#
# 能重载的都重载
#
# 代码可读性永远优先。
#
# 六十二、__slots__ 复习
#
# 你 dataclass 写过：
#
# @dataclass(slots=True)
#
# 它会限制实例属性布局。
#
# 普通类：
#
# class Order:
#     pass
#
#
# order = Order()
#
# order.xxx = 123
#
# 随便可以加属性。
#
# slots：
#
# @dataclass(slots=True)
# class Order:
#     order_no: str
#
# 通常就不能：
#
# order.xxx = 123
#
# 这样做有几个好处：
#
# 减少实例内存
# 减少拼错属性名的风险
# 对象结构更明确
# 六十三、dataclass 本质帮你生成哪些东西
#
# 例如：
#
# @dataclass
# class Order:
#     order_no: str
#     status: str
#
# 大致帮你生成：
#
# __init__
# __repr__
# __eq__
#
# 根据配置还可能影响：
#
# __hash__
# ordering
# slots
# frozen
#
# 所以 dataclass 本质是：
#
# 自动生成常见对象协议代码。
#
# 六十四、order=True
#
# 例如：
#
# @dataclass(order=True)
# class Order:
#     amount: Decimal
#
# 会帮你生成：
#
# __lt__
# __le__
# __gt__
# __ge__
#
# 但默认按照字段顺序比较。
#
# 所以一定要谨慎。
#
# 六十五、字段顺序会影响比较
# @dataclass(order=True)
# class Order:
#     order_no: str
#     amount: Decimal
#
# 那么比较可能先比较：
#
# order_no
#
# 再比较：
#
# amount
#
# 这可能不是你的业务预期。
#
# 所以业务对象通常：
#
# 不建议随便 order=True。
#
# 六十六、今天的设计思想
#
# 今天真正应该记住：
#
# 1. 对象协议
#
# Python不是靠继承接口获得能力。
#
# 很多时候：
#
# 实现特殊方法
# → 获得语言能力
# 2. 组合优于继承
#
# 复杂业务依赖：
#
# Repository
# Cache
# Notifier
# Client
#
# 用组合。
#
# 3. 继承表示 is-a
#
# 例如：
#
# OrderNotFoundError is OrderError
# 4. Mixin 表示横向能力
#
# 例如：
#
# JsonMixin
# LoggingMixin
# 5. super 按 MRO 工作
#
# 不是简单：
#
# 父类
#
# 而是：
#
# MRO中的下一个类