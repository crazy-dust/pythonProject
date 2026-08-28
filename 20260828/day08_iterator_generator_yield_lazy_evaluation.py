# 今天的核心目标只有一句话：
#
###### 不要一次性把所有数据都算出来、放进内存；而是需要一个，生成一个。
#
# 这对你特别重要，因为你本身做过：
#
# 大批量订单
# 数据清洗
# API 拉取
# 分页
# 爬虫
# CSV / JSON
# 百万级数据处理
#
# 这些场景都非常适合生成器。



# 一、先看最直观的问题
# 假设有 1000 万个订单号。
# 普通写法：
def build_order_nos() -> list[str]:
    result = []

    for i in range(10_000_000):
        result.append(f"ORDER-{i}")

    return result

# 调用：
# orders = build_order_nos()

# 它会：
# 一次性创建 1000 万个字符串
# ↓
# 全部放进 list
# ↓
# 占大量内存
# ↓
# 函数执行完以后才返回

# 生成器写法：
def generate_order_nos():
    for i in range(10_000_000):
        yield f"ORDER-{i}"

# 调用：
orders = generate_order_nos()

# 这时根本没有生成 1000 万个订单。
# 只有你真正取值：
# for order_no in orders:
#     print(order_no)

# 它才：
# 要一个
# ↓
# 生成一个
# ↓
# 返回一个
# ↓
# 暂停
# ↓
# 下次继续

# 这就是：
# 惰性计算 Lazy Evaluation



# 二、先理解 iterable 和 iterator
# 这两个词很容易混。

# Iterable：可迭代对象
#
# 只要可以：
#
# for x in something:
#
# 通常就是 iterable。

# 例如：
# list
# tuple
# dict
# set
# str
# range

# 比如：
numbers = [1, 2, 3]
for number in numbers:
    print(number)
# numbers 是：
# Iterable



# 三、Iterator：迭代器
# 迭代器是：
# 真正负责“一个一个取值”的对象。
# 例如：
numbers = [1, 2, 3]

iterator = iter(numbers)

# 现在：
# iterator
# 就是迭代器。

# 可以：
print(next(iterator))
# 输出：
# 1

# 再：
print(next(iterator))
# 输出：
# 2

# 再：
print(next(iterator))
# 输出：
# 3

# 再调用：
# next(iterator)

# 会抛：
# StopIteration

# 表示：
# 没数据了。



# 四、Java 类比
# Java：
# List<Integer> numbers = List.of(1, 2, 3);
#
# Iterator<Integer> iterator = numbers.iterator();
#
# while (iterator.hasNext()) {
#     Integer value = iterator.next();
# }

# Python：
numbers = [1, 2, 3]
iterator = iter(numbers)
while True:
    try:
        value = next(iterator)
        print(value)
    except StopIteration:
        break

# 对应关系：
## Python	        Java
# iter(obj)	        obj.iterator()
# next(iterator)	iterator.next()
# StopIteration	    hasNext() == false
# Iterable	        Iterable<T>
# Iterator	        Iterator<T>



# 五、for 循环底层做了什么
# 你写：
for number in [1, 2, 3]:
    print(number)

# Python 底层逻辑可以理解为：
iterator = iter([1, 2, 3])
while True:
    try:
        number = next(iterator)
        print(number)
    except StopIteration:
        break

# 所以：
# for 本质就是不停调用 next()。
# 这点非常重要。



# 六、什么是生成器
# 生成器 Generator，本质上是一种特殊迭代器。
# 只要函数里面出现：
### yield
#
# 它就不是普通函数了，而是：
# 生成器函数

# 例如：
def generate_numbers():
    yield 1
    yield 2
    yield 3

# 调用：
result = generate_numbers()

# 注意：
# 此时不会执行函数体。

print(result)
# 你会看到类似：
# <generator object generate_numbers at ...>

# 真正执行：
print(next(result))
# 返回：
# 1

# 第二次：
print(next(result))
# 返回：
# 2

# 第三次：
print(next(result))
# 返回：
# 3

# 第四次：
# next(result)
# 抛：
# StopIteration



# 七、yield 和 return 最大区别
## 普通函数：
# def demo():
#     return 1
#     return 2

# 实际上：
# 执行到第一个 return
# ↓
# 函数结束
# 所以第二个永远不会执行。

## 生成器：
def demo():
    yield 101
    yield 202

# 执行：
generator = demo()

# 第一次：
print(next(generator))

# 执行到：
# yield 1
# 返回：
# 1

# 但是函数没有彻底结束。
# 只是：
# 暂停。

# 下一次：
print(next(generator))

# 从刚刚暂停的位置继续：
# yield 2
# 返回：
# 2



# 八、最关键的一句话
### yield 可以理解为：
### “先把这个值交出去，同时保存当前函数运行状态，下次从这里继续。”

# Java 普通方法没有完全对应的语言级机制。
# 你可以粗略类比：
# 普通函数 return
# ≈ Java return

# 生成器 yield
# ≈ 一个自动保存游标状态的 Iterator



# 九、看一个执行顺序
def generate():
    print("开始")

    yield 1

    print("生成第二个")

    yield 2

    print("结束")

# 调用：
g = generate()

# 这时候：
# 什么都不会打印
# 然后：
print(next(g))
# 执行：
# 开始
# 1

# 函数暂停在：
# yield 1

# 然后：
print(next(g))
# 执行：
# 生成第二个
# 2
# 再次暂停。

# 第三次：
# next(g)
# 执行：
# 结束
# 然后抛：
# StopIteration



# 十、生成器最适合分页 API
# 这个场景你非常常见。
# 假设 Shopify API 每页 100 条。
# 普通做法：
# def load_all_orders() -> list[dict]:
#     all_orders = []
#     page = 1
#
#     while True:
#         # orders = request_orders(page)
#         if not orders:
#             break
#         all_orders.extend(orders)
#         page += 1
#     return all_orders

# 问题：
# 100页
# ×
# 100条
# =
# 10000条全部放进内存
# 如果是几十万甚至几百万条，更明显。


### 生成器写法：
# def iter_orders():
#     page = 1
#
#     while True:
#         # orders = request_orders(page)
#         if not orders:
#             break
#         for order in orders:
#             yield order
#         page += 1
#
# # 使用：
# for order in iter_orders():
#     ...
    # process_order(order)

# 现在执行流程：
# 请求第一页
# ↓
# 逐条处理
# ↓
# 处理完第一页
# ↓
# 请求第二页
# ↓
# 逐条处理
# ↓
# ...
#
# 这就叫：
#
# 流式处理

# 十一、Java
# 对应
# Stream
# 思维

# Java：
# orders.stream()
# .filter(...)
# .map(...)
# .forEach(...);

# Python：
# (
# transform(order)
# for order in orders
# if is_valid(order)
# )

# 这种写法也是惰性的。



# 十二、生成器表达式

# 你之前写过：
# sum(
#     order["amount"]
#     for order in orders
# )

# 这里：
# order["amount"]
# for order in orders
# 不是 list comprehension。

# 而是：
# generator expression
# 生成器表达式。

# 对比：
# [
#     order["amount"]
#     for order in orders
# ]

# 这是list comprehension。
# 会：
# 一次性生成整个 list

# 而：
# (
#     order["amount"]
#     for order in orders
# )
# 是generator expression
# 会：
# 按需产生


# 十三、[] 和 () 的区别非常重要
# List comprehension
numbers = [
    i * 2 for i in range(1_000_000)
]
# 马上生成 100 万个元素。

# Generator expression
numbers = (
    i * 2 for i in range(1_000_000)
)
# 此时几乎没有生成数据。
# 只有：
# next(numbers)
# 才算一个。



# 十四、什么时候该 list，什么时候 generator
# 如果后续需要：
# len()
# 索引
# 切片
# 重复遍历
# 随机访问
# 用：list

# 例如：
# orders[10]
# orders[-1]
# len(orders)

# 如果只是：
# 一条一条处理
# 顺序消费
# 数据很多
# 只遍历一次
# 优先考虑：generator



# 十五、生成器只能消费一次
# 这个是坑。

g = (
    i for i in range(3)
)

# 第一次：
print(list(g))
# 输出：
# [0, 1, 2]

# 第二次：
print(list(g))
# 输出：
# []
# 为什么？
# 因为第一次已经消费完了。

# 这和：
# 数据库 ResultSet
# 文件流
# Iterator
# 很像。


# 十六、Java 类比
# Java：
# Iterator<Integer> iterator = ...

# 你调用完：
# next()
# next()
# next()

# 也不会自动回到开头。
# Python generator 同样如此。



# 十七、yield 可以放在循环里
# 最典型：
def even_numbers(
    max_value: int,
):
    for number in range(max_value + 1):
        if number % 2 == 0:
            yield number

# 使用：
for number in even_numbers(10):
    print(number)

# 输出：
# 0
# 2
# 4
# 6
# 8
# 10



