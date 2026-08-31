import { z } from "zod";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@/lib/api/client";

/**
 * The cahier journal of one jour de classe.
 *
 * A ligne is a discipline and a durée, the objectifs and the bilan — the three columns of
 * `docs/exemple-cahier-journal-quotidien.pdf`. `planned_session_id` is null on a ligne the
 * teacher wrote herself, which is what tells a ligne from the séance it was copied from.
 */
export const journalEntrySchema = z.object({
	id: z.string(),
	school_day_id: z.string(),
	planned_session_id: z.string().nullable(),
	discipline: z.string(),
	duration_minutes: z.number().nullable(),
	objectives: z.string().nullable(),
	bilan: z.string().nullable(),
	notes: z.string().nullable(),
	position: z.number(),
});
export type JournalEntry = z.infer<typeof journalEntrySchema>;

/**
 * A day's cahier journal, with the context the printed page needs in its header.
 *
 * `initialised` says whether the day has one at all. A day never filled and a day whose
 * lignes have all been deleted read the same, and filling either is what would be asked
 * for anyway (ADR-0021).
 */
export const journalDaySchema = z.object({
	date: z.string(),
	week_number: z.number(),
	number_in_period: z.number(),
	period_code: z.string(),
	is_off: z.boolean(),
	off_reason: z.string().nullable(),
	initialised: z.boolean(),
	entries: z.array(journalEntrySchema),
});
export type JournalDay = z.infer<typeof journalDaySchema>;

export function getJournal(date: string): Promise<JournalDay> {
	return apiGet(`/journal/${date}`, journalDaySchema);
}

/**
 * Fill a day's cahier journal from its séances, once.
 *
 * Idempotent: the API answers 201 the once it fills the day and 200 every time after, and
 * both render the same day, so nothing here has to branch on it. **This writes**, and a
 * day that holds a ligne is a day a re-generation will not touch — which is why the vue
 * Jour does not call it for a day the teacher is only looking at (ADR-0028).
 */
export function initialiseJournal(date: string): Promise<JournalDay> {
	return apiPost(`/journal/${date}/initialise`, journalDaySchema);
}

/** What a new ligne may say. Only the discipline is required (`min_length=1`). */
export interface EntryCreate {
	discipline: string;
	duration_minutes?: number | null;
	objectives?: string | null;
	bilan?: string | null;
	notes?: string | null;
	planned_session_id?: string | null;
}

/** Add a ligne at the end of a day's cahier journal. */
export function addEntry(
	date: string,
	body: EntryCreate,
): Promise<JournalEntry> {
	return apiPost(`/journal/${date}/entries`, journalEntrySchema, body);
}

/** What a ligne may be told to say. Everything on it is the teacher's to change. */
export type EntryUpdate = Partial<
	Pick<
		JournalEntry,
		"discipline" | "duration_minutes" | "objectives" | "bilan" | "notes"
	>
>;

/** Change one ligne, and get back what was written — the row the cache should now hold. */
export function updateEntry(
	id: string,
	body: EntryUpdate,
): Promise<JournalEntry> {
	return apiPatch(`/journal/entries/${id}`, journalEntrySchema, body);
}

/** Remove one ligne. The cahier journal is the teacher's: nothing puts it back. */
export function deleteEntry(id: string): Promise<void> {
	return apiDelete(`/journal/entries/${id}`);
}

/**
 * Renumber a day's lignes into the given order.
 *
 * The list must name every ligne of the day exactly once — a partial order is a 400, so
 * the caller sends the whole order and never a move (ADR-0029).
 */
export function reorderJournal(
	date: string,
	entryIds: string[],
): Promise<JournalDay> {
	return apiPut(`/journal/${date}/order`, journalDaySchema, {
		entry_ids: entryIds,
	});
}
