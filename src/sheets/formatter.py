import dataclasses
import json
from src.models import CompanyRecord, PortalRecord


def to_json(records: list[CompanyRecord], status: str = "success") -> str:
    """JSON形式で出力。統一フォーマット。"""
    return json.dumps(
        {
            "status": status,
            "count": len(records),
            "records": [
                {
                    "name": r.name,
                    "url": r.url,
                    "contact_url": r.contact_url,
                    "source": r.source,
                    "status": r.status,
                }
                for r in records
            ],
            "errors": [],
        },
        ensure_ascii=False,
        indent=2,
    )


def portal_to_json(records: list[PortalRecord], status: str = "success") -> str:
    """ポータル管理シートのレコードをJSON形式で出力。"""
    return json.dumps(
        {
            "status": status,
            "count": len(records),
            "records": [dataclasses.asdict(r) for r in records],
            "errors": [],
        },
        ensure_ascii=False,
        indent=2,
    )


def portal_to_tsv(records: list[PortalRecord]) -> str:
    """ポータル管理シートのレコードをTSV形式で出力（Spreadsheetへのペースト用）。
    列順: ポータルURL\tポータル名\t最終クロール日\t取得企業数\tステータス\t最終ページ\t前回新規数
    """
    lines = []
    for r in records:
        lines.append(
            f"{r.url}\t{r.name}\t{r.last_crawled}\t{r.company_count}\t{r.status}\t{r.last_page}\t{r.new_count}"
        )
    return "\n".join(lines)


def to_tsv(records: list[CompanyRecord]) -> str:
    """TSV形式で出力（Spreadsheetへのペースト用）。
    列順: 企業名\tFALSE\tURL\tお問い合わせURL
    """
    lines = []
    for r in records:
        lines.append(f"{r.name}\tFALSE\t{r.url}\t{r.contact_url}")
    return "\n".join(lines)
