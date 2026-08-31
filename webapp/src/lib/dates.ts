/**
 * French date and time formatting.
 *
 * §6 asks for `Intl.DateTimeFormat` and helpers rather than a date library. The API sends
 * ISO calendar dates (`2026-09-07`) and wall-clock times (`09:10:00`), neither of which
 * carries a timezone: a date is parsed into a *local* `Date` so that formatting can never
 * shift it a day backwards, and a time is formatted as text without a `Date` at all.
 */

const LONG_DATE = new Intl.DateTimeFormat("fr-FR", {
	weekday: "long",
	day: "numeric",
	month: "long",
	year: "numeric",
});

const DAY_AND_MONTH = new Intl.DateTimeFormat("fr-FR", {
	day: "numeric",
	month: "long",
});

const SHORT_DAY = new Intl.DateTimeFormat("fr-FR", {
	weekday: "long",
	day: "numeric",
	month: "short",
});

const COMPACT = new Intl.DateTimeFormat("fr-FR", {
	day: "numeric",
	month: "short",
});

/** Parse `2026-09-07` into local midnight, never UTC midnight. */
export function parseIsoDate(iso: string): Date {
	const [year, month, day] = iso.split("-").map(Number);
	return new Date(year, month - 1, day);
}

/** « lundi 7 septembre 2026 » */
export function formatLongDate(iso: string): string {
	return LONG_DATE.format(parseIsoDate(iso));
}

/** « lundi 7 sept. » — the header of a jour column. */
export function formatShortDate(iso: string): string {
	return SHORT_DAY.format(parseIsoDate(iso));
}

/**
 * « du 31 août au 4 septembre 2026 », dropping the year and the month where both ends
 * share them.
 */
export function formatDateRange(startIso: string, endIso: string): string {
	const start = parseIsoDate(startIso);
	const end = parseIsoDate(endIso);
	const sameYear = start.getFullYear() === end.getFullYear();
	const head = sameYear
		? DAY_AND_MONTH.format(start)
		: LONG_DATE.format(start).replace(/^\S+\s/, "");
	const tail = LONG_DATE.format(end).replace(/^\S+\s/, "");
	return `du ${head} au ${tail}`;
}

/** « 31 août » */
export function formatCompactDate(iso: string): string {
	return COMPACT.format(parseIsoDate(iso));
}

/** « 31 août – 4 sept. » — narrow enough for a semaine chip. */
export function formatCompactRange(startIso: string, endIso: string): string {
	return `${formatCompactDate(startIso)} – ${formatCompactDate(endIso)}`;
}

/** `09:10:00` → « 9h10 ». A wall-clock time, formatted as the EDT prints it. */
export function formatTime(time: string): string {
	const [hours, minutes] = time.split(":");
	return `${Number(hours)}h${minutes}`;
}

/** `45` → « 45 min ». The teaching time of a créneau, which is not always its span (ADR-0003). */
export function formatDuration(minutes: number): string {
	return `${minutes} min`;
}

/** `09:10:00` → 550. Minutes since midnight, for placing a créneau in the grid. */
export function timeToMinutes(time: string): number {
	const [hours, minutes] = time.split(":").map(Number);
	return hours * 60 + minutes;
}
