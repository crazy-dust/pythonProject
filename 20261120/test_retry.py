from unittest.mock import patch
import day_09_jsonschema_openai_2 as app

attempts = []


def fake_classify(description, max_tokens, stats):
    attempts.append(max_tokens)

    # 前两次模拟输出截断
    if len(attempts) < 3:
        raise app.OutputLengthError("length")

    # 第三次成功
    return {
        "order_id": "ORD001",
        "error_type": "OTHER",
        "confidence": 0.7
    }


# 这相当于临时替换模块中的 classify_order() 函数。
#
# 当 classify_with_retry() 调用它时，实际上执行的是 fake_classify()。
#
# 因此可以精确模拟：
#
# 第一次失败 → 第二次失败 → 第三次成功。
#
# 关键工程原则：重试机制必须能够脱离真实 LLM 服务独立测试。
#
# 否则测试会依赖网络、模型服务商状态，而且产生不必要的 Token 成本。
with patch.object(
        app,
        "classify_order",
        side_effect=fake_classify
):
    result = app.classify_with_retry(
        "订单 ORD001 系统异常"
    )

assert attempts == [512, 1024, 2048]
assert result["order_id"] == "ORD001"

print("测试通过")