import type { Today, YearOverview } from "@/lib/api/calendar";

/**
 * Which semaine « la semaine courante » means (§8 Phase 5).
 *
 * `GET /api/calendar` answers it directly while today falls inside a semaine — including
 * the days between two périodes, since a semaine runs Monday to Friday and the vacances
 * start mid-week. It is null once the year is over, and there `next_taught_day` is null
 * too, so the last resort is the first semaine: an empty page would be worse than the
 * rentrée.
 */
export function resolveCurrentWeek(
	year: Pick<YearOverview, "current_week_number">,
	today: Pick<Today, "next_taught_day"> | undefined,
): number {
	return year.current_week_number ?? today?.next_taught_day?.week_number ?? 1;
}
