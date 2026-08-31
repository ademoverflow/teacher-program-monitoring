import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CircleAlert, ListPlus, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { JournalTable, type RowFailure } from "@/components/JournalTable";
import type { DayDetail, PlannedSessionDetail } from "@/lib/api/days";
import {
	addEntry,
	type EntryUpdate,
	initialiseJournal,
	type JournalDay,
	deleteEntry as removeEntry,
	reorderJournal,
	updateEntry,
} from "@/lib/api/journal";
import {
	type SessionStatus,
	updateSessionStatus,
} from "@/lib/api/planned-sessions";
import {
	buildJournalRows,
	fillsItself,
	moveEntry,
	parseDuration,
} from "@/lib/day-journal";

/**
 * The cahier journal of one jour: the table, and everything that writes to it.
 *
 * Every mutation puts the row the API answered with straight into the cache rather than
 * invalidating the query (ADR-0029). A `PATCH` on blur that triggered a refetch would land
 * under the cursor of the next field the teacher had already moved to; writing the answer
 * back cannot.
 *
 * `["day", date]` is invalidated on the changes that alter what the day says about itself —
 * `has_journal` — and never on an edit.
 */

interface JournalPanelProps {
	day: DayDetail;
	journal: JournalDay;
	/** Today's date, which is what decides whether this day fills itself (ADR-0028). */
	todayDate: string | undefined;
}

/** What a new ligne says before the teacher has said anything. */
const NEW_DISCIPLINE = "Nouvelle ligne";

export function JournalPanel({ day, journal, todayDate }: JournalPanelProps) {
	const queryClient = useQueryClient();
	// One refused write at a time, and where it was refused. A failure carrying an `entryId`
	// is shown on that ligne; one without — an initialisation, an add — over the table.
	const [failure, setFailure] = useState<RowFailure | null>(null);
	const key = ["journal", day.date];
	const dayKey = ["day", day.date];

	function patchJournal(update: (previous: JournalDay) => JournalDay) {
		queryClient.setQueryData<JournalDay>(key, (previous) =>
			previous === undefined ? previous : update(previous),
		);
	}

	/** `ApiError.message` is already the server's French sentence, or a French fallback. */
	function report(entryId: string, error: Error) {
		setFailure({ entryId, message: error.message });
	}

	function onWritten() {
		setFailure(null);
	}

	const initialise = useMutation({
		mutationFn: () => initialiseJournal(day.date),
		onError: (error: Error) => report("", error),
		onSuccess: (filled) => {
			onWritten();
			queryClient.setQueryData(key, filled);
			queryClient.invalidateQueries({ queryKey: dayKey });
		},
	});

	const edit = useMutation({
		mutationFn: ({ id, patch }: { id: string; patch: EntryUpdate }) =>
			updateEntry(id, patch),
		onError: (error: Error, { id }) => report(id, error),
		onSuccess: (written) => {
			onWritten();
			patchJournal((previous) => ({
				...previous,
				entries: previous.entries.map((entry) =>
					entry.id === written.id ? written : entry,
				),
			}));
		},
	});

	const add = useMutation({
		mutationFn: () => addEntry(day.date, { discipline: NEW_DISCIPLINE }),
		onError: (error: Error) => report("", error),
		onSuccess: (written) => {
			onWritten();
			patchJournal((previous) => ({
				...previous,
				initialised: true,
				entries: [...previous.entries, written],
			}));
			queryClient.invalidateQueries({ queryKey: dayKey });
		},
	});

	const remove = useMutation({
		mutationFn: (id: string) => removeEntry(id),
		onError: (error: Error, id: string) => report(id, error),
		onSuccess: (_answer, id) => {
			onWritten();
			patchJournal((previous) => {
				const entries = previous.entries.filter((entry) => entry.id !== id);
				return { ...previous, entries, initialised: entries.length > 0 };
			});
			queryClient.invalidateQueries({ queryKey: dayKey });
		},
	});

	const reorder = useMutation({
		mutationFn: ({ order }: { entryId: string; order: string[] }) =>
			reorderJournal(day.date, order),
		onError: (error: Error, { entryId }) => report(entryId, error),
		onSuccess: (reordered) => {
			onWritten();
			queryClient.setQueryData(key, reordered);
		},
	});

	const setStatus = useMutation({
		mutationFn: ({ id, status }: { id: string; status: SessionStatus }) =>
			updateSessionStatus(id, status),
		onError: (error: Error) => report("", error),
		onSuccess: (written) => {
			onWritten();
			queryClient.setQueryData<DayDetail>(dayKey, (previous) =>
				previous === undefined
					? previous
					: {
							...previous,
							sessions: previous.sessions.map((session) =>
								session.id === written.id ? written : session,
							),
						},
			);
		},
	});

	// The day being taught fills itself, once. Every other day waits to be asked, because a
	// day holding a ligne is a day the génération will not write again (ADR-0028).
	const asked = useRef<string | null>(null);
	const automatic = fillsItself(day, journal, todayDate);
	useEffect(() => {
		if (automatic && asked.current !== day.date) {
			asked.current = day.date;
			initialise.mutate();
		}
	}, [automatic, day.date, initialise.mutate]);

	const entryIds = journal.entries.map((entry) => entry.id);
	const rows = buildJournalRows(journal.entries, day.sessions);

	/**
	 * Send a durée the teacher typed.
	 *
	 * Parsing it here rather than in the table is what gives a refusal a voice: « 45 min »
	 * is not a number of minutes, and storing null for it would drop the durée the ligne
	 * already had without a word. The rejection is what puts the field back.
	 */
	function onDuration(id: string, text: string): Promise<unknown> {
		const minutes = parseDuration(text);
		if (minutes === undefined) {
			const message = "Une durée s'écrit en minutes, par exemple 45.";
			setFailure({ entryId: id, message });
			return Promise.reject(new Error(message));
		}
		return edit.mutateAsync({ id, patch: { duration_minutes: minutes } });
	}

	return (
		<section aria-label="Cahier journal">
			{/* A refusal that belongs to no ligne — an initialisation, an added ligne. */}
			{failure !== null && failure.entryId === "" && (
				<p
					role="alert"
					className="mb-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 print:hidden"
				>
					<CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
					{failure.message}
				</p>
			)}

			{journal.entries.length === 0 ? (
				<EmptyJournal
					day={day}
					pending={initialise.isPending}
					onInitialise={() => initialise.mutate()}
					onAdd={() => add.mutate()}
				/>
			) : (
				<>
					<JournalTable
						rows={rows}
						entryIds={entryIds}
						onEdit={(id, patch) => edit.mutateAsync({ id, patch })}
						onDuration={onDuration}
						onDelete={(id) => remove.mutate(id)}
						onMove={(id, direction) =>
							reorder.mutate({
								entryId: id,
								order: moveEntry(entryIds, id, direction),
							})
						}
						onStatus={(id, status) => setStatus.mutate({ id, status })}
						failure={failure}
					/>
					<button
						type="button"
						onClick={() => add.mutate()}
						disabled={add.isPending}
						className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100 print:hidden"
					>
						<Plus className="size-4" aria-hidden="true" />
						Ajouter une ligne
					</button>
				</>
			)}
		</section>
	);
}

