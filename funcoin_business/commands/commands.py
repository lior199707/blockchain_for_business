from enum import Enum
from enum import auto


class CommandErrorException(Exception):
    pass


class Command(Enum):
    """
    Class Command, holds all types of commands that derive from users actions on the server
    Enum:
    Transaction - command indicating a transaction
    NEW_CAR - command indicating a new car was created
    SUCCESS - command indicating no other actions are required on the server after the action ended.
    ERROR - command indicating an error occurred during an action
    DESTROY_CAR - command indicating a car was destroyed
    """
    TRANSACTION = auto()
    NEW_CAR = auto()
    # Should be sent when no other actions are required
    SUCCESS = auto()
    ERROR = auto()
    DESTROY_CAR = auto()
