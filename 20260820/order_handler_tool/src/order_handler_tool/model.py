from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum

MONEY_SCALE = Decimal("0.01")


def normalize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_SCALE, rounding=ROUND_HALF_UP)


class OrderStatusEnum(StrEnum):
    PAID = "PAID"
    UNPAID = "UNPAID"


@dataclass(slots=True, kw_only=True)
class Order:
    order_no: str
    sku: str
    price: Decimal
    quantity: int
    status: OrderStatusEnum

    def __post_init__(self):
        self.order_no = str(self.order_no).upper()
        self.sku = str(self.sku).upper()
        self.price = normalize_amount(self.price)

        if not self.order_no:
            raise ValueError("订单号不能为空")

        if not self.sku:
            raise ValueError("SKU不能为空")

        if self.price < Decimal("0.00"):
            raise ValueError("价格小于0")

        if self.quantity <= 0:
            raise ValueError("数量必须大于0")

    @property
    def amount(self) -> Decimal:
        return normalize_amount(self.quantity * self.price)
