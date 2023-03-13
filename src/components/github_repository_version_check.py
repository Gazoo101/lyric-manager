# Python
import requests
import json
import logging
from typing import Optional

# 3rd Party
from packaging import version


# 1st Party


class GithubRepositoryVersionCheck():


    @staticmethod
    def _fetch_latest_version_from_github_repo(user: str, repo_name:str):
        api_url = f"https://api.github.com/repos/{user}/{repo_name}/releases/latest"
        response = requests.get(api_url)
        if response.status_code != 200:
            logging.info(f"Error when accessing githib api url: {response.status_code} {response.reason}")
            return None
        
        release_info = json.loads(response.text)
        latest_version = release_info['tag_name']

        return latest_version

    @staticmethod
    def get_newer_version_if_available(version_current: str) -> Optional[str]:
        """ Checks against online version... """

        fetched_version = GithubRepositoryVersionCheck._fetch_latest_version_from_github_repo("Gazoo101", "lyric-manager")

        if version.parse(version_current) < version.parse(fetched_version):
            #logging.warning(f"Current Python version '{version_current}', is below required version '{version_required}'.")
            return fetched_version
        
        return None
