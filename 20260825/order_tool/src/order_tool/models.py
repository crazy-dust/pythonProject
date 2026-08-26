from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum


MONEY_SCALE = Decimal("0.01")


def normalize_money(amount: Decimal) -> Decimal:
    return amount.quantize(
        MONEY_SCALE,
        rounding=ROUND_HALF_UP,
    )


class OrderStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


@dataclass(slots=True, kw_only=True)
class Order:
    order_no: str
    sku: str
    price: Decimal
    quantity: int
    status: OrderStatus

    def __post_init__(self) -> None:
        self.order_no = self.order_no.strip().upper()
        self.sku = self.sku.strip().upper()
        self.price = normalize_money(self.price)

        if not self.order_no:
            raise ValueError("订单号不能为空")

        if not self.sku:
            raise ValueError("SKU不能为空")

        if self.price <= Decimal("0"):
            raise ValueError("价格必须大于0")

        if self.quantity <= 0:
            raise ValueError("数量必须大于0")

    @property
    def amount(self) -> Decimal:
        return normalize_money(
            self.price * self.quantity
        )