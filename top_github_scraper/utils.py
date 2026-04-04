import logging
from dataclasses import dataclass
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from IPython import get_ipython
from rich import print
from rich.progress import track
from tqdm import tqdm

from top_github_scraper.auth import get_auth

SKIP_PATHS = {
    "/search",
    "/topics",
    "/settings",
    "/pricing",
    "/features",
    "/enterprise",
    "/sponsors",
    "/explore",
    "/trending",
    "/marketplace",
    "/notifications",
    "/new",
    "/orgs",
    "/login",
    "/signup",
    "/join",
    "/security",
    "/about",
}


def _is_repo_link(href):
    return (
        href.startswith("/")
        and not href.startswith("//")
        and href.count("/") == 2
        and not any(href.startswith(s) for s in SKIP_PATHS)
    )


def _is_user_link(href):
    return (
        href.startswith("/")
        and not href.startswith("//")
        and href.count("/") == 1
        and len(href) > 1
        and not any(href.startswith(s) for s in SKIP_PATHS)
    )


class ScrapeGithubUrl:
    """Scrape top Github urls based on a certain keyword and type

    Parameters
    -------
    keyword: str
        keyword to search on Github
    search_type: str
        whether to search for User or Repositories
    sort_by: str
        sort by best match or most stars, by default 'best_match', which will sort by best match.
        Use 'stars' to sort by most stars.
    start_page_num: int
        page number to start scraping. The default is 0
    stop_page_num: int
        page number to stop scraping

    Returns
    -------
    List[str]
    """

    def __init__(
        self,
        keyword: str,
        search_type: str,
        sort_by: str,
        start_page_num: int,
        stop_page_num: int,
    ):
        self.keyword = keyword
        self.type = search_type
        self.start_page_num = start_page_num
        self.stop_page_num = stop_page_num
        if sort_by == "best_match":
            self.sort_by = ""
        else:
            self.sort_by = sort_by

    @staticmethod
    def _keyword_to_url(
        page_num: int, keyword: str, search_type: str, sort_by: str
    ):
        """Change keyword to a url"""
        keyword_no_space = ("+").join(keyword.split(" "))
        return f"https://github.com/search?o=desc&p={str(page_num)}&q={keyword_no_space}&s={sort_by}&type={search_type}"

    def _scrape_top_repo_url_one_page(self, page_num: int):
        """Scrape urls of top Github repositories in 1 page"""
        url = self._keyword_to_url(
            page_num, self.keyword, search_type=self.type, sort_by=self.sort_by
        )
        page = requests.get(url, auth=get_auth())
        if page.status_code != 200:
            print(
                f"Bad HTTP Response from: {url}. Got an HTTP response of: {page.status_code}.\n Please confirm this URL is valid."
            )

        soup = BeautifulSoup(page.text, "html.parser")
        a_tags = soup.find_all("a", href=True)

        if self.type == "Repositories":
            urls = [a.get("href") for a in a_tags if _is_repo_link(a["href"])]
        elif self.type == "Users":
            urls = [a.get("href") for a in a_tags if _is_user_link(a["href"])]
        else:
            urls = []

        return list(dict.fromkeys(urls))

    def scrape_top_repo_url_multiple_pages(self):
        """Scrape urls of top Github repositories in multiple pages"""
        urls = []
        if isnotebook():
            for page_num in tqdm(
                range(self.start_page_num, self.stop_page_num),
                desc="Scraping top GitHub URLs...",
            ):
                urls.extend(self._scrape_top_repo_url_one_page(page_num))
        else:
            for page_num in track(
                range(self.start_page_num, self.stop_page_num),
                description="Scraping top GitHub URLs...",
            ):
                urls.extend(self._scrape_top_repo_url_one_page(page_num))
        return urls


class UserProfileGetter:
    """Get the information from users' homepage"""

    def __init__(self, urls: List[str]) -> None:
        self.urls = urls
        # Comment out the features that you dont want to show up in the final report.
        self.profile_features = [
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
        ]

    def _get_one_user_profile(self, profile_url: str):
        profile = requests.get(profile_url, auth=get_auth()).json()
        return {
            key: val
            for key, val in profile.items()
            if key in self.profile_features
        }

    def get_all_user_profiles(self):

        if isnotebook():
            all_contributors = [
                self._get_one_user_profile(url)
                for url in tqdm(
                    self.urls, desc="Scraping top GitHub profiles..."
                )
            ]
        else:
            all_contributors = [
                self._get_one_user_profile(url)
                for url in track(
                    self.urls, description="Scraping top GitHub profiles..."
                )
            ]
        all_contributors_df = pd.DataFrame(all_contributors).reset_index(
            drop=True
        )

        return all_contributors_df


def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter
