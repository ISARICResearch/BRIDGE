import os
from unittest import mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from requests.exceptions import RequestException

from bridge.arc.arc_api import ArcApiClient, ArcApiClientError


@pytest.fixture(scope="session")
def client_production():
    os.environ["ENV"] = "production"
    os.environ["GITHUB_TOKEN"] = "abc123"
    return ArcApiClient()


@pytest.fixture(scope="session")
def client_development():
    os.environ["ENV"] = "development"
    os.environ["GITHUB_TOKEN"] = "def456"
    return ArcApiClient()


@pytest.fixture()
def data_path():
    data_path = "my/test/path"
    return data_path


@pytest.fixture()
def mock_language_json():
    language_json = [
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/English?ref=main"
            },
            "name": "English",
            "path": "ARCH1.1.3/English",
        },
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/French?ref=main"
            },
            "name": "French",
            "path": "ARCH1.1.3/French",
        },
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/Portuguese?ref=main"
            },
            "name": "Portuguese",
            "path": "ARCH1.1.3/Portuguese",
        },
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/Spanish?ref=main"
            },
            "name": "Spanish",
            "path": "ARCH1.1.3/Spanish",
        },
    ]
    return language_json


@mock.patch("bridge.arc.arc_api.logger")
def test_get_api_response_exception(mock_logger, client_production):
    class FakeResponse:
        def raise_for_status(self):
            raise RequestException

    with mock.patch("bridge.arc.arc_api.requests.get", return_value=FakeResponse()):
        with pytest.raises(ArcApiClientError):
            client_production._get_api_response("test_url")


@mock.patch("bridge.arc.arc_api.logger")
def test_get_api_response(mock_logger, mock_language_json, client_production):
    class FakeResponse:
        def raise_for_status(self):
            pass

        @staticmethod
        def json():
            return mock_language_json

    with mock.patch("bridge.arc.arc_api.requests.get", return_value=FakeResponse()):
        output = client_production._get_api_response("test_url")
        assert output == mock_language_json


@mock.patch("bridge.arc.arc_api.pd.read_csv")
@mock.patch("bridge.arc.arc_api.logger")
def test_write_to_dataframe_csv(mock_logger, mock_read_csv, data_path):
    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
    }
    df_mock = pd.DataFrame(data)
    mock_read_csv.return_value = df_mock
    output = ArcApiClient._write_to_dataframe(data_path)
    assert_frame_equal(output, df_mock)


@mock.patch("bridge.arc.arc_api.pd.read_json")
@mock.patch("bridge.arc.arc_api.logger")
def test_write_to_dataframe_json(mock_logger, mock_read_json, data_path):
    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
    }
    df_mock = pd.DataFrame(data)
    mock_read_json.return_value = df_mock
    output = ArcApiClient._write_to_dataframe(data_path, True)
    assert_frame_equal(output, df_mock)


@mock.patch("bridge.arc.arc_api.ArcApiClient._get_api_response")
def test_get_arc_version_list(mock_release_json, client_production):
    release_json = [
        {"name": "v1.1.4", "tag_name": "v1.1.4"},
        {"name": "v1.1.3", "tag_name": "v1.1.3"},
        {"name": "v1.1.2", "tag_name": "v1.1.2"},
        {"name": "v1.1.1", "tag_name": "v1.1.1"},
        {"name": "v1.1.0", "tag_name": "v1.1.0"},
        {"name": "v1.0.4", "tag_name": "v1.0.4"},
        {"name": "v1.0.0", "tag_name": "v1.0.0"},
    ]
    mock_release_json.return_value = release_json

    expected = [
        "v1.1.4",
        "v1.1.3",
        "v1.1.2",
        "v1.1.1",
        "v1.1.0",
        "v1.0.4",
        "v1.0.0",
    ]
    output = client_production.get_arc_version_list()

    assert output == expected


@mock.patch("bridge.arc.arc_api.ArcApiClient._get_api_response")
def test_get_arc_version_list_development(mock_release_json, client_development):
    release_json = [
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH0.0.1",
            "path": "ARCH/ARCH0.0.1",
        },
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH1.1.0",
            "path": "ARCH/ARCH1.1.0",
        },
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH1.1.1",
            "path": "ARCH/ARCH1.1.1",
        },
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH1.1.2",
            "path": "ARCH/ARCH1.1.2",
        },
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH1.1.3",
            "path": "ARCH/ARCH1.1.3",
        },
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH1.1.4",
            "path": "ARCH/ARCH1.1.4",
        },
        {
            "_links": {"git": "https://api..."},
            "download_url": None,
            "name": "ARCH1.2.0-rc",
            "path": "ARCH/ARCH1.2.0-rc",
        },
    ]

    mock_release_json.return_value = release_json

    expected = [
        "v1.2.0-rc",
        "v1.1.4",
        "v1.1.3",
        "v1.1.2",
        "v1.1.1",
        "v1.1.0",
        "v0.0.1",
    ]
    output = client_development.get_arc_version_list()

    assert output == expected


