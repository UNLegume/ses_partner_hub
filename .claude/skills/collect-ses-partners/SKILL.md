---
name: collect-ses-partners
description: SES企業パートナー候補のお問い合わせフォームURLを自動収集し、Google Spreadsheetに統合する。4ステップを順次実行する。`--step N` で個別ステップのみ実行可能。
---

## 環境情報

- スプレッドシートID: 環境変数 `SPREADSHEET_ID` を参照
- シート1 GID: 環境変数 `SHEET1_GID` を参照
- 作業用シート GID: 環境変数 `WORK_SHEET_GID` を参照
- Pythonパス: `.venv/bin/python3`
- CLI: `.venv/bin/python3 -m src`

## 引数の解釈

引数: $ARGUMENTS

- 引数なし → ステップ1〜4を順次実行
- `--step 1` → ステップ1のみ
- `--step 2` → ステップ2のみ
- `--step 3` → ステップ3のみ
- `--step 4` → ステップ4のみ
- `--limit N` → ステップ4でシート1に追加する企業を先頭N件に制限

## ステップ1: ポータルサイト自動探索

**目的**: ポータル管理シートを確認し、未完了ポータルを優先クロール。新規ポータルはGoogle検索で発見する。

フロー:
1. Playwright MCPでポータル管理シートをCSVエクスポート → `/tmp/portal_sheet.csv`
2. Pythonでクロール対象を判定（→ references/cli-reference.md）
3. targets 0件なら: Google検索で新規ポータルを探索
   - 検索クエリ: `SES 企業一覧`, `SES パートナー企業 一覧`, `SES会社 リスト`, `システムエンジニアリングサービス 企業一覧`, `SES企業 まとめ`
   - 判別基準: 複数企業のリスト存在、各企業に個別リンク、SES・IT企業特化
4. targets がある場合: 既存ポータルを優先クロール（ステップ2へ）
5. 新規ポータル発見時: ポータル管理シートに行追加（ステータス: 未クロール）

アクセス間隔: 各検索後 3〜5秒のウェイト

## ステップ2: 企業リスト収集

**目的**: ポータルからSES企業名・URLを収集し、作業用シートに記録する。

フロー:
1. check-portals の結果から crawl_targets を取得（各ターゲットに url, name, last_page, status）
2. Playwright MCPで各ポータルにアクセス
3. HTMLをPythonでパース（→ references/cli-reference.md: scrape / list-sources）
   - 未登録ポータルの場合はAIでHTML構造を解析して企業名・URLを直接抽出
4. last_page > 0 ならそのページから再開（中断復旧）
5. ページネーション検出・全ページ走査
6. 取得データを作業用シートのA列（企業名）・C列（URL）に追記（→ references/spreadsheet-schema.md）
7. ポータル走査完了後、結果を記録（→ references/cli-reference.md: update-portal）
8. エラー発生時（→ references/cli-reference.md: portal-error）
9. 全ポータル処理完了後、ポータル管理データをスプレッドシートに書き戻す

アクセス間隔: 各ページ後 1〜3秒のウェイト

## ステップ3: お問い合わせURL取得

**目的**: 各企業サイトからお問い合わせフォームURLを特定する。

フロー:
1. 作業用シートのC列（企業URL）を読み取り（E列が空の行のみ対象）（→ references/spreadsheet-schema.md）
2. Playwright MCPで各企業サイトにアクセス
3. HTMLをPythonでお問い合わせURL抽出（→ references/cli-reference.md: find-contacts）
4. 結果を作業用シートに記録: D列: お問い合わせURL、E列: `URL済` / `取得失敗` / `アクセスエラー`
5. 複数候補がある場合、AIが最適なものを選択

アクセス間隔: 各サイト後 1〜3秒のウェイト
エラー: タイムアウト/404/403 → E列に「アクセスエラー」、フォーム未検出 → E列に「取得失敗」

## ステップ4: シート統合

**目的**: 作業用シートから重複を除いた新規企業のみをシート1に統合する。

フロー:
1. Playwright MCPで両シートをCSVエクスポート（→ `/tmp/work_sheet.csv`, `/tmp/sheet1.csv`）
2. Pythonでマージプレビュー（→ references/cli-reference.md: merge-preview）
3. プレビュー結果をユーザーに提示し確認を求める
4. 確認後、マージ実行（→ references/cli-reference.md: merge --format tsv）
5. TSV出力をPlaywright MCPでシート1末尾にペースト
6. 追記内容: A列:企業名 / B列:FALSE / C列:URL / D列:お問い合わせURL / E〜G列:空欄

重複判定（→ references/spreadsheet-schema.md）

## 大量データ操作の安定性対策

- セル操作は50〜100行単位のバッチで実行
- 各バッチ間で保存待ちを挟む
- 書き込み失敗時は3回までリトライ
- CSVエクスポート/インポートを優先的に使用

## 進捗報告

各ステップ完了後に以下を報告:
- 処理件数
- エラー件数
- 次のステップの概要
