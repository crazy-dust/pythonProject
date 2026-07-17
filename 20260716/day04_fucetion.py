# Day 4：函数进阶、作用域、闭包与装饰器
#
# Python 中，函数不仅是一段可调用代码，还是一个普通对象，可以：
# 赋值给变量
# 作为参数传递
# 作为返回值返回
# 保存在 list、dict 中
# 在函数内部定义
# 被装饰器包装
#
# Java 8 以后也有 Lambda、函数式接口，但 Python 的函数是一等对象，使用更自然。

# 一、今日目标
# 今天需要掌握：
#
# 位置参数与关键字参数
# 默认参数
# *args 与 **kwargs
# 参数解包
# 仅限位置参数与仅限关键字参数
# LEGB 作用域规则
# 函数作为参数和返回值
# Lambda 的适用边界
# 闭包
# 装饰器基础
# functools.wraps

# 二、位置参数和关键字参数
# 2.1普通函数：
def create_order(
        order_no: str,
        sku: str,
        quantity: int,
) -> dict[str, object]:
    return {
        "order_no": order_no,
        "sku": sku,
        "quantity": quantity,
    }


# 2.2位置参数调用
# 按照参数定义顺序传递：
order = create_order("A001", "SKU001", 2)

# 对应关系：
# "A001"   → order_no
# "SKU001" → sku
# 2        → quantity

# 位置参数的问题是，当参数较多时，可读性下降：
create_order("A001", "SKU001", 2)
# 不看函数定义，不容易确认每个值对应什么。

# 2.3关键字参数调用
# 优点：
# 可读性高
# 不依赖参数顺序
# 适合参数较多的业务函数
order = create_order(
    order_no="A001",
    sku="SKU001",
    quantity=2,
)
# 例如：
order = create_order(
    quantity=2,
    order_no="A001",
    sku="SKU001",
)

# 2.4位置参数和关键字参数混用
# 但位置参数必须在关键字参数之前。
# 可以：
create_order(
    "A001",
    sku="SKU001",
    quantity=2,
)


# 错误：会产生语法错误。
# create_order(
#     order_no="A001",
#     "SKU001",
#     2,
# )

# 三、默认参数
# 3.1
def create_order(
        order_no: str,
        sku: str,
        quantity: int = 1,
        status: str = "UNPAID",
) -> dict[str, object]:
    return {
        "order_no": order_no,
        "sku": sku,
        "quantity": quantity,
        "status": status,
    }


# 调用：
create_order("A001", "SKU001")

# 相当于：
create_order(
    order_no="A001",
    sku="SKU001",
    quantity=1,
    status="UNPAID",
)

# 也可以覆盖默认值：
create_order(
    order_no="A001",
    sku="SKU001",
    quantity=3,
    status="PAID",
)


# 3.2默认参数必须放在非默认参数后面
# 正确：
def query_orders(
        site_id: int,
        page: int = 1,
        page_size: int = 20,
) -> None:
    pass

# 错误：
# def query_orders(
#     page: int = 1,
#     site_id: int,
# ) -> None:
#     pass
# 会报错，因为必填参数不能放在默认参数后面。


# 四、*args：接收任意数量的位置参数
# 4.1
def calculate_sum(*numbers: int) -> int:
    print(type(numbers))
    return sum(numbers)

# 调用：
print(calculate_sum(1, 2, 3, 4))

# 输出：
# <class 'tuple'>
# 10

# *args 本质是一个 tuple：
# numbers == (1, 2, 3, 4)

# 参数名不一定必须叫 args：
def calculate_sum(*numbers: int) -> int:
    ...

# 推荐使用有业务语义的名字。

# 4.2 业务例子：合并多个订单号
def build_order_message(*order_nos: str) -> str:
    return ",".join(order_nos)


message = build_order_message(
    "A001",
    "A002",
    "A003",
)

print(message)


# 4.3 Java 类比
# Java 可变参数：
# public int calculateSum(int... numbers) {
#     ...
# }

