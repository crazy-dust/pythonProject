"""Day 13 作业正确答案：asyncio 并发、限流、失败隔离与队列。"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


# 练习 1：协程与并发（重点）
# 写 5 个协程，每个等待 1 秒并返回编号；分别用顺序 await 和 gather，观察总
# 耗时，并解释为什么一个约 5 秒、一个约 1 秒。
#
# 练习 2：限流（重点）
# 模拟 20 个 HTTP 请求，每个等待 0.5 秒，用 Semaphore(4) 限制并发；证明
# 同时进行的请求不超过 4 个。
#
# 练习 3：超时与失败隔离（重点）
# 第 3 个请求抛出 ValueError，第 7 个请求等待 3 秒，其余等待 0.2 秒；设置
# 1 秒超时，输出成功、失败、超时数量，保证单个失败不影响其他请求。
#
# 练习 4：生产者消费者
# 使用 asyncio.Queue(maxsize=5)，一个生产者生成 100 个订单，3 个消费者处理；
# 正确使用结束哨兵和 task_done()，确保每单恰好处理一次且程序正常退出。
#
# 练习 5：同步代码接入
# 写一个 time.sleep(2) 的同步函数，分别直接在协程中调用和通过
# asyncio.to_thread() 调用，对比 3 个任务耗时并解释事件循环为何不再被阻塞。


@dataclass(frozen=True, slots=True)
class TimingResult:
    sequential_seconds: float
    concurrent_seconds: float
    values: tuple[int, ...]


async def numbered_work(number: int, delay: float = 1.0) -> int:
    await asyncio.sleep(delay)
    return number


async def compare_sequential_and_gather(
    *,
    task_count: int = 5,
    delay: float = 1.0,
) -> TimingResult:
    start = time.perf_counter()
    sequential = [await numbered_work(number, delay) for number in range(1, task_count + 1)]
    sequential_seconds = time.perf_counter() - start

    start = time.perf_counter()
    concurrent = await asyncio.gather(
        *(numbered_work(number, delay) for number in range(1, task_count + 1))
    )
    concurrent_seconds = time.perf_counter() - start

    assert sequential == concurrent
    return TimingResult(sequential_seconds, concurrent_seconds, tuple(concurrent))


async def run_semaphore_demo(
    *,
    request_count: int = 20,
    limit: int = 4,
    delay: float = 0.5,
) -> tuple[list[int], int]:
    semaphore = asyncio.Semaphore(limit)
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
                await asyncio.sleep(delay)
                return request_id
            finally:
                async with state_lock:
                    active -= 1

    results = await asyncio.gather(*(request(i) for i in range(1, request_count + 1)))
    return results, max_active


@dataclass(frozen=True, slots=True)
class IsolationResult:
    successful: int
    failed: int
    timed_out: int


async def run_failure_isolation() -> IsolationResult:
    async def simulated_request(request_id: int) -> int:
        if request_id == 3:
            await asyncio.sleep(0.2)
            raise ValueError("第 3 个请求模拟业务失败")
        await asyncio.sleep(3.0 if request_id == 7 else 0.2)
        return request_id

    async def guarded_request(request_id: int) -> int:
        return await asyncio.wait_for(simulated_request(request_id), timeout=1.0)

    outcomes = await asyncio.gather(
        *(guarded_request(i) for i in range(1, 11)),
        return_exceptions=True,
    )
    successful = sum(not isinstance(item, BaseException) for item in outcomes)
    failed = sum(isinstance(item, ValueError) for item in outcomes)
    timed_out = sum(isinstance(item, TimeoutError) for item in outcomes)
    return IsolationResult(successful, failed, timed_out)


async def run_queue_demo(
    *,
    order_count: int = 100,
    consumer_count: int = 3,
) -> list[int]:
    queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=5)
    processed: list[int] = []

    async def producer() -> None:
        for order_id in range(1, order_count + 1):
            await queue.put(order_id)
        # 每个消费者都需要一个结束哨兵。
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
    producer_task = asyncio.create_task(producer())
    await producer_task
    await queue.join()
    await asyncio.gather(*consumers)
    return processed


def blocking_io(task_id: int, delay: float = 2.0) -> int:
    time.sleep(delay)
    return task_id


async def compare_blocking_and_to_thread(
    *,
    task_count: int = 3,
    delay: float = 2.0,
) -> tuple[float, float]:
    async def bad_call(task_id: int) -> int:
        # 这里没有异步等待点，time.sleep 会逐个阻塞事件循环。
        return blocking_io(task_id, delay)

    start = time.perf_counter()
    await asyncio.gather(*(bad_call(i) for i in range(task_count)))
    direct_seconds = time.perf_counter() - start

    start = time.perf_counter()
    await asyncio.gather(
        *(asyncio.to_thread(blocking_io, i, delay) for i in range(task_count))
    )
    threaded_seconds = time.perf_counter() - start
    return direct_seconds, threaded_seconds


async def main() -> None:
    timing = await compare_sequential_and_gather()
    assert timing.sequential_seconds >= 4.5
    assert timing.concurrent_seconds < 2.0

    requests, max_active = await run_semaphore_demo()
    assert len(requests) == 20
    assert max_active <= 4

    isolation = await run_failure_isolation()
    assert isolation == IsolationResult(successful=8, failed=1, timed_out=1)

    processed = await run_queue_demo()
    assert sorted(processed) == list(range(1, 101))
    assert len(processed) == len(set(processed)) == 100

    direct_seconds, threaded_seconds = await compare_blocking_and_to_thread()
    assert direct_seconds >= 5.5
    assert threaded_seconds < 3.5

    print(
        f"顺序约 {timing.sequential_seconds:.1f}s，并发约 "
        f"{timing.concurrent_seconds:.1f}s"
    )
    print(f"Semaphore 实测最大并发：{max_active}")
    print("失败隔离统计：", isolation)
    print("Queue 恰好处理订单数：", len(processed))
    print(f"直接阻塞约 {direct_seconds:.1f}s，to_thread 约 {threaded_seconds:.1f}s")
    print("Day 13 作业验收通过")


if __name__ == "__main__":
    asyncio.run(main())
