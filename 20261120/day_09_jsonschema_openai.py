
import os
import json
from openai import OpenAI
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


# 1. 输出数据契约
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {
            "type": ["string", "null"],
            "pattern": r"\S"
        },
        "error_type": {
            "type": "string",
            "enum": [
                "INVENTORY_ERROR",
                "LOGISTICS_ERROR",
                "OTHER"
            ]
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        }
    },
    "required": [
        "order_id",
        "error_type",
        "confidence"
    ],
    "additionalProperties": False
}


# 2. 启动时初始化校验器
Draft202012Validator.check_schema(OUTPUT_SCHEMA)
validator = Draft202012Validator(OUTPUT_SCHEMA)


# 3. 自定义模型输出异常
class ModelOutputError(Exception):
    pass


# 4. 创建模型客户端
client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
    timeout=20.0,
    max_retries=0
)


def classify_order(description: str) -> dict:

    # 5. 请求模型
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": (
                    "你是跨境电商订单异常分类器。"
                    "请只输出 JSON，不要输出解释或 Markdown。"
                    "必须包含 order_id、error_type、confidence。"
                    "error_type 只能是 INVENTORY_ERROR、"
                    "LOGISTICS_ERROR、OTHER。"
                    "如果用户没有提供订单号，order_id 必须返回 null。 禁止猜测或编造订单号"
                    "confidence 必须在 0 到 1 之间。"
                    '示例：{"order_id":"ORD001",'
                    '"error_type":"INVENTORY_ERROR",'
                    '"confidence":0.9}'
                )
            },
            {
                "role": "user",
                "content": description
            }
        ],
        response_format={"type": "json_object"}
    )

    # TODO 1：检查响应是否正常完成
    if not response.choices:
        raise ModelOutputError("模型没有返回候选结果")

    choice = response.choices[0]

    if choice.finish_reason != "stop":
        raise ModelOutputError(
            f"模型未正常完成: {choice.finish_reason}"
        )

    # 检查模型是否拒绝回答
    if choice.message.refusal:
        raise ModelOutputError("模型拒绝回答")

    # TODO 2：检查 content
    content = choice.message.content

    if not isinstance(content, str) or not content.strip():
        raise ModelOutputError("模型返回空内容")

    # TODO 3：解析 JSON
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelOutputError(
            "模型返回的内容不是合法 JSON"
        ) from exc

    # TODO 4：校验 Schema
    try:
        validator.validate(result)
    except ValidationError as exc:
        field = ".".join(map(str, exc.path)) or "根对象"

        print("响应 ID:", response.id)
        print("错误字段:", field)
        print("错误规则:", exc.validator)
        print("实际数据类型:", type(exc.instance).__name__)
        print("实际错误值:", repr(exc.instance))
        print("完整错误:", exc.message)

        raise ModelOutputError(
            f"Schema 校验失败: {field}"
        ) from exc

    # TODO 5：返回结构化数据
    return result


# 6. 主程序入口
if __name__ == "__main__":
    description = (
        "订单系统挂了"
    )

    try:
        result = classify_order(description)

        print("分类成功：")
        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ))

    except ModelOutputError as exc:
        print(f"模型输出异常：{exc}")

    except Exception as exc:
        # 演示用：真实生产环境应区分网络、
        # 超时、限流、认证和服务端错误
        print(f"模型调用异常：{type(exc).__name__}")
