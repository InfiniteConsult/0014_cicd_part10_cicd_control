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

# --- API Layer (The Logic) ---

class CicdApiError(CicdError):
    """Base for HTTP 4xx/5xx responses. Contains status_code."""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code

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