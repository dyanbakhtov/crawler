import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTMLParser:

    def __init__(self, parser: str = "lxml") -> None:
        self.parser = parser

    async def parse_html(self, html: str, url: str) -> dict:
        try:
            soup = BeautifulSoup(html, self.parser)
            return {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "text": self.extract_text(soup),
                "links": self.extract_links(soup, url),
                "metadata": self.extract_metadata(soup),
            }
        except Exception as e:
            logger.warning("Ошибка парсинга %s: %s", url, e)
            return {"url": url, "title": None, "text": "", "links": [], "metadata": {}}

    def extract_links(
            self,
            soup: BeautifulSoup,
            base_url: str,
            filter_external: bool = False
    ) -> list[str]:
        base_host = urlparse(base_url).netloc.lower()
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag.get("href")
            if not isinstance(href, str) or not href.strip():
                continue
            link = urljoin(base_url, href)
            if not self._is_valid_url(link):
                continue
            if filter_external and urlparse(link).netloc.lower() != base_host:
                continue
            links.append(link)
        return links

    def _is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def extract_text(self, soup: BeautifulSoup, selector: Optional[str] = None) -> str:
        if selector:
            elements = soup.select(selector)
            return "\n".join(el.get_text(strip=True) for el in elements)
        return soup.get_text(separator=" ", strip=True)

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}
        if soup.title and soup.title.string:
            metadata["title"] = soup.title.string.strip()
        for name in ("description", "keywords"):
            tag = soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                metadata[name] = tag["content"]
        return metadata
