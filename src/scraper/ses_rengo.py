from bs4 import BeautifulSoup

from src.models import CompanyRecord
from src.scraper.base import BaseScraper
from src.scraper.registry import register


@register
class SesRengoScraper(BaseScraper):
    source_name = "ses_rengo"
    source_url = "https://ses.ren-go.com/ses-partner-list"

    def parse(self, html: str) -> list[CompanyRecord]:
        soup = BeautifulSoup(html, "lxml")
        records = []
        for card in soup.select("div.card"):
            name_elem = card.select_one('h3[itemprop="name"]')
            if not name_elem:
                name_elem = card.select_one("h3")
            if not name_elem:
                continue
            name = name_elem.get_text(strip=True)

            # URLはカード内のaタグから取得
            url = ""
            link = card.select_one("a[href]")
            if link:
                href = link.get("href", "")
                if href.startswith("http"):
                    url = href

            records.append(CompanyRecord(name=name, url=url, source="ses_rengo"))
        return records
