import json

from src.models import CompanyRecord
from src.sheets.formatter import to_json, to_tsv


def make_record(
    name: str = "テスト株式会社",
    url: str = "https://test.co.jp",
    contact_url: str = "https://test.co.jp/contact",
    source: str = "ses_rengo",
    status: str = "URL済",
) -> CompanyRecord:
    return CompanyRecord(
        name=name,
        url=url,
        contact_url=contact_url,
        source=source,
        status=status,
    )


class TestToJson:
    def test_correct_structure(self):
        records = [make_record()]
        result = json.loads(to_json(records))
        assert result["status"] == "success"
        assert result["count"] == 1
        assert isinstance(result["records"], list)
        assert isinstance(result["errors"], list)
        assert result["errors"] == []

    def test_record_fields_in_output(self):
        r = make_record(
            name="株式会社ABC",
            url="https://abc.co.jp",
            contact_url="https://abc.co.jp/form",
            source="willof",
            status="URL済",
        )
        result = json.loads(to_json([r]))
        rec = result["records"][0]
        assert rec["name"] == "株式会社ABC"
        assert rec["url"] == "https://abc.co.jp"
        assert rec["contact_url"] == "https://abc.co.jp/form"
        assert rec["source"] == "willof"
        assert rec["status"] == "URL済"

    def test_count_matches_records(self):
        records = [make_record(), make_record(name="別会社")]
        result = json.loads(to_json(records))
        assert result["count"] == 2
        assert len(result["records"]) == 2

    def test_custom_status(self):
        result = json.loads(to_json([], status="error"))
        assert result["status"] == "error"

    def test_empty_list(self):
        result = json.loads(to_json([]))
        assert result["status"] == "success"
        assert result["count"] == 0
        assert result["records"] == []
        assert result["errors"] == []

    def test_japanese_ensure_ascii_false(self):
        r = make_record(name="日本語企業名")
        raw = to_json([r])
        assert "日本語企業名" in raw


class TestToTsv:
    def test_single_record(self):
        r = make_record(
            name="テスト会社",
            url="https://test.co.jp",
            contact_url="https://test.co.jp/contact",
        )
        result = to_tsv([r])
        assert result == "テスト会社\tFALSE\thttps://test.co.jp\thttps://test.co.jp/contact"

    def test_multiple_records(self):
        records = [
            make_record(name="会社A", url="https://a.co.jp", contact_url="https://a.co.jp/c"),
            make_record(name="会社B", url="https://b.co.jp", contact_url=""),
        ]
        result = to_tsv(records)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "会社A\tFALSE\thttps://a.co.jp\thttps://a.co.jp/c"
        assert lines[1] == "会社B\tFALSE\thttps://b.co.jp\t"

    def test_empty_list(self):
        result = to_tsv([])
        assert result == ""

    def test_format_has_four_columns(self):
        r = make_record()
        result = to_tsv([r])
        columns = result.split("\t")
        assert len(columns) == 4
        assert columns[1] == "FALSE"