interface EmptyJournalProps {
	day: DayDetail;
	pending: boolean;
	onInitialise: () => void;
	onAdd: () => void;
}

/**
 * A day with no ligne: the one before it is filled, and the one after it is emptied.
 *
 * A jour chômé says why instead — there is no séance to copy, and initialising it would
 * answer 200 having written nothing (ADR-0021).
 */
function EmptyJournal({
	day,
	pending,
	onInitialise,
	onAdd,
}: EmptyJournalProps) {
	if (day.is_off) {
		return (
			<p className="rounded-lg border border-dashed border-amber-300 bg-amber-50 p-6 text-center text-sm text-amber-800">
				Pas de classe ce jour-là
				{day.off_reason !== null && <> : {day.off_reason}</>}. Le cahier journal
				de ce jour reste vide.
			</p>
		);
	}

	return (
		<div className="rounded-lg border border-dashed border-slate-300 p-6 text-center print:hidden">
			<p className="text-sm text-slate-500">
				{describeProgramme(day.sessions)}
			</p>
			<div className="mt-3 flex flex-wrap justify-center gap-2">
				<button
					type="button"
					onClick={onInitialise}
					disabled={pending || day.sessions.length === 0}
					className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700 disabled:opacity-40"
				>
					<ListPlus className="size-4" aria-hidden="true" />
					Initialiser depuis la programmation
				</button>
				<button
					type="button"
					onClick={onAdd}
					className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100"
				>
					<Plus className="size-4" aria-hidden="true" />
					Ajouter une ligne
				</button>
			</div>
		</div>
	);
}

function describeProgramme(sessions: PlannedSessionDetail[]): string {
	if (sessions.length === 0) {
		return "Ce jour n'a aucune séance programmée : le cahier journal est à écrire à la main.";
	}
	return `Le cahier journal de ce jour n'a pas encore été rempli. La programmation lui donne ${sessions.length} séances.`;
}
