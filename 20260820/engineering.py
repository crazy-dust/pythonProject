# 一、今天的学习目标
#
# 今天掌握：
# 模块和包
# 1、import 的工作方式
# 2、__name__ 与 __main__
# 3、绝对导入和相对导入
# 4、循环导入问题
# 5、Python 项目目录结构
# 6、logging 日志系统
# 7、argparse 命令行参数
# 8、配置与环境变量
# 9、完成订单清洗命令行工具

# 二、什么是模块
# 一个 .py 文件就是一个模块。
# 例如：
# money.py

# 内容：
from decimal import Decimal, ROUND_HALF_UP

MONEY_SCALE = Decimal("0.01")

def normalize_money(amount: Decimal) -> Decimal:
    return amount.quantize(
        MONEY_SCALE,
        rounding=ROUND_HALF_UP,
    )

# 另一个文件可以导入：
# from money import normalize_money
# amount = normalize_money(Decimal("100.126"))

# 这里：
# money.py               → 模块
# normalize_money        → 模块中的函数
# MONEY_SCALE            → 模块中的变量

# Java 类比：
# Python模块 ≈ Java中的一个类文件或工具类所在的包单元

# 但 Python 模块可以直接包含，不要求所有内容都放进类。：
# 函数
# 类
# 常量
# 可执行代码


# 三、什么是包
# 包是用于组织多个模块的目录。
#
# 例如：
# order_tool/
# ├── __init__.py
# ├── cleaner.py
# ├── models.py
# └── exporter.py
#
# 这个目录就是一个包。

# 导入：
# from order_tool.cleaner import clean_orders

# Java 类比：
# import com.example.order.cleaner.OrderCleaner;

# Python：
# from order_tool.cleaner import clean_orders

# 四、__init__.py 是什么
# 传统上，一个目录中有：
# __init__.py

# Python 就会把它视为包。

# 可以是空文件：

# order_tool/__init__.py

# 也可以用于暴露包的公开接口：
# from order_tool.cleaner import clean_orders
# from order_tool.models import Order, OrderItem

# __all__ = [
#     "Order",
#     "OrderItem",
#     "clean_orders",
# ]

# 然后外部可以：
# from order_tool import Order, clean_orders

# 但不要在 __init__.py 里塞大量业务逻辑，否则容易产生循环导入。
#
# 当前阶段建议：
#
# __init__.py 保持为空，或者只暴露少量稳定接口。


# 五、import 时到底发生了什么
#
# 假设：
#
# import order_tool.cleaner
#
# Python 会大致执行：
#
# 在模块搜索路径中寻找 order_tool
# 找到包后寻找 cleaner.py
# 执行 cleaner.py 的顶层代码
# 创建模块对象
# 将模块缓存到 sys.modules
# 把模块引用绑定到当前命名空间
#
# 重点：
#
# 模块第一次导入时，顶层代码会执行一次。
# 例如：

# demo.py
print("demo模块正在加载")

def test() -> None:
    print("test")

# 另一个文件：

# import demo
# import demo

# 通常只打印一次：
#
# demo模块正在加载
#
# 因为模块已经被缓存。

# 六、为什么不要在模块顶层写业务执行代码
#
# 不推荐：

# cleaner.py

# orders = load_orders(...)
# cleaned_orders = clean_orders(orders)
# export_orders(cleaned_orders)

# 只要其他模块导入：
#
# import cleaner
#
# 业务就会自动执行。
#
# 这可能导致：
#
# 导入时读取文件
# 导入时连接数据库
# 导入时调用接口
# 导入时创建线程
# 测试时产生副作用
#
# 推荐：
#
# def main() -> None:
#     orders = load_orders(...)
#     cleaned_orders = clean_orders(orders)
#     export_orders(cleaned_orders)
#
#
# if __name__ == "__main__":
#     main()

# 七、__name__ 的真正含义
#
# 每个 Python 模块都有：
#
# __name__
# 直接运行文件
# python cleaner.py
#
# 此时：
#
# __name__ == "__main__"
# 被其他模块导入
# import cleaner
#
# 此时：
#
# __name__ == "cleaner"
#
# 所以：
#
# if __name__ == "__main__":
#     main()
#
# 表示：
#
# 只有当前文件作为程序入口运行时，才调用 main()；被导入时不执行。

# 八、包级运行入口：__main__.py
#
# 假设项目：
#
# src/
# └── order_tool/
#     ├── __init__.py
#     └── __main__.py
#
# __main__.py：
#
# from order_tool.cli import main
#
#
# if __name__ == "__main__":
#     main()
#
# 安装项目后，可以运行：
#
# python -m order_tool
#
# Python 会自动寻找：
#
# order_tool/__main__.py
#
# 这相当于 Java 的应用启动类：
#
# public static void main(String[] args)

