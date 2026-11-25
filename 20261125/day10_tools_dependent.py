"""第 2 周 Day 3：有依赖工具：订单结果驱动库存调用 + 三轮 LLM 请求。
学习环境 Python 3.14；依赖 openai、jsonschema（版本及 DeepSeek API 参数需核对官方文档）。
运行：python day3_tools_dependent.py --mock --trace（不访问网络）
真实调用：配置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL 后去掉 --mock。
仅使用构造的业务数据。固定流程演示；工具异常直接抛出，不做自动重试或错误回传。
"""

import argparse
import json
import os
import time
from types import SimpleNamespace
from copy import deepcopy

from jsonschema import Draft202012Validator


# 1. 模拟 OMS / WMS：sleep 模拟 I/O 等待，不连接真实系统。
# 只接受示例数据，避免把虚构的库存用于真实业务。
def get_order_status(order_id: str) -> dict:
    time.sleep(0.6)
    if order_id != "ORD001":
        raise ValueError("模拟订单不存在")
    return {"order_id": order_id, "status": "PAID",
            "sku": "SKU001", "warehouse_id": "WH001",
            "inventory_locked": False}


def get_inventory(sku: str, warehouse_id: str) -> dict:
    time.sleep(0.6)
    if (sku, warehouse_id) != ("SKU001", "WH001"):
        raise ValueError("模拟 SKU 或仓库不存在")
    return {"sku": sku, "warehouse_id": warehouse_id,
            "available_quantity": 0}


# 2. 工具契约 + 函数引用统一注册。避免 if/elif 按工具名分发。
# 函数对象留在应用内，只把 description 和 parameters 发送给模型。
REGISTRY = {
    "get_order_status": {
        "func": get_order_status,
        "description": "按 OMS 订单号查询订单状态、SKU、仓库和锁库状态。",
        "schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "pattern": r"\S"}},
            "required": ["order_id"], "additionalProperties": False,
        },
    },
    "get_inventory": {
        "func": get_inventory,
        "description": "按 SKU 和海外仓编号查询可用库存。缺少参数时禁止猜测。",
        "schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "pattern": r"\S"},
                "warehouse_id": {"type": "string", "pattern": r"\S"},
            },
            "required": ["sku", "warehouse_id"], "additionalProperties": False,
        },
    },
}

TOOLS = []
VALIDATORS = {}
for name, item in REGISTRY.items():
    Draft202012Validator.check_schema(item["schema"])
    VALIDATORS[name] = Draft202012Validator(item["schema"])
    TOOLS.append({"type": "function", "function": {
        "name": name, "description": item["description"],
        "parameters": item["schema"],
    }})


def named_tool(name: str) -> dict:
    """强制指定工具（DeepSeek 非思考模式）。不是直接执行该工具。"""
    return {"type": "function", "function": {"name": name}}


# 3. 每次模型请求携带完整消息历史。trace 只用于脱敏的模拟数据。
def ask_model(client, model, messages, tool_choice, round_no, trace=False):
    body = {"model": model, "messages": messages, "tools": TOOLS,
            "tool_choice": tool_choice, "stream": False}
    # extra_body 会合并至 HTTP JSON；thinking 是 DeepSeek 特有配置。
    # 换服务商前必须核对文档，不要照搬此扩展字段。
    if trace:
        print("\n请求 JSON:", json.dumps(
            {**body, "thinking": {"type": "disabled"}},
            ensure_ascii=False, indent=2))
    start = time.perf_counter()
    response = client.chat.completions.create(
        **body, extra_body={"thinking": {"type": "disabled"}})
    elapsed = time.perf_counter() - start
    usage = getattr(response, "usage", None)
    tokens = getattr(usage, "total_tokens", None)
    print(f"[LLM 第 {round_no} 轮] id={response.id} "
          f"耗时={elapsed:.3f}s tokens={tokens if tokens is not None else 'unknown'}")
    if trace:
        # SDK 对象的 JSON 表示，不保证与原始 HTTP 响应字节完全一致。
        print("响应 JSON:", response.model_dump_json(indent=2))
    if not response.choices:
        raise RuntimeError("模型未返回候选结果")
    choice = response.choices[0]
    if getattr(choice.message, "refusal", None):
        raise RuntimeError("模型拒答")
    return choice


