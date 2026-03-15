from pathlib import Path

import pytest

import src.scraper  # noqa: F401 — 自動登録のためインポート
from src.scraper.ses_rengo import SesRengoScraper

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ses_rengo_sample.html"


@pytest.fixture
def scraper() -> SesRengoScraper:
    return SesRengoScraper()


@pytest.fixture
def sample_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_returns_correct_count(scraper: SesRengoScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    assert len(records) == 3


def test_parse_company_names(scraper: SesRengoScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    names = [r.name for r in records]
    assert "株式会社テストA" in names
    assert "テストB株式会社" in names
    assert "（株）テストC" in names


def test_parse_company_urls(scraper: SesRengoScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    urls = [r.url for r in records]
    assert "https://test-a.co.jp" in urls
    assert "https://test-b.co.jp" in urls
    assert "https://test-c.co.jp" in urls


def test_parse_source_field(scraper: SesRengoScraper, sample_html: str) -> None:
    records = scraper.parse(sample_html)
    for record in records:
        assert record.source == "ses_rengo"


def test_parse_empty_html_returns_empty_list(scraper: SesRengoScraper) -> None:
    records = scraper.parse("<html><body></body></html>")
    assert records == []


def test_source_name(scraper: SesRengoScraper) -> None:
    assert scraper.source_name == "ses_rengo"


def test_source_url(scraper: SesRengoScraper) -> None:
    assert scraper.source_url == "https://ses.ren-go.com/ses-partner-list"
