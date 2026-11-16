import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def empty_page_result(url: str) -> dict:
    return {"url": url, "title": None, "text": "", "links": [], "metadata": {}}


class HTMLParser:

    def __init__(self, parser: str = "lxml") -> None:
        self.parser = parser

    def make_soup(self, html: str) -> BeautifulSoup | None:
        try:
            return BeautifulSoup(html, self.parser)
        except Exception as e:
            logger.warning("Ошибка разбора HTML: %s", e)
            return None

    async def parse_html(self, html: str, url: str) -> dict:
        result = empty_page_result(url)
        soup = self.make_soup(html)
        if soup is None:
            return result
        return self._parse_soup(soup, url, result)

    def _parse_soup(self, soup: BeautifulSoup, url: str, result: dict) -> dict:
        extractors = {
            "title": lambda: soup.title.string if soup.title else None,
            "text": lambda: self.extract_text(soup),
            "links": lambda: self.extract_links(soup, url),
            "metadata": lambda: self.extract_metadata(soup),
        }
        for key, extractor in extractors.items():
            try:
                result[key] = extractor()
            except Exception as e:
                logger.warning("Ошибка извлечения %s для %s: %s", key, url, e)
        return result

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

    def extract_text(self, soup: BeautifulSoup, selector: str | None = None) -> str:
        if selector:
            elements = soup.select(selector)
            return "\n".join(el.get_text(strip=True) for el in elements)
        return soup.get_text(separator=" ", strip=True)

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}
        title = soup.title.string if soup.title else None
        if title:
            metadata["title"] = title.strip()
        for name in ("description", "keywords"):
            tag = soup.find("meta", attrs={"name": name})
            content = tag.get("content") if tag else None
            if isinstance(content, str) and content:
                metadata[name] = content
        return metadata

    def extract_images(self, soup: BeautifulSoup, base_url: str = "") -> list[dict]:
        images = []
        for tag in soup.find_all("img"):
            src = tag.get("src")
            if isinstance(src, str) and src.strip():
                alt = tag.get("alt")
                images.append({
                    "src": urljoin(base_url, src) if base_url else src,
                    "alt": alt if isinstance(alt, str) else "",
                })
        return images

    def extract_headings(self, soup: BeautifulSoup) -> list[dict]:
        return [
            {"level": tag.name, "text": tag.get_text(strip=True)}
            for tag in soup.find_all(["h1", "h2", "h3"])
        ]

    def extract_tables(self, soup: BeautifulSoup) -> list[list[list[str]]]:
        return [
            [
                [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
                for row in table.find_all("tr")
            ]
            for table in soup.find_all("table")
        ]

    def extract_lists(self, soup: BeautifulSoup) -> list[dict]:
        return [
            {
                "type": tag.name,
                "items": [
                    li.get_text(strip=True)
                    for li in tag.find_all("li", recursive=False)
                ],
            }
            for tag in soup.find_all(["ul", "ol"])
        ]
