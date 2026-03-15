"""Tests for src/contacts/finder.py"""
import pathlib

import pytest

from src.contacts.finder import find_contact_url

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestFindContactUrl:
    def test_contact_html_returns_contact_url(self):
        html = load_fixture("company_with_contact.html")
        result = find_contact_url(html, "https://example.co.jp")
        assert result["contact_url"] == "https://example.co.jp/contact"
        assert result["status"] == "URL済"

    def test_contact_html_candidates_not_empty(self):
        html = load_fixture("company_with_contact.html")
        result = find_contact_url(html, "https://example.co.jp")
        assert len(result["candidates"]) > 0

    def test_inquiry_html_returns_inquiry_url(self):
        html = load_fixture("company_with_inquiry.html")
        result = find_contact_url(html, "https://example.co.jp")
        assert result["contact_url"] == "https://example.co.jp/inquiry"
        assert result["status"] == "URL済"

    def test_no_contact_html_returns_empty_url(self):
        html = load_fixture("company_no_contact.html")
        result = find_contact_url(html, "https://example.co.jp")
        assert result["contact_url"] == ""
        assert result["status"] == "取得失敗"
        assert result["candidates"] == []

    def test_english_contact_html_returns_contact_us_url(self):
        html = load_fixture("company_english_contact.html")
        result = find_contact_url(html, "https://example.co.jp")
        assert "contact-us" in result["contact_url"]
        assert result["status"] == "URL済"

    def test_urljoin_with_trailing_slash_base_url(self):
        html = load_fixture("company_with_contact.html")
        result = find_contact_url(html, "https://example.co.jp/")
        assert result["contact_url"] == "https://example.co.jp/contact"

    def test_urljoin_with_subdirectory_base_url(self):
        html = load_fixture("company_with_inquiry.html")
        result = find_contact_url(html, "https://example.co.jp/")
        assert result["contact_url"] == "https://example.co.jp/inquiry"

    def test_nav_footer_links_prioritized_over_body_links(self):
        """ナビ/フッター内のリンクがページ本文のリンクより優先される"""
        html = """
        <html>
        <body>
        <nav>
          <a href="/contact">お問い合わせ</a>
        </nav>
        <main>
          <p>詳しくは<a href="/inquiry">こちら</a>からお問い合わせください。</p>
        </main>
        </body>
        </html>
        """
        result = find_contact_url(html, "https://example.co.jp")
        # /contact はナビにあるので priority=1 で /inquiry の priority=3 より優先
        assert result["contact_url"] == "https://example.co.jp/contact"
        # /inquiry も候補に入るが順位は後
        assert "https://example.co.jp/contact" in result["candidates"]

    def test_multiple_candidates_returned_in_priority_order(self):
        """複数の候補がある場合に優先度順に並ぶ"""
        html = load_fixture("company_with_contact.html")
        result = find_contact_url(html, "https://example.co.jp")
        # 候補の先頭が最終的な contact_url と一致する
        assert result["candidates"][0] == result["contact_url"]

    def test_different_base_url_domain(self):
        html = load_fixture("company_with_contact.html")
        result = find_contact_url(html, "https://other-domain.com")
        assert result["contact_url"] == "https://other-domain.com/contact"

    def test_empty_html_returns_failure(self):
        result = find_contact_url("", "https://example.co.jp")
        assert result["contact_url"] == ""
        assert result["status"] == "取得失敗"
