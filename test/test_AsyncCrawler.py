import asyncio
import socket
import time

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from src.AsyncCrawler import AsyncCrawler

async def create_test_server():
    app = web.Application()

    async def success(request):
        return web.Response(text="Hello, crawler!")

    async def not_found(request):
        return web.Response(status=404, text="Not found")

    async def delayed(request):
        await asyncio.sleep(0.3)
        return web.Response(text="Delayed response")

    app.router.add_get("/ok", success)
    app.router.add_get("/404", not_found)
    app.router.add_get("/delay", delayed)

    server = TestServer(app)
    await server.start_server()

    return server


@pytest.mark.asyncio
async def test_valid_url():
    server = await create_test_server()

    try:
        async with AsyncCrawler() as crawler:
            result = await crawler.fetch_url(
                str(server.make_url("/ok"))
            )

            assert result.is_success
            assert result.status == 200
            assert result.data == "Hello, crawler!"
            assert result.error is None
    finally:
        await server.close()


@pytest.mark.asyncio
async def test_not_found():
    server = await create_test_server()

    try:
        async with AsyncCrawler() as crawler:
            result = await crawler.fetch_url(
                str(server.make_url("/404"))
            )

            assert not result.is_success
            assert result.status == 404
            assert result.data is None
            assert result.error is not None
    finally:
        await server.close()


@pytest.mark.asyncio
async def test_delayed():
    server = await create_test_server()

    try:
        async with AsyncCrawler(read_timeout=0.1) as crawler:
            result = await crawler.fetch_url(
                str(server.make_url("/delay"))
            )

            assert not result.is_success
            assert result.status is None
            assert result.data is None
            assert result.error is not None
    finally:
        await server.close()


@pytest.mark.asyncio
async def test_connection_error():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    async with AsyncCrawler() as crawler:
        result = await crawler.fetch_url(
            f"http://127.0.0.1:{port}"
        )

    assert not result.is_success
    assert result.status is None
    assert result.error is not None


@pytest.mark.asyncio
async def test_parallel_vs_sequential():
    server = await create_test_server()

    try:
        urls = [
            str(server.make_url("/delay")) for _ in range(5)
        ]

        async with AsyncCrawler(
                max_concurrent=5,
                max_connections=5
        ) as crawler:

            # Parallel
            start = time.perf_counter()

            parallel_results = await crawler.fetch_urls(urls)

            parallel_duration = time.perf_counter() - start

            # Sequential
            start = time.perf_counter()

            sequential_results = []

            for url in urls:
                result = await crawler.fetch_url(url)
                sequential_results.append(result)

            sequential_duration = time.perf_counter() - start

        assert all(r.is_success for r in parallel_results)
        assert all(r.is_success for r in sequential_results)

        print(f"\nParallel:   {parallel_duration:.2f} sec")
        print(f"Sequential: {sequential_duration:.2f} sec")

        assert parallel_duration < sequential_duration

    finally:
        await server.close()
