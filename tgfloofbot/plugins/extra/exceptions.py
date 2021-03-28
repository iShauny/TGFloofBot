from ... import exceptions as core_exceptions

from ...helpers import em


class UserNotFoundException(core_exceptions.FloofbotException):
    title = "User not found"

    def __init__(self, username: str):
        super().__init__(em(f'User "{username}" not found'))
