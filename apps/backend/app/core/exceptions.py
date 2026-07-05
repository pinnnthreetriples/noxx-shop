class DomainException(Exception):
    """Base domain exception."""
    status_code: int = 500
    detail: str = "Domain error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail


class NotFoundException(DomainException):
    status_code = 404
    detail = "Not found"


class ValidationException(DomainException):
    status_code = 400
    detail = "Validation error"


class PermissionDeniedException(DomainException):
    status_code = 403
    detail = "Permission denied"


class AuthenticationException(DomainException):
    status_code = 401
    detail = "Authentication required"


class PaymentException(DomainException):
    status_code = 402
    detail = "Payment error"


class ConflictException(DomainException):
    status_code = 409
    detail = "Conflict"
