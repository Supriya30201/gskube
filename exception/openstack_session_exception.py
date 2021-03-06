from exception.sol_exception import SOLException


class OpenstackSessionException(SOLException):
    def __init__(self, message=None, exception=None, logger=None):
        SOLException.__init__(self, message, exception, logger)
