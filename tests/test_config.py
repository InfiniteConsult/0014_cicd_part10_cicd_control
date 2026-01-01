import os


from pathlib import Path
from unittest.mock import patch


import pytest
from _pytest.monkeypatch import MonkeyPatch

from cicd_control.errors import CicdConfigError
from cicd_control.config import ServiceConfig, GlobalConfig, ConfigLoader, _default_urls


services: list[str] = ["gitlab", "jenkins", "sonarqube", "artifactory", "mattermost"]
token_names: list[str] = [x.upper() + "_TOKEN" for x in services]
valid_config: str = "\n".join([x + "=xxx" for x in token_names])


class TestConfigLoader:
    def test_create_config_valid(self, tmp_path: Path):
        with patch.dict(os.environ):
            cicd_config_file = tmp_path / "cicd.env"
            cicd_config_file.write_text(valid_config)
            config: GlobalConfig = ConfigLoader.from_file(cicd_config_file)
            k: str
            v: ServiceConfig
            for k, v in vars(config).items():
                assert v.url == _default_urls[k]
                assert v.token == "xxx"

    def test_create_config_missing(self, tmp_path: Path):
        with patch.dict(os.environ):
            cicd_config_file = tmp_path / "cicd.env"
            cicd_config_file.write_text(valid_config.split("\n")[0])
            with pytest.raises(CicdConfigError, match="No token found for jenkins"):
                _config: GlobalConfig = ConfigLoader.from_file(cicd_config_file)

    def test_create_config_not_found(self, tmp_path: Path):
        with pytest.raises(CicdConfigError, match="Configuration file does_not_exist not found."):
            _config: GlobalConfig = ConfigLoader.from_file("does_not_exist")

    def test_create_config_invalid(self, tmp_path: Path):
        with patch.dict(os.environ):
            cicd_config_file = tmp_path / "cicd.env"
            cicd_config_file.write_text("{\"bad\": \"config\"}")
            with pytest.raises(CicdConfigError, match="Configuration file .* invalid or corrupt"):
                _config: GlobalConfig = ConfigLoader.from_file(cicd_config_file)

    def test_default_config_loading(self, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(ConfigLoader, "_default_config_path", "does_not_exist")
        with pytest.raises(CicdConfigError, match="Configuration file does_not_exist not found."):
            _config: GlobalConfig = ConfigLoader.default()
