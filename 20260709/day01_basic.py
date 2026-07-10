from decimal import Decimal


def calculateOrderAmt(price: Decimal, quantity: int) -> Decimal:
    return price * quantity


print(f"Order amount: {calculateOrderAmt(Decimal('10.5078'), 2):.2f}")


def getOrderLevel(amt: Decimal) -> str:
    if amt >= 2000:
        return "大额订单"
    elif amt >= 1000:
        return "中额订单"
    else:
        return "小额订单"


print(getOrderLevel(Decimal('1500.00')))


def main() -> None:
    orderNo = "ORD-123"
    sku = "AAA1111"
    price = Decimal("10.5078")
    quantity = 10

    orderAmt = calculateOrderAmt(price, quantity)
    level = getOrderLevel(orderAmt)
    print(f"订单号：{orderNo}")
    print(f"SKU：{sku}")
    print(f"单价：{price:.2f}")
    print(f"数量：{quantity}")
    print(f"订单总金额：{orderAmt:.2f}")
    print(f"订单等级：{level}")


if __name__ == '__main__':
    main()
