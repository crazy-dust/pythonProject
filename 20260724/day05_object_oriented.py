# # Day 5：类、对象、Dataclass、枚举与数据建模


# Python 面向对象强调：
    # 默认公开，按约定封装
    # 少写样板代码
    # 优先组合，谨慎继承
    # 数据对象优先使用 dataclass
    # 行为和数据放在合适的位置
    # 使用属性、协议和枚举表达业务约束


# 一、今日目标
# 今天完成后，你应该掌握：
#
# 内容	                目标
# 普通类	                能定义实例属性和实例方法
# 类属性	                理解实例属性与类共享属性
# @classmethod	        编写替代构造方法
# @staticmethod	        编写与实例无关的类内工具函数
# @property	            控制属性读取和修改
# dataclass	            快速定义业务数据模型
# field(default_factory=...)	正确处理可变默认值
# Enum / StrEnum	    建立状态枚举
# 组合与继承	            做出正确设计选择
# Protocol / ABC	    表达接口和抽象能力


# 二、最基础的类
# Java：
# public class Order {
#     private String orderNo;
#     private String status;
#
#     public Order(String orderNo, String status) {
#         this.orderNo = orderNo;
#         this.status = status;
#     }
# }

# Python：
class Order:
    def __init__(self, order_no: str, status: str) -> None:
        self.order_no = order_no
        self.status = status

order = Order("A001", "PAID")
print(order.order_no)
print(order.status)


# 三、self 是什么
class Order:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no

    def print_order_no(self) -> None:
        print(self.order_no)

# 调用：
order = Order("A001")
order.print_order_no()

# 表面上是：
order.print_order_no()

# 本质可以理解成：
Order.print_order_no(order)

# 所以 self 就是当前实例对象，类似 Java 的 this。
# 区别是：
    # this 是 Java 关键字
    # self 不是 Python 关键字，只是社区强约定
    # 实例方法第一个参数必须接收当前实例，习惯命名为 self

# 不要写成：
def print_order_no(this):
    ...

# 虽然能运行，但严重违反 Python 习惯。


# 四、实例属性
class Order:
    def __init__(
        self,
        order_no: str,
        status: str,
    ) -> None:
        self.order_no = order_no
        self.status = status

# 这里：
# self.order_no
# self.status
# 都是实例属性。

# 不同实例互不影响：
order1 = Order("A001", "PAID")
order2 = Order("A002", "UNPAID")

order1.status = "SHIPPED"

print(order1.status)  # SHIPPED
print(order2.status)  # UNPAID


# 五、Python 默认没有严格的 private
# Java：
# private String orderNo;

# Python 通常写：
# self.order_no = order_no

# 默认可以从外部访问。
# Python 更依赖约定。

# 单下划线
# self._internal_status = "PAID"
# 含义是：
    # 这是内部实现，外部不要随便访问。
    # 但技术上仍然能访问：
    # print(order._internal_status)

# 双下划线
# self.__secret = "value"
# Python 会进行名称改写，变成类似：
# _Order__secret

# 但这并不是真正安全的 private，只是避免子类和外部代码意外冲突。

# 生产代码通常优先：
# _internal_value

# 而不是大量使用：
# __private_value

# 示例
from decimal import Decimal

class Order:
    def __init__(
        self,
        order_no: str,
        amount: Decimal,
        status: str,
    ) -> None:
        self.order_no = order_no
        self.amount = amount
        self.status = status

    def is_paid(self) -> bool:
        return self.status == "PAID"

    def change_status(self, new_status: str) -> None:
        self.status = new_status

order = Order(
    order_no="A001",
    amount=Decimal("100.00"),
    status="PAID",
)
print(order.is_paid())
order.change_status("SHIPPED")
print(order.status)


# 七、类属性
# 实例属性属于每一个对象，类属性由所有实例共享。
class Order:
    platform = "SHOPIFY"

    def __init__(self, order_no: str) -> None:
        self.order_no = order_no

# 访问：
print(Order.platform)

order1 = Order("A001")
order2 = Order("A002")

# 都输出：
# SHOPIFY
print(order1.platform)
print(order2.platform)

# 修改类属性：
Order.platform = "TIKTOK"

# 所有没有自己覆盖该属性的实例都会看到新值。
# 类属性的覆盖问题
order1.platform = "AMAZON"

# 这不是修改类属性，而是在 order1 上创建了一个同名实例属性。
print(order1.platform)  # AMAZON
print(order2.platform)  # TIKTOK
print(Order.platform)   # TIKTOK

