"""Basic MessageBus implementation."""
from dataclasses import dataclass, field
from typing import Callable, DefaultDict, Type, TypeVar

from . import email
from .domain.events import Event, OutOfStock

TEvent = TypeVar("TEvent", bound=Event)
Handler = Callable[[TEvent], None]


@dataclass
class MessageBus:
    """A message bus implementation."""

    handlers: DefaultDict[Type[Event], list[Handler[Event]]] = field(
        default_factory=lambda: DefaultDict(list)
    )

    def handle(self, event: Event) -> None:
        """Handle an incoming event."""
        for handler in self.handlers[type(event)]:
            handler(event)

    def add_handler(self, event: Type[TEvent], handler: Handler[TEvent]) -> None:
        """Add an event handler."""
        self.handlers[event].append(handler)  # type: ignore


def send_out_of_stock_notification(event: OutOfStock) -> None:
    """Send a notification when an OutOfStock event happens."""
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )
