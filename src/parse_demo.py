import asyncio
import json
import logging

from bs4 import BeautifulSoup

from AsyncCrawler import AsyncCrawler
from HTMLParser import HTMLParser

# WARNING, чтобы INFO-логи краулера не засоряли вывод демо
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

URLS = [
    "https://example.com",
    "https://python.org",
    "https://httpbin.org/html",
]

MAX_LINKS_SHOWN = 5


def print_page(summary: dict, headings: list[dict]) -> None:
    print(f"\n=== {summary['url']} ===")

    print("Заголовки:")
    for heading in headings:
        print(f"  [{heading['level']}] {heading['text']}")

    print("Итог:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_summary(parser: HTMLParser, soup: BeautifulSoup, page: dict, url: str) -> dict:
    links = page["links"]
    return {
        "url": url,
        "title": page["title"],
        "text_length": len(page["text"]),
        "links_count": len(links),
        "links": links[:MAX_LINKS_SHOWN],
        "images_count": len(parser.extract_images(soup)),
    }


async def main():
    parser = HTMLParser()

    async with AsyncCrawler() as crawler:

        fetch_results = await asyncio.gather(
            *(crawler.fetch_url(url) for url in URLS)
        )

        summaries = []
        for fetch_result, url in zip(fetch_results, URLS):
            if not fetch_result.is_success:
                print(f"❌ {url} | HTTP {fetch_result.status} | {fetch_result.error}")
                continue

            soup = BeautifulSoup(fetch_result.data, parser.parser)
            headings = parser.extract_headings(soup)
            page = await parser.parse_html(fetch_result.data, url)

            summary = build_summary(parser, soup, page, url)
            summaries.append(summary)
            print_page(summary, headings)

        # Общая статистика
        print("\n--- Статистика ---")
        print(f"Страниц обработано: {len(summaries)} из {len(URLS)}")
        if summaries:
            total_links = sum(s["links_count"] for s in summaries)
            avg_text_length = sum(s["text_length"] for s in summaries) / len(summaries)
            print(f"Всего ссылок: {total_links}")
            print(f"Средняя длина текста: {avg_text_length:.0f}")


if __name__ == "__main__":
    asyncio.run(main())
