"""Exception hierarchy for source connectors."""


class ConnectorError(Exception):
    """Base class for all connector errors."""


class ConnectorRequestError(ConnectorError):
    """Raised when an HTTP request fails after all retries are exhausted,
    or when a connector is misconfigured (e.g. missing API key)."""


class ConnectorValidationError(ConnectorError):
    """Raised when a response body doesn't match the expected schema."""
