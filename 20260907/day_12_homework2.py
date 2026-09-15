# 现在把今天的核心知识组合起来。
# 业务要求
# 模拟同步多个站点订单：
# 最多同时执行 3 个站点；
# 每个站点可能成功或失败；
# 谁先完成就先处理谁；
# 单个站点失败不影响其他站点；
# 最后统计成功和失败数量；
# 不在工作线程里直接修改共享统计变量。
import logging
import time
from asyncio import as_completed
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SyncResult:
    site_id: int
    totalOrder: int
    successCount: int
    failCount: int


def sync_site(site_id: int) -> SyncResult:
    logger.info(f"开始同步站点 {site_id}")

    time.sleep(0.5 + site_id * 0.1)

    if site_id == 3:
        raise ValueError("模拟异常")

    result = SyncResult(site_id=site_id, totalOrder=site_id * 10, successCount=0, failCount=0)

    logger.info(f"站点同步完成 {site_id}")

    return result


def main() -> None:
    site_ids = [1, 2, 3, 4, 5]
    success_results: list[SyncResult] = []
    failed_sites: dict[int, str] = {}

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="thread-order_sync") as executor:
        # 提交全部任务
        feature_to_site = {
            executor.submit(sync_site, site_id): site_id for site_id in site_ids
        }

        # 按顺序获取任务
        for feature in as_completed(feature_to_site):
            site_id = feature_to_site[feature]

            try:
                result = feature.result()
            except Exception as e:
                failed_sites[site_id] = str(e)
                logger.error("同步失败 site_id = %s error = %s", site_id, str(e))
            else:
                success_results.append(result)

    # 统计在主线程完成，不需要额外加锁
    total_orders = sum(result.successCount for result in success_results)
    print(f"成功站点数：{len(success_results)}")
    print(f"失败站点数：{len(failed_sites)}")
    print(f"同步订单总数：{total_orders}")
    print(f"失败站点：{failed_sites}")


if __name__ == '__main__':
    main()
