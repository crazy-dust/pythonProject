from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter


# 要求理解：
#
# yield前 = enter
# yield后 = exit
@contextmanager
def timer(
    name: str,
) -> Iterator[None]:
    start = perf_counter()

    try:
        yield
    finally:
        cost = perf_counter() - start

        print(
            f"{name}耗时："
            f"{cost:.3f}秒"
        )


@contextmanager
def open_output_file(
    path: Path,
) -> Iterator[object]:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file = path.open(
        "w",
        encoding="utf-8",
    )

    try:
        yield file
    finally:
        file.close()


def main() -> None:
    output_path = Path(
        "output/orders.txt"
    )

    with timer("订单导出"):
        with open_output_file(
            output_path
        ) as file:
            file.write(
                "A001\n"
            )

            file.write(
                "A002\n"
            )


if __name__ == "__main__":
    main()


# 四十五、也可以多个 with 合并
# with (
#     timer("订单导出"),
#     open_output_file(
#         output_path
#     ) as file,
# ):
#     file.write("A001\n")
#
# 可读性也不错。