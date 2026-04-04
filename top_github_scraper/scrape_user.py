import json
import os
from pathlib import Path

from rich import print

from top_github_scraper.utils import (
    SearchGithubUsers,
    UserProfileGetter,
)


def get_top_user_urls(
    keyword: str,
    save_directory: str = ".",
    start_page: int = 1,
    stop_page: int = 50,
):
    """Get the URLs of the repositories pop up when searching for a specific
    keyword on GitHub.

    See PARAMETERs.md for a description of the parameters of this function
    """
    safe_keyword = keyword.replace(" ", "_")
    Path(save_directory).mkdir(parents=True, exist_ok=True)
    save_path = f"{save_directory}/top_user_urls_{safe_keyword}_{start_page}_{stop_page}.json"
    repo_urls = SearchGithubUsers(
        keyword, "followers", start_page, stop_page
    ).search_multiple_pages()
    with open(save_path, "w") as outfile:
        json.dump(repo_urls, outfile)
    return repo_urls


def get_top_users(
    keyword: str,
    start_page: int = 1,
    stop_page: int = 50,
    save_directory: str = ".",
):
    """
    Get the information of the owners and contributors of the repositories pop up when searching for a specific
    keyword on GitHub.

    See PARAMETERs.md for a description of the parameters of this function.
    """
    safe_keyword = keyword.replace(" ", "_")
    full_url_save_path = f"{save_directory}/top_user_urls_{safe_keyword}_{start_page}_{stop_page}.json"
    user_save_path = f"{save_directory}/top_user_info_{safe_keyword}_{start_page}_{stop_page}.csv"
    if not Path(full_url_save_path).exists():
        get_top_user_urls(
            keyword=keyword,
            start_page=start_page,
            stop_page=stop_page,
            save_directory=save_directory,
        )
    with open(full_url_save_path, "r") as infile:
        user_urls = json.load(infile)
        url = "https://api.github.com/users"
        urls = [url + user for user in user_urls]
        top_users = UserProfileGetter(urls).get_all_user_profiles()
        top_users.to_csv(user_save_path)
        return top_users
