from collections import defaultdict
from decimal import Decimal


def get_paid_orders(orders: list[dict]) -> list[dict]:
    return [order for order in orders if order["status"] == "PAID"]


def get_order_nos(orders: list[dict]) -> list[str]:
    return [order["order_no"] for order in orders]


def calculate_total_amount(orders: list[dict]) -> Decimal:
    return sum((order["amount"] for order in orders), Decimal("0.00"))


def calculate_sku_sales(orders: list[dict]) -> dict[str, int]:
    sku_sale_map = defaultdict(int)

    for order in orders:
        sku = order["sku"]
        quantity = order["quantity"]
        sku_sale_map[sku] += quantity

    return dict(sku_sale_map)


def get_unique_skus(orders: list[dict]) -> set[str]:
    return {order["sku"] for order in orders}


def main() -> None:
    orders = [
        {
            "order_no": "A001",
            "sku": "SKU001",
            "quantity": 2,
            "amount": Decimal("100.00"),
            "status": "PAID",
        },
        {
            "order_no": "A002",
            "sku": "SKU002",
            "quantity": 1,
            "amount": Decimal("300.00"),
            "status": "UNPAID",
        },
        {
            "order_no": "A003",
            "sku": "SKU001",
            "quantity": 3,
            "amount": Decimal("500.00"),
            "status": "PAID",
        },
    ]

    print("已支付订单：", get_paid_orders(orders))
    print("订单号列表：", get_order_nos(orders))
    print("订单总金额：", calculate_total_amount(orders))
    print("SKU销量统计：", calculate_sku_sales(orders))
    print("去重SKU：", get_unique_skus(orders))


if __name__ == "__main__":
    main()

# 这段代码你要重点理解

# 1. 为什么 sum 里加 Decimal("0.00")
# return sum((order["amount"] for order in orders), Decimal("0.00"))
#
# 因为 sum() 默认初始值是 0，也就是 int。
#
# 金额是 Decimal，所以我们给它一个 Decimal 初始值，更严谨。

# 2. 为什么返回 dict(sku_sale_map)
# return dict(sku_sale_map)
#
# 因为 defaultdict(int) 打印出来是：
#
# defaultdict(<class 'int'>, {'SKU001': 5})
#
# 业务函数对外返回普通 dict 更干净。

# 3. 为什么这个是 set 推导式
# return {order["sku"] for order in orders}
#
# 因为 {} 里面是一个表达式加 for，就是 set 推导式。
#
# 如果是：
#
# {order["sku"]: order for order in orders}
#
# 那就是 dict 推导式。