# 十八、生成器可以无限生成
# 这个非常强。
def sequence():
    number = 1

    while True:
        yield number
        number += 1

# 这个理论上：
# 永远不会结束
# 但完全不会一次性把无限数据放进内存。

# 使用：
generator = sequence()

print(next(generator))
print(next(generator))
print(next(generator))

# 输出：
# 1
# 2
# 3



# 十九、订单 ID 生成器
# 比如你想产生批次号：
def generate_batch_ids():
    batch_id = 1

    while True:
        yield batch_id
        batch_id += 1

# 使用：
batch_ids = generate_batch_ids()
print(next(batch_ids))
print(next(batch_ids))



# 二十、yield from
# 假设：
def generate_group1():
    yield 1
    yield 2


def generate_group2():
    yield 3
    yield 4

# 你想合并：
def generate_all():
    for value in generate_group1():
        yield value

    for value in generate_group2():
        yield value

# 可以简写成：
def generate_all():
    yield from generate_group1()
    yield from generate_group2()

for value in generate_all():
    print(value)

# 输出：
# 1
# 2
# 3
# 4



# 二十一、yield from Java 类比
# 可以理解成：
# 把另一个 iterable 里的元素
# 一个一个继续 yield 出去

# 类似：
# stream1
# +
# stream2

# 或者：flatMap的部分思想



# 二十二、文件读取其实天然就是惰性的
# 你之前写：
# with path.open(
#     "r",
#     encoding="utf-8",
# ) as file:
#     for line in file:
#         ...

# 这里：file本身就是 iterable。

# 它不会：
# 一次性把整个文件全部读进内存
# 而是：一行一行读
# 这就是典型的流式处理。



# 二十三、对比 read_text
# 比如一个 5GB 日志文件。
# 这样：
# content = path.read_text()
# 会尝试：5GB 全部读进内存

# 而：
# with path.open() as file:
#     for line in file:
#         process(line)

# 是：一行一行处理
# 生产环境大文件优先后一种。



# 二十四、订单 JSON 怎么流式处理
#
# 标准 json.load()：
#
# data = json.load(file)
#
# 通常会一次性加载整个 JSON。
#
# 如果文件几十 MB 还行。
#
# 如果几 GB：
#
# 内存压力会很大
#
# 生产环境可以使用：
#
# JSON Lines / NDJSON
#
# 格式：
#
# {"order_no":"A001"}
# {"order_no":"A002"}
# {"order_no":"A003"}
#
# 然后：
#
# def iter_json_lines(
#     path: Path,
# ):
#     with path.open(
#         "r",
#         encoding="utf-8",
#     ) as file:
#         for line in file:
#             if not line.strip():
#                 continue
#
#             yield json.loads(line)
#
# 这样一条一条读。



# 二十五、非常实用：流式订单清洗
# 以前：
# raw_orders = load_raw_orders(...)
# orders = clean_orders(raw_orders)
# export_orders_to_csv(orders)

# 这里：
# 全部原始订单进内存
# ↓
# 全部清洗订单又进内存
# ↓
# 再导出

# 可能出现：
# 100万原始订单
# +
# 80万清洗结果
# 两份数据同时占内存。

# 可以升级成：
# def iter_clean_orders(
#     raw_orders,
# ):
#     for raw_order in raw_orders:
#         order = clean_order(raw_order)
#
#         if order is not None:
#             yield order
#
# 然后：
#
# for order in iter_clean_orders(iter_raw_orders(path)):
#     write_order(order)
#
# 整个链路：
#
# 读1条
# ↓
# 清洗1条
# ↓
# 写1条
# ↓
# 释放
# ↓
# 下一条
#
# 这就是流式 pipeline。



# 二十六、这和 Java Stream 很像

# Java：
# orders.stream()
#     .filter(this::isValid)
#     .map(this::convert)
#     .forEach(this::save);

# Python：
# for order in (
#     clean_order(raw_order)
#     for raw_order in raw_orders
# ):
#     ...

# 不过 Python generator 更贴近：
# Iterator + lazy stream


# 二十七、自己实现 Iterator
# 你可以不用 yield，自己实现迭代器。

class OrderNumberIterator:
    def __init__(
        self,
        max_value: int,
    ) -> None:
        self.current = 1
        self.max_value = max_value

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current > self.max_value:
            raise StopIteration

        value = self.current
        self.current += 1

        return value

# 使用：
# iterator = OrderNumberIterator(3)
#
# for number in iterator:
#     print(number)
#
# 输出：
# 1
# 2
# 3



