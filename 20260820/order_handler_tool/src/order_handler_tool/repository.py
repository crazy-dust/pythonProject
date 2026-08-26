import json
from pathlib import Path
from typing import Any


def load_raw_orders(input_path: Path) -> list[dict[str, Any]]:
    with input_path.open(
            "r",
            encoding="utf-8"
    ) as file:
        raw_orders = json.load(file)

        if not isinstance(raw_orders, list):
            raise ValueError("JSON根节点必须是数组")

        if not all(isinstance(item, dict) for item in raw_orders):
            raise ValueError("订单里面的数组必须是对象")

        return raw_orders