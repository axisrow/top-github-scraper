# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest tests/

# Run a single test
poetry run pytest tests/test_utils.py::test_keyword_to_url

# Format code
poetry run black .
poetry run isort .
poetry run flake8 .

# Run the example
poetry run python example.py
```

Pre-commit hooks (black, flake8, isort) run automatically on `git commit` after `pre-commit install`.

## Environment Setup

Create a `.env` file with GitHub credentials (unauthenticated requests are limited to 60/hour):

```
GITHUB_USERNAME=yourusername
GITHUB_TOKEN=yourtoken
```

## Architecture

The package exposes five public functions via `top_github_scraper/__init__.py`:
- `get_top_repo_urls` / `get_top_repos` / `get_top_contributors` → `scrape_repo.py`
- `get_top_user_urls` / `get_top_users` → `scrape_user.py`

**Data flow:** `ScrapeGithubUrl` (BeautifulSoup scrapes GitHub search HTML) → `RepoScraper` (GitHub API fetches repo stats + contributors) → `DataProcessor` (pandas merges data) → `UserProfileGetter` (GitHub API fetches full user profiles) → CSV/JSON output.

### Key classes in `utils.py`
- **`ScrapeGithubUrl`** — constructs GitHub search URLs and scrapes repo/user paths from HTML
- **`UserProfileGetter`** — fetches user profiles from the GitHub API (`/users/{login}`)

### Key classes in `scrape_repo.py`
- **`RepoScraper`** — wraps GitHub API calls for repo stats and contributor lists
- **`DataProcessor`** — merges contributor data across repos using pandas

### Output files
All outputs are written to the working directory (`.json` and `.csv` are gitignored):
- `top_repo_urls_{keyword}_{start}_{stop}.json`
- `top_repo_info_{keyword}_{start}_{stop}.json`
- `top_contributor_info_{keyword}_{start}_{stop}.csv`
- `top_user_info_{keyword}_{start}_{stop}.csv`

## Code Style

- Line length: 79 (black + flake8)
- isort with trailing comma style (multi-line output mode 3)
- Flake8 ignores: E203, E266, E501, W503, F403, F401; max complexity 18

## Notes

- The `html/` folder contains auto-generated pdoc3 documentation — do not index it.
- `isnotebook()` in `utils.py` detects Jupyter environment to choose between `tqdm` and `tqdm.notebook` progress bars.
