"""
Domain exceptions — equivalent to custom exception types in your C# Domain project.

In .NET you'd have:
    public class DomainException : Exception { ... }
    public class NotFoundException : DomainException { ... }
    public class BusinessRuleViolationException : DomainException { ... }

These are thrown from Domain/Application and caught by Presentation middleware.
"""


class DomainException(Exception):
    """Base class for all domain exceptions — like DomainException in C#."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundException(DomainException):
    """
    Entity not found — equivalent to NotFoundException in C#.
    Middleware maps this to HTTP 404.
    """

    def __init__(self, entity_name: str, entity_id: object) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with id '{entity_id}' was not found.")


class BusinessRuleViolationException(DomainException):
    """
    A business/domain rule was violated — maps to HTTP 422.
    Equivalent to throwing InvalidOperationException with domain context in C#.
    """

    def __init__(self, rule: str) -> None:
        self.rule = rule
        super().__init__(f"Business rule violated: {rule}")


class ConflictException(DomainException):
    """
    Concurrency / duplicate conflict — maps to HTTP 409.
    Like DbUpdateConcurrencyException handling in EF Core.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

