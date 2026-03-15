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
    last_crawled: str = ""
    company_count: int = 0
    status: str = ""  # クロール済み, エラー
