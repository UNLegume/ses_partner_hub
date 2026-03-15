from abc import ABC, abstractmethod

from src.models import CompanyRecord


class BaseScraper(ABC):
    """スクレイパーの基底クラス"""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """ソース名（registry登録用）"""
        ...

    @property
    @abstractmethod
    def source_url(self) -> str:
        """ポータルのベースURL"""
        ...

    @abstractmethod
    def parse(self, html: str) -> list[CompanyRecord]:
        """HTMLをパースして企業レコードのリストを返す"""
        ...
