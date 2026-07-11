# Python	Java 类比
# list	ArrayList
# dict	HashMap
# set	HashSet
# tuple	不可变 List / 简单值对象
# list[dict]	List<Map<String, Object>>
# dict[str, list]	Map<String, List<?>>

# 1. list：对应 Java ArrayList
order_nos = ["A1", "A2", "A3", "A4", "A5"]
print(order_nos[0])
print(order_nos[1])
# 注意：-1 表示最后一个元素，这个是 Python 很常用的写法。
print(order_nos[-1])

# 1.list 添加元素
order_nos = ["A001", "A002"]
order_nos.append("A003")
print(order_nos)

# list 插入元素
order_nos.insert(1, "A000")
print(order_nos)

# list 删除元素
order_nos = ["A001", "A002", "A003"]
order_nos.remove("A002")
print(order_nos)

order_nos = ["A001", "A002", "A003"]
deleted = order_nos.pop(1)
print(deleted)
print(order_nos)

# list 修改元素
order_nos = ["A001", "A002", "A003"]
order_nos[1] = "A000"
print(order_nos)

# list 长度
order_nos = ["A001", "A002", "A003"]
print(len(order_nos))

# 2.list 切片
# 规则是：
# 左闭右开
# 包含开始下标
# 不包含结束下标
nums = [0, 1, 2, 3, 4, 5]
print(nums[1:4])

nums = [0, 1, 2, 3, 4, 5]

print(nums[:3])  # 前 3 个
print(nums[3:])  # 从第 4 个到最后
print(nums[-2:])  # 最后 2 个
print(nums[:-1])  # 去掉最后 1 个
# 输出：
# [0, 1, 2]
# [3, 4, 5]
# [4, 5]
# [0, 1, 2, 3, 4]

# 3. list 遍历
order_nos = ["A001", "A002", "A003"]
for order_no in order_nos:
    print(order_no)

for index, order_no in enumerate(order_nos, start=1):
    print(f"第{index}个订单：{order_no}")

# 4. list 推导式
amounts = [100, 200, 300, 400]
newamount = [amount * 2 for amount in amounts]
print(newamount)

# 带过滤的推导式
amounts = [100, 200, 300, 400]
big_amounts = [amount for amount in amounts if amount > 100]
print(big_amounts)

# 提取所有订单号：
orders = [
    {"order_no": "A001", "amount": 100},
    {"order_no": "A002", "amount": 500},
    {"order_no": "A003", "amount": 900},
]
order_nos = [order["order_no"] for order in orders]
print(order_nos)

# 筛选大于等于 500 的订单：
big_orders = [order for order in orders if order["amount"] >= 500]
print(big_orders)

# 5. dict：对应 Java HashMap
order = {
    "order_no": "A001",
    "sku": "SKU001",
    "amount": 199.99,
    "status": "PAID"
}

print(order["order_no"])
print(order["amount"])

# dict 新增和修改
order["status"] = "PAID"
order["amount"] = 299.99
print(order)

# dict 删除
order = {
    "order_no": "A001",
    "amount": 199.99,
    "status": "PAID"
}
# del order["status"]
# print(order)
status = order.pop("status")
print(order)

# 6. dict 取值：重点区别
# order["amount"] 和 order.get("amount")
# 区别是：
# 6.1 使用 []
# order = {"order_no": "A001"}
# print(order["amount"])
# 如果 key 不存在，会报错：
# KeyError: 'amount'

# 6.2 使用 .get()
# order = {"order_no": "A001"}
# print(order.get("amount"))
# 输出：
# None
# 也可以给默认值：
# amount = order.get("amount", 0)
# print(amount)

# 7. dict 遍历
order = {
    "order_no": "A001",
    "amount": 199.99,
    "status": "PAID"
}
for key in order:
    print(key, order[key])

# 遍历 key：
for key in order:
    print(key)

# 遍历 value：
for value in order.values():
    print(value)

# 遍历 key 和 value：
for key, value in order.items():
    print(key, value)

# 最常用的是：
for key, value in order.items():
    print(f"{key} = {value}")

# 8. dict 推导式
orders = [
    {"order_no": "A001", "amount": 100},
    {"order_no": "A002", "amount": 200},
    {"order_no": "A003", "amount": 300},
]
# 你想构建一个 order_no -> order 的映射。
order_map = {order["order_no"]: order for order in orders}
print(order_map)

# 9. set：对应 Java HashSet
sku_list = ["SKU001", "SKU002", "SKU001", "SKU003"]
sku_set = set(sku_list)
print(sku_set)

# set 常用场景：去重
order_nos = ["A001", "A002", "A001", "A003"]
unique_order_nos = set(order_nos)
print(unique_order_nos)

# set 判断是否存在
black_skus = {"SKU001", "SKU002"}
if "SKU001" in black_skus:
    print("黑名单 SKU")

# set 集合运算
a = {"A001", "A002", "A003"}
b = {"A002", "A003", "A004"}
# 交集： {'A002', 'A003'}
print(a & b)

# 并集：{'A001', 'A002', 'A003', 'A004'}
print(a | b)

# 差集：{'A001'}
print(a - b)

# 对称差集：{'A001', 'A004'}
print(a ^ b)


# 10. tuple：不可变序列
# tuple 和 list 很像，但它不可修改。
# point = (10, 20)
# print(point[0])
# print(point[1])
#
# 不能这样：
# point[0] = 100
# 会报错。

# tuple 常用场景
# 1. 返回多个值 Python 函数返回多个值，本质上就是返回 tuple。
def parse_sku(sku: str) -> tuple[str, str]:
    parts = sku.split("-")
    return parts[0], parts[1]

spu, color = parse_sku("TSHIRT-RED")

print(spu)
print(color)

# 2. 固定结构数据
# date_range = ("2026-07-01", "2026-07-31")

# 3. dict 的 key
# 因为 tuple 不可变，所以可以作为 dict 的 key：作为联合 key
stock_map = {
    ("SKU001", "US"): 100,
    ("SKU001", "UK"): 50,
}

print(stock_map[("SKU001", "US")])

# 11. list[dict]：Python 业务代码核心形态
orders = [
    {
        "order_no": "A001",
        "sku": "SKU001",
        "quantity": 2,
        "amount": 100,
        "status": "PAID",
    },
    {
        "order_no": "A002",
        "sku": "SKU002",
        "quantity": 1,
        "amount": 300,
        "status": "UNPAID",
    },
    {
        "order_no": "A003",
        "sku": "SKU001",
        "quantity": 3,
        "amount": 500,
        "status": "PAID",
    },
]

# 提取所有订单号
order_nos = [order["order_no"] for order in orders]
print(order_nos)

# 筛选已支付订单
paid_orders = [order for order in orders if order["status"] == "PAID"]
print(paid_orders)

# 统计总金额
total_amount = sum(order["amount"] for order in orders)
print(total_amount)

# 注意这里不是 list 推导式，而是生成器表达式：以后大数据量处理时优先用生成器表达式。
sum(order["amount"] for order in orders)
# 比下面这个更省内存：
sum([order["amount"] for order in orders])

# 统计总数量
total_quantity = sum(order["quantity"] for order in orders)
print(total_quantity)

# 按 SKU 统计销量
sku_sale_map = {}
for order in orders:
    sku = order["sku"]
    quantity = order["quantity"]

    if sku not in sku_sale_map:
        sku_sale_map[sku] = 0

    sku_sale_map[sku] += quantity

print(sku_sale_map)

# # 更推荐写法，用 defaultdict：
from collections import defaultdict

sku_sale_map = defaultdict(int)

for order in orders:
    sku_sale_map[order["sku"]] += order["quantity"]

print(dict(sku_sale_map))

# 12. in 判断
# 效率上：
# list 查找：O(n)
# set 查找：平均 O(1)
# dict key 查找：平均 O(1)
order_nos = ["A001", "A002"]
if "A001" in order_nos:
    print("存在")

# dict 判断 key：
order = {"order_no": "A001", "amount": 100}
if "order_no" in order:
    print("存在 order_no")

# set 判断：
black_skus = {"SKU001", "SKU002"}
if "SKU001" in black_skus:
    print("黑名单")


# 13. 重要坑：list 是可变对象 因为 a 和 b 指向同一个 list。这个和 Java 里的引用很像
a = [1, 2, 3]
b = a

b.append(4)

print(a)
print(b)

# 如果你想复制一份
a = [1, 2, 3]
b = a.copy()

b.append(4)

print(a)
print(b)

# 14. 重要坑：不要用可变对象做默认参数 看似没问题，但会有隐藏 bug。
# Python 的默认参数不是每次调用函数时重新创建，而是在函数定义时只创建一次。所以这个 [] 会被多次调用共享。
# 实际上不是。这个默认列表只创建一次，后面一直复用。
# Python 就创建了一个列表对象，并把它保存在函数对象内部。
# print(add_order.__defaults__)
# 用 Java 思维理解：它的效果有点像你在 Java 里把一个 List 放成静态共享变量；虽然 Python 默认参数不完全等同于 Java 的 static，但从“共享同一个对象”的效果看，可以这样理解。
def add_order(order_no: str, order_nos: list[str] = []) -> list[str]:
    order_nos.append(order_no)
    return order_nos

# 正确写法：
# 为什么 None 写法就安全，每次不传 order_nos 时：  if order_nos is None: order_nos = []
# 为什么数字、字符串做默认参数没问题？
# 因为这些是不可变对象：int; float; str; bool; None; tuple；函数内部不能直接修改原对象本身。

# 而这些是可变对象，通常不能直接作为默认值：list; dict; set; 自定义的可变对象
# 默认参数在定义时求值一次；list、dict、set 会被共享，所以用 None 作为哨兵值，在函数内部重新创建。

# tuple 为什么通常可以
# def process(statuses: tuple[str, ...] = ("PAID", "SHIPPED")):
#     pass
# 这是安全的，因为 tuple 不可变，无法执行：
# statuses.append("CANCELLED")
# 但是要注意，如果 tuple 内部装了可变对象，仍可能有问题：
# def test(data: tuple[list[str]] = ([],)):
#     data[0].append("A001")
#     return data
# 虽然 tuple 本身不能修改，但里面的 list 可以修改。

def add_order(order_no: str, order_nos: list[str] | None = None) -> list[str]:
    if order_nos is None:
        order_nos = []

    order_nos.append(order_no)
    return order_nos

# 1. list 是有序可变集合
# 2. dict 是 key-value 映射，业务开发最常用
# 3. set 用于去重和快速判断存在
# 4. tuple 是不可变序列，适合固定结构和多返回值
# 5. enumerate 可以同时拿下标和值
# 6. dict.get 可以避免 KeyError
# 7. list/dict/set 都有推导式
# 8. 大量判断存在时用 set，不要用 list
# 9. 可变对象不要做默认参数
# 10. list[dict] 是 Python 处理业务数据的核心形态