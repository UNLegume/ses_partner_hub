# SES Partner Hub

## アーキテクチャ
- Claude Code（オーケストレーション） + Playwright MCP（ブラウザ操作） + Python src/（データ加工専用）
- I/Oフロー: Playwright取得 → Python加工(stdout JSON) → Claude判断 → Playwright書込
- PythonからSpreadsheetへは直接アクセスしない

## CLI
- エントリポイント: `python3 -m src`
- 全コマンド出力は JSON: `{"status": "success", "count": N, "records": [...], "errors": [...]}`

## テスト
- `python3 -m pytest tests/ -v`
- テスト用HTMLスナップショットは `tests/fixtures/` に配置

## コーディング規約
- Python 3.11+
- dataclass使用（models.py）
- 型ヒント必須
