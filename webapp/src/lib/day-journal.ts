import type { PlannedSessionDetail } from "@/lib/api/days";
import type { JournalEntry } from "@/lib/api/journal";
import { type Break, findBreaks } from "@/lib/breaks";
import { timeToMinutes } from "@/lib/dates";

/**
 * Assembling the cahier journal of one jour, from `GET /api/days/{d}` and
 * `GET /api/journal/{d}`.
 *
 * `docs/exemple-cahier-journal-quotidien.pdf` prints la récréation and la pause méridienne
 * **across** the table, between the lignes they separate. A ligne carries a durée and no
 * hour, so where they go is not written on the cahier journal at all — it is written on
 * the day's créneaux, and this is where the two responses are put back together: the
 * breaks are the gaps between the day's créneaux (ADR-0024), and a break is printed before
 * the first ligne whose séance starts after it.
 *
 * A ligne the teacher wrote herself has no séance and therefore no hour, so it never moves
 * a break: it sits where she put it. A break that no remaining ligne comes after is not
 * printed — nothing follows it.
 *
 * Nothing here is a React concern: it takes two responses and returns a list, which is why
 * the day's shape is tested against frozen responses with no network and no DOM.
 */

/** One row of the cahier journal as it is drawn: a ligne, or a break across the table. */
export type JournalRow =
	| {
			kind: "entry";
			entry: JournalEntry;
			/** The séance the ligne was copied from, where it still has one. */
			session: PlannedSessionDetail | null;
	  }
	| { kind: "break"; break: Break };

/** The séances of a jour, by id, so a ligne can find the one it came from. */
export function sessionsById(
	sessions: PlannedSessionDetail[],
): Map<string, PlannedSessionDetail> {
	return new Map(sessions.map((session) => [session.id, session]));
}

/** The distinct créneaux of a jour — two séances of a split créneau name the same one. */
function slotsOf(sessions: PlannedSessionDetail[]) {
	return [
		...new Map(
			sessions.map((session) => [session.slot.id, session.slot]),
		).values(),
	];
}

/**
 * Interleave a day's lignes with la récréation and la pause méridienne.
 *
 * The lignes come in the order the response gives them, which is the order they are
 * written down; nothing is re-sorted here — a reordered cahier journal is the teacher's
 * order, not the clock's.
 */
export function buildJournalRows(
	entries: JournalEntry[],
	sessions: PlannedSessionDetail[],
): JournalRow[] {
	const byId = sessionsById(sessions);
	const breaks = findBreaks(slotsOf(sessions));

	const rows: JournalRow[] = [];
	let next = 0;
	for (const entry of entries) {
		const session =
			entry.planned_session_id === null
				? null
				: (byId.get(entry.planned_session_id) ?? null);
		const startsAt = session?.slot.starts_at;
		while (
			next < breaks.length &&
			startsAt !== undefined &&
			timeToMinutes(startsAt) >= timeToMinutes(breaks[next].endsAt)
		) {
			rows.push({ kind: "break", break: breaks[next] });
			next += 1;
		}
		rows.push({ kind: "entry", entry, session });
	}
	return rows;
}

/**
 * The day's lignes in the order they would be in after one ▲ or ▼.
 *
 * The whole list comes back, because that is what `PUT /{date}/order` takes: it must name
 * every ligne of the day exactly once, so a move is sent as an order and never as a move
 * (ADR-0029). A move off either end returns the list unchanged.
 */
export function moveEntry(
	entryIds: string[],
	id: string,
	direction: -1 | 1,
): string[] {
	const from = entryIds.indexOf(id);
	const to = from + direction;
	if (from < 0 || to < 0 || to >= entryIds.length) {
		return entryIds;
	}
	const moved = [...entryIds];
	moved[from] = entryIds[to];
	moved[to] = entryIds[from];
	return moved;
}
