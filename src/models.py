from dataclasses import dataclass, field


@dataclass
class CompanyRecord:
    name: str
    url: str = ""
    contact_url: str = ""
    source: str = ""
    status: str = ""  # URL済, 取得失敗, アクセスエラー


@dataclass
class PortalRecord:
    url: str
    name: str = ""
    last_crawled: str = ""  # YYYY-MM-DD
    company_count: int = 0
    status: str = ""  # 未クロール, クロール済み, 完了, エラー
    last_page: int = 0  # ページネーション位置（0=未開始）
    new_count: int = 0  # 前回クロール時の新規企業数
