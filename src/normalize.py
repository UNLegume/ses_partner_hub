import re


def normalize_company_name(name: str) -> str:
    """企業名を正規化する。

    - 「株式会社」「（株）」「(株)」を除去
    - 全角・半角スペースを除去
    - 小文字に統一

    Spreadsheet関数との対応:
    =SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(A2,"株式会社",""),"（株）",""),"(株)","")," ","")
    ただしPython側ではさらに小文字化する。
    """
    result = name
    result = result.replace("株式会社", "")
    result = result.replace("（株）", "")
    result = result.replace("(株)", "")
    # 全角スペース・半角スペースを除去
    result = result.replace("\u3000", "")
    result = result.replace(" ", "")
    # 小文字に統一
    result = result.lower()
    return result


def normalize_url(url: str) -> str:
    """URLを正規化する。

    - https:// / http:// を除去
    - www. を除去
    - 末尾の / を除去

    Spreadsheet関数との対応:
    =REGEXREPLACE(REGEXREPLACE(REGEXREPLACE(C2,"^https?://",""),"^www[.]",""),"/$","")
    """
    result = url
    # https:// または http:// を除去
    result = re.sub(r"^https?://", "", result)
    # 先頭の www. を除去
    result = re.sub(r"^www\.", "", result)
    # 末尾の / を除去
    result = re.sub(r"/$", "", result)
    return result


def is_same_company(name1: str, name2: str) -> bool:
    """正規化後の企業名が一致するか判定"""
    return normalize_company_name(name1) == normalize_company_name(name2)


def is_same_url(url1: str, url2: str) -> bool:
    """正規化後のURLが一致するか判定"""
    return normalize_url(url1) == normalize_url(url2)
