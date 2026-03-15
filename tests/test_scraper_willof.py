from pathlib import Path

import pytest

import src.scraper  # noqa: F401 — 自動登録のためインポート
from src.scraper.willof import WillofScraper

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "willof_sample.html"


@pytest.fixture
def scraper() -> WillofScraper:
    return WillofScraper()


@pytest.fixture
def sample_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_returns_correct_count(scraper: WillofScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    assert len(records) == 3


def test_parse_company_names(scraper: WillofScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    names = [r.name for r in records]
    assert "株式会社サンプルX" in names
    assert "サンプルY株式会社" in names
    assert "（株）サンプルZ" in names


def test_parse_company_urls(scraper: WillofScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    urls = [r.url for r in records]
    assert "https://sample-x.co.jp" in urls
    assert "https://sample-y.co.jp" in urls
    assert "https://sample-z.co.jp" in urls


def test_parse_source_field(scraper: WillofScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    for record in records:
        assert record.source == "willof"


def test_parse_empty_html_returns_empty_list(scraper: WillofScraper) -> None:
    records = scraper.parse("<html><body></body></html>")
    assert records == []


def test_source_name(scraper: WillofScraper) -> None:
    assert scraper.source_name == "willof"


def test_source_url(scraper: WillofScraper) -> None:
    assert scraper.source_url == "https://willof.jp/techcareer/company/industry_14655"
