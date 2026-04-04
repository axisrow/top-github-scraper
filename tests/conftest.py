import os

import pytest

import vcr


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set fake credentials if real ones are not configured."""
    if not os.getenv("GITHUB_USERNAME"):
        monkeypatch.setenv("GITHUB_USERNAME", "test_user")
    if not os.getenv("GITHUB_TOKEN"):
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")


CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")

RECORD_MODE = os.getenv("VCR_RECORD_MODE", "none")


@pytest.fixture
def vcr_instance():
    """Returns a configured VCR instance."""
    return vcr.VCR(
        cassette_library_dir=CASSETTES_DIR,
        record_mode=RECORD_MODE,
        match_on=["uri", "method"],
        filter_headers=["authorization"],
    )


@pytest.fixture
def sample_repo_urls():
    return [
        "/josephmisiti/awesome-machine-learning",
        "/scikit-learn/scikit-learn",
    ]


@pytest.fixture
def sample_user_urls():
    return [
        "https://api.github.com/users/jakevdp",
        "https://api.github.com/users/fuglede",
    ]


@pytest.fixture
def sample_repo_info():
    """Sample data returned by RepoScraper."""
    return [
        {
            "stargazers_count": 50000,
            "forks_count": 10000,
            "contributors": {
                "login": ["user1", "user2"],
                "url": [
                    "https://api.github.com/users/user1",
                    "https://api.github.com/users/user2",
                ],
                "contributions": [100, 50],
            },
        }
    ]


@pytest.fixture
def sample_contributor_page():
    """Sample GitHub API /contributors response."""
    return [
        {
            "login": "user1",
            "url": "https://api.github.com/users/user1",
            "contributions": 100,
        },
        {
            "login": "user2",
            "url": "https://api.github.com/users/user2",
            "contributions": 50,
        },
        {
            "login": "user3",
            "url": "https://api.github.com/users/user3",
            "contributions": 25,
        },
    ]


@pytest.fixture
def sample_user_profile():
    """Sample GitHub API /users/username response."""
    return {
        "login": "jakevdp",
        "url": "https://api.github.com/users/jakevdp",
        "type": "User",
        "name": "Jake VanderPlas",
        "company": "Google",
        "location": "Seattle, WA",
        "email": None,
        "hireable": None,
        "bio": "Data scientist",
        "public_repos": 100,
        "public_gists": 50,
        "followers": 5000,
        "following": 100,
        "twitter_username": None,
        "extra_field": "should_be_filtered",
    }
