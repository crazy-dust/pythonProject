"""Day 14 作业正确答案：可靠的异步订单同步与批处理。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Protocol


class OrderValidationError(ValueError):
    """订单字段不符合业务要求；数据问题不应该通过重试接口解决。"""


class OrderApiError(RuntimeError):
    """外部订单接口失败。"""


# 作业 1：基础改造（重点）
# 在当前项目中增加订单数量 quantity，要求必须为正整数，并增加 total_amount
# 属性，计算 amount * quantity。
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


def clean_order(raw: dict[str, Any]) -> Order:
    try:
        site_id = int(raw["site_id"])
        order_id = str(raw["order_id"]).strip()
        sku = str(raw["sku"]).strip().upper()
        amount = Decimal(str(raw["amount"])).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        raw_quantity = raw["quantity"]
        if isinstance(raw_quantity, bool):
            raise ValueError("bool 不是有效数量")
        if isinstance(raw_quantity, int):
            quantity = raw_quantity
        elif isinstance(raw_quantity, str) and raw_quantity.strip().isdigit():
            quantity = int(raw_quantity.strip())
        else:
            raise ValueError("quantity 必须是整数或整数字符串")
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise OrderValidationError(f"订单字段无效: {raw!r}") from exc

    if site_id <= 0:
        raise OrderValidationError("site_id 必须大于 0")
    if not order_id:
        raise OrderValidationError("order_id 不能为空")
    if not sku:
        raise OrderValidationError("sku 不能为空")
    if not amount.is_finite() or amount < 0:
        raise OrderValidationError("amount 必须是非负有限数值")
    if quantity <= 0:
        raise OrderValidationError("quantity 必须是正整数")

    return Order(site_id, order_id, sku, amount, quantity)


def batched(items: list[Order], batch_size: int):
    if batch_size <= 0:
        raise ValueError("batch_size 必须大于 0")
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


class OrderApi(Protocol):
    async def fetch_orders(self, site_id: int) -> list[dict[str, Any]]:
        ...


class FakeOrderApi:
    """可验证超时重试和并发上限的模拟接口。"""

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
                raise OrderApiError("模拟不可重试的接口错误")
            return self._build_orders(site_id)
        finally:
            self.active_requests -= 1

    @staticmethod
    def _build_orders(site_id: int) -> list[dict[str, Any]]:
        orders = [
            {
                "site_id": site_id,
                "order_id": str(1000 + number),
                "sku": f" sku-{number} ",
                "amount": "19.995",
                "quantity": number,
            }
            for number in range(1, 6)
        ]
        orders.append(dict(orders[0]))  # 本批次重复订单。
        orders.append(
            {
                "site_id": site_id,
                "order_id": "invalid",
                "sku": " ",
                "amount": "10.00",
                "quantity": 1,
            }
        )
        return orders


class OrderRepository:
    """用字典模拟 (site_id, order_id) 唯一约束和幂等写入。"""

    def __init__(self) -> None:
        self._orders: dict[tuple[int, str], Order] = {}
        self.saved_batch_sizes: list[int] = []

    def save_batch(self, orders: list[Order]) -> int:
        self.saved_batch_sizes.append(len(orders))
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


# 作业 2：可靠性改造（重点）
# 给接口拉取增加最多 3 次重试；超时可以重试，订单校验失败不重试，并记录
# 实际重试次数。
# 作业 3：并发控制（重点）
# 使用 Semaphore(3) 同步 10 个店铺，并测试同时进入接口的请求数量不超过 3。
# 作业 4：幂等测试（重点）
# 同一个 OrderSyncService 连续执行两次同步，第二次不再新增订单，并解释 valid
# 与 saved 为什么可能不同。
# 作业 5：批处理扩展（次重点）
# 批次大小设置为 2，记录每次保存的批次大小，验证 5 条订单拆成 2、2、1。
class OrderSyncService:
    def __init__(
        self,
        api: OrderApi,
        repository: OrderRepository,
        *,
        concurrency: int = 5,
        batch_size: int = 500,
        timeout: float = 1.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.01,
    ) -> None:
        if concurrency <= 0 or batch_size <= 0 or timeout <= 0:
            raise ValueError("concurrency、batch_size 和 timeout 必须大于 0")
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
        fetched_results = await asyncio.gather(
            *(self._fetch_one(site_id, semaphore) for site_id in site_ids)
        )

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

        for batch in batched(valid_orders, self.batch_size):
            result.batch_sizes.append(len(batch))
            result.saved += self.repository.save_batch(batch)
        return result


# 作业 6：工程思考（次重点）
# 如果同步 1000 个店铺，每店 10 万条订单，当前 gather() 版本会出现什么问题？
# 如何改造成“分页拉取 + 有界队列 + 批量保存”？
PRODUCTION_DESIGN_ANSWER = """
1000 个店铺、每店 10 万订单时，一次性创建全部任务并用 gather 保留所有结果会
造成巨大的 Task 和订单对象内存占用。生产方案应按店铺和游标分页拉取；生产者
把每页数据写入有界 asyncio.Queue 形成背压；固定数量消费者完成清洗、校验与
批量保存；数据库用 (site_id, order_id) 唯一索引/UPSERT 保证幂等，并持久化
分页游标用于断点续传。还需要限流、重试退避、事务、失败队列、指标和监控。
""".strip()


async def run_self_check() -> None:
    cleaned = clean_order(
        {
            "site_id": 1,
            "order_id": "1001",
            "sku": " abc ",
            "amount": "19.995",
            "quantity": 2,
        }
    )
    assert cleaned.amount == Decimal("20.00")
    assert cleaned.total_amount == Decimal("40.00")
    try:
        clean_order(
            {
                "site_id": 1,
                "order_id": "1002",
                "sku": "ABC",
                "amount": "10",
                "quantity": 0,
            }
        )
    except OrderValidationError:
        pass
    else:
        raise AssertionError("quantity=0 应校验失败")

    try:
        clean_order(
            {
                "site_id": 1,
                "order_id": "1003",
                "sku": "ABC",
                "amount": "10",
                "quantity": 1.5,
            }
        )
    except OrderValidationError:
        pass
    else:
        raise AssertionError("quantity=1.5 不应被截断成整数")

    retry_api = FakeOrderApi(timeout_failures={1: 2})
    retry_service = OrderSyncService(
        retry_api,
        OrderRepository(),
        concurrency=1,
        batch_size=2,
        max_retries=3,
        retry_base_delay=0,
    )
    retry_result = await retry_service.sync([1])
    assert retry_api.calls[1] == 3
    assert retry_result.retries == 2
    assert retry_result.invalid == 1  # 校验失败没有触发接口重试。

    concurrency_api = FakeOrderApi(delay=0.02)
    concurrency_service = OrderSyncService(
        concurrency_api,
        OrderRepository(),
        concurrency=3,
        batch_size=20,
    )
    await concurrency_service.sync(list(range(1, 11)))
    assert concurrency_api.max_active_requests <= 3

    repository = OrderRepository()
    service = OrderSyncService(
        FakeOrderApi(delay=0),
        repository,
        concurrency=3,
        batch_size=2,
    )
    first = await service.sync([1])
    second = await service.sync([1])
    assert first.valid == 5 and first.saved == 5
    assert first.batch_sizes == [2, 2, 1]
    assert second.valid == 5 and second.saved == 0
    assert len(repository.list_all()) == 5

    # valid 表示通过校验且在本轮内去重后的数量；saved 还受持久化幂等约束影响。
    print("重试统计：", retry_result.retries)
    print("Semaphore 实测最大并发：", concurrency_api.max_active_requests)
    print("首次批次大小：", first.batch_sizes)
    print("两次保存数量：", first.saved, second.saved)
    print("Day 14 作业验收通过")


if __name__ == "__main__":
    asyncio.run(run_self_check())
