import { Link } from "@tanstack/react-router";
import { CalendarOff } from "lucide-react";
import { LevelBadge } from "@/components/LevelBadge";
import type { PlannedSessionSummary, SlotSummary } from "@/lib/api/shared";
import type { DayInWeek, WeekCell, WeekDetail } from "@/lib/api/weeks";
import { sessionSubject, subjectStyle } from "@/lib/colors";
import { formatDuration, formatShortDate, formatTime } from "@/lib/dates";
import { buildWeekGrid, cellSubject, type GridBand } from "@/lib/week-grid";

/**
 * The grid of §4.1: the jours in columns, the créneaux in bands.
 *
 * Everything about the shape comes from `buildWeekGrid`; this file only draws it. One
 * outer CSS grid holds the hour gutter and the jour columns, and a jour column is a grid
 * of its own — the bands as rows, its lanes as columns — so a créneau spanning two bands
 * and a pair of créneaux sharing an hour are both just a `grid-area`.
 *
 * A jour column is a list, because that is what it is: the time blocks of that day in
 * order, la récréation and la pause méridienne among them. Each block carries its hour and
 * its créneau as its accessible name, which is what tells two cellules of the same hour
 * apart.
 */

interface WeekGridProps {
	week: WeekDetail;
}

export function WeekGrid({ week }: WeekGridProps) {
	const grid = buildWeekGrid(week);
	const bandCount = grid.bands.length;

	return (
		<div
			className="grid gap-x-2 gap-y-1 overflow-x-auto"
			style={{
				gridTemplateColumns: `4rem repeat(${grid.columns.length}, minmax(11rem, 1fr))`,
				// Row 1 is the jour headers; the bands follow. Every column below is a
				// `subgrid`, so a cellule pushed open by its title moves the hour beside it
				// too — the alternative, sizing each column on its own content, drifts.
				gridTemplateRows: `auto ${grid.bands.map(bandHeight).join(" ")}`,
			}}
		>
			{grid.columns.map((column, index) => (
				<DayHeader
					key={column.day.id}
					day={column.day}
					style={{ gridRow: 1, gridColumn: index + 2 }}
				/>
			))}

			<div
				className="grid grid-rows-subgrid"
				style={{ gridRow: `2 / span ${bandCount}`, gridColumn: 1 }}
			>
				{grid.bands.map((band) => (
					<div
						key={band.startsAt}
						className="pr-2 text-right text-xs tabular-nums text-slate-400"
					>
						{band.isBreak ? "" : formatTime(band.startsAt)}
					</div>
				))}
			</div>

			{grid.columns.map((column, index) => (
				<ul
					key={column.day.id}
					aria-label={`Créneaux du ${formatShortDate(column.day.date)}`}
					className="grid grid-rows-subgrid gap-x-1"
					style={{
						gridRow: `2 / span ${bandCount}`,
						gridColumn: index + 2,
						gridTemplateColumns: `repeat(${column.laneCount}, minmax(0, 1fr))`,
					}}
				>
					{grid.bands.map((band, index) =>
						band.isBreak ? (
							<BreakBand
								key={band.startsAt}
								band={band}
								bandIndex={index}
								laneCount={column.laneCount}
							/>
						) : null,
					)}
					{column.cells.map((placed) => (
						<CellBox
							key={placed.cell.slot.id}
							cell={placed.cell}
							isOff={column.day.is_off}
							style={{
								gridRow: `${placed.bandStart + 1} / ${placed.bandEnd + 1}`,
								gridColumn: `${placed.lane + 1} / span ${placed.laneSpan}`,
							}}
						/>
					))}
				</ul>
			))}
		</div>
	);
}

/**
 * How tall a band is drawn.
 *
 * Not proportional to its minutes: the pause méridienne is ninety of them and would
 * swallow the afternoon. Short bands get a floor so a 10' accueil stays legible, long ones
 * a ceiling, and `auto` lets a busy cellule push its band open.
 */
function bandHeight(band: GridBand): string {
	if (band.isBreak) {
		return "1.5rem";
	}
	const rem = Math.min(4, Math.max(2, band.minutes * 0.075));
	return `minmax(${rem}rem, auto)`;
}

interface DayHeaderProps {
	day: DayInWeek;
	style: React.CSSProperties;
}

