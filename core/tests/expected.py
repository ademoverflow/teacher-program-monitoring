"""The year's counts, recomputed once and asserted everywhere.

MASTER-PROMPT.md §8 asks each phase to verify its numbers by calculation rather than
assumption. These are the ones Phases 1 to 3 left in the database; the tests that name
them are what would catch a regression that quietly changed the shape of the year.
"""

OK = 200
CREATED = 201
NO_CONTENT = 204
BAD_REQUEST = 400
NOT_FOUND = 404
CONFLICT = 409
UNPROCESSABLE = 422

SUBJECTS = 12
DOMAINS = 45
PERIODS = 5
WEEKS = 36
HOLIDAYS = 5
SCHOOL_DAYS = 143
TAUGHT_DAYS = 139
DAYS_OFF = 4
TIMETABLE_SLOTS = 44
ALTERNATING_SLOTS = 6
PROGRAM_ITEMS = 220
SEQUENCES = 120
SEQUENCE_SESSIONS = 36
PLANNED_SESSIONS = 1740
PROGRAM_LINKS = 4040
SPLIT_CELLS = 208

WEEKS_PER_PERIOD = {"P1": 7, "P2": 7, "P3": 5, "P4": 6, "P5": 11}
SLOTS_PER_WEEKDAY = {1: 10, 2: 12, 4: 12, 5: 10}

# S1 has no lundi (the year opens on a mardi), so it plans 12 séances fewer than a full
# semaine — which is 50 once the six créneaux split by niveau are counted (ADR-0010).
SESSIONS_IN_FIRST_WEEK = 38
SESSIONS_IN_A_FULL_WEEK = 50
# The lundi of P1-S2: 10 créneaux, of which the grammaire and maths cells carry two.
SESSIONS_ON_A_MONDAY = 12
