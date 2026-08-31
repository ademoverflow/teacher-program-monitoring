import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { EditableText } from "@/components/EditableText";
import type { EntryUpdate } from "@/lib/api/journal";
import {
	SESSION_STATUSES,
	type SessionStatus,
} from "@/lib/api/planned-sessions";
import { formatTime } from "@/lib/dates";
import type { JournalRow } from "@/lib/day-journal";

/**
 * The cahier journal of one jour, as `docs/exemple-cahier-journal-quotidien.pdf` prints it:
 * *Discipline - Durée* | *Objectif(s) et compétence(s)* | *Bilan*, with la récréation and
 * la pause méridienne across the table.
 *
 * A fourth column holds the controls and does not print (ADR-0030). Everything else on
 * screen is what comes out of the printer, which is why the fields are edited in place
 * rather than in a dialog.
 */

/** Every cell of the table. Printed, the rules go darker: the model's are ink (ADR-0030). */
const CELL = "border border-slate-400 px-2 py-1 print:border-slate-700";

interface JournalTableProps {
	rows: JournalRow[];
	/** The day's lignes in order, so ▲ and ▼ know the ends of the list. */
	entryIds: string[];
	onEdit: (id: string, patch: EntryUpdate) => void;
	onDelete: (id: string) => void;
	onMove: (id: string, direction: -1 | 1) => void;
	onStatus: (sessionId: string, status: SessionStatus) => void;
}

export function JournalTable({
	rows,
	entryIds,
	onEdit,
	onDelete,
	onMove,
	onStatus,
}: JournalTableProps) {
	return (
		<table className="w-full table-fixed border-collapse text-sm">
			{/*
			 * The widths are shares rather than pixels: the controls column disappears in
			 * print and its share goes to the objectifs, which is the widest column of the
			 * model and the one that has the most to say.
			 */}
			<thead>
				<tr className="text-left">
					<th className={`w-[22%] font-normal ${CELL}`}>Discipline - Durée</th>
					<th className={`font-normal ${CELL}`}>
						Objectif(s) et compétence(s)
					</th>
					<th className={`w-[26%] font-normal ${CELL}`}>Bilan</th>
					<th className={`w-[13%] font-normal print:hidden ${CELL}`}>
						<span className="sr-only">Actions</span>
					</th>
				</tr>
			</thead>
			<tbody>
				{rows.map((row) =>
					row.kind === "break" ? (
						<tr key={`break-${row.break.startsAt}`}>
							{/*
							 * Across the three columns of the model, and never across the
							 * controls column — which is not printed, so a `colSpan` of four
							 * would leave the printed row wider than the printed table.
							 */}
							<td colSpan={3} className={`text-center text-slate-600 ${CELL}`}>
								{row.break.label ?? "Interclasse"}{" "}
								{formatTime(row.break.startsAt)} –{" "}
								{formatTime(row.break.endsAt)}
							</td>
							<td className="print:hidden" />
						</tr>
					) : (
						<EntryRow
							key={row.entry.id}
							row={row}
							isFirst={entryIds[0] === row.entry.id}
							isLast={entryIds[entryIds.length - 1] === row.entry.id}
							onEdit={onEdit}
							onDelete={onDelete}
							onMove={onMove}
							onStatus={onStatus}
						/>
					),
				)}
			</tbody>
		</table>
	);
}

interface EntryRowProps {
	row: Extract<JournalRow, { kind: "entry" }>;
	isFirst: boolean;
	isLast: boolean;
	onEdit: (id: string, patch: EntryUpdate) => void;
	onDelete: (id: string) => void;
	onMove: (id: string, direction: -1 | 1) => void;
	onStatus: (sessionId: string, status: SessionStatus) => void;
}

function EntryRow({
	row,
	isFirst,
	isLast,
	onEdit,
	onDelete,
	onMove,
	onStatus,
}: EntryRowProps) {
	const { entry, session } = row;
	const name = entry.discipline;

	return (
		<tr className="align-top">
			<td className={CELL}>
				<EditableText
					value={entry.discipline}
					label={`Discipline de la ligne « ${name} »`}
					shape="wrapped"
					onCommit={(discipline) => onEdit(entry.id, { discipline })}
					className="text-center"
				/>
				<p className="flex items-baseline justify-center gap-1 text-slate-600">
					<EditableText
						value={
							entry.duration_minutes === null
								? ""
								: String(entry.duration_minutes)
						}
						label={`Durée de la ligne « ${name} », en minutes`}
						inputMode="numeric"
						onCommit={(next) =>
							onEdit(entry.id, { duration_minutes: parseDuration(next) })
						}
						className="w-12 text-right tabular-nums"
					/>
					min
				</p>
			</td>

			<td className={CELL}>
				<EditableText
					value={entry.objectives ?? ""}
					label={`Objectifs de la ligne « ${name} »`}
					shape="block"
					onCommit={(objectives) => onEdit(entry.id, { objectives })}
				/>
			</td>

			<td className={CELL}>
				<EditableText
					value={entry.bilan ?? ""}
					label={`Bilan de la ligne « ${name} »`}
					shape="block"
					onCommit={(bilan) => onEdit(entry.id, { bilan })}
				/>
			</td>

			<td className={`print:hidden ${CELL}`}>
				{/*
				 * The statut is the séance's, not the ligne's: a ligne the teacher wrote
				 * herself has no séance behind it and so has nothing to set (ADR-0031).
				 */}
				{session !== null && (
					<select
						aria-label={`Statut de la séance « ${session.title} »`}
						value={session.status}
						onChange={(event) =>
							onStatus(session.id, event.target.value as SessionStatus)
						}
						className="mb-1 w-full rounded border border-slate-300 bg-white px-1 py-0.5 text-xs"
					>
						{SESSION_STATUSES.map((status) => (
							<option key={status} value={status}>
								{status}
							</option>
						))}
					</select>
				)}
				<div className="flex justify-end gap-0.5">
					<RowButton
						label={`Monter la ligne « ${name} »`}
						disabled={isFirst}
						onClick={() => onMove(entry.id, -1)}
					>
						<ChevronUp className="size-4" aria-hidden="true" />
					</RowButton>
					<RowButton
						label={`Descendre la ligne « ${name} »`}
						disabled={isLast}
						onClick={() => onMove(entry.id, 1)}
					>
						<ChevronDown className="size-4" aria-hidden="true" />
					</RowButton>
					<RowButton
						label={`Supprimer la ligne « ${name} »`}
						onClick={() => onDelete(entry.id)}
					>
						<Trash2 className="size-4 text-red-700" aria-hidden="true" />
					</RowButton>
				</div>
			</td>
		</tr>
	);
}

/** `« 45 »` → 45, `« »` → null. A durée the teacher clears is a durée she did not record. */
function parseDuration(text: string): number | null {
	const trimmed = text.trim();
	if (trimmed === "") {
		return null;
	}
	const minutes = Number(trimmed);
	return Number.isFinite(minutes) && minutes >= 0 ? Math.round(minutes) : null;
}

interface RowButtonProps {
	label: string;
	disabled?: boolean;
	onClick: () => void;
	children: React.ReactNode;
}

function RowButton({
	label,
	disabled = false,
	onClick,
	children,
}: RowButtonProps) {
	return (
		<button
			type="button"
			aria-label={label}
			title={label}
			disabled={disabled}
			onClick={onClick}
			className="rounded p-1 text-slate-500 hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent"
		>
			{children}
		</button>
	);
}