# Python：
def calculate_sum(*numbers: int) -> int:
    ...

# 区别是 Python 中 numbers 是 tuple。

# 输出：
# A001,A002,A003


# 五、**kwargs：接收任意数量的关键字参数
# 5.1
def print_order_info(**order_info: object) -> None:
    print(type(order_info))

    for key, value in order_info.items():
        print(f"{key} = {value}")

# 调用：
print_order_info(
    order_no="A001",
    sku="SKU001",
    quantity=2,
    status="PAID",
)

# order_info 本质是一个字典：
{
    "order_no": "A001",
    "sku": "SKU001",
    "quantity": 2,
    "status": "PAID",
}


# 5.2 *args 和 **kwargs 同时使用
def demo(
    required: str,
    *args: object,
    **kwargs: object,
) -> None:
    print(required)
    print(args)
    print(kwargs)

# 调用：
demo(
    "A001",
    "SKU001",
    2,
    status="PAID",
    site_id=1001,
)

# 输出：
# A001
# ('SKU001', 2)
# {'status': 'PAID', 'site_id': 1001}

# 六、参数解包
#6.1 list / tuple 解包
# * 和 ** 不仅可以用在函数定义中，还能用在函数调用中。
def calculate_total(
    price: int,
    quantity: int,
    discount: int,
) -> int:
    return price * quantity * discount

# 参数存在 tuple 中：
params = (100, 2, 1)

# 6.2 普通调用：
calculate_total(
    params[0],
    params[1],
    params[2],
)

# 6.3 解包调用：
result = calculate_total(*params)
# *params 会将 tuple 拆成三个位置参数。

# 6.4 dict 解包
def create_order(
    order_no: str,
    sku: str,
    quantity: int,
) -> dict[str, object]:
    return {
        "order_no": order_no,
        "sku": sku,
        "quantity": quantity,
    }

# 参数字典：
order_params = {
    "order_no": "A001",
    "sku": "SKU001",
    "quantity": 2,
}

# 调用：
order = create_order(**order_params)

# 相当于：
order = create_order(
    order_no="A001",
    sku="SKU001",
    quantity=2,
)
# 注意：字典 key 必须与函数参数名对应。

# 6.5 集合和字典解包
# 6.5.1 合并列表：
list_a = [1, 2]
list_b = [3, 4]

result = [*list_a, *list_b]

print(result)
# 输出：
[1, 2, 3, 4]

# 6.5.2 合并字典：
base_order = {
    "order_no": "A001",
    "status": "UNPAID",
}

update_data = {
    "status": "PAID",
    "quantity": 2,
}

result = {
    **base_order,
    **update_data,
}

print(result)

# 输出：
{
    "order_no": "A001",
    "status": "PAID",
    "quantity": 2,
}
# 后面的字典会覆盖前面的同名 key。

# Python 3.9+ 也可以写：
result = base_order | update_data


# 七、仅限关键字参数
# 某些参数不希望调用者通过位置传递，可以在参数中使用 *。
from decimal import Decimal

def calculate_order_amount(
    price: Decimal,
    quantity: int,
    *,
    discount: Decimal = Decimal("1.00"),
    shipping_fee: Decimal = Decimal("0.00"),
) -> Decimal:
    return price * quantity * discount + shipping_fee

# * 后面的参数必须使用关键字传递。
# 正确：
calculate_order_amount(
    Decimal("100.00"),
    2,
    discount=Decimal("0.80"),
    shipping_fee=Decimal("10.00"),
)

# 错误：
# calculate_order_amount(
#     Decimal("100.00"),
#     2,
#     Decimal("0.80"),
#     Decimal("10.00"),
# )
# 会报：TypeError

# 为什么推荐关键字限定
# 看下面调用：
# calculate_order_amount(
#     Decimal("100.00"),
#     2,
#     Decimal("0.80"),
#     Decimal("10.00"),
# )

