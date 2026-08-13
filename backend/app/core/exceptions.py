class ApplicationError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AuthenticationError(ApplicationError):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(ApplicationError):
    status_code = 403
    code = "authorization_error"


class NotFoundError(ApplicationError):
    status_code = 404
    code = "not_found"


class ConflictError(ApplicationError):
    status_code = 409
    code = "conflict"

