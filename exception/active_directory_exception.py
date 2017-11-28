from exception.sol_exception import SOLException


class ActiveDirectoryException(SOLException):
    def __init__(self, message=None, exception=None):
        SOLException.__init__(self, message, exception)

    def get_message(self):
        return super(self.__class__, self).get_message()

    def get_exception(self):
        return super(self.__class__, self).get_exception()