# 二十八、Java 对应
# Java：
# class OrderNumberIterator
#         implements Iterator<Integer> {
#
#     private int current = 1;
#     private int max;
#
#     @Override
#     public boolean hasNext() {
#         return current <= max;
#     }
#
#     @Override
#     public Integer next() {
#         return current++;
#     }
# }

# Python：
# __iter__()
# __next__()

# Java：
# hasNext()
# next()

# 差异：
# Python 不用 hasNext()。

# 而是：
# raise StopIteration
#
# 表示结束。



# 二十九、为什么 yield 更推荐

# 自己写：
# __iter__
# __next__
# current
# StopIteration
# 比较麻烦。

# 用生成器：
# def generate_numbers(max_value: int):
#     for number in range(1, max_value + 1):
#         yield number

# 功能一样。
#
# 所以：
#
# 能用 generator 表达的迭代逻辑，通常比手写 Iterator 类更简单。



# 三十、Iterable 和 Iterator 的区别再讲透
# 看：
# numbers = [1, 2, 3]
# numbers 是：
# Iterable
# 但不是 Iterator。


# 可以：
# iterator = iter(numbers)
# 得到：
# Iterator
# 再：
# next(iterator)

# Iterator 一定是 Iterable
# 一般：
# iter(iterator) is iterator
#
# 但：
#
# iter(list) is list
#
# 通常是 False。
#
# 所以：
# Iterable
#     ↓ iter()
# Iterator
#     ↓ next()
# value



# 三十一、生成器对象既是 Iterator，也是 Iterable
# g = generate_numbers()
#
# 通常：
#
# iter(g) is g
#
# 所以 generator 本身就是 Iterator。



# 三十二、一个很重要的生产坑
#
# 假设：
#
# orders = iter_orders()
#
# 然后：
#
# print(
#     f"订单数量：{len(list(orders))}"
# )
#
# 此时已经把 generator 消费完了。
#
# 后面：
#
# for order in orders:
#     ...
#
# 一个都没有。
#
# 这是非常常见的坑。



# 三十三、不要为了看数量把 generator 转 list
#
# 如果：
#
# list(generator)
#
# 就又失去了惰性计算优势。
#
# 如果必须统计数量，可以边处理边计数：
#
# count = 0
#
# for order in orders:
#     process(order)
#     count += 1
#
# 或者：
#
# count = sum(
#     1
#     for _ in orders
# )
#
# 但注意后者也会消费 generator。



# 三十四、生成器里面的异常
#
# 例如：
#
# def parse_orders(raw_orders):
#     for raw_order in raw_orders:
#         yield parse_order(raw_order)
#
# 真正异常不是在：
#
# generator = parse_orders(...)
#
# 这里发生。
#
# 而是在：
#
# next(generator)
#
# 或者：
#
# for order in generator:
#
# 消费时发生。
#
# 因为生成器是惰性的。
#
# 这是调试时很重要的一点。



# 三十五、一个很典型的例子
# def demo():
#     print("开始")
#
#     value = 1 / 0
#
#     yield value
#
# 调用：
#
# g = demo()
#
# 不会报错。
#
# 真正：
#
# next(g)
#
# 才报：
#
# ZeroDivisionError
#
# 因为函数体这时才开始执行。



# 三十六、什么时候用 yield，什么时候 return list
# 用 list
#
# 如果：
#
# 数据量不大
# 需要多次使用
# 需要随机访问
# 需要len
# 需要排序
#
# 比如：
#
# def get_valid_statuses() -> list[str]:
#     return [
#         "PAID",
#         "UNPAID",
#         "SHIPPED",
#     ]
#
# 完全没必要 generator。


# 用 generator
#
# 如果：
#
# 数据很多
# 数据从外部逐步产生
# API分页
# 读取大文件
# 爬虫
# 数据库流式结果
# 队列消费
# 数据清洗pipeline
#
# 用 generator。



# 三十七、生成器表达式配合 sum
#
# 比如：
#
# total = sum(
#     order.amount
#     for order in orders
# )
#
# 这里不需要先：
#
# amounts = [
#     order.amount
#     for order in orders
# ]
#
# total = sum(amounts)
#
# 生成器表达式更自然


# 三十八、配合 any
#
# 比如：
#
# has_large_order = any(
#     order.amount >= Decimal("500")
#     for order in orders
# )
#
# any() 还是短路的。
#
# 假设：
#
# 第3个订单就满足
#
# 它不会继续检查第4、第5……
#
# 非常高效。


