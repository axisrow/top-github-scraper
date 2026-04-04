import json
import os

import pandas as pd
import pytest

from tests.conftest import vcr
from top_github_scraper.scrape_user import get_top_user_urls, get_top_users

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")


# --- Unit tests with VCR cassettes (recorded responses, no network) ---


class TestGetTopUserUrlsVcr:
    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "top_user_urls.yaml")
    )
    def test_scrapes_and_saves_urls(self, tmp_path):
        result = get_top_user_urls(
            keyword="machine learning",
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, list)
        assert len(result) > 0
        saved_files = list(tmp_path.glob("*.json"))
        assert len(saved_files) == 1


class TestGetTopUsersVcr:
    @vcr.use_cassette(
        os.path.join(CASSETTES_DIR, "top_users.yaml")
    )
    def test_returns_dataframe(self, tmp_path):
        user_urls = [
            "/jakevdp",
            "/fuglede",
        ]
        url_file = (
            tmp_path / "top_user_urls_machine_learning_1_2.json"
        )
        url_file.write_text(json.dumps(user_urls))

        result = get_top_users(
            keyword="machine learning",
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, pd.DataFrame)
        assert "login" in result.columns
        assert len(result) == 2
        saved_csvs = list(tmp_path.glob("*.csv"))
        assert len(saved_csvs) == 1


# --- Integration tests (real GitHub API) ---


@pytest.mark.integration
class TestGetTopUserUrlsIntegration:
    def test_scrapes_real_user_urls(self, tmp_path):
        result = get_top_user_urls(
            keyword="machine learning",
            start_page=1,
            stop_page=2,
            save_directory=str(tmp_path),
        )
        assert isinstance(result, list)
        assert len(result) > 0
        for url in result:
            assert url.startswith("/")
