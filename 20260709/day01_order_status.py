# pay_status = "PAID"，ship_status = "SHIPPED"     返回 "已支付已发货"
# pay_status = "PAID"，ship_status = "WAITING"     返回 "已支付待发货"
# pay_status = "UNPAID"                            返回 "未支付"
# 其他情况                                      返回 "异常状态"

def queryOrderStatus(payStatus: str, shipStatus: str) -> str:
    if payStatus == "PAID" and shipStatus == "SHIPPED":
        return "已支付已发货"
    elif payStatus == "PAID" and shipStatus == "WAITING":
        return "已支付待发货"
    elif payStatus == "UNPAID":
        return "未支付"
    else:
        return "异常状态"

if __name__ == '__main__':
    print(queryOrderStatus("UNPAID", "WAITING"))