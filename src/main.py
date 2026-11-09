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

    async with AsyncCrawler(max_concurrent=10, max_connections=10) as crawler:

        # sequential
        start = time.perf_counter()
        sync_results = []
        for url in urls:
            result = await crawler.fetch_url(url)
            sync_results.append(result)
        sequential_duration = time.perf_counter() - start
        print(f"Синхронно загружено {len(sync_results)} страниц за {sequential_duration:.2f}")

        # async
        start = time.perf_counter()
        async_results = await crawler.fetch_urls(urls)
        async_duration = time.perf_counter() - start
        print(f"Асинхронно загружено {len(async_results)} страниц за {async_duration:.2f}")

        if async_duration > 0:
            speedup = sequential_duration / async_duration
            print(f"Ускорение при асинхронной загрузке: {speedup:.2f}x")

if __name__ == '__main__':
    asyncio.run(main())