@mock.patch("bridge.arc.arc_api.ArcApiClient._get_api_response")
def test_get_arc_version_sha(mock_tag_json, client_production):
    expected_sha = "87e78283e0412d78e247fd2a2618e2bb09a0ca17"
    tag_json = [
        {
            "commit": {"sha": "7865ffce987395528e9151854aa524db9d9d0361"},
            "name": "v1.1.3",
        },
        {
            "commit": {"sha": "b823c02718f59c3f972976d7b64ad996572a062c"},
            "name": "v1.1.2",
        },
        {"commit": {"sha": expected_sha}, "name": "v1.1.1"},
        {
            "commit": {"sha": "c1b084da3ef73bff8ef18b113cf736cf0234823f"},
            "name": "v1.1.0",
        },
    ]
    mock_tag_json.return_value = tag_json

    output = client_production.get_arc_version_sha("v1.1.1")
    assert output == expected_sha


@mock.patch("bridge.arc.arc_api.ArcApiClient._get_api_response")
def test_get_arc_version_sha_development(mock_tag_json, client_development):
    expected_sha = "000000a"
    tag_json = [
        {
            "message": "Update ARCH.csv definition",
            "tree": {"sha": "000000"},
            "sha": "000000a",
        },
        {
            "message": "Update something else",
            "tree": {"sha": "111111"},
            "sha": "111111a",
        },
        {
            "message": "Another older update",
            "tree": {"sha": "222222"},
            "sha": "222222a",
        },
    ]
    mock_tag_json.return_value = tag_json

    output = client_development.get_arc_version_sha("v1.1.1")
    assert output == expected_sha


@mock.patch("bridge.arc.arc_api.logger")
@mock.patch("bridge.arc.arc_api.ArcApiClient._get_api_response")
def test_get_arc_version_sha_exception(mock_tag_json, mock_logger, client_production):
    tag_json = [
        {
            "commit": {"sha": "7865ffce987395528e9151854aa524db9d9d0361"},
            "name": "v1.1.3",
        },
        {
            "commit": {"sha": "b823c02718f59c3f972976d7b64ad996572a062c"},
            "name": "v1.1.2",
        },
    ]
    mock_tag_json.return_value = tag_json

    with pytest.raises(ArcApiClientError):
        client_production.get_arc_version_sha("v2.0.0")


@mock.patch("bridge.arc.arc_api.ArcApiClient._write_to_dataframe")
def test_get_dataframe_arc_list_version_language(mock_write_to_df, client_production):
    data_list = {
        "Condition": [
            "Obesity",
            "Hemiplegia",
            "Dementia",
            "Leukemia",
            "Asplenia",
        ],
    }
    df_mock_list = pd.DataFrame(data_list)
    mock_write_to_df.return_value = df_mock_list

    data_expected = {
        "Condition": [
            "Asplenia",
            "Dementia",
            "Hemiplegia",
            "Leukemia",
            "Obesity",
        ],
    }
    df_expected = pd.DataFrame(data_expected)

    version = "v1.1.1"
    language = "English"
    list_name = "conditions/Comorbidities"
    df_output = client_production.get_dataframe_arc_list_version_language(
        version, language, list_name
    )

    assert_frame_equal(df_output, df_expected)


@mock.patch("bridge.arc.arc_api.ArcApiClient._write_to_dataframe")
def test_get_dataframe_arc_list_version_language_development(
    mock_write_to_df, client_development
):
    data_list = {
        "Condition": [
            "Obesity",
            "Hemiplegia",
            "Dementia",
            "Leukemia",
            "Asplenia",
        ],
    }
    df_mock_list = pd.DataFrame(data_list)
    mock_write_to_df.return_value = df_mock_list

    data_expected = {
        "Condition": [
            "Asplenia",
            "Dementia",
            "Hemiplegia",
            "Leukemia",
            "Obesity",
        ],
    }
    df_expected = pd.DataFrame(data_expected)

    version = "v1.1.1"
    language = "English"
    list_name = "conditions/Comorbidities"
    df_output = client_development.get_dataframe_arc_list_version_language(
        version, language, list_name
    )

    assert_frame_equal(df_output, df_expected)


@mock.patch("bridge.arc.arc_api.ArcApiClient._get_api_response")
def test_get_arc_language_list_version(
    mock_response, mock_language_json, client_production
):
    mock_response.return_value = mock_language_json
    version = "v1.1.1"
    expected = [
        "English",
        "French",
        "Portuguese",
        "Spanish",
    ]
    output = client_production.get_arc_language_list_version(version)
    assert output == expected


def test_get_arc_language_list_version_development(client_development):
    version = "v1.1.1"
    expected = [
        "English",
    ]
    output = client_development.get_arc_language_list_version(version)
    assert output == expected


def test_get_arch_version_string(client_production):
    version = "v1.1.1"
    expected = "ARCH1.1.1"
    output = client_production.get_arch_version_string(version)
    assert output == expected


def test_get_version_string(client_production):
    version = "ARCH1.1.1"
    expected = "v1.1.1"
    output = client_production.get_version_string(version)
    assert output == expected
