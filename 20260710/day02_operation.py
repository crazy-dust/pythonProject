from collections import defaultdict
from decimal import Decimal


# 作业 1：筛选大额订单
# 写函数：
# def get_large_orders(orders: list[dict], min_amount: Decimal) -> list[dict]:
# 要求：返回 amount >= min_amount 的订单列表
def get_large_orders(orders: list[dict], min_amount: Decimal) -> list[dict]:
    return [order for order in orders if order["amount"] >= min_amount]


# 作业 2：按订单状态分组
# 写函数：
# def group_orders_by_status(orders: list[dict]) -> dict[str, list[dict]]:
# 示例结果：
# {
#     "PAID": [
#         {"order_no": "A001", ...},
#         {"order_no": "A003", ...},
#     ],
#     "UNPAID": [
#         {"order_no": "A002", ...},
#     ]
# }
# 提示：可以用defaultdict(list)。
def group_orders_by_status(orders: list[dict]) -> dict[str, list[dict]]:
    status_map = defaultdict(list)
    for order in orders:
        status_map[order["status"]].append(order)
    return dict(status_map)


# 作业 3：统计每个 SKU 的销售金额
# 写函数：
# def calculate_sku_amounts(orders: list[dict]) -> dict[str, Decimal]:
# 要求：按 SKU 统计 amount 总和
# 示例：
# {
#     "SKU001": Decimal("600.00"),
#     "SKU002": Decimal("300.00")
# }
def calculate_sku_amounts(orders: list[dict]) -> dict[str, Decimal]:
    sku_amount_map = defaultdict(lambda: Decimal("0.00"))
    for order in orders:
        sku_amount_map[order["sku"]] += order["amount"]
    return dict(sku_amount_map)


# 作业 4：找出未支付订单号
# 写函数：
# def get_unpaid_order_nos(orders: list[dict]) -> list[str]:
# 要求：返回 status == "UNPAID" 的订单号列表
# 建议用 list 推导式。
def get_unpaid_order_nos(orders: list[dict]) -> list[str]:
    return [order["order_no"] for order in orders if order["status"] == "UNPAID"]


# 逐渐建立这个意识：[转换结果 for 元素 in 集合 if 条件]
# 这里：
# order["order_no"]                  # map
# for order in orders                # 遍历
# if order["status"] == "UNPAID"     # filter

# 作业 5：SKU 去重
# 写函数：
# def get_unique_skus(orders: list[dict]) -> set[str]:
# 要求：返回订单里的所有 SKU，不能重复
# 建议用 set 推导式。
def get_unique_skus(orders: list[dict]) -> set[str]:
    unique_skus = set()
    for order in orders:
        unique_skus.add(order["sku"])
    return unique_skus


#   return {order["sku"] for order in orders}

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
        {
            "order_no": "A004",
            "sku": "SKU003",
            "quantity": 1,
            "amount": Decimal("900.00"),
            "status": "PAID",
        },
    ]
    print(get_large_orders(orders, min_amount=Decimal("0.00")))
    print(group_orders_by_status(orders))
    print(calculate_sku_amounts(orders))
    print(get_unpaid_order_nos(orders))
    print(get_unique_skus(orders))


if __name__ == '__main__':
    main()
