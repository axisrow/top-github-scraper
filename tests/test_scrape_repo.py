import json
import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import vcr

from top_github_scraper.scrape_repo import (
    DataProcessor,
    RepoScraper,
    get_top_contributors,
    get_top_repo_urls,
    get_top_repos,
)

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")


class TestGetContributorGeneralInfo:
    def test_appends_one_contributor(self):
        contributors_info = {
            "login": [],
            "url": [],
            "contributions": [],
        }
        contributor = {
            "login": "user1",
            "url": "https://api.github.com/users/user1",
            "contributions": 42,
        }
        RepoScraper._get_contributor_general_info(
            contributors_info, contributor
        )
        assert contributors_info["login"] == ["user1"]
        assert contributors_info["url"] == [
            "https://api.github.com/users/user1"
        ]
        assert contributors_info["contributions"] == [42]

    def test_appends_multiple_contributors(self):
        contributors_info = {
            "login": [],
            "url": [],
            "contributions": [],
        }
        for i in range(3):
            RepoScraper._get_contributor_general_info(
                contributors_info,
                {
                    "login": f"user{i}",
                    "url": f"https://api.github.com/users/user{i}",
                    "contributions": i * 10,
                },
            )
        assert len(contributors_info["login"]) == 3


class TestDataProcessor:
    def test_get_repo_stats_filters_keys(self):
        repo_info = {
            "stargazers_count": 100,
            "forks_count": 50,
            "created_at": "2020-01-01",
            "updated_at": "2021-01-01",
            "contributors": {},
            "other_key": "ignored",
        }
        result = DataProcessor.get_repo_stats(repo_info)
        assert "stargazers_count" in result
        assert "forks_count" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert "contributors" not in result
        assert "other_key" not in result

    def test_process_one_repo(self, sample_repo_info):
        processor = DataProcessor(sample_repo_info)
        result = processor.process_one_repo(sample_repo_info[0])
        assert isinstance(result, pd.DataFrame)
        assert "login" in result.columns
        assert "stargazers_count" in result.columns

    def test_process_returns_dataframe(self, sample_repo_info):
        processor = DataProcessor(sample_repo_info)
        result = processor.process()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2


class TestRepoScraperErrorHandling:
    def test_get_repo_information_bad_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch(
            "top_github_scraper.scrape_repo.requests.get",
            return_value=mock_response,
        ):
            scraper = RepoScraper(["/test/repo"], max_n_top_contributors=5)
            result = scraper._get_repo_information("/test/repo")
            assert result["stargazers_count"] == 0
            assert result["forks_count"] == 0
            assert result["contributors"]["login"] == []

    def test_get_contributors_bad_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch(
            "top_github_scraper.scrape_repo.requests.get",
            return_value=mock_response,
        ):
            scraper = RepoScraper(["/test/repo"], max_n_top_contributors=5)
            result = scraper._get_contributor_repo_of_one_repo(
                "/test/repo"
            )
            assert result == {
                "login": [],
                "url": [],
                "contributions": [],
            }

    def test_get_contributors_empty_page(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch(
            "top_github_scraper.scrape_repo.requests.get",
            return_value=mock_response,
        ):
            scraper = RepoScraper(["/test/repo"], max_n_top_contributors=5)
            result = scraper._get_contributor_repo_of_one_repo(
                "/test/repo"
            )
            assert result["login"] == []


# --- Unit tests with VCR cassettes (recorded responses, no network) ---


class TestRepoScraperVcr:
    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "repo_info.yaml")
    )
    def test_get_repo_information(self):
        scraper = RepoScraper(
            ["/josephmisiti/awesome-machine-learning"],
            max_n_top_contributors=2,
        )
        result = scraper._get_repo_information(
            "/josephmisiti/awesome-machine-learning"
        )
        assert "stargazers_count" in result
        assert "forks_count" in result
        assert "contributors" in result

    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "repo_contributors.yaml")
    )
    def test_get_contributors_of_one_repo(self):
        scraper = RepoScraper(
            ["/josephmisiti/awesome-machine-learning"],
            max_n_top_contributors=3,
        )
        result = scraper._get_contributor_repo_of_one_repo(
            "/josephmisiti/awesome-machine-learning"
        )
        assert "login" in result
        assert "url" in result
        assert "contributions" in result
        assert len(result["login"]) <= 3


class TestPublicFunctionsVcr:
    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "top_repo_urls.yaml")
    )
    def test_get_top_repo_urls(self, tmp_path):
        result = get_top_repo_urls(
            keyword="machine learning",
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, list)
        assert len(result) > 0
        saved_files = list(tmp_path.glob("*.json"))
        assert len(saved_files) == 1

    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "top_repos.yaml")
    )
    def test_get_top_repos(self, tmp_path):
        result = get_top_repos(
            keyword="machine learning",
            max_n_top_contributors=2,
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, list)
        assert len(result) > 0
        assert "stargazers_count" in result[0]

    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "top_contributors.yaml")
    )
    def test_get_top_contributors(self, tmp_path):
        result = get_top_contributors(
            keyword="machine learning",
            max_n_top_contributors=2,
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, pd.DataFrame)
        assert "login" in result.columns


# --- Integration tests (real GitHub API) ---


@pytest.mark.integration
class TestRepoScraperIntegration:
    def test_get_real_repo_information(self):
        scraper = RepoScraper(
            ["/josephmisiti/awesome-machine-learning"],
            max_n_top_contributors=2,
        )
        result = scraper._get_repo_information(
            "/josephmisiti/awesome-machine-learning"
        )
        assert result["stargazers_count"] > 0
        assert "contributors" in result
        assert len(result["contributors"]["login"]) > 0


@pytest.mark.integration
class TestPublicFunctionsIntegration:
    def test_get_top_repo_urls_from_real_api(self, tmp_path):
        result = get_top_repo_urls(
            keyword="machine learning",
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, list)
        assert len(result) > 0
