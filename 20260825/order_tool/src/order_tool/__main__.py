from order_tool.cli import main


if __name__ == "__main__":
    main()

# 三十五、运行项目
#
# 项目根目录执行：
#
# python -m pip install -e .
#
# 然后：
#
# python -m order_tool  --input data/orders.json  --output output/clean_orders.csv
#
# python -m order_tool \
#   --input data/orders.json \
#   --output output/clean_orders.csv
#
# Windows PowerShell 可以写一行：
#
# python -m order_tool --input data/orders.json --output output/clean_orders.csv
#
# 开启调试：
#
# python -m order_tool --input data/orders.json --output output/clean_orders.csv --debug
#
# 安装了 [project.scripts] 后，也可以：
#
# order-tool --input data/orders.json --output output/clean_orders.csv

# python -m order_tool
#         │
#         ▼
# order_tool/__main__.py
#         │
#         ▼
# cli.main()
#         │
#         ├─ parse_args()
#         │      └─ 解析命令行参数
#         │
#         ├─ build_config()
#         │      └─ 创建 AppConfig
#         │
#         ├─ configure_logging()
#         │      └─ 初始化日志
#         │
#         └─ run(config)
#                │
#                ├─ load_raw_orders()
#                │      └─ 读取JSON
#                │
#                ├─ clean_orders()
#                │      └─ clean_order()
#                │             └─ 创建Order对象
#                │
#                ├─ export_orders_to_csv()
#                │
#                └─ 输出统计日志


# 三十七、这套结构对应 Java 什么
# Python	        Java 类比
# models.py	        Domain / DTO
# repository.py	    Repository / DAO
# cleaner.py	    Service / Domain Service
# exporter.py	    Adapter / Writer
# config.py	        Configuration Properties
# cli.py	        Controller / Application Service
# __main__.py	    Spring Boot Main
# logging	        SLF4J + Logback
# argparse	        命令行参数解析
# pyproject.toml	Maven pom.xml 的一部分
#
# 但 Python 项目不必机械分成很多类。
#
# 当前项目：
#
# 模块承担职责
# 函数承担行为
# dataclass承担数据模型
#
# 比：
#
# OrderCleanerService
# OrderCleanerServiceImpl
# OrderExporter
# OrderExporterImpl
#
# 更轻量。


# 三十八、今天的编程思想
# 1. 单一职责
# repository：读取数据
# cleaner：清洗数据
# models：表达领域对象
# exporter：导出文件
# cli：编排流程
# 2. 依赖方向
# cli
#  ├─ cleaner
#  ├─ repository
#  └─ exporter
#
# cleaner
#  └─ models
#
# exporter
#  └─ models
#
# models 不反向依赖 cli 或 cleaner。
#
# 3. 边界与核心分离
#
# 外部数据：
#
# dict[str, Any]
#
# 进入核心后：
#
# Order
#
# 导出时再转换：
#
# Order → CSV行
# 4. 入口层统一处理异常
#
# 底层模块：
#
# raise FileNotFoundError
# raise ValueError
#
# 入口层：
#
# except FileNotFoundError:
#     ...
# 5. 配置和代码分离
#
# 路径通过命令行传入，不写死在业务代码中。