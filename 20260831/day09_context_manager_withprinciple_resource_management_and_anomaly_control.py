# Day 9：上下文管理器、with 原理、资源管理与异常控制
#
# 今天的核心问题：
#
# 为什么 Python 打开文件时推荐：
#
# with path.open(...) as file:
#     ...
#
# 而不是：
#
# file = path.open(...)
# ...
# file.close()
#
# 因为 with 本质上是在做：
#
# 进入资源 → 使用资源 → 无论成功还是异常，都负责退出和清理。
#
# 这就是上下文管理器，Context Manager。


### 一、今天目标
#
# 今天掌握：
#
# with 到底做了什么
# __enter__
# __exit__
# with ... as ...
# 异常发生时 with 如何清理
# 自定义上下文管理器
# contextlib.contextmanager
# 多个上下文管理器
# 文件、锁、事务场景
# Java try-with-resources 类比


### 二、先从最熟悉的文件开始
#
# 你之前写过：
#
# from pathlib import Path
#
#
# path = Path("orders.txt")
#
# with path.open(
#     "r",
#     encoding="utf-8",
# ) as file:
#     content = file.read()
#
# 为什么不需要：
#
# file.close()
#
# 因为离开 with 代码块时，Python 会自动关闭文件。
#
# 即使中间报异常：
#
# with path.open(
#     "r",
#     encoding="utf-8",
# ) as file:
#     content = file.read()
#
#     raise ValueError("测试异常")
#
# 文件仍然会被关闭。


### 三、Java 类比
#
# Java：
#
# try (
#     BufferedReader reader =
#         Files.newBufferedReader(path)
# ) {
#     ...
# }
#
# Python：
#
# with path.open() as file:
#     ...
#
# 本质思想一样：
#
# 自动管理资源生命周期。
#
# Java 依赖：
#
# AutoCloseable
#
# Python 依赖：
#
# __enter__()
# __exit__()


# 四、with 背后的核心协议
#
# 一个对象只要实现：
#
# __enter__()
#
# 和：
#
# __exit__()
#
# 就可以用于：
#
# with ...
#
# 例如：
#
# class DemoContext:
#     def __enter__(self):
#         print("进入")
#
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         print("退出")
#
# 使用：
#
# with DemoContext():
#     print("执行代码")
#
# 输出：
#
# 进入
# 执行代码
# 退出


# 五、with 的执行顺序
#
# 看：
#
# with DemoContext():
#     print("业务代码")
#
# 可以粗略理解为：
#
# context = DemoContext()
#
# context.__enter__()
#
# try:
#     print("业务代码")
# finally:
#     context.__exit__(
#         ...,
#     )
#
# 所以重点就是：
#
# __enter__
# ↓
# 执行 with 内部代码
# ↓
# __exit__


# 六、with ... as ... 的值从哪里来
#
# 看：
#
# class DemoContext:
#     def __enter__(self):
#         print("进入")
#         return "HELLO"
#
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         print("退出")
#
# 调用：
#
# with DemoContext() as value:
#     print(value)
#
# 输出：
#
# 进入
# HELLO
# 退出
#
# 所以：
#
# value
#
# 实际上就是：
#
# __enter__()
#
# 的返回值。


# 七、文件对象为什么能写 as file
#
# 你写：
#
# with path.open() as file:
#
# 本质：
#
# path.open()
# ↓
# 返回文件对象
# ↓
# 调用文件对象.__enter__()
# ↓
# __enter__ 返回文件对象本身
# ↓
# 绑定给 file
#
# 所以：
#
# file
#
# 是上下文管理器 __enter__() 返回的对象。


# 八、自己写一个资源管理器
#
# 比如模拟数据库连接：
#
# class DatabaseConnection:
#     def __enter__(self):
#         print("打开数据库连接")
#         return self
#
#     def query(
#         self,
#         sql: str,
#     ) -> None:
#         print(
#             f"执行SQL：{sql}"
#         )
#
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         print("关闭数据库连接")
#
# 使用：
#
# with DatabaseConnection() as connection:
#     connection.query(
#         "SELECT * FROM orders"
#     )
#
# 输出：
#
# 打开数据库连接
# 执行SQL：SELECT * FROM orders
# 关闭数据库连接


# 九、这里相当于 Java 什么
#
# Java：
#
# try (Connection connection = getConnection()) {
#     ...
# }
#
# Python：
#
# with DatabaseConnection() as connection:
#     ...
#
# 对应关系：
#
# Python	        Java
# __enter__()	    获取资源 / 初始化
# __exit__()	    close()
# with	            try-with-resources
# as connection	    try 中资源变量


# 十、__exit__ 的三个异常参数
#
# 定义：
#
# def __exit__(
#     self,
#     exc_type,
#     exc_value,
#     traceback,
# ):
#     ...
#
# 这三个参数非常重要。
#
# 如果 with 里面没有异常：
#
# with DemoContext():
#     print("正常")
#
# 那么：
#
# exc_type = None
# exc_value = None
# traceback = None
# 如果：
#
# with DemoContext():
#     raise ValueError(
#         "订单数据错误"
#     )
#
# 那么大致：
#
# exc_type = ValueError
# exc_value = ValueError("订单数据错误")
# traceback = 异常堆栈对象


# 十一、打印异常信息
# class DemoContext:
#     def __enter__(self):
#         print("进入")
#         return self
#
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         print(
#             "异常类型：",
#             exc_type,
#         )
#
#         print(
#             "异常对象：",
#             exc_value,
#         )
#
#         print("退出")
#
# 调用：
#
# with DemoContext():
#     raise ValueError("测试")
#
# 输出类似：
#
# 进入
# 异常类型：<class 'ValueError'>
# 异常对象：测试
# 退出
#
# 然后异常继续往外抛。


# 十二、__exit__ 返回值很重要
#
# 默认：
#
# return None
#
# 或者：
#
# return False
#
# 表示：
#
# 不处理异常，让异常继续传播。
#
# 例如：
#
# class DemoContext:
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         return False
#
# 调用：
#
# with DemoContext():
#     raise ValueError("错误")
#
# 最终外面仍会收到：
#
# ValueError


# 十三、如果 __exit__ 返回 True
# class DemoContext:
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         return True
#
# 那么：
#
# with DemoContext():
#     raise ValueError("错误")
#
# print("继续执行")
#
# 异常会被吞掉。
#
# 输出：
#
# 继续执行
#
# 这点非常危险。
#
# 所以通常：
#
# 不要随便 return True。


# 十四、Java 类比异常吞掉
#
# 相当于 Java：
#
# try {
#     ...
# } catch (Exception e) {
#     // 什么都不做
# }
#
# 异常被吃掉。
#
# 生产代码中这种写法很危险。
#
# Python 上下文管理器也是一样。


# 十五、一个真正实用的事务上下文管理器
#
# 比如：
#
# class Transaction:
#     def __enter__(self):
#         print("BEGIN")
#         return self
#
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         if exc_type is None:
#             print("COMMIT")
#         else:
#             print("ROLLBACK")
#
#         return False
#
# 正常：
#
# with Transaction():
#     print("创建订单")
#
# 输出：
#
# BEGIN
# 创建订单
# COMMIT
#
# 异常：
#
# with Transaction():
#     print("创建订单")
#     raise ValueError(
#         "库存不足"
#     )
#
# 输出：
#
# BEGIN
# 创建订单
# ROLLBACK
#
# 然后异常继续往上抛。


# 十六、这就是数据库事务思想
#
# Java Spring：
#
# @Transactional
# public void createOrder() {
#     ...
# }
#
# 或者 JDBC：
#
# try {
#     connection.setAutoCommit(false);
#
#     ...
#
#     connection.commit();
# } catch (Exception e) {
#     connection.rollback();
#     throw e;
# }
#
# Python 上下文管理器可以非常自然地表达：
#
# with transaction():
#     ...


# 十七、try/finally 和 with 的关系
#
# 没有 with：
#
# file = path.open(
#     "r",
#     encoding="utf-8",
# )
#
# try:
#     content = file.read()
# finally:
#     file.close()
#
# 用 with：
#
# with path.open(
#     "r",
#     encoding="utf-8",
# ) as file:
#     content = file.read()
#
# 所以可以理解：
#
# with 是资源型 try/finally 的结构化封装。


# 十八、为什么不要手动 close
#
# 错误风险：
#
# file = path.open()
#
# process(file)
#
# file.close()
#
# 如果：
#
# process(file)
#
# 抛异常：
#
# file.close()
# 不会执行
#
# 资源泄漏。
#
# 正确：
#
# with path.open() as file:
#     process(file)
#
# 无论：
#
# 正常
# 异常
# return
#
# 退出时都会调用：
#
# __exit__()


# 十九、with 不只用于文件
#
# 常见：
#
# with open(...):
#
# 文件。
#
# with lock:
#
# 锁。
#
# with connection:
#
# 数据库。
#
# with transaction:
#
# 事务。
#
# with tempfile.TemporaryDirectory():
#
# 临时目录。
#
# with pytest.raises(...):
#
# 测试异常。
#
# 你 Day 7 已经用过：
#
# with pytest.raises(ValueError):
#
# 这本身就是上下文管理器。


# 二十、重新理解 pytest.raises
#
# 你之前写：
#
# with pytest.raises(ValueError):
#     OrderItem(...)
#
# 背后思想：
#
# 进入上下文
# ↓
# 开始监控异常
# ↓
# 执行OrderItem
# ↓
# 捕获ValueError
# ↓
# 检查是不是预期异常
# ↓
# 退出上下文
#
# 所以：
#
# pytest.raises(...)
#
# 返回的就是一个上下文管理器。


# 二十一、锁也可以 with
#
# 以后并发会写：
#
# from threading import Lock
#
#
# lock = Lock()
#
#
# with lock:
#     # 临界区
#     update_stock()
#
# 相当于：
#
# lock.acquire()
#
# try:
#     update_stock()
# finally:
#     lock.release()
#
# 所以：
#
# with 其实就是统一资源生命周期管理模式。


# 二十二、自定义锁类理解
#
# 你可以想象：
#
# class Lock:
#     def __enter__(self):
#         self.acquire()
#         return self
#
#     def __exit__(
#         self,
#         exc_type,
#         exc_value,
#         traceback,
#     ):
#         self.release()
#
# 所以才能：
#
# with lock:


# 二十三、多个上下文管理器
#
# 可以：
#
# with (
#     input_path.open(
#         "r",
#         encoding="utf-8",
#     ) as input_file,
#     output_path.open(
#         "w",
#         encoding="utf-8",
#     ) as output_file,
# ):
#     ...
#
# 意思是同时管理两个资源。


# 二十四、退出顺序
#
# 例如：
#
# with A(), B():
#     ...
#
# 进入：
#
# A.__enter__
# B.__enter__
#
# 退出：
#
# B.__exit__
# A.__exit__
#
# 注意：
#
# 后进先出。
#
# 类似栈。


# 二十五、Java 类比
#
# Java：
#
# try (
#     InputStream in = ...;
#     OutputStream out = ...
# ) {
#     ...
# }
#
# 关闭顺序也是逆序。
#
# Python思想一致。

# 要求理解：
#
# yield前 = enter
# yield后 = exit
# 二十六、contextlib.contextmanager
#
# 有时候为了一个简单上下文管理器，写一个类太重：
#
# class Transaction:
#     ...
#
# Python 提供：
#
# from contextlib import contextmanager
#
# 然后可以这样写：
#
# from contextlib import contextmanager
# from collections.abc import Iterator
#
#
# @contextmanager
# def transaction() -> Iterator[None]:
#     print("BEGIN")
#
#     try:
#         yield
#     except Exception:
#         print("ROLLBACK")
#         raise
#     else:
#         print("COMMIT")
#
# 使用：
#
# with transaction():
#     print("创建订单")


# 二十七、这里的 yield 又出现了
#
# Day 8 学的 yield 在这里继续发挥作用。
#
# @contextmanager
# def transaction():
#     print("进入")
#
#     yield
#
#     print("退出")
#
# 这里：
#
# yield前
# ↓
# 相当于 __enter__
#
# yield
# ↓
# 把控制权交给 with 内部
#
# yield后
# ↓
# 相当于 __exit__


# 二十八、执行流程
# @contextmanager
# def demo():
#     print("进入")
#
#     yield
#
#     print("退出")
#
# 调用：
#
# with demo():
#     print("业务")
#
# 输出：
#
# 进入
# 业务
# 退出


# 二十九、yield 可以返回 as 的值
# @contextmanager
# def connection():
#     conn = {
#         "status": "connected"
#     }
#
#     print("建立连接")
#
#     try:
#         yield conn
#     finally:
#         print("关闭连接")
#
# 使用：
#
# with connection() as conn:
#     print(conn)
#
# 这里：
#
# conn
#
# 就是：
#
# yield conn
#
# yield 出去的值。


# 三十、类式 vs contextmanager
#
# 两种都可以。
#
# 类方式：
#
# class Transaction:
#     def __enter__(...):
#         ...
#
#     def __exit__(...):
#         ...
#
# 函数方式：
#
# @contextmanager
# def transaction():
#     ...
#     yield
#     ...
#
# 什么时候用哪个？
#
# 简单资源：
#
# 函数 + @contextmanager
#
# 复杂资源，有状态、有多个方法：
#
# class + __enter__/__exit__


# 三十一、一个业务例子：执行计时器
# from contextlib import contextmanager
# from time import perf_counter
# from collections.abc import Iterator
#
#
# @contextmanager
# def timer(
#     name: str,
# ) -> Iterator[None]:
#     start = perf_counter()
#
#     try:
#         yield
#     finally:
#         cost = perf_counter() - start
#
#         print(
#             f"{name}耗时："
#             f"{cost:.3f}秒"
#         )
#
# 使用：
#
# with timer("订单清洗"):
#     clean_orders()
#
# 输出：
#
# 订单清洗耗时：0.352秒


# 三十二、Java 类比计时
#
# Java 可能写：
#
# long start = System.nanoTime();
#
# try {
#     cleanOrders();
# } finally {
#     long cost =
#         System.nanoTime() - start;
# }
#
# Python：
#
# with timer("订单清洗"):
#     clean_orders()
#
# 更适合复用。


# 三十三、一个更完整的数据库事务例子
# from contextlib import contextmanager
# from collections.abc import Iterator
#
#
# class Connection:
#     def begin(self) -> None:
#         print("BEGIN")
#
#     def commit(self) -> None:
#         print("COMMIT")
#
#     def rollback(self) -> None:
#         print("ROLLBACK")
#
#     def close(self) -> None:
#         print("CLOSE")
#
#
# @contextmanager
# def transaction(
#     connection: Connection,
# ) -> Iterator[Connection]:
#     connection.begin()
#
#     try:
#         yield connection
#     except Exception:
#         connection.rollback()
#         raise
#     else:
#         connection.commit()
#     finally:
#         connection.close()
#
# 使用：
#
# connection = Connection()
#
# with transaction(connection) as conn:
#     print("插入订单")
#     print("扣减库存")


# 三十四、这里 try/except/else/finally 又复习到了
# try:
#     yield connection
# except Exception:
#     rollback
#     raise
# else:
#     commit
# finally:
#     close
#
# 对应：
#
# 执行异常
# → except
# → rollback
#
# 执行成功
# → else
# → commit
#
# 不管成功失败
# → finally
# → close
#
# 这个结构非常重要。


# 三十五、上下文管理器的编程思想
#
# 核心不是语法。
#
# 而是：
#
# 把“成对出现的操作”封装起来。
#
# 例如：
#
# open / close
# lock / unlock
# begin / commit-or-rollback
# connect / disconnect
# start / stop
# create / cleanup
#
# 这叫：
#
# Resource Acquisition Is Initialization / 生命周期管理思想
#
# Python用上下文管理器表达得特别自然。


# 三十六、为什么这比手写更安全
#
# 比如锁：
#
# lock.acquire()
#
# update_stock()
#
# lock.release()
#
# 一旦：
#
# update_stock()
#
# 异常：
#
# release不会执行
# ↓
# 锁永远不释放
# ↓
# 后续线程卡死
#
# 改成：
#
# with lock:
#     update_stock()
#
# 异常也会释放。


# 三十七、你的业务场景
#
# 以后你写：
#
# 文件处理
# with path.open() as file:
#     ...
# Redis 分布式锁
#
# 概念上：
#
# with redis_lock:
#     deduct_stock()
# 数据库事务
# with transaction():
#     create_order()
#     deduct_stock()
# 临时文件
# with TemporaryDirectory() as directory:
#     ...
# 性能统计
# with timer("订单同步"):
#     sync_orders()


# 三十八、ExitStack
#
# 如果上下文数量是动态的，可以用：
#
# from contextlib import ExitStack
#
# 例如：
#
# with ExitStack() as stack:
#     files = [
#         stack.enter_context(
#             path.open()
#         )
#         for path in paths
#     ]
#
#     ...
#
# 因为你事先不知道要打开多少个文件。
#
# 当前阶段先知道它存在即可。


# 三十九、同步和异步上下文管理器
#
# 以后学 asyncio 会遇到：
#
# async with ...
#
# 对应：
#
# __aenter__()
# __aexit__()
#
# 例如：
#
# async with client.session():
#     ...
#
# 今天先知道：
#
# with
# → 同步上下文管理器
#
# async with
# → 异步上下文管理器
#
# Day 13 会深入。


# 四十、常见错误1：忘记 finally
#
# 不安全：
#
# @contextmanager
# def connection():
#     conn = create_connection()
#
#     yield conn
#
#     conn.close()
#
# 如果 with 内部报错：
#
# yield之后的代码可能无法正常到达
#
# 推荐：
#
# @contextmanager
# def connection():
#     conn = create_connection()
#
#     try:
#         yield conn
#     finally:
#         conn.close()


# 四十一、常见错误2：吞异常
#
# 错误：
#
# @contextmanager
# def transaction():
#     try:
#         yield
#     except Exception:
#         rollback()
#
# 没有：
#
# raise
#
# 异常就被吃掉了。
#
# 更合理：
#
# except Exception:
#     rollback()
#     raise


# 四十二、常见错误3：资源对象设计成全局变量
#
# 不推荐：
#
# connection = create_connection()
#
# 全局一直不关闭。
#
# 更推荐：
#
# with connection() as conn:
#     ...
#
# 让生命周期清晰。


# 四十三、常见错误4：with 块太大
#
# 例如：
#
# with connection() as conn:
#     # 500行代码
#
# 不好。
#
# 应该让资源持有时间尽可能短：
#
# data = prepare_data()
#
# with connection() as conn:
#     save_data(
#         conn,
#         data,
#     )
#
# 这和 Java 数据库连接、事务范围一样。