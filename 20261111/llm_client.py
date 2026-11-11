import os
import time
from typing import Iterator

from openai import OpenAI
from openai import (APITimeoutError, APIConnectionError, APIStatusError)

class LLMClient:
    def __init__(self):
        self.model = os.environ["LLM_MODEL"]

        self.client = OpenAI(
            api_key = os.environ["LLM_API_KEY"],
            base_url = os.environ["LLM_BASE_URL"],
            timeout = 20.0,
            max_retries = 2
        )

    def complete(self, prompt: str) -> str:
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model = self.model,
            messages = [
                {"role": "user", "content": prompt}
            ],
            stream = False
        )

        elapsed = time.perf_counter() - start
        print(f"latency = {elapsed:.2f}s")
        print(f"usage = {response.usage}")

        return response.choices[0].message.content or ""

    def stream(self, prompt:str) -> Iterator[str]:
        stream = self.client.chat.completions.create(
            model = self.model,
            messages = [
                {"role" : "user", "content": prompt}
            ],
            stream = True
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                yield content

if __name__ == '__main__':
    llm = LLMClient()
    prompt = "介绍一下大模型"

    print("===非流式===")
    try:
        print(llm.complete(prompt))
    except APITimeoutError:
        print("模型请求超时")
    except APIConnectionError:
        print("模型连接错误")
    except APIStatusError as exec:
        print(f"模型HTTP失败: {exec.status_code}" )


    print("===流式===")
    try:
        for text in llm.stream(prompt):
            print(text, end="", flush=True)
    except APITimeoutError:
        print("模型请求超时")
    except APIConnectionError:
        print("模型连接错误")
    except APIStatusError as exec:
        print(f"模型HTTP失败: {exec.status_code}" )
    print()
