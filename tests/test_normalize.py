import pytest
from src.normalize import normalize_company_name, normalize_url, is_same_company, is_same_url


# --- normalize_company_name ---

class TestNormalizeCompanyName:
    def test_prefix_kabushiki_gaisha(self):
        assert normalize_company_name("株式会社テスト") == "テスト"

    def test_suffix_kabushiki_gaisha(self):
        assert normalize_company_name("テスト株式会社") == "テスト"

    def test_prefix_kabu_fullwidth(self):
        assert normalize_company_name("（株）テスト") == "テスト"

    def test_prefix_kabu_halfwidth(self):
        assert normalize_company_name("(株)テスト") == "テスト"

    def test_fullwidth_space_removal(self):
        # 全角スペース除去
        assert normalize_company_name("テスト\u3000会社") == "テスト会社"

    def test_halfwidth_space_removal(self):
        # 半角スペース除去
        assert normalize_company_name("テスト 会社") == "テスト会社"

    def test_lowercase_and_space_removal(self):
        # 小文字化+スペース除去
        assert normalize_company_name("ABC Company") == "abccompany"

    def test_kabushiki_with_space(self):
        assert normalize_company_name("株式会社 テスト") == "テスト"

    def test_empty_string(self):
        assert normalize_company_name("") == ""

    def test_no_special_suffix(self):
        assert normalize_company_name("テストシステムズ") == "テストシステムズ"

    def test_mixed_case(self):
        assert normalize_company_name("Test Inc") == "testinc"

    def test_multiple_spaces(self):
        assert normalize_company_name("テスト  会社") == "テスト会社"


# --- normalize_url ---

class TestNormalizeUrl:
    def test_https(self):
        assert normalize_url("https://example.com") == "example.com"

    def test_http(self):
        assert normalize_url("http://example.com") == "example.com"

    def test_https_www(self):
        assert normalize_url("https://www.example.com") == "example.com"

    def test_trailing_slash(self):
        assert normalize_url("https://example.com/") == "example.com"

    def test_https_www_trailing_slash(self):
        assert normalize_url("https://www.example.com/") == "example.com"

    def test_http_www_with_path_trailing_slash(self):
        assert normalize_url("http://www.example.com/path/") == "example.com/path"

    def test_already_normalized(self):
        assert normalize_url("example.com") == "example.com"

    def test_with_path(self):
        assert normalize_url("https://example.com/contact") == "example.com/contact"

    def test_empty_string(self):
        assert normalize_url("") == ""

    def test_no_trailing_slash_preserved(self):
        # パスが存在する場合、末尾スラッシュのみ除去
        assert normalize_url("https://example.com/path/to/page") == "example.com/path/to/page"


# --- is_same_company ---

class TestIsSameCompany:
    def test_same_with_prefix_and_suffix(self):
        assert is_same_company("株式会社テスト", "テスト株式会社") is True

    def test_same_with_case_and_space(self):
        # スペース除去+小文字: "abc company" -> "abccompany"
        assert is_same_company("ABC Company", "abccompany") is True

    def test_different_companies(self):
        assert is_same_company("テスト", "サンプル") is False

    def test_same_without_normalization_needed(self):
        assert is_same_company("テスト", "テスト") is True

    def test_different_with_kabu(self):
        assert is_same_company("株式会社テスト", "サンプル株式会社") is False


# --- is_same_url ---

class TestIsSameUrl:
    def test_https_vs_http_with_trailing_slash(self):
        assert is_same_url("https://example.com", "http://example.com/") is True

    def test_https_www_vs_bare(self):
        assert is_same_url("https://www.example.com", "example.com") is True

    def test_different_domains(self):
        assert is_same_url("https://example.com", "https://other.com") is False

    def test_same_normalized(self):
        assert is_same_url("example.com", "example.com") is True

    def test_http_with_path_vs_https_with_path(self):
        assert is_same_url("http://example.com/contact", "https://example.com/contact") is True
