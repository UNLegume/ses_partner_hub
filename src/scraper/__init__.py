# scraperモジュールをインポートして自動登録を発生させる
from src.scraper import ses_rengo, willof  # noqa: F401

__all__ = ["ses_rengo", "willof"]
