"""Typed errors exposed by the Home Assistant client."""


class HoidError(Exception):
    """Base class for safe-to-display application errors."""


class DeviceError(HoidError):
    """Device is unknown or the requested action is not permitted."""


class ConfigurationError(HoidError):
    """Runtime configuration is missing or invalid."""


class AuthenticationError(HoidError):
    """Home Assistant rejected authentication or authorization."""


class HomeAssistantUnavailable(HoidError):
    """Home Assistant could not be reached or timed out."""


class EntityNotFound(HoidError):
    """Configured entity does not exist in Home Assistant."""


class EntityUnavailable(HoidError):
    """Home Assistant reports the entity as unavailable or unknown."""


class CommandRejected(HoidError):
    """Home Assistant rejected the requested service call."""


class VerificationFailed(HoidError):
    """State did not reach the requested value within the verification window."""


class OutcomeUncertain(VerificationFailed):
    """The command may have run, but its final state could not be confirmed."""
