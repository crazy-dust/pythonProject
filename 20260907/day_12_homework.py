"""Day 12 作业正确答案：线程池、异常隔离、锁和进程池。"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass


# 作业 1：线程池基础
# 实现 fetch_order_count(site_id)，模拟 5 个站点；使用
# ThreadPoolExecutor(max_workers=3) 和 as_completed()，每站返回订单数量，
# 最后统计总订单数。
#
# 作业 2：异常隔离
# 在作业 1 基础上让站点 3 抛出异常；其他站点继续执行，记录失败站点，最终
# 输出成功数、失败数和订单总数，不能因一个站点失败让整个批次退出。
#
# 作业 3：共享状态与锁
# 5 个线程共同修改计数器，每线程执行 10,000 次；使用 Lock 保证最终结果正确，
# 并解释为什么不能依赖 GIL 保证业务正确性。
#
# 作业 4：进程池
# 实现 calculate_sum(limit)，用 ProcessPoolExecutor 提交 4 个 CPU 任务并获取
# 全部结果；使用 if __name__ == "__main__"，解释任务函数不能随便写成局部
# 函数或 lambda。
#
# 作业 5：思考题
# 同步 200 个 Shopify 站点，每站平均请求 1 秒且有独立 API 限流：应该使用
# 线程池还是进程池？max_workers 如何确定？单站失败如何隔离？如何避免重复同步？


@dataclass(frozen=True, slots=True)
class ThreadBatchResult:
    successful_sites: tuple[int, ...]
    failed_sites: dict[int, str]
    total_orders: int


def fetch_order_count(
    site_id: int,
    *,
    fail_site_3: bool = False,
    delay: float = 0.02,
) -> int:
    """模拟 I/O 请求，并返回某个站点的订单数量。"""
    time.sleep(delay)
    if fail_site_3 and site_id == 3:
        raise RuntimeError("站点 3 模拟接口失败")
    return site_id * 10


def run_thread_pool_demo(*, fail_site_3: bool = False) -> ThreadBatchResult:
    site_ids = [1, 2, 3, 4, 5]
    successful: list[int] = []
    failed: dict[int, str] = {}
    total_orders = 0

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="site-sync") as executor:
        future_to_site = {
            executor.submit(
                fetch_order_count,
                site_id,
                fail_site_3=fail_site_3,
            ): site_id
            for site_id in site_ids
        }

        # as_completed 按完成顺序返回；future.result() 会重新抛出工作线程异常。
        for future in as_completed(future_to_site):
            site_id = future_to_site[future]
            try:
                order_count = future.result()
            except Exception as exc:
                failed[site_id] = str(exc)
            else:
                successful.append(site_id)
                total_orders += order_count

    return ThreadBatchResult(tuple(sorted(successful)), failed, total_orders)


def run_locked_counter(*, workers: int = 5, increments: int = 10_000) -> int:
    """由多个线程安全地执行共享计数器的读-改-写。"""
    counter = 0
    lock = threading.Lock()

    def increment() -> None:
        nonlocal counter
        for _ in range(increments):
            # GIL 不是业务一致性锁；临界区仍需显式 Lock。
            with lock:
                counter += 1

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(increment) for _ in range(workers)]
        for future in futures:
            future.result()

    return counter


def calculate_sum(limit: int) -> int:
    """模块顶层的纯 Python CPU 任务，可被进程池 pickle。"""
    return sum(i * i for i in range(limit))


def run_process_pool_demo(limits: list[int] | None = None) -> list[int]:
    task_limits = limits or [100_000] * 4
    if len(task_limits) != 4:
        raise ValueError("必须提交 4 个 CPU 计算任务")

    with ProcessPoolExecutor(max_workers=4) as executor:
        return list(executor.map(calculate_sum, task_limits))


SHOPIFY_SCENARIO_ANSWER = """
200 个 Shopify 站点主要在等待网络，优先使用线程池（同步 SDK）或 asyncio
（异步客户端），不应使用进程池。max_workers 需要结合每店铺 API 限流、HTTP
连接池、数据库连接池、本机资源和压测结果确定，而不是直接设为 200。用
future_to_site + as_completed 对每个 Future 单独 try/except，可让单站点失败不
影响其他站点。避免重复同步应使用 (site_id, order_id) 业务唯一键、数据库唯一
索引或 UPSERT，并记录同步游标；内存 set 只能解决单批次内去重。
""".strip()


def run_self_check() -> None:
    all_success = run_thread_pool_demo()
    assert len(all_success.successful_sites) == 5
    assert not all_success.failed_sites
    assert all_success.total_orders == 150

    isolated_failure = run_thread_pool_demo(fail_site_3=True)
    assert len(isolated_failure.successful_sites) == 4
    assert set(isolated_failure.failed_sites) == {3}
    assert isolated_failure.total_orders == 120

    assert run_locked_counter() == 50_000

    process_results = run_process_pool_demo()
    assert len(process_results) == 4
    assert len(set(process_results)) == 1

    print("线程池异常隔离：", isolated_failure)
    print("加锁计数器：50,000")
    print("进程池结果数量：", len(process_results))
    print("Day 12 作业验收通过")


if __name__ == "__main__":
    # Windows 子进程会重新导入主模块，创建进程池必须放在入口保护内。
    run_self_check()