/** §7 écran 2's « clic sur un jour → vue Jour ». The whole header is the link. */
function DayHeader({ day, style }: DayHeaderProps) {
	return (
		<div style={style} className="border-b border-slate-200 pb-1">
			<Link
				to="/jour/$date"
				params={{ date: day.date }}
				aria-label={`Cahier journal du ${formatShortDate(day.date)}`}
				className="block text-sm font-semibold first-letter:uppercase underline-offset-2 hover:underline"
			>
				{formatShortDate(day.date)}
			</Link>
			{day.is_off && day.off_reason !== null && (
				<p className="flex items-center gap-1 text-xs font-medium text-amber-700">
					<CalendarOff className="size-3 shrink-0" aria-hidden="true" />
					{day.off_reason}
				</p>
			)}
		</div>
	);
}

interface BreakBandProps {
	band: GridBand;
	bandIndex: number;
	laneCount: number;
}

/**
 * La récréation and la pause méridienne. Neither has a row in `timetable_slots` — they are
 * the gaps between créneaux, and §4.1 is where their names come from (ADR-0024).
 */
function BreakBand({ band, bandIndex, laneCount }: BreakBandProps) {
	return (
		<li
			style={{ gridRow: bandIndex + 1, gridColumn: `1 / span ${laneCount}` }}
			className="flex items-center justify-center rounded bg-slate-100 text-[0.6875rem] uppercase tracking-wide text-slate-400"
		>
			{band.breakLabel}
		</li>
	);
}

interface CellBoxProps {
	cell: WeekCell;
	isOff: boolean;
	style: React.CSSProperties;
}

/**
 * One cellule: a créneau on a jour, holding its 0, 1 or 2 séances.
 *
 * Two séances stack inside this one box — a commun créneau a per-niveau méthodo splits
 * (ADR-0010) — which is what tells them apart from the hours where the EDT itself has two
 * créneaux, drawn as two boxes side by side.
 */
function CellBox({ cell, isOff, style }: CellBoxProps) {
	const { slot, sessions } = cell;
	const name = `${formatTime(slot.starts_at)} · ${slot.label}`;

	// An empty cellule still says what is normally taught in it — the maths cellule of a
	// lundi de Pâques stays pink (ADR-0025) — muted, so an empty box never reads as a full
	// one. `cellSubject` falls back to the créneau, which is all there is here.
	if (isOff || sessions.length === 0) {
		return (
			<li
				aria-label={name}
				style={{ ...style, ...subjectStyle(cellSubject(cell)) }}
				className="rounded border-s-4 px-1.5 py-1 opacity-45"
			>
				<p className="truncate text-[0.6875rem] text-slate-600">{slot.label}</p>
			</li>
		);
	}

	return (
		<li
			aria-label={name}
			style={style}
			className="flex flex-col gap-px overflow-hidden rounded"
		>
			{sessions.map((session, index) => (
				<SessionBox
					key={session.id}
					session={session}
					slot={slot}
					showDuration={index === 0}
				/>
			))}
		</li>
	);
}

interface SessionBoxProps {
	session: PlannedSessionSummary;
	slot: SlotSummary;
	showDuration: boolean;
}

/**
 * One séance inside a cellule, tinted by `sessionSubject` — the cascade of ADR-0025 read
 * one séance at a time, so that two stacked séances never borrow each other's colour.
 */
function SessionBox({ session, slot, showDuration }: SessionBoxProps) {
	return (
		<div
			style={subjectStyle(sessionSubject(session, slot))}
			className="min-h-0 flex-1 border-s-4 px-1.5 py-1 text-slate-900"
		>
			<div className="flex items-start justify-between gap-1">
				<p className="truncate text-[0.6875rem] font-medium uppercase tracking-wide text-slate-600">
					{session.subject?.label ?? slot.label}
				</p>
				<span className="flex shrink-0 items-center gap-1">
					<LevelBadge level={session.level} />
					{showDuration && (
						<span className="text-[0.625rem] tabular-nums text-slate-500">
							{formatDuration(slot.duration_minutes)}
						</span>
					)}
				</span>
			</div>
			<p className="line-clamp-2 text-xs leading-tight" title={session.title}>
				{session.title}
			</p>
		</div>
	);
}
