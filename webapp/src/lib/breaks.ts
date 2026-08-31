import { timeToMinutes } from "@/lib/dates";

/**
 * La récréation and la pause méridienne, found rather than declared (ADR-0024).
 *
 * Neither has a row in `timetable_slots`: they are the stretches of the day that no
 * créneau covers. §4.1 prints them and so does the cahier journal, so both the semaine
 * grid and the printed jour have to draw them — and both find them the same way, from the
 * boundaries of the créneaux around them. Only the names are written down, in the table
 * below; a gap the table does not name is still a gap, drawn without a name.
 */

/** What §4.1 calls the two stretches it prints between the créneaux. */
const NAMES: { startsAt: string; endsAt: string; label: string }[] = [
	{ startsAt: "10:15", endsAt: "10:45", label: "Récréation" },
	{ startsAt: "12:30", endsAt: "14:00", label: "Pause méridienne" },
];

/** A stretch of the day no créneau covers. */
export interface Break {
	/** `10:15:00`, as the API writes a wall-clock time. */
	startsAt: string;
	endsAt: string;
	/** The name §4.1 gives it, where it names one. */
	label: string | null;
}

/** The name §4.1 gives the stretch running between these two minutes, if it names one. */
export function breakLabelFor(
	startMinutes: number,
	endMinutes: number,
): string | null {
	const found = NAMES.find(
		(candidate) =>
			timeToMinutes(candidate.startsAt) === startMinutes &&
			timeToMinutes(candidate.endsAt) === endMinutes,
	);
	return found?.label ?? null;
}

export function minutesToTime(minutes: number): string {
	const hours = Math.floor(minutes / 60);
	return `${String(hours).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}:00`;
}

/** Anything with the two boundaries of a créneau — a `SlotSummary` is one. */
interface TimeRange {
	starts_at: string;
	ends_at: string;
}

/**
 * The gaps between a day's créneaux, in clock order.
 *
 * A lundi gives back exactly two — 10h15-10h45 and 12h30-14h00 — because every other
 * minute of its ten créneaux is taught. Overlapping ranges are merged first, so two
 * créneaux running at the same hour (mardi 11h30) do not invent a gap between them.
 */
export function findBreaks(ranges: TimeRange[]): Break[] {
	const spans = ranges
		.map((range) => ({
			from: timeToMinutes(range.starts_at),
			to: timeToMinutes(range.ends_at),
		}))
		.sort((left, right) => left.from - right.from);

	const breaks: Break[] = [];
	let covered = spans[0]?.to ?? 0;
	for (const span of spans) {
		if (span.from > covered) {
			breaks.push({
				startsAt: minutesToTime(covered),
				endsAt: minutesToTime(span.from),
				label: breakLabelFor(covered, span.from),
			});
		}
		covered = Math.max(covered, span.to);
	}
	return breaks;
}
