class SOLException(Exception):
    message = None
    exception = None

    def __init__(self, message=None, exception=None):
        self.message = message
        self.exception = exception

    def get_message(self):
        return self.message

    def get_exception(self):
        return self.exception
