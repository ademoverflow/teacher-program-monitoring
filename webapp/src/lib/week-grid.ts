import type { SubjectRef } from "@/lib/api/shared";
import type { DayInWeek, WeekCell, WeekDetail } from "@/lib/api/weeks";
import { timeToMinutes } from "@/lib/dates";

/**
 * Assembling the semaine grid of §4.1 from one `GET /api/weeks/{n}` response.
 *
 * The grid's rows are **derived from the créneaux themselves** (ADR-0024): take every
 * boundary the semaine's créneaux name, sort them, and the consecutive pairs are the
 * bands. For this EDT that gives thirteen, and every band of every jour is covered by
 * exactly one créneau — apart from two that no créneau covers at all, which are la
 * récréation and la pause méridienne. They have no row in `timetable_slots`; the front
 * finds the hole and §4.1 names it.
 *
 * That derivation is what makes vendredi fall into place. Its 11h30-12h00 and 12h00-12h30
 * cells do not sit on the 11h30-12h15 / 12h15-12h30 boundaries the other jours use
 * (ADR-0003), so a grid of one row per printed time range would need two rows only
 * vendredi fills and two only the others do. Spanning bands instead, a créneau occupies
 * exactly its own minutes and nothing has a hole.
 *
 * Nothing here is a React concern: it takes a response and returns a shape, which is why
 * the three traps of the phase — S1's missing lundi, a jour chômé, a cellule holding two
 * séances — are tested against a frozen response with no network and no DOM.
 */

/** The two breaks §4.1 prints, which are gaps between créneaux rather than créneaux. */
const BREAKS: { startsAt: string; endsAt: string; label: string }[] = [
	{ startsAt: "10:15", endsAt: "10:45", label: "Récréation" },
	{ startsAt: "12:30", endsAt: "14:00", label: "Pause méridienne" },
];

/** One horizontal band of the grid: a stretch of the day no créneau boundary cuts. */
export interface GridBand {
	startsAt: string;
	endsAt: string;
	startMinutes: number;
	endMinutes: number;
	minutes: number;
	/** True when no créneau of any jour covers this band. */
	isBreak: boolean;
	/** The name §4.1 gives the break, where it names one. */
	breakLabel: string | null;
}

/** One cellule, placed: which bands it spans and which lane of its jour it takes. */
export interface PlacedCell {
	cell: WeekCell;
	/** Index of the first band the créneau covers. */
	bandStart: number;
	/** Index one past the last band the créneau covers. */
	bandEnd: number;
	lane: number;
	laneSpan: number;
}

/**
 * One jour column.
 *
 * `laneCount` is how many créneaux the jour ever runs at once — two on mardi and jeudi,
 * where the EDT itself splits an hour by niveau, one on lundi and vendredi.
 */
export interface GridColumn {
	day: DayInWeek;
	laneCount: number;
	cells: PlacedCell[];
}

export interface WeekGrid {
	bands: GridBand[];
	columns: GridColumn[];
}

/** CM1 before CM2 before commun — the order §4.1 prints a split hour in. */
const LEVEL_ORDER: Record<string, number> = { CM1: 0, CM2: 1, commun: 2 };

function breakLabelFor(
	startMinutes: number,
	endMinutes: number,
): string | null {
	const found = BREAKS.find(
		(candidate) =>
			timeToMinutes(candidate.startsAt) === startMinutes &&
			timeToMinutes(candidate.endsAt) === endMinutes,
	);
	return found?.label ?? null;
}

function minutesToTime(minutes: number): string {
	const hours = Math.floor(minutes / 60);
	return `${String(hours).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}:00`;
}

/** Group a jour's cellules by the exact time range of their créneau, in clock order. */
function groupByRange(day: DayInWeek): WeekCell[][] {
	const groups = new Map<string, WeekCell[]>();
	for (const cell of day.cells) {
		const key = `${cell.slot.starts_at}|${cell.slot.ends_at}`;
		const group = groups.get(key);
		if (group === undefined) {
			groups.set(key, [cell]);
		} else {
			group.push(cell);
		}
	}
	const ordered = [...groups.values()];
	for (const group of ordered) {
		group.sort(
			(left, right) =>
				(LEVEL_ORDER[left.slot.level] ?? 9) -
					(LEVEL_ORDER[right.slot.level] ?? 9) ||
				left.slot.label.localeCompare(right.slot.label, "fr"),
		);
	}
	ordered.sort(
		(left, right) =>
			timeToMinutes(left[0].slot.starts_at) -
			timeToMinutes(right[0].slot.starts_at),
	);
	return ordered;
}

/**
 * Turn a semaine into the grid that draws it.
 *
 * The columns are the jours the response carries — three in S1, which opens on a mardi —
 * and never four by assumption.
 */
export function buildWeekGrid(week: WeekDetail): WeekGrid {
	const boundaries = new Set<number>();
	for (const day of week.days) {
		for (const cell of day.cells) {
			boundaries.add(timeToMinutes(cell.slot.starts_at));
			boundaries.add(timeToMinutes(cell.slot.ends_at));
		}
	}
	const edges = [...boundaries].sort((left, right) => left - right);

	const bands: GridBand[] = [];
	for (let index = 0; index < edges.length - 1; index += 1) {
		const startMinutes = edges[index];
		const endMinutes = edges[index + 1];
		const covered = week.days.some((day) =>
			day.cells.some(
				(cell) =>
					timeToMinutes(cell.slot.starts_at) < endMinutes &&
					timeToMinutes(cell.slot.ends_at) > startMinutes,
			),
		);
		bands.push({
			startsAt: minutesToTime(startMinutes),
			endsAt: minutesToTime(endMinutes),
			startMinutes,
			endMinutes,
			minutes: endMinutes - startMinutes,
			isBreak: !covered,
			breakLabel: covered ? null : breakLabelFor(startMinutes, endMinutes),
		});
	}

	const bandIndex = new Map(edges.map((minutes, index) => [minutes, index]));
	const columns: GridColumn[] = week.days.map((day) => {
		const groups = groupByRange(day);
		const laneCount = groups.reduce(
			(widest, group) => Math.max(widest, group.length),
			1,
		);
		const cells: PlacedCell[] = [];
		for (const group of groups) {
			const laneSpan = Math.floor(laneCount / group.length);
			group.forEach((cell, position) => {
				const isLast = position === group.length - 1;
				cells.push({
					cell,
					bandStart: bandIndex.get(timeToMinutes(cell.slot.starts_at)) ?? 0,
					bandEnd: bandIndex.get(timeToMinutes(cell.slot.ends_at)) ?? 0,
					lane: position * laneSpan,
					laneSpan: isLast ? laneCount - position * laneSpan : laneSpan,
				});
			});
		}
		return { day, laneCount, cells };
	});

	return { bands, columns };
}

/**
 * The matière a cellule is coloured by (ADR-0025).
 *
 * The séance first: the six alternating créneaux carry no matière of their own and it is
 * the séance that names the one the génération resolved (ADR-0002). Then the créneau, so
 * an unplanned cellule still shows what is normally taught in it. Then nothing:
 * l'accueil du matin has no matière at either end (ADR-0015), and neither has an empty
 * cellule of a jour chômé.
 */
export function cellSubject(cell: WeekCell): SubjectRef | null {
	return cell.sessions[0]?.subject ?? cell.slot.subject ?? null;
}
