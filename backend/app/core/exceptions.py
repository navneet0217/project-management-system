class AppError(Exception):
    """Base class for expected errors. The handler in main.py turns them into JSON responses."""

    status_code = 400
    default_detail = "Bad request"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class BadRequest(AppError):
    status_code = 400


class Unauthorized(AppError):
    status_code = 401
    default_detail = "Not authenticated"


class Forbidden(AppError):
    status_code = 403
    default_detail = "You do not have permission to do this"


class NotFound(AppError):
    status_code = 404
    default_detail = "Not found"


class Conflict(AppError):
    status_code = 409


class TooManyRequests(AppError):
    status_code = 429
    default_detail = "Too many attempts. Please try again later."
