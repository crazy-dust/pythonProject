from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Any

FORMAT_NUMBERS = Decimal("0.01")


@dataclass(kw_only=True)
class Order:
    id: int
    order_no: str
    order_status: OrderStatus
    order_items: list[OrderItem] = field(default_factory=list)
    order_address: OrderAddress

    def __post_init__(self) -> None:
        """
        初始化完成后进行数据清洗和类型转换。
        """

        self.order_no = str(self.order_no).strip()

        # 支持传入字符串或者 OrderStatus 枚举
        self.order_status = OrderStatus(self.order_status)

        # 检查订单中已有的明细是否属于当前订单
        for order_item in self.order_items:
            self._validate_order_item(order_item)

    def _validate_order_item(self, order_item: OrderItem) -> None:
        if order_item.order_id != self.id:
            raise ValueError(
                f"订单明细 order_id={order_item.order_id} "
                f"与订单 id={self.id} 不一致"
            )

        if order_item.order_no != self.order_no:
            raise ValueError(
                f"订单明细 order_no={order_item.order_no} "
                f"与订单 order_no={self.order_no} 不一致"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Order:
        order_items = [
            item
            if isinstance(item, OrderItem)
            else OrderItem.from_dict(item)
            for item in data.get("order_items", [])
        ]

        address_data = data["order_address"]

        order_address = (
            address_data
            if isinstance(address_data, OrderAddress)
            else OrderAddress.from_dict(address_data)
        )

        return cls(
            id=data["id"],
            order_no=data["order_no"],
            order_status=OrderStatus(data["order_status"]),
            order_items=order_items,
            order_address=order_address,
        )

    @property
    def order_total_amount(self):
        return sum([item.amount for item in self.order_items], Decimal("0"))

    @property
    def is_paid(self):
        return self.order_status == OrderStatus.PAID

    def add_order_item(self, order_item: OrderItem):
        self.order_items.append(order_item)


def FORMAT_CURRENCY(amount: Decimal) -> Decimal:
    return amount.quantize(FORMAT_NUMBERS, rounding=ROUND_HALF_UP)


@dataclass(kw_only=True)
class OrderItem:
    order_id: int
    order_no: str
    sku: str
    price: Decimal
    quantity: int

    @classmethod
    def from_dict(cls, order_item: dict[str, Any]) -> OrderItem:
        return cls(**order_item)

    @property
    def amount(self):
        return FORMAT_CURRENCY(self.price * self.quantity)


@dataclass(kw_only=True)
class OrderAddress:
    order_id: int
    first_name: str
    last_name: str
    address: str

    def __post_init__(self) -> None:
        self.first_name = str(self.first_name).strip()
        self.last_name = str(self.last_name).strip()
        self.address = str(self.address).strip()

    def complete_address(self):
        return f"{self.first_name} {self.last_name}, {self.address}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrderAddress:
        return cls(**data)


class OrderStatus(StrEnum):
    UNPAID = "UNPAID",
    PAID = "PAID",
    SHIPPED = "SHIPPED",
    ERROR = "ERROR"


def main() -> None:
    order = Order.from_dict({
        "id": 123,
        "order_no": "ORD-123",
        "order_status": OrderStatus.PAID,
        "order_items": [
            {
                "order_id": 123,
                "order_no": "ORD-123",
                "sku": "SKU123",
                "price": 100,
                "quantity": 1,
            }
        ],
        "order_address": {
            "order_id": 123,
            "first_name": "FirstName",
            "last_name": "lastName",
            "address": "123123232"
        }
    })
    print(order)


if __name__ == '__main__':
    main()
