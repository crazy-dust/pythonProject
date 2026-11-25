"""Day 3: 单工具、两轮 Chat Completions 教学示例。仅使用模拟订单。"""
import json
import os

from jsonschema import Draft202012Validator
from openai import OpenAI

# 1. 工具实现：模拟 OMS 查询。真实项目中替换为内部接口调用。
def get_order_status(order_id: str) -> dict:
    if order_id == "ORD001":
        return {"order_id": order_id, "status": "PAID", "inventory_locked": False}
    return {"order_id": order_id, "error": "ORDER_NOT_FOUND"}


# 2. 工具契约：告诉模型有哪些参数，不发送 Python 函数实现。
ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {"type": "string", "pattern": r"\S", "description": "订单唯一编号"}
    },
    "required": ["order_id"],
    "additionalProperties": False,
}
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "根据订单编号查询 OMS 的真实订单状态及库存锁定情况",
        "parameters": ORDER_SCHEMA,
    },
}]
Draft202012Validator.check_schema(ORDER_SCHEMA)
validator = Draft202012Validator(ORDER_SCHEMA)


def ask_order(client: OpenAI, model: str, question: str) -> str:
    messages = [
        {"role": "system", "content": "你是订单履约助手。根据工具返回的数据回答，禁止编造订单状态。"},
        {"role": "user", "content": question},
    ]

    # 3. 第一轮：模型选择是否调用工具。
    first = client.chat.completions.create(
        model=model, messages=messages, tools=TOOLS,
        tool_choice="auto", stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    print("第一轮响应：", first.model_dump_json(indent=2))
    if not first.choices:
        raise RuntimeError("第一轮没有候选结果")
    choice = first.choices[0]
    message = choice.message
    if choice.finish_reason == "stop" and not message.tool_calls:
        # auto 允许模型直接回答，不能假定一定会调用工具。
        if not message.content or not message.content.strip() or getattr(message, "refusal", None):
            raise RuntimeError("模型未返回可用回答")
        return message.content
    if choice.finish_reason != "tool_calls" or not message.tool_calls:
        raise RuntimeError(f"非预期结束原因：{choice.finish_reason}")
    if len(message.tool_calls) != 1:
        raise RuntimeError("本教学示例仅支持一次单工具调用")

    # 4. 解析调用意图，并且只允许执行已知工具。
    call = message.tool_calls[0]
    if call.type != "function" or call.function.name != "get_order_status":
        raise ValueError("未知工具")
    arguments = json.loads(call.function.arguments)
    validator.validate(arguments)  # 参数非法时直接失败，不执行工具。
    result = get_order_status(**arguments)
    print("本地工具结果：", json.dumps(result, ensure_ascii=False))

    # 5. 保留 assistant 的调用意图，然后追加 role=tool 的实际结果。
    messages.append({
        "role": "assistant",
        "content": message.content,
        "tool_calls": [{
            "id": call.id,
            "type": "function",
            "function": {
                "name": call.function.name,
                "arguments": call.function.arguments,
            },
        }],
    })
    messages.append({
        "role": "tool",
        "tool_call_id": call.id,
        "content": json.dumps(result, ensure_ascii=False),
    })
    print("第二轮消息历史：", json.dumps(messages, ensure_ascii=False, indent=2))

    # 6. 第二轮：本例只允许两轮，禁止继续提出工具调用。
    second = client.chat.completions.create(
        model=model, messages=messages, tools=TOOLS,
        tool_choice="none", stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    print("第二轮响应：", second.model_dump_json(indent=2))
    if not second.choices:
        raise RuntimeError("第二轮没有候选结果")
    choice = second.choices[0]
    if (choice.finish_reason != "stop" or choice.message.tool_calls
            or not choice.message.content or not choice.message.content.strip()
            or getattr(choice.message, "refusal", None)):
        raise RuntimeError(f"未得到可用最终回答：{choice.finish_reason}")
    return choice.message.content


if __name__ == "__main__":
    with OpenAI(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.environ["LLM_BASE_URL"],
            timeout=20.0,
            max_retries=0,
    ) as client:
        answer = ask_order(client, os.environ["LLM_MODEL"], "帮我查询订单 ORD001 的状态")
        print("最终回答：", answer)
