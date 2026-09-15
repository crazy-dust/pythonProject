"""Day 14：订单同步与批处理综合实战。

学习目标
========
把前几天的数据模型、异常、生成器、测试、线程/进程与 asyncio 知识连接起来，
实现一个结构清晰、失败可隔离、结果可验证的订单同步流程：

    多店铺接口
        -> 异步限流拉取
        -> 字段转换与业务校验
        -> 本轮去重
        -> 固定大小分批
        -> 幂等保存
        -> 同步统计

今天最重要的四件事是：数据正确性、并发边界、失败处理和可测试性。会写并发
代码不等于已经写出了可靠的同步系统。

一、先分层，再写并发
--------------------
* OrderApi：只负责从外部系统获取原始订单。
* clean_order：在系统边界把不可信 dict 转换成可信 Order。
* OrderRepository：负责持久化和业务唯一键约束。
* OrderSyncService：编排拉取、清洗、去重、分批、保存与统计。

异步是执行方式，分层是代码结构，两者不是一回事。把请求、清洗、保存、日志
和重试全部塞进一个巨大 async 函数，会让测试和故障定位变得困难。

二、数据模型与清洗
------------------
订单模型使用 ``@dataclass(frozen=True, slots=True)`` 表达结构固定的不可变数据。
金额应从字符串构造 Decimal，再按 ROUND_HALF_UP 保留两位小数；不要先转换为
float。``Decimal("NaN")`` 可以构造成功，因此还需要 ``is_finite()`` 校验。

原始字典必须先转换类型，再检查业务规则：site_id 大于零、order_id 和 SKU 非空、
amount 为非负有限数、quantity 为正整数。字段缺失、格式错误与业务不合法统一
转换为明确的 OrderValidationError。

三、并发、超时与重试边界
------------------------
拉取店铺订单属于 I/O 密集阶段，适合 asyncio。Semaphore 限制同时访问接口的
店铺数量，wait_for 限制单次接口等待时间。

重试应只包裹可恢复的外部请求：

* HTTP 超时：可以有限重试，并使用退避。
* 订单字段校验失败：属于数据问题，不重试接口。
* 数据库写入失败：必须结合事务和幂等策略判断，不能盲目重试整个流程。

如果保存已经成功，却重试完整的“拉取—清洗—保存”，就可能重复写入。重试边界
越精确，副作用越容易控制。单店铺接口失败应记录到 failed_sites，不影响其他
店铺；意外的程序缺陷不应被 ``except Exception: pass`` 吞掉。

四、去重、幂等与批处理
----------------------
去重处理同一轮输入中的重复数据；幂等保证同一个同步动作重复执行时，不会产生
额外持久化结果。二者不是同一个概念：

* 本轮 set/seen：过滤当前批次内重复的 ``(site_id, order_id)``。
* Repository 唯一键：防止多次执行重复写入。
* 生产数据库：最终应使用唯一索引、UPSERT 或事务保证并发场景下的正确性。

批处理避免一次向数据库提交过多记录。生成器 ``batched`` 每次只产出一个批次，
例如五条数据、batch_size=2 会得到 2、2、1。

``valid`` 表示通过校验并完成本轮去重的数量，``saved`` 表示本次真正新增的数量。
第二次同步时 valid 可能与第一次相同，但 saved 可以为零。

五、异常与取消
--------------
* 单订单业务错误：记录并跳过这一条。
* 单店铺接口错误：隔离该店铺并继续其他店铺。
* 程序内部 TypeError、AttributeError 等：不要随意吞掉。
* CancelledError：完成必要清理后继续抛出，让上层正确结束任务。

六、生产级边界
--------------
教学版先 gather 所有店铺结果，适合小规模练习。若同步 1000 个店铺、每店十万条
订单，一次性创建任务并保留全部结果会消耗大量内存。生产实现应改成：

1. 按店铺和游标分页拉取。
2. 生产者把页面放入有界 asyncio.Queue，利用 maxsize 提供背压。
3. 固定数量消费者完成清洗、去重和批量保存。
4. 数据库使用唯一约束/UPSERT，并在成功提交后持久化同步游标。
5. 增加限流响应处理、随机重试抖动、事务、断点续传、失败队列、指标和告警。

若接入同步数据库驱动，不应直接在协程里执行长时间阻塞 I/O；应使用异步驱动，
或在确认连接安全后用 asyncio.to_thread 桥接。线程化不会自动解决连接池、事务、
幂等和批量写入问题。

复习清单
--------
* 能解释拉取、清洗、仓储和服务编排的职责边界。
* 能正确处理 Decimal、quantity、空字段和 NaN。
* 能用 Semaphore、wait_for 和有限重试组织多店铺拉取。
* 能区分去重与幂等，并解释数据库唯一约束的作用。
* 能证明批次为 2、2、1，且第二次同步 saved 为零。
* 能说明为何大规模同步需要分页、有界队列和固定 worker。
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Protocol, TypeVar


class OrderValidationError(ValueError):
    """外部订单字段或业务规则不合法。"""


class OrderApiError(RuntimeError):
    """外部订单接口发生不可重试错误。"""


@dataclass(frozen=True, slots=True)
class Order:
    site_id: int
    order_id: str
    sku: str
    amount: Decimal
    quantity: int

    @property
    def total_amount(self) -> Decimal:
        return self.amount * self.quantity


@dataclass(slots=True)
class SyncResult:
    fetched: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    saved: int = 0
    failed_sites: int = 0
    retries: int = 0
    batch_sizes: list[int] = field(default_factory=list)


def parse_positive_int(value: Any, *, field_name: str) -> int:
    """只接受 int 或纯数字字符串，避免 int(1.5) 被静默截断。"""
    if isinstance(value, bool):
        raise OrderValidationError(f"{field_name} 必须是正整数")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str) and value.strip().isdigit():
        result = int(value.strip())
    else:
        raise OrderValidationError(f"{field_name} 必须是正整数")
    if result <= 0:
        raise OrderValidationError(f"{field_name} 必须是正整数")
    return result


def clean_order(raw: dict[str, Any]) -> Order:
    try:
        site_id = parse_positive_int(raw["site_id"], field_name="site_id")
        order_id = str(raw["order_id"]).strip()
        sku = str(raw["sku"]).strip().upper()
        quantity = parse_positive_int(raw["quantity"], field_name="quantity")
        amount = Decimal(str(raw["amount"])).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except OrderValidationError:
        raise
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise OrderValidationError(f"订单字段无效: {raw!r}") from exc

    if not order_id:
        raise OrderValidationError("order_id 不能为空")
    if not sku:
        raise OrderValidationError("sku 不能为空")
    if not amount.is_finite() or amount < 0:
        raise OrderValidationError("amount 必须是非负有限数值")

    return Order(
        site_id=site_id,
        order_id=order_id,
        sku=sku,
        amount=amount,
        quantity=quantity,
    )


ItemT = TypeVar("ItemT")


def batched(items: list[ItemT], batch_size: int) -> Iterator[list[ItemT]]:
    if batch_size <= 0:
        raise ValueError("batch_size 必须大于 0")
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


class OrderApi(Protocol):
    async def fetch_orders(self, site_id: int) -> list[dict[str, Any]]:
        ...


class OrderRepositoryProtocol(Protocol):
    def save_batch(self, orders: list[Order]) -> int:
        ...


class FakeOrderApi:
    """模拟异步接口，并记录调用次数和实际最大并发。"""

    def __init__(
        self,
        *,
        delay: float = 0.01,
        timeout_failures: dict[int, int] | None = None,
    ) -> None:
        self.delay = delay
        self.timeout_failures = timeout_failures or {}
        self.calls: dict[int, int] = {}
        self.active_requests = 0
        self.max_active_requests = 0

    async def fetch_orders(self, site_id: int) -> list[dict[str, Any]]:
        self.calls[site_id] = self.calls.get(site_id, 0) + 1
        self.active_requests += 1
        self.max_active_requests = max(self.max_active_requests, self.active_requests)
        try:
            await asyncio.sleep(self.delay)
            if self.calls[site_id] <= self.timeout_failures.get(site_id, 0):
                raise TimeoutError(f"店铺 {site_id} 模拟超时")
            if site_id == 99:
                raise OrderApiError("模拟店铺接口故障")
            return self._orders_for(site_id)
        finally:
            self.active_requests -= 1

    @staticmethod
    def _orders_for(site_id: int) -> list[dict[str, Any]]:
        return [
            {
                "site_id": site_id,
                "order_id": "1001",
                "sku": " abc-001 ",
                "amount": "19.995",
                "quantity": 2,
            },
            {
                "site_id": site_id,
                "order_id": "1002",
                "sku": "XYZ-002",
                "amount": "30.00",
                "quantity": 1,
            },
            {
                "site_id": site_id,
                "order_id": "1001",
                "sku": "ABC-001",
                "amount": "19.995",
                "quantity": 2,
            },
            {
                "site_id": site_id,
                "order_id": "1003",
                "sku": " ",
                "amount": "10.00",
                "quantity": 1,
            },
        ]


class InMemoryOrderRepository:
    """用字典模拟业务唯一键；真实系统仍需数据库唯一约束。"""

    def __init__(self) -> None:
        self._orders: dict[tuple[int, str], Order] = {}
        self.recorded_batch_sizes: list[int] = []

    def save_batch(self, orders: list[Order]) -> int:
        self.recorded_batch_sizes.append(len(orders))
        saved = 0
        for order in orders:
            key = (order.site_id, order.order_id)
            if key in self._orders:
                continue
            self._orders[key] = order
            saved += 1
        return saved

    def list_all(self) -> list[Order]:
        return list(self._orders.values())


class OrderSyncService:
    def __init__(
        self,
        api: OrderApi,
        repository: OrderRepositoryProtocol,
        *,
        concurrency: int = 5,
        batch_size: int = 500,
        timeout: float = 1.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.01,
    ) -> None:
        if concurrency <= 0:
            raise ValueError("concurrency 必须大于 0")
        if batch_size <= 0:
            raise ValueError("batch_size 必须大于 0")
        if timeout <= 0:
            raise ValueError("timeout 必须大于 0")
        if max_retries < 0 or retry_base_delay < 0:
            raise ValueError("重试次数和退避时间不能小于 0")

        self.api = api
        self.repository = repository
        self.concurrency = concurrency
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    async def _fetch_one(
        self,
        site_id: int,
        semaphore: asyncio.Semaphore,
    ) -> tuple[int, list[dict[str, Any]] | None, int]:
        retries_used = 0
        async with semaphore:
            for attempt in range(self.max_retries + 1):
                try:
                    orders = await asyncio.wait_for(
                        self.api.fetch_orders(site_id),
                        timeout=self.timeout,
                    )
                    return site_id, orders, retries_used
                except TimeoutError:
                    if attempt == self.max_retries:
                        return site_id, None, retries_used
                    retries_used += 1
                    await asyncio.sleep(self.retry_base_delay * (2**attempt))
                except OrderApiError:
                    return site_id, None, retries_used
        raise AssertionError("不可达分支")

    async def sync(self, site_ids: list[int]) -> SyncResult:
        result = SyncResult()
        semaphore = asyncio.Semaphore(self.concurrency)

        # 第一阶段：并发拉取。每个店铺的预期接口失败已在 _fetch_one 内隔离。
        fetched_results = await asyncio.gather(
            *(self._fetch_one(site_id, semaphore) for site_id in site_ids)
        )

        # 第二阶段：清洗与本轮去重。
        valid_orders: list[Order] = []
        seen: set[tuple[int, str]] = set()
        for _site_id, raw_orders, retries_used in fetched_results:
            result.retries += retries_used
            if raw_orders is None:
                result.failed_sites += 1
                continue

            result.fetched += len(raw_orders)
            for raw in raw_orders:
                try:
                    order = clean_order(raw)
                except OrderValidationError:
                    result.invalid += 1
                    continue

                key = (order.site_id, order.order_id)
                if key in seen:
                    result.duplicates += 1
                    continue
                seen.add(key)
                valid_orders.append(order)
                result.valid += 1

        # 第三阶段：分批幂等保存。
        for batch in batched(valid_orders, self.batch_size):
            result.batch_sizes.append(len(batch))
            result.saved += self.repository.save_batch(batch)

        return result


async def main() -> None:
    cleaned = clean_order(
        {
            "site_id": "1",
            "order_id": "1001",
            "sku": " abc ",
            "amount": "19.995",
            "quantity": "2",
        }
    )
    assert cleaned.amount == Decimal("20.00")
    assert cleaned.total_amount == Decimal("40.00")

    api = FakeOrderApi(timeout_failures={1: 2})
    repository = InMemoryOrderRepository()
    service = OrderSyncService(
        api,
        repository,
        concurrency=3,
        batch_size=2,
        max_retries=3,
        retry_base_delay=0,
    )

    first = await service.sync([1, 2, 3, 99])
    assert first.fetched == 12
    assert first.valid == 6
    assert first.invalid == 3
    assert first.duplicates == 3
    assert first.saved == 6
    assert first.failed_sites == 1
    assert first.retries == 2
    assert first.batch_sizes == [2, 2, 2]
    assert api.max_active_requests <= 3

    second = await service.sync([1, 2, 3])
    assert second.valid == 6
    assert second.saved == 0
    assert len(repository.list_all()) == 6

    assert [len(batch) for batch in batched(list(range(5)), 2)] == [2, 2, 1]

    print("首次同步：", first)
    print("第二次新增：", second.saved)
    print("实际最大并发：", api.max_active_requests)
    print("Day 14 示例检查通过")


if __name__ == "__main__":
    asyncio.run(main())
