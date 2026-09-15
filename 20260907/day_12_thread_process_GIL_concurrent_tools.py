"""Day 12：线程、进程、GIL 与 concurrent.futures。

学习目标
========
1. 区分并发与并行，并根据任务瓶颈选择工具。
2. 使用 ThreadPoolExecutor、Future 和 as_completed 组织同步 I/O 并发。
3. 正确回收任务异常，并用 Lock 保护线程共享状态。
4. 使用 ProcessPoolExecutor 执行纯 Python CPU 密集任务。

一、先判断任务类型
------------------
并发表示多个任务在同一时间段内推进；并行表示多个任务真正同时占用不同 CPU
核心。选择工具前要先定位瓶颈：

* HTTP、远程数据库、下载等 I/O 密集任务：线程池或 asyncio。
* 大量纯 Python 计算：通常优先考虑进程池。
* 单次轻量清洗或金额计算：直接执行通常比引入并发更简单。

并发量不是越大越好。线程数还会受到 API 限流、HTTP 连接池、数据库连接池、
CPU、内存和下游承载能力的约束，应通过测量确定。

二、GIL 的正确理解
------------------
常规 CPython 的 GIL 会限制一个进程内同时执行 Python 字节码的线程数量，因此
纯 Python CPU 密集任务通常不能靠普通线程实现多核并行。但线程在网络或文件
I/O 等待期间会让其他线程继续工作，所以 I/O 密集任务仍能明显受益。

GIL 不是业务数据的一致性锁。``counter += 1`` 在业务上包含读取、计算和写回，
多个线程修改共享状态时仍应使用 Lock，不能依赖某个解释器版本中“碰巧原子”的
行为。Python 3.14 提供可选的 free-threaded 构建，但并非所有安装和第三方库都
默认采用它；业务代码仍应显式表达同步要求。

三、Future 与线程池
-------------------
``executor.submit()`` 返回 Future，而不是业务结果。Future 保存任务状态、结果
或异常。调用 ``future.result()`` 时，工作线程中的异常会在当前线程重新抛出。

推荐模式是：先提交全部任务，再用 ``as_completed()`` 按完成顺序处理，并用
``future -> business_id`` 字典保留业务上下文。不要每提交一个任务就立刻调用
``result()``，否则并发会退化成近似串行。

``executor.map()`` 适合简单映射，但按输入顺序返回结果；``as_completed()``
适合需要完成顺序、业务 ID 和逐任务异常隔离的场景。

四、线程同步工具
----------------
* Lock：保护同一进程内线程共享状态的临界区。
* RLock：允许同一线程重复获取同一把锁，适合受锁方法的嵌套调用。
* threading.local：为每个线程保存独立上下文；线程池复用线程时要清理旧值。
* Event：在线程间传递开始、就绪或停止信号，适合实现优雅退出。

Lock 不能替代数据库事务、Redis 分布式锁或跨服务的一致性机制。

五、进程池
----------
进程有独立解释器和内存，可让纯 Python CPU 任务使用多个核心，但创建和数据传输
成本更高。任务函数和参数通常必须能被 pickle，因此任务函数应放在模块顶层，
不要依赖 lambda 或局部函数。

Windows 子进程会重新导入主模块，创建进程池的代码必须放在
``if __name__ == "__main__"`` 入口保护内。

六、超时与取消
--------------
``future.result(timeout=1)`` 只表示当前线程最多等待一秒，不会强制杀死已运行
任务。``future.cancel()`` 通常也只能取消尚未开始的任务。网络连接与读取超时应
在 HTTP 客户端中设置；长任务的停止需要任务主动检查 Event 等停止信号。

复习清单
--------
* 能解释 I/O 密集与 CPU 密集任务为何选择不同工具。
* 能写出 Future 到业务 ID 的映射和 as_completed 异常隔离。
* 能解释 GIL 为什么既不等于“线程无用”，也不等于“无需加锁”。
* 能说明 Future 超时、网络超时和强制终止的区别。
* 能安全启动 ProcessPoolExecutor，并说明 pickle 限制。
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1. 线程池：按完成顺序处理，并隔离单站点异常
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SiteSyncResult:
    site_id: int
    order_count: int


@dataclass(frozen=True, slots=True)
class BatchSummary:
    successful: tuple[SiteSyncResult, ...]
    failed_sites: dict[int, str]

    @property
    def total_orders(self) -> int:
        return sum(result.order_count for result in self.successful)


def fetch_order_count(
    site_id: int,
    *,
    failed_site: int | None = None,
    delay: float = 0.02,
) -> SiteSyncResult:
    """用 sleep 模拟同步 HTTP I/O。"""
    time.sleep(delay)
    if site_id == failed_site:
        raise RuntimeError(f"站点 {site_id} 模拟接口失败")
    return SiteSyncResult(site_id=site_id, order_count=site_id * 10)


def sync_sites_with_threads(
    site_ids: list[int],
    *,
    max_workers: int = 3,
    failed_site: int | None = None,
) -> BatchSummary:
    if max_workers <= 0:
        raise ValueError("max_workers 必须大于 0")

    successful: list[SiteSyncResult] = []
    failed_sites: dict[int, str] = {}

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="site-sync",
    ) as executor:
        future_to_site = {
            executor.submit(
                fetch_order_count,
                site_id,
                failed_site=failed_site,
            ): site_id
            for site_id in site_ids
        }

        for future in as_completed(future_to_site):
            site_id = future_to_site[future]
            try:
                successful.append(future.result())
            except RuntimeError as exc:
                failed_sites[site_id] = str(exc)

    return BatchSummary(
        successful=tuple(sorted(successful, key=lambda item: item.site_id)),
        failed_sites=failed_sites,
    )


# ---------------------------------------------------------------------------
# 2. Lock：保护共享计数器的读-改-写
# ---------------------------------------------------------------------------


def count_with_lock(*, workers: int = 5, increments: int = 10_000) -> int:
    counter = 0
    lock = threading.Lock()

    def increment() -> None:
        nonlocal counter
        for _ in range(increments):
            with lock:
                counter += 1

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(increment) for _ in range(workers)]
        for future in futures:
            future.result()

    return counter


class NestedCounter:
    """RLock 允许 increase_twice 调用另一个同样需要锁的方法。"""

    def __init__(self) -> None:
        self.value = 0
        self._lock = threading.RLock()

    def increase(self) -> None:
        with self._lock:
            self.value += 1

    def increase_twice(self) -> None:
        with self._lock:
            self.increase()
            self.increase()


# ---------------------------------------------------------------------------
# 3. Event：通过显式信号让线程停止
# ---------------------------------------------------------------------------


def event_worker(stop_event: threading.Event, ticks: list[int]) -> None:
    while not stop_event.is_set():
        ticks.append(len(ticks) + 1)
        stop_event.wait(0.005)


def demonstrate_event() -> int:
    stop_event = threading.Event()
    ticks: list[int] = []
    thread = threading.Thread(target=event_worker, args=(stop_event, ticks))
    thread.start()
    time.sleep(0.02)
    stop_event.set()
    thread.join()
    return len(ticks)


# ---------------------------------------------------------------------------
# 4. 进程池：顶层函数 + __main__ 入口保护
# ---------------------------------------------------------------------------


def calculate_sum(limit: int) -> int:
    """模拟纯 Python CPU 计算；模块顶层函数可以被进程池序列化。"""
    return sum(number * number for number in range(limit))


def calculate_in_processes(limits: list[int]) -> list[int]:
    with ProcessPoolExecutor(max_workers=min(4, len(limits))) as executor:
        return list(executor.map(calculate_sum, limits))


def main() -> None:
    normal = sync_sites_with_threads([1, 2, 3, 4, 5])
    assert len(normal.successful) == 5
    assert normal.total_orders == 150

    isolated = sync_sites_with_threads([1, 2, 3, 4, 5], failed_site=3)
    assert len(isolated.successful) == 4
    assert set(isolated.failed_sites) == {3}
    assert isolated.total_orders == 120

    assert count_with_lock() == 50_000

    nested = NestedCounter()
    nested.increase_twice()
    assert nested.value == 2

    assert demonstrate_event() > 0

    process_results = calculate_in_processes([50_000] * 4)
    assert len(process_results) == 4
    assert len(set(process_results)) == 1

    print("线程池汇总：", isolated)
    print("加锁计数：50,000")
    print("进程池任务数：", len(process_results))
    print("Day 12 示例检查通过")


if __name__ == "__main__":
    main()
