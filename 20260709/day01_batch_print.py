# 给你一个订单号列表：
# order_nos = ["A001", "A002", "A003", "A004"]
# 要求输出：
#     第1个订单：A001
#     第2个订单：A002
#     第3个订单：A003
#     第4个订单：A004
# 必须使用：enumerate()

order_nos = ["A001", "A002", "A003", "A004"]
for index, orderNo in enumerate(order_nos, start=1):
    print(f"第{index}个订单：{orderNo}")
