"""tests/test_portal_tracker.py — PortalTracker の全メソッドのテスト"""
import pytest
from unittest.mock import patch
from datetime import date

from src.models import PortalRecord
from src.portal.tracker import PortalTracker


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def make_portal(
    url: str,
    name: str = "",
    last_crawled: str = "",
    company_count: int = 0,
    status: str = "",
    last_page: int = 0,
    new_count: int = 0,
) -> PortalRecord:
    return PortalRecord(
        url=url,
        name=name,
        last_crawled=last_crawled,
        company_count=company_count,
        status=status,
        last_page=last_page,
        new_count=new_count,
    )


TODAY = date(2026, 3, 16).isoformat()  # テスト基準日


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------

@pytest.fixture
def portal_records() -> list[PortalRecord]:
    return [
        make_portal("https://portal-a.com/", name="ポータルA", status="未クロール"),
        make_portal("https://portal-b.com/", name="ポータルB", status="クロール済み", last_crawled="2026-03-01", company_count=30, last_page=3, new_count=5),
        make_portal("https://portal-c.com/", name="ポータルC", status="完了", last_crawled="2026-03-10", company_count=50, last_page=5, new_count=0),
        make_portal("https://portal-d.com/", name="ポータルD", status="エラー", last_crawled="2026-03-12"),
    ]


@pytest.fixture
def tracker(portal_records) -> PortalTracker:
    return PortalTracker(portal_records)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_loads_all_records(self, tracker, portal_records):
        """初期化時に全レコードが読み込まれる"""
        assert len(tracker.get_all()) == len(portal_records)

    def test_empty_init(self):
        """空リストで初期化しても問題ない"""
        t = PortalTracker([])
        assert tracker is not None
        assert t.get_all() == []

    def test_url_normalized_on_init(self):
        """URLが正規化されてキー管理される（末尾スラッシュ違いは同一）"""
        r1 = make_portal("https://portal-a.com/", status="完了")
        r2 = make_portal("https://portal-a.com", status="完了")
        # 後から追加した r2 が上書きするが、同じキーで1件だけ管理される
        t = PortalTracker([r1, r2])
        assert len(t.get_all()) == 1


# ---------------------------------------------------------------------------
# should_crawl
# ---------------------------------------------------------------------------

class TestShouldCrawl:
    def test_unregistered_url_returns_true(self, tracker):
        """未登録URLは True"""
        assert tracker.should_crawl("https://new-portal.com/") is True

    def test_status_miku_rouru_returns_true(self, tracker):
        """status='未クロール' は True"""
        assert tracker.should_crawl("https://portal-a.com/") is True

    def test_status_crawled_returns_true(self, tracker):
        """status='クロール済み' は True"""
        assert tracker.should_crawl("https://portal-b.com/") is True

    def test_status_error_returns_true(self, tracker):
        """status='エラー' は True（リトライ対象）"""
        assert tracker.should_crawl("https://portal-d.com/") is True

    def test_status_kanryo_returns_false(self, tracker):
        """status='完了' は False"""
        assert tracker.should_crawl("https://portal-c.com/") is False

    def test_url_normalization_trailing_slash(self, tracker):
        """末尾スラッシュの有無を吸収して判定"""
        # portal-c.com は完了
        assert tracker.should_crawl("https://portal-c.com") is False

    def test_url_normalization_http_vs_https(self):
        """http と https を吸収して判定"""
        r = make_portal("https://portal-e.com/", status="完了")
        t = PortalTracker([r])
        assert t.should_crawl("http://portal-e.com/") is False

    def test_url_normalization_www(self):
        """www の有無を吸収して判定"""
        r = make_portal("https://www.portal-f.com/", status="完了")
        t = PortalTracker([r])
        assert t.should_crawl("https://portal-f.com/") is False


# ---------------------------------------------------------------------------
# get_start_page
# ---------------------------------------------------------------------------

class TestGetStartPage:
    def test_unregistered_returns_zero(self, tracker):
        """未登録URLは 0"""
        assert tracker.get_start_page("https://new-portal.com/") == 0

    def test_registered_returns_last_page(self, tracker):
        """登録済みURLは last_page を返す"""
        assert tracker.get_start_page("https://portal-b.com/") == 3

    def test_no_last_page_returns_zero(self, tracker):
        """last_page が 0 のポータルは 0 を返す"""
        assert tracker.get_start_page("https://portal-a.com/") == 0


# ---------------------------------------------------------------------------
# get_crawl_targets
# ---------------------------------------------------------------------------

class TestGetCrawlTargets:
    def test_excludes_completed(self, tracker):
        """status='完了' のポータルは対象外"""
        targets = tracker.get_crawl_targets()
        urls = [r.url for r in targets]
        assert not any("portal-c.com" in u for u in urls)

    def test_includes_non_completed(self, tracker):
        """完了以外のポータルは全て対象"""
        targets = tracker.get_crawl_targets()
        # portal-a（未クロール）, portal-b（クロール済み）, portal-d（エラー）
        assert len(targets) == 3

    def test_empty_tracker_returns_empty(self):
        t = PortalTracker([])
        assert t.get_crawl_targets() == []

    def test_all_completed_returns_empty(self):
        records = [
            make_portal("https://a.com/", status="完了"),
            make_portal("https://b.com/", status="完了"),
        ]
        t = PortalTracker(records)
        assert t.get_crawl_targets() == []


# ---------------------------------------------------------------------------
# update_after_crawl
# ---------------------------------------------------------------------------

class TestUpdateAfterCrawl:
    @patch("src.portal.tracker.date")
    def test_new_count_zero_sets_kanryo(self, mock_date, tracker):
        """new_count=0 → status='完了'"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.update_after_crawl(
            url="https://portal-a.com/",
            name="ポータルA",
            company_count=10,
            new_count=0,
            last_page=2,
        )
        assert result.status == "完了"

    @patch("src.portal.tracker.date")
    def test_new_count_positive_sets_crawled(self, mock_date, tracker):
        """new_count>0 → status='クロール済み'"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.update_after_crawl(
            url="https://portal-a.com/",
            name="ポータルA",
            company_count=10,
            new_count=5,
            last_page=2,
        )
        assert result.status == "クロール済み"

    @patch("src.portal.tracker.date")
    def test_sets_last_crawled_today(self, mock_date, tracker):
        """last_crawled が今日の日付に設定される"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.update_after_crawl(
            url="https://portal-a.com/",
            name="ポータルA",
            company_count=10,
            new_count=3,
            last_page=1,
        )
        assert result.last_crawled == "2026-03-16"

    @patch("src.portal.tracker.date")
    def test_updates_existing_record(self, mock_date, tracker):
        """既存レコードを更新する（新規作成ではない）"""
        mock_date.today.return_value = date(2026, 3, 16)
        tracker.update_after_crawl(
            url="https://portal-b.com/",
            name="ポータルB",
            company_count=40,
            new_count=10,
            last_page=4,
        )
        # get_all で件数が変わっていないこと
        all_records = tracker.get_all()
        portal_b_records = [r for r in all_records if "portal-b.com" in r.url]
        assert len(portal_b_records) == 1
        assert portal_b_records[0].company_count == 40
        assert portal_b_records[0].last_page == 4

    @patch("src.portal.tracker.date")
    def test_creates_new_record_for_unknown_url(self, mock_date, tracker):
        """未登録URLは新規レコードとして追加される"""
        mock_date.today.return_value = date(2026, 3, 16)
        before_count = len(tracker.get_all())
        tracker.update_after_crawl(
            url="https://new-portal.com/",
            name="新規ポータル",
            company_count=20,
            new_count=20,
            last_page=2,
        )
        assert len(tracker.get_all()) == before_count + 1

    @patch("src.portal.tracker.date")
    def test_company_count_and_new_count_saved(self, mock_date, tracker):
        """company_count と new_count が正しく保存される"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.update_after_crawl(
            url="https://portal-a.com/",
            name="ポータルA",
            company_count=25,
            new_count=7,
            last_page=3,
        )
        assert result.company_count == 25
        assert result.new_count == 7
        assert result.last_page == 3

    @patch("src.portal.tracker.date")
    def test_empty_name_keeps_existing_name(self, mock_date, tracker):
        """name が空の場合、既存の name を維持する"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.update_after_crawl(
            url="https://portal-b.com/",
            name="",
            company_count=30,
            new_count=5,
            last_page=3,
        )
        assert result.name == "ポータルB"


# ---------------------------------------------------------------------------
# mark_error
# ---------------------------------------------------------------------------

class TestMarkError:
    @patch("src.portal.tracker.date")
    def test_sets_error_status(self, mock_date, tracker):
        """status が 'エラー' に設定される"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.mark_error("https://portal-a.com/")
        assert result.status == "エラー"

    @patch("src.portal.tracker.date")
    def test_sets_last_crawled_today(self, mock_date, tracker):
        """last_crawled が今日の日付に設定される"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.mark_error("https://portal-a.com/")
        assert result.last_crawled == "2026-03-16"

    @patch("src.portal.tracker.date")
    def test_creates_new_record_for_unknown_url(self, mock_date, tracker):
        """未登録URLは新規エラーレコードとして追加される"""
        mock_date.today.return_value = date(2026, 3, 16)
        before_count = len(tracker.get_all())
        tracker.mark_error("https://unknown-portal.com/")
        assert len(tracker.get_all()) == before_count + 1

    @patch("src.portal.tracker.date")
    def test_name_set_when_provided(self, mock_date, tracker):
        """name を指定した場合、name が設定される"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.mark_error("https://unknown-portal.com/", name="不明ポータル")
        assert result.name == "不明ポータル"

    @patch("src.portal.tracker.date")
    def test_empty_name_keeps_existing_name(self, mock_date, tracker):
        """既存レコードで name 未指定の場合、既存の name を維持する"""
        mock_date.today.return_value = date(2026, 3, 16)
        result = tracker.mark_error("https://portal-b.com/")
        assert result.name == "ポータルB"


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------

class TestGetAll:
    def test_returns_all_records(self, tracker, portal_records):
        """全レコードを返す"""
        assert len(tracker.get_all()) == len(portal_records)

    def test_returns_list_of_portal_records(self, tracker):
        """PortalRecord のリストを返す"""
        for r in tracker.get_all():
            assert isinstance(r, PortalRecord)

    def test_empty_returns_empty_list(self):
        t = PortalTracker([])
        assert t.get_all() == []


# ---------------------------------------------------------------------------
# get_record
# ---------------------------------------------------------------------------

class TestGetRecord:
    def test_found_by_url(self, tracker):
        """登録済みURLでレコードを取得できる"""
        record = tracker.get_record("https://portal-a.com/")
        assert record is not None
        assert record.name == "ポータルA"

    def test_not_found_returns_none(self, tracker):
        """未登録URLは None を返す"""
        assert tracker.get_record("https://not-exist.com/") is None

    def test_url_normalization_trailing_slash(self, tracker):
        """末尾スラッシュの有無を吸収して検索できる"""
        record = tracker.get_record("https://portal-b.com")
        assert record is not None
        assert record.name == "ポータルB"

    def test_url_normalization_http_vs_https(self):
        """http と https を吸収して検索できる"""
        r = make_portal("https://portal-g.com/", name="ポータルG", status="完了")
        t = PortalTracker([r])
        result = t.get_record("http://portal-g.com/")
        assert result is not None
        assert result.name == "ポータルG"

    def test_url_normalization_www(self):
        """www の有無を吸収して検索できる"""
        r = make_portal("https://www.portal-h.com/", name="ポータルH", status="未クロール")
        t = PortalTracker([r])
        result = t.get_record("https://portal-h.com/")
        assert result is not None
        assert result.name == "ポータルH"
