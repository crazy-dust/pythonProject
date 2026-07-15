import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

MONEY_SCALE = Decimal("0.01")


def normalize_money(amount: Decimal) -> Decimal:
    return amount.quantize(
        MONEY_SCALE,
        rounding=ROUND_HALF_UP,
    )


def load_orders(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        raise FileNotFoundError(f"订单文件不存在：{file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("订单文件根节点必须是 JSON 数组")

    return data


def clean_order(
        raw_order: dict[str, Any],
) -> dict[str, Any] | None:
    order_no = str(raw_order.get("order_no") or "").strip()
    sku = str(raw_order.get("sku") or "").strip().upper()
    status = str(raw_order.get("status") or "").strip().upper()

    if not order_no:
        return None

    if not sku:
        return None

    try:
        price = Decimal(str(raw_order.get("price")))
        quantity = int(raw_order.get("quantity"))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if price <= Decimal("0") or quantity <= 0:
        return None

    amount = normalize_money(price * quantity)

    return {
        "order_no": order_no,
        "sku": sku,
        "price": str(normalize_money(price)),
        "quantity": quantity,
        "amount": str(amount),
        "status": status,
    }


def clean_orders(
        raw_orders: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    clean_result: list[dict[str, Any]] = []

    for raw_order in raw_orders:
        clean_order_result = clean_order(raw_order)

        if clean_order_result is not None:
            clean_result.append(clean_order_result)

    return clean_result


def export_orders_to_csv(
        orders: list[dict[str, Any]],
        output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "order_no",
        "sku",
        "price",
        "quantity",
        "amount",
        "status",
    ]

    with output_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(orders)


def main() -> None:
    input_path = Path("data/orders.json")
    output_path = Path("output/clean_orders.csv")

    try:
        raw_orders = load_orders(input_path)
        orders = clean_orders(raw_orders)
        export_orders_to_csv(orders, output_path)
    except FileNotFoundError as error:
        print(f"文件错误：{error}")
    except json.JSONDecodeError as error:
        print(f"JSON格式错误：{error}")
    except ValueError as error:
        print(f"数据格式错误：{error}")
    else:
        print(f"原始订单数量：{len(raw_orders)}")
        print(f"有效订单数量：{len(orders)}")
        print(f"无效订单数量：{len(raw_orders) - len(orders)}")
        print(f"导出文件：{output_path.resolve()}")


if __name__ == "__main__":
    main()

# 二十二、重点代码解释
# 1. 为什么使用 Any
# dict[str, Any]
#
# 外部 JSON 中字段类型不可靠：
#
# quantity 可能是 int
# quantity 也可能是 str
# sku 可能是 None
# price 可能是错误字符串
#
# 所以原始数据暂时使用：
#
# dict[str, Any]
#
# 后续清洗完成后，才逐步转换成明确类型。
#
# 2. 为什么写成这样
# order_no = str(raw_order.get("order_no") or "").strip()
#
# 分解：
#
# raw_order.get("order_no")
#
# 取字段，字段不存在返回 None。
#
# raw_order.get("order_no") or ""
#
# 如果值是 None 或空值，转成空字符串。
#
# str(...).strip()
#
# 确保最终是去掉首尾空格的字符串。
#
# 3. 为什么 Decimal 外面加 str
# price = Decimal(str(raw_order.get("price")))
#
# 如果原始数据是：
#
# 100.1
#
# 它已经是 float。
#
# 使用：
#
# str(100.1)
#
# 先转成 "100.1"，再构造 Decimal，可以减少二进制浮点误差传播。
#
# 但最理想的 JSON 金额仍然应该直接传字符串。
#
# 4. 为什么捕获多个异常
# except (InvalidOperation, TypeError, ValueError):
#
# 可能出现：
#
# Decimal("abc") → InvalidOperation
# int(None) → TypeError
# int("2.5") → ValueError
#
# 这些都属于当前订单的数据错误，所以统一判定为无效订单。
#
# 5. 为什么清洗函数返回 None
# def clean_order(...) -> dict[str, Any] | None:
#
# 含义：
#
# 返回 dict：清洗成功
# 返回 None：订单无效
#
# 调用方：
#
# if clean_order_result is not None:
#     clean_result.append(clean_order_result)
#
# 这是 Python 中常见的失败表示方式。
#
# 后面更复杂的业务会改成：
#
# 返回成功结果
# 返回错误原因
# 抛出业务异常
# 使用数据模型校验


# 二十三、当前实现的不足
# 这版只是 Day 3 版本，还不算高级生产代码。
#
# 目前无效订单只返回：
#
# None
#
# 但不知道为什么无效。
#
# 真正业务中应该记录：
#
# 订单号为空
# SKU为空
# 金额格式错误
# 数量错误
# 金额小于等于0
#
# 后续会升级成类似：
#
# {
#     "success": False,
#     "reason": "INVALID_PRICE",
#     "raw_order": raw_order,
# }
#
# 或者使用 dataclass / Pydantic Model。


# 二十六、今天的 Code Review 检查表
# 完成后自己检查：
# 是否使用 Path，而不是手工拼接路径？
# 文件是否通过 with 打开？
# 是否明确指定 encoding？
# CSV 是否使用 newline=""？
# CSV 是否使用 utf-8-sig？
# JSON 中文是否使用 ensure_ascii=False？
# 金额是否使用 Decimal？
# 是否捕获了明确异常，而不是裸 except？
# 函数是否只承担一个职责？
# 无效数据是否有清晰处理策略？
# 今天必须记住
# Path：处理文件路径
# with：自动释放文件资源
# json.load：从文件读取 JSON
# json.loads：从字符串读取 JSON
# json.dump：向文件写 JSON
# json.dumps：生成 JSON 字符串
# csv.DictReader：CSV 行转字典
# csv.DictWriter：字典写入 CSV
# utf-8-sig：方便 Windows Excel 打开中文 CSV
# Decimal 不能直接 JSON 序列化
# 外部数据永远不能默认可信