# 不看函数定义，很难看懂：
# 0.80 是折扣？
# 10.00 是运费？
# 还是税费？

# 使用关键字后：
calculate_order_amount(
    Decimal("100.00"),
    2,
    discount=Decimal("0.80"),
    shipping_fee=Decimal("10.00"),
)

# 示例一下
from decimal import Decimal

def calculate_order_amount(
    price: Decimal,
    quantity: int,
    *,
    discount: Decimal = Decimal("1.00"),
    shipping_fee: Decimal = Decimal("0.00"),
) -> Decimal:
    return price * quantity * discount + shipping_fee

result = calculate_order_amount(*(Decimal("1.1"), 2), discount=Decimal("1.00"), shipping_fee=Decimal("0.00"))
print(result)

# 业务语义更明确。
# 高级工程代码中，对于：
# 布尔开关
# 可选配置
# 金额参数
# 超时时间
# 重试次数
# 经常使用仅限关键字参数


# 八、仅限位置参数
# 使用 / 可以规定前面的参数只能按位置传递：
def contains(value: str, container: list[str], /) -> bool:
    return value in container

# 正确：
contains("A001", ["A001", "A002"])

# 错误：
# contains(
#     value="A001",
#     container=["A001", "A002"],
# )
# 这在普通业务代码中不如仅限关键字参数常用。
#
# 很多 Python 内置函数会使用仅限位置参数，主要为了：
# 保持 API 灵活
# 避免参数名成为公开接口
# 更接近底层实现
# 当前知道语法即可。

# 九、Python 参数完整顺序
# 完整参数顺序：
def function(
    positional_only,
    /,
    normal,
    *args,
    keyword_only,
    **kwargs,
):
    ...

# 示例：
def demo(
    a: int,
    /,
    b: int,
    *numbers: int,
    multiplier: int = 1,
    **options: object,
) -> None:
    print(a)
    print(b)
    print(numbers)
    print(multiplier)
    print(options)

# 当前阶段重点掌握：
# 普通参数
# 默认参数
# *args
# 仅限关键字参数
# **kwargs


# 十、作用域：LEGB 规则
# 10.1
# Python 查找变量时遵循 LEGB：
# L：Local，本地作用域
# E：Enclosing，外层函数作用域
# G：Global，模块全局作用域
# B：Built-in，内置作用域
# Local：本地作用域

def calculate() -> None:
    amount = 100
    print(amount)
# amount 只能在函数内部使用。
# 外部调用：
# print(amount)
# 会报：NameError

# 10.2 Global：全局作用域
DEFAULT_STATUS = "UNPAID"

def create_order() -> dict[str, str]:
    return {
        "status": DEFAULT_STATUS,
    }

# 函数内部可以读取全局变量。
# 但不要随便修改全局变量。

count = 0

def increase() -> None:
    global count
    count += 1

# global count 表示修改模块级变量。
# 虽然可以用，但业务代码中通常不推荐大量使用，因为：
# 隐式共享状态
# 难测试
# 并发不安全
# 调用结果依赖外部状态

# 更好的方式是通过参数和返回值传递：
def increase(count: int) -> int:
    return count + 1


# 10.3 Enclosing：外层函数作用域
# inner() 中找不到本地 message，会到外层函数查找。
# nonlocal
# 如果内部函数需要修改外层函数变量：
def outer() -> None:
    message = "订单处理"

    def inner() -> None:
        print(message)

    inner()


# 使用：
# 这里的 count 被保存了下来。
# 这就进入了闭包。
def create_counter():
    count = 0

    def increase() -> int:
        nonlocal count
        count += 1
        return count

    return increase

counter = create_counter()

print(counter())  # 1
print(counter())  # 2
print(counter())  # 3


# 十一、函数是一等对象
# 定义函数：
def validate_paid_order(order: dict[str, object]) -> bool:
    return order["status"] == "PAID"

# 可以赋值给变量：
validator = validate_paid_order

# 调用：
result = validator({
    "status": "PAID",
})

print(result)

# 注意：
validator = validate_paid_order
# 没有括号，表示把函数对象赋值给变量。

# 而： 有括号，表示立即执行函数，并将返回值赋值给变量。
# validator = validate_paid_order(...)


# 十二、函数作为参数：高阶函数
from collections.abc import Callable
from typing import Any

def filter_orders(
    orders: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    return [
        order
        for order in orders
        if predicate(order)
    ]

# 定义过滤规则：
def is_paid(order: dict[str, Any]) -> bool:
    return order["status"] == "PAID"

# 使用：
# 这里的 filter_orders 是高阶函数，因为它接收另一个函数作为参数。
orders = [
    {
        "order_no": "A001",
        "status": "PAID",
    },
    {
        "order_no": "A002",
        "status": "UNPAID",
    },
]
paid_orders = filter_orders(orders, is_paid)

# Java 类似：
# Python 不需要专门定义函数式接口。
# List<Order> filterOrders(
#     List<Order> orders,
#     Predicate<Order> predicate
# )


# 十三、Callable 类型标注
# Callable[[参数类型], 返回值类型]
# 例如：
# 表示：接收两个 int 参数, 返回一个 int
# 示例：
Callable[[int, int], int]

from collections.abc import Callable

def execute(
    operation: Callable[[int, int], int],
    a: int,
    b: int,
) -> int:
    return operation(a, b)
# 传入函数：
def add(a: int, b: int) -> int:
    return a + b
print(execute(add, 10, 20))


# 十四、Lambda 表达式
# 简单函数：
def double(number: int) -> int:
    return number * 2

# Lambda：
double = lambda number: number * 2

# 调用：
print(double(10))

# 但不要滥用 Lambda。
# 适合：
orders = [
    {
        "order_no": "A001",
        "amount": 100,
    },
    {
        "order_no": "A002",
        "amount": 500,
    },
]
orders.sort(
    key=lambda order: order["amount"],
)

# 或者：
large_orders = filter_orders(
    orders,
    lambda order: order["amount"] >= 500,
)

# 不适合复杂业务：
# 如果逻辑超过一行、需要异常处理或需要复用，应该写普通函数。
lambda order: ...


# 十五、函数作为返回值
from collections.abc import Callable
from decimal import Decimal

def create_amount_validator(
    min_amount: Decimal,
) -> Callable[[dict[str, object]], bool]:
    def validator(order: dict[str, object]) -> bool:
        amount = order["amount"]
        if not isinstance(amount, Decimal):
            return False
        return amount >= min_amount
    return validator

# 使用：
large_order_validator = create_amount_validator(
    Decimal("500.00"),
)

result = large_order_validator({
    "amount": Decimal("900.00"),
})

print(result)

# 外层函数执行完后，内部函数仍然记住：
# 这就是闭包。
min_amount = Decimal("500.00")


# 十六、什么是闭包

# 闭包需要满足：
# 函数内部定义了另一个函数
# 内部函数引用了外部函数变量
# 外部函数返回内部函数

# 示例：
def create_multiplier(
        multiplier: int,
):
    def multiply(value: int) -> int:
        return value * multiplier

    return multiply

# 使用：
double = create_multiplier(2)
triple = create_multiplier(3)

print(double(10))  # 20
print(triple(10))  # 30

# double 记住了 multiplier=2。
# triple 记住了 multiplier=3

# Java 类比
# Java Lambda 捕获外部变量：
# Function<Integer, Integer> createMultiplier(int multiplier) {
#     return value -> value * multiplier;
# }
# 思想相似。
# Python 闭包后面是理解装饰器的基础。


# 十七、装饰器基础
# 假设多个函数都需要打印执行日志。
# 普通方式：
def sync_order() -> None:
    print("开始执行")
    print("同步订单")
    print("执行完成")

# 如果很多函数都这样写，会产生重复代码。
# 装饰器可以在不修改业务函数主体的情况下增加功能。

# 最基础的装饰器
from collections.abc import Callable
from typing import Any

def log_execution(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"开始执行：{func.__name__}")

        result = func(*args, **kwargs)

        print(f"执行完成：{func.__name__}")
        return result

    return wrapper

# 使用：
@log_execution
def sync_order(order_no: str) -> str:
    print(f"同步订单：{order_no}")
    return "SUCCESS"

# 调用：
result = sync_order("A001")
print(result)

# 输出：
# 开始执行：sync_order
# 同步订单：A001
# 执行完成：sync_order
# SUCCESS


# 十八、装饰器语法本质
# 下面写法：
@log_execution
def sync_order(order_no: str) -> str:
    ...

# 本质等价于：
def sync_order(order_no: str) -> str:
    ...

sync_order = log_execution(sync_order)

# 执行过程：
# 原 sync_order 函数
#     ↓
# 传给 log_execution
#     ↓
# 返回 wrapper
#     ↓
# 新的 sync_order 实际指向 wrapper

# 所以调用：
sync_order("A001")

# 真正执行的是：
# wrapper("A001")
# 然后 wrapper 内部再执行原函数。


# 十九、为什么 wrapper 使用 *args 和 **kwargs
# 如果装饰器只写：
def wrapper(order_no: str):
    ...

# 它只能包装固定参数形式的函数。
# 使用：
def wrapper(*args: Any, **kwargs: Any) -> Any:
    ...

# 就可以适配不同参数的函数：
# sync_order("A001")
# calculate_amount(
#     price=Decimal("100.00"),
#     quantity=2,
# )


# 二十、装饰器必须使用 functools.wraps
# 前面的装饰器有一个问题：
print(sync_order.__name__)
# 可能输出：wrapper

# 因为原函数被包装函数替换了。
# 正确写法：
from collections.abc import Callable
from functools import wraps
from typing import Any


def log_execution(
    func: Callable[..., Any],
) -> Callable[..., Any]:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"开始执行：{func.__name__}")

        result = func(*args, **kwargs)

        print(f"执行完成：{func.__name__}")
        return result

    return wrapper