# 九、绝对导入
#
# 推荐优先使用绝对导入。
#
# 项目：
#
# order_tool/
# ├── cleaner.py
# ├── models.py
# └── exporter.py
#
# 在 cleaner.py 中：
#
# from order_tool.models import Order
#
# 优点：
#
# 导入来源清晰
# 重构时更容易理解
# 跨包引用不容易混乱

# 十、相对导入
#
# 也可以：
#
# from .models import Order
#
# 这里的：
#
# .
#
# 表示当前包。
#
# 上一级包：
#
# from ..common import normalize_money
#
# 相对导入适合包内部引用，但过多层级会难读：
#
# from ....common.utils import xxx
#
# 通常建议：
#
# 项目内优先绝对导入；同包内非常近的模块可以使用相对导入。
#
# 本课程项目统一使用绝对导入。


# 十一、循环导入问题
#
# 假设：
#
models.py
# from order_tool.service import OrderService
#
# 同时：
#
service.py
# from order_tool.models import Order
#
# 形成：
#
# models → service → models
#
# 可能报：
#
# ImportError: cannot import name ... from partially initialized module
#
# Java 依赖 Spring 容器时也会遇到循环依赖，但 Python 循环导入更多发生在模块初始化阶段。
#
# 常见解决方式
# 1. 调整职责
#
# 通常循环导入说明模块划分有问题。
#
# 比如：
#
# models.py 不应该依赖 service.py
# service.py 可以依赖 models.py
#
# 依赖方向应当是：
#
# 高层业务 → 底层模型
#
# 而不是双向。
#
# 2. 提取公共模块
# models.py
# service.py
# common.py
#
# 双方共同依赖 common.py。
#
# 3. 仅类型检查时导入
# from typing import TYPE_CHECKING
#
# if TYPE_CHECKING:
#     from order_tool.service import OrderService
#
# 运行时不会导入，只供类型检查器使用。
#
# 4. 局部导入
# def execute() -> None:
#     from order_tool.service import OrderService
#
# 可以临时解决，但不应该成为默认设计。


# 十二、Python 项目为什么推荐 src 目录
#
# 推荐：
#
# order_tool/
# ├── pyproject.toml
# ├── src/
# │   └── order_tool/
# │       └── ...
# └── tests/
#
# 而不是：
#
# order_tool/
# ├── order_tool/
# ├── tests/
# └── ...
#
# src 布局的优点：
#
# 避免意外从当前目录导入未安装代码
# 更接近真实安装环境
# 减少路径和测试环境差异
# 包结构更明确
#
# Java 类比：
#
# src/main/java
# src/test/java
#
# Python：
#
# src/order_tool
# tests


# 十三、pyproject.toml
#
# 现代 Python 项目通常使用：
#
# pyproject.toml
#
# 用于管理：
#
# 项目名称
# Python 版本
# 依赖
# 构建配置
# 格式化工具
# 测试工具
# 类型检查工具
#
# 基础版本：
#
# [project]
# name = "order-tool"
# version = "0.1.0"
# description = "订单数据清洗工具"
# requires-python = ">=3.14"
# dependencies = []
#
# [project.scripts]
# order-tool = "order_tool.cli:main"
#
# [build-system]
# requires = ["setuptools>=75"]
# build-backend = "setuptools.build_meta"
#
# [tool.setuptools.packages.find]
# where = ["src"]
#
# 安装当前项目：
#
# python -m pip install -e .
#
# -e 表示 editable，可编辑安装。
#
# 安装后可以直接运行：
#
# order-tool
#
# 它会执行：
#
# order_tool.cli:main


# 十四、日志不能长期使用 print
#
# 学习阶段用：
#
# print("订单处理完成")
#
# 没问题。
#
# 生产项目应该使用：
#
# logging
#
# 原因：
#
# 可以区分日志级别
# 可以输出时间
# 可以输出模块名
# 可以写入文件
# 可以统一控制格式
# 可以关闭低级别日志
# 可以接入日志平台
# 十五、日志级别
#
# Python 日志级别：
#
# 级别	使用场景
# DEBUG	调试细节
# INFO	正常业务流程
# WARNING	非致命异常或风险
# ERROR	当前操作失败
# CRITICAL	系统严重故障
#
# 示例：
#
# import logging
#
#
# logger = logging.getLogger(__name__)
#
# logger.debug("开始解析订单字段")
# logger.info("订单处理完成")
# logger.warning("订单缺少备注字段")
# logger.error("订单文件读取失败")
# logger.critical("数据库完全不可用")


