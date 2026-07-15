from pathlib import Path

# 一、今天的学习目标
# 今天需要掌握：
# pathlib 文件路径处理
# with 上下文管理器
# 文本文件读写
# JSON 序列化与反序列化
# CSV 文件读写
# 文件和数据异常处理
# Decimal 与 JSON 的兼容问题
# 完成订单数据清洗工具


# 二、pathlib：现代文件路径处理
file_path = Path("data") / "orders.json"
print(file_path)

# 1. 常用路径操作
file_path = Path("data/orders.json")
print(file_path.name)  # orders.json
print(file_path.stem)  # orders
print(file_path.suffix)  # .json
print(file_path.parent)  # data
print(file_path.exists())  # 是否存在
print(file_path.is_file())  # 是否是文件

# 2. 创建目录
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# 如果有多层目录：
# parents=True：父目录不存在时一起创建
# exist_ok=True：目录已经存在时不报错
# 类似 Java：Files.createDirectories(path);
output_dir = Path("data/output/result")
output_dir.mkdir(parents=True, exist_ok=True)

# 三、文本文件读写
# 1. 读取整个文件
file_path = Path("data/test.txt")
content = file_path.read_text(encoding="utf-8")
print(content)

# 2. 写入文件 write_text() 默认会覆盖原内容
file_path = Path("output/result.txt")
file_path.parent.mkdir(parents=True, exist_ok=True)
file_path.write_text(
    "订单处理完成测试啊",
    encoding="utf-8",
)

# 3. 使用 with open()
# with 代码块结束后，文件会自动关闭。
file_path = Path("data/test.txt")
with file_path.open("r", encoding="utf-8") as file:
    content = file.read()
print(content)

# 四、文件打开模式
# 常见模式：
# 模式	含义
# "r"	读取
# "w"	覆盖写入
# "a"	追加写入
# "x"	文件不存在时创建，存在时报错
# "b"	二进制模式
# "t"	文本模式，默认
with Path("log.txt").open("a", encoding="utf-8") as file:
    file.write("新增一条日志\n")

# 五、逐行读取大文件
# 小文件可以：
# content = file.read()
# 但大文件不要一次全部加载到内存。
# 推荐逐行处理：
# line.strip()会去除字符串首尾的：空格; 换行符; 制表符
file_path = Path("data/orders.txt")
with file_path.open("r", encoding="utf-8") as file:
    for line in file:
        clean_line = line.strip()
        if not clean_line:
            continue
        print(clean_line)

# 六、JSON 基础
# Python 标准库：
# JSON 和 Python 类型对应关系：
# JSON	Python
# object	dict
# array	list
# string	str
# number	int / float
# true	True
# false	False
# null	None


# 七、JSON 字符串转 Python 对象
# 使用：json.loads()
import json

json_text = """
{
    "order_no": "123456789",
    "customer_name": "张三",
    "amount": 19.99,
    "items": ["商品1", "商品2"],
    "is_paid": true
}
"""

order = json.loads(json_text)

print(order)
print(type(order))
print(order["order_no"])

# 八、Python 对象转 JSON 字符串
# 使用：json.dumps()
# 参数含义：

# ensure_ascii=False：中文不转成 Unicode 转义
# 如果不加：ensure_ascii=False
# 中文可能输出为：
# \u5df2\u652f\u4ed8

# indent=4：格式化缩进
import json

order = {
    "order_no": "A001",
    "amount": 199.99,
    "status": "已支付",
}

json_text = json.dumps(
    order,
    ensure_ascii=False,
    indent=4,
)

print(json_text)

# 九、读取 JSON 文件
# 假设 orders.json 内容：

[
    {
        "order_no": "A001",
        "sku": "SKU001",
        "price": "100.00",
        "quantity": 2,
        "status": "PAID"
    },
    {
        "order_no": "A002",
        "sku": "SKU002",
        "price": "300.00",
        "quantity": 1,
        "status": "UNPAID"
    }
]
import json
from pathlib import Path

file_path = Path("data/orders.json")

with file_path.open("r", encoding="utf-8") as file:
    orders = json.load(file)

print(type(orders))
print(orders)

# 注意区别：
# json.loads()：读取 JSON 字符串
# json.load()：读取 JSON 文件
#
# json.dumps()：生成 JSON 字符串
# json.dump()：写入 JSON 文件

# 口诀：有 s 的处理字符串，没有 s 的处理文件对象。


# 十、写入 JSON 文件
import json
from pathlib import Path

orders = [
    {
        "order_no": "A001",
        "status": "PAID",
    }
]

