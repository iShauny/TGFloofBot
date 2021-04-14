from ... import exceptions as core_exceptions

from ...helpers import em


class UserNotFoundException(core_exceptions.FloofbotException):
    title = "User not found"

    def __init__(self, username: str):
        super().__init__(em(f'User "{username}" not found'))


class WarningReasonDeliveryException(core_exceptions.FloofbotException):
    title = "Warning reason could not be delivered to the user"

    def __init__(self, exception: Exception):
        super().__init__(em(f"Exception: {exception}"))