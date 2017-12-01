import traceback


class SOLException(Exception):
    message = None
    exception = None
    logger = None

    def __init__(self, message=None, exception=None, logger=None):
        self.message = message
        self.exception = exception
        if logger:
            if message:
                logger.error(message)
            if exception:
                logger.error(traceback.format_exc(exception))

    def get_message(self):
        return self.message

    def get_exception(self):
        return self.exception

    def __str__(self):
        return self.message
