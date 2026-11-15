import logging
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTMLParser:
    """Парсер HTML-контента: извлечение ссылок, текста и метаданных."""

    def __init__(self, parser: str = "lxml") -> None:
        self.parser = parser

    async def parse_html(self, html: str, url: str) -> dict:
        """Парсинг HTML и извлечение структурированных данных страницы."""
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

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Извлечение всех ссылок с конвертацией относительных в абсолютные."""
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag.get("href")
            if isinstance(href, str) and href.strip():
                links.append(urljoin(base_url, href))
        return links

    def extract_text(self, soup: BeautifulSoup, selector: Optional[str] = None) -> str:
        """Извлечение текста (всей страницы или по CSS-селектору)."""
        if selector:
            elements = soup.select(selector)
            return "\n".join(el.get_text(strip=True) for el in elements)
        return soup.get_text(separator=" ", strip=True)

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Извлечение мета-тегов: title, description, keywords."""
        metadata = {}
        if soup.title and soup.title.string:
            metadata["title"] = soup.title.string.strip()
        for name in ("description", "keywords"):
            tag = soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                metadata[name] = tag["content"]
        return metadata
