from enum import Enum


class EventKind(str, Enum):
    """How a webhook gateway event should be dispatched to the per-PR/MR workflow."""

    start = "start"
    update = "update"
    close = "close"
