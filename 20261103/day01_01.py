def check_order(order):
    # 1. 读取 order_id
    order_id = order.get("order_id")

    str_status = ""
    if order.get("status") is None:
        str_status = "数据异常"

    if "wms_status" not in order:
        str_status = "数据异常"
    elif order.get("wms_status") is None:
        str_status = "数据异常"

    if str_status:
        return {"order_id": order_id, "result": str_status}

    # 3. 如果 status 为 PAID 且
    #    wms_status 为 NOT_CREATED
    #    返回 "异常"
    # 4. 其他情况返回 "正常"
    if order.get("status") == 'PAID' and order.get("wms_status") == 'NOT_CREATED':
        str_status = "异常"
    elif order.get("status") == 'PAID' and order.get("wms_status") == 'CREATED':
        str_status = "正常"
    else:
        str_status = "异常"

    return {"order_id": order_id, "result": str_status}


if __name__ == '__main__':
    order1 = {
        "order_id": "SO-1001",
        "status": "PAID",
        "wms_status": "NOT_CREATED"
    }

    order2 = {
        "order_id": "SO-1002",
        "status": "PAID",
        "wms_status": "CREATED"
    }

    order3 = {
        "order_id": "SO-1003",
        "status": "PAID"
    }

    orders = []
    orders.append(order1)
    orders.append(order2)
    orders.append(order3)

    results = []
    for order in orders:
        result = check_order(order)
        results.append(result)

    print(results)