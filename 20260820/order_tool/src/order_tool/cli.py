import argparse
import json
import logging
from pathlib import Path

from order_tool.cleaner import clean_orders
from order_tool.config import AppConfig
from order_tool.exporter import export_orders_to_csv
from order_tool.logging_config import configure_logging
from order_tool.repository import load_raw_orders


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="订单JSON清洗并导出CSV",
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="输入JSON文件路径",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="输出CSV文件路径",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="开启DEBUG日志",
    )

    return parser.parse_args()


def build_config(
    args: argparse.Namespace,
) -> AppConfig:
    return AppConfig(
        input_path=args.input,
        output_path=args.output,
        debug=args.debug,
    )


def run(config: AppConfig) -> None:
    raw_orders = load_raw_orders(
        config.input_path
    )

    orders = clean_orders(raw_orders)

    export_orders_to_csv(
        orders,
        config.output_path,
    )

    logger.info(
        "原始订单数量：%s",
        len(raw_orders),
    )

    logger.info(
        "有效订单数量：%s",
        len(orders),
    )

    logger.info(
        "无效订单数量：%s",
        len(raw_orders) - len(orders),
    )

    logger.info(
        "导出文件：%s",
        config.output_path.resolve(),
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)

    configure_logging(
        debug=config.debug,
    )

    try:
        run(config)
    except FileNotFoundError:
        logger.exception(
            "输入文件不存在"
        )
        raise SystemExit(1)
    except json.JSONDecodeError:
        logger.exception(
            "JSON格式错误"
        )
        raise SystemExit(2)
    except PermissionError:
        logger.exception(
            "文件权限错误"
        )
        raise SystemExit(3)
    except ValueError:
        logger.exception(
            "数据格式错误"
        )
        raise SystemExit(4)