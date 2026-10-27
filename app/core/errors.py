class AppError(Exception):
    status_code = 400
    error_code = "VALIDATION_ERROR"

    def __init__(self, detail: str, field: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.field = field


class BadRequestError(AppError):
    status_code = 400
    error_code = "VALIDATION_ERROR"


def check_range(low, high, low_field: str, high_field: str) -> None:
    if low is not None and high is not None and low > high:
        raise BadRequestError(f"{low_field} cannot be greater than {high_field}", field=low_field)


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"