def prepare_calls(choice, expected: dict) -> list:
    """先校验整个批次，再执行；expected 是本次固定教学场景的业务边界。

    expected: {工具名: 本轮允许的具体参数}。
    这里严格检查数量、名称、ID 和参数来源，绝不执行猜测出的订单/SKU。
    通用 Agent 不会写死这些业务场景，后续再实现统一循环与授权机制。
    """
    calls = choice.message.tool_calls or []
    if choice.finish_reason != "tool_calls" or len(calls) != len(expected):
        raise RuntimeError(f"模型没有按本轮要求生成工具调用: {choice.finish_reason}, 数量={len(calls)}")
    prepared = []
    names, ids = set(), set()
    for call in calls:
        if call.type != "function" or not call.id or call.id in ids:
            raise ValueError("工具类型或调用 ID 非法")
        name = call.function.name
        if name not in REGISTRY or name not in expected or name in names:
            raise ValueError(f"工具未授权、未预期或重复: {name}")
        # arguments 是 JSON 字符串；**args 需要的是 Python 字典。
        args = json.loads(call.function.arguments)
        VALIDATORS[name].validate(args)
        if args != expected[name]:
            raise ValueError(f"{name} 的参数与已知业务数据不一致")
        names.add(name)
        ids.add(call.id)
        prepared.append((call, args))
    return prepared


def append_intent(messages, choice):
    """保留 assistant 原始调用意图；不能用工具结果替代它。"""
    message = choice.message
    messages.append({"role": "assistant", "content": message.content,
                     "tool_calls": [
        {"id": call.id, "type": "function", "function": {
            "name": call.function.name,
            "arguments": call.function.arguments,
        }} for call in message.tool_calls
    ]})


def execute(prepared):
    """统一动态执行：字典取函数引用，类似 Java Map<String, ToolHandler>。"""
    call, args = prepared
    name = call.function.name
    start = time.perf_counter()
    print(f"[TOOL 开始] {name} id={call.id}")
    result = REGISTRY[name]["func"](**args)
    print(f"[TOOL 完成] {name} 耗时={time.perf_counter()-start:.3f}s")
    return result


def append_result(messages, call, result):
    # tool_call_id 关联的是调用实例，不是函数名，也不是业务幂等键。
    messages.append({"role": "tool", "tool_call_id": call.id,
                     "content": json.dumps(result, ensure_ascii=False)})


def final_answer(choice):
    message = choice.message
    if (choice.finish_reason != "stop" or message.tool_calls
            or not isinstance(message.content, str) or not message.content.strip()):
        raise RuntimeError(f"没有得到最终回答: {choice.finish_reason}")
    return message.content


# 4. 离线模拟：构造与 SDK 字段结构一致的响应替身，检验应用的编排逻辑。
# 不调用真实模型、不需要密钥、不消耗 Token；无法证明真实模型选择准确率。
def fake_response(round_no, calls=None, text=None):
    message = {"role": "assistant", "content": text}
    if calls:
        message["tool_calls"] = [
            {"id": call_id, "type": "function", "function": {
                "name": name, "arguments": json.dumps(args)}}
            for call_id, name, args in calls]
    payload = {
        "id": f"mock_{round_no}", "object": "chat.completion", "created": 0,
        "model": "mock", "choices": [{"index": 0, "message": message,
            "finish_reason": "tool_calls" if calls else "stop"}],
    }
    # object_hook 将每层字典转换为支持属性访问的对象，模拟 SDK 响应。
    response = json.loads(json.dumps(payload), object_hook=lambda obj: SimpleNamespace(**obj))
    response.choices[0].message.tool_calls = getattr(response.choices[0].message, "tool_calls", None)
    response.model_dump_json = lambda **kwargs: json.dumps(payload, ensure_ascii=False, **kwargs)
    return response


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.requests.append(deepcopy(kwargs))
        return next(self.responses)


