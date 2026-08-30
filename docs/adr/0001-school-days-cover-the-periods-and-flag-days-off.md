# `school_days` covers every teaching weekday inside a période, and flags the days off

`school_days` holds one row per Monday, Tuesday, Thursday and Friday falling inside a période's
date range, and marks the four public-holiday/bridge days (29/03/2027, 06-07/05/2027,
17/05/2027) with `is_off` rather than omitting them. This gives 143 rows for 139 real days of
class, and it means Monday 31/08/2026 has no row at all even though it is a Monday of S1: the
pupils' year starts on Tuesday 01/09, so 31/08 falls outside P1 and is not a jour de classe that
was lost — it is a day that was never in the year.

The alternative was to store only the 139 days actually taught. We kept the days off because the
week views and the year generator both need to say "there is normally class here, and this week
there isn't" — a missing row cannot carry a reason, and the teacher needs to see the Easter
Monday hole in P4-S6 rather than infer it. The rule is uniform and derivable: membership follows
the période's bounds, `is_off` follows the public-holiday list.
