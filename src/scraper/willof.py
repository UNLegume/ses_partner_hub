from bs4 import BeautifulSoup

from src.models import CompanyRecord
from src.scraper.base import BaseScraper
from src.scraper.registry import register


@register
class WillofScraper(BaseScraper):
    source_name = "willof"
    source_url = "https://willof.jp/techcareer/company/industry_14655"

    def parse(self, html: str) -> list[CompanyRecord]:
        soup = BeautifulSoup(html, "lxml")
        records = []
        for item in soup.select("ul.company-list-article li"):
            name_elem = item.select_one("h2")
            if not name_elem:
                continue
            name = name_elem.get_text(strip=True)

            url = ""
            link = item.select_one("a[href]")
            if link:
                href = link.get("href", "")
                if href.startswith("http"):
                    url = href

            records.append(CompanyRecord(name=name, url=url, source="willof"))
        return records
