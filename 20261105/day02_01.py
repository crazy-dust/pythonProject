from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Order(BaseModel):
    # model_config = ConfigDict(extra="forbid") 告诉 Pydantic：输入里出现 Order 模型没有声明的字段，就报错。
    # 比如这笔订单的三个必填字段都正确，但多传了一个 note：
    # {
    #     "order_id": "A001",
    #     "status": "PAID",
    #     "amount_cents": 1200,
    #     "note": "加急"
    # }
    # 因为 Order 没有声明 note，`Order.model_validate_json(...)` 会抛出 ValidationError，指出 note 是多余字段，错误类型是 extra_forbidden。如果省略这行配置，Pydantic 默认会忽略 note，并用其余三个字段创建订单

    # 对应上一段 JSON Schema 里的 "additionalProperties": false。`model_config` 是整个模型的配置，而 Field(ge=0) 只约束它所在的字段
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1)
    # Literal 对应 Schema 的 enum
    status: Literal["PENDING", "PAID", "CANCELLED"]
    # `ge=0` 对应 minimum: 0
    # `strict=True` 让金额字段拒绝字符串 "1200"
    amount_cents: int = Field(ge=0, strict=True)


if __name__ == '__main__':
    pydantic_obj = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "minLength": 1},
            "status": {"enum": ["PENDING", "PAID", "CANCELLED"]},
            "amount_cents": {"type": "integer", "minimum": 0}
        },
        "required": ["order_id", "status", "amount_cents"],
        "additionalProperties": False
    }

    raw = '{"order_id": "A001", "status": "PAID", "amount_cents": 1200}'
    try:
        # 如果要从模型生成一份 JSON Schema，可以调用 Order.model_json_schema()，它返回一个字典
        order = Order.model_validate_json(raw)
    except ValidationError as exc:
        print(exc)
    else:
        print(order.status, order.amount_cents)
