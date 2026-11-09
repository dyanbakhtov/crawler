import asyncio
import aiohttp
from dataclasses import dataclass

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

    async def fetch_url(self, url: str) -> str:
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
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except aiohttp.ClientResponseError as e:
                return str(e)
            except asyncio.TimeoutError:
                ...
            except aiohttp.ClientError as e:
                ...

    async def fetch_urls(self, urls: list[str]) -> dict[str, str]:
        results = await asyncio.gather(
            *(self.fetch_url(url) for url in urls)
        )
        return dict(zip(urls, results))

    async def close(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()

    async def __aenter__(self) -> AsyncCrawler:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


@dataclass
class HttpResponse:
    url: str
    status: int
    data: Optional[str] = None
    error: Optional[str] = None
