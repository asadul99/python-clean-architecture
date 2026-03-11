"""
Base entity — equivalent to a base Entity class in C# DDD projects.

In .NET Clean Architecture:
    public abstract class BaseEntity {
        public int Id { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
        private List<INotification> _domainEvents = new();
    }
"""

from datetime import datetime, timezone

from domain.events import HasDomainEvents


class BaseEntity(HasDomainEvents):
    """
    All domain entities inherit from this.
    Provides identity, audit fields, and domain event support.
    Like Entity<TId> base class in C# DDD projects.
    """

    def __init__(self, id: int | None = None) -> None:
        super().__init__()  # Initialize domain events list
        self.id = id
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id) if self.id else hash(id(self))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

