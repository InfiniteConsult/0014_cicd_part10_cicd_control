# --- The Root of all errors ---
class CicdError(Exception):
    """Base exception for all CICD Control errors."""
    pass

# --- Transport Layer (The Wire) ---

class CicdTransportError(CicdError):
    """Base for network-level failures."""
    pass

class CicdDnsError(CicdTransportError):
    """Host resolution failed (gaierror)."""
    pass

class CicdConnectionError(CicdTransportError):
    """TCP connection refused, reset, or timed out."""
    pass

class CicdTlsError(CicdTransportError):
    """SSL/TLS handshake failed (Root CA trust issues)."""
    pass

class CicdSubprocessError(CicdTransportError):
    """Base class for ExecutorProtocol failures"""
    pass

class CicdCommandError(CicdSubprocessError):
    """The command ran but exited with non-zero status."""
    pass

class CicdExecutableNotFoundError(CicdSubprocessError):
    """The binary is missing from PATH"""
    pass

# --- API Layer (The Logic) ---

class CicdApiError(CicdError):
    """Base for HTTP 4xx/5xx responses. Contains status_code."""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code: int = status_code

class CicdAuthError(CicdApiError):
    """401 Unauthorized / 403 Forbidden."""
    pass

class CicdNotFoundError(CicdApiError):
    """404 Not Found."""
    pass

class CicdConflictError(CicdApiError):
    """409 Conflict (e.g., Resource already exists)."""
    pass

class CicdServerError(CicdApiError):
    """500+ Server Errors."""
    pass

# --- Configuration and Lifecycle (The Evolution) ---

class CicdConfigError(CicdError):
    """All errors related to loading configuration files."""
    pass

class CicdManifestError(CicdConfigError):
    """The :class:`StackManifest` contains invalid data (e.g. bad version string)"""
    pass

class CicdTemplateError(CicdConfigError):
    """Generator failed to produce valid config (missing variable)"""
    pass

class CicdUpgradeError(CicdError):
    """Base from the Upgrade Engine."""
    pass

class CicdMigrationError(CicdUpgradeError):
    """A specific migration script failed."""
    pass

class CicdVersionConflictError(CicdUpgradeError):
    """Attempted illegal upgrade path (e.g. downgrading)"""
    pass

# --- Vault Layer (The Memory) ---

class CicdVaultError(CicdError):
    """Base for database interactions."""
    pass

class CicdEncryptionError(CicdVaultError):
    """General crypto failure."""
    pass

class CicdDecryptionError(CicdEncryptionError):
    """The Master Key provided cannot decrypt the data"""
    pass

class CicdKeyDerivationError(CicdEncryptionError):
    """Failed to derive AES key from password"""
    pass

# --- Infrastructure Layer (The Environment) ---

class CicdInfraError(CicdError):
    """Base for host/container orchestration issues"""
    pass

class CicdDockerError(CicdInfraError):
    """Docker-specific failures."""
    pass

class CicdDockerDaemonError(CicdDockerError):
    """Cannot connect to Docker Socket."""
    pass

class CicdContainerError(CicdDockerError):
    """Container state is invalid (e.g. restart loop)"""
    pass

class CicdHostError(CicdInfraError):
    """Host machine issues."""
    pass

class CicdPermissionError(CicdHostError):
    """Failed to write file or change sysctl (sudo required)"""
    pass

class CicdRequirementError(CicdHostError):
    """Host missing prerequisites (RAM, Disk, Dependencies)"""
    pass

# --- Service Layer (The Business Logic) ---

class CicdServiceError(CicdError):
    """Base for high-level logic failures."""
    pass

class CicdHealthError(CicdServiceError):
    """Service failed to become "Green" after retries."""
    pass

class CicdHeistError(CicdServiceError):
    """Failed to generate tokens in privileged mode"""
    pass

class CicdIntegrationError(CicdServiceError):
    """Failed to write two services together"""
    pass