import re

from scrapy import Request
from scrapy_redis.spiders import RedisSpider

from qq_reading_rank.items import QqReadingRankItem


class QqHotRankSpider(RedisSpider):
    name = "qq_hot_rank"
    allowed_domains = ["book.qq.com"]
    redis_key = "qq_hot_rank:start_urls"

    rank_url = "https://book.qq.com/book-rank"

    def make_request_from_data(self, data):
        url = data.decode("utf-8") if isinstance(data, bytes) else data
        return Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        book_nodes = response.xpath(
            "//li[.//a[contains(@href, '/book-detail/')]]"
            " | //div[contains(@class, 'rank') or contains(@class, 'book')]"
            "[.//a[contains(@href, '/book-detail/')]]"
        )

        seen_urls = set()
        for index, node in enumerate(book_nodes, start=1):
            href = node.xpath(".//a[contains(@href, '/book-detail/')]/@href").get()
            if not href:
                continue

            book_url = response.urljoin(href)
            if book_url in seen_urls:
                continue
            seen_urls.add(book_url)

            item = QqReadingRankItem()
            item["rank"] = self._extract_rank(node) or index
            item["book_url"] = book_url
            item["title"] = self._first_text(
                node,
                [
                    ".//*[self::h2 or self::h3 or self::h4]//a[contains(@href, '/book-detail/')]/text()",
                    ".//a[contains(@href, '/book-detail/')]/@title",
                    ".//a[contains(@href, '/book-detail/')]/text()",
                ],
            )
            item["author"] = self._first_text(
                node,
                [
                    ".//a[contains(@href, '/author')]/text()",
                    ".//*[contains(@class, 'author')]//text()",
                ],
            )
            item["tags"] = self._clean_list(
                node.xpath(
                    ".//*[contains(@class, 'tag') or contains(@class, 'info')]//a/text()"
                    " | .//*[contains(@class, 'tag') or contains(@class, 'info')]//span/text()"
                ).getall()
            )
            item["intro"] = self._first_text(
                node,
                [
                    ".//*[contains(@class, 'intro') or contains(@class, 'desc') or contains(@class, 'description')]//text()",
                    ".//p//text()",
                ],
            )

            yield response.follow(
                book_url,
                callback=self.parse_detail,
                meta={"item": item},
                dont_filter=False,
            )

        for href in response.xpath(
            "//a[contains(@href, 'book-rank') and normalize-space()]/@href"
        ).getall():
            next_url = response.urljoin(href)
            if next_url != response.url:
                yield response.follow(next_url, callback=self.parse)

    def parse_detail(self, response):
        item = response.meta["item"]
        body_text = "\n".join(self._clean_list(response.xpath("//body//text()").getall()))

        item["title"] = item.get("title") or self._first_text(
            response,
            [
                "//h1/text()",
                "//*[contains(@class, 'book-info')]//*[self::h1 or self::h2]/text()",
                "//meta[@property='og:novel:book_name']/@content",
                "//meta[@name='book_name']/@content",
            ],
        )
        item["author"] = item.get("author") or self._first_text(
            response,
            [
                "//meta[@property='og:novel:author']/@content",
                "//meta[@name='author']/@content",
                "//*[contains(@class, 'author')]//a/text()",
                "//a[contains(@href, '/author')]/text()",
            ],
        )
        item["update_time"] = self._extract_update_time(response, body_text)
        item["tags"] = self._extract_tags(response) or item.get("tags")
        item["intro"] = item.get("intro") or self._first_text(
            response,
            [
                "//meta[@property='og:description']/@content",
                "//meta[@name='description']/@content",
                "//*[contains(@class, 'book-intro') or contains(@class, 'intro') or contains(@class, 'desc')]//p//text()",
                "//*[contains(@class, 'book-intro') or contains(@class, 'intro') or contains(@class, 'desc')]//text()",
            ],
        )

        yield item

    def _extract_rank(self, selector):
        text = " ".join(selector.xpath(".//text()").getall())
        match = re.search(r"^\s*(\d{1,3})\b", text)
        return int(match.group(1)) if match else None

    def _extract_update_time(self, response, body_text):
        meta_time = self._first_text(
            response,
            [
                "//meta[@property='og:novel:update_time']/@content",
                "//meta[@name='update_time']/@content",
            ],
        )
        if meta_time:
            return meta_time

        candidates = response.xpath(
            "//*[contains(text(), '更新时间') or contains(text(), '最近更新') or contains(text(), '更新于')]//text()"
        ).getall()
        candidates.append(body_text)

        for text in candidates:
            cleaned = " ".join(text.split())
            match = re.search(
                r"(?:更新时间|最近更新|更新于)\s*[：:]?\s*"
                r"([0-9]{4}[-/年.][0-9]{1,2}[-/月.][0-9]{1,2}(?:日)?(?:\s+[0-9]{1,2}:[0-9]{2})?|[0-9]{1,2}小时前|[0-9]{1,2}分钟前|昨天|今天)",
                cleaned,
            )
            if match:
                return match.group(1).strip()
        return None

    def _extract_tags(self, response):
        tags = self._clean_list(
            response.xpath(
                "//meta[@property='og:novel:category']/@content"
                " | //meta[@name='category']/@content"
                " | //meta[@property='og:novel:status']/@content"
            ).getall()
        )
        if tags:
            return tags

        return self._clean_list(
            response.xpath(
                "//*[contains(@class, 'book-info') or contains(@class, 'bookInfo')]"
                "//*[contains(@class, 'tag') or contains(@class, 'label')]//text()"
            ).getall()
        )

    def _first_text(self, selector, xpaths):
        for xpath in xpaths:
            value = selector.xpath(xpath).get()
            if value:
                cleaned = " ".join(value.split())
                if cleaned:
                    return cleaned
        return None

    def _clean_list(self, values):
        cleaned = []
        for value in values:
            text = " ".join(value.split())
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned
