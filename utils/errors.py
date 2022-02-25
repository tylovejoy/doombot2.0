class InvalidTime(Exception):
    """Invalid time entered."""

class MapCodeDoesNotExist(Exception):
    """Map code does not exist in the database."""

class NoPermissions(Exception):
    """User doesn't have sufficient permissions."""

class InvalidMapName(Exception):
    """Map name is invalid."""

class SearchNotFound(Exception):
    """Nothing was found in a database query."""

class IncorrectChannel(Exception):
    """User used command in incorrect channel."""

class RecordNotFaster(Exception):
    """Submitted record was not faster than previously submitted record."""