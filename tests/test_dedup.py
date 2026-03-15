"""tests/test_dedup.py — DedupChecker / merge_preview / merge のテスト"""
import os
import pytest

from src.models import CompanyRecord
from src.merge.dedup import DedupChecker, merge_preview, merge

# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
WORK_CSV = os.path.join(FIXTURES_DIR, "work_sheet_for_merge.csv")
SHEET1_CSV = os.path.join(FIXTURES_DIR, "sheet1_sample.csv")


def make_record(name: str, url: str = "", contact_url: str = "", source: str = "", status: str = "") -> CompanyRecord:
    return CompanyRecord(name=name, url=url, contact_url=contact_url, source=source, status=status)


@pytest.fixture
def sheet1_records() -> list[CompanyRecord]:
    """シート1のレコード（sheet1_sample.csv の内容に対応）"""
    return [
        make_record("既存株式会社", url="https://existing.co.jp", contact_url="https://existing.co.jp/contact"),
        make_record("株式会社サンプル", url="https://sample.co.jp", contact_url="https://sample.co.jp/form"),
    ]


@pytest.fixture
def work_records() -> list[CompanyRecord]:
    """作業用シートのレコード（work_sheet_for_merge.csv の内容に対応）"""
    return [
        make_record("株式会社テストA", url="https://test-a.co.jp", contact_url="https://test-a.co.jp/contact", source="ses_rengo", status="URL済"),
        make_record("テストB株式会社", url="https://test-b.co.jp", source="ses_rengo", status="取得失敗"),
        make_record("新規企業C", url="https://new-c.co.jp", contact_url="https://new-c.co.jp/inquiry", source="willof", status="URL済"),
        make_record("株式会社既存", url="https://existing.co.jp", contact_url="https://existing.co.jp/contact", source="ses_rengo", status="URL済"),
        make_record("新規D株式会社", url="https://sample.co.jp", source="willof", status="取得失敗"),
    ]


# ---------------------------------------------------------------------------
# DedupChecker のテスト
# ---------------------------------------------------------------------------

class TestDedupChecker:
    def test_duplicate_by_name(self, sheet1_records):
        """企業名一致で重複判定（「既存株式会社」と「株式会社既存」は正規化後同一）"""
        checker = DedupChecker(sheet1_records)
        record = make_record("株式会社既存", url="https://other.co.jp")
        assert checker.is_duplicate(record) is True

    def test_duplicate_by_url(self, sheet1_records):
        """URL一致で重複判定（企業名が異なっていてもURLが一致すれば重複）"""
        checker = DedupChecker(sheet1_records)
        record = make_record("全く別の会社", url="https://sample.co.jp")
        assert checker.is_duplicate(record) is True

    def test_new_record_not_duplicate(self, sheet1_records):
        """新規レコードは重複と判定されない"""
        checker = DedupChecker(sheet1_records)
        record = make_record("新規企業C", url="https://new-c.co.jp")
        assert checker.is_duplicate(record) is False

    def test_new_record_with_no_url_not_duplicate(self, sheet1_records):
        """URLなしの新規レコードも重複と判定されない"""
        checker = DedupChecker(sheet1_records)
        record = make_record("テストB株式会社", url="https://test-b.co.jp")
        assert checker.is_duplicate(record) is False

    def test_classify_correct_counts(self, sheet1_records, work_records):
        """classify()で5件中3件新規、2件重複に正しく分類される"""
        checker = DedupChecker(sheet1_records)
        new_records, duplicate_records = checker.classify(work_records)
        assert len(new_records) == 3
        assert len(duplicate_records) == 2

    def test_classify_new_names(self, sheet1_records, work_records):
        """新規に分類されるレコードの企業名が正しい"""
        checker = DedupChecker(sheet1_records)
        new_records, _ = checker.classify(work_records)
        new_names = {r.name for r in new_records}
        assert "株式会社テストA" in new_names
        assert "テストB株式会社" in new_names
        assert "新規企業C" in new_names

    def test_classify_duplicate_names(self, sheet1_records, work_records):
        """重複に分類されるレコードの企業名が正しい"""
        checker = DedupChecker(sheet1_records)
        _, duplicate_records = checker.classify(work_records)
        dup_names = {r.name for r in duplicate_records}
        assert "株式会社既存" in dup_names
        assert "新規D株式会社" in dup_names

    def test_empty_sheet1_all_new(self, work_records):
        """空のシート1では全件新規になる"""
        checker = DedupChecker([])
        new_records, duplicate_records = checker.classify(work_records)
        assert len(new_records) == len(work_records)
        assert len(duplicate_records) == 0

    def test_empty_work_records(self, sheet1_records):
        """空の作業用シートでは空リストが返る"""
        checker = DedupChecker(sheet1_records)
        new_records, duplicate_records = checker.classify([])
        assert new_records == []
        assert duplicate_records == []

    def test_duplicate_by_name_exact_match(self, sheet1_records):
        """「既存株式会社」そのままも重複と判定される"""
        checker = DedupChecker(sheet1_records)
        record = make_record("既存株式会社", url="https://other-new.co.jp")
        assert checker.is_duplicate(record) is True

    def test_url_normalization_https_vs_http(self, sheet1_records):
        """http:// と https:// の違いを吸収して重複判定できる"""
        checker = DedupChecker(sheet1_records)
        record = make_record("別会社", url="http://existing.co.jp")
        assert checker.is_duplicate(record) is True

    def test_url_normalization_trailing_slash(self, sheet1_records):
        """末尾スラッシュを吸収して重複判定できる"""
        checker = DedupChecker(sheet1_records)
        record = make_record("別会社", url="https://existing.co.jp/")
        assert checker.is_duplicate(record) is True


