"""Days of the week, numbered the way ``datetime.date.isoweekday`` numbers them."""

from enum import IntEnum


class Weekday(IntEnum):
    """A weekday. Class is never on a Wednesday, but the number still exists."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5


FRENCH_WEEKDAYS: dict[str, Weekday] = {
    "lundi": Weekday.MONDAY,
    "mardi": Weekday.TUESDAY,
    "mercredi": Weekday.WEDNESDAY,
    "jeudi": Weekday.THURSDAY,
    "vendredi": Weekday.FRIDAY,
}
