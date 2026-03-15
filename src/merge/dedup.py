from src.models import CompanyRecord
from src.normalize import normalize_company_name, normalize_url


class DedupChecker:
    """重複チェッカー。シート1のデータを保持し、作業用シートのレコードと照合する。"""

    def __init__(self, sheet1_records: list[CompanyRecord]):
        """シート1のレコードから正規化済みの名前・URLのセットを構築する。"""
        self._names: set[str] = set()
        self._urls: set[str] = set()
        for r in sheet1_records:
            normalized_name = normalize_company_name(r.name)
            if normalized_name:
                self._names.add(normalized_name)
            normalized_url = normalize_url(r.url)
            if normalized_url:
                self._urls.add(normalized_url)

    def is_duplicate(self, record: CompanyRecord) -> bool:
        """レコードがシート1に重複するか判定する（OR条件）。
        - 正規化企業名が既存セットに含まれる → True
        - 正規化URLが既存セットに含まれる → True
        """
        normalized_name = normalize_company_name(record.name)
        if normalized_name and normalized_name in self._names:
            return True
        normalized_url = normalize_url(record.url)
        if normalized_url and normalized_url in self._urls:
            return True
        return False

    def classify(self, work_records: list[CompanyRecord]) -> tuple[list[CompanyRecord], list[CompanyRecord]]:
        """作業用シートのレコードを新規と重複に分類する。

        Returns:
            (new_records, duplicate_records) のタプル
        """
        new_records = []
        duplicate_records = []
        for r in work_records:
            if self.is_duplicate(r):
                duplicate_records.append(r)
            else:
                new_records.append(r)
        return new_records, duplicate_records


def merge_preview(work_records: list[CompanyRecord], sheet1_records: list[CompanyRecord], limit: int | None = None) -> dict:
    """マージプレビュー。新規/重複の分類結果を返す。

    Args:
        work_records: 作業用シートのレコード
        sheet1_records: シート1のレコード
        limit: 新規レコードの最大件数。None の場合は全件返す。

    Returns:
        {
            "status": "success",
            "total": N,
            "new_count": N,
            "duplicate_count": N,
            "new_records": [...],
            "duplicate_records": [...],
            "limit": N or None,
            "limited": true/false,
        }
    """
    checker = DedupChecker(sheet1_records)
    new_records, duplicate_records = checker.classify(work_records)
    all_new_count = len(new_records)
    if limit is not None:
        new_records = new_records[:limit]
    limited = limit is not None and len(new_records) < all_new_count
    return {
        "status": "success",
        "total": len(work_records),
        "new_count": len(new_records),
        "duplicate_count": len(duplicate_records),
        "new_records": [
            {"name": r.name, "url": r.url, "contact_url": r.contact_url, "source": r.source, "status": r.status}
            for r in new_records
        ],
        "duplicate_records": [
            {"name": r.name, "url": r.url, "contact_url": r.contact_url, "source": r.source, "status": r.status}
            for r in duplicate_records
        ],
        "limit": limit,
        "limited": limited,
    }


def merge(work_records: list[CompanyRecord], sheet1_records: list[CompanyRecord], limit: int | None = None) -> list[CompanyRecord]:
    """マージ実行。新規レコードのみを返す。

    Args:
        work_records: 作業用シートのレコード
        sheet1_records: シート1のレコード
        limit: 新規レコードの最大件数。None の場合は全件返す。
    """
    checker = DedupChecker(sheet1_records)
    new_records, _ = checker.classify(work_records)
    if limit is not None:
        new_records = new_records[:limit]
    return new_records
