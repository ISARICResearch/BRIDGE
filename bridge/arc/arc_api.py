from os import getenv

import pandas as pd
import requests
from requests.exceptions import RequestException

from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True


class ArcApiClientError(Exception):
    pass


class ArcApiClient:
    def __init__(self) -> None:
        if getenv("ENV") == "development":
            self.environment = "development"
        else:
            self.environment = "production"

        self.base_url_api: str = "https://api.github.com/repos/ISARICResearch"
        self.base_url_raw_content: str = (
            "https://raw.githubusercontent.com/ISARICResearch"
        )

    @staticmethod
    def _get_api_response(data_url: str) -> dict:
        logger.info(
            "GITHUB_TOKEN is set"
            if getenv("GITHUB_TOKEN")
            else "GITHUB_TOKEN is not set. Making unauthenticated request"
        )

        # Use GITHUB_TOKEN if it exists; otherwise, make unauthenticated request
        # Unauthenticated requests are limited to 60 requests per hour
        github_token = getenv("GITHUB_TOKEN")
        headers = {"Authorization": f"token {github_token}"} if github_token else {}

        try:
            if github_token:
                logger.info("Making authenticated request to GitHub API")
            response = requests.get(data_url, headers=headers)
            response.raise_for_status()
        except RequestException as e:
            logger.error(e)
            raise ArcApiClientError(f"Failed to fetch data: '{data_url}'")
        response_json = response.json()
        return response_json

    @staticmethod
    def _write_to_dataframe(data_path: str, json: bool = False) -> pd.DataFrame:
        try:
            if json:
                df = pd.read_json(data_path, encoding="utf-8")
            else:
                df = pd.read_csv(data_path, encoding="utf-8")
        except UnicodeDecodeError:
            if json:
                df = pd.read_json(data_path, encoding="latin1")
            else:
                df = pd.read_csv(data_path, encoding="latin1")
        except Exception as e:
            logger.error(e)
            raise ArcApiClientError(f"Failed to read data: {data_path}")
        return df

    def get_arc_version_list(self) -> list:
        if self.environment != "development":
            url = "/".join([self.base_url_api, "ARC", "releases"])
            release_json = self._get_api_response(url)
            version_list = [release_dict["tag_name"] for release_dict in release_json]
        else:
            url = "/".join([self.base_url_api, "DataPlatform", "contents", "ARCH"])
            release_json = self._get_api_response(url)
            version_list = sorted(
                [
                    self.get_version_string(release_dict["name"])
                    for release_dict in release_json
                    if release_dict["name"].startswith("ARCH")
                ],
                reverse=True,
            )
        return version_list

    def get_arc_version_sha(self, version: str) -> str:
        try:
            if self.environment != "development":
                url = "/".join([self.base_url_api, "ARC", "tags"])
                tag_json = self._get_api_response(url)
                version_dict = list(filter(lambda x: x["name"] == version, tag_json))[0]
                version_sha = version_dict["commit"]["sha"]
            else:
                # Get the latest commit as the code is not tagged
                url = "/".join([self.base_url_api, "DataPlatform", "commits"])
                tag_json = self._get_api_response(url)
                version_dict = tag_json[0]
                version_sha = version_dict["sha"]
            return version_sha
        except Exception as e:
            logger.error(e)
            raise ArcApiClientError(
                f"Unable to determine commit for version '{version}'"
            )

    def get_dataframe_arc_sha(self, sha: str, version: str) -> pd.DataFrame:
        if self.environment != "development":
            url = "/".join([self.base_url_raw_content, "ARC", sha, "ARC.csv"])
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    sha,
                    "ARCH",
                    self.get_arch_version_string(version),
                    "ARCH.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        return df

    def get_dataframe_arc_version_language(
        self, version: str, language: str
    ) -> pd.DataFrame:
        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(version),
                    language,
                    "ARCH.csv",
                ]
            )
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    "main",
                    "ARCH",
                    self.get_arch_version_string(version),
                    "ARCH.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        return df

    def get_dataframe_arc_list_version_language(
        self, version: str, language: str, list_name: str
    ) -> pd.DataFrame:
        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(version),
                    language,
                    "Lists",
                    f"{list_name}.csv",
                ]
            )
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    "main",
                    "ARCH",
                    self.get_arch_version_string(version),
                    "Lists",
                    f"{list_name}.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        df = df.sort_values(by=df.columns[0], ascending=True).reset_index(drop=True)
        return df

    def get_arc_language_list_version(self, version: str | None) -> list:
        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_api,
                    "ARC-Translations",
                    "contents",
                    self.get_arch_version_string(version),
                ]
            )
            language_json = self._get_api_response(url)
            df = pd.DataFrame.from_dict(language_json)
            language_list = df["name"].to_list()
        else:
            language_list = ["English"]
        return language_list

    def get_dataframe_paper_like_details(
        self, version: str, language: str
    ) -> pd.DataFrame:
        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(version),
                    language,
                    "paper_like_details.csv",
                ]
            )
        else:
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "DataPlatform",
                    "main",
                    "ARCH",
                    self.get_arch_version_string(version),
                    "paper_like_details.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        return df

    def get_dataframe_supplemental_phrases(
        self, version: str, language: str
    ) -> pd.DataFrame:
        if self.environment != "development":
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(version),
                    language,
                    "supplemental_phrases.csv",
                ]
            )
        else:
            # Use the latest ARC one
            url = "/".join([self.base_url_api, "ARC", "releases"])
            release_json = self._get_api_response(url)
            version_list = [release_dict["tag_name"] for release_dict in release_json]
            url = "/".join(
                [
                    self.base_url_raw_content,
                    "ARC-Translations",
                    "main",
                    self.get_arch_version_string(max(version_list)),
                    language,
                    "supplemental_phrases.csv",
                ]
            )
        df = self._write_to_dataframe(url)
        return df

    @staticmethod
    def get_arch_version_string(version: str) -> str:
        return f'ARCH{str(version.replace('v', ''))}'

    @staticmethod
    def get_version_string(version: str) -> str:
        return f'v{str(version.replace('ARCH', ''))}'