# 三十九、配合 all
# all_paid = all(
#     order.status == OrderStatus.PAID
#     for order in orders
# )
#
# 一旦发现：
#
# 一个不是 PAID
#
# 立刻停止。
#
# 这也是惰性计算


# 四十、配合 next
#
# 找第一个满足条件的订单：
#
# first_paid_order = next(
#     (
#         order
#         for order in orders
#         if order.status == OrderStatus.PAID
#     ),
#     None,
# )
#
# 意思：
#
# 遍历订单
# ↓
# 找到第一个 PAID
# ↓
# 马上返回
# ↓
# 后面不再遍历
#
# 如果没找到：
#
# None



# 四十一、Java 类比
#
# Java：
#
# orders.stream()
#     .filter(order ->
#         order.getStatus() == PAID
#     )
#     .findFirst()
#     .orElse(null);
#
# Python：
#
# next(
#     (
#         order
#         for order in orders
#         if order.status == OrderStatus.PAID
#     ),
#     None,
# )



# 四十二、itertools
#
# Python 标准库里专门处理迭代器的：
#
# itertools
#
# 非常强。
#
# 今天先认识几个。



# 四十三、islice
#
# 类似对 generator 做切片：
#
# from itertools import islice
#
# 例如：
#
# orders = iter_orders()
#
# first_100 = islice(
#     orders,
#     100,
# )
#
# 不会把全部数据变成 list。



# 四十四、chain
#
# 合并多个 iterable：
#
# from itertools import chain
# all_orders = chain(
#     domestic_orders,
#     overseas_orders,
# )
#
# 类似：
#
# 两个流拼接
#
# Java 类比：
#
# Stream.concat(...)



# 四十五、filterfalse
# from itertools import filterfalse
#
# 得到条件不成立的数据。
#
# 例如：
#
# invalid_orders = filterfalse(
#     is_valid_order,
#     orders,
# )



# 四十六、batched
#
# Python 现代版本支持：
#
# from itertools import batched
#
# 批处理：
#
# for batch in batched(
#     orders,
#     100,
# ):
#     save_batch(batch)
#
# 假设：
#
# 1000 个订单
#
# 会产生：
#
# 第1批100
# 第2批100
# ...
# 第10批100
#
# 这个对你非常实用。
#
# 例如：
#
# 批量 insert
# 批量 API
# 批量 Redis
# 批量 MQ



# 四十七、你的业务非常适合 batched
#
# 例如批量同步订单：
#
# from itertools import batched
#
#
# def sync_orders(
#     orders,
# ) -> None:
#     for batch in batched(
#         orders,
#         100,
#     ):
#         send_to_remote(batch)
#
# Java 里你以前可能自己写：
#
# ListUtils.partition(...)
#
# Python 标准库直接提供。



# 四十八、生成器 pipeline
#
# 最终可以形成：
#
# raw_orders = iter_raw_orders(path)
#
# clean_orders = (
#     clean_order(raw_order)
#     for raw_order in raw_orders
# )
#
# valid_orders = (
#     order
#     for order in clean_orders
#     if order is not None
# )
#
# paid_orders = (
#     order
#     for order in valid_orders
#     if order.status == OrderStatus.PAID
# )
#
# for batch in batched(
#     paid_orders,
#     100,
# ):
#     save_batch(batch)
#
# 执行过程不是：
#
# 先全部raw
# ↓
# 再全部clean
# ↓
# 再全部valid
# ↓
# 再全部paid
#
# 而是：
#
# 第1条raw
# ↓
# clean
# ↓
# valid
# ↓
# paid判断
# ↓
# 进入batch
#
# 第2条raw
# ↓
# clean
# ↓
# ...
#
# 这就是：
#
# lazy pipeline



# 四十九、函数式编程思想
#
# 今天实际上已经接触到一些函数式思想：
#
# map
# filter
# generator expression
# higher-order function
# pure function
# lazy evaluation
# pipeline
#
# 但 Python 不追求纯函数式。
#
# Python 通常是：
#
# 命令式 + 面向对象 + 函数式混合使用。



# 五十、不要为了炫技全部写生成器
#
# 例如：
#
# statuses = (
#     status
#     for status in [
#         "PAID",
#         "UNPAID",
#     ]
# )
#
# 完全没必要。
#
# 数据就 2 个。
#
# 直接：
#
# statuses = [
#     "PAID",
#     "UNPAID",
# ]
# 
# 更清晰。
#
# 原则：
#
# generator 是为了解决流式、内存、延迟计算问题，不是为了让代码看起来高级。