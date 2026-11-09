
import asyncio
import logging
import time

from AsyncCrawler import AsyncCrawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def print_results(results):
    for result in results:
        if result.is_success:
            print(f"✅ {result.url} | HTTP {result.status}")
        else:
            print(
                f"❌ {result.url} | "
                f"HTTP {result.status} | {result.error}"
            )


async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/2",
        "https://httpbin.org/delay/3",
        "https://httpbin.org/status/404",
        "https://python.org",
    ]

    async with AsyncCrawler(max_concurrent=5) as crawler:

        # Параллельная загрузка
        start = time.perf_counter()

        async_results = await crawler.fetch_urls(urls)

        async_duration = time.perf_counter() - start

        print("\n--- Parallel fetching ---")
        print_results(async_results)
        print(f"Total time: {async_duration:.2f} seconds")

        # Последовательная загрузка
        start = time.perf_counter()

        sequential_results = []
        for url in urls:
            result = await crawler.fetch_url(url)
            sequential_results.append(result)

        sequential_duration = time.perf_counter() - start

        print("\n--- Sequential fetching ---")
        print_results(sequential_results)
        print(f"Total time: {sequential_duration:.2f} seconds")

        # Сравнение
        print("\n--- Performance comparison ---")
        print(f"Parallel:   {async_duration:.2f} seconds")
        print(f"Sequential: {sequential_duration:.2f} seconds")

        if async_duration > 0:
            speedup = sequential_duration / async_duration
            print(f"Speedup: {speedup:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())
