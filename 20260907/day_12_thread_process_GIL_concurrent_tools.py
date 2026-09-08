# Day12：线程、进程、GIL
# 与并发工具
#
# 今日目标： 能根据任务类型选择线程或进程，正确使用线程池、进程池、Future
# 和锁，并理解为什么
# Python
# 的并发不能直接照搬
# Java。
#
# 建议学习时间： 3–4
# 小时。今天内容较多，可以分两次完成，但知识点是一整天的完整课程。
#
# 一、今天的知识地图
#
# 模块
#
# 重点程度
#
# 学完应该掌握
#
# 并发、并行、I / O
# 密集与
# CPU
# 密集
#
#
#
# ★★★★★
#
#
#
# 能判断业务应该使用什么模型
#
# CPython
# 的
# GIL
#
#
#
# ★★★★★
#
#
#
# 理解线程为什么不一定能加速
# CPU
# 计算
#
# threading
# 基础
#
#
#
# ★★★★☆
#
#
#
# 创建线程、启动、等待、理解共享内存
#
# ThreadPoolExecutor
#
#
#
# ★★★★★
#
#
#
# 使用线程池处理批量
# I / O
# 任务
#
# Future
# 与
# as_completed
#
#
#
# ★★★★★
#
#
#
# 获取结果、处理异常、按完成顺序消费
#
# 共享状态与
# Lock
#
#
#
# ★★★★★
#
#
#
# 理解竞态条件，正确保护临界区
#
# RLock、threading.local、Event
#
#
#
# ★★★★☆
#
#
#
# 掌握常见线程协调工具
#
# ProcessPoolExecutor
#
#
#
# ★★★★★
#
#
#
# 使用多进程处理
# CPU
# 密集任务
#
# 进程通信、序列化与启动方式
#
#
#
# ★★★★☆
#
#
#
# 避免
# Windows
# 和跨进程数据传递陷阱
#
# 超时、取消、资源控制与工程实践
#
#
#
# ★★★★★
#
#
#
# 写出可靠的批处理并发代码
#
# 综合案例与作业
#
#
#
# ★★★★★
#
#
#
# 将并发能力应用到订单处理
#
# 二、先建立一个正确的并发模型
# 1.
# 并发和并行不是一回事
#
# 假设你有
# 100
# 个
# Shopify
# 站点，每个站点都要请求接口同步订单。
#
# 串行执行：
#
# 请求站点
# A ───── 等待 ───── 完成
# 请求站点
# B ───── 等待 ───── 完成
#
# 并发执行：
#
# 请求站点
# A ───── 等待 ───── 完成
# 请求站点
# B ───── 等待 ───── 完成
# 请求站点
# C ───── 等待 ───── 完成
#
# 多个任务在同一段时间内推进，叫并发。多个任务真正同时占用不同
# CPU
# 核心执行，叫并行。
#
# 对于
# HTTP
# 请求，程序的大部分时间可能是在等网络，而不是计算。因此，即使没有多个
# Python
# 线程同时执行
# Python
# 字节码，也可以通过并发显著减少总耗时。
#
# 2.
# 先判断任务类型，再选工具
#
# 业务任务
#
# 主要瓶颈
#
# 通常选择
#
# 请求
# Shopify
# API
#
# 网络等待
#
# 线程池或异步
#
# 批量查询远程数据库
#
# 网络等待
#
# 线程池或异步
#
# 下载文件
#
# 网络等待
#
# 线程池或异步
#
# 大量
# JSON / 文件读写
#
# 视具体瓶颈而定
#
# 先测量，I / O
# 多可用线程
#
# 纯
# Python
# 大量数学计算
#
# CPU
#
# 多进程
#
# 大量图像计算
#
# CPU，但可能由
# C
# 扩展释放
# GIL
#
# 测量后选择
#
# 订单金额计算
#
# 通常计算量很小
#
# 不必为了并发而并发
#
# 最重要的原则： 并发不是越多越快。先找到瓶颈，再选择模型。
#
# 三、GIL：Java
# 开发最需要纠正的认知
# 1.
# GIL
# 是什么？
#
# GIL（Global
# Interpreter
# Lock，全局解释器锁）是常规
# CPython
# 构建中的一种机制，它限制同一时刻执行
# Python
# 字节码的线程数量。
#
# 你可以把它理解为：
#
# 一个
# Python
# 进程
# ├── Thread1 ──┐
# ├── Thread2 ──┼── 竞争执行
# Python
# 字节码
# └── Thread3 ──┘
#
# 在常规
# CPython
# 中，一个进程内的多个线程通常不能同时在多个
# CPU
# 核心上执行纯
# Python
# 字节码。
#
# 但这不等于
# Python
# 线程没有用。线程遇到网络等待、文件
# I / O
# 或某些释放
# GIL
# 的
# C
# 扩展操作时，其他线程可以继续执行。
#
# 2.
# 为什么
# I / O
# 密集任务适合线程？
#
# 例如：
#
# import time
#
#
# def fetch_orders(site_id: int) -> str:
#     time.sleep(2)  # 模拟网络等待
#     return f"站点 {site_id} 同步完成"
#
#
# time.sleep()
# 期间线程不需要持续执行
# Python
# 字节码，其他线程可以工作。
#
# 如果串行处理
# 5
# 个站点，每个等待
# 2
# 秒，总耗时大约
# 10
# 秒；使用
# 5
# 个线程并发等待，理想情况下接近
# 2
# 秒，再加少量调度开销。
#
# 3.
# 为什么
# CPU
# 密集任务通常不适合普通线程？
#
# def calculate() -> int:
#     total = 0
#     for i in range(20_000_000):
#         total += i * i
#     return total
#
#
# 这段代码主要在执行
# Python
# 计算。常规
# CPython
# 的多个线程无法让这些纯
# Python
# 字节码在多个核心上真正并行。
#
# 因此：
#
# I / O
# 密集
# → 线程 / asyncio
#
# CPU
# 密集（纯
# Python）
# → 多进程
#
# CPU
# 密集（NumPy
# 等
# C
# 扩展）
# → 需要实际测试，不能一概而论
# 4.
# Python
# 3.14
# 需要知道的补充
#
# 你使用的是
# Python
# 3.14。Python
# 已经提供可选的
# free - threaded
# 构建，它可以禁用
# GIL，但这不代表所有
# Python
# 3.14
# 安装默认都没有
# GIL，也不代表所有第三方库都已经适配。
#
# 本课程先以常规
# CPython
# 为基准。这样你理解的模型仍然适用于大量现有生产环境。
#
# 四、threading：线程最基础的使用
#
# Java
# 中你熟悉：
#
# Thread
# thread = new
# Thread(() -> {
#              // 执行任务
# });
# thread.start();
# thread.join();
#
# Python
# 对应：
#
# import threading
# import time
#
#
# def sync_site(site_id: int) -> None:
#     print(f"开始同步站点：{site_id}")
#     time.sleep(1)
#     print(f"同步完成：{site_id}")
#
#
# threads: list[threading.Thread] = []
#
# for site_id in range(1, 4):
#     thread = threading.Thread(
#         target=sync_site,
#         args=(site_id,),
#         name=f"site-sync-{site_id}",
#     )
#     thread.start()
#     threads.append(thread)
#
# for thread in threads:
#     thread.join()
#
# print("所有站点同步完成")
# 关键解释
#
# target
# 是线程执行的函数，args
# 是传给函数的位置参数。(site_id,)
# 必须带逗号，因为这是单元素元组。
#
# start()
# 才是真正启动线程。join()
# 表示当前线程等待目标线程结束。
#
# 注意： 创建线程不等于立即执行完毕，线程之间的执行顺序也不能依赖。
#
# 不要这样写
# thread = threading.Thread(target=sync_site(1))
#
# 这里的
# sync_site(1)
# 会先在当前线程执行，然后把返回值交给
# target，并不是把函数交给新线程。
#
# 正确写法：
#
# thread = threading.Thread(target=sync_site, args=(1,))
# 五、为什么生产代码更推荐线程池？
#
# 手动创建线程适合理解机制，但批量业务通常使用：
#
# from concurrent.futures import ThreadPoolExecutor
#
# 它与
# Java
# 的
# ExecutorService
# 很接近。
#
# 1.
# 最基础的线程池
# from concurrent.futures import ThreadPoolExecutor
# import time
#
#
# def sync_site(site_id: int) -> str:
#     time.sleep(1)
#     return f"站点 {site_id} 同步完成"
#
#
# with ThreadPoolExecutor(max_workers=3) as executor:
#     results = executor.map(sync_site, [1, 2, 3, 4, 5])
#
#     for result in results:
#         print(result)
#
# max_workers = 3
# 表示最多同时有
# 3
# 个工作线程执行任务。
#
# with 退出时会关闭线程池，并等待已提交的任务完成。
#
# 2.
# map()
# 的特点
# executor.map(function, iterable)
#
# 它类似
# Java
# 的批量任务映射，返回一个可迭代结果。
#
# 重要：map()
# 按输入顺序返回结果，不是按完成顺序。
#
# 例如：
#
# 任务1：耗时
# 3
# 秒
# 任务2：耗时
# 1
# 秒
# 任务3：耗时
# 1
# 秒
#
# 即使任务2、任务3先完成，遍历
# map()
# 时仍可能先等待任务1。
#
# 如果你希望谁先完成就先处理谁，就需要
# as_completed()。
#
# 六、Future：理解线程池的核心
#
# Java：
#
# Future < String > future = executor.submit(task);
# String
# result = future.get();
#
# Python：
#
# from concurrent.futures import ThreadPoolExecutor, Future
#
#
# def calculate(value: int) -> int:
#     return value * 2
#
#
# with ThreadPoolExecutor(max_workers=2) as executor:
#     future: Future[int] = executor.submit(calculate, 10)
#
#     result = future.result()
#     print(result)  # 20
#
# submit()
# 立即返回一个
# Future，它代表“一个尚未必然完成的任务结果”。
#
# Future
# 的生命周期
# 提交任务
# ↓
# PENDING（等待执行）
# ↓
# RUNNING（执行中）
# ↓
# FINISHED（完成）
# ├── 成功 → result()
# └── 异常 → result()
# 重新抛出异常
#
# 常用方法：
#
# 方法
#
# 作用
#
# result()
#
# 等待任务完成并获取结果
#
# result(timeout=...)
#
# 最多等待指定时间
#
# done()
#
# 是否已经完成
#
# running()
#
# 是否正在运行
#
# cancel()
#
# 尝试取消尚未开始的任务
#
# cancelled()
#
# 是否已取消
#
# exception()
#
# 获取任务异常
#
# 一个非常重要的坑
# with ThreadPoolExecutor(max_workers=3) as executor:
#     for site_id in range(1, 6):
#         future = executor.submit(sync_site, site_id)
#         print(future.result())
#
# 虽然使用了线程池，但每提交一个任务就立刻等待，实际效果接近串行。
#
# 正确思路是先提交，再集中获取结果。
#
# 七、as_completed()：按完成顺序处理
#
# 这是你以后做多站点同步、批量请求、并发爬虫时非常常用的模式。
#
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import time
#
#
# def sync_site(site_id: int) -> str:
#     # 模拟不同站点接口耗时
#     time.sleep(4 - site_id)
#     return f"站点 {site_id} 同步成功"
#
#
# with ThreadPoolExecutor(max_workers=3) as executor:
#     futures = {
#         executor.submit(sync_site, site_id): site_id
#         for site_id in range(1, 4)
#     }
#
#     for future in as_completed(futures):
#         site_id = futures[future]
#
#         try:
#             result = future.result()
#             print(result)
#         except Exception as exc:
#             print(f"站点 {site_id} 同步失败：{exc}")
# 为什么要用字典？
# futures = {
#     future: site_id
# }
#
# 因为任务完成后，你需要知道这个
# Future
# 对应哪个站点。
#
# Java
# 中你可能会使用任务包装对象、CompletableFuture
# 或携带业务
# ID
# 的结果对象。Python
# 用字典建立映射非常自然。
#
# as_completed()
# 与
# map()
# 的区别
#
# 对比
#
# map()
#
# as_completed()
#
# 返回顺序
#
# 输入顺序
#
# 完成顺序
#
# 是否方便关联业务
# ID
#
# 一般
#
# 很方便
#
# 单任务异常处理
#
# 不够灵活
#
# 很方便
#
# 适合场景
#
# 简单批量映射
#
# 复杂业务并发
#
# 八、异常不会自动在主线程抛出
#
# 看下面的代码：
#
# def dangerous_task() -> None:
#     raise ValueError("订单数据错误")
#
#
# 提交到线程池：
#
# future = executor.submit(dangerous_task)
#
# 异常会被保存到
# Future
# 中。通常在调用：
#
# future.result()
#
# 时重新抛出。
#
# 因此生产代码不能只提交任务就不管：
#
# executor.submit(dangerous_task)
#
# 否则你可能根本没有正确处理任务失败。
#
# 推荐模式：
#
# for future in as_completed(futures):
#     try:
#         result = future.result()
#     except Exception:
#         logger.exception("任务执行失败")
#
# 这与你在
# Java
# 中处理
# Future.get()
# 的异常很相似。
#
# 九、线程共享内存：为什么需要锁？
#
# Python
# 同一进程内的线程共享对象。
#
# counter = 0
#
# 多个线程都可以访问它。
#
# 假设两个线程执行：
#
# counter += 1
#
# 从逻辑上可以拆解为：
#
# 读取
# counter
# 计算
# counter + 1
# 写回
# counter
#
# 如果两个线程交错执行，可能发生丢失更新。
#
# 不要认为有
# GIL
# 就不需要锁。 GIL
# 不是你的业务数据一致性锁，也不应该依赖某个
# CPython
# 版本中某条语句“碰巧是原子的”。
#
# 十、Lock：保护临界区
#
# Java：
#
# synchronized(lock)
# {
#     counter + +;
# }
#
# Python：
#
# import threading
# from concurrent.futures import ThreadPoolExecutor
#
# counter = 0
# lock = threading.Lock()
#
#
# def increment() -> None:
#     global counter
#
#     for _ in range(10_000):
#         with lock:
#             counter += 1
#
#
# with ThreadPoolExecutor(max_workers=5) as executor:
#     futures = [executor.submit(increment) for _ in range(5)]
#
#     for future in futures:
#         future.result()
#
# print(counter)
#
# 这里的
# with lock 相当于：
#
# lock.acquire()
#
# try:
#     counter += 1
# finally:
#     lock.release()
# 锁保护的是什么？
#
# 不是“保护一个函数”，而是保护共享状态的一段读—改—写操作。
#
# 例如库存扣减：
#
# 读取库存
# ↓
# 判断库存是否足够
# ↓
# 扣减库存
#
# 如果多个线程共享同一个内存库存对象，这整个操作需要作为一个临界区考虑。
#
# 但注意：Python
# 的
# Lock
# 只能协调同一进程内的线程。 它不能替代数据库事务、Redis
# 分布式锁，也不能保护多个服务实例之间的库存一致性。
#
# 十一、RLock：可重入锁
#
# Java
# 的
# ReentrantLock
# 你应该很熟悉。
#
# Python：
#
# import threading
#
# lock = threading.RLock()
#
#
# def outer() -> None:
#     with lock:
#         inner()
#
#
# def inner() -> None:
#     with lock:
#         print("执行内部逻辑")
#
#
# outer()
#
# 同一个线程可以重复获取
# RLock。
#
# 如果这里使用普通
# Lock：
#
# lock = threading.Lock()
#
# outer()
# 已经持有锁，再调用
# inner()
# 获取同一把锁，就可能发生死锁。
#
# 什么时候用？
#
# 当受锁保护的方法之间存在嵌套调用，并且确实需要同一线程重复获取同一把锁时。
#
# 不要因为
# RLock
# 更“高级”就全部使用它。普通
# Lock
# 的语义更简单。
#
# 十二、threading.local()：线程局部变量
#
# Java
# 对应：
#
# ThreadLocal < T >
#
# Python：
#
# import threading
# from concurrent.futures import ThreadPoolExecutor
#
# thread_context = threading.local()
#
#
# def process_order(order_id: int) -> None:
#     thread_context.order_id = order_id
#
#     print(
#         threading.current_thread().name,
#         thread_context.order_id,
#     )
#
#
# with ThreadPoolExecutor(max_workers=2) as executor:
#     list(executor.map(process_order, [101, 102, 103]))
#
# 不同线程拥有各自的
# thread_context.order_id。
#
# 业务场景
#
# 例如：
#
# 线程1 → trace_id = A
# 线程2 → trace_id = B
#
# 日志打印时可以读取当前线程的
# trace_id。
#
# 但要注意线程池会复用线程，所以业务上下文需要正确设置和清理，不能假设一个线程只处理一个请求。
#
# 十三、Event：线程之间的信号
#
# Event
# 可以理解为一个线程间的“开关”。
#
# import threading
# import time
#
# stop_event = threading.Event()
#
#
# def worker() -> None:
#     while not stop_event.is_set():
#         print("正在处理任务")
#         time.sleep(0.5)
#
#     print("收到停止信号，退出")
#
#
# thread = threading.Thread(target=worker)
# thread.start()
#
# time.sleep(2)
# stop_event.set()
#
# thread.join()
#
# 常用方法：
#
# event.set()  # 设置为真
# event.clear()  # 清除
# event.is_set()  # 是否已设置
# event.wait()  # 等待信号
# 工程意义
#
# 当你需要让一个后台工作线程优雅停止时，Event
# 比随意修改全局布尔变量更明确。
#
# 十四、进程：为什么能利用多个
# CPU
# 核心？
#
# 线程：
#
# Python
# 进程
# ├── Thread1
# ├── Thread2
# └── Thread3
#
# 多进程：
#
# Process1 → Python
# 解释器 → CPU核心1
# Process2 → Python
# 解释器 → CPU核心2
# Process3 → Python
# 解释器 → CPU核心3
#
# 每个进程有自己的解释器和内存空间。在常规
# CPython
# 中，多进程可以绕开单进程
# GIL
# 对纯
# Python
# CPU
# 并行的限制。
#
# 但代价是：
#
# 创建进程更重；
#
# 进程之间不直接共享普通
# Python
# 对象；
#
# 传递数据通常需要序列化；
#
# 大数据传输可能产生明显开销。
#
# 十五、ProcessPoolExecutor：进程池
#
# 与线程池的
# API
# 非常相似：
#
# from concurrent.futures import ProcessPoolExecutor
#
# 完整可运行示例
#
# 建议保存为
# process_demo.py：
#
# from concurrent.futures import ProcessPoolExecutor
#
#
# def calculate_sum(limit: int) -> int:
#     """模拟 CPU 密集计算。"""
#     total = 0
#
#     for i in range(limit):
#         total += i * i
#
#     return total
#
#
# def main() -> None:
#     limits = [
#         5_000_000,
#         5_000_000,
#         5_000_000,
#         5_000_000,
#     ]
#
#     with ProcessPoolExecutor(max_workers=4) as executor:
#         results = executor.map(calculate_sum, limits)
#
#         for result in results:
#             print(result)
#
#
# if __name__ == "__main__":
#     main()
# 为什么必须注意 if __name__ == "__main__"？
#
# 特别是
# Windows
# 环境，子进程启动时会重新导入主模块。
#
# 如果你把创建进程池的代码直接放在模块顶层，可能导致子进程导入时再次创建进程池，引发递归启动问题。
#
# 所以要形成习惯：
#
# def main() -> None:
#     ...
#
#
# if __name__ == "__main__":
#     main()
#
# 这也是你之前学习
# __main__
# 的一个重要实际用途。
#
# 十六、进程之间不能直接共享普通对象
#
# 例如：
#
# counter = 0
#
# 在多进程中，每个进程通常有自己的地址空间。子进程修改自己的
# counter，不会自动修改主进程的
# counter。
#
# 这与线程共享内存有本质区别。
#
# 进程通信的常见方式
#
# 方式
#
# 用途
#
# ProcessPoolExecutor
# 返回值
#
# 最简单的结果传递
#
# multiprocessing.Queue
#
# 进程间消息传递
#
# multiprocessing.Pipe
#
# 两端通信
#
# multiprocessing.Value / Array
#
# 共享简单数据
#
# multiprocessing.shared_memory
#
# 共享内存
#
# 数据库、Redis、消息队列
#
# 跨进程甚至跨机器协作
#
# 对于普通业务开发，优先使用任务输入 + 返回值，不要一开始就设计复杂共享内存。
#
# 十七、进程池的序列化限制
#
# 线程池可以直接访问同一进程中的对象，而进程池需要把任务及参数传给其他进程。
#
# 因此通常需要对象能够被
# pickle
# 序列化。
#
# 推荐：
#
# def calculate(value: int) -> int:
#     return value * value
#
#
# 避免依赖：
#
# lambda x: x * x
#
# 或者定义在函数内部的局部函数，作为进程池任务。
#
# 例如：
#
# def main() -> None:
#     def calculate(value: int) -> int:
#         return value * value
#
#
# 这种局部函数通常不能作为标准进程池的可序列化任务使用。
#
# 工程习惯：进程池任务函数放在模块顶层。
#
# 十八、线程池与进程池的完整对比
#
# 维度
#
# ThreadPoolExecutor
#
# ProcessPoolExecutor
#
# 主要用途
#
# I / O
# 密集
#
# CPU
# 密集
#
# 内存
#
# 同进程共享
#
# 进程独立
#
# 创建成本
#
# 较低
#
# 较高
#
# 数据传递
#
# 直接引用对象
#
# 通常需要序列化
#
# GIL
# 影响
#
# 常规
# CPython
# 纯
# Python
# CPU
# 计算受限
#
# 可利用多核
#
# 适合订单
# API
# 同步
#
# 很适合
#
# 通常没必要
#
# 适合大量纯
# Python
# 计算
#
# 通常不理想
#
# 更适合
#
# 共享状态风险
#
# 竞态条件
#
# 进程通信与一致性问题
#
# 十九、超时：不要以为
# Future.result(timeout=...)
# 能杀死任务
# future.result(timeout=3)
#
# 含义是：
#
# 当前线程最多等待
# 3
# 秒获取结果。
#
# 不是：
#
# 任务执行超过
# 3
# 秒就会被强制终止。
#
# 例如：
#
# from concurrent.futures import ThreadPoolExecutor, TimeoutError
# import time
#
#
# def slow_task() -> str:
#     time.sleep(10)
#     return "完成"
#
#
# with ThreadPoolExecutor(max_workers=1) as executor:
#     future = executor.submit(slow_task)
#
#     try:
#         print(future.result(timeout=1))
#     except TimeoutError:
#         print("等待超时")
#
# 这里打印“等待超时”后，任务可能仍在继续执行。
#
# 而且
# with 退出时默认会等待已提交任务完成，因此整个程序不一定立即结束。
#
# 真正的网络超时应该在哪里设置？
#
# 在
# HTTP
# 客户端本身：
#
# # 例如 requests
# response = requests.get(
#     "https://example.com",
#     timeout=(3, 10),
# )
#
# 其中连接超时和读取超时由
# HTTP
# 客户端控制。
#
# Future
# 超时 ≠ 网络请求超时 ≠ 任务强制终止。
#
# 二十、取消任务也不是强制中断
# future.cancel()
#
# 只能尝试取消尚未开始执行的任务。
#
# 如果任务已经运行：
#
# future.cancel()
#
# 通常不能直接把正在运行的
# Python
# 线程杀掉。
#
# 因此需要设计：
#
# 提交任务
# ↓
# 任务检查停止信号
# ↓
# 收到停止请求
# ↓
# 完成必要清理
# ↓
# 主动退出
#
# 这也是前面
# threading.Event
# 的实际价值。
#
# 二十一、线程池大小不是越大越好
#
# 例如你有
# 1000
# 个站点：
#
# ThreadPoolExecutor(max_workers=1000)
#
# 不一定合理。
#
# 可能出现：
#
# 对方
# API
# 限流；
#
# 本地连接数过多；
#
# 内存消耗增加；
#
# 数据库连接池耗尽；
#
# 请求超时增加；
#
# 下游服务被打满。
#
# 正确的思考方式
# 业务并发量
# ↓
# HTTP连接池
# ↓
# 对方API限流
# ↓
# 数据库连接池
# ↓
# 本机CPU / 内存
# ↓
# 综合确定
# max_workers
#
# 例如：
#
# with ThreadPoolExecutor(max_workers=8) as executor:
#     ...
#
# 这里的
# 8
# 只是示例值，不是通用最优值。
#
# 对于
# Shopify、TikTok
# Shop
# 这类接口，还要考虑每个店铺、每个应用或每个接口的限流规则，不能只靠线程池控制所有问题。
#
# 二十二、综合实战：多站点订单同步
#
# 现在把今天的核心知识组合起来。
#
# 业务要求
#
# 模拟同步多个站点订单：
#
# 最多同时执行
# 3
# 个站点；
#
# 每个站点可能成功或失败；
#
# 谁先完成就先处理谁；
#
# 单个站点失败不影响其他站点；
#
# 最后统计成功和失败数量；
#
# 不在工作线程里直接修改共享统计变量。
#
# 完整源码
# from __future__ import annotations
#
# import logging
# import time
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from dataclasses import dataclass
#
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(threadName)s] %(message)s",
# )
#
# logger = logging.getLogger(__name__)
#
#
# @dataclass(frozen=True)
# class SyncResult:
#     site_id: int
#     order_count: int
#
#
# def sync_site(site_id: int) -> SyncResult:
#     """
#     模拟同步某个站点的订单。
#
#     实际业务中，这里可以替换为：
#     1. 调用 Shopify/TikTok Shop API；
#     2. 解析订单；
#     3. 清洗数据；
#     4. 返回同步结果。
#     """
#     logger.info("开始同步站点 %s", site_id)
#
#     # 模拟网络等待
#     time.sleep(0.5 + site_id * 0.1)
#
#     # 模拟某个站点接口失败
#     if site_id == 3:
#         raise RuntimeError("模拟 API 限流")
#
#     result = SyncResult(
#         site_id=site_id,
#         order_count=site_id * 10,
#     )
#
#     logger.info("站点 %s 同步完成", site_id)
#     return result
#
#
# def main() -> None:
#     site_ids = [1, 2, 3, 4, 5]
#
#     success_results: list[SyncResult] = []
#     failed_sites: dict[int, str] = {}
#
#     with ThreadPoolExecutor(
#             max_workers=3,
#             thread_name_prefix="order-sync",
#     ) as executor:
#
#         # 先提交全部任务
#         future_to_site = {
#             executor.submit(sync_site, site_id): site_id
#             for site_id in site_ids
#         }
#
#         # 按完成顺序处理
#         for future in as_completed(future_to_site):
#             site_id = future_to_site[future]
#
#             try:
#                 result = future.result()
#             except Exception as exc:
#                 failed_sites[site_id] = str(exc)
#                 logger.error(
#                     "站点 %s 同步失败：%s",
#                     site_id,
#                     exc,
#                 )
#             else:
#                 success_results.append(result)
#
#     # 统计在主线程完成，不需要额外加锁
#     total_orders = sum(
#         result.order_count
#         for result in success_results
#     )
#
#     print("\n===== 同步结果 =====")
#     print(f"成功站点数：{len(success_results)}")
#     print(f"失败站点数：{len(failed_sites)}")
#     print(f"同步订单总数：{total_orders}")
#     print(f"失败站点：{failed_sites}")
#
#
# if __name__ == "__main__":
#     main()
# 为什么这个设计比“线程里直接改全局变量”更好？
#
# 因为工作线程只负责：
#
# 输入
# site_id
# ↓
# 执行同步
# ↓
# 返回
# SyncResult
#
# 主线程负责：
#
# 收集结果
# ↓
# 统计
# ↓
# 输出
#
# 这样共享状态更少，锁也更少，代码更容易测试。
#
# 这是一种非常值得养成的工程习惯：优先通过返回值传递结果，而不是让多个线程共同修改业务状态。
#
# 二十三、Java
# 与
# Python
# 并发对照
#
# Java
#
# Python
#
# 说明
#
# Thread
#
# threading.Thread
#
# 线程
#
# ExecutorService
#
# ThreadPoolExecutor
#
# 线程池
#
# Future.get()
#
# Future.result()
#
# 获取任务结果
#
# CompletableFuture
#
# Future + 回调 / asyncio
#
# 不完全等价
#
# synchronized
#
# Lock +
# with
#
# 临界区保护
#
# ReentrantLock
#
# RLock
#
# 可重入锁
#
# ThreadLocal
#
# threading.local()
#
# 线程局部变量
#
# CountDownLatch
#
# 可用
# Event、Barrier
# 等组合
#
# 没有完全相同的单一基础
# API
#
# Process / 多
# JVM
#
# multiprocessing
#
# 多进程
#
# ExecutorService
# 处理
# CPU
# 任务
#
# ProcessPoolExecutor
#
# 常规
# CPython
# 中常用多核方案
#
# 最大的思维差异： Java
# 中你可能习惯“CPU
# 密集 → 线程池”，但常规
# CPython
# 中，纯
# Python
# CPU
# 密集任务通常优先考虑进程池。
#
# 二十四、今天必须记住的
# 10
# 个结论
#
# I / O
# 密集优先线程或异步，纯
# Python
# CPU
# 密集通常优先进程。
#
# GIL
# 不等于线程无用，也不等于不需要锁。
#
# ThreadPoolExecutor
# 是批量
# I / O
# 并发的常用工具。
#
# submit()
# 返回
# Future，不是直接返回业务结果。
#
# map()
# 按输入顺序返回，as_completed()
# 按完成顺序处理。
#
# 不要每提交一个任务就立即
# result()，否则容易退化成串行。
#
# 线程异常需要通过
# Future.result()
# 等方式正确处理。
#
# Lock
# 保护共享内存临界区，不能替代跨服务分布式锁。
#
# 进程池任务函数尽量放模块顶层，并使用
# __main__
# 保护入口。
#
# Future
# 的超时和取消都不等于强制终止正在运行的任务。