"""Day 13：asyncio、async/await 与异步并发。

学习目标
========
1. 区分协程函数、协程对象、Task 和 Future。
2. 理解 await 的执行语义，以及顺序等待与并发调度的区别。
3. 使用 gather、TaskGroup、超时和取消组织可靠的异步任务。
4. 使用 Semaphore、Lock、Event 和 Queue 控制并发与协作。
5. 避免阻塞事件循环，并用 asyncio.to_thread 接入同步 I/O。

一、协程与事件循环
------------------
协程是可以在执行过程中暂停、让出执行权，并在等待条件满足后恢复的执行单元。
它不是线程或进程，而是由事件循环协作式调度。

* ``async def work()`` 定义协程函数。
* ``work()`` 调用协程函数并得到协程对象，此时通常还没有执行。
* ``await work()`` 等待协程完成并取得结果。
* ``asyncio.create_task(work())`` 把协程交给事件循环调度。

如果协程对象既没有被 await，也没有交给 Task，程序会提示
``coroutine was never awaited``。普通脚本通常只在入口调用一次
``asyncio.run(main())``；已运行的事件循环内部不能再次调用 asyncio.run。

二、await 不等于并发
--------------------
``await`` 表示等待一个可等待对象。等待尚未完成时，当前协程可以让出执行权；
但连续执行多个 ``await`` 通常仍是顺序执行。

五个每次等待一秒的协程：

* 逐个 await：等待时间相加，总耗时约五秒。
* 先创建多个 Task 或交给 gather：等待区间重叠，总耗时约一秒。

asyncio 的主要收益来自 I/O 等待重叠，不会自动让纯 Python CPU 代码多核并行。

三、Task、gather 与 TaskGroup
----------------------------
Task 包装一个被事件循环管理的协程，并保存执行状态、结果、异常和取消状态。
``task.result()`` 不是等待方法；任务未完成时应优先 ``await task``。

``asyncio.gather`` 适合并发收集多个结果，返回顺序与传入顺序一致。默认情况下，
第一个异常会传播给等待方，但这不代表其他任务已经自动回滚或全部取消。若每个
任务允许独立成败，可以让任务内部转换状态，或使用
``gather(..., return_exceptions=True)`` 收集异常后分类。

``asyncio.TaskGroup`` 适合有共同生命周期的一组任务。若一个子任务出现未处理的
普通异常，TaskGroup 会取消其他未完成任务，等待清理，然后汇总传播异常。

四、超时、取消与资源清理
------------------------
Python 3.11+ 推荐用 ``asyncio.timeout`` 表达超时作用域；``asyncio.wait_for``
适合给单个等待对象设置超时。超时范围应明确：只限制 HTTP 拉取，还是限制整个
“拉取—清洗—保存”流程。

``task.cancel()`` 发出取消请求，CancelledError 通常在下一个可取消等待点抛出。
协程收到取消后应在 finally 中释放资源，并继续抛出 CancelledError；随意吞掉它
会破坏 TaskGroup 和超时机制的生命周期管理。

五、并发控制与协程协作
----------------------
* Semaphore：限制同时进入某段资源代码的协程数量。
* Lock：保护协程共享状态；读—改—写之间只要有 await，就可能出现竞态。
* Event：一个协程通知其他协程某个条件已经满足。
* Queue：组织生产者消费者；maxsize 提供背压。

Semaphore 限制的是进入资源区的并发量，不是已创建 Task 的总数。创建一百万个
Task 后再用 Semaphore(10)，仍会占用大量内存；超大规模任务应使用有界 Queue
和固定数量的 worker。

Queue 的关键规则：每次 ``get()`` 都要对应一次 ``task_done()``；``join()`` 等待
所有入队项处理完成；结束哨兵只是应用约定，有几个消费者通常就需要几个哨兵。

六、不要阻塞事件循环
--------------------
``async def`` 不会把内部代码自动变成非阻塞。直接调用 ``time.sleep``、``requests.get`` 或同步数据库查询，仍会阻塞整个事件循环。

优先使用真正的异步客户端；必须接入现有同步阻塞 I/O 时，可使用
``await asyncio.to_thread(function, *args)``。to_thread 不是纯 Python CPU 密集
计算的通用加速器，CPU 任务仍需评估进程池或原生扩展。

复习清单
--------
* 能解释协程函数、协程对象、Task 和 Future 的关系。
* 能说明连续 await 为什么没有自动并发。
* 能根据失败语义选择 gather(return_exceptions=True) 或 TaskGroup。
* 能正确设置超时、传播取消并在 finally 中释放资源。
* 能使用 Semaphore 和 Queue(maxsize) 控制并发与内存。
* 能识别阻塞事件循环的同步调用，并合理使用 to_thread。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1. 顺序 await 与 gather 并发
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TimingResult:
    sequential_seconds: float
    concurrent_seconds: float
    values: tuple[int, ...]


async def delayed_number(number: int, delay: float = 0.1) -> int:
    await asyncio.sleep(delay)
    return number


async def compare_sequential_and_concurrent(
    *,
    task_count: int = 5,
    delay: float = 0.1,
) -> TimingResult:
    start = time.perf_counter()
    sequential = [
        await delayed_number(number, delay)
        for number in range(1, task_count + 1)
    ]
    sequential_seconds = time.perf_counter() - start

    start = time.perf_counter()
    concurrent = await asyncio.gather(
        *(delayed_number(number, delay) for number in range(1, task_count + 1))
    )
    concurrent_seconds = time.perf_counter() - start

    assert sequential == concurrent
    return TimingResult(
        sequential_seconds=sequential_seconds,
        concurrent_seconds=concurrent_seconds,
        values=tuple(concurrent),
    )


# ---------------------------------------------------------------------------
# 2. gather：收集独立任务的成功、失败与超时
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OutcomeSummary:
    successful: int
    failed: int
    timed_out: int


async def simulated_request(request_id: int) -> int:
    if request_id == 3:
        await asyncio.sleep(0.02)
        raise ValueError("第 3 个请求模拟业务失败")
    await asyncio.sleep(0.3 if request_id == 7 else 0.02)
    return request_id


async def collect_independent_outcomes() -> OutcomeSummary:
    async def guarded(request_id: int) -> int:
        return await asyncio.wait_for(simulated_request(request_id), timeout=0.1)

    outcomes = await asyncio.gather(
        *(guarded(request_id) for request_id in range(1, 11)),
        return_exceptions=True,
    )
    return OutcomeSummary(
        successful=sum(not isinstance(item, BaseException) for item in outcomes),
        failed=sum(isinstance(item, ValueError) for item in outcomes),
        timed_out=sum(isinstance(item, TimeoutError) for item in outcomes),
    )


# ---------------------------------------------------------------------------
# 3. Semaphore：只限制外部接口阶段
# ---------------------------------------------------------------------------


async def limited_requests(
    *,
    request_count: int = 20,
    concurrency: int = 4,
) -> tuple[list[int], int]:
    semaphore = asyncio.Semaphore(concurrency)
    state_lock = asyncio.Lock()
    active = 0
    max_active = 0

    async def request(request_id: int) -> int:
        nonlocal active, max_active
        async with semaphore:
            async with state_lock:
                active += 1
                max_active = max(max_active, active)
            try:
                await asyncio.sleep(0.01)
                return request_id
            finally:
                async with state_lock:
                    active -= 1

    results = await asyncio.gather(
        *(request(request_id) for request_id in range(1, request_count + 1))
    )
    return results, max_active


# ---------------------------------------------------------------------------
# 4. Queue：有界生产者消费者
# ---------------------------------------------------------------------------


async def process_with_queue(
    *,
    order_count: int = 100,
    consumer_count: int = 3,
) -> list[int]:
    queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=5)
    processed: list[int] = []

    async def producer() -> None:
        for order_id in range(1, order_count + 1):
            await queue.put(order_id)
        for _ in range(consumer_count):
            await queue.put(None)

    async def consumer() -> None:
        while True:
            order_id = await queue.get()
            try:
                if order_id is None:
                    return
                await asyncio.sleep(0)
                processed.append(order_id)
            finally:
                queue.task_done()

    consumers = [asyncio.create_task(consumer()) for _ in range(consumer_count)]
    await producer()
    await queue.join()
    await asyncio.gather(*consumers)
    return processed


# ---------------------------------------------------------------------------
# 5. TaskGroup：共同生命周期的订单处理任务
# ---------------------------------------------------------------------------


async def process_order(order_id: int) -> str:
    await asyncio.sleep(0.01)
    return f"order-{order_id}"


async def process_orders_as_group(order_ids: list[int]) -> list[str]:
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(process_order(order_id)) for order_id in order_ids]
    return [task.result() for task in tasks]


# ---------------------------------------------------------------------------
# 6. to_thread：桥接同步阻塞 I/O
# ---------------------------------------------------------------------------


def blocking_io(task_id: int, delay: float = 0.03) -> int:
    time.sleep(delay)
    return task_id


async def bridge_blocking_io(task_ids: list[int]) -> list[int]:
    return list(
        await asyncio.gather(
            *(asyncio.to_thread(blocking_io, task_id) for task_id in task_ids)
        )
    )


# ---------------------------------------------------------------------------
# 7. 取消：清理后继续传播 CancelledError
# ---------------------------------------------------------------------------


async def cancellable_worker(cleanup_log: list[str]) -> None:
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        cleanup_log.append("cancelled")
        raise
    finally:
        cleanup_log.append("released")


async def verify_cancellation() -> list[str]:
    cleanup_log: list[str] = []
    task = asyncio.create_task(cancellable_worker(cleanup_log))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    return cleanup_log


async def main() -> None:
    timing = await compare_sequential_and_concurrent()
    assert timing.sequential_seconds >= 0.45
    assert timing.concurrent_seconds < 0.25

    outcomes = await collect_independent_outcomes()
    assert outcomes == OutcomeSummary(successful=8, failed=1, timed_out=1)

    results, max_active = await limited_requests()
    assert len(results) == 20
    assert max_active <= 4

    processed = await process_with_queue()
    assert sorted(processed) == list(range(1, 101))
    assert len(processed) == len(set(processed)) == 100

    grouped = await process_orders_as_group([1, 2, 3])
    assert grouped == ["order-1", "order-2", "order-3"]

    bridged = await bridge_blocking_io([1, 2, 3])
    assert bridged == [1, 2, 3]

    cleanup_log = await verify_cancellation()
    assert cleanup_log == ["cancelled", "released"]

    print(
        f"顺序约 {timing.sequential_seconds:.2f}s，"
        f"并发约 {timing.concurrent_seconds:.2f}s"
    )
    print("独立结果：", outcomes)
    print("最大并发：", max_active)
    print("Queue 处理数量：", len(processed))
    print("Day 13 示例检查通过")


if __name__ == "__main__":
    asyncio.run(main())