# ---------------------------------------------------------------------------
# merge_preview のテスト
# ---------------------------------------------------------------------------

class TestMergePreview:
    def test_returns_correct_structure(self, work_records, sheet1_records):
        """正しい構造（status, total, new_count, duplicate_count, new_records, duplicate_records）が返る"""
        result = merge_preview(work_records, sheet1_records)
        assert result["status"] == "success"
        assert "total" in result
        assert "new_count" in result
        assert "duplicate_count" in result
        assert "new_records" in result
        assert "duplicate_records" in result

    def test_correct_counts(self, work_records, sheet1_records):
        """件数が正しい（total=5, new=3, dup=2）"""
        result = merge_preview(work_records, sheet1_records)
        assert result["total"] == 5
        assert result["new_count"] == 3
        assert result["duplicate_count"] == 2

    def test_new_records_count_matches(self, work_records, sheet1_records):
        """new_records リストの長さが new_count と一致する"""
        result = merge_preview(work_records, sheet1_records)
        assert len(result["new_records"]) == result["new_count"]

    def test_duplicate_records_count_matches(self, work_records, sheet1_records):
        """duplicate_records リストの長さが duplicate_count と一致する"""
        result = merge_preview(work_records, sheet1_records)
        assert len(result["duplicate_records"]) == result["duplicate_count"]

    def test_record_dict_has_required_keys(self, work_records, sheet1_records):
        """各レコード辞書に必要なキーが含まれる"""
        result = merge_preview(work_records, sheet1_records)
        required_keys = {"name", "url", "contact_url", "source", "status"}
        for rec in result["new_records"] + result["duplicate_records"]:
            assert required_keys.issubset(rec.keys())

    def test_empty_work_returns_zero(self, sheet1_records):
        """空の作業用シートでは total=0, new_count=0, duplicate_count=0"""
        result = merge_preview([], sheet1_records)
        assert result["total"] == 0
        assert result["new_count"] == 0
        assert result["duplicate_count"] == 0

    def test_limit_returns_specified_count(self, work_records, sheet1_records):
        """limit=2 で新規レコードが2件のみ返ること"""
        result = merge_preview(work_records, sheet1_records, limit=2)
        assert result["new_count"] == 2
        assert len(result["new_records"]) == 2

    def test_limit_exceeds_new_count_returns_all(self, work_records, sheet1_records):
        """limit=100（新規件数超過）で全新規レコードが返ること"""
        result = merge_preview(work_records, sheet1_records, limit=100)
        assert result["new_count"] == 3
        assert len(result["new_records"]) == 3

    def test_limit_none_returns_all(self, work_records, sheet1_records):
        """limit=None で全新規レコードが返ること（既存動作の確認）"""
        result = merge_preview(work_records, sheet1_records, limit=None)
        assert result["new_count"] == 3
        assert len(result["new_records"]) == 3

    def test_limited_flag_true_when_truncated(self, work_records, sheet1_records):
        """limit指定で切り捨てが発生した場合、limited=True になること"""
        result = merge_preview(work_records, sheet1_records, limit=2)
        assert result["limit"] == 2
        assert result["limited"] is True

    def test_limited_flag_false_when_not_truncated(self, work_records, sheet1_records):
        """limit指定でも切り捨てが発生しない場合、limited=False になること"""
        result = merge_preview(work_records, sheet1_records, limit=100)
        assert result["limit"] == 100
        assert result["limited"] is False

    def test_limited_flag_false_when_limit_none(self, work_records, sheet1_records):
        """limit=None の場合、limited=False になること"""
        result = merge_preview(work_records, sheet1_records, limit=None)
        assert result["limit"] is None
        assert result["limited"] is False


# ---------------------------------------------------------------------------
# merge のテスト
# ---------------------------------------------------------------------------

class TestMerge:
    def test_returns_only_new_records(self, work_records, sheet1_records):
        """新規レコードのみが返る"""
        result = merge(work_records, sheet1_records)
        assert len(result) == 3

    def test_duplicate_not_in_result(self, work_records, sheet1_records):
        """重複レコードが結果に含まれない"""
        result = merge(work_records, sheet1_records)
        result_names = {r.name for r in result}
        assert "株式会社既存" not in result_names
        assert "新規D株式会社" not in result_names

    def test_new_records_in_result(self, work_records, sheet1_records):
        """新規レコードが結果に含まれる"""
        result = merge(work_records, sheet1_records)
        result_names = {r.name for r in result}
        assert "株式会社テストA" in result_names
        assert "テストB株式会社" in result_names
        assert "新規企業C" in result_names

    def test_returns_company_record_instances(self, work_records, sheet1_records):
        """返り値が CompanyRecord のリストである"""
        result = merge(work_records, sheet1_records)
        for r in result:
            assert isinstance(r, CompanyRecord)

    def test_empty_work_returns_empty(self, sheet1_records):
        """空の作業用シートでは空リストが返る"""
        result = merge([], sheet1_records)
        assert result == []

    def test_empty_sheet1_returns_all(self, work_records):
        """空のシート1では全件が返る"""
        result = merge(work_records, [])
        assert len(result) == len(work_records)

    def test_limit_returns_specified_count(self, work_records, sheet1_records):
        """limit=1 で1件のみ返ること"""
        result = merge(work_records, sheet1_records, limit=1)
        assert len(result) == 1

    def test_limit_none_returns_all(self, work_records, sheet1_records):
        """limit=None で全件返ること"""
        result = merge(work_records, sheet1_records, limit=None)
        assert len(result) == 3
