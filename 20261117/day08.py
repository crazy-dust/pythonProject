# 环节 1：进阶摸底（预计 8 分钟）
# 考虑一个跨境电商订单查询接口。
#
# 输入 JSON 必须满足以下规则：
# 1. order_id：必填，字符串，不能是空字符串或纯空格。
# 2. status：必填，只允许 PAID、SHIPPED、CANCELLED。
# 3. warehouse_id：可选，但如果传入，必须是字符串。
# 4. limit：可选，必须是 1～100 之间的整数。
# 5. 禁止出现未定义的字段。
# 问题：
#
# 请尝试编写一份完整的 JSON Schema（即使不熟悉语法，也可以先写出你认为合理的结构）。
#
# 并说明以下输入是否应该通过校验：
# {
#     "order_id": "   ",
#     "status": "PAID",
#     "limit": 10,
#     "debug": true
# }
#
#
# 不要求第一次就写对。我会根据你的答案判断是否需要压缩基础概念讲解。

import json

import jsonschema


def check_json(order_json: str) -> dict:
    # 1. 解析 JSON
    # 非法 JSON 自动抛出 JSONDecodeError
    order = json.loads(order_json)

    # 2. 校验顶层必须是字典
    if not isinstance(order, dict):
        raise ValueError("订单数据必须是 JSON 对象")

    # 3. 校验 order_id（必填）
    order_id = order.get("order_id")
    if not isinstance(order_id, str) or not order_id.strip():
        raise ValueError("order_id 必须是非空字符串，且不能全是空格")

    # 4. 校验 status（必填）
    allowed_statuses = {"PAID", "SHIPPED", "CANCELLED"}
    status = order.get("status")

    if not isinstance(status, str) or status not in allowed_statuses:
        raise ValueError("status 必须是允许的订单状态")

    # 5. 校验 warehouse_id（可选）
    if "warehouse_id" in order:
        warehouse_id = order["warehouse_id"]

        if not isinstance(warehouse_id, str):
            raise ValueError("warehouse_id 必须是字符串类型")

    # 6. 校验 limit（可选）
    if "limit" in order:
        limit = order["limit"]

        # 使用 type() 避免 bool 被当成 int
        if type(limit) is not int:
            raise ValueError("limit 必须是整数")

        if not 1 <= limit <= 100:
            raise ValueError("limit 必须在 1～100 范围内")

    # 7. 校验是否存在未知字段
    allowed_fields = {
        "order_id",
        "status",
        "warehouse_id",
        "limit"
    }

    unknown_fields = set(order.keys()) - allowed_fields

    if unknown_fields:
        raise ValueError(f"存在未定义字段: {sorted(unknown_fields)}")

    # 8. 返回合法数据
    return order



# 以上是硬编码，如果是Python里面的JSON Schema，我猜想是有支持的语法，
# 可以类似Java lombok那种方式一样，可以直接定义一个类，然后里面的所有属性都可以以类似注解那种形式限定规则，然后通过语法可以check json转为的字典对象是否符合定义的这个类和其规则






# 四、接下来做一次修正练习
# JSON Schema 有几个核心关键字：
# - type：规定数据类型。
# - properties：定义对象字段。
# - required：规定必填字段。
# - enum：限定允许的值。
# - minimum / maximum：数值范围。
# - additionalProperties：控制额外字段。
# - pattern：字符串正则约束。
# 本轮唯一待办：
#
# 请不再使用 Python if 判断，尝试用上述 JSON Schema 关键字重新描述刚才的五条订单规则。
#
# 直接写 JSON 对象即可。写完后我会评审，并解释 JSON Schema 的校验机制。

import jsonschema
from jsonschema.exceptions import ValidationError


# 1. Schema 定义在函数外，避免重复创建
ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {
            "type": "string",
            "pattern": r"\S"
        },
        "status": {
            "type": "string",
            "enum": ["PAID", "SHIPPED", "CANCELLED"]
        },
        "warehouse_id": {
            "type": "string"
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100
        }
    },
    "required": ["order_id", "status"],
    "additionalProperties": False
}


# 2. 订单参数校验
def validate_order(order: dict) -> dict:
    # 校验失败会抛出 ValidationError
    # 校验成功时 validate() 返回 None
    jsonschema.validate(
        instance=order,
        schema=ORDER_SCHEMA
    )

    # 成功后主动返回原始订单
    return order


# 3. 测试
if __name__ == "__main__":

    test_orders = [
        {
            "order_id": "ORD001",
            "status": "PAID",
            "warehouse_id": "X1001",
            "limit": 20
        },
        {
            "order_id": "   ",
            "status": "PAID",
            "limit": 20
        },
        {
            "order_id": "ORD003",
            "status": "UNKNOWN"
        },
        {
            "order_id": "ORD004",
            "status": "PAID",
            "debug": True
        }
    ]

    for index, order in enumerate(test_orders, start=1):
        try:
            result = validate_order(order)
            print(f"测试 {index}：校验通过，订单：{result}")

        except ValidationError as exc:
            # exc.path：出错字段的路径
            # exc.message：具体校验失败原因
            field = ".".join(map(str, exc.path)) or "根对象"

            print(f"测试 {index}：校验失败")
            print(f"  错误字段：{field}")
            print(f"  错误原因：{exc.message}")
