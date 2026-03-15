import json
import os
import tempfile
from argparse import Namespace
from io import StringIO
from unittest.mock import patch

import pytest

from src.cli import build_parser, handle_stats

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
WORK_SHEET_CSV = os.path.join(FIXTURES_DIR, "work_sheet_sample.csv")
SHEET1_CSV = os.path.join(FIXTURES_DIR, "sheet1_sample.csv")

WORK_SHEET_HEADER = "企業名,フォーム送信,URL,お問い合わせURL,URL取得状態,ソース,正規化企業名,重複フラグ\n"
SHEET1_HEADER = "企業名,フォーム送信,URL,お問い合わせURL,面談について,概要,メモ,正規化企業名,正規化URL\n"


def run_stats(*argv) -> dict:
    """CLIパーサー経由で stats コマンドを実行し、JSON出力を返す。"""
    parser = build_parser()
    args = parser.parse_args(["stats", *argv])
    with patch("builtins.print") as mock_print:
        try:
            args.func(args)
        except SystemExit:
            pass
        if mock_print.call_args is None:
            return {}
        return json.loads(mock_print.call_args[0][0])


class TestStatsWorkSheetOnly:
    def test_status_success(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert result["status"] == "success"

    def test_work_sheet_key_present(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert "work_sheet" in result

    def test_sheet1_key_absent(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert "sheet1" not in result

    def test_total_count(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert result["work_sheet"]["total"] == 3

    def test_by_status_url_done(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        # work_sheet_sample.csv: URL済 2件, 取得失敗 1件
        assert result["work_sheet"]["by_status"]["URL済"] == 2

    def test_by_status_fetch_failed(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert result["work_sheet"]["by_status"]["取得失敗"] == 1

    def test_by_source_ses_rengo(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        # work_sheet_sample.csv: ses_rengo 2件, willof 1件
        assert result["work_sheet"]["by_source"]["ses_rengo"] == 2

    def test_by_source_willof(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert result["work_sheet"]["by_source"]["willof"] == 1

    def test_with_contact_url(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        # work_sheet_sample.csv: contact_url あり 2件, なし 1件
        assert result["work_sheet"]["with_contact_url"] == 2

    def test_without_contact_url(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV)
        assert result["work_sheet"]["without_contact_url"] == 1


class TestStatsSheet1Only:
    def test_status_success(self):
        result = run_stats("--sheet1-csv", SHEET1_CSV)
        assert result["status"] == "success"

    def test_sheet1_key_present(self):
        result = run_stats("--sheet1-csv", SHEET1_CSV)
        assert "sheet1" in result

    def test_work_sheet_key_absent(self):
        result = run_stats("--sheet1-csv", SHEET1_CSV)
        assert "work_sheet" not in result

    def test_total_count(self):
        result = run_stats("--sheet1-csv", SHEET1_CSV)
        # sheet1_sample.csv: 2件
        assert result["sheet1"]["total"] == 2

    def test_with_contact_url(self):
        result = run_stats("--sheet1-csv", SHEET1_CSV)
        # sheet1_sample.csv: contact_url あり 2件
        assert result["sheet1"]["with_contact_url"] == 2

    def test_without_contact_url(self):
        result = run_stats("--sheet1-csv", SHEET1_CSV)
        assert result["sheet1"]["without_contact_url"] == 0


class TestStatsBothCsvs:
    def test_status_success(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV, "--sheet1-csv", SHEET1_CSV)
        assert result["status"] == "success"

    def test_both_keys_present(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV, "--sheet1-csv", SHEET1_CSV)
        assert "work_sheet" in result
        assert "sheet1" in result

    def test_work_sheet_total(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV, "--sheet1-csv", SHEET1_CSV)
        assert result["work_sheet"]["total"] == 3

    def test_sheet1_total(self):
        result = run_stats("--work-csv", WORK_SHEET_CSV, "--sheet1-csv", SHEET1_CSV)
        assert result["sheet1"]["total"] == 2


class TestStatsStatusAggregation:
    def test_empty_status_counted_as_unprocessed(self):
        """status が空文字のレコードは「未処理」としてカウントされる。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(WORK_SHEET_HEADER)
            f.write("企業A,FALSE,https://a.co.jp,,, ses_rengo,企業A,FALSE\n")
            f.write("企業B,FALSE,https://b.co.jp,,URL済,ses_rengo,企業B,FALSE\n")
            tmp_path = f.name
        try:
            result = run_stats("--work-csv", tmp_path)
            assert result["work_sheet"]["by_status"].get("未処理", 0) == 1
            assert result["work_sheet"]["by_status"].get("URL済", 0) == 1
        finally:
            os.unlink(tmp_path)

    def test_multiple_statuses(self):
        """複数の status 値が正しく集計される。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(WORK_SHEET_HEADER)
            f.write("企業A,FALSE,https://a.co.jp,,URL済,ses_rengo,企業A,FALSE\n")
            f.write("企業B,FALSE,https://b.co.jp,,取得失敗,ses_rengo,企業B,FALSE\n")
            f.write("企業C,FALSE,https://c.co.jp,,アクセスエラー,willof,企業C,FALSE\n")
            f.write("企業D,FALSE,https://d.co.jp,,,willof,企業D,FALSE\n")
            tmp_path = f.name
        try:
            result = run_stats("--work-csv", tmp_path)
            ws = result["work_sheet"]
            assert ws["by_status"]["URL済"] == 1
            assert ws["by_status"]["取得失敗"] == 1
            assert ws["by_status"]["アクセスエラー"] == 1
            assert ws["by_status"]["未処理"] == 1
            assert ws["total"] == 4
        finally:
            os.unlink(tmp_path)


class TestStatsSourceAggregation:
    def test_source_counts(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(WORK_SHEET_HEADER)
            f.write("企業A,FALSE,https://a.co.jp,,URL済,ses_rengo,企業A,FALSE\n")
            f.write("企業B,FALSE,https://b.co.jp,,URL済,ses_rengo,企業B,FALSE\n")
            f.write("企業C,FALSE,https://c.co.jp,,URL済,new,企業C,FALSE\n")
            tmp_path = f.name
        try:
            result = run_stats("--work-csv", tmp_path)
            assert result["work_sheet"]["by_source"]["ses_rengo"] == 2
            assert result["work_sheet"]["by_source"]["new"] == 1
        finally:
            os.unlink(tmp_path)


class TestStatsContactUrlAggregation:
    def test_contact_url_counts(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(WORK_SHEET_HEADER)
            f.write("企業A,FALSE,https://a.co.jp,https://a.co.jp/contact,URL済,ses_rengo,企業A,FALSE\n")
            f.write("企業B,FALSE,https://b.co.jp,,取得失敗,ses_rengo,企業B,FALSE\n")
            f.write("企業C,FALSE,https://c.co.jp,https://c.co.jp/form,URL済,willof,企業C,FALSE\n")
            tmp_path = f.name
        try:
            result = run_stats("--work-csv", tmp_path)
            assert result["work_sheet"]["with_contact_url"] == 2
            assert result["work_sheet"]["without_contact_url"] == 1
        finally:
            os.unlink(tmp_path)


class TestStatsEmptyCsv:
    def test_empty_work_csv_total_zero(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(WORK_SHEET_HEADER)
            tmp_path = f.name
        try:
            result = run_stats("--work-csv", tmp_path)
            assert result["work_sheet"]["total"] == 0
            assert result["work_sheet"]["by_status"] == {}
            assert result["work_sheet"]["by_source"] == {}
            assert result["work_sheet"]["with_contact_url"] == 0
            assert result["work_sheet"]["without_contact_url"] == 0
        finally:
            os.unlink(tmp_path)

    def test_empty_sheet1_csv_total_zero(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write(SHEET1_HEADER)
            tmp_path = f.name
        try:
            result = run_stats("--sheet1-csv", tmp_path)
            assert result["sheet1"]["total"] == 0
            assert result["sheet1"]["with_contact_url"] == 0
            assert result["sheet1"]["without_contact_url"] == 0
        finally:
            os.unlink(tmp_path)


class TestStatsNoArguments:
    def test_no_csv_returns_error(self):
        args = Namespace(work_csv=None, sheet1_csv=None)
        with patch("builtins.print") as mock_print:
            try:
                handle_stats(args)
            except SystemExit:
                pass
            result = json.loads(mock_print.call_args[0][0])
        assert result["status"] == "error"
        assert "message" in result