# 5. 场景 B：用户只给订单号；库存查询需要先获取真实 SKU 和仓库编号。
# 固定三轮教学工作流，不是自主 Agent 的通用循环。
def run(client, model, trace=False):
    messages = [
        {"role": "system", "content": "你是订单履约助手。先查询订单，"
         "再根据真实订单返回的 SKU 和 warehouse_id 查询库存。"
         "不得猜测参数。根据两个工具的结果给出解释，不要编造因果关系。"},
        {"role": "user", "content": "订单 ORD001 为什么没有发货？请查询其对应商品库存。"},
    ]

    # 第一轮只允许模型提出订单查询：此时应用还不知道 SKU 和仓库。
    first = ask_model(client, model, messages, named_tool("get_order_status"), 1, trace)
    prepared = prepare_calls(first, {"get_order_status": {"order_id": "ORD001"}})
    append_intent(messages, first)
    order = execute(prepared[0])
    append_result(messages, prepared[0][0], order)

    # 数据依赖：库存查询的参数必须来自真实订单工具结果，不来自模型猜测。
    # 这里是应用的确定性校验；缺失字段会失败，不会执行后续库存查询。
    inventory_args = {"sku": order["sku"], "warehouse_id": order["warehouse_id"]}
    VALIDATORS["get_inventory"].validate(inventory_args)

    # 第二轮将订单结果回传给模型，指定它生成库存调用。
    # 注意：并未由应用伪造 assistant tool_calls，调用参数仍由模型产生。
    second = ask_model(client, model, messages, named_tool("get_inventory"), 2, trace)
    prepared = prepare_calls(second, {"get_inventory": inventory_args})
    append_intent(messages, second)
    inventory = execute(prepared[0])
    append_result(messages, prepared[0][0], inventory)

    # 第三轮：模型已拥有两份真实（本例为模拟）业务结果，生成最终回答。
    third = ask_model(client, model, messages, "none", 3, trace)
    return final_answer(third)


def self_test(trace=False):
    fake = FakeClient([
        fake_response(1, [("call_order", "get_order_status", {"order_id": "ORD001"})]),
        fake_response(2, [("call_stock", "get_inventory", {"sku": "SKU001", "warehouse_id": "WH001"})]),
        fake_response(3, text="订单已付款、未锁库；指定仓库可用库存为 0，可能与未发货有关。"),
    ])
    answer = run(fake, "mock", trace)
    assert len(fake.requests) == 3
    second_history = fake.requests[1]["messages"]
    assert [m["role"] for m in second_history] == ["system", "user", "assistant", "tool"]
    order = json.loads(second_history[-1]["content"])
    assert order["sku"] == "SKU001" and order["warehouse_id"] == "WH001"
    third_history = fake.requests[2]["messages"]
    assert [m["role"] for m in third_history] == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert [m["tool_call_id"] for m in third_history if m["role"] == "tool"] == ["call_order", "call_stock"]
    assert fake.requests[0]["tool_choice"] == named_tool("get_order_status")
    assert fake.requests[1]["tool_choice"] == named_tool("get_inventory")
    assert fake.requests[2]["tool_choice"] == "none"
    print("最终回答（模拟）：", answer)
    print("离线测试通过：3 轮请求，订单结果先回传，库存参数正确关联。")

    # 反例：第二轮模型猜错 SKU，必须拒绝，不能访问错误商品库存。
    bad = FakeClient([
        fake_response(1, [("call_order", "get_order_status", {"order_id": "ORD001"})]),
        fake_response(2, [("call_stock", "get_inventory", {"sku": "WRONG", "warehouse_id": "WH001"})]),
    ])
    from unittest.mock import patch
    def forbidden_inventory(**kwargs):
        raise AssertionError("不应调用库存工具")

    with patch.dict(REGISTRY["get_inventory"], func=forbidden_inventory):
        try:
            run(bad, "mock", False)
        except ValueError as exc:
            assert "参数与已知业务数据不一致" in str(exc)
            assert len(bad.requests) == 2
        else:
            raise AssertionError("错误 SKU 未被拦截")
    print("反例测试通过：错误 SKU 在执行库存查询前被拦截。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true", help="离线模拟并执行断言")
    parser.add_argument("--trace", action="store_true", help="打印完整请求和响应 JSON（仅模拟业务数据）")
    args = parser.parse_args()
    if args.mock:
        self_test(args.trace)
        return
    # 仅真实 API 模式才加载 SDK；离线测试不依赖它。
    from openai import OpenAI

    with OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"],
                timeout=20.0, max_retries=0) as client:
        print("最终回答：", run(client, os.environ["LLM_MODEL"], args.trace))


if __name__ == "__main__":
    main()
