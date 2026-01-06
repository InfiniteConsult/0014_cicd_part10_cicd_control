import os


# --- Filesystem ---

VAULT_FILENAME: str = "cicd_vault.db" # Encrypted passwords and configs
DEFAULT_HOST_DATA_PATH: str = os.path.expanduser("~/cicd/data") # Overridable by seed.yaml
CONFIG_DIR_NAME: str = os.path.expanduser("~/cicd/config") # Overridable by seed.yaml

# --- Cryptography ---
KDF_ALGORITHM: str = "sha256"
KDF_ITERATIONS: int = 600_000
AES_KEY_SIZE: int = 32
GCM_IV_SIZE: int = 12
GCM_TAG_SIZE: int = 16

# --- Operational Limits ---
DEFAULT_REQUEST_TIMEOUT: int = 30
SUBPROCESS_TIMEOUT: int = 300
MAX_HEALTH_RETRIES: int = 60
HEALTH_CHECK_INTERVAL: int = 5

# --- Service Identifiers ---
GITLAB: str = "gitlab"
JENKINS: str = "jenkins"
ARTIFACTORY: str = "artifactory"
POSTGRES: str = "postgres"
SONARQUBE: str = "sonarqube"
MATTERMOST: str = "mattermost"
COTURN: str = "coturn"
ELASTICSEARCH: str = "elasticsearch"
KIBANA: str = "kibana"
FILEBEAT: str = "filebeat"
NODE_EXPORTER: str = "node-exporter"
CADVISOR: str = "cadvisor"
ELASTICSEARCH_EXPORTER: str = "elasticsearch-exporter"
PROMETHEUS: str = "prometheus"
GRAFANA: str = "grafana"
NGINX: str = "nginx"
