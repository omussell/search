
class APIConnectionException(Exception):
    pass


class OrcidAPIException(Exception):
    pass


class OrcidAPINotFoundException(OrcidAPIException):
    pass


class OrcidAPIUnauthorizedException(OrcidAPIException):
    pass
