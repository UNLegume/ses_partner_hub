from bs4 import BeautifulSoup
from urllib.parse import urljoin


def find_contact_url(html: str, base_url: str) -> dict:
    """HTMLからお問い合わせURLを抽出する。

    探索優先順位:
    1. ナビゲーション・フッターの「お問い合わせ」「contact」リンクを検出
    2. URLパターンマッチング: /contact, /inquiry, /form, お問い合わせ 等
    3. ページ全体のリンクからパターンマッチ

    Returns:
        {
            "contact_url": "https://...",  # 見つからない場合は空文字
            "status": "URL済" | "取得失敗",
            "candidates": ["url1", "url2", ...],  # 候補一覧（デバッグ用）
        }
    """
    soup = BeautifulSoup(html, "lxml")
    candidates = []

    # パターン定義
    # リンクテキストのパターン（日本語・英語）
    text_patterns = [
        "お問い合わせ", "お問合せ", "お問合わせ",
        "contact", "Contact", "CONTACT",
        "お問い合わせフォーム",
    ]

    # URLパスのパターン
    url_patterns = [
        "/contact", "/inquiry", "/form", "/enquiry",
        "/toiawase", "/otoiawase",
        "contact", "inquiry", "form",
    ]

    # Step 1: nav, header, footer 内のリンクを優先検索
    for area_tag in ["nav", "header", "footer"]:
        for area in soup.find_all(area_tag):
            for link in area.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True).lower()
                full_url = urljoin(base_url, href)

                # テキストマッチ
                for pattern in text_patterns:
                    if pattern.lower() in text:
                        candidates.append({"url": full_url, "priority": 1, "reason": f"nav/footer text match: {pattern}"})

                # URLパターンマッチ
                for pattern in url_patterns:
                    if pattern in href.lower():
                        candidates.append({"url": full_url, "priority": 2, "reason": f"nav/footer url match: {pattern}"})

    # Step 2: ページ全体のリンクからパターンマッチ
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(strip=True).lower()
        full_url = urljoin(base_url, href)

        for pattern in text_patterns:
            if pattern.lower() in text:
                candidates.append({"url": full_url, "priority": 3, "reason": f"page text match: {pattern}"})

        for pattern in url_patterns:
            if pattern in href.lower():
                candidates.append({"url": full_url, "priority": 4, "reason": f"page url match: {pattern}"})

    # 重複除去して優先度順にソート
    seen = set()
    unique_candidates = []
    for c in sorted(candidates, key=lambda x: x["priority"]):
        if c["url"] not in seen:
            seen.add(c["url"])
            unique_candidates.append(c)

    if unique_candidates:
        best = unique_candidates[0]
        return {
            "contact_url": best["url"],
            "status": "URL済",
            "candidates": [c["url"] for c in unique_candidates],
        }

    return {
        "contact_url": "",
        "status": "取得失敗",
        "candidates": [],
    }