# @wraps(func) 会保留原函数的：
# 函数名
# 文档字符串
# 类型信息
# 模块信息
# 生产代码写装饰器，应该养成使用 @wraps 的习惯。


# 二十一、带参数的装饰器
# 例如希望控制重试次数：
from collections.abc import Callable
from functools import wraps
from typing import Any


def retry(
    max_attempts: int,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

    def decorator(
        func: Callable[..., Any],
    ) -> Callable[..., Any]:

        @wraps(func)
        def wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            last_error: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    print(
                        f"第{attempt}次执行失败：{error}"
                    )

            if last_error is not None:
                raise last_error

            raise RuntimeError("重试执行异常")

        return wrapper

    return decorator

# 使用：
@retry(max_attempts=3)
def call_api() -> str:
    raise TimeoutError("接口超时")

# 这里有三层函数：
# retry(max_attempts)
#     decorator(func)
#         wrapper(*args, **kwargs)
#
# 当前先理解结构即可，后面会专门深入装饰器。



# 二十二、闭包的经典坑：延迟绑定
# 看下面代码：
functions = []

for index in range(3):
    functions.append(lambda: index)

for function in functions:
    print(function())

# 你可能以为输出：
# 0
# 1
# 2

# 实际输出：
# 2
# 2
# 2

# 原因是 Lambda 保存的不是每轮 index 的值，而是这个变量本身。
# 等真正调用时，循环已经结束：
# index == 2
# 所以全部输出 2。

# 修复方式：
functions = []

for index in range(3):
    functions.append(
        lambda index=index: index
    )

# 输出：
# 0
# 1
# 2

# 这里利用了“默认参数在函数定义时求值一次”的规则。
# 这和之前可变默认参数的问题是同一个底层规则，但此处使用的是不可变整数，所以可以安全地固定当时的值。