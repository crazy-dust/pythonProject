
import os
import json
import time
import random
import logging

from openai import (
    OpenAI,
    APIError,
    APIStatusError,
    APITimeoutError
)
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("order_classifier")

# 输出契约
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "order_id": {
            "type": "string",
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
    "required": ["order_id", "error_type", "confidence"],
    "additionalProperties": False
}

Draft202012Validator.check_schema(OUTPUT_SCHEMA)
validator = Draft202012Validator(OUTPUT_SCHEMA)


class ModelOutputError(Exception):
    pass


# 单独区分输出截断异常
class OutputLengthError(ModelOutputError):
    pass


client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
    timeout=20.0,
    max_retries=0
)

# 首次调用 + 最多重试两次
MAX_ATTEMPTS = 3

# 应用自己的输出 Token 预算上限
MAX_OUTPUT_TOKENS = 2048


def classify_order(
        description: str,
        max_tokens: int,
        stats: dict
) -> dict:

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": (
                    "你是跨境电商订单异常分类器。"
                    "只输出 JSON，不要 Markdown。"
                    "必须包含 order_id、error_type、confidence。"
                    "error_type 仅可为 INVENTORY_ERROR、"
                    "LOGISTICS_ERROR、OTHER。"
                    "confidence 在 0 到 1 之间。"
                    "如果没有明确订单号，使用字符串 UNKNOWN "
                    "作为缺失标记，不要编造订单号。"
                )
            },
            {
                "role": "user",
                "content": description
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=max_tokens
    )

    # 先统计 Token，保证后续校验失败也能计入
    usage = response.usage
    if usage is not None and usage.total_tokens is not None:
        stats["known_tokens"] += usage.total_tokens
        tokens = usage.total_tokens
    else:
        stats["usage_unknown_calls"] += 1
        tokens = "unknown"

    logger.info(
        "response_id=%s tokens=%s",
        response.id,
        tokens
    )

    if not response.choices:
        raise ModelOutputError("模型没有返回候选结果")

    choice = response.choices[0]

    # 特殊处理：输出截断
    if choice.finish_reason == "length":
        raise OutputLengthError("模型输出被截断")

    if choice.finish_reason != "stop":
        raise ModelOutputError(
            f"模型异常停止: {choice.finish_reason}"
        )

    if getattr(choice.message, "refusal", None):
        raise ModelOutputError("模型拒绝回答")

    content = choice.message.content

    if not isinstance(content, str) or not content.strip():
        raise ModelOutputError("模型返回空内容")

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelOutputError("JSON 解析失败") from exc

    try:
        validator.validate(result)
    except ValidationError as exc:
        field = ".".join(map(str, exc.path)) or "根对象"
        raise ModelOutputError(
            f"Schema 校验失败: "
            f"field={field}, code={exc.validator}"
        ) from exc

    return result


def backoff_seconds(attempt: int) -> float:
    # 指数退避 + 少量随机抖动
    return min(8.0, 2 ** (attempt - 1)) + random.uniform(0, 0.3)


