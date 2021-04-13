class FloofbotException(Exception):
    ## If True, reports the error to the bot administrators
    notify = False
    ## If True, shuts down the bot
    critical = False
    ## If True, does not send an error message to the relevant chat
    silent = False

    ## The human readable name of the error to be displayed in a non-silent error message
    @classmethod
    @property
    def title(cls):
        return f"{cls.__name__} error"


class FloofbotLoaderException(FloofbotException):
    critical = True


class FloofbotSyntaxError(FloofbotException):
    pass


class FloofbotPermissionsError(FloofbotException):
    title = "Permissions error"
