"""
演示 functools.wraps 的作用。

运行方式：
    python wraps_demo.py
"""

from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import Any


def log_without_wraps(
        func: Callable[..., Any],
) -> Callable[..., Any]:
    """不使用 @wraps 的装饰器。"""

    # wrapper 会替代原函数，因此外部看到的函数元信息会变成 wrapper 的元信息
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"[无 wraps] 开始调用：{func.__name__}")
        result = func(*args, **kwargs)
        print(f"[无 wraps] 调用结束：{func.__name__}")
        return result

    return wrapper


def log_with_wraps(
        func: Callable[..., Any],
) -> Callable[..., Any]:
    """使用 @wraps 的装饰器。"""

    # @wraps(func) 会把原函数的重要元信息复制到 wrapper 上
    # 同时还会设置 wrapper.__wrapped__，指向原始函数
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"[有 wraps] 开始调用：{func.__name__}")
        result = func(*args, **kwargs)
        print(f"[有 wraps] 调用结束：{func.__name__}")
        return result

    return wrapper


@log_without_wraps
def query_order_without_wraps(
        order_no: str,
        include_items: bool = False,
) -> dict[str, object]:
    """查询订单：这是原函数的文档字符串。"""
    return {
        "order_no": order_no,
        "include_items": include_items,
        "status": "PAID",
    }


@log_with_wraps
def query_order_with_wraps(
        order_no: str,
        include_items: bool = False,
) -> dict[str, object]:
    """查询订单：这是原函数的文档字符串。"""
    return {
        "order_no": order_no,
        "include_items": include_items,
        "status": "PAID",
    }


def print_function_metadata(
        title: str,
        func: Callable[..., Any],
) -> None:
    """打印函数的关键元信息，观察 wraps 是否生效。"""

    print(f"\n{'=' * 18} {title} {'=' * 18}")

    # 函数名称
    print("__name__：", func.__name__)

    # 函数文档字符串
    print("__doc__：", func.__doc__)

    # 函数类型标注
    print("__annotations__：", func.__annotations__)

    # inspect.signature 会读取函数签名
    print("signature：", signature(func))

    # 使用 @wraps 后，包装函数会有 __wrapped__ 属性，指向原函数
    print("是否存在 __wrapped__：", hasattr(func, "__wrapped__"))

    if hasattr(func, "__wrapped__"):
        print("原函数名称：", func.__wrapped__.__name__)
        print("原函数签名：", signature(func.__wrapped__))


def main() -> None:
    # 一、不使用 @wraps
    # 外部看到的是 wrapper，而不是原来的 query_order_without_wraps
    print_function_metadata(
        "不使用 @wraps",
        query_order_without_wraps,
    )

    # 二、使用 @wraps
    # 外部仍能看到原函数的名称、文档、注解和签名
    print_function_metadata(
        "使用 @wraps",
        query_order_with_wraps,
    )

    print("\n开始执行两个被装饰后的函数：")

    result1 = query_order_without_wraps(
        "A001",
        include_items=True,
    )
    print("无 wraps 返回结果：", result1)

    result2 = query_order_with_wraps(
        "A002",
        include_items=True,
    )
    print("有 wraps 返回结果：", result2)

    print("\n结论：")
    print("1. 不加 @wraps，函数通常仍然可以正常执行。")
    print("2. 但函数名、文档、注解和签名会变成 wrapper 的信息。")
    print("3. 加上 @wraps，可以保留原函数元信息，并通过 __wrapped__ 找到原函数。")
    print("4. FastAPI、pytest、日志、调试、文档生成和依赖注入都可能依赖这些元信息。")


if __name__ == "__main__":
    main()
