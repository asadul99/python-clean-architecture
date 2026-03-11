"""
SQLAlchemy ORM models — equivalent to EF Core entity configurations / DbSet<T>.
These map domain entities to database tables (like EntityTypeConfiguration in C#).
"""

from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from domain.entities.order import OrderStatus


class Base(DeclarativeBase):
    """Base class for all ORM models — like EF Core's DbContext.Model."""
    pass


class OrderModel(Base):
    """
    ORM model mapped to 'orders' table.
    Equivalent to modelBuilder.Entity<Order>() in EF Core.
    """
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_address: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(OrderStatus, name="order_status"), default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Navigation property — like ICollection<OrderItem> in C#
    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",  # eager loading like .Include() in EF Core
    )

    # Computed property so Pydantic model_validate can read 'total'
    @property
    def total(self) -> float:
        return sum(item.line_total for item in self.items)

    @property
    def item_count(self) -> int:
        return len(self.items)


class OrderItemModel(Base):
    """ORM model mapped to 'order_items' table."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Navigation property back to parent
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")

    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price

