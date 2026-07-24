from dataclasses import dataclass, field
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


@dataclass(frozen=True, slots=True, kw_only=True)
class Address:
    country: str
    province: str
    city: str
    detail: str

    def __post_init__(self) -> None:
        if not self.country.strip():
            raise ValueError("国家不能为空")

        if not self.city.strip():
            raise ValueError("城市不能为空")

        if not self.detail.strip():
            raise ValueError("详细地址不能为空")


@dataclass(slots=True, kw_only=True)
class OrderItem:
    sku: str
    price: Decimal
    quantity: int

    def __post_init__(self) -> None:
        self.sku = self.sku.strip().upper()

        if not self.sku:
            raise ValueError("SKU不能为空")

        if self.price <= Decimal("0"):
            raise ValueError("商品价格必须大于0")

        if self.quantity <= 0:
            raise ValueError("商品数量必须大于0")

        self.price = normalize_money(self.price)

    @property
    def amount(self) -> Decimal:
        return normalize_money(
            self.price * self.quantity
        )


@dataclass(slots=True, kw_only=True)
class Order:
    order_no: str
    status: OrderStatus
    address: Address
    items: list[OrderItem] = field(
        default_factory=list
    )
    tags: set[str] = field(
        default_factory=set
    )

    def __post_init__(self) -> None:
        self.order_no = self.order_no.strip().upper()

        if not self.order_no:
            raise ValueError("订单号不能为空")

    @property
    def total_amount(self) -> Decimal:
        return sum(
            (item.amount for item in self.items),
            Decimal("0.00"),
        )

    @property
    def total_quantity(self) -> int:
        return sum(
            item.quantity
            for item in self.items
        )

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    def add_tag(self, tag: str) -> None:
        normalized_tag = tag.strip().upper()

        if normalized_tag:
            self.tags.add(normalized_tag)

    def pay(self) -> None:
        if self.status != OrderStatus.UNPAID:
            raise ValueError(
                f"当前状态不允许支付：{self.status}"
            )

        self.status = OrderStatus.PAID

    def ship(self) -> None:
        if self.status != OrderStatus.PAID:
            raise ValueError(
                f"当前状态不允许发货：{self.status}"
            )

        if not self.items:
            raise ValueError("空订单不能发货")

        self.status = OrderStatus.SHIPPED

    def cancel(self) -> None:
        if self.status == OrderStatus.SHIPPED:
            raise ValueError("已发货订单不能直接取消")

        self.status = OrderStatus.CANCELLED


def main() -> None:
    address = Address(
        country="US",
        province="CA",
        city="Los Angeles",
        detail="123 Main Street",
    )

    order = Order(
        order_no=" a001 ",
        status=OrderStatus.UNPAID,
        address=address,
    )

    order.add_item(
        OrderItem(
            sku=" sku001 ",
            price=Decimal("100.126"),
            quantity=2,
        )
    )

    order.add_item(
        OrderItem(
            sku="SKU002",
            price=Decimal("50.00"),
            quantity=1,
        )
    )

    order.add_tag(" high_risk ")
    order.add_tag("HIGH_RISK")

    print(order)
    print(f"总数量：{order.total_quantity}")
    print(f"总金额：{order.total_amount}")
    print(f"标签：{order.tags}")

    order.pay()
    print(f"支付后状态：{order.status}")

    order.ship()
    print(f"发货后状态：{order.status}")


if __name__ == "__main__":
    main()


# 三十四、这个模型体现了什么
# 数据与行为结合
#
# 订单不只是数据：
    # order_no
    # status
    # items
#
# 还包含业务行为：
    # order.pay()
    # order.ship()
    # order.cancel()
#
# 这比外部随意写：
    # order.status = "SHIPPED"
#
# 更安全。
#
# 状态流转受到约束
    # UNPAID → PAID → SHIPPED
#
# 不允许：
    # UNPAID → SHIPPED
# 金额是计算属性
# 不用额外维护一个容易不一致的 total_amount 字段。
    # order.total_amount
#
# 可变字段使用 default_factory
# 不同订单不会共享集合。
    # items = field(default_factory=list)
    # tags = field(default_factory=set)


