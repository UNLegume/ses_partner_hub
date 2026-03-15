import csv
from src.models import CompanyRecord


def read_work_sheet(csv_path: str) -> list[CompanyRecord]:
    """作業用シートCSVを読み取り、CompanyRecordリストに変換する。

    CSVの列マッピング（ヘッダーベース）:
    - A列「企業名」→ name
    - C列「URL」→ url
    - D列「お問い合わせURL」→ contact_url
    - E列「URL取得状態」→ status
    - F列「ソース」→ source

    ヘッダー行が存在する前提。ヘッダー名で列を特定する。
    """
    records: list[CompanyRecord] = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("企業名", "").strip()
            if not name:
                continue
            records.append(
                CompanyRecord(
                    name=name,
                    url=row.get("URL", "").strip(),
                    contact_url=row.get("お問い合わせURL", "").strip(),
                    status=row.get("URL取得状態", "").strip(),
                    source=row.get("ソース", "").strip(),
                )
            )
    return records


def read_sheet1(csv_path: str) -> list[CompanyRecord]:
    """シート1 CSVを読み取り、CompanyRecordリストに変換する。

    CSVの列マッピング（ヘッダーベース）:
    - A列「企業名」→ name
    - C列「URL」→ url
    - D列「お問い合わせURL」→ contact_url
    """
    records: list[CompanyRecord] = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("企業名", "").strip()
            if not name:
                continue
            records.append(
                CompanyRecord(
                    name=name,
                    url=row.get("URL", "").strip(),
                    contact_url=row.get("お問い合わせURL", "").strip(),
                )
            )
    return records
