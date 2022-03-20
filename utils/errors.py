class DoombotBaseException(Exception):
    """Base exception for Doombot."""


class InvalidTime(DoombotBaseException):
    """Invalid time entered."""


class MapCodeDoesNotExist(DoombotBaseException):
    """Map code does not exist in the database."""


class NoPermissions(DoombotBaseException):
    """User doesn't have sufficient permissions."""


class InvalidMapName(DoombotBaseException):
    """Map name is invalid."""


class SearchNotFound(DoombotBaseException):
    """Nothing was found in a database query."""


class IncorrectChannel(DoombotBaseException):
    """User used command in incorrect channel."""


class RecordNotFaster(DoombotBaseException):
    """Submitted record was not faster than previously submitted record."""


class DocumentAlreadyExists(DoombotBaseException):
    """Database document already exists."""


class TournamentStateError(DoombotBaseException):
    """Tournament is incorrect active state."""


class InvalidEventType(DoombotBaseException):
    """Event type is invalid."""


class InvalidMapFilters(DoombotBaseException):
    """Map search must have at least one filter."""


class NameTooLong(DoombotBaseException):
    """User alias must be less than 25 characters."""


class UserNotFound(DoombotBaseException):
    """User hasn't submitted a time to the tournament in this category."""
