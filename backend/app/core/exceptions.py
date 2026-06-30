"""Project-wide custom exceptions."""


class CashlibotError(Exception):
    """Base for all custom errors raised by app code."""


class ConfigError(CashlibotError):
    """YAML config or environment misconfiguration discovered at startup."""


class InsufficientCreditsError(CashlibotError):
    """Raised when a credit-charging operation cannot be funded."""
