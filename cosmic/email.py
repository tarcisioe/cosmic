"""Dummy e-mail implementation."""


def send_mail(receiver: str, message: str) -> None:
    """Pretend we are sending e-mail."""
    print(f"SENDING EMAIL: to: {receiver}, message: {message}")
