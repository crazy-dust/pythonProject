import argparse
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://www.v2ex.com"


@dataclass
class Reply:
    """帖子回复"""

    floor: str | None
    author: str | None
    content: str


@dataclass
class Topic:
    """V2EX 帖子"""

    title: str
    url: str
    author: str | None = None
    node: str | None = None
    reply_count: int = 0

    # 抓取帖子详情后才会有
    content: str | None = None
    replies: list[Reply] | None = None


class V2EXSpider:

    def __init__(
        self,
        delay: float = 1.5,
        timeout: int = 15,
    ):
        """
        :param delay: 每次请求之间的基础间隔，单位秒
        :param timeout: HTTP 请求超时时间
        """

        self.delay = delay
        self.timeout = timeout

        self.session = requests.Session()

        # 模拟正常浏览器请求
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
            }
        )

        # 请求失败时自动重试
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=1,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=["GET"],
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(max_retries=retry)

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _sleep(self) -> None:
        """
        每次请求后随机暂停一下。

        不建议高速并发抓取 V2EX。
        随机延迟可以让请求更加平缓。
        """

        sleep_time = self.delay + random.uniform(0.2, 0.8)
        time.sleep(sleep_time)

    def get(self, url: str) -> str:
        """发送 GET 请求"""

        print(f"[GET] {url}")

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        response.raise_for_status()

        self._sleep()

        return response.text

    def crawl_topic_list(self, url: str) -> list[Topic]:
        """
        抓取 V2EX 一个页面中的帖子列表。

        支持：
        https://www.v2ex.com/go/programmer?p=1
        https://www.v2ex.com/go/python?p=1
        """

        html = self.get(url)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        topics: list[Topic] = []

        # --------------------------------------------------
        # 不再使用 div.cell.item
        #
        # 直接查找帖子标题链接：
        #
        # <span class="item_title">
        #     <a href="/t/xxxxx">标题</a>
        # </span>
        #
        # 这样即使 V2EX 修改外层 div class，
        # 只要帖子链接结构没有变化，就还能正常工作。
        # --------------------------------------------------

        title_elements = soup.select(
            'span.item_title a[href^="/t/"]'
        )

        print(
            f"[DEBUG] 找到标题元素："
            f"{len(title_elements)} 个"
        )

        for title_element in title_elements:

            # --------------------------------------
            # 标题
            # --------------------------------------

            title = title_element.get_text(
                strip=True
            )

            href = title_element.get("href")

            if not href:
                continue

            # V2EX 链接有时类似：
            #
            # /t/1234567#reply10
            #
            # 去掉后面的 #replyxx
            href = href.split("#")[0]

            topic_url = urljoin(
                BASE_URL,
                href,
            )

            # --------------------------------------
            # 找到当前帖子所属的 cell
            # --------------------------------------

            item = title_element.find_parent(
                "div",
                class_="cell",
            )

            # 理论上应该能找到
            # 找不到也不影响标题和 URL
            if item is None:
                topics.append(
                    Topic(
                        title=title,
                        url=topic_url,
                    )
                )

                continue

            # --------------------------------------
            # 作者
            # --------------------------------------

            author = None

            author_element = item.select_one(
                'a[href^="/member/"]'
            )

            if author_element:
                author = author_element.get_text(
                    strip=True
                )

            # --------------------------------------
            # 节点
            #
            # 首页通常会显示节点
            # /go/programmer 页面不一定显示节点
            # --------------------------------------

            node = None

            node_element = item.select_one(
                'a[href^="/go/"]'
            )

            if node_element:
                node = node_element.get_text(
                    strip=True
                )

            # 如果当前就是节点页面
            # 从 URL 中获取节点名称
            if node is None and "/go/" in url:

                try:
                    node = (
                        url.split("/go/")[1]
                        .split("?")[0]
                        .split("/")[0]
                    )

                except IndexError:
                    pass

            # --------------------------------------
            # 回复数量
            # --------------------------------------

            reply_count = 0

            # V2EX 回复数链接通常也是指向当前帖子
            reply_elements = item.select(
                'a[href^="/t/"]'
            )

            for reply_element in reply_elements:

                reply_text = reply_element.get_text(
                    strip=True
                )

                # 回复数一般是纯数字
                if reply_text.isdigit():
                    reply_count = int(
                        reply_text
                    )

            # --------------------------------------
            # 创建 Topic
            # --------------------------------------

            topic = Topic(
                title=title,
                url=topic_url,
                author=author,
                node=node,
                reply_count=reply_count,
            )

            topics.append(topic)

        return topics

    def crawl_topic_detail(
        self,
        topic: Topic,
    ) -> Topic:
        """
        进入帖子详情页面。

        获取：
        1. 正文
        2. 回复
        """

        html = self.get(topic.url)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        # ----------------------------
        # 帖子正文
        # ----------------------------

        content_element = soup.select_one(
            "div.topic_content"
        )

        if content_element:
            topic.content = content_element.get_text(
                "\n",
                strip=True,
            )

        # ----------------------------
        # 回复
        # ----------------------------

        replies: list[Reply] = []

        reply_elements = soup.select(
            'div.cell[id^="r_"]'
        )

        for reply_element in reply_elements:

            # 回复人
            author_element = reply_element.select_one(
                'strong a[href^="/member/"]'
            )

            author = (
                author_element.get_text(strip=True)
                if author_element
                else None
            )

            # 回复楼层
            floor_element = reply_element.select_one(
                ".no"
            )

            floor = (
                floor_element.get_text(strip=True)
                if floor_element
                else None
            )

            # 回复内容
            content_element = reply_element.select_one(
                ".reply_content"
            )

            if content_element is None:
                continue

            content = content_element.get_text(
                "\n",
                strip=True,
            )

            replies.append(
                Reply(
                    floor=floor,
                    author=author,
                    content=content,
                )
            )

        topic.replies = replies

        return topic

    def crawl_node(
        self,
        node: str,
        pages: int = 1,
        fetch_detail: bool = False,
    ) -> list[Topic]:
        """
        抓取指定 V2EX 节点。

        例如：

        programmer
        python
        java
        jobs
        share
        """

        topics: list[Topic] = []

        for page in range(1, pages + 1):

            url = (
                f"{BASE_URL}/go/{node}"
                f"?p={page}"
            )

            print()
            print(
                f"========== "
                f"节点 {node} "
                f"第 {page} 页 "
                f"=========="
            )

            page_topics = self.crawl_topic_list(
                url
            )

            print(
                f"发现 {len(page_topics)} 个帖子"
            )

            if fetch_detail:

                for index, topic in enumerate(
                    page_topics,
                    start=1,
                ):

                    print(
                        f"[{index}/{len(page_topics)}] "
                        f"{topic.title}"
                    )

                    try:
                        self.crawl_topic_detail(topic)

                    except requests.RequestException as e:
                        print(
                            f"[ERROR] 抓取帖子失败："
                            f"{topic.url}"
                        )
                        print(e)

            topics.extend(page_topics)

        return topics


def save_jsonl(
    topics: list[Topic],
    output: str,
) -> None:
    """
    将帖子保存成 JSONL。

    每一行是一个完整 JSON 对象。

    相比整个文件使用一个 JSON 数组，
    JSONL 更适合大量爬虫数据。
    """

    path = Path(output)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for topic in topics:

            data: dict[str, Any] = asdict(topic)

            file.write(
                json.dumps(
                    data,
                    ensure_ascii=False,
                )
            )

            file.write("\n")

    print()
    print(
        f"数据保存完成：{path.absolute()}"
    )

    print(
        f"总帖子数：{len(topics)}"
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description="V2EX 帖子爬虫"
    )

    parser.add_argument(
        "--node",
        default="programmer",
        help="V2EX 节点，例如 programmer、python、java",
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="抓取页数",
    )

    parser.add_argument(
        "--detail",
        action="store_true",
        help="是否进入帖子抓取正文和回复",
    )

    parser.add_argument(
        "--output",
        default="v2ex_topics.jsonl",
        help="输出文件",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="请求基础间隔秒数",
    )

    args = parser.parse_args()

    spider = V2EXSpider(
        delay=args.delay,
    )

    try:

        topics = spider.crawl_node(
            node=args.node,
            pages=args.pages,
            fetch_detail=args.detail,
        )

        save_jsonl(
            topics,
            args.output,
        )

    except KeyboardInterrupt:

        print()
        print("程序已手动停止")

    except requests.RequestException as e:

        print()
        print("网络请求发生异常：")
        print(e)


if __name__ == "__main__":
    main()