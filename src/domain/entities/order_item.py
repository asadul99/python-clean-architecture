"""OrderItem value object — child of Order aggregate."""

from domain.entities.base_entity import BaseEntity


class OrderItem(BaseEntity):
    def __init__(
        self,
        product_name: str,
        quantity: int,
        unit_price: float,
        id: int | None = None,
    ) -> None:
        super().__init__(id)
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price

