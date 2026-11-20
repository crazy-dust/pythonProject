
from jsonschema import Draft202012Validator

# 1. 定义 JSON Schema
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

# 2. 启动时检查 Schema 是否合法
Draft202012Validator.check_schema(ORDER_SCHEMA)

# 3. 创建可复用的 Validator
validator = Draft202012Validator(ORDER_SCHEMA)


def validate_order(order: dict) -> dict:
    # 4. 收集所有参数校验错误
    errors = list(validator.iter_errors(order))

    # 5. 转换为统一错误结构
    error_details = []

    for error in errors:
        error_details.append({
            "field": ".".join(map(str, error.path)) or "根对象",
            "code": error.validator,
            "message": error.message
        })

    # 排序，保证结果顺序稳定
    error_details.sort(
        key=lambda item: (item["field"], item["code"])
    )

    # 6. 返回统一结果
    return {
        "valid": len(error_details) == 0,
        "errors": error_details
    }


if __name__ == "__main__":
    test_orders = [
        {
            "order_id": "ORD001",
            "status": "PAID",
            "limit": 20
        },
        {
            "order_id": "   ",
            "status": "UNKNOWN",
            "limit": 200
        },
        {
            "order_id": "ORD003",
            "status": "SHIPPED",
            "debug": True
        }
    ]

    for order in test_orders:
        result = validate_order(order)
        print(result)
