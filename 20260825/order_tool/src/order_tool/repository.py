import json
from pathlib import Path
from typing import Any


def load_raw_orders(
    input_path: Path,
) -> list[dict[str, Any]]:
    with input_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "JSON根节点必须是数组"
        )

    if not all(
        isinstance(item, dict)
        for item in data
    ):
        raise ValueError(
            "订单数组中的元素必须是对象"
        )

    return data


# 这里使用 repository 只是表达：
#
# 该模块负责数据来源。
#
# 当前没有必要建立 OrderRepository 类，一个函数足够。