"""Eval notification capture."""

# Global notification collector for eval runs
_eval_notifications = []


async def capture_notification(notification):
    """Capture notifications during eval runs and show progress."""
    _eval_notifications.append(
        {"type": notification.type, "data": notification.data, "timestamp": notification.timestamp}
    )

    # Store notifications but don't pollute terminal output
    # (notifications are saved to .json in run folder)


def callback():
    """Get notification callback for injecting into agents during evals."""
    return capture_notification


def clear():
    """Clear notification capture for fresh run."""
    global _eval_notifications
    _eval_notifications.clear()


def get_all():
    """Get all captured notifications."""
    return _eval_notifications.copy()
