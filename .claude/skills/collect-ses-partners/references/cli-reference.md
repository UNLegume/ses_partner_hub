# CLI リファレンス

## 環境

- Pythonパス: `.venv/bin/python3`
- CLI実行: `.venv/bin/python3 -m src`

---

## 全コマンド一覧

| コマンド | 概要 | 主な引数 |
|---|---|---|
| `scrape` | ポータルHTMLから企業リスト抽出 | `--source` (必須) |
| `find-contacts` | 企業サイトHTMLからお問い合わせURL抽出 | `--base-url` (必須) |
| `read-work` | 作業用シートCSV読み取り | `--input-file` (必須) |
| `read-sheet1` | シート1 CSV読み取り | `--input-file` (必須) |
| `merge-preview` | マージプレビュー | `--work-csv`, `--sheet1-csv` (必須) |
| `merge` | マージ実行 | `--work-csv`, `--sheet1-csv` (必須) |
| `check-portals` | クロール対象ポータルの判定 | `--portal-csv` (必須) |
| `update-portal` | ポータルクロール結果の更新 | `--portal-csv`, `--url`, `--company-count`, `--new-count`, `--last-page` (必須) |
| `portal-error` | ポータルのエラー記録 | `--portal-csv`, `--url` (必須) |
| `list-sources` | 登録済みスクレイパーソース一覧 | なし |
| `stats` | 統計情報 | `--work-csv` または `--sheet1-csv` (いずれか必須) |

---

## 各コマンド詳細

### `scrape`
ポータルHTMLから企業リストを抽出する。HTMLはstdinから受け取る。

```
echo "$HTML" | .venv/bin/python3 -m src scrape --source <source_name>
```

出力: `{"status": "success", "count": N, "records": [{"name": "...", "url": "..."}]}`

---

### `find-contacts`
企業サイトHTMLからお問い合わせURLを抽出する。HTMLはstdinから受け取る。

```
echo "$HTML" | .venv/bin/python3 -m src find-contacts --base-url <url>
```

出力: `{"status": "success", "count": 1, "records": [...], "errors": []}`

---

### `read-work`
作業用シートのCSVファイルを読み取りJSONで出力する。

```
.venv/bin/python3 -m src read-work --input-file <csv>
```

---

### `read-sheet1`
シート1のCSVファイルを読み取りJSONで出力する。

```
.venv/bin/python3 -m src read-sheet1 --input-file <csv>
```

---

### `merge-preview`
作業用シートとシート1のマージ結果をプレビューする。

```
.venv/bin/python3 -m src merge-preview \
  --work-csv <f> --sheet1-csv <f> [--limit <n>]
```

---

### `merge`
作業用シートとシート1をマージして出力する。`--format` は `json`（デフォルト）または `tsv`。

```
.venv/bin/python3 -m src merge \
  --work-csv <f> --sheet1-csv <f> [--format json|tsv] [--limit <n>]
```

---

### `check-portals`
ポータル管理シートを読み込み、クロール対象・済みを判定する。

```
.venv/bin/python3 -m src check-portals --portal-csv <csv>
```

出力: `{"status": "success", "total": N, "crawl_targets": N, "completed": N, "error": N, "targets": [...], "skipped": [...]}`

---

### `update-portal`
クロール結果を受け取り、ポータルのステータスを更新する。

```
.venv/bin/python3 -m src update-portal \
  --portal-csv <csv> \
  --url <url> \
  [--name <name>] \
  --company-count <n> \
  --new-count <n> \
  --last-page <n>
```

出力: `{"status": "success", "portal": {...}}`

---

### `portal-error`
ポータルのエラーを記録する。

```
.venv/bin/python3 -m src portal-error \
  --portal-csv <csv> \
  --url <url> \
  [--name <name>]
```

出力: `{"status": "success", "portal": {...}}`

---

### `list-sources`
登録済みスクレイパーソースの一覧を表示する。

```
.venv/bin/python3 -m src list-sources
```

出力: `{"status": "success", "sources": [...]}`

---

### `stats`
作業シート・シート1の統計情報を表示する。いずれか一方のみでも可。

```
.venv/bin/python3 -m src stats [--work-csv <f>] [--sheet1-csv <f>]
```

---

## 各ステップでの実行例

### ステップ1: クロール対象ポータルの確認

```bash
.venv/bin/python3 -m src check-portals --portal-csv /tmp/portal_sheet.csv
```

### ステップ2: ポータルクロール（企業リスト収集）

```bash
# 登録済みスクレイパー確認
.venv/bin/python3 -m src list-sources

# 登録済みスクレイパーでHTMLから企業リスト抽出
echo "$HTML" | .venv/bin/python3 -m src scrape --source <source_name>

# クロール完了後にポータルステータスを更新
.venv/bin/python3 -m src update-portal \
  --portal-csv /tmp/portal_sheet.csv \
  --url "$URL" \
  --name "$NAME" \
  --company-count $COUNT \
  --new-count $NEW \
  --last-page $PAGE

# エラー発生時
.venv/bin/python3 -m src portal-error \
  --portal-csv /tmp/portal_sheet.csv \
  --url "$URL"
```

### ステップ3: お問い合わせURL収集

```bash
echo "$HTML" | .venv/bin/python3 -m src find-contacts --base-url "$COMPANY_URL"
```

### ステップ4: データマージ・集計

```bash
# マージプレビュー
.venv/bin/python3 -m src merge-preview \
  --work-csv /tmp/work_sheet.csv --sheet1-csv /tmp/sheet1.csv [--limit N]

# マージ実行（TSV出力）
.venv/bin/python3 -m src merge \
  --work-csv /tmp/work_sheet.csv --sheet1-csv /tmp/sheet1.csv --format tsv [--limit N]

# 統計情報
.venv/bin/python3 -m src stats \
  --work-csv /tmp/work_sheet.csv --sheet1-csv /tmp/sheet1.csv
```
