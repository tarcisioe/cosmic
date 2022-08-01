"""Repository abstractions."""
from dataclasses import dataclass, field
from typing import Protocol, Set

from .domain.product import Product


class ProductRepository(Protocol):
    """A repository capable of handling Products."""

    def add(self, product: Product) -> None:
        """Add a Product to the repository."""

    def get(self, sku: str) -> Product | None:
        """Get a Product by its sku."""


@dataclass
class TrackingProductRepository:
    """A ProductRepository capable of tracking its objects."""

    wrapped: ProductRepository
    seen: Set[Product] = field(init=False, default_factory=set)

    def add(self, product: Product) -> None:
        """Add a Product to the repository and track it."""
        self.wrapped.add(product)
        self.seen.add(product)

    def get(self, sku: str) -> Product | None:
        """Get a product from the repository and track it."""
        product = self.wrapped.get(sku)

        if product:
            self.seen.add(product)

        return product
