# Day
# 14：综合实战——订单同步与批处理工具
#
# 前面确定的路线是：Day12
# 线程、进程、GIL
# 与并发工具 → Day13
# asyncio
# 异步编程 → Day14
# 订单同步与批处理综合实战。今天不再增加一套新的语法，而是把前
# 13
# 天的知识组合成一个可以运行、测试、扩展的工程。
#
# 本次按照“学习目标 → 知识地图 → 场景与架构 → 核心知识讲解 → 完整实战 → 测试 → 作业 → 验收”的结构展开。重点级别统一使用文字，不使用特殊
# emoji。
#
# 一、今日学习目标
#
# 学完后，你应该能够独立完成一个订单同步程序：从外部接口拉取订单，清洗和校验数据，去重后批量保存，并输出同步结果。同时，你需要能够解释并发方案的选择、控制并发数量、处理超时与重试、避免重复写入，并通过测试证明这些行为正确。
#
# 建议学习时间：4–6
# 小时。 今天的代码量比前几天大，重点不是背诵，而是理解各模块之间的职责，以及为什么要这样设计。
#
# 二、Day14
# 完整知识地图
#
# 模块
#
# 重点级别
#
# 必须掌握的内容
#
# 1.
# 需求分析与处理流程
#
# 重点
#
# 明确输入、输出、成功条件、失败条件
#
# 2.
# 项目结构与模块职责
#
# 重点
#
# 将接口、清洗、存储、编排分离
#
# 3.
# 数据模型与类型标注
#
# 重点
#
# dataclass、Decimal、类型转换、业务校验
#
# 4.
# 异步订单拉取
#
# 重点
#
#
#
# async / await、Task、并发上限、超时
#
# 5.
# 清洗、去重与批处理
#
# 重点
#
# 生成器、过滤、批次、业务唯一键
#
# 6.
# 幂等与可靠性
#
# 重点
#
# 重复同步、部分失败、重试边界
#
# 7.
# 异常处理与日志
#
# 重点
#
# 区分订单错误、接口错误、程序错误
#
# 8.
# 测试与可验证性
#
# 重点
#
# 单元测试、异步测试、故障场景
#
# 9.
# CLI
# 与工程运行
#
# 次重点
#
# argparse、入口函数、退出码
#
# 10.
# 性能与并发方案选择
#
# 次重点
#
# 线程池、asyncio、进程池的适用场景
#
# 11.
# 配置、指标与工程扩展
#
# 次重点
#
# 并发数、批次大小、统计结果
#
# 12.
# 生产级扩展方向
#
# 了解即可
#
# 数据库事务、限流、断点续传、分布式任务
#
# 今天最重要的四件事：数据正确性、并发边界、失败处理、可测试性。 能写出并发代码不等于能写出可靠的同步系统。
#
# 三、先用一个真实业务场景理解
#
# 假设你负责一个跨境电商
# OMS，需要从多个店铺同步订单。每个店铺接口返回一批订单，程序需要清洗金额和
# SKU，再写入本地存储。
#
# 多个店铺
# │
# ▼
# 异步拉取订单
# │
# ▼
# 解析与业务校验
# │
# ▼
# 清洗、过滤、去重
# │
# ▼
# 按固定大小分批
# │
# ▼
# 批量保存
# │
# ▼
# 输出同步统计
#
# 这里有两个不同层面的并发问题：拉取阶段是
# I / O
# 密集型，适合
# asyncio；清洗阶段通常是普通
# CPU
# 计算，不需要为了“异步”而强行写成协程。 如果以后清洗变成大量图片处理、复杂计算，才需要考虑进程池。
#
# 与
# Java
# 的对应关系
#
# Java
# 中熟悉的概念
#
# Python
# 今天的对应方式
#
# CompletableFuture / 异步任务
#
# asyncio.Task
#
# 线程池并发控制
#
# asyncio.Semaphore
#
# DTO / VO
#
# dataclass
#
# Service
# 编排
#
# OrderSyncService
#
# Repository
#
# OrderRepository
#
# BigDecimal
#
# Decimal
#
# 批量
# saveBatch
#
# save_batch
#
# JUnit
#
# pytest
#
# 命令行启动类
#
# __main__.py / argparse
#
# 注意：这些是帮助理解的对应关系，不代表实现机制完全相同。
#
# 四、核心知识一：先设计数据模型，再写并发
# 1.
# 为什么不直接传递原始
# dict
#
# 外部接口返回的字典不一定可靠：
#
# {
#     "order_id": "1001",
#     "amount": "19.90",
#     "sku": " abc-001 "
# }
#
# 如果所有模块都直接读取这些字段，金额格式、空
# SKU、缺失订单号等问题就会散落在各处。更合理的方式是：在系统边界将不可信数据转换成可信的业务对象。
#
# from dataclasses import dataclass
# from decimal import Decimal
#
#
# @dataclass(frozen=True, slots=True)
# class Order:
#     site_id: int
#     order_id: str
#     sku: str
#     amount: Decimal
#
#
# 这里的
# frozen = True
# 表示对象创建后不能直接修改字段，slots = True
# 可以减少实例的动态属性开销。它们不是业务正确性的核心，但适合这种结构固定的数据对象。
#
# 2.
# 金额必须使用
# Decimal
# from decimal import Decimal, ROUND_HALF_UP
#
# amount = Decimal("19.995").quantize(
#     Decimal("0.01"),
#     rounding=ROUND_HALF_UP,
# )
#
# 不要先把金额转换为
# float
# 再转换为
# Decimal：
#
# # 不推荐
# Decimal(19.90)
#
# 应该从字符串构造：
#
# Decimal("19.90")
#
# 这是
# Day1
# 的知识在真实业务中的复用。
#
# 五、核心知识二：把“拉取”和“处理”分开
#
# 一个常见错误是把所有逻辑写在一个巨大的异步函数中：
#
# async def sync():
#     # 请求接口
#     # 清洗订单
#     # 去重
#     # 保存数据库
#     # 记录日志
#     # 处理重试
#     ...
#
#
# 这样会导致测试困难、职责混乱，也容易让同步数据库操作阻塞事件循环。
#
# 建议拆成以下职责：
#
# OrderApi
# 只负责获取外部订单
#
# OrderCleaner
# 只负责转换、校验、清洗
#
# OrderRepository
# 只负责保存和查询
#
# OrderSyncService
# 负责组织整个同步流程
#
# 重点：异步是执行方式，分层是代码结构。两者不是一回事。
#
# 六、核心知识三：并发控制不是“任务越多越好”
#
# 假设有
# 100
# 个店铺，不应该直接无限制地同时请求。接口可能有
# QPS
# 限制，本机也可能出现连接数、内存和超时问题。
#
# 使用
# Semaphore：
#
# semaphore = asyncio.Semaphore(5)
#
#
# async def fetch_one(site_id: int):
#     async with semaphore:
#         return await api.fetch_orders(site_id)
#
#
# 这表示同一时间最多有
# 5
# 个任务进入受保护的拉取区域。
#
# 需要区分两个概念：
#
# 创建
# 100
# 个
# Task
# │
# ▼
# Semaphore(5)
# │
# ▼
# 同一时间最多
# 5
# 个执行接口请求
#
# Task
# 数量不等于同时执行的请求数量。
#
# 七、核心知识四：批处理、去重与幂等
# 1.
# 批处理
#
# 如果一次同步
# 100
# 万条订单，不应该把所有数据一次性提交给数据库。可以按固定大小分批：
#
# def batched(items, batch_size: int):
#     if batch_size <= 0:
#         raise ValueError("batch_size 必须大于 0")
#
#     batch = []
#
#     for item in items:
#         batch.append(item)
#
#         if len(batch) == batch_size:
#             yield batch
#             batch = []
#
#     if batch:
#         yield batch
#
#
# 使用：
#
# for batch in batched(orders, 500):
#     repository.save_batch(batch)
#
# 这里复用了
# Day8
# 的生成器知识。yield 让函数逐批产出结果，而不是必须一次性构造全部批次。
#
# 2.
# 去重不等于幂等
#
# 去重通常处理本次数据中的重复订单；幂等处理同一个同步请求重复执行时的结果一致性。
#
# 例如：
#
# 第一次同步：订单
# 1001 → 保存成功
# 第二次同步：订单
# 1001 → 不应该重复插入
#
# 业务唯一键可以设计为：
#
# (site_id, order_id)
#
# 但要注意，Python
# 内存中的
# set
# 去重不能替代数据库唯一约束。真实生产环境中，最终仍应通过数据库唯一索引、UPSERT
# 或其他持久化机制保证幂等。
#
# 八、完整实战：可运行的订单同步工具
#
# 下面实现一个教学版工程。它使用模拟接口和内存仓储，避免依赖真实店铺密钥或数据库，但保留真实系统需要的分层、并发、清洗、幂等、批处理和失败统计。
#
# 1.
# 项目结构
# day14_order_sync /
# ├── __init__.py
# ├── __main__.py
# ├── models.py
# ├── cleaner.py
# ├── api.py
# ├── repository.py
# ├── service.py
# └── tests /
# └── test_service.py
# 2.
# models.py：业务模型
# from dataclasses import dataclass
# from decimal import Decimal
#
#
# @dataclass(frozen=True, slots=True)
# class Order:
#     site_id: int
#     order_id: str
#     sku: str
#     amount: Decimal
#
#
# @dataclass(slots=True)
# class SyncResult:
#     fetched: int = 0
#     valid: int = 0
#     invalid: int = 0
#     duplicates: int = 0
#     saved: int = 0
#     failed_sites: int = 0
#
#
# SyncResult
# 是同步结果对象。它不是订单数据，而是一次任务的统计信息。
#
# 3.
# cleaner.py：清洗与校验
# from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
# from typing import Any
#
# from .models import Order
#
#
# class OrderValidationError(ValueError):
#     """订单数据不符合业务要求。"""
#
#
# def clean_order(raw: dict[str, Any]) -> Order:
#     try:
#         site_id = int(raw["site_id"])
#         order_id = str(raw["order_id"]).strip()
#         sku = str(raw["sku"]).strip().upper()
#
#         # 金额从字符串构造，避免浮点数精度问题。
#         amount = Decimal(str(raw["amount"])).quantize(
#             Decimal("0.01"),
#             rounding=ROUND_HALF_UP,
#         )
#
#     except (
#             KeyError,
#             TypeError,
#             ValueError,
#             InvalidOperation,
#     ) as exc:
#         raise OrderValidationError(
#             f"订单字段无效: {raw!r}"
#         ) from exc
#
#     if site_id <= 0:
#         raise OrderValidationError("site_id 必须大于 0")
#
#     if not order_id:
#         raise OrderValidationError("order_id 不能为空")
#
#     if not sku:
#         raise OrderValidationError("sku 不能为空")
#
#     if not amount.is_finite():
#         raise OrderValidationError("amount 必须是有限数值")
#
#     if amount < 0:
#         raise OrderValidationError("amount 不能小于 0")
#
#     return Order(
#         site_id=site_id,
#         order_id=order_id,
#         sku=sku,
#         amount=amount,
#     )
#
#
# 这里有一个工程细节：Decimal("NaN")
# 不会在构造时自动报错，所以还需要
# is_finite()
# 校验。
#
# 4.
# api.py：模拟外部接口
# import asyncio
# from typing import Any
#
#
# class OrderApiError(RuntimeError):
#     """外部订单接口失败。"""
#
#
# class FakeOrderApi:
#     def __init__(self, delay: float = 0.1):
#         self.delay = delay
#
#     async def fetch_orders(
#             self,
#             site_id: int,
#     ) -> list[dict[str, Any]]:
#         # 模拟 HTTP 请求的等待时间。
#         await asyncio.sleep(self.delay)
#
#         if site_id == 99:
#             raise OrderApiError("模拟店铺接口故障")
#
#         return [
#             {
#                 "site_id": site_id,
#                 "order_id": "1001",
#                 "sku": " abc-001 ",
#                 "amount": "19.995",
#             },
#             {
#                 "site_id": site_id,
#                 "order_id": "1002",
#                 "sku": "XYZ-002",
#                 "amount": "30.00",
#             },
#             {
#                 # 模拟重复订单。
#                 "site_id": site_id,
#                 "order_id": "1001",
#                 "sku": "ABC-001",
#                 "amount": "19.995",
#             },
#             {
#                 # 模拟脏数据。
#                 "site_id": site_id,
#                 "order_id": "1003",
#                 "sku": " ",
#                 "amount": "10.00",
#             },
#         ]
#
#
# 这里的
# asyncio.sleep()
# 是为了模拟非阻塞
# I / O。真实项目中应由异步
# HTTP
# 客户端执行请求，而不是用它替代真实网络请求。
#
# 5.
# repository.py：内存仓储与幂等
# from .models import Order
#
#
# class OrderRepository:
#     def __init__(self):
#         self._orders: dict[tuple[int, str], Order] = {}
#
#     def exists(self, site_id: int, order_id: str) -> bool:
#         return (site_id, order_id) in self._orders
#
#     def save_batch(self, orders: list[Order]) -> int:
#         saved = 0
#
#         for order in orders:
#             key = (order.site_id, order.order_id)
#
#             if key in self._orders:
#                 continue
#
#             self._orders[key] = order
#             saved += 1
#
#         return saved
#
#     def list_all(self) -> list[Order]:
#         return list(self._orders.values())
#
#
# 这里用字典模拟持久化唯一键。真实数据库应使用唯一索引保证并发写入时的最终正确性。
#
# 6.
# service.py：同步编排核心
#
# 这是今天最重要的文件。
#
# import asyncio
# import logging
# from typing import Any
#
# from .api import FakeOrderApi, OrderApiError
# from .cleaner import OrderValidationError, clean_order
# from .models import Order, SyncResult
# from .repository import OrderRepository
#
# logger = logging.getLogger(__name__)
#
#
# def batched(items: list[Order], batch_size: int):
#     if batch_size <= 0:
#         raise ValueError("batch_size 必须大于 0")
#
#     for start in range(0, len(items), batch_size):
#         yield items[start:start + batch_size]
#
#
# class OrderSyncService:
#     def __init__(
#             self,
#             api: FakeOrderApi,
#             repository: OrderRepository,
#             concurrency: int = 5,
#             batch_size: int = 500,
#             timeout: float = 5.0,
#     ):
#         if concurrency <= 0:
#             raise ValueError("concurrency 必须大于 0")
#
#         if batch_size <= 0:
#             raise ValueError("batch_size 必须大于 0")
#
#         if timeout <= 0:
#             raise ValueError("timeout 必须大于 0")
#
#         self.api = api
#         self.repository = repository
#         self.concurrency = concurrency
#         self.batch_size = batch_size
#         self.timeout = timeout
#
#     async def _fetch_one(
#             self,
#             site_id: int,
#             semaphore: asyncio.Semaphore,
#     ) -> tuple[int, list[dict[str, Any]] | None]:
#
#         async with semaphore:
#             try:
#                 orders = await asyncio.wait_for(
#                     self.api.fetch_orders(site_id),
#                     timeout=self.timeout,
#                 )
#                 return site_id, orders
#
#             except TimeoutError:
#                 logger.warning(
#                     "店铺同步超时 site_id=%s",
#                     site_id,
#                 )
#                 return site_id, None
#
#             except OrderApiError:
#                 logger.exception(
#                     "店铺接口失败 site_id=%s",
#                     site_id,
#                 )
#                 return site_id, None
#
#     async def sync(self, site_ids: list[int]) -> SyncResult:
#         result = SyncResult()
#         semaphore = asyncio.Semaphore(self.concurrency)
#
#         # 第一阶段：并发拉取。
#         tasks = [
#             asyncio.create_task(
#                 self._fetch_one(site_id, semaphore)
#             )
#             for site_id in site_ids
#         ]
#
#         fetched_results = await asyncio.gather(*tasks)
#
#         # 第二阶段：清洗与去重。
#         valid_orders: list[Order] = []
#         seen: set[tuple[int, str]] = set()
#
#         for site_id, raw_orders in fetched_results:
#             if raw_orders is None:
#                 result.failed_sites += 1
#                 continue
#
#             result.fetched += len(raw_orders)
#
#             for raw in raw_orders:
#                 try:
#                     order = clean_order(raw)
#                 except OrderValidationError:
#                     result.invalid += 1
#                     logger.warning(
#                         "订单数据无效 site_id=%s raw=%r",
#                         site_id,
#                         raw,
#                     )
#                     continue
#
#                 key = (order.site_id, order.order_id)
#
#                 if key in seen:
#                     result.duplicates += 1
#                     continue
#
#                 seen.add(key)
#                 valid_orders.append(order)
#                 result.valid += 1
#
#         # 第三阶段：批量保存。
#         for batch in batched(valid_orders, self.batch_size):
#             result.saved += self.repository.save_batch(batch)
#
#         return result
#
#
# 7.
# __main__.py：命令行入口
# import argparse
# import asyncio
# import logging
#
# from .api import FakeOrderApi
# from .repository import OrderRepository
# from .service import OrderSyncService
#
#
# async def async_main(
#         site_ids: list[int],
#         concurrency: int,
#         batch_size: int,
# ) -> None:
#     repository = OrderRepository()
#
#     service = OrderSyncService(
#         api=FakeOrderApi(),
#         repository=repository,
#         concurrency=concurrency,
#         batch_size=batch_size,
#     )
#
#     result = await service.sync(site_ids)
#
#     print("同步结果：", result)
#     print("保存订单：")
#
#     for order in repository.list_all():
#         print(order)
#
#
# def main() -> None:
#     parser = argparse.ArgumentParser(
#         description="Day14 订单同步工具"
#     )
#
#     parser.add_argument(
#         "--sites",
#         nargs="+",
#         type=int,
#         required=True,
#     )
#     parser.add_argument(
#         "--concurrency",
#         type=int,
#         default=5,
#     )
#     parser.add_argument(
#         "--batch-size",
#         type=int,
#         default=500,
#     )
#
#     args = parser.parse_args()
#
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(levelname)s %(message)s",
#     )
#
#     asyncio.run(
#         async_main(
#             site_ids=args.sites,
#             concurrency=args.concurrency,
#             batch_size=args.batch_size,
#         )
#     )
#
#
# if __name__ == "__main__":
#     main()
#
# 运行方式（在项目父目录执行）：
#
# python - m
# day14_order_sync - -sites
# 1
# 2
# 3 - -concurrency
# 2 - -batch - size
# 2
# 8.
# 预期结果
#
# 每个正常店铺返回
# 4
# 条原始数据，其中
# 1
# 条重复、1
# 条无效，因此每个正常店铺最终保存
# 2
# 条。
#
# 对于
# 3
# 个正常店铺：
#
# fetched = 12
# valid = 6
# invalid = 3
# duplicates = 3
# saved = 6
# failed_sites = 0
#
# 这些统计只针对这个模拟数据集，不代表真实业务的固定比例。
#
# 九、核心知识五：异常处理必须有边界
#
# 今天必须理解：不是所有异常都应该捕获后继续运行。
#
# 1.
# 可以跳过的业务错误
#
# 例如：
#
# 某条订单
# SKU
# 为空
#
# 处理方式：记录错误，跳过这一条，继续其他订单。
#
# 2.
# 可以隔离的外部接口错误
#
# 例如：
#
# 店铺
# A
# 接口超时
# 店铺
# B
# 接口正常
#
# 处理方式：记录店铺
# A
# 失败，继续处理店铺
# B。
#
# 3.
# 不应该随意吞掉的程序错误
#
# 例如：
#
# AttributeError
# TypeError（程序内部逻辑错误）
# 数据库连接配置错误
#
# 不能简单写成：
#
# except Exception:
# pass
#
# 否则程序看似成功，实际可能已经丢失数据。
#
# 4.
# 取消异常要正确传播
#
# Day13
# 学过的
# CancelledError
# 在今天仍然重要。任务被取消时，通常应该完成必要清理后重新抛出，而不是把取消当作普通业务失败吞掉。
#
# try:
#     await do_work()
# except asyncio.CancelledError:
#     # 执行必要清理
#     raise
# 十、核心知识六：重试要放在正确的位置
#
# 假设一次订单同步包含：
#
# HTTP
# 拉取 → 清洗 → 保存
#
# 如果保存已经成功，但你重试整个流程，就可能再次写入订单。因此，重试必须明确作用范围。
#
# 推荐的理解方式
# HTTP
# 请求失败
# ↓
# 可以重试
# HTTP
# 请求
#
# 订单字段无效
# ↓
# 通常不重试，属于数据问题
#
# 数据库写入失败
# ↓
# 需要根据事务和幂等策略决定是否重试
#
# 下面是一个带指数退避的异步重试示例：
#
# import asyncio
#
#
# async def fetch_with_retry(
#         api,
#         site_id: int,
#         retries: int = 3,
# ):
#     for attempt in range(retries + 1):
#         try:
#             return await api.fetch_orders(site_id)
#
#         except TimeoutError:
#             if attempt == retries:
#                 raise
#
#             delay = 0.5 * (2 ** attempt)
#             await asyncio.sleep(delay)
#
#
# 生产环境还应考虑随机抖动、接口限流响应、最大退避时间和请求幂等性。今天先掌握重试边界与基本实现即可。
#
# 十一、核心知识七：测试不能只验证“正常运行”
# 1.
# 清洗测试
# from decimal import Decimal
#
# from day14_order_sync.cleaner import clean_order
#
#
# def test_clean_order():
#     order = clean_order({
#         "site_id": 1,
#         "order_id": "1001",
#         "sku": " abc ",
#         "amount": "19.995",
#     })
#
#     assert order.sku == "ABC"
#     assert order.amount == Decimal("20.00")
#
#
# 2.
# 无效数据测试
# import pytest
#
# from day14_order_sync.cleaner import (
#     OrderValidationError,
#     clean_order,
# )
#
#
# def test_empty_sku():
#     with pytest.raises(OrderValidationError):
#         clean_order({
#             "site_id": 1,
#             "order_id": "1001",
#             "sku": " ",
#             "amount": "10.00",
#         })
#
#
# 3.
# 幂等测试
# from decimal import Decimal
#
# from day14_order_sync.models import Order
# from day14_order_sync.repository import OrderRepository
#
#
# def test_save_batch_idempotent():
#     repository = OrderRepository()
#
#     order = Order(
#         site_id=1,
#         order_id="1001",
#         sku="ABC",
#         amount=Decimal("10.00"),
#     )
#
#     assert repository.save_batch([order]) == 1
#     assert repository.save_batch([order]) == 0
#     assert len(repository.list_all()) == 1
#
#
# 4.
# 异步同步测试
# import asyncio
#
# from day14_order_sync.api import FakeOrderApi
# from day14_order_sync.repository import OrderRepository
# from day14_order_sync.service import OrderSyncService
#
#
# def test_sync():
#     repository = OrderRepository()
#
#     service = OrderSyncService(
#         api=FakeOrderApi(delay=0),
#         repository=repository,
#         concurrency=2,
#         batch_size=2,
#     )
#
#     result = asyncio.run(service.sync([1, 2, 3]))
#
#     assert result.fetched == 12
#     assert result.valid == 6
#     assert result.invalid == 3
#     assert result.duplicates == 3
#     assert result.saved == 6
#     assert len(repository.list_all()) == 6
#
#
# 这里使用
# asyncio.run()，因此不需要额外安装异步
# pytest
# 插件。
#
# 十二、工程可靠性：今天必须知道的三个限制
#
# 上面的代码是完整的教学实战，但不是可以直接连接生产数据库的最终版本。你需要明确它的边界。
#
# 1.
# gather()
# 会保留所有拉取结果
#
# 当前实现会先拉取所有店铺，再统一处理。如果店铺很多、订单量很大，内存可能持续增长。生产环境可以改为分页拉取、边获取边处理，或使用有界队列。
#
# 2.
# 内存幂等不等于数据库幂等
#
# seen
# 只能处理本次执行中的重复数据，OrderRepository
# 也只是模拟。真实系统必须依赖持久化唯一键、事务或
# UPSERT
# 等机制。
#
# 3.
# 同步数据库操作可能阻塞事件循环
#
# 如果以后接入的是同步
# MySQL
# 驱动，不应该直接在异步函数中执行长时间阻塞的数据库操作。可以使用异步数据库驱动，或者通过
# asyncio.to_thread()
# 将适合的同步
# I / O
# 放到线程中执行。
#
# saved = await asyncio.to_thread(
#     repository.save_batch,
#     batch,
# )
#
# 但要注意：线程化不自动解决数据库连接安全、事务、幂等和批量写入问题。
#
# 十三、线程池、异步、进程池怎么选
#
# 这是
# Day12–Day14
# 的最终知识闭环。
#
# 场景
#
# 优先考虑
#
# 原因
#
# 大量
# HTTP
# 请求
#
# asyncio
#
# 等待期间可调度其他协程
#
# 已有同步
# HTTP
# SDK
#
# 线程池
#
# 不需要强行改写
# SDK
#
# 同步数据库
# I / O
#
# 线程池或异步驱动
#
# 避免阻塞事件循环
#
# 大量
# JSON / 业务清洗
#
# 先普通代码
#
# 通常不需要为了并发而复杂化
#
# 大量纯
# Python
# CPU
# 计算
#
# 进程池
#
# 可利用多个进程执行
# CPU
# 任务
#
# 单个轻量订单校验
#
# 普通函数
#
# 并发开销可能大于收益
#
# 关键结论：先判断瓶颈，再选择并发工具。不要因为学了
# asyncio，就把所有函数都写成async def 。