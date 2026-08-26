import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from order_tool.models import Order, OrderStatus


logger = logging.getLogger(__name__)


def parse_status(value: object) -> OrderStatus | None:
    if value is None:
        return None

    normalized = str(value).strip().upper()

    try:
        return OrderStatus(normalized)
    except ValueError:
        return None


def parse_price(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None

    if not amount.is_finite():
        return None

    return amount


def parse_quantity(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, str):
        normalized = value.strip()

        if not normalized.isdigit():
            return None

        quantity = int(normalized)
        return quantity if quantity > 0 else None

    return None


def clean_order(
    raw_order: dict[str, Any],
) -> Order | None:
    order_no = str(
        raw_order.get("order_no") or ""
    ).strip()

    sku = str(
        raw_order.get("sku") or ""
    ).strip()

    price = parse_price(
        raw_order.get("price")
    )

    quantity = parse_quantity(
        raw_order.get("quantity")
    )

    status = parse_status(
        raw_order.get("status")
    )

    if not order_no:
        logger.warning(
            "跳过订单：订单号为空，原始数据=%s",
            raw_order,
        )
        return None

    if not sku:
        logger.warning(
            "跳过订单%s：SKU为空",
            order_no,
        )
        return None

    if price is None:
        logger.warning(
            "跳过订单%s：价格非法",
            order_no,
        )
        return None

    if quantity is None:
        logger.warning(
            "跳过订单%s：数量非法",
            order_no,
        )
        return None

    if status is None:
        logger.warning(
            "跳过订单%s：状态非法",
            order_no,
        )
        return None

    try:
        return Order(
            order_no=order_no,
            sku=sku,
            price=price,
            quantity=quantity,
            status=status,
        )
    except ValueError as error:
        logger.warning(
            "跳过订单%s：%s",
            order_no,
            error,
        )
        return None


def clean_orders(
    raw_orders: list[dict[str, Any]],
) -> list[Order]:
    result: list[Order] = []

    for raw_order in raw_orders:
        order = clean_order(raw_order)

        if order is not None:
            result.append(order)

    return result