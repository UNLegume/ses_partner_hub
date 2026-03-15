import os
import tempfile

import pytest

from src.sheets.reader import read_work_sheet, read_sheet1

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
WORK_SHEET_CSV = os.path.join(FIXTURES_DIR, "work_sheet_sample.csv")
SHEET1_CSV = os.path.join(FIXTURES_DIR, "sheet1_sample.csv")


class TestReadWorkSheet:
    def test_returns_three_records(self):
        records = read_work_sheet(WORK_SHEET_CSV)
        assert len(records) == 3

    def test_first_record_fields(self):
        records = read_work_sheet(WORK_SHEET_CSV)
        r = records[0]
        assert r.name == "株式会社テストA"
        assert r.url == "https://test-a.co.jp"
        assert r.contact_url == "https://test-a.co.jp/contact"
        assert r.status == "URL済"
        assert r.source == "ses_rengo"

    def test_second_record_empty_contact_url(self):
        records = read_work_sheet(WORK_SHEET_CSV)
        r = records[1]
        assert r.name == "テストB株式会社"
        assert r.url == "https://test-b.co.jp"
        assert r.contact_url == ""
        assert r.status == "取得失敗"
        assert r.source == "ses_rengo"

    def test_third_record_fields(self):
        records = read_work_sheet(WORK_SHEET_CSV)
        r = records[2]
        assert r.name == "（株）テストC"
        assert r.url == "https://test-c.co.jp"
        assert r.contact_url == "https://test-c.co.jp/inquiry"
        assert r.status == "URL済"
        assert r.source == "willof"

    def test_empty_csv_returns_empty_list(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write("企業名,フォーム送信,URL,お問い合わせURL,URL取得状態,ソース,正規化企業名,重複フラグ\n")
            tmp_path = f.name
        try:
            records = read_work_sheet(tmp_path)
            assert records == []
        finally:
            os.unlink(tmp_path)

    def test_bom_csv_reads_correctly(self):
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
        ) as f:
            content = (
                "企業名,フォーム送信,URL,お問い合わせURL,URL取得状態,ソース,正規化企業名,重複フラグ\n"
                "BOM企業,FALSE,https://bom.co.jp,,URL済,test,BOM企業,FALSE\n"
            )
            f.write(b"\xef\xbb\xbf" + content.encode("utf-8"))
            tmp_path = f.name
        try:
            records = read_work_sheet(tmp_path)
            assert len(records) == 1
            assert records[0].name == "BOM企業"
            assert records[0].url == "https://bom.co.jp"
        finally:
            os.unlink(tmp_path)


class TestReadSheet1:
    def test_returns_two_records(self):
        records = read_sheet1(SHEET1_CSV)
        assert len(records) == 2

    def test_first_record_fields(self):
        records = read_sheet1(SHEET1_CSV)
        r = records[0]
        assert r.name == "既存株式会社"
        assert r.url == "https://existing.co.jp"
        assert r.contact_url == "https://existing.co.jp/contact"

    def test_second_record_fields(self):
        records = read_sheet1(SHEET1_CSV)
        r = records[1]
        assert r.name == "株式会社サンプル"
        assert r.url == "https://sample.co.jp"
        assert r.contact_url == "https://sample.co.jp/form"

    def test_empty_csv_returns_empty_list(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", encoding="utf-8", delete=False
        ) as f:
            f.write("企業名,フォーム送信,URL,お問い合わせURL,面談について,概要,メモ,正規化企業名,正規化URL\n")
            tmp_path = f.name
        try:
            records = read_sheet1(tmp_path)
            assert records == []
        finally:
            os.unlink(tmp_path)

    def test_bom_csv_reads_correctly(self):
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv", delete=False
        ) as f:
            content = (
                "企業名,フォーム送信,URL,お問い合わせURL,面談について,概要,メモ,正規化企業名,正規化URL\n"
                "BOM株式会社,FALSE,https://bom-sheet1.co.jp,https://bom-sheet1.co.jp/contact,,,,BOM,bom-sheet1.co.jp\n"
            )
            f.write(b"\xef\xbb\xbf" + content.encode("utf-8"))
            tmp_path = f.name
        try:
            records = read_sheet1(tmp_path)
            assert len(records) == 1
            assert records[0].name == "BOM株式会社"
            assert records[0].url == "https://bom-sheet1.co.jp"
        finally:
            os.unlink(tmp_path)
