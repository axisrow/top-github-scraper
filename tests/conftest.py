import os

import pytest
import vcr as vcrpy

CASSETTES_DIR = os.path.join(os.path.dirname(__file__), "cassettes")

vcr = vcrpy.VCR(
    cassette_library_dir=CASSETTES_DIR,
    record_mode="none",
    match_on=["uri", "method"],
    filter_headers=["authorization"],
)


def pytest_addoption(parser):
    parser.addoption(
        "--record-vcr",
        action="store_true",
        help="Record new VCR cassettes instead of using recorded ones",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: hit real GitHub API (deselected by default)"
    )


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch, request):
    """Set fake credentials for unit tests."""
    if "integration" in request.keywords:
        return
    if not os.getenv("GITHUB_USERNAME"):
        monkeypatch.setenv("GITHUB_USERNAME", "test_user")
    if not os.getenv("GITHUB_TOKEN"):
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")


@pytest.fixture
def cassettes_dir():
    return CASSETTES_DIR


@pytest.fixture
def record_vcr(request):
    return request.config.getoption("--record-vcr", default=False)


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
