import asyncio
import logging
from dataclasses import dataclass

import aiohttp

try:
    from src.HTMLParser import HTMLParser, empty_page_result
except ImportError:
    from HTMLParser import HTMLParser, empty_page_result

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
            read_timeout: float = 30.0,
            parser: HTMLParser | None = None
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
        self.parser = parser or HTMLParser()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: aiohttp.ClientSession | None = None
        self.session_lock = asyncio.Lock()

        self.timeout = aiohttp.ClientTimeout(
            connect=connect_timeout,
            sock_read=read_timeout
        )

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self.session is not None and not self.session.closed:
            return self.session
        async with self.session_lock:
            session = self.session
            if session is None or session.closed:
                session = aiohttp.ClientSession(
                    timeout=self.timeout,
                    connector=aiohttp.TCPConnector(
                        limit=self.max_connections
                    )
                )
                self.session = session
            return session

    async def fetch_url(self, url: str) -> FetchResult:
        session = await self._ensure_session()
        async with self.semaphore:
            try:
                logger.info("Starting download: %s", url)
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.text()
                    logger.info("Successfully downloaded: %s, status: %s", url, response.status)
                    return FetchResult(url=url, status=response.status, data=data)
            except aiohttp.ClientResponseError as exc:
                logger.warning("HTTP error for %s: %s, status: %s", url, type(exc).__name__, exc.status)
                return FetchResult(url=url, status=exc.status, error=str(exc))
            except asyncio.TimeoutError as exc:
                logger.warning("Timeout error for %s: %s", url, type(exc).__name__)
                return FetchResult(url=url, error=str(exc))
            except aiohttp.ClientError as exc:
                logger.error("Client error for %s: %s", url, type(exc).__name__)
                return FetchResult(url=url, error=str(exc))

    async def fetch_urls(self, urls: list[str]) -> list[FetchResult]:
        return list(
            await asyncio.gather(
                *(self.fetch_url(url) for url in urls)
            )
        )

    async def fetch_and_parse(self, url: str) -> dict:
        fetch_result = await self.fetch_url(url)
        if not fetch_result.is_success:
            logger.warning("Error fetching page %s: %s", url, fetch_result.error)
            return empty_page_result(url)
        return await self.parser.parse_html(fetch_result.data or "", url)

    async def close(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def __aenter__(self) -> AsyncCrawler:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
