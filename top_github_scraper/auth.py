import logging
import os
import subprocess

from dotenv import load_dotenv

load_dotenv()


def get_github_auth():
    """Returns (username, token) or (None, None)."""
    username = os.getenv("GITHUB_USERNAME")
    token = os.getenv("GITHUB_TOKEN")

    # Fallback: get token from gh CLI
    if not token:
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                token = result.stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

    # Fallback: get username from gh CLI
    if not username and token:
        try:
            result = subprocess.run(
                ["gh", "api", "user", "-q", ".login"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                username = result.stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

    if not token:
        logging.warning(
            "You are using the GitHub API as an unauthenticated user. "
            "Limited to 60 requests/hour. Set GITHUB_USERNAME/GITHUB_TOKEN "
            "in .env or run `gh auth login`."
        )

    return username, token


USERNAME, TOKEN = get_github_auth()


def get_auth():
    """Returns auth tuple for requests, or None if unauthenticated."""
    if TOKEN:
        return (USERNAME or TOKEN, TOKEN)
    return None
