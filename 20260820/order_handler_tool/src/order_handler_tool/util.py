import csv
from pathlib import Path

from order_handler_tool.model import Order


def export_orders_to_csv(orders: list[Order], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "order_no",
        "sku",
        "price",
        "quantity",
        "amount",
        "status",
    ]

    with output_path.open(mode="w",
                          encoding="utf-8-sig",
                          newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for order in orders:
            writer.writerow(
                {
                    "order_no": order.order_no,
                    "sku": order.sku,
                    "price": str(order.price),
                    "quantity": order.quantity,
                    "amount": str(order.amount),
                    "status": order.status.value,
                }
            )