# 十六、为什么使用 logging.getLogger(__name__)
# logger = logging.getLogger(__name__)
#
# 如果当前模块是：
#
# order_tool.cleaner
#
# 日志记录器名称就是：
#
# order_tool.cleaner
#
# 方便识别日志来源。
#
# Java 类比：
#
# private static final Logger log =
#     LoggerFactory.getLogger(OrderCleaner.class);
#
# Python：
#
# logger = logging.getLogger(__name__)


# 十七、统一日志配置
#
# logging_config.py：
#
# import logging
#
#
# def configure_logging(
#     level: int = logging.INFO,
# ) -> None:
#     logging.basicConfig(
#         level=level,
#         format=(
#             "%(asctime)s "
#             "%(levelname)s "
#             "%(name)s - "
#             "%(message)s"
#         ),
#     )
#
# 使用：
#
# from order_tool.logging_config import configure_logging
#
#
# configure_logging()
#
# 输出：
#
# 2026-07-24 13:20:00 INFO order_tool.cleaner - 清洗完成


# 十八、日志参数不要提前拼接
#
# 不太推荐：
#
# logger.info(f"成功处理订单：{order_no}")
#
# 推荐：
#
# logger.info(
#     "成功处理订单：%s",
#     order_no,
# )
#
# 原因：
#
# 日志级别关闭时，可以避免无意义的字符串拼接
# 是 logging 模块惯用方式
# 格式和参数分离
#
# Java SLF4J 类似：
#
# log.info("成功处理订单：{}", orderNo);
#
# Python：
#
# logger.info("成功处理订单：%s", order_no)


# 十九、记录异常堆栈
#
# 不要只写：
#
# except Exception as error:
#     logger.error("处理失败：%s", error)
#
# 这样只有错误信息，没有完整堆栈。
#
# 在 except 中可以：
#
# except Exception:
#     logger.exception("订单处理失败")
#
# logger.exception() 会自动记录当前异常堆栈。
#
# 类似 Java：
#
# log.error("订单处理失败", exception);


# 二十、命令行参数 argparse
#
# 我们不希望路径写死：
#
# input_path = Path("data/orders.json")
# output_path = Path("output/orders.csv")
#
# 应该让用户运行时传参：
#
# python -m order_tool \
#   --input data/orders.json \
#   --output output/orders.csv
#
# Python 标准库：
#
# argparse


# 二十一、基础 argparse
# import argparse
#
#
# def parse_args() -> argparse.Namespace:
#     parser = argparse.ArgumentParser(
#         description="订单数据清洗工具",
#     )
#
#     parser.add_argument(
#         "--input",
#         required=True,
#         help="输入JSON文件路径",
#     )
#
#     parser.add_argument(
#         "--output",
#         required=True,
#         help="输出CSV文件路径",
#     )
#
#     return parser.parse_args()
#
# 调用：
#
# python main.py \
#   --input data/orders.json \
#   --output output/orders.csv
#
# 代码中：
#
# args = parse_args()
#
# print(args.input)
# print(args.output)


# 二十二、参数类型转换
#
# 可以直接让 argparse 转换成 Path：
#
# from pathlib import Path
#
#
# parser.add_argument(
#     "--input",
#     type=Path,
#     required=True,
# )
#
# 然后：
#
# args.input
#
# 已经是：
#
# Path
#
# 不需要：
#
# Path(args.input)


# 二十三、布尔开关参数
#
# 例如开启调试日志：
#
# parser.add_argument(
#     "--debug",
#     action="store_true",
#     help="开启DEBUG日志",
# )
#
# 运行：
#
# python -m order_tool --debug
#
# 此时：
#
# args.debug is True
#
# 不传时：
#
# args.debug is False


# 二十四、配置与环境变量
#
# 生产项目中，一些配置不应该写死：
#
# DATABASE_PASSWORD = "123456"
#
# 可以从环境变量读取：
#
# import os
#
#
# database_password = os.environ.get("DATABASE_PASSWORD")
#
# 或者：
#
# database_password = os.getenv(
#     "DATABASE_PASSWORD",
#     "",
# )
#
# Java 类比：
#
# System.getenv("DATABASE_PASSWORD")


# 二十五、使用 dataclass 管理配置
# import os
# from dataclasses import dataclass
# from pathlib import Path
#
#
# @dataclass(frozen=True, slots=True)
# class AppConfig:
#     input_path: Path
#     output_path: Path
#     debug: bool
#
#
# def load_config(
#     *,
#     input_path: Path,
#     output_path: Path,
#     debug: bool,
# ) -> AppConfig:
#     return AppConfig(
#         input_path=input_path,
#         output_path=output_path,
#         debug=debug,
#     )
#
# 配置对象用 frozen=True 很合适，因为程序运行过程中通常不应随意修改配置。