# 四十六、Day 9 作业1：自定义上下文类
#
# 实现：
#
import time
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import batched
from pathlib import Path
from typing import Iterator

import timer


class Timer:
    def __init__(self, name: str):
        self.name = name
        self.start_time: float | None = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        print(f"{self.name}开始")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        if self.start_time is not None:
            elapsed_time = self.end_time - self.start_time
            print(f"{self.name}结束，耗时{elapsed_time:.3f}秒")
#
# 支持：
#
#
# 要求使用：
#
# __enter__
# __exit__
#
# 输出：
#
# 订单清洗开始
# 订单清洗结束，耗时0.123秒
with Timer("订单清洗"):
    time.sleep(0.123)


# 四十七、作业2：事务模拟器
#
# 实现：
#
class Transaction:
    def __enter__(self):
        print("BEGIN")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print("COMMIT")
        else:
            print("ROLLBACK")

        print("CLOSE")

        return False
#
# 正常：
#
with Transaction():
    print("创建订单")
#
# 输出：
#
# BEGIN
# 创建订单
# COMMIT
# CLOSE
#
# 异常：
#
# with Transaction():
#     raise ValueError("库存不足")
#
# 输出：
#
# BEGIN
# ROLLBACK
# CLOSE
#
# 并且异常继续抛出。


# 四十八、作业3：使用 contextmanager 重写
#
# 把上面的：
#
# Transaction
#
# 再使用：
#
# @contextmanager
#
# 写一版。
#
# 要求理解：
#
# yield前 = enter
# yield后 = exit
# @contextmanager
# def transaction() -> Iterator[None]:
#     print("BEGIN")
#     try:
#         yield
#     except Exception:
#         print("ROLLBACK")
#         raise
#     else:
#         print("COMMIT")
#     finally:
#         print("CLOSE")
#
# with transaction():
#     raise ValueError("库存不足")


# 四十九、作业4：文件复制
#
# 实现：
#

def copy_file(
    source: Path,
    target: Path,
) -> None:
    if not source.exists():
        raise FileNotFoundError(f"源文件不存在：{source}")

    if not source.is_file():
        raise ValueError(f"源路径不是文件：{source}")

    # 自动创建目标文件的父目录
    target.parent.mkdir(parents=True, exist_ok=True)

    with (
        source.open("r", encoding="utf-8") as source_file,
        target.open("w", encoding="utf-8") as target_file,
    ):
        content = source_file.read()
        target_file.write(content)

#
# 要求同时：
#
# with (
#     source.open(...) as source_file,
#     target.open(...) as target_file,
# ):
#
# 不能手动：
#
# close()


# 五十、作业5：异常控制
#
# 实现：
#
# @contextmanager
# def ignore_value_error() -> Iterator[None]:
#     try:
#         yield
#     except ValueError:
#         pass
# #
# # 效果：
# #
# with ignore_value_error():
#     raise ValueError("测试")

print("继续")
#
# 允许吞掉：
#
# ValueError
#
# 但：
#
# TypeError
#
# 必须继续抛出。
#
# 这个作业用于让你理解：
#
# 上下文管理器可以控制异常传播。
#
# 但生产代码不要滥用这种模式。


# 五十一、加分作业：订单批处理计时
#
# 结合 Day 8：
#
# for batch in batched(
#     orders,
#     100,
# ):
#     with timer(
#         f"批次{batch_no}"
#     ):
#         process_batch(batch)
#
# 最后打印：
#
# 批次1耗时：0.120秒
# 批次2耗时：0.108秒
# 批次3耗时：0.141秒
#
# 这就把 Day 8：
#
# 生成器 / batched
#
# 和 Day 9：
#
# 上下文管理器
#
# 组合起来了。
@dataclass(kw_only=True)
class Order:
    order_no: str

@contextmanager
def timer(name: str) -> Iterator[None]:
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        print(f"{name}耗时{end_time - start_time}秒")

class Timer:
    def __init__(self, name: str):
        self.name = name
        self.start_time: float | None = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        if self.start_time is not None:
            elapsed_time = self.end_time - self.start_time
            print(f"{self.name}耗时{elapsed_time:.6f}秒")

def batch_handler(orders: list[Order]) -> None:
    for index, batch_order in enumerate(batched(orders, 1), start=1):
        with timer(f"批次{index}"):
            print(batch_order)

if __name__ == '__main__':
    orders = [
        Order(order_no="no1"),
        Order(order_no="no2"),
        Order(order_no="no3")
    ]
    batch_handler(orders)

# 五十二、今天必须记住
# with = 自动管理资源生命周期
#
# __enter__
# → 进入上下文
#
# __exit__
# → 离开上下文
#
# as变量
# → __enter__的返回值
#
# __exit__返回False/None
# → 异常继续传播
#
# __exit__返回True
# → 异常被吞掉
#
# @contextmanager
# → 用生成器方式快速创建上下文管理器
#
# yield前
# → 进入阶段
#
# yield后
# → 退出阶段


# Day 9 最重要的四句话
#
# 第一句：
#
# with 本质是把 try/finally 封装成可复用的资源管理协议。
#
# 第二句：
#
# Python 上下文管理器靠 __enter__() 和 __exit__() 工作。
#
# 第三句：
#
# @contextmanager 把 Day 8 的 yield 用到了资源生命周期管理上。
#
# 第四句：
#
# 只要一件事情有“获取/释放、开始/结束、加锁/解锁、提交/回滚”这种成对操作，就应该想到上下文管理器。