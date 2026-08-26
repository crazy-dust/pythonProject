import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from order_handler_tool.model import Order
from order_handler_tool.model import OrderStatusEnum

logger = logging.getLogger(__name__)


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
        normalized_value = value.strip()

        if not normalized_value.isdigit():
            return None

        quantity = int(normalized_value)
        return quantity if quantity > 0 else None

    return None


def parse_status(value: object) -> OrderStatusEnum | None:
    if value is None:
        return None

    normalized = str(value).strip().upper()

    try:
        return OrderStatusEnum(normalized)
    except ValueError:
        return None


def clean_order(raw_order: dict[str, Any]) -> Order | None:
    order_no = str(raw_order.get("order_no") or "").strip()
    sku = str(raw_order.get("sku") or "").strip()
    price = parse_price(raw_order.get("price"))
    quantity = parse_quantity(raw_order.get("quantity"))
    status = parse_status(raw_order.get("status"))

    if not order_no:
        logger.warning("跳过订单，订单号为空，原始数据%s", raw_order)
        return None

    if not sku:
        logger.warning("跳过订单，SKU为空，原始数据%s", raw_order)
        return None

    if not price:
        logger.warning("跳过订单，价格非法，原始数据%s", raw_order)
        return None

    if not quantity:
        logger.warning("跳过订单，数量非法，原始数据%s", raw_order)
        return None

    if not status:
        logger.warning("跳过订单，状态非法，原始数据%s", raw_order)
        return None

    try:
        return Order(order_no=order_no,
                     sku=sku,
                     price=price,
                     quantity=quantity,
                     status=status)
    except ValueError as error:
        logger.warning("跳过订单%s", order_no, error)
        return None


def clean_orders(raw_orders: list[dict[str, Any]]) -> list[Order]:
    orders: list[Order] = []
    for raw_order in raw_orders:
        order = clean_order(raw_order)
        if order is not None:
            orders.append(order)

    return orders
