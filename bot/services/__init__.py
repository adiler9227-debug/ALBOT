"""Services package."""

from .channel import add_to_channel, check_channel_membership, remove_from_channel
from .payments import create_payment_record, get_payment_history, get_total_revenue
from .subscriptions import (
    check_expiry,
    deactivate_subscription,
    extend_subscription,
    get_days_left,
    get_expired_subscriptions,
    get_subscription,
)
from .users import (
    add_user,
    check_agreement,
    get_lesson_progress,
    get_user,
    is_admin,
    mark_lesson_clicked,
    mark_reminder_sent,
    set_agreement,
    start_lesson,
    user_exists,
)

__all__ = [
    # Channel
    "add_to_channel",
    "remove_from_channel",
    "check_channel_membership",
    # Payments
    "create_payment_record",
    "get_payment_history",
    "get_total_revenue",
    # Subscriptions
    "get_subscription",
    "check_expiry",
    "extend_subscription",
    "get_days_left",
    "deactivate_subscription",
    "get_expired_subscriptions",
    # Users
    "add_user",
    "user_exists",
    "get_user",
    "is_admin",
    "check_agreement",
    "set_agreement",
    "get_lesson_progress",
    "start_lesson",
    "mark_lesson_clicked",
    "mark_reminder_sent",
]
