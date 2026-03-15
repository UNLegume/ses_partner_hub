import json
from src.models import CompanyRecord


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


def to_tsv(records: list[CompanyRecord]) -> str:
    """TSV形式で出力（Spreadsheetへのペースト用）。
    列順: 企業名\tFALSE\tURL\tお問い合わせURL
    """
    lines = []
    for r in records:
        lines.append(f"{r.name}\tFALSE\t{r.url}\t{r.contact_url}")
    return "\n".join(lines)
