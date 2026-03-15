import csv
from src.models import CompanyRecord, PortalRecord


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


def read_portal_sheet(csv_path: str) -> list[PortalRecord]:
    """ポータル管理シートCSVを読み取り、PortalRecordリストに変換する。

    CSVの列マッピング（ヘッダーベース）:
    - 「ポータルURL」→ url
    - 「ポータル名」→ name
    - 「最終クロール日」→ last_crawled
    - 「取得企業数」→ company_count
    - 「ステータス」→ status
    - 「最終ページ」→ last_page
    - 「前回新規数」→ new_count

    ヘッダー行が存在する前提。ヘッダー名で列を特定する。
    """
    records: list[PortalRecord] = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("ポータルURL", "").strip()
            if not url:
                continue

            try:
                company_count = int(row.get("取得企業数", "0").strip() or "0")
            except ValueError:
                company_count = 0

            try:
                last_page = int(row.get("最終ページ", "0").strip() or "0")
            except ValueError:
                last_page = 0

            try:
                new_count = int(row.get("前回新規数", "0").strip() or "0")
            except ValueError:
                new_count = 0

            records.append(
                PortalRecord(
                    url=url,
                    name=row.get("ポータル名", "").strip(),
                    last_crawled=row.get("最終クロール日", "").strip(),
                    company_count=company_count,
                    status=row.get("ステータス", "").strip(),
                    last_page=last_page,
                    new_count=new_count,
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
