"""
Use :class:`ConfigLoader` to generate a :class:`GlobalConfig` for the CI/CD control package.
"""
import os
from os import PathLike
from pathlib import Path
from dataclasses import dataclass, asdict
from collections.abc import ItemsView


from dotenv import load_dotenv


from cicd_control.errors import CicdConfigError


@dataclass
class ServiceConfig:
    """
    Configuration for any of our particular services.
    """
    url: str
    """
    The URL for the service on our CI/CD network. Note, the hostname or IP will need to match the TLS certificate for
    connections to succeed.
    """

    token: str | None = None
    """
    A token or password for communicating with the APIs. Check the docs for any of the services to see what type of
    token or password is required.
    """


@dataclass
class GlobalConfig:
    """
    Aggregates all service configs into one manageable object.
    """
    gitlab: ServiceConfig
    """
    The Library
    """
    jenkins: ServiceConfig
    """
    The Factory
    """
    sonarqube: ServiceConfig
    """
    The Inspector
    """
    artifactory: ServiceConfig
    """
    The Warehouse
    """
    mattermost: ServiceConfig
    """
    The Town Square/Command Centre
    """


_default_urls: dict[str, str] = {
    "gitlab": "https://gitlab.cicd.local:10300",
    "jenkins": "https://jenkins.cicd.local:10400",
    "sonarqube": "http://sonarqube.cicd.local:9000",
    "artifactory": "https://artifactory.cicd.local:8082",
    "mattermost": "https://mattermost.cicd.local:8065",
}
"""
Default URLs for stack as per my articles
"""


class ConfigLoader:
    """
    Provides methods to load configuration files. Choose from either default (searches a known dev container path) or
    from_file which allows the user to override details for a custom stack that deviates from the articles.

    Required variables:

    - GITLAB_URL
    - GITLAB_TOKEN
    - JENKINS_URL
    - JENKINS_TOKEN
    - SONARQUBE_URL
    - SONARQUBE_TOKEN
    - ARTIFACTORY_URL
    - ARTIFACTORY_TOKEN
    - MATTERMOST_URL
    - MATTERMOST_TOKEN

    """
    _default_config_path: Path = Path("~/data/cicd.env").expanduser()
    """
    Default file path for our CI/CD environment variables.
    """

    @staticmethod
    def default() -> GlobalConfig:
        """
        Attempts to load a default configuration file from ~/data/cicd.env.

        Precedence: Environment > Default

        :raises CicdConfigError: If no configuration file was found.
        :raises CicdConfigError: If unable to load default config file.
        :raises CicdConfigError: If required tokens not found.
        :rtype: GlobalConfig
        :return: A configuration object representing the default stack URLs and tokens.
        """
        return ConfigLoader._create_config(ConfigLoader._default_config_path)

    @staticmethod
    def from_file(config_path: PathLike) -> GlobalConfig:
        """
        Attempts to load a configuration file from a user specified path.

        Precedence: Environment > File > Default

        :param PathLike config_path: A user specified env file.
        :raises CicdConfigError: If no configuration file was found.
        :raises CicdConfigError: If unable to load custom config file.
        :raises CicdConfigError: If required tokens not found.
        :rtype: GlobalConfig
        :return: A configuration object representing the custom stack URLs and tokens.
        """
        return ConfigLoader._create_config(config_path)

    @staticmethod
    def _load_env_file(path: PathLike) -> bool:
        """
        Loads the environment variables from a specified path.

        :param PathLike path: The default or user specified env file
        :rtype: bool
        :return: Whether the environment variables were successfully loaded
        """
        return load_dotenv(dotenv_path=path)

    @staticmethod
    def _create_config(path: PathLike) -> GlobalConfig:
        """
        Creates a global configuration object from a specified path.

        :param PathLike path: The default or user specified env file
        :raises CicdConfigError: If no configuration file was found.
        :raises CicdConfigError: If config file is unable to load.
        :raises CicdConfigError: If required tokens not found.
        :rtype: GlobalConfig
        :return: A configuration object representing the default or custom stack URLs and tokens.
        """
        if not Path(path).exists():
            raise CicdConfigError(f"Configuration file {path} not found.")

        if not ConfigLoader._load_env_file(path):
            raise CicdConfigError(f"Configuration file {path} invalid or corrupt.")

        # All default configs with no tokens at this point
        service_configs: dict[str, ServiceConfig] = {x: ServiceConfig(url=_default_urls[x]) for x in _default_urls}
        config: GlobalConfig = GlobalConfig(**service_configs)

        # Continue processing from environment
        # Dotenv won't overwrite keys already in the environment, ensuring precedence.
        for name, service in vars(config).items():
            env_token = os.environ.get(f"{name.upper()}_TOKEN")
            if env_token:
                service.token = env_token

            if service.token is None:
                raise CicdConfigError(f"No token found for {name}")

        return config