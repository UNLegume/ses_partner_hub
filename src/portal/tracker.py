from datetime import date

from src.models import PortalRecord
from src.normalize import normalize_url


class PortalTracker:
    """ポータルURLの管理。クロール対象の選別とステータス更新。"""

    def __init__(self, portal_records: list[PortalRecord]) -> None:
        """既存のポータル管理データを読み込む。"""
        # 正規化URLをキーにしてレコードを管理
        self._records: dict[str, PortalRecord] = {}
        for record in portal_records:
            key = normalize_url(record.url)
            self._records[key] = record

    def _get_key(self, url: str) -> str:
        return normalize_url(url)

    def should_crawl(self, url: str) -> bool:
        """このURLをクロールすべきかを判定。

        - status == '完了' → False（二度と踏まない）
        - status == 'エラー' → True（リトライ対象）
        - status == 'クロール済み' → True（新規があるかもしれない）
        - 未登録 → True（新規ポータル）
        """
        key = self._get_key(url)
        record = self._records.get(key)
        if record is None:
            return True
        return record.status != "完了"

    def get_start_page(self, url: str) -> int:
        """ページネーション再開位置を返す。未登録なら0。"""
        key = self._get_key(url)
        record = self._records.get(key)
        if record is None:
            return 0
        return record.last_page

    def get_crawl_targets(self) -> list[PortalRecord]:
        """クロール対象のポータルレコードを返す（status != '完了'のもの）。"""
        return [r for r in self._records.values() if r.status != "完了"]

    def update_after_crawl(
        self,
        url: str,
        name: str,
        company_count: int,
        new_count: int,
        last_page: int,
    ) -> PortalRecord:
        """クロール後のステータス更新。

        - new_count == 0 → status = '完了'
        - new_count > 0 → status = 'クロール済み'
        - last_crawled = 今日の日付
        """
        key = self._get_key(url)
        status = "完了" if new_count == 0 else "クロール済み"
        today = date.today().isoformat()

        existing = self._records.get(key)
        if existing is not None:
            existing.name = name or existing.name
            existing.last_crawled = today
            existing.company_count = company_count
            existing.status = status
            existing.last_page = last_page
            existing.new_count = new_count
            return existing

        record = PortalRecord(
            url=url,
            name=name,
            last_crawled=today,
            company_count=company_count,
            status=status,
            last_page=last_page,
            new_count=new_count,
        )
        self._records[key] = record
        return record

    def mark_error(self, url: str, name: str = "") -> PortalRecord:
        """エラー時のステータス更新。"""
        key = self._get_key(url)
        today = date.today().isoformat()

        existing = self._records.get(key)
        if existing is not None:
            existing.name = name or existing.name
            existing.status = "エラー"
            existing.last_crawled = today
            return existing

        record = PortalRecord(
            url=url,
            name=name,
            last_crawled=today,
            status="エラー",
        )
        self._records[key] = record
        return record

    def get_all(self) -> list[PortalRecord]:
        """全ポータルレコードを返す。"""
        return list(self._records.values())

    def get_record(self, url: str) -> PortalRecord | None:
        """URL正規化して既存レコードを検索。"""
        key = self._get_key(url)
        return self._records.get(key)
