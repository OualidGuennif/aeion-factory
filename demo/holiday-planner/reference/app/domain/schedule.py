# Spec: knowledge/components/schedule.md
"""One day's activities: validated times, ordered by start, never overlapping (REQ-008..010, CON-002).

A pure function of its inputs; the store wraps add() in one write transaction so two concurrent
requests are checked one after the other."""
from dataclasses import dataclass

DAY_END = 1440


class Refused(ValueError):
    def __init__(self, field, reason):
        super().__init__(f"{field}: {reason}")
        self.field, self.reason = field, reason


class Overlap(Refused):
    def __init__(self, other):
        super().__init__("start_minute", "overlap")
        self.other = other


@dataclass(frozen=True)
class Activity:
    id: str
    title: str
    start_minute: int
    end_minute: int


class Schedule:
    """The activities of one day, kept sorted by start minute."""

    def __init__(self, activities=()):
        self.activities = sorted(activities, key=lambda a: (a.start_minute, a.id))

    def add(self, activity_id, title, start_minute, duration):
        """Place a new activity; Refused for an invalid time, Overlap when CON-002 is false."""
        # Validate the time before looking at the day: an invalid request never reads state.
        if not title.strip():
            raise Refused("title", "required")
        if type(start_minute) is not int or not 0 <= start_minute < DAY_END:
            raise Refused("start_minute", "out_of_range")
        if type(duration) is not int or duration <= 0:
            raise Refused("duration", "not_positive")
        end_minute = start_minute + duration
        if end_minute > DAY_END:
            raise Refused("duration", "past_midnight")
        # Admit only a slot that fits (CON-002): touching ends are not an overlap.
        for other in self.activities:
            if start_minute < other.end_minute and other.start_minute < end_minute:
                raise Overlap(other)
        # Keep the day ordered by start minute (REQ-008).
        activity = Activity(activity_id, title.strip(), start_minute, end_minute)
        self.activities = sorted([*self.activities, activity], key=lambda a: (a.start_minute, a.id))
        return activity
