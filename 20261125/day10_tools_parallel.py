"""第 2 周 Day 3：无依赖工具：同轮调用 + 线程池并发执行 + 两轮 LLM 请求。
学习环境 Python 3.14；依赖 openai、jsonschema（版本及 DeepSeek API 参数需核对官方文档）。
运行：python day3_tools_parallel.py --mock --trace（不访问网络）
真实调用：配置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL 后去掉 --mock。
仅使用构造的业务数据。固定流程演示；工具异常直接抛出，不做自动重试或错误回传。
"""

from concurrent.futures import ThreadPoolExecutor
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


# 5. 场景 A：两个工具的全部参数已经由用户提供，不依赖彼此结果。
# 目标是观察同一轮的两个 tool_calls，再由线程池并发执行。
def run(client, model, trace=False):
    messages = [
        {"role": "system", "content": "你是订单履约助手。两个查询参数均已提供，"
         "请在同一轮分别调用订单和库存工具各一次，不要猜测数据。"
         "收到两个结果后综合回答，不要编造。"},
        {"role": "user", "content": "查询 ORD001 的订单状态，同时查询 SKU001 在 WH001 的可用库存。"},
    ]
    expected = {"get_order_status": {"order_id": "ORD001"},
                "get_inventory": {"sku": "SKU001", "warehouse_id": "WH001"}}
    first = ask_model(client, model, messages, "auto", 1, trace)
    prepared = prepare_calls(first, expected)
    append_intent(messages, first)

    # submit 会立即提交任务，返回 Future（类似 Java Future）。
    # 必须先全部 submit，再 result；如果每次 submit 后立即 result，就变成串行。
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(execute, item) for item in prepared]
        # result() 等待结果。虽然按原始顺序取结果，两个任务已经在并发运行。
        results = [future.result() for future in futures]
    print(f"[TOOL 批次] 总耗时={time.perf_counter()-start:.3f}s")
    # 工作线程不直接修改 messages；主线程按原始调用顺序回传，避免竞争。
    for (call, _), result in zip(prepared, results, strict=True):
        append_result(messages, call, result)

    # 固定两轮教学流程，全部结果回传后禁止再次调用工具。
    second = ask_model(client, model, messages, "none", 2, trace)
    return final_answer(second)


def self_test(trace=False):
    from threading import Barrier
    from unittest.mock import patch

    fake = FakeClient([
        fake_response(1, [
            ("call_order", "get_order_status", {"order_id": "ORD001"}),
            ("call_stock", "get_inventory", {"sku": "SKU001", "warehouse_id": "WH001"}),
        ]),
        fake_response(2, text="订单已付款但未锁库；指定仓库可用库存为 0。"),
    ])
    # Barrier 要求两个线程均到达后才继续。如果误写成串行，测试会超时失败。
    gate = Barrier(2, timeout=3)
    def wait_then_call(func):
        def wrapper(**kwargs):
            gate.wait()
            return func(**kwargs)
        return wrapper

    with patch.dict(REGISTRY["get_order_status"], func=wait_then_call(get_order_status)), \
         patch.dict(REGISTRY["get_inventory"], func=wait_then_call(get_inventory)):
        answer = run(fake, "mock", trace)
    assert len(fake.requests) == 2
    history = fake.requests[1]["messages"]
    assert [m["role"] for m in history] == ["system", "user", "assistant", "tool", "tool"]
    assert [m["tool_call_id"] for m in history[-2:]] == ["call_order", "call_stock"]
    assert fake.requests[1]["tool_choice"] == "none"
    assert json.loads(history[-1]["content"])["available_quantity"] == 0
    print("最终回答（模拟）：", answer)
    print("离线测试通过：两个线程确实重叠执行，2 轮模型请求，工具 ID 正确。")


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
