"""Inline keyboards."""

from .agreement import agreement_keyboard
from .menu import back_to_main_keyboard, main_keyboard, documents_keyboard
from .subscription import back_to_account_keyboard, subscription_keyboard, buy_subscription_keyboard
from .tariffs import tariffs_keyboard

__all__ = [
    "agreement_keyboard",
    "main_keyboard",
    "back_to_main_keyboard",
    "documents_keyboard",
    "subscription_keyboard",
    "back_to_account_keyboard",
    "buy_subscription_keyboard",
    "tariffs_keyboard",
]