# 属性查找顺序大致是：
# 先找实例属性
# 再找类属性
# 再找父类属性


# 八、类属性可变对象的坑
# 错误：
class Order:
    tags: list[str] = []

# 所有实例共享同一个列表：
order1 = Order()
order2 = Order()
order1.tags.append("HIGH_RISK")

print(order2.tags)
# order2 也会看到：
['HIGH_RISK']

# 这和之前的“可变默认参数”本质类似：多个对象共享同一个可变对象。
# 正确做法是放到实例中：

class Order:
    def __init__(self) -> None:
        self.tags: list[str] = []


# 九、@classmethod
# 类方法第一个参数通常叫 cls，代表当前类。
class Order:
    def __init__(
        self,
        order_no: str,
        status: str,
    ) -> None:
        self.order_no = order_no
        self.status = status

    @classmethod
    def create_unpaid(cls, order_no: str) -> "Order":
        return cls(
            order_no=order_no,
            status="UNPAID",
        )

# 使用：
order = Order.create_unpaid("A001")

# 输出：
print(order.status)  # UNPAID

# 这叫替代构造方法。
# Java 类似：
    # public static Order createUnpaid(String orderNo) {
    #     return new Order(orderNo, "UNPAID");
    # }

# 但 Python 中使用 cls(...) 而不是写死 Order(...)，对子类更友好。

# 从字典创建对象
from typing import Any
class Order:
    def __init__(
        self,
        order_no: str,
        status: str,
    ) -> None:
        self.order_no = order_no
        self.status = status

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Order":
        return cls(
            order_no=str(data["order_no"]).strip(),
            status=str(data["status"]).strip().upper(),
        )

# 调用：
order = Order.from_dict({
    "order_no": " A001 ",
    "status": " paid ",
})


# 十、@staticmethod
# 静态方法不接收 self，也不接收 cls。
class Order:
    @staticmethod
    def normalize_status(status: str) -> str:
        return status.strip().upper()

# 调用：
status = Order.normalize_status(" paid ")

# 输出：
# PAID

# 静态方法适合：
# 逻辑概念上属于这个类
# 但不需要读取实例
# 也不需要读取或创建当前类

# 不过不要把所有工具函数都塞进类里。

# 如果函数跟类关系不强，直接写模块级函数更 Pythonic：
def normalize_status(status: str) -> str:
    return status.strip().upper()


# 十一、三种方法的区别
    # 类型	    第一个参数	主要用途
    # 实例方法	self	    操作当前对象
    # 类方法	    cls	        替代构造、操作类级信息
    # 静态方法	无特殊参数	与类有关的独立工具逻辑
# 示例：
class Order:
    platform = "SHOPIFY"

    def print_order(self) -> None:
        print(self.order_no)

    @classmethod
    def create_default(cls, order_no: str) -> "Order":
        return cls(order_no)

    @staticmethod
    def normalize_order_no(order_no: str) -> str:
        return order_no.strip().upper()


# 十二、__repr__：开发者可读表示
# 普通类：
class Order:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no

# 打印：
order = Order("A001")
print(order)

# 可能得到：
# <__main__.Order object at 0x...>
# 不直观。

# 实现 __repr__：
# !r 会使用值的 repr() 表示，字符串会带引号，更适合调试。
class Order:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no

    def __repr__(self) -> str:
        return f"Order(order_no={self.order_no!r})"

# 输出：
order = Order("A001")
print(order)


# 十三、__str__ 与 __repr__
class Order:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no

    def __str__(self) -> str:
        return f"订单号：{self.order_no}"

    def __repr__(self) -> str:
        return f"Order(order_no={self.order_no!r})"

order = Order("A001")

print(str(order))
print(repr(order))

# 输出：
    # 订单号：A001
    # Order(order_no='A001')

# 一般理解：
    # __str__：面向用户
    # __repr__：面向开发者和调试


# 十四、对象相等性
# 普通类默认比较对象身份：
class Order:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no


order1 = Order("A001")
order2 = Order("A001")

print(order1 == order2)

# 结果通常是：
False

# 因为它们是两个不同对象。
# 可以实现：

class Order:
    def __init__(self, order_no: str) -> None:
        self.order_no = order_no

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented

        return self.order_no == other.order_no

# 但数据类会自动生成这些样板代码。


# 十五、dataclass：Python 数据对象首选
# 定义业务数据模型时，普通类有大量样板代码：
class Order:
    def __init__(
        self,
        order_no: str,
        status: str,
        amount: Decimal,
    ) -> None:
        self.order_no = order_no
        self.status = status
        self.amount = amount

# 使用 dataclass：
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Order:
    order_no: str
    status: str
    amount: Decimal

# 它会自动生成： 相当于是个lombok差不多
# __init__  构造方法
# __repr__  toString方法
# __eq__    equals

# 使用：
order = Order(
    order_no="A001",
    status="PAID",
    amount=Decimal("100.00"),
)

# 输出类似：
# Order(order_no='A001', status='PAID', amount=Decimal('100.00'))
print(order)


# 十六、dataclass 默认值
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Order:
    order_no: str
    status: str = "UNPAID"
    amount: Decimal = Decimal("0.00")

# 调用：
order = Order(order_no="A001")

# 注意规则和函数参数类似：
# 没有默认值的字段必须放在有默认值字段之前。

# 错误：
# 会报错。
# @dataclass
# class Order:
#     status: str = "UNPAID"
#     order_no: str


# 十七、可变默认值必须用 default_factory
# 错误：
from dataclasses import dataclass

# @dataclass
# class Order:
#     order_no: str
#     tags: list[str] = []

# dataclass 会直接阻止这种写法，因为它知道这是危险的共享可变对象。

# 正确：
from dataclasses import dataclass, field


@dataclass
class Order:
    order_no: str
    tags: list[str] = field(default_factory=list)

# 每个实例都会获得独立列表：
order1 = Order("A001")
order2 = Order("A002")

order1.tags.append("HIGH_RISK")

print(order1.tags)  # ['HIGH_RISK']
print(order2.tags)  # []

# 字典同理：
metadata: dict[str, str] = field(default_factory=dict)

# 集合：
labels: set[str] = field(default_factory=set)


# 十八、__post_init__
# dataclass 自动生成 __init__ 后，可以通过 __post_init__ 做归一化和校验。
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Order:
    order_no: str
    status: str
    amount: Decimal

    def __post_init__(self) -> None:
        self.order_no = self.order_no.strip()
        self.status = self.status.strip().upper()

        if not self.order_no:
            raise ValueError("订单号不能为空")

        if self.amount < Decimal("0"):
            raise ValueError("订单金额不能小于0")

# 调用：
order = Order(
    order_no=" A001 ",
    status=" paid ",
    amount=Decimal("100.00"),
)

# 得到：
print(order.order_no)  # A001
print(order.status)    # PAID


# 十九、不可变数据类
from dataclasses import dataclass
@dataclass(frozen=True)
class Address:
    country: str
    province: str
    city: str

# 创建后不能修改：
address = Address(
    country="US",
    province="CA",
    city="Los Angeles",
)

# 会报错。
# address.city = "New York"



# 适合：
    # 值对象
    # 配置对象
    # 坐标
    # 日期范围
    # 地址快照
    # 不希望被修改的领域数据

# Java 类似不可变 Value Object 或 record。


# 二十、slots=True
# Python 对象默认通常有一个：
# instance.__dict__
# 保存动态属性。

# 可以写：
@dataclass(slots=True)
class Order:
    order_no: str
    status: str

# 优点：
#     内存占用更小
#     属性访问可能略快
#     防止随意添加未定义属性

# 例如：
# order = Order("A001", "PAID")
# order.unknown = "value"

# 使用 slots=True 时会报错。
# 业务模型较稳定时，可以考虑：

@dataclass(slots=True)
class Order:
    ...

# Day 5 可以开始使用，但先理解普通 dataclass 更重要。


# 二十一、kw_only=True
@dataclass(kw_only=True)
class Order:
    order_no: str
    status: str
    amount: Decimal

# 必须通过关键字创建：
order = Order(
    order_no="A001",
    status="PAID",
    amount=Decimal("100.00"),
)

# 不能：
# Order("A001", "PAID", Decimal("100.00"))

# 业务字段较多时，我推荐：
# 可读性更好，也避免参数顺序错误。
@dataclass(slots=True, kw_only=True)
class Order:
    ...


# 二十二、枚举 Enum
# 不要在业务代码中到处写魔法字符串：
if order.status == "PAID":
    ...

# 容易出现：
#     PAID
#     paid
#     Paid
#     PAYED

