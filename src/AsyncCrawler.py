import asyncio
import logging
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    status: int | None = None
    data: str | None = None
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None and self.status is not None and 200 <= self.status < 300


class AsyncCrawler:

    def __init__(
            self,
            max_concurrent: int = 10,
            max_connections: int = 10,
            connect_timeout: float = 10.0,
            read_timeout: float = 30.0
    ) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be greater than 0")
        if max_connections < 1:
            raise ValueError("max_connections must be greater than 0")
        if connect_timeout < 0:
            raise ValueError("connect_timeout must not be negative")
        if read_timeout < 0:
            raise ValueError("read_timeout must not be negative")

        self.max_concurrent = max_concurrent
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
        self.session_lock = asyncio.Lock()

        self.timeout = aiohttp.ClientTimeout(
            connect=connect_timeout,
            sock_read=read_timeout
        )

    async def fetch_url(self, url: str) -> FetchResult:
        async with self.session_lock:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession(
                    timeout=self.timeout,
                    connector=aiohttp.TCPConnector(
                        limit=self.max_connections
                    )
                )
        async with self.semaphore:
            try:
                logger.info("Starting download: %s", url)
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    data = await response.text()
                    logger.info("Successfully downloaded: %s, status: %s", url, response.status)
                    return FetchResult(url=url, status=response.status, data=data)
            except aiohttp.ClientResponseError as cre:
                logger.warning("HTTP error for %s: %s, status: %s", url, type(cre).__name__, cre.status)
                return FetchResult(url=url, status=cre.status, error=str(cre))
            except asyncio.TimeoutError as te:
                logger.warning("Timeout error for %s: %s", url, type(te).__name__)
                return FetchResult(url=url, error=str(te))
            except aiohttp.ClientError as ce:
                logger.error("Client error for %s: %s", url, type(ce).__name__)
                return FetchResult(url=url, error=str(ce))

    async def fetch_urls(self, urls: list[str]) -> list[FetchResult]:
        return list(
            await asyncio.gather(
                *(self.fetch_url(url) for url in urls)
            )
        )

    async def close(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def __aenter__(self) -> AsyncCrawler:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
