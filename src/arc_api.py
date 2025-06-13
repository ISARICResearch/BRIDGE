from os import environ
from os import getenv

import pandas as pd
import requests
from requests import Response
from requests.exceptions import RequestException

from logger import setup_logger

logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True


class ArcApiClientError(Exception):
    pass


class ArcApiClient:
    BASE_URL_API: str = 'https://api.github.com/repos/ISARICResearch'
    BASE_URL_RAW_CONTENT: str = 'https://raw.githubusercontent.com/ISARICResearch'

    @staticmethod
    def _get_api_response(data_url: str) -> Response:
        logger.info("GITHUB_TOKEN is set" if getenv(
            'GITHUB_TOKEN') else "GITHUB_TOKEN is not set. Making unauthenticated request")

        # Use GITHUB_TOKEN if it exists; otherwise, make unauthenticated request
        # Unauthenticated requests are limited to 60 requests per hour
        github_token = getenv('GITHUB_TOKEN')
        headers = {'Authorization': f'token {github_token}'} if github_token else {}

        try:
            if github_token:
                logger.info("Making authenticated request to GitHub API")
            response = requests.get(data_url, headers=headers)
            response.raise_for_status()
        except RequestException as e:
            logger.error(e)
            raise ArcApiClientError(f"Failed to fetch data: '{data_url}'")
        return response

    @staticmethod
    def _write_to_dataframe(data_path, json=False):
        try:
            if json:
                df = pd.read_json(data_path, encoding='utf-8')
            else:
                df = pd.read_csv(data_path, encoding='utf-8')
        except UnicodeDecodeError:
            if json:
                df = pd.read_json(data_path, encoding='latin1')
            else:
                df = pd.read_csv(data_path, encoding='latin1')
        except Exception as e:
            logger.error(e)
            raise ArcApiClientError(f"Failed to read data: {data_path}")
        return df

    def _get_release_json(self, repository):
        url = '/'.join([self.BASE_URL_API, repository, 'releases'])
        release_json = self._get_api_response(url).json()
        return release_json

    def _get_tag_json(self, repository):
        url = '/'.join([self.BASE_URL_API, repository, 'tags'])
        tag_json = self._get_api_response(url).json()
        return tag_json

    def get_release_tag_name_list(self, repository):
        release_dict_list = self._get_release_json(repository)
        tag_name_list = [release_dict['tag_name'] for release_dict in release_dict_list]
        return tag_name_list

    def get_repo_version_sha(self, repository, version):
        release_dict_list = self._get_tag_json(repository)
        try:
            version_dict = list(filter(lambda x: x['name'] == version, release_dict_list))[0]
            version_sha = version_dict['commit']['sha']
            return version_sha
        except Exception as e:
            logger.error(e)
            raise ArcApiClientError(f"Unable to determine commit for version '{version}'")

    def get_dataframe_arc_sha(self, sha):
        url = '/'.join([self.BASE_URL_RAW_CONTENT, 'ARC', sha, 'ARC.csv'])
        df = self._write_to_dataframe(url)
        return df

    def get_dataframe_arc_list_sha(self, sha, list_name):
        url = '/'.join([self.BASE_URL_RAW_CONTENT, 'ARC', sha, 'Lists', f'{list_name}.csv'])
        df = self._write_to_dataframe(url)
        df = df.sort_values(by=df.columns[0], ascending=True)
        return df

    def get_dataframe_arc_version_language(self, repository, version, language):
        url = '/'.join([self.BASE_URL_RAW_CONTENT, repository, 'main', self.get_arch_version_string(version), language,
                        'ARCH.csv'])
        df = self._write_to_dataframe(url)
        return df

    def get_dataframe_arc_list_version_language(self, version, language, list_name):
        url = '/'.join(
            [self.BASE_URL_RAW_CONTENT, 'ARC-Translations', 'main', self.get_arch_version_string(version), language,
             'Lists', f'{list_name}.csv'])
        df = self._write_to_dataframe(url)
        df = df.sort_values(by=df.columns[0], ascending=True)
        return df

    def get_arc_language_list(self, version):
        url = '/'.join([self.BASE_URL_API, 'ARC-Translations', 'contents', self.get_arch_version_string(version)])
        df = self._write_to_dataframe(url, json=True)
        language_list = df['name'].to_list()
        return language_list

    def get_dataframe_paper_like_details(self, version, language):
        url = '/'.join([self.BASE_URL_RAW_CONTENT, 'ARC-Translations', 'main', self.get_arch_version_string(version),
                        language, 'paper_like_details.csv'])
        df = self._write_to_dataframe(url)
        return df

    def get_dataframe_supplemental_phrases(self, version, language):
        url = '/'.join([self.BASE_URL_RAW_CONTENT, 'ARC-Translations', 'main', self.get_arch_version_string(version),
                        language, 'supplemental_phrases.csv'])
        df = self._write_to_dataframe(url)
        return df

    @staticmethod
    def get_arch_version_string(version):
        if environ.get('ENV') == 'test':
            version_string = version[4:]
        else:
            version_string = version[1:]
        return f'ARCH{str(version_string)}'