output_path = Path("output/orders.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as file:
    json.dump(
        orders,
        file,
        ensure_ascii=False,
        indent=4,
    )

# 十一、JSON 和 Decimal 的重要问题
# 下面代码会报错：
# import json
# from decimal import Decimal
#
# order = {
#     "amount": Decimal("100.00"),
# }
#
# print(json.dumps(order))

# 错误：TypeError: Object of type Decimal is not JSON serializable
# 因为 JSON 标准只认识普通数字，不认识 Python 的 Decimal 对象。
# 方案一：转成字符串
# 金额数据最严谨的做法：
# 优点是不会损失金额精度。

import json
from decimal import Decimal

order = {
    "amount": Decimal("100.00"),
}

json_text = json.dumps(
    order,
    default=str,
)

print(json_text)

# 输出：
{"amount": "100.00"}

# 方案二：转成 float
# 但金融金额不建议随意转 float，可能产生精度问题。
# 订单、支付、退款金额优先转成字符串。
order = {
    "amount": float(Decimal("100.00")),
}

# 输出：
{"amount": 100.0}

# 十二、从 JSON 读取金额
# JSON 中金额建议保存为字符串：
order = {
    "price": "100.00"
}

# Python 读取后转换：
from decimal import Decimal

price = Decimal(order["price"])

# 不要写：price = Decimal(100.1)
# 因为 100.1 已经先被转成了不精确的浮点数。
# 推荐：
price = Decimal("100.1")

# 十三、CSV 文件
# CSV 本质上是文本表格。
# 例如：
# order_no,sku,amount,status
# A001,SKU001,200.00,PAID
# A002,SKU002,300.00,UNPAID
# Python 使用标准库：import csv
# 十四、写 CSV 文件
import csv
from pathlib import Path

orders = [
    {
        "order_no": "A001",
        "sku": "SKU001",
        "amount": "200.00",
        "status": "PAID",
    },
    {
        "order_no": "A002",
        "sku": "SKU002",
        "amount": "300.00",
        "status": "UNPAID",
    },
]

output_path = Path("output/orders.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "order_no",
            "sku",
            "amount",
            "status",
        ],
    )

    writer.writeheader()
    writer.writerows(orders)

# 重点参数：
# encoding="utf-8-sig"
# 这样 Windows Excel 打开中文 CSV 时更不容易乱码。
#
# newline=""
# 避免 Windows 下 CSV 出现空行。

# 十五、读取 CSV 文件
import csv
from pathlib import Path

file_path = Path("output/orders.csv")

with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
) as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row)

# 每一行是一个字典：
{
    "order_no": "A001",
    "sku": "SKU001",
    "amount": "200.00",
    "status": "PAID",
}

# 注意：
# CSV 读取出来的字段默认全是字符串。
# 即使 CSV 中写的是：
# quantity = 2
# amount = 100.00

# # 读取后依然是：
# quantity == "2"
# amount == "100.00"
#
# 需要主动转换：
# quantity = int(row["quantity"])
# amount = Decimal(row["amount"])


# 十六、异常处理
# Python 使用：
try:
    ...
except:
    ...

# 基本写法：
try:
    quantity = int("abc")
except ValueError as error:
    print(f"数量转换失败：{error}")

# Java 对应：
# try {
#     Integer.parseInt("abc");
# } catch (NumberFormatException e) {
#     ...
# }

# 常见文件异常
from pathlib import Path

file_path = Path("data/orders.json")
try:
    content = file_path.read_text(encoding="utf-8")
except FileNotFoundError:
    print(f"文件不存在：{file_path}")
except PermissionError:
    print(f"没有权限读取文件：{file_path}")

# JSON 解析异常
import json
from pathlib import Path

try:
    with Path("data/orders.json").open("r", encoding="utf-8") as file:
        orders = json.load(file)
except FileNotFoundError:
    print("文件不存在")
except json.JSONDecodeError as error:
    print(f"JSON格式错误：{error}")

# 十七、不要随便使用裸 except
# 不推荐：
try:
    ...
except:
    print("发生异常")

# 因为它会捕获太多异常，甚至可能把程序退出等信号一起吞掉。
# 也不推荐：
try:
    ...
except Exception:
    pass

# 这会隐藏错误。
# 推荐捕获明确异常：
try:
    quantity = int(value)
except ValueError:
    ...

# 在系统边界层，确实需要兜底时才使用：
except Exception as error:
    print(f"未知异常：{error}")

# 十八、else 和 finally
# 完整结构：
try:
    quantity = int("10")
except ValueError:
    print("转换失败")
else:
    print(f"转换成功：{quantity}")
finally:
    print("无论是否异常都会执行")

# 含义：
# try：可能发生异常的代码
# except：发生异常时执行
# else：没有异常时执行
# finally：无论是否异常都执行
#
# 文件资源通常用 with 管理，不需要自己在 finally 中关闭。

# 十九、业务数据清洗原则
# 处理外部订单数据时，必须考虑：
# 字段缺失
# 字段为 None
# 字符串带空格
# 大小写不统一
# 数量格式错误
# 金额格式错误
# 订单号为空
# JSON 格式错误
# 比如：
raw_order = {
    "order_no": " A001 ",
    "sku": " sku001 ",
    "price": "100.00",
    "quantity": "2",
    "status": "paid",
}

# 清洗后：
{
    "order_no": "A001",
    "sku": "SKU001",
    "price": Decimal("100.00"),
    "quantity": 2,
    "status": "PAID",
}
# 这也是一种归一化。