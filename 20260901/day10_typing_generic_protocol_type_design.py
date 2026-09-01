# Day 10：Typing 深入、泛型、Protocol 与类型设计
#
# 今天这一课非常重要。
#
# 前面你已经会写：
#
# def clean_order(
#     raw_order: dict[str, Any],
# ) -> Order | None:
#     ...
#
# 今天开始要解决更高级的问题：
#
# Any 到底意味着什么？
# 为什么 Callable[..., Any] 不够精确？
# Java 的泛型 <T> 在 Python 怎么写？
# Python 为什么不需要 implements 也能实现“接口”？
# 怎么让 IDE 和类型检查器真正理解我们的代码？
#
# Python 的类型标注主要服务于 IDE、静态类型检查器和代码可维护性，Python 运行时通常不会自动强制执行这些类型。Python 3.14 推荐的现代泛型语法是在函数、类或类型别名名称后直接声明类型参数，例如 def func[T]...、class Box[T]...。


# 一、今天学什么
#
# 今天重点掌握：
#
# 1. Any 和 object 的区别
# 2. Union / | / None
# 3. 类型别名 type
# 4. 泛型函数
# 5. 泛型类
# 6. TypeVar 的本质
# 7. bound 和 constraints
# 8. Protocol
# 9. 泛型 Protocol
# 10. TypedDict
# 11. Callable 精确类型
# 12. ParamSpec
# 13. 给装饰器写出真正正确的类型
# 14. Python 与 Java 泛型/接口思想的区别


# 二、先搞明白：Python 类型标注不是 Java 类型系统
#
# Java：
#
# String name = 123;
#
# 编译直接失败。
#
# Python：
#
# name: str = 123
#
# Python 解释器通常仍然能运行。
#
# 也就是说：
#
# name: str
#
# 不是在告诉 Python：
#
# 运行时必须检查这是 str。
#
# 而是在告诉：
#
# PyCharm
# Pyright
# mypy
# ruff 等工具
#
# 我设计上认为这里应该是 str。
#
# 官方文档也明确说明，Python 运行时不会自动强制函数和变量的类型注解。
#
# 所以 Python 类型系统更接近：
#
# 静态设计约束 + IDE 协议
#
# 而不是 Java 那种编译期强制类型系统。


# 三、为什么还要认真写类型
#
# 因为大型项目里：
#
# def query_order(order_no):
#     ...
#
# 你不知道：
#
# order_no 是 str？
# int？
# None？
# UUID？
#
# 返回什么？
# dict？
# Order？
# None？
#
# 而：
#
# def query_order(
#     order_no: str,
# ) -> Order | None:
#     ...
#
# 信息量明显提高。
#
# 对于高级 Python 工程代码：
#
# 类型标注不是装饰，是 API 设计的一部分。


# 四、Any 到底是什么
#
# 你已经大量见过：
#
# from typing import Any
#
#
# raw_order: dict[str, Any]
#
# Any 可以理解成：
#
# 关闭这里的静态类型检查。
#
# 例如：
#
# value: Any = 123
#
# value.upper()
# value.append(1)
# value.foo.bar()
#
# 静态类型检查器通常不会像处理明确类型那样阻止你。
#
# 即使运行：
#
# value.upper()
#
# 最终可能：
#
# AttributeError


# 五、object 和 Any 完全不是一个意思
#
# 这两个特别容易混淆。
#
# value: object
#
# 表示：
#
# 我不知道具体是什么类型，但我仍然要求类型安全。
#
# 例如：
#
# def print_value(
#     value: object,
# ) -> None:
#     print(value)
#
# 什么都可以传：
#
# print_value(123)
# print_value("abc")
# print_value([])
#
# 但是你不能随便：
#
# value.upper()
#
# 因为类型检查器只知道：
#
# value 是 object
#
# 并不知道它是不是 str。
#
# 而：
#
# value: Any
#
# 基本相当于告诉类型检查器：
#
# 别管这里。


# 六、Java 类比 Any / object
#
# 可以粗略理解：
#
# Python object
# ≈ Java Object
#
# 但是：
#
# Python Any
# ≈ Java里关闭一部分类型检查
#
# Java 没有完全对应 Any 的东西。
#
# 所以：
#
# 类型	含义
# str	明确字符串
# object	任意对象，但仍保持类型安全
# Any	任意类型，并大幅放弃静态检查


# 七、什么时候应该用 Any
#
# 外部原始数据：
#
# dict[str, Any]
#
# 有时合理。
#
# 例如 Shopify 返回：
#
# raw_order: dict[str, Any]
#
# 因为值可能是：
#
# str
# int
# float
# bool
# list
# dict
# None
#
# 但是：
#
# 数据进入你自己的领域层以后，应该逐渐消灭 Any。
#
# 例如：
#
# 外部接口
# ↓
# dict[str, Any]
# ↓
# 清洗
# ↓
# Order
# ↓
# 业务逻辑
#
# 你之前的代码正是在这么做。


# 八、Union：一个值可能有多种类型
#
# 以前：
#
# from typing import Union
#
# value: Union[str, int]
#
# 现代 Python：
#
# value: str | int
#
# 你使用 Python 3.14，直接使用：
#
# str | int
#
# 即可。
#
# 比如：
#
# def parse_order_id(
#     value: str | int,
# ) -> str:
#     return str(value)
#
# 表示：
#
# value 可以是 str
# 也可以是 int


# 九、None 也是一种类型状态
#
# 例如：
#
# def find_order(
#     order_no: str,
# ) -> Order | None:
#     ...
#
# 意思：
#
# 找到
# → Order
#
# 没找到
# → None
#
# Java 很像：
#
# Optional<Order>
#
# 但并不完全等价。
#
# Python：
#
# order = find_order("A001")
#
# if order is None:
#     return
#
# print(order.status)
#
# 这里：
#
# if order is None:
#
# 以后，类型检查器知道：
#
# order 一定是 Order
#
# 这个过程叫：
#
# type narrowing，类型收窄。


# 十、类型收窄
#
# 比如：
#
# def normalize(
#     value: object,
# ) -> str:
#     if isinstance(value, str):
#         return value.strip()
#
#     return str(value)
#
# 进入：
#
# if isinstance(value, str):
#
# 之后，IDE知道：
#
# value: str
#
# 所以可以：
#
# value.strip()
#
# 这就是：
#
# object
# ↓
# isinstance
# ↓
# str


# 十一、类型别名
#
# 假设项目大量出现：
#
# dict[str, list[Order]]
#
# 你可以定义别名。
#
# Python 3.14 推荐：
#
# type OrdersByStatus = dict[
#     str,
#     list[Order],
# ]
#
# 使用：
#
# def group_orders(
#     orders: list[Order],
# ) -> OrdersByStatus:
#     ...
#
# type 声明类型别名是现代 Python 提供的专用语法。


# 十二、为什么类型别名有价值
#
# 否则：
#
# def group_orders(
#     orders: list[Order],
# ) -> dict[
#     OrderStatus,
#     list[Order],
# ]:
#     ...
#
# 到处重复。
#
# 可以：
#
# type OrderGroup = dict[
#     OrderStatus,
#     list[Order],
# ]
#
# 然后：
#
# def group_orders(
#     orders: list[Order],
# ) -> OrderGroup:
#     ...


# 十三、类型别名不是新类型
#
# 非常重要。
#
# type OrderNo = str
#
# 只是：
#
# 给 str 这个类型表达式一个别名。
#
# 所以：
#
# def query_order(
#     order_no: OrderNo,
# ) -> None:
#     ...
#
# 本质仍然接受 str。


# 十四、如果真的想区分 ID
#
# 比如：
#
# order_id
# user_id
# site_id
#
# 运行时都是：
#
# int
#
# 但你希望类型检查器不要搞混。
#
# 可以：
#
# from typing import NewType
#
#
# OrderId = NewType(
#     "OrderId",
#     int,
# )
#
# UserId = NewType(
#     "UserId",
#     int,
# )
#
# 然后：
#
# def query_order(
#     order_id: OrderId,
# ) -> None:
#     ...
#
# 这样类型检查器可以帮助发现：
#
# query_order(
#     UserId(1001)
# )
#
# 这种逻辑错误。官方文档也将 NewType 定义为创建静态意义上不同类型的工具


# 十五、进入今天核心：泛型
#
# Java：
#
# public <T> T first(List<T> values) {
#     return values.get(0);
# }
#
# 这里：
#
# <T>
#
# 表示：
#
# 具体类型暂时不知道，由调用的时候决定。
#
# Python 3.14：
#
# def first[T](
#     values: list[T],
# ) -> T:
#     return values[0]
#
# 是不是已经非常像 Java 了？


# 十六、调用泛型函数
# names = [
#     "Tom",
#     "Jerry",
# ]
#
# name = first(names)
#
# 类型检查器推断：
#
# T = str
#
# 所以：
#
# name: str
#
# 调用：
#
# numbers = [
#     1,
#     2,
#     3,
# ]
#
# number = first(numbers)
#
# 此时：
#
# T = int
#
# 所以：
#
# number: int


# 十七、为什么不能写 object
#
# 你可能想：
#
# def first(
#     values: list[object],
# ) -> object:
#     return values[0]
#
# 问题是：
#
# names: list[str]
#
# 调用以后返回：
#
# object
#
# 类型信息丢失了。
#
# 你明明知道输入：
#
# list[str]
#
# 输出必然：
#
# str
#
# 泛型就是解决这种：
#
# 多个位置之间存在类型关联。


# 十八、泛型最核心的意义
#
# 不是：
#
# 这里可以放任何类型。
#
# 那是 Any。
#
# 泛型真正表达的是：
#
# 这里是什么类型，其他相关位置必须保持相同类型关系。
#
# 例如：
#
# def first[T](
#     values: list[T],
# ) -> T:
#
# 这里建立：
#
# 输入元素类型 T
#       ↓
# 返回类型仍然 T


# 十九、Any 和泛型区别
#
# 这段：
#
# def first(
#     values: list[Any],
# ) -> Any:
#     ...
#
# 意味着：
#
# 进去什么
# ↓
# 我不知道出来什么
#
# 而：
#
# def first[T](
#     values: list[T],
# ) -> T:
#
# 意味着：
#
# 进去什么类型
# ↓
# 出来就是同一个类型
#
# 这个区别非常重要。


# 二十、Java 泛型直接对照
#
# Java：
#
# public static <T> T first(
#     List<T> values
# ) {
#     return values.get(0);
# }
#
# Python：
#
# def first[T](
#     values: list[T],
# ) -> T:
#     return values[0]
#
# 对应：
#
# Java <T>
#     ↓
# Python [T]
#
# Python 3.12+ 就支持这种类型参数语法，你现在的 3.14 可以直接使用


# 二十一、以前 Python 怎么写泛型
#
# 网上大量教程还会写：
#
# from typing import TypeVar
#
#
# T = TypeVar("T")
#
#
# def first(
#     values: list[T],
# ) -> T:
#     return values[0]
#
# 这是旧式写法。
#
# 不是错误。
#
# 为了兼容 Python 3.11 及更早版本仍然经常见到。Python 3.14 官方文档则更推荐专用的类型参数语法。
# 你现在学习：
#
# def first[T](...)
#
# 为主。
#
# 但一定要能看懂：
#
# T = TypeVar("T")
#
# 因为大量现有项目还是这么写。


# 二十二、泛型函数业务案例
#
# 比如：
#
# def first_or_none[T](
#     values: list[T],
# ) -> T | None:
#     if not values:
#         return None
#
#     return values[0]
#
# 调用：
#
# order = first_or_none(
#     orders
# )
#
# 如果：
#
# orders: list[Order]
#
# 那么：
#
# order: Order | None
#
# IDE完全知道。


# 二十三、再看一个函数
# def get_by_index[T](
#     values: list[T],
#     index: int,
# ) -> T | None:
#     if index < 0:
#         return None
#
#     if index >= len(values):
#         return None
#
#     return values[index]
#
# 可以用于：
#
# list[str]
# list[int]
# list[Order]
# list[OrderItem]
#
# 而类型不会丢。


# 二十四、泛型类
#
# Java：
#
# public class ApiResponse<T> {
#
#     private T data;
#
# }
#
# Python：
#
# from dataclasses import dataclass
#
#
# @dataclass(slots=True)
# class ApiResponse[T]:
#     success: bool
#     data: T
#
# 使用：
#
# response: ApiResponse[Order] = ApiResponse(
#     success=True,
#     data=order,
# )
#
# 此时：
#
# response.data
#
# 类型就是：
#
# Order


# 二十五、非常典型的 API 泛型
#
# 以后 FastAPI 中很有价值：
#
# @dataclass(slots=True)
# class PageResult[T]:
#     items: list[T]
#     total: int
#     page: int
#     page_size: int
#
# 订单：
#
# orders: PageResult[Order]
#
# 商品：
#
# products: PageResult[Product]
#
# 用户：
#
# users: PageResult[User]
#
# 这就和 Java：
#
# PageResult<Order>
# PageResult<Product>
# PageResult<User>
#
# 几乎一样。


# 二十六、泛型 Repository
#
# 例如：
#
# class Repository[T]:
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
# 那么：
#
# class OrderRepository(
#     Repository[Order]
# ):
#     ...
#
# 以后：
#
# repository.find_by_id(1)
#
# 类型检查器知道返回：
#
# Order | None


# 二十七、泛型的 bound
#
# 有时候我们不是允许任意 T。
#
# 假设：
#
# class Order:
#     amount: Decimal
#
# 我们希望泛型必须具有某种能力。
#
# 最简单先看继承：
#
# class BaseEntity:
#     id: int
#
# 可以：
#
# def get_id[
#     T: BaseEntity
# ](
#     entity: T,
# ) -> int:
#     return entity.id
#
# 这里：
#
# T: BaseEntity
#
# 表示：
#
# T 必须是 BaseEntity 或其子类型。
#
# 这叫：
#
# upper bound，上界约束。
#
# 官方 Python 3.14 泛型语法允许直接写这种 bound。


# 二十八、旧语法长什么样
#
# 旧式：
#
# from typing import TypeVar
#
#
# T = TypeVar(
#     "T",
#     bound=BaseEntity,
# )
#
# 然后：
#
# def get_id(
#     entity: T,
# ) -> int:
#     ...
#
# 现代：
#
# def get_id[
#     T: BaseEntity
# ](
#     entity: T,
# ) -> int:
#     ...
#
# 你现在优先掌握现代语法。


# 二十九、constraints 和 bound 不一样
#
# 还可以约束：
#
# def concat[
#     T: (str, bytes)
# ](
#     left: T,
#     right: T,
# ) -> T:
#     return left + right
#
# 表示：
#
# T 要么是 str
# 要么是 bytes
#
# 官方文档称这种写法为 constrained type variable；它和 bound 语义不同，一个 TypeVar 不能同时既是 bound 又是 constraints。
#
# 当前阶段记住：
#
# T: BaseClass
# → 上界
#
# T: (str, bytes)
# → 只能在指定类型集合里选


# 三十、开始讲 Protocol
#
# 这个是今天第二核心。
#
# 假设你要做支付：
#
# class PayPalGateway:
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 还有：
#
# class StripeGateway:
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 业务代码：
#
# def pay_order(
#     order: Order,
#     gateway: ???,
# ) -> bool:
#     return gateway.pay(order)
#
# 这里 gateway 应该写什么类型？


# 三十一、Java 的做法
#
# Java：
#
# public interface PaymentGateway {
#
#     boolean pay(Order order);
#
# }
#
# 然后：
#
# public class PayPalGateway
#         implements PaymentGateway {
#
#     @Override
#     public boolean pay(Order order) {
#         ...
#     }
# }
#
# 业务：
#
# public boolean payOrder(
#     Order order,
#     PaymentGateway gateway
# ) {
#     return gateway.pay(order);
# }


# 三十二、Python 的 Protocol
#
# Python：
#
# from typing import Protocol
#
#
# class PaymentGateway(Protocol):
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 业务：
#
# def pay_order(
#     order: Order,
#     gateway: PaymentGateway,
# ) -> bool:
#     return gateway.pay(order)
#
# 实现：
#
# class PayPalGateway:
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         print(
#             f"PayPal支付：{order.order_no}"
#         )
#         return True
#
# 注意：
#
# class PayPalGateway:
#
# 没有写：
#
# PaymentGateway
#
# 也没有：
#
# implements
#
# 但是类型检查器仍然认为它符合：
#
# PaymentGateway
#
# 只要结构匹配。Python 的 Protocol 正是用于这种 structural subtyping，也就是静态 duck typing


# 三十三、这就是 Python 的结构化类型
#
# Java：
#
# 你必须明确声明“我实现这个接口”。
#
# Python Protocol：
#
# 我不管你声明没声明，只要你长得像这个接口就行。
#
# 例如：
#
# class MockGateway:
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         return True
#
# 它也符合：
#
# PaymentGateway


# 三十四、鸭子类型
#
# Python 有一句经典思想：
#
# If it walks like a duck and quacks like a duck, it's a duck.
#
# 翻译成人话：
#
# 我不关心你是什么类，只关心你有没有我要的能力。
#
# 对于：
#
# PaymentGateway
#
# 业务只关心：
#
# gateway.pay(order)
#
# 并不关心：
#
# PayPal
# Stripe
# Mock
# 测试桩


# 三十五、Protocol = 带静态检查的鸭子类型
#
# 纯鸭子类型：
#
# def pay_order(
#     order,
#     gateway,
# ):
#     return gateway.pay(order)
#
# 灵活，但 IDE 不知道 gateway 是什么。
#
# Protocol：
#
# def pay_order(
#     order: Order,
#     gateway: PaymentGateway,
# ) -> bool:
#
# 既保持：
#
# 鸭子类型灵活性
#
# 又增加：
#
# IDE提示
# 静态检查
# 接口文档
#
# 这就是它真正的价值。


# 三十六、什么时候应该用 Protocol
#
# 非常适合：
#
# Repository
# PaymentGateway
# MessageSender
# Cache
# Storage
# HTTP Client
# Clock
# ID Generator
# AI Model Client
# LLM Client
#
# 例如以后 Agent 项目：
#
# class LLMClient(Protocol):
#     def chat(
#         self,
#         prompt: str,
#     ) -> str:
#         ...
#
# 然后：
#
# OpenAIClient
# ClaudeClient
# QwenClient
# MockLLMClient
#
# 都可以符合这个 Protocol。


# 三十七、Protocol 和 ABC 有什么区别
#
# 你 Day 5 学过 ABC。
#
# ABC：
#
# from abc import ABC, abstractmethod
#
#
# class PaymentGateway(ABC):
#
#     @abstractmethod
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 实现必须：
#
# class PayPalGateway(
#     PaymentGateway
# ):
#     ...
#
# 这是：
#
# nominal typing，名义类型。
#
# Protocol：
#
# class PaymentGateway(Protocol):
#     def pay(...) -> bool:
#         ...
#
# 实现不要求继承：
#
# class PayPalGateway:
#     ...
#
# 这是：
#
# structural typing，结构类型。


# 三十八、Java 类比
#
# 可以这样记：
#
# ABC
# ≈ Java abstract class / interface 的显式继承风格
#
# Protocol
# ≈ Java interface + Go interface + Duck Typing 的结合
#
# 尤其像 Go：
#
# 不需要声明 implements，只要方法集满足即可。


# 三十九、runtime_checkable
#
# 默认 Protocol 主要用于：
#
# 静态类型检查
#
# 如果你想：
#
# isinstance(
#     gateway,
#     PaymentGateway,
# )
#
# 需要：
#
# from typing import (
#     Protocol,
#     runtime_checkable,
# )
#
#
# @runtime_checkable
# class PaymentGateway(Protocol):
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         ...
#
# 不过要注意，运行时检查主要检查相应属性/方法是否存在，并不会完整验证方法参数和返回类型签名。官方文档明确强调了这一点。
#
# 所以：
#
# Protocol 最主要还是静态设计工具，不是运行时 Bean Validation。


# 四十、泛型 Protocol
#
# Repository 特别典型：
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
# 订单：
#
# def process_order(
#     repository: Repository[Order],
# ) -> None:
#     order = repository.find_by_id(
#         1001
#     )
#
# 这里类型检查器知道：
#
# order: Order | None
#
# Python 3.14 的 Protocol 可以直接配合现代泛型语法


# 四十一、实现不需要继承 Repository
# class MySqlOrderRepository:
#     def save(
#         self,
#         entity: Order,
#     ) -> None:
#         ...
#
#     def find_by_id(
#         self,
#         entity_id: int,
#     ) -> Order | None:
#         ...
#
# 只要结构匹配：
#
# Repository[Order]
#
# 即可。


# 四十二、TypedDict
#
# 你目前有很多：
#
# dict[str, Any]
#
# 例如：
#
# raw_order = {
#     "order_no": "A001",
#     "price": "100.00",
#     "quantity": 2,
#     "status": "PAID",
# }
#
# 如果一直写：
#
# dict[str, Any]
#
# IDE根本不知道有哪些字段。
#
# 可以使用：
#
# from typing import TypedDict


# 四十三、定义 RawOrder
# class RawOrder(
#     TypedDict
# ):
#     order_no: str
#     price: str
#     quantity: int
#     status: str
#
# 然后：
#
# def clean_order(
#     raw_order: RawOrder,
# ) -> Order:
#     ...
#
# IDE现在知道：
#
# raw_order["order_no"]
#
# 是：
#
# str
#
# 以及有哪些 key。


# 四十四、TypedDict 运行时还是 dict
#
# 非常重要。
#
# class RawOrder(TypedDict):
#     order_no: str
#
# 运行：
#
# raw_order = RawOrder(
#     order_no="A001",
# )
#
# 本质上仍然就是：
#
# dict
#
# TypedDict 的字段要求主要供静态类型检查使用，运行时实例本质还是普通 dict。
#
# 所以：
#
# isinstance(
#     raw_order,
#     dict,
# )
#
# 是：
#
# True


# 四十五、外部数据字段可能缺失
#
# 例如 Shopify 原始数据：
#
# class RawOrder(
#     TypedDict,
#     total=False,
# ):
#     order_no: str
#     price: str
#     quantity: int
#     status: str
#
# 这里：
#
# total=False
#
# 表示字段可以缺失。
#
# 于是你的清洗代码仍然可以：
#
# raw_order.get(
#     "order_no"
# )
#
# 这种非常适合：
#
# 外部 API
# JSON
# 第三方 webhook


# 四十六、TypedDict 和 dataclass 怎么选
#
# 这是你必须掌握的。
#
### TypedDict
#
# 适合：
#
# 外部原始字典
# JSON结构
# API返回
# 动态dict
#
# 例如：
#
# class ShopifyOrder(
#     TypedDict,
#     total=False,
# ):
#     id: int
#     email: str
#     line_items: list[dict[str, object]]
#
### dataclass
#
# 适合：
#
# 进入你自己系统后的领域模型
#
# 例如：
#
# @dataclass(slots=True)
# class Order:
#     order_no: str
#     amount: Decimal
#     status: OrderStatus
#
# 数据流：
#
# Shopify JSON
# ↓
# TypedDict / dict
# ↓
# 解析、校验
# ↓
# dataclass Order
#
# 非常合理。


# 四十七、Callable 复习
#
# 你已经写过：
#
# from collections.abc import Callable
#
#
# predicate: Callable[
#     [Order],
#     bool,
# ]
#
# 意思：
#
# 接受 Order
# 返回 bool
#
# Java：
#
# Predicate<Order>


# 四十八、Callable[..., Any] 的问题
#
# 你以前的装饰器：
#
# def log_execution(
#     func: Callable[..., Any],
# ) -> Callable[..., Any]:
#
# 意思基本是：
#
# 什么函数都行
# 参数我不管
# 返回类型我也不管
#
# 能用。
#
# 但类型信息丢了。
#
# 例如原函数：
#
# def get_order(
#     order_no: str,
# ) -> Order:
#     ...
#
# 经过装饰器：
#
# @log_execution
# def get_order(...):
#
# 类型检查器可能只能看到比较模糊的：
#
# Callable[..., Any]
#
# 我们希望做到：
#
# 原函数参数类型
# ↓
# 完整保留
#
# 原函数返回类型
# ↓
# 完整保留
#
# 这就轮到：
#
# ParamSpec


# 四十九、ParamSpec 是什么
#
# TypeVar：
#
# 保存一个“类型”
#
# 例如：
#
# T = Order
#
# ParamSpec：
#
# 保存一整个“函数参数列表”
#
# 例如：
#
# (
#     order_no: str,
#     include_items: bool = False,
# )
#
# 官方文档描述 ParamSpec 的核心用途，就是把一个 Callable 的参数类型原样转发给另一个 Callable，典型用途正是高阶函数和装饰器


# 五十、Python 3.14 精确装饰器
#
# 可以这样写：
#
# from collections.abc import Callable
# from functools import wraps
#
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
#         print(
#             f"开始执行："
#             f"{func.__name__}"
#         )
#
#         result = func(
#             *args,
#             **kwargs,
#         )
#
#         print(
#             f"执行完成："
#             f"{func.__name__}"
#         )
#
#         return result
#
#     return wrapper
#
# 这一段很高级，我们拆开。


# 五十一、P 是什么
# **P
#
# 表示：
#
# 一整套函数参数。
#
# 假设被装饰函数：
#
# def query_order(
#     order_no: str,
#     include_items: bool = False,
# ) -> Order:
#
# 那么可以理解：
#
# P =
# (
#     order_no: str,
#     include_items: bool = False
# )


# 五十二、R 是什么
# R
#
# 表示：
#
# 函数返回类型。
#
# 对于：
#
# query_order(...)
#
# 这里：
#
# R = Order


# 五十三、于是这一句怎么读
# func: Callable[P, R]
#
# 就是：
#
# func 是一个参数列表为 P、返回值为 R 的函数。
#
# 返回：
#
# Callable[P, R]
#
# 表示：
#
# 装饰完以后，仍然保持同样的参数列表和返回类型。


# 五十四、wrapper 参数
# def wrapper(
#     *args: P.args,
#     **kwargs: P.kwargs,
# ) -> R:
#
# 意思：
#
# 原函数的位置参数
# → P.args
#
# 原函数的关键字参数
# → P.kwargs
#
# 返回
# → R
#
# 这比以前：
#
# *args: Any
# **kwargs: Any
# -> Any
#
# 精确很多。


# 五十五、Java 类比 ParamSpec
#
# Java 泛型很擅长：
#
# Function<T, R>
# Predicate<T>
# BiFunction<T, U, R>
#
# 但是任意函数签名转发并不如 Python ParamSpec 自然。
#
# Python：
#
# Callable[P, R]
#
# 表达：
#
# 参数列表 P 不管有多少个参数，我全部保存下来。
#
# 这对装饰器尤其重要。


# 五十六、回头看 @wraps
#
# 你前几天问：
#
# @wraps(func)
#
# 现在可以看到两个东西其实解决不同问题：
#
# @wraps(func)
# ↓
# 运行时保留函数元信息
#
# ParamSpec + R
# ↓
# 静态类型系统保留函数签名
#
# 两者组合：
#
# @wraps(func)
# def wrapper(
#     *args: P.args,
#     **kwargs: P.kwargs,
# ) -> R:
#
# 才是更完整的高级装饰器写法。


# 五十七、这就是你学习路线开始串起来了
#
# Day 4：
#
# 装饰器
# *args
# **kwargs
# @wraps
#
# Day 8：
#
# 生成器
# Iterator
#
# Day 9：
#
# Protocol式资源协议
# with
#
# Day 10：
#
# Callable
# TypeVar
# ParamSpec
# Protocol
# Generic
#
# 开始不是孤立语法了，而是一套语言系统。


# 五十八、一个完整业务示例
#
# 假设：
#
# from dataclasses import dataclass
# from decimal import Decimal
# from typing import Protocol
#
#
# @dataclass(slots=True)
# class Order:
#     order_no: str
#     amount: Decimal
#
# 定义支付协议：
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
# PayPal：
#
# class PayPalGateway:
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         print(
#             f"PayPal支付："
#             f"{order.order_no}"
#         )
#
#         return True
#
# Mock：
#
# class MockGateway:
#     def pay(
#         self,
#         order: Order,
#     ) -> bool:
#         return True
#
# 业务：
#
# def pay_order(
#     order: Order,
#     gateway: PaymentGateway,
# ) -> bool:
#     return gateway.pay(order)
#
# 现在：
#
# 业务层
# ↓
# 依赖 PaymentGateway
#
# 而不是
# ↓
# 依赖 PayPalGateway
#
# 这就是：
#
# 依赖倒置。


# 五十九、Java 思维转换
#
# Java 里：
#
# interface
# ↓
# implements
# ↓
# Spring注入
#
# Python 很多时候：
#
# Protocol
# ↓
# 结构匹配
# ↓
# 直接传对象
#
# 不需要为了接口专门：
#
# class PayPalGateway(
#     PaymentGateway
# ):
#
# 当然也可以显式继承，但不是必须。


# 六十、泛型 + Protocol + 依赖注入
#
# 你以后很可能写：
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
# 订单 Service：
#
# class OrderService:
#     def __init__(
#         self,
#         repository: Repository[Order],
#     ) -> None:
#         self.repository = repository
#
# 然后可以注入：
#
# MySQL实现
# Redis实现
# Mock实现
# 内存实现
#
# 这已经和 Java 高级工程设计非常接近



# 六十一、一个很重要的坑：list 泛型通常是 invariant
#
# 假设：
#
# class Animal:
#     pass
#
#
# class Cat(Animal):
#     pass
#
#
# class Dog(Animal):
#     pass
#
# 直觉可能认为：
#
# list[Cat]
#
# 可以当：
#
# list[Animal]
#
# 使用。
#
# 实际上类型系统通常不允许。
#
# 为什么？
#
# 假设：
#
# def add_animal(
#     animals: list[Animal],
# ) -> None:
#     animals.append(
#         Dog()
#     )
#
# 然后你传：
#
# cats: list[Cat]
#
# 如果允许：
#
# add_animal(cats)
#
# 那么 cats 里面突然出现：
#
# Dog
#
# 类型就被破坏了。
#
# 所以：
#
# Cat 是 Animal
#
# 不意味着：
#
# list[Cat] 是 list[Animal]
#
# 这叫：
#
# invariance，不变。


# 六十二、只读场景可以考虑 Iterable / Sequence
#
# 如果函数只是读：
#
# from collections.abc import Sequence
#
#
# def print_animals(
#     animals: Sequence[Animal],
# ) -> None:
#     for animal in animals:
#         print(animal)
#
# 这类抽象通常比：
#
# list[Animal]
#
# 更加灵活。
#
# 所以类型设计还有一个原则：
#
# 参数尽量接受你真正需要的最小能力。
#
# 比如只需要遍历：
#
# 不要：
#
# def process(
#     orders: list[Order],
# ):
#
# 可以：
#
# from collections.abc import Iterable
#
#
# def process(
#     orders: Iterable[Order],
# ) -> None:
#     ...
#
# 因为你其实不关心它是不是 list。
#
# 可能传：
#
# list
# tuple
# generator
# 数据库结果
# 文件流
#
# 这又和 Day 8 串起来了。


# 六十三、当前阶段类型设计原则
#
# 建议你以后按照这个优先级思考：
#
# 明确类型
# >
# Protocol / Iterable 等抽象能力
# >
# object
# >
# Any
#
# 不要动不动：
#
# Any
#
# Any 应该是：
#
# 类型系统逃生舱。
#
# 而不是：
#
# 默认类型。