import argparse
import dataclasses
import json
import sys
from typing import Any

import src.scraper  # noqa: F401 — スクレイパー自動登録のためインポート
from src.scraper.registry import get_scraper, list_sources
from src.sheets.reader import read_work_sheet, read_sheet1
from src.sheets.formatter import to_json as sheets_to_json, to_tsv
from src.contacts.finder import find_contact_url
from src.merge.dedup import merge_preview as do_merge_preview, merge as do_merge

NOT_IMPLEMENTED_RESPONSE: dict[str, Any] = {"status": "not_implemented"}


def _output(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False))


def handle_scrape(args: argparse.Namespace) -> None:
    """stdinからHTMLを読み、ポータルHTMLから企業リスト抽出。JSON出力"""
    try:
        scraper = get_scraper(args.source)
    except KeyError as e:
        _output({"status": "error", "message": str(e)})
        sys.exit(1)

    html = sys.stdin.read()
    records = scraper.parse(html)
    _output({
        "status": "success",
        "count": len(records),
        "records": [dataclasses.asdict(r) for r in records],
    })


def handle_find_contacts(args: argparse.Namespace) -> None:
    """stdinからHTMLを読み、企業サイトHTMLからお問い合わせURL抽出。JSON出力"""
    html = sys.stdin.read()
    result = find_contact_url(html, args.base_url)
    _output({
        "status": "success",
        "count": 1,
        "records": [result],
        "errors": [],
    })


def handle_read_work(args: argparse.Namespace) -> None:
    """作業用シートCSV読み取り。JSON出力"""
    records = read_work_sheet(args.input_file)
    print(sheets_to_json(records))


def handle_read_sheet1(args: argparse.Namespace) -> None:
    """シート1 CSV読み取り。JSON出力"""
    records = read_sheet1(args.input_file)
    print(sheets_to_json(records))


def handle_merge_preview(args: argparse.Namespace) -> None:
    """マージプレビュー。JSON出力"""
    work_records = read_work_sheet(args.work_csv)
    sheet1_records = read_sheet1(args.sheet1_csv)
    result = do_merge_preview(work_records, sheet1_records, limit=args.limit)
    _output(result)


def handle_merge(args: argparse.Namespace) -> None:
    """マージ実行。TSV/JSON出力"""
    work_records = read_work_sheet(args.work_csv)
    sheet1_records = read_sheet1(args.sheet1_csv)
    new_records = do_merge(work_records, sheet1_records, limit=args.limit)
    fmt = getattr(args, "format", "json")
    if fmt == "tsv":
        print(to_tsv(new_records))
    else:
        _output({
            "status": "success",
            "count": len(new_records),
            "records": [
                {"name": r.name, "url": r.url, "contact_url": r.contact_url, "source": r.source, "status": r.status}
                for r in new_records
            ],
        })


def handle_list_sources(args: argparse.Namespace) -> None:
    """登録済みスクレイパーソース一覧"""
    sources = list_sources()
    _output({"status": "success", "sources": sources})


def handle_stats(args: argparse.Namespace) -> None:
    """統計情報"""
    work_csv = getattr(args, "work_csv", None)
    sheet1_csv = getattr(args, "sheet1_csv", None)

    if not work_csv and not sheet1_csv:
        _output({"status": "error", "message": "--work-csv または --sheet1-csv のいずれかを指定してください"})
        sys.exit(1)

    result: dict[str, Any] = {"status": "success"}

    if work_csv:
        records = read_work_sheet(work_csv)
        by_status: dict[str, int] = {}
        by_source: dict[str, int] = {}
        with_contact = 0
        without_contact = 0
        for r in records:
            status_key = r.status if r.status else "未処理"
            by_status[status_key] = by_status.get(status_key, 0) + 1
            if r.source:
                by_source[r.source] = by_source.get(r.source, 0) + 1
            if r.contact_url:
                with_contact += 1
            else:
                without_contact += 1
        result["work_sheet"] = {
            "total": len(records),
            "by_status": by_status,
            "by_source": by_source,
            "with_contact_url": with_contact,
            "without_contact_url": without_contact,
        }

    if sheet1_csv:
        records = read_sheet1(sheet1_csv)
        with_contact = sum(1 for r in records if r.contact_url)
        without_contact = len(records) - with_contact
        result["sheet1"] = {
            "total": len(records),
            "with_contact_url": with_contact,
            "without_contact_url": without_contact,
        }

    _output(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ses-partner-hub",
        description="SES企業パートナー候補のフォームURL収集・管理CLIツール",
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # scrape
    scrape_parser = subparsers.add_parser(
        "scrape",
        help="stdinからHTMLを読み、ポータルHTMLから企業リスト抽出。JSON出力",
    )
    scrape_parser.add_argument(
        "--source",
        required=True,
        metavar="<name>",
        help="スクレイパーソース名",
    )
    scrape_parser.set_defaults(func=handle_scrape)

    # find-contacts
    find_contacts_parser = subparsers.add_parser(
        "find-contacts",
        help="stdinからHTMLを読み、企業サイトHTMLからお問い合わせURL抽出。JSON出力",
    )
    find_contacts_parser.add_argument(
        "--base-url",
        required=True,
        metavar="<url>",
        help="企業サイトのベースURL",
    )
    find_contacts_parser.set_defaults(func=handle_find_contacts)

    # read-work
    read_work_parser = subparsers.add_parser(
        "read-work",
        help="作業用シートCSV読み取り。JSON出力",
    )
    read_work_parser.add_argument(
        "--input-file",
        required=True,
        metavar="<csv>",
        help="作業用シートCSVファイルパス",
    )
    read_work_parser.set_defaults(func=handle_read_work)

    # read-sheet1
    read_sheet1_parser = subparsers.add_parser(
        "read-sheet1",
        help="シート1 CSV読み取り。JSON出力",
    )
    read_sheet1_parser.add_argument(
        "--input-file",
        required=True,
        metavar="<csv>",
        help="シート1 CSVファイルパス",
    )
    read_sheet1_parser.set_defaults(func=handle_read_sheet1)

    # merge-preview
    merge_preview_parser = subparsers.add_parser(
        "merge-preview",
        help="マージプレビュー。JSON出力",
    )
    merge_preview_parser.add_argument(
        "--work-csv",
        required=True,
        metavar="<f>",
        help="作業用シートCSVファイルパス",
    )
    merge_preview_parser.add_argument(
        "--sheet1-csv",
        required=True,
        metavar="<f>",
        help="シート1 CSVファイルパス",
    )
    merge_preview_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="<n>",
        help="新規レコードの最大件数（省略時は全件）",
    )
    merge_preview_parser.set_defaults(func=handle_merge_preview)

    # merge
    merge_parser = subparsers.add_parser(
        "merge",
        help="マージ実行。TSV/JSON出力",
    )
    merge_parser.add_argument(
        "--work-csv",
        required=True,
        metavar="<f>",
        help="作業用シートCSVファイルパス",
    )
    merge_parser.add_argument(
        "--sheet1-csv",
        required=True,
        metavar="<f>",
        help="シート1 CSVファイルパス",
    )
    merge_parser.add_argument(
        "--format",
        choices=["json", "tsv"],
        default="json",
        help="出力フォーマット（json or tsv、デフォルト json）",
    )
    merge_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="<n>",
        help="新規レコードの最大件数（省略時は全件）",
    )
    merge_parser.set_defaults(func=handle_merge)

    # list-sources
    list_sources_parser = subparsers.add_parser(
        "list-sources",
        help="登録済みスクレイパーソース一覧",
    )
    list_sources_parser.set_defaults(func=handle_list_sources)

    # stats
    stats_parser = subparsers.add_parser(
        "stats",
        help="統計情報",
    )
    stats_parser.add_argument(
        "--work-csv",
        default=None,
        metavar="<f>",
        help="作業用シートCSVファイルパス",
    )
    stats_parser.add_argument(
        "--sheet1-csv",
        default=None,
        metavar="<f>",
        help="シート1 CSVファイルパス",
    )
    stats_parser.set_defaults(func=handle_stats)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)
