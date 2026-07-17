from collections.abc import Callable
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from typing import Any

MONEY_SCALE = Decimal("0.01")


def normalize_money(amount: Decimal) -> Decimal:
    return amount.quantize(
        MONEY_SCALE,
        rounding=ROUND_HALF_UP,
    )


def calculate_order_amount(
        price: Decimal,
        quantity: int,
        *,
        discount: Decimal = Decimal("1.00"),
        shipping_fee: Decimal = Decimal("0.00"),
) -> Decimal:
    if price <= Decimal("0"):
        return Decimal("0.00")

    if quantity <= 0:
        return Decimal("0.00")

    if discount <= Decimal("0") or discount > Decimal("1"):
        return Decimal("0.00")

    if shipping_fee < Decimal("0"):
        return Decimal("0.00")

    amount = price * quantity * discount + shipping_fee
    return normalize_money(amount)


def filter_orders(
        orders: list[dict[str, Any]],
        predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    return [
        order
        for order in orders
        if predicate(order)
    ]


def create_status_filter(
        status: str,
) -> Callable[[dict[str, Any]], bool]:
    normalized_status = status.strip().upper()

    def predicate(order: dict[str, Any]) -> bool:
        order_status = str(
            order.get("status") or ""
        ).strip().upper()

        return order_status == normalized_status

    return predicate


def log_execution(
        func: Callable[..., Any],
) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"开始执行：{func.__name__}")

        result = func(*args, **kwargs)

        print(f"执行完成：{func.__name__}")
        return result

    return wrapper


@log_execution
def get_paid_orders(
        orders: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paid_filter = create_status_filter("PAID")
    return filter_orders(orders, paid_filter)


def main() -> None:
    orders = [
        {
            "order_no": "A001",
            "amount": Decimal("100.00"),
            "status": "PAID",
        },
        {
            "order_no": "A002",
            "amount": Decimal("300.00"),
            "status": "UNPAID",
        },
        {
            "order_no": "A003",
            "amount": Decimal("500.00"),
            "status": "PAID",
        },
    ]

    amount = calculate_order_amount(
        Decimal("100.00"),
        2,
        discount=Decimal("0.80"),
        shipping_fee=Decimal("10.00"),
    )

    print(f"订单金额：{amount}")

    paid_orders = get_paid_orders(orders)
    print(f"已支付订单：{paid_orders}")


if __name__ == "__main__":
    main()
