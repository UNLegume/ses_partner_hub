from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.scraper.base import BaseScraper

# スクレイパーの登録・取得
_registry: dict[str, type[BaseScraper]] = {}


def register(scraper_class: type[BaseScraper]) -> type[BaseScraper]:
    """デコレータとして使用"""
    _registry[scraper_class.source_name] = scraper_class
    return scraper_class


def get_scraper(name: str) -> BaseScraper:
    """名前からスクレイパーインスタンスを取得"""
    if name not in _registry:
        raise KeyError(f"Unknown scraper source: '{name}'. Available: {list(_registry.keys())}")
    return _registry[name]()


def list_sources() -> list[str]:
    """登録済みソース名一覧"""
    return list(_registry.keys())
