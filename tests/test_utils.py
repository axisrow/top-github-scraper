import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tests.conftest import vcr
from top_github_scraper.utils import (
    ScrapeGithubUrl,
    UserProfileGetter,
    isnotebook,
)

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")


class TestKeywordToUrl:
    def test_single_word_keyword(self):
        result = ScrapeGithubUrl._keyword_to_url(
            page_num=1,
            keyword="python",
            search_type="Repositories",
            sort_by="stars",
        )
        assert (
            result
            == "https://github.com/search?o=desc&p=1&q=python&s=stars&type=Repositories"
        )

    def test_multi_word_keyword(self):
        result = ScrapeGithubUrl._keyword_to_url(
            page_num=1,
            keyword="machine learning",
            search_type="Users",
            sort_by="followers",
        )
        assert (
            result
            == "https://github.com/search?o=desc&p=1&q=machine+learning&s=followers&type=Users"
        )

    def test_page_number_in_url(self):
        result = ScrapeGithubUrl._keyword_to_url(
            page_num=5,
            keyword="test",
            search_type="Repositories",
            sort_by="",
        )
        assert "p=5" in result

    def test_empty_sort_by(self):
        result = ScrapeGithubUrl._keyword_to_url(
            page_num=1,
            keyword="test",
            search_type="Repositories",
            sort_by="",
        )
        assert "s=&" in result


class TestScrapeGithubUrlInit:
    def test_best_match_sort(self):
        scraper = ScrapeGithubUrl("test", "Repositories", "best_match", 1, 5)
        assert scraper.sort_by == ""

    def test_stars_sort(self):
        scraper = ScrapeGithubUrl("test", "Repositories", "stars", 1, 5)
        assert scraper.sort_by == "stars"

    def test_stores_keyword(self):
        scraper = ScrapeGithubUrl(
            "machine learning", "Repositories", "stars", 1, 5
        )
        assert scraper.keyword == "machine learning"

    def test_stores_page_range(self):
        scraper = ScrapeGithubUrl("test", "Repositories", "stars", 2, 7)
        assert scraper.start_page_num == 2
        assert scraper.stop_page_num == 7


class TestUserProfileGetterFiltering:
    def test_filters_profile_features(self, sample_user_profile):
        getter = UserProfileGetter(
            ["https://api.github.com/users/jakevdp"]
        )

        mock_response = MagicMock()
        mock_response.json.return_value = sample_user_profile

        with patch(
            "top_github_scraper.utils.requests.get",
            return_value=mock_response,
        ):
            result = getter._get_one_user_profile(
                "https://api.github.com/users/jakevdp"
            )

        assert "login" in result
        assert "name" in result
        assert "extra_field" not in result

    def test_all_expected_fields_present(self, sample_user_profile):
        getter = UserProfileGetter(["url"])

        mock_response = MagicMock()
        mock_response.json.return_value = sample_user_profile

        with patch(
            "top_github_scraper.utils.requests.get",
            return_value=mock_response,
        ):
            result = getter._get_one_user_profile("url")

        expected_fields = {
            "login",
            "url",
            "type",
            "name",
            "company",
            "location",
            "email",
            "hireable",
            "bio",
            "public_repos",
            "public_gists",
            "followers",
            "following",
            "twitter_username",
        }
        assert set(result.keys()) == expected_fields


class TestIsNotebook:
    def test_returns_false_in_standard_python(self):
        assert isnotebook() is False

    def test_returns_false_on_name_error(self):
        with patch(
            "top_github_scraper.utils.get_ipython", side_effect=NameError
        ):
            assert isnotebook() is False

    def test_returns_true_for_zmq_shell(self):
        mock_ipython = MagicMock()
        mock_ipython.__class__.__name__ = "ZMQInteractiveShell"
        with patch(
            "top_github_scraper.utils.get_ipython",
            return_value=mock_ipython,
        ):
            assert isnotebook() is True

    def test_returns_false_for_terminal_shell(self):
        mock_ipython = MagicMock()
        mock_ipython.__class__.__name__ = "TerminalInteractiveShell"
        with patch(
            "top_github_scraper.utils.get_ipython",
            return_value=mock_ipython,
        ):
            assert isnotebook() is False


class TestScrapeGithubUrlErrorHandling:
    def test_bad_http_response_returns_empty_list(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "<html></html>"

        with patch(
            "top_github_scraper.utils.requests.get",
            return_value=mock_response,
        ):
            scraper = ScrapeGithubUrl(
                "test", "Repositories", "stars", 1, 2
            )
            result = scraper._scrape_top_repo_url_one_page(1)
            assert isinstance(result, list)
            assert len(result) == 0


# --- Unit tests with VCR cassettes (recorded responses, no network) ---


class TestScrapeGithubUrlVcr:
    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "scrape_one_page.yaml")
    )
    def test_scrape_one_page_returns_urls(self):
        scraper = ScrapeGithubUrl(
            "machine learning", "Repositories", "stars", 1, 2
        )
        urls = scraper._scrape_top_repo_url_one_page(1)
        assert isinstance(urls, list)
        assert len(urls) > 0

    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "scrape_multiple_pages.yaml")
    )
    def test_scrape_multiple_pages(self):
        scraper = ScrapeGithubUrl(
            "machine learning", "Repositories", "stars", 1, 3
        )
        urls = scraper.scrape_top_repo_url_multiple_pages()
        assert isinstance(urls, list)
        assert len(urls) > 0


class TestUserProfileGetterVcr:
    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "user_profile.yaml")
    )
    def test_get_all_user_profiles_returns_dataframe(self):
        urls = [
            "https://api.github.com/users/jakevdp",
            "https://api.github.com/users/fuglede",
        ]
        getter = UserProfileGetter(urls)
        result = getter.get_all_user_profiles()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "login" in result.columns


# --- Integration tests (real GitHub API) ---


@pytest.mark.integration
class TestScrapeGithubUrlIntegration:
    def test_scrape_one_page_from_real_api(self):
        scraper = ScrapeGithubUrl(
            "machine learning", "Repositories", "stars", 1, 2
        )
        urls = scraper._scrape_top_repo_url_one_page(1)
        assert isinstance(urls, list)
        assert len(urls) > 0
        for url in urls:
            assert url.startswith("/")


@pytest.mark.integration
class TestUserProfileGetterIntegration:
    def test_get_real_user_profile(self):
        getter = UserProfileGetter(
            ["https://api.github.com/users/jakevdp"]
        )
        result = getter._get_one_user_profile(
            "https://api.github.com/users/jakevdp"
        )
        assert result["login"] == "jakevdp"
        assert "name" in result