# 使用枚举：
from enum import Enum
class OrderStatus(Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

# 使用：
status = OrderStatus.PAID
print(status)
print(status.value)


# 二十三、Python 3.14 推荐使用 StrEnum
# 你现在用 Python 3.14，可以直接使用：
from enum import StrEnum

class OrderStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

# StrEnum 同时具备字符串行为。
status = OrderStatus.PAID
print(status == "PAID")  # True
print(status.value)      # PAID

# 还可以使用自动值：
from enum import StrEnum, auto
class OrderStatus(StrEnum):
    UNPAID = auto()
    PAID = auto()
    SHIPPED = auto()

# 你的业务状态使用大写，所以建议显式写值。
# 但 auto() 对 StrEnum 通常会生成小写值，例如：
# unpaid
# paid
# shipped


# 二十四、字符串转枚举
# status = OrderStatus("PAID")

# 结果：
# OrderStatus.PAID

# 非法值：
# OrderStatus("UNKNOWN")
# 会抛出：
# ValueError

# 可以封装：
def parse_order_status(value: object) -> OrderStatus | None:
    if value is None:
        return None

    normalized_value = str(value).strip().upper()

    try:
        return OrderStatus(normalized_value)
    except ValueError:
        return None


# 二十五、枚举和数据类结合
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

class OrderStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

@dataclass(slots=True, kw_only=True)
class Order:
    order_no: str
    status: OrderStatus
    amount: Decimal

    def is_paid(self) -> bool:
        return self.status == OrderStatus.PAID

# 调用：
# 这样就不容易传入非法状态。
order = Order(
    order_no="A001",
    status=OrderStatus.PAID,
    amount=Decimal("100.00"),
)


# 二十六、@property
# 假设订单总金额是根据单价和数量计算的，不应该让外部随意赋值。

from decimal import Decimal

class OrderItem:
    def __init__(
        self,
        price: Decimal,
        quantity: int,
    ) -> None:
        self.price = price
        self.quantity = quantity

    @property
    def amount(self) -> Decimal:
        return self.price * self.quantity

# 使用时像属性：
item = OrderItem(
    price=Decimal("100.00"),
    quantity=2,
)
print(item.amount)

# 但本质会执行方法。
# 不需要写：
    # item.get_amount()

# 为什么 property 比 getter 更 Pythonic
# Java 常见：
    # order.getAmount();

# Python 更倾向：
#     order.amount
# 如果以后需要增加校验或计算，可以把普通属性升级成 property，调用方通常不需要改变。


# 二十七、property setter
class OrderItem:
    def __init__(
        self,
        price: Decimal,
        quantity: int,
    ) -> None:
        self.price = price
        self.quantity = quantity

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value <= 0:
            raise ValueError("数量必须大于0")

        self._quantity = value

# 调用：
item.quantity = 3

# 如果：
# 会抛出异常。
item.quantity = 0
# 不过对于简单数据模型，通常优先在 dataclass.__post_init__ 中校验，不要为每个字段机械地写 getter/setter。


# 二十八、继承
class Payment:
    def pay(self) -> None:
        raise NotImplementedError

class PayPalPayment(Payment):
    def pay(self) -> None:
        print("使用 PayPal 支付")

class StripePayment(Payment):
    def pay(self) -> None:
        print("使用 Stripe 支付")

# 可以运行，但直接用 NotImplementedError 只是简单手段。
# 更正式可使用抽象基类。


# 二十九、ABC 抽象基类
from abc import ABC, abstractmethod
from decimal import Decimal

class PaymentGateway(ABC):
    @abstractmethod
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        raise NotImplementedError

# 实现：
class PayPalGateway(PaymentGateway):
    def pay(self) -> str:
        return f"PayPal支付成功：{self.order_no}"

# 未实现抽象方法的子类不能实例化。
# 这和 Java 抽象类比较接近。


# Python多态示例
from abc import ABC, abstractmethod
from decimal import Decimal

class PaymentGateway(ABC):
    @abstractmethod
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        raise NotImplementedError

class PayPalGateway(PaymentGateway):
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        return f"PayPal支付成功：{order_no}，金额：{amount}"

class StripeGateway(PaymentGateway):
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        return f"Stripe支付成功：{order_no}，金额：{amount}"


class WeChatGateway(PaymentGateway):
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        return f"微信支付成功：{order_no}，金额：{amount}"


def process_payment(
    gateway: PaymentGateway,
    order_no: str,
    amount: Decimal,
) -> str:
    return gateway.pay(order_no, amount)


gateways: list[PaymentGateway] = [
    PayPalGateway(),
    StripeGateway(),
    WeChatGateway(),
]

for gateway in gateways:
    result = process_payment(
        gateway,
        order_no="ORDER-001",
        amount=Decimal("99.90"),
    )
    print(result)


# 三十、Protocol：Python 的结构化接口
# Java 接口要求显式实现：
# class PayPalGateway implements PaymentGateway

# Python Protocol 可以基于“长得像”来判断。
from decimal import Decimal
from typing import Protocol

class PaymentGateway(Protocol):
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        ...

# 实现类不需要声明继承：
class PayPalGateway:
    def pay(
        self,
        order_no: str,
        amount: Decimal,
    ) -> str:
        return "SUCCESS"

# 只要方法签名符合，类型检查器就认为它满足协议。
# 这就是鸭子类型：
# 如果它走起来像鸭子，叫起来像鸭子，那就把它当鸭子。

# 使用：
def execute_payment(
    gateway: PaymentGateway,
    order_no: str,
    amount: Decimal,
) -> str:
    return gateway.pay(order_no, amount)

# 创建具体的支付网关对象
paypal_gateway = PayPalGateway()

# 调用统一的支付函数
result = execute_payment(
    gateway=paypal_gateway,
    order_no="ORDER-20260724-001",
    amount=Decimal("99.90"),
)

print(result)


# 三十一、优先组合，而不是继承
# 不推荐为了复用一点代码建立很深的继承体系：
# BaseOrder
#   └── EcommerceOrder
#        └── CrossBorderOrder
#             └── TikTokOrder

# 更推荐组合：
@dataclass
class Address:
    country: str
    city: str


@dataclass
class OrderItem:
    sku: str
    quantity: int

@dataclass
class Order:
    order_no: str
    address: Address
    items: list[OrderItem]

# Order 拥有：
#     地址
#     商品明细
#     支付信息
#     物流信息

# 而不是把它们都通过继承塞进一个巨大基类。


# 三十五、哪些类应该用 dataclass
# 适合：
#     DTO
#     配置对象
#     领域值对象
#     文件解析结果
#     数据库查询结果
#     请求和响应中间模型
#     订单、明细、地址等结构化数据

# 不一定适合：
#     主要只有行为、数据很少的服务类
#     管理连接和资源生命周期的对象
#     框架要求特殊构造方式的类
#     复杂 ORM Entity
#     需要大量动态属性的对象

# 例如服务类没必要用：
@dataclass
class OrderService:
    ...

# 除非它确实只是注入几个依赖并保存。


# 三十六、Java 开发者容易犯的错误
# 1. 给每个字段写 Getter/Setter
# 不推荐：
def get_order_no(self) -> str:
    return self.order_no

def set_order_no(self, value: str) -> None:
    self.order_no = value

# 直接：
# 有控制需求时再使用 property。
order.order_no



# 2. 所有东西都写成类
# 不推荐：
# class MoneyUtils:
#     @staticmethod
    # def normalize_money(...):
    #     ...

# Python 更推荐模块级函数：
# def normalize_money(...):
#     ...

# 3. 继承层级过深
# Python 更倾向：
#     小类
#     小函数
#     组合
#     Protocol

# 4. 把 dict 永远当业务模型
# dict 适合：
#     外部不可信数据
#     JSON 原始数据
#     动态字段

# 但进入核心业务后，应该逐步转换为：
#     dataclass
#     Pydantic Model
#     ORM Model


# 三十九、Code Review 检查表
# 完成后检查：
#     是否避免机械编写 getter/setter？
#     实例属性是否在 __init__ 或 dataclass 中定义？
#     可变默认值是否使用 default_factory？
#     dataclass 是否正确使用 __post_init__？
#     业务状态是否使用 StrEnum？
#     计算字段是否适合使用 property？
#     类方法是否使用 cls 而不是写死类名？
#     静态方法是否真的属于该类？
#     是否优先使用组合而不是深层继承？
#     业务方法是否保护了状态流转？
#     今天必须记住
    #     self：当前实例
    #     cls：当前类
    #     实例方法：操作当前对象
    #     classmethod：替代构造、类级行为
    #     staticmethod：与实例和类状态无关的相关工具
    #     dataclass：减少数据对象样板代码
    #     default_factory：为每个实例创建独立可变对象
    #     __post_init__：初始化后归一化和校验
    #     property：以属性方式暴露计算或受控数据
    #     StrEnum：表达业务状态
    #     Protocol：按行为定义接口
    #     优先组合，谨慎继承

# 第五天最核心的一句话是：
    # 原始外部数据可以使用 dict，进入核心业务后，应尽快转换成有类型、有约束、有行为的领域对象。