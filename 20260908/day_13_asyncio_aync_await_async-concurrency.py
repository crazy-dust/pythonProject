# 第
# 13
# 天：asyncio
# 异步编程
#
# 今天的重点不是记住 async 和
# await 两个关键字，而是建立一套完整的异步编程模型：协程是什么 → 事件循环如何调度 → Task
# 如何并发 → 如何处理超时、取消、异常 → 如何控制并发 → 如何与线程协作。
#
# 你已经学过第
# 12
# 天的线程，可以把今天理解为：线程主要依靠操作系统调度；asyncio
# 主要依靠协程在合适的位置主动让出执行权。 两者都能提高
# I / O
# 密集型任务的吞吐量，但实现方式不同。
#
# 一、今天的学习目标与重点级别
#
# 模块
#
# 重点
#
# 学完应该掌握
#
# 协程与 async / await
#
#
#
# ⭐⭐⭐⭐⭐
#
#
#
# 区分协程函数、协程对象、Task，理解
# await
#
# 事件循环
#
#
#
# ⭐⭐⭐⭐⭐
#
#
#
# 理解单线程如何运行多个
# I / O
# 任务
#
# create_task
# 与
# gather
#
#
#
# ⭐⭐⭐⭐⭐
#
#
#
# 正确创建并发任务，理解顺序执行与并发执行
#
# TaskGroup
#
#
#
# ⭐⭐⭐⭐⭐
#
#
#
# 掌握现代
# Python
# 的结构化并发
#
# 超时、取消、异常
#
#
#
# ⭐⭐⭐⭐⭐
#
#
#
# 写出不会失控的异步任务
#
# Semaphore
# 并发控制
#
#
#
# ⭐⭐⭐⭐⭐
#
#
#
# 控制
# HTTP、数据库等资源的并发量
#
# Lock、Event、Queue
#
#
#
# ⭐⭐⭐⭐
#
#
#
# 掌握协程间同步与生产者消费者
#
# asyncio.to_thread
#
#
#
# ⭐⭐⭐⭐
#
#
#
# 把阻塞同步代码接入异步系统
#
# Future、shield、底层事件循环
#
#
#
# ⭐⭐
#
#
#
# 理解用途即可，暂时不需要深入实现
#
# 今天的核心验收标准：能够独立写出一个“并发拉取订单 → 限流 → 超时处理 → 清洗 → 存储 → 正确收尾”的异步程序。
#
# 二、先把协程彻底讲明白
# 1.
# 什么是协程？
#
# 协程（Coroutine）是一种可以在执行过程中暂停，并在之后恢复执行的函数执行单元。
#
# 普通函数通常是：
#
# 调用 → 一直执行 → 返回
#
# 协程可以是：
#
# 执行一部分 → await 等待 → 暂停
# ↓
# 其他协程执行
# ↓
# 等待条件满足
# ↓
# 恢复执行 → 返回
#
# 协程不是线程，也不是进程。它是一种由程序语言和运行时支持的协作式并发机制。
#
# 2.
#
#
# async def 、协程对象
#
# 、await
# import asyncio
#
#
# async def hello() -> str:
#     print("开始执行")
#     await asyncio.sleep(1)
#     print("执行结束")
#     return "hello"
#
#
# async def main() -> None:
#     result = await hello()
#     print(result)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
#
# 输出：
#
# 开始执行
# 执行结束
# hello
#
# 这里有三个不同的概念：
#
# 写法
#
# 含义
#
#
# async def hello()
#
#
# 定义一个协程函数
#
# hello()
#
# 调用协程函数，得到协程对象
#
# await hello()
#
# 等待协程执行并取得结果
#
# 注意：调用协程函数，并不等于它已经开始执行。
#
# import asyncio
#
#
# async def hello() -> str:
#     print("真正开始执行")
#     return "OK"
#
#
# async def main() -> None:
#     coro = hello()
#     print("协程对象已经创建")
#
#     result = await coro
#     print(result)
#
#
# asyncio.run(main())
#
# 输出：
#
# 协程对象已经创建
# 真正开始执行
# OK
#
# 如果只写：
#
# coro = hello()
#
# 而既不
# await，也不把它交给
# Task
# 调度，那么它通常不会执行。协程对象被回收时，还可能出现
# coroutine
# was
# never
# awaited
# 警告。
#
# 3.
# await 到底做了什么？
#
# await 的含义是：
#
# 等待一个可等待对象完成，并在需要等待时允许事件循环运行其他任务。
#
# 例如：
#
# await asyncio.sleep(2)
#
# 当前协程不需要占着
# CPU
# 空转两秒，可以暂时让出执行权。
#
# 但有一个重要细节：不是每次执行
# await 都一定发生任务切换。 如果等待的操作已经完成，它可能直接继续执行。
#
# 三、事件循环：asyncio
# 的调度中心
# 1.
# 事件循环是什么？
#
# 事件循环（Event
# Loop）负责管理异步任务，处理
# I / O
# 就绪事件、定时器和任务恢复。
#
# 可以把它理解成一个调度器：
#
# 事件循环
# │
# ├── 协程
# A：发起
# HTTP
# 请求 → 等待网络
# ├── 协程
# B：查询数据库   → 等待数据库
# └── 协程
# C：定时器       → 等待时间
#
# 网络返回 / 数据库返回 / 定时器到期
# ↓
# 事件循环恢复对应协程
#
# 一个典型的
# asyncio
# 程序，通常由一个线程中的一个事件循环调度多个协程。它们不是同时在多个
# CPU
# 核心上执行
# Python
# 代码，而是在等待期间交替推进。
#
# 2.
# 和第
# 12
# 天线程的区别
#
# 对比
#
# threading
#
# asyncio
#
# 调度方式
#
# 主要由操作系统调度
#
# 主要由事件循环协作式调度
#
# 执行单位
#
# 线程
#
# 协程 / Task
#
# 等待
# I / O
#
# 线程可以阻塞，CPU
# 可运行其他线程
#
# 协程通过异步等待让出执行权
#
# 资源开销
#
# 每个线程有线程栈等开销
#
# Task
# 通常更轻量
#
# 适合场景
#
# 阻塞
# I / O、同步库集成
#
# 大量可异步化的
# I / O
#
# CPU
# 密集计算
#
# 可结合进程等方式
#
# 单纯
# asyncio
# 不会自动加速
#
# 你第
# 12
# 天的订单例子，换成
# asyncio
# 就是：
#
# Task
# A：HTTP
# 拉取订单 ─────等待─────→ 清洗 → 存储
# Task
# B：HTTP
# 拉取订单 ─────等待─────→ 清洗 → 存储
# Task
# C：HTTP
# 拉取订单 ─────等待─────→ 清洗 → 存储
#
# 关键：等待必须是“异步等待”，而不是把同步阻塞代码直接放进
#
#
# async def 。
#
#
# 3.
# asyncio.run()
# asyncio.run(main())
#
# 它是普通脚本启动
# asyncio
# 程序的推荐入口，负责创建事件循环、运行主协程，并在结束时进行收尾。
#
# 你通常只需要在程序入口调用一次：
#
# async def main() -> None:
#     ...
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
#
# 不要在已经运行的事件循环内部再次调用
# asyncio.run()。
#
# 四、顺序执行与并发执行：最重要的第一个实验
# 1.
# 顺序执行
# import asyncio
# import time
#
#
# async def fetch_order(order_id: int) -> str:
#     print(f"订单 {order_id} 开始")
#     await asyncio.sleep(2)
#     print(f"订单 {order_id} 完成")
#     return f"order-{order_id}"
#
#
# async def main() -> None:
#     start = time.perf_counter()
#
#     result1 = await fetch_order(1)
#     result2 = await fetch_order(2)
#     result3 = await fetch_order(3)
#
#     print([result1, result2, result3])
#     print(f"耗时约 {time.perf_counter() - start:.1f} 秒")
#
#
# asyncio.run(main())
#
# 输出示意：
#
# 订单
# 1
# 开始
# 订单
# 1
# 完成
# 订单
# 2
# 开始
# 订单
# 2
# 完成
# 订单
# 3
# 开始
# 订单
# 3
# 完成
# ['order-1', 'order-2', 'order-3']
# 耗时约
# 6.0
# 秒
#
# 虽然函数都是
#
#
# async def ，但你连续
#
#
# await，仍然是顺序执行。
#
# 2.
# 使用
# create_task
# 并发执行
# import asyncio
# import time
#
#
# async def fetch_order(order_id: int) -> str:
#     print(f"订单 {order_id} 开始")
#     await asyncio.sleep(2)
#     print(f"订单 {order_id} 完成")
#     return f"order-{order_id}"
#
#
# async def main() -> None:
#     start = time.perf_counter()
#
#     tasks = [
#         asyncio.create_task(fetch_order(1)),
#         asyncio.create_task(fetch_order(2)),
#         asyncio.create_task(fetch_order(3)),
#     ]
#
#     results = await asyncio.gather(*tasks)
#
#     print(results)
#     print(f"耗时约 {time.perf_counter() - start:.1f} 秒")
#
#
# asyncio.run(main())
#
# 输出示意：
#
# 订单
# 1
# 开始
# 订单
# 2
# 开始
# 订单
# 3
# 开始
# 订单
# 1
# 完成
# 订单
# 2
# 完成
# 订单
# 3
# 完成
# ['order-1', 'order-2', 'order-3']
# 耗时约
# 2.0
# 秒
#
# 这就是异步并发的核心收益：三个任务的等待时间发生了重叠。
#
# 实际运行时间会有少量误差；同时完成的任务，其打印顺序也不应该作为业务保证。
#
# 五、Task：协程真正被调度的载体
# 1.
# 协程对象和
# Task
# 的区别
# coro = fetch_order(1)
# task = asyncio.create_task(fetch_order(2))
#
# coro
# 只是协程对象；task
# 是事件循环可以调度和管理的任务。
#
# 一个
# Task
# 可以理解为：
#
# 一个正在被事件循环管理的协程，以及它的执行状态、结果、异常和取消能力。
#
# 2.
# Task
# 的常用操作
# import asyncio
#
#
# async def work() -> int:
#     await asyncio.sleep(1)
#     return 100
#
#
# async def main() -> None:
#     task = asyncio.create_task(work(), name="my-work")
#
#     print(task.get_name())
#     print(task.done())
#
#     result = await task
#
#     print(result)
#     print(task.done())
#     print(task.result())
#
#
# asyncio.run(main())
#
# 输出：
#
# my - work
# False
# 100
# True
# 100
#
# 常用方法：
#
# 方法
#
# 作用
#
# task.done()
#
# 是否已经完成
#
# task.cancel()
#
# 请求取消任务
#
# task.cancelled()
#
# 是否最终以取消状态结束
#
# task.result()
#
# 获取已完成任务的结果
#
# task.exception()
#
# 获取已完成任务的异常
#
# task.get_name()
#
# 获取任务名称
#
# 注意： result()
# 和
# exception()
# 不是等待方法。任务还没完成时直接调用，会抛出异常。通常优先使用
# await task。
#
# 六、gather
# 与
# TaskGroup：现代异步并发的两种重要方式
# 1.
# asyncio.gather()
#
# gather
# 适合把多个异步操作并发执行，并收集它们的结果。
#
# import asyncio
#
#
# async def square(n: int) -> int:
#     await asyncio.sleep(0.1)
#     return n * n
#
#
# async def main() -> None:
#     results = await asyncio.gather(
#         square(2),
#         square(3),
#         square(4),
#     )
#     print(results)
#
#
# asyncio.run(main())
#
# 输出：
#
# [4, 9, 16]
#
# gather
# 返回的结果顺序与传入顺序一致，不取决于任务实际完成顺序。
#
# 2.
# return_exceptions = True
# import asyncio
#
#
# async def work(n: int) -> int:
#     await asyncio.sleep(0.1)
#     if n == 2:
#         raise ValueError("订单 2 失败")
#     return n * 10
#
#
# async def main() -> None:
#     results = await asyncio.gather(
#         work(1),
#         work(2),
#         work(3),
#         return_exceptions=True,
#     )
#
#     for result in results:
#         if isinstance(result, BaseException):
#             print(f"失败：{result}")
#         else:
#             print(f"成功：{result}")
#
#
# asyncio.run(main())
#
# 输出：
#
# 成功：10
# 失败：订单
# 2
# 失败
# 成功：30
#
# 默认情况下，gather
# 会将第一个异常传播给等待它的协程。这不意味着其他任务一定已经被取消；它们可能继续运行。不要把它误解成“一个失败，全部自动回滚”。
#
# 3.
# TaskGroup：第
# 13
# 天必须掌握
#
# Python
# 3.11
# 引入的
# asyncio.TaskGroup
# 是现代
# asyncio
# 的重要能力。
#
# import asyncio
#
#
# async def fetch_order(order_id: int) -> str:
#     await asyncio.sleep(0.5)
#     return f"order-{order_id}"
#
#
# async def main() -> None:
#     async with asyncio.TaskGroup() as tg:
#         task1 = tg.create_task(fetch_order(1))
#         task2 = tg.create_task(fetch_order(2))
#         task3 = tg.create_task(fetch_order(3))
#
#     print(task1.result())
#     print(task2.result())
#     print(task3.result())
#
#
# asyncio.run(main())
#
# 输出：
#
# order - 1
# order - 2
# order - 3
#
# TaskGroup
# 的含义是：
#
# 这一组任务属于同一个作用域。离开这个作用域时，所有任务都必须已经结束。
#
# 如果某个子任务发生未处理的普通异常，TaskGroup
# 会取消其他尚未完成的子任务，并等待它们完成取消清理，然后将异常汇总传播。
#
# 4.
# gather
# 和
# TaskGroup
# 怎么选？
#
# 场景
#
# 推荐
#
# 简单并发收集多个结果
#
# gather
#
# 多个任务属于同一个业务操作
#
# TaskGroup
#
# 希望一个子任务失败时，其他任务得到取消并统一收尾
#
# TaskGroup
#
# 希望每个任务独立成功或失败，并收集各自结果
#
# gather(return_exceptions=True)
# 或任务内部处理异常
#
# 工程建议：新代码中，具有明确生命周期的一组并发任务，优先考虑
# TaskGroup。
#
# 七、超时与取消：异步程序不能缺少的生产能力
# 1.
# asyncio.timeout()
# import asyncio
#
#
# async def slow_api() -> str:
#     await asyncio.sleep(3)
#     return "完成"
#
#
# async def main() -> None:
#     try:
#         async with asyncio.timeout(1):
#             result = await slow_api()
#             print(result)
#     except TimeoutError:
#         print("请求超时")
#
#
# asyncio.run(main())
#
# 输出：
#
# 请求超时
#
# asyncio.timeout()
# 是
# Python
# 3.11 + 的现代写法，适合给一段异步操作设置时间限制。
#
# 2.
# asyncio.wait_for()
# result = await asyncio.wait_for(slow_api(), timeout=1)
#
# 同样可以设置超时。你需要认识它，但新代码中可以优先使用
# asyncio.timeout()
# 来表达一个超时作用域。
#
# 3.
# 取消任务
# import asyncio
#
#
# async def worker() -> None:
#     try:
#         print("任务开始")
#         await asyncio.sleep(10)
#         print("任务正常完成")
#     except asyncio.CancelledError:
#         print("收到取消请求")
#         raise
#     finally:
#         print("释放资源")
#
#
# async def main() -> None:
#     task = asyncio.create_task(worker())
#
#     await asyncio.sleep(0.1)
#     task.cancel()
#
#     try:
#         await task
#     except asyncio.CancelledError:
#         print("主协程确认任务已取消")
#
#
# asyncio.run(main())
#
# 输出：
#
# 任务开始
# 收到取消请求
# 释放资源
# 主协程确认任务已取消
#
# 这里有两个关键点：
#
# 第一，取消不是强制杀死线程。 task.cancel()
# 是向任务发出取消请求，通常会在协程下一个可取消的等待点抛出
# CancelledError。
#
# 第二，收到取消后通常要重新抛出。
#
# except asyncio.CancelledError:
# # 清理资源
# raise
#
# 不要随意吞掉取消异常，否则
# TaskGroup、超时机制等结构化并发能力可能无法按预期工作。
#
# 4. finally 是资源清理的核心
#
#
# async def process() -> None:
#     resource = await acquire_resource()
#     try:
#         await do_work(resource)
#     finally:
#         await release_resource(resource)
#
#
# 真实项目还可以使用异步上下文管理器
# async with 管理连接、会话等资源。取消可能发生在任意等待点，所以资源清理必须提前设计。
#
# 5.
# shield
# 了解即可
#
# asyncio.shield()
# 可以防止被包裹的等待任务因为外部等待者的取消而直接被取消，但它并不是“任务永远不能取消”，也不会让外层取消消失。
#
# 今天只需要知道它用于特殊的取消隔离场景，不要把它当成常规超时或取消处理方案。
#
# 八、并发控制：Semaphore
# 必须掌握
#
# 假设你有
# 1000
# 个订单要拉取：
#
# await asyncio.gather(*(fetch_order(i) for i in range(1000)))
#
# 这会创建大量任务，但你通常不希望同时向下游发出
# 1000
# 个请求。
#
# 原因包括：
#
# HTTP
# 连接数限制
#
# 下游
# API
# 限流
#
# 数据库连接池容量
#
# 内存与资源占用
#
# 下游服务承载能力
#
# 使用信号量限制并发
# import asyncio
#
#
# async def fetch_order(order_id: int) -> str:
#     print(f"开始请求 {order_id}")
#     await asyncio.sleep(1)
#     print(f"完成请求 {order_id}")
#     return f"order-{order_id}"
#
#
# async def main() -> None:
#     semaphore = asyncio.Semaphore(2)
#
#     async def limited_fetch(order_id: int) -> str:
#         async with semaphore:
#             return await fetch_order(order_id)
#
#     results = await asyncio.gather(
#         *(limited_fetch(i) for i in range(1, 6))
#     )
#
#     print(results)
#
#
# asyncio.run(main())
#
# 输出示意：
#
# 开始请求
# 1
# 开始请求
# 2
# 完成请求
# 1
# 完成请求
# 2
# 开始请求
# 3
# 开始请求
# 4
# 完成请求
# 3
# 完成请求
# 4
# 开始请求
# 5
# 完成请求
# 5
# ['order-1', 'order-2', 'order-3', 'order-4', 'order-5']
#
# 重点：信号量限制的是进入某段代码的并发数量，不是限制总任务数量。
#
# 如果创建一百万个
# Task，再用信号量限制为
# 10，仍然可能占用大量内存。超大规模任务应该进一步使用有界队列 + 固定数量
# Worker。
#
# 九、Lock、Event、Queue：协程之间如何协作？
# 1.
# asyncio.Lock
#
# 用于保护多个协程共享的状态。
#
# import asyncio
#
#
# async def main() -> None:
#     lock = asyncio.Lock()
#     counter = 0
#
#     async def increment() -> None:
#         nonlocal counter
#
#         async with lock:
#             old = counter
#             await asyncio.sleep(0)
#             counter = old + 1
#
#     await asyncio.gather(*(increment() for _ in range(100)))
#
#     print(counter)
#
#
# asyncio.run(main())
#
# 输出：
#
# 100
#
# 虽然
# asyncio
# 常常只在一个线程运行，但这不代表共享状态永远安全。只要读—改—写之间存在可能让出执行权的操作，就可能出现协程级竞态条件。
#
# 2.
# asyncio.Event
#
# 适合一个协程通知其他协程：“某个条件已经满足。”
#
# import asyncio
#
#
# async def main() -> None:
#     event = asyncio.Event()
#
#     async def worker() -> None:
#         print("等待配置加载")
#         await event.wait()
#         print("开始工作")
#
#     async def loader() -> None:
#         await asyncio.sleep(1)
#         print("配置加载完成")
#         event.set()
#
#     await asyncio.gather(worker(), loader())
#
#
# asyncio.run(main())
#
# 输出：
#
# 等待配置加载
# 配置加载完成
# 开始工作
# 3.
# asyncio.Queue
#
# 适合生产者消费者模型。
#
# import asyncio
#
#
# async def main() -> None:
#     queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=3)
#
#     async def producer() -> None:
#         for order_id in range(1, 6):
#             await queue.put(order_id)
#             print(f"生产订单 {order_id}")
#
#         await queue.put(None)
#
#     async def consumer() -> None:
#         while True:
#             order_id = await queue.get()
#             try:
#                 if order_id is None:
#                     break
#
#                 print(f"处理订单 {order_id}")
#                 await asyncio.sleep(0.2)
#             finally:
#                 queue.task_done()
#
#     await asyncio.gather(producer(), consumer())
#     await queue.join()
#
#
# asyncio.run(main())
#
# 输出示意：
#
# 生产订单
# 1
# 生产订单
# 2
# 生产订单
# 3
# 处理订单
# 1
# 生产订单
# 4
# 处理订单
# 2
# 生产订单
# 5
# 处理订单
# 3
# 处理订单
# 4
# 处理订单
# 5
#
# 这里最重要的是：
#
# maxsize
# 提供背压，队列满了生产者就需要等待。
#
# task_done()
# 表示一个队列项已经处理完。
#
# queue.join()
# 等待所有入队项都被标记完成。
#
# None
# 在这个例子里是结束哨兵，不是
# asyncio
# 内置的特殊值。
#
# Condition
# 也是
# asyncio
# 的同步原语，适合“持有锁并等待某个状态条件”的场景，今天知道用途即可。
#
# 十、异步代码最常见的坑：阻塞事件循环
# 错误示例
# import asyncio
# import time
#
#
# async def bad_work() -> None:
#     time.sleep(2)  # 阻塞整个事件循环
#
#
# async def 不会把内部代码自动变成非阻塞代码。
#
#
# 如果你在协程里直接调用：
#
# requests.get(...)
# time.sleep(...)
# 同步数据库查询(...)
#
# 这些同步操作仍然可能阻塞事件循环。
#
# 正确方式一：使用异步
# API
# await asyncio.sleep(2)
#
# 真实
# HTTP
# 项目可以使用支持
# asyncio
# 的
# HTTP
# 客户端，例如
# aiohttp
# 或
# httpx.AsyncClient。数据库也需要使用相应的异步驱动，不能只给同步函数外面加一个 async。
#
# 正确方式二：asyncio.to_thread()
#
# 当你必须调用同步阻塞函数时，可以把它放进线程执行。
#
# import asyncio
# import time
#
#
# def blocking_io(order_id: int) -> str:
#     time.sleep(2)
#     return f"order-{order_id}"
#
#
# async def main() -> None:
#     results = await asyncio.gather(
#         asyncio.to_thread(blocking_io, 1),
#         asyncio.to_thread(blocking_io, 2),
#         asyncio.to_thread(blocking_io, 3),
#     )
#     print(results)
#
#
# asyncio.run(main())
#
# 输出：
#
# ['order-1', 'order-2', 'order-3']
#
# 这就是第
# 12
# 天和第
# 13
# 天的连接点：
#
# asyncio
# 负责组织异步任务；线程可以帮助它兼容现有的阻塞同步代码。
#
# 但
# to_thread
# 不是
# CPU
# 密集计算的通用加速器。标准
# CPython
# 构建中的
# GIL
# 仍然会影响纯
# Python
# CPU
# 代码的多线程并行能力；CPU
# 密集任务应另外评估进程池、原生扩展或适合的并行方案。
#
# 十一、完整实战：异步订单处理管道
#
# 现在把今天的知识组合起来，模拟一个真实后端场景：
#
# 并发拉取订单 → 限制
# HTTP
# 并发 → 每个请求独立超时 → 清洗 → 存储 → 汇总成功失败。
#
# 下面只使用标准库，可以直接运行，不依赖真实网络服务。
#
# import asyncio
# import time
# from dataclasses import dataclass
#
#
# @dataclass
# class Order:
#     order_id: int
#     amount: float
#
#
# async def fetch_order(order_id: int) -> Order:
#     """模拟异步 HTTP 请求。"""
#     await asyncio.sleep(0.3)
#
#     if order_id == 4:
#         raise ValueError("上游返回非法订单")
#
#     return Order(order_id=order_id, amount=order_id * 10.0)
#
#
# async def clean_order(order: Order) -> Order:
#     """模拟轻量数据清洗。"""
#     await asyncio.sleep(0.05)
#     order.amount = round(order.amount, 2)
#     return order
#
#
# async def save_order(order: Order) -> None:
#     """模拟异步数据库写入。"""
#     await asyncio.sleep(0.1)
#
#
# async def process_order(
#         order_id: int,
#         semaphore: asyncio.Semaphore,
# ) -> tuple[int, str]:
#     try:
#         # 只限制 HTTP 请求的并发，而不是整个处理管道。
#         async with semaphore:
#             async with asyncio.timeout(1.0):
#                 order = await fetch_order(order_id)
#
#         order = await clean_order(order)
#         await save_order(order)
#
#         return order_id, "success"
#
#     except TimeoutError:
#         return order_id, "timeout"
#
#     except ValueError as exc:
#         return order_id, f"failed: {exc}"
#
#
# async def main() -> None:
#     start = time.perf_counter()
#     semaphore = asyncio.Semaphore(3)
#
#     async with asyncio.TaskGroup() as tg:
#         tasks = [
#             tg.create_task(process_order(order_id, semaphore))
#             for order_id in range(1, 11)
#         ]
#
#     results = [task.result() for task in tasks]
#
#     success_count = sum(
#         1 for _, status in results if status == "success"
#     )
#     failed_count = len(results) - success_count
#
#     print(f"成功：{success_count}，失败：{failed_count}")
#     for order_id, status in results:
#         print(f"订单 {order_id}: {status}")
#
#     print(f"总耗时约 {time.perf_counter() - start:.1f} 秒")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
#
# 输出示意：
#
# 成功：9，失败：1
# 订单
# 1: success
# 订单
# 2: success
# 订单
# 3: success
# 订单
# 4: failed: 上游返回非法订单
# 订单
# 5: success
# 订单
# 6: success
# 订单
# 7: success
# 订单
# 8: success
# 订单
# 9: success
# 订单
# 10: success
# 总耗时约
# 1.4
# 秒
#
# 这个实战体现了几个工程设计点：
#
# 并发边界： Semaphore(3)
# 只限制拉取阶段，清洗和存储可以继续推进。
#
# 失败隔离： 每个订单在
# process_order
# 内处理预期异常，因此订单
# 4
# 失败不会导致其他订单全部取消。
#
# 任务生命周期： TaskGroup
# 保证离开作用域时所有订单任务已经结束。
#
# 超时范围： 当前超时只包裹
# HTTP
# 拉取。如果希望整个“拉取—清洗—存储”都受一个总超时约束，应把
# asyncio.timeout()
# 放到整个管道外层。
#
# 真实项目注意： 清洗如果是长时间纯
# CPU
# 计算，不应该因为写成
#
#
# async def 就认为它不会阻塞；
#
#
#     应根据计算量选择同步直接执行、线程或进程等方案。
#
# 十二、底层原理补充：Future
# 与事件循环如何配合？
#
# 这一部分是理解机制，不要求今天手写底层实现。
#
# 1.
# Future
# 是什么？
#
# Future
# 表示一个未来才会有结果的对象，可以处于未完成、完成、异常或取消等状态。
#
# Task
# 与
# Future
# 的关系可以简化理解为：
#
# Future：表示未来的结果
# Task：管理一个协程的执行，本身也是
# Future
# 的一种
#
# 当协程等待某个
# I / O
# 操作时，底层机制可以把“等待完成后恢复任务”与
# Future
# 关联起来。
#
# 2.
# asyncio.sleep()
# 为什么不阻塞？
#
# 简化过程：
#
# 协程执行
# await asyncio.sleep(2)
# ↓
# 注册一个约
# 2
# 秒后的定时器
# ↓
# 当前
# Task
# 暂停
# ↓
# 事件循环运行其他就绪
# Task
# ↓
# 定时器到期
# ↓
# 原
# Task
# 恢复执行
#
# 真正的网络
# I / O
# 也是类似思想：事件循环通过操作系统提供的
# I / O
# 就绪机制，等待网络等事件，而不是让
# Python
# 代码不断空转检查。
#
# 3.
# 不需要今天掌握什么？
#
# 不需要手写事件循环、不需要手动创建
# Future、不需要研究
# selector
# 的底层实现，也不需要先学完所有
# asyncio
# API
# 才能进入
# Agent
# 开发。


# 十三、今天必须记住的 10 个结论
#
# 协程函数调用后得到协程对象，不会因为调用就自动执行。
#
# await 是等待可等待对象，不等于创建并发。
#
# 连续 await 通常是顺序执行；先创建多个 Task 才能组织并发。
#
# asyncio 的优势主要来自 I/O 等待重叠，不是自动实现多核 CPU 并行。
#
# async def 内部调用阻塞函数，仍然可能阻塞事件循环。
#
# TaskGroup 适合具有共同生命周期的一组任务。
#
# 超时和取消必须考虑资源清理，通常不要吞掉 CancelledError。
#
# Semaphore 控制资源并发，Queue(maxsize=...) 可以提供背压。
#
# Lock 用于共享状态，Event 用于通知，Queue 用于生产者消费者。
#
# to_thread 是异步系统兼容同步阻塞代码的重要桥梁。