import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CircleAlert, ListPlus, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { JournalTable } from "@/components/JournalTable";
import { ApiError } from "@/lib/api/client";
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
import { buildJournalRows, moveEntry } from "@/lib/day-journal";

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
	/** True when the app may fill this day by itself, without being asked (ADR-0028). */
	autoInitialise: boolean;
}

/** What a new ligne says before the teacher has said anything. */
const NEW_DISCIPLINE = "Nouvelle ligne";

export function JournalPanel({
	day,
	journal,
	autoInitialise,
}: JournalPanelProps) {
	const queryClient = useQueryClient();
	const [failure, setFailure] = useState<string | null>(null);
	const key = ["journal", day.date];
	const dayKey = ["day", day.date];

	function patchJournal(update: (previous: JournalDay) => JournalDay) {
		queryClient.setQueryData<JournalDay>(key, (previous) =>
			previous === undefined ? previous : update(previous),
		);
	}

	function onError(error: Error) {
		setFailure(
			error instanceof ApiError && error.detail !== null
				? error.detail
				: `L'enregistrement a échoué (${error.message}).`,
		);
	}

	function onWritten() {
		setFailure(null);
	}

	const initialise = useMutation({
		mutationFn: () => initialiseJournal(day.date),
		onError,
		onSuccess: (filled) => {
			onWritten();
			queryClient.setQueryData(key, filled);
			queryClient.invalidateQueries({ queryKey: dayKey });
		},
	});

	const edit = useMutation({
		mutationFn: ({ id, patch }: { id: string; patch: EntryUpdate }) =>
			updateEntry(id, patch),
		onError,
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
		onError,
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
		onError,
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
		mutationFn: (entryIds: string[]) => reorderJournal(day.date, entryIds),
		onError,
		onSuccess: (reordered) => {
			onWritten();
			queryClient.setQueryData(key, reordered);
		},
	});

	const setStatus = useMutation({
		mutationFn: ({ id, status }: { id: string; status: SessionStatus }) =>
			updateSessionStatus(id, status),
		onError,
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

	// ADR-0028: the day being taught fills itself, once. Every other day waits to be asked,
	// because a day holding a ligne is a day the génération will not write again.
	const asked = useRef<string | null>(null);
	const fillable = !journal.initialised && day.sessions.length > 0;
	useEffect(() => {
		if (autoInitialise && fillable && asked.current !== day.date) {
			asked.current = day.date;
			initialise.mutate();
		}
	}, [autoInitialise, fillable, day.date, initialise.mutate]);

	const entryIds = journal.entries.map((entry) => entry.id);
	const rows = buildJournalRows(journal.entries, day.sessions);

	return (
		<section aria-label="Cahier journal">
			{failure !== null && (
				<p
					role="alert"
					className="mb-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 print:hidden"
				>
					<CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
					{failure}
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
						onEdit={(id, patch) => edit.mutate({ id, patch })}
						onDelete={(id) => remove.mutate(id)}
						onMove={(id, direction) =>
							reorder.mutate(moveEntry(entryIds, id, direction))
						}
						onStatus={(id, status) => setStatus.mutate({ id, status })}
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