def classify_with_retry(description: str) -> dict:

    stats = {
        "known_tokens": 0,
        "usage_unknown_calls": 0
    }

    max_tokens = 512
    attempt_count = 0

    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            attempt_count = attempt

            logger.info(
                "attempt=%d/%d max_tokens=%d",
                attempt,
                MAX_ATTEMPTS,
                max_tokens
            )

            try:
                return classify_order(
                    description,
                    max_tokens,
                    stats
                )

            # 情况 1：输出截断
            except OutputLengthError:
                if (
                        attempt == MAX_ATTEMPTS
                        or max_tokens >= MAX_OUTPUT_TOKENS
                ):
                    raise

                max_tokens = min(
                    max_tokens * 2,
                    MAX_OUTPUT_TOKENS
                )

                logger.warning(
                    "输出截断，下次 max_tokens=%d",
                    max_tokens
                )
                continue

            # 情况 2：请求超时，包括读超时
            except APITimeoutError:
                stats["usage_unknown_calls"] += 1

                if attempt == MAX_ATTEMPTS:
                    raise

                delay = backoff_seconds(attempt)

                logger.warning(
                    "请求超时，%.2f 秒后重试",
                    delay
                )

                time.sleep(delay)

            # 情况 3：HTTP 状态异常
            except APIStatusError as exc:
                stats["usage_unknown_calls"] += 1

                retryable = (
                        exc.status_code == 429
                        or 500 <= exc.status_code <= 599
                )

                if not retryable or attempt == MAX_ATTEMPTS:
                    raise

                delay = backoff_seconds(attempt)

                logger.warning(
                    "HTTP %d，%.2f 秒后重试",
                    exc.status_code,
                    delay
                )

                time.sleep(delay)

    finally:
        logger.info(
            "调用次数=%d，已知Token总量=%d，"
            "用量未知的调用=%d",
            attempt_count,
            stats["known_tokens"],
            stats["usage_unknown_calls"]
        )


if __name__ == "__main__":

    description = (
        "订单 ORD001 库存锁定失败，"
        "仓库返回库存不足"
    )

    try:
        result = classify_with_retry(description)

        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ))

    except (ModelOutputError, APIError) as exc:
        logger.error(
            "分类失败: %s",
            type(exc).__name__
        )
        raise SystemExit(1) from exc


# 下面把你之前的 classify_order() 补充成可运行的完整版本，重点增加你要求的两种失败处理。
# 失败情况	处理方式
# HTTP 429、5xx	指数退避、有限重试
# 网络读超时	对当前只读的模型分类请求有限重试
# finish_reason="length"	增加 max_tokens 后重新请求
# JSON 格式错误、Schema 校验失败	暂不自动重试，直接抛出异常
# HTTP 401 等不可重试错误	立即失败
#
# 这里有两个特别重要的概念：
#
# 1. max_tokens 是什么？
#
# 它是一次模型请求的最大生成 Token 预算，和 finish_reason 直接相关。
#
# 例如第一次设置 max_tokens=512，如果因为输出预算不足而返回 length，第二次可以提高到 1024，第三次到 2048。
#
# 但 length 也可能因为上下文长度不足导致，所以增大 max_tokens 不保证一定解决问题。
# DeepSeek API Docs
#
#
# 2. 为什么网络读超时允许重试？
#
# 因为当前调用只是让模型分析订单异常，不会修改 OMS、ERP 或库存。重复调用不会造成业务写操作重复执行。
#
# 但第一次请求可能已经被模型服务商处理并计费。即使客户端没收到响应，也不能认为该次调用没有产生 Token 成本。
#
# 因此必须限制重试次数，并在日志中保留费用可能未知的情况。


# 两个你需要重点理解的实现
# 第一：超时后重试不是恢复上次请求。
#
# APITimeoutError 是 SDK 的请求超时异常，覆盖读超时等情况。程序重试时会重新发起一个完整请求，而不是接收原请求剩余的内容。
# GitHub
#
#
# 因此，该策略只适用于当前没有业务写入副作用的分类场景。超时调用的 Token 消耗可能未知，不能当成零。
#
# 第二：length 后是提高预算重新生成。
# except OutputLengthError:    if attempt == MAX_ATTEMPTS or max_tokens >= MAX_OUTPUT_TOKENS:        raise    max_tokens = min(max_tokens * 2, MAX_OUTPUT_TOKENS)    continue
#
#
#
# 这里的 continue 会进入下一轮循环，重新调用模型。它不会在原响应后续写。
#
# 另外，max_retries=0 是为了关闭 SDK 的内置重试，避免重试次数叠加。
# GitHub
#
# 仍需补强的生产边界
# 这版实现完成了你要求的核心重试策略，但还没有总请求时限、Retry-After 处理、熔断以及跨服务商能力适配。尤其是模型若因上下文窗口耗尽而返回 length，提高输出预算可能无效。当前 2048 是示例应用预算，并非服务商上限。