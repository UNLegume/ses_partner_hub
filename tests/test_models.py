import pytest
from src.models import CompanyRecord, PortalRecord


class TestCompanyRecord:
    def test_default_values(self):
        record = CompanyRecord(name="テスト株式会社")
        assert record.name == "テスト株式会社"
        assert record.url == ""
        assert record.contact_url == ""
        assert record.source == ""
        assert record.status == ""

    def test_set_all_fields(self):
        record = CompanyRecord(
            name="テスト株式会社",
            url="https://example.com",
            contact_url="https://example.com/contact",
            source="portal-a",
            status="URL済",
        )
        assert record.name == "テスト株式会社"
        assert record.url == "https://example.com"
        assert record.contact_url == "https://example.com/contact"
        assert record.source == "portal-a"
        assert record.status == "URL済"

    def test_status_values(self):
        for status in ["URL済", "取得失敗", "アクセスエラー"]:
            record = CompanyRecord(name="テスト", status=status)
            assert record.status == status

    def test_name_is_required(self):
        with pytest.raises(TypeError):
            CompanyRecord()  # type: ignore[call-arg]


class TestPortalRecord:
    def test_default_values(self):
        record = PortalRecord(url="https://portal.example.com")
        assert record.url == "https://portal.example.com"
        assert record.name == ""
        assert record.last_crawled == ""
        assert record.company_count == 0
        assert record.status == ""

    def test_set_all_fields(self):
        record = PortalRecord(
            url="https://portal.example.com",
            name="SESポータル",
            last_crawled="2026-03-14",
            company_count=50,
            status="クロール済み",
        )
        assert record.url == "https://portal.example.com"
        assert record.name == "SESポータル"
        assert record.last_crawled == "2026-03-14"
        assert record.company_count == 50
        assert record.status == "クロール済み"

    def test_status_values(self):
        for status in ["クロール済み", "エラー"]:
            record = PortalRecord(url="https://example.com", status=status)
            assert record.status == status

    def test_url_is_required(self):
        with pytest.raises(TypeError):
            PortalRecord()  # type: ignore[call-arg]

    def test_company_count_default_is_int(self):
        record = PortalRecord(url="https://example.com")
        assert isinstance(record.company_count, int)
        assert record.company_count == 0
