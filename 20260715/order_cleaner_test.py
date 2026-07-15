import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


MONEY_SCALE = Decimal("0.01")
ZERO_AMOUNT = Decimal("0.00")

VALID_ORDER_STATUSES = {
    "PAID",
    "UNPAID",
    "SHIPPED",
    "CANCELLED",
}


def normalize_money(amount: Decimal) -> Decimal:
    return amount.quantize(
        MONEY_SCALE,
        rounding=ROUND_HALF_UP,
    )


def format_money(amount: Decimal) -> str:
    return str(normalize_money(amount))


def load_orders(
    input_path: Path,
) -> list[dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("JSON根节点必须是数组")

    if not all(isinstance(item, dict) for item in data):
        raise ValueError("订单数组中的每个元素必须是JSON对象")

    return data


def parse_quantity(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, str):
        normalized_value = value.strip()

        if not normalized_value.isdigit():
            return None

        quantity = int(normalized_value)
        return quantity if quantity > 0 else None

    return None


def parse_money(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None

    if not amount.is_finite() or amount <= ZERO_AMOUNT:
        return None

    return normalize_money(amount)


def clean_order(
    order: dict[str, Any],
) -> dict[str, Any] | None:
    order_no = str(order.get("order_no") or "").strip()

    if not order_no:
        return None

    sku = str(order.get("sku") or "").strip().upper()

    if not sku:
        return None

    status = str(order.get("status") or "").strip().upper()

    if status not in VALID_ORDER_STATUSES:
        return None

    price = parse_money(order.get("price"))
    quantity = parse_quantity(order.get("quantity"))

    if price is None or quantity is None:
        return None

    amount = normalize_money(price * quantity)

    return {
        "order_no": order_no,
        "sku": sku,
        "price": format_money(price),
        "quantity": quantity,
        "amount": format_money(amount),
        "status": status,
    }


def clean_orders(
    raw_orders: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    cleaned_orders: list[dict[str, Any]] = []

    for raw_order in raw_orders:
        cleaned_order = clean_order(raw_order)

        if cleaned_order is not None:
            cleaned_orders.append(cleaned_order)

    return cleaned_orders


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
    output_path = Path("output/clean_orders_test.csv")

    try:
        original_orders = load_orders(input_path)
        cleaned_orders = clean_orders(original_orders)
        export_orders_to_csv(cleaned_orders, output_path)
    except FileNotFoundError as error:
        print(f"文件错误：{error}")
    except json.JSONDecodeError as error:
        print(f"JSON格式错误：{error}")
    except ValueError as error:
        print(f"数据格式错误：{error}")
    except PermissionError as error:
        print(f"文件权限错误：{error}")
    else:
        print(f"原始订单数量：{len(original_orders)}")
        print(f"有效订单数量：{len(cleaned_orders)}")
        print(
            f"无效订单数量："
            f"{len(original_orders) - len(cleaned_orders)}"
        )
        print(f"导出文件：{output_path.resolve()}")


if __name__ == "__main__":
    main()