# 六十四、Day 10 作业 1：泛型函数
#
# 实现：
#
# def first_or_none[T](
#     items: list[T],
# ) -> T | None:
#     ...
#
# 测试：
#
# list[str]
# list[int]
# list[Order]
#
# 要求 IDE 能正确推断返回类型。


# 六十五、作业 2：泛型分页对象
#
# 实现：
#
# @dataclass(slots=True)
# class PageResult[T]:
#     items: list[T]
#     total: int
#     page: int
#     page_size: int
#
# 创建：
#
# PageResult[Order]
# PageResult[str]


# 六十六、作业 3：PaymentGateway Protocol
#
# 定义：
#
# class PaymentGateway(
#     Protocol
# ):
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 实现：
#
# PayPalGateway
# MockGateway
#
# 注意：
#
# 两个实现类都不要继承 PaymentGateway。
#
# 然后：
#
# def pay_order(
#     order: Order,
#     gateway: PaymentGateway,
# ) -> bool:
#     ...


# 六十七、作业 4：Repository Protocol
#
# 实现：
#
# class Repository[T](
#     Protocol
# ):
#     def save(
#         self,
#         entity: T,
#     ) -> None:
#         ...
#
#     def find_by_id(
#         self,
#         entity_id: int,
#     ) -> T | None:
#         ...
#
# 再实现：
#
# class MemoryOrderRepository:
#     ...
#
# 内部使用：
#
# dict[int, Order]


# 六十八、作业 5：TypedDict
#
# 将 Day 6：
#
# dict[str, Any]
#
# 改成：
#
# class RawOrder(
#     TypedDict,
#     total=False,
# ):
#     order_no: str
#     sku: str
#     price: str
#     quantity: int | str
#     status: str
#
# 然后：
#
# def clean_order(
#     raw_order: RawOrder,
# ) -> Order | None:
#     ...


# 六十九、作业 6：升级装饰器
#
# 把原来的：
#
# def log_execution(
#     func: Callable[..., Any],
# ) -> Callable[..., Any]:
#
# 升级成：
#
# def log_execution[**P, R](
#     func: Callable[P, R],
# ) -> Callable[P, R]:
#     ...
#
# wrapper：
#
# @wraps(func)
# def wrapper(
#     *args: P.args,
#     **kwargs: P.kwargs,
# ) -> R:
#     ...
#
# 这是今天含金量最高的一道作业。


# 七十、加分题
#
# 定义：
#
# class Serializer[T](
#     Protocol
# ):
#     def serialize(
#         self,
#         value: T,
#     ) -> str:
#         ...
#
#     def deserialize(
#         self,
#         value: str,
#     ) -> T:
#         ...
#
# 实现：
#
# OrderSerializer
#
# 让：
#
# Serializer[Order]
#
# 完整工作。


# 七十一、今天必须彻底搞懂的对应关系
# Java	            Python
# Object	        object
# <T>	            [T]
# T extends X	    T: X
# List<T>	        list[T]
# Optional<T>	    T | None
# interface	        Protocol
# implements	    Protocol 下可以不需要
# Predicate<T>	    Callable[[T], bool]
# DTO Map	        TypedDict
# 泛型返回关联	    Type parameter
# 任意函数签名转发	    ParamSpec


# Day 10 最重要的五句话
#
# 第一：
#
# Any 是放弃类型检查，object 是“未知具体类型但仍保持类型安全”。
#
# 第二：
#
# 泛型不是“什么类型都可以”，而是“多个位置之间保持类型关系”。
#
# 比如：
#
# def first[T](
#     values: list[T],
# ) -> T:
#
# 核心是：
#
# 输入T → 输出仍然T
#
# 第三：
#
# Protocol 是 Python 对“接口”的高级表达：不要求显式 implements，只要求结构满足。
#
# 第四：
#
# TypedDict 用来描述外部 dict，dataclass 用来表达进入领域后的对象。
#
# 第五：
#
# TypeVar 保存“一个类型”，ParamSpec 保存“整套函数参数”。
#
# 而你前几天的装饰器：
#
# @wraps(func)
# def wrapper(
#     *args,
#     **kwargs,
# ):
#
# 升级到今天就是：
#
# def log_execution[**P, R](
#     func: Callable[P, R],
# ) -> Callable[P, R]:
#
#     @wraps(func)
#     def wrapper(
#         *args: P.args,
#         **kwargs: P.kwargs,
#     ) -> R:
#         return func(
#             *args,
#             **kwargs,
#         )
#
#     return wrapper
#
# 这已经开始进入真正的高级 Python 工程代码了。