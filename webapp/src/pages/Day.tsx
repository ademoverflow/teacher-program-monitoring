import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { CalendarOff, ChevronLeft, ChevronRight, Printer } from "lucide-react";
import { DayProgramme } from "@/components/DayProgramme";
import { JournalPanel } from "@/components/JournalPanel";
import { LoadFailure } from "@/components/LoadFailure";
import { Loading } from "@/components/Loading";
import { getToday } from "@/lib/api/calendar";
import { ApiError } from "@/lib/api/client";
import { getDay } from "@/lib/api/days";
import { getJournal } from "@/lib/api/journal";
import { formatLongDate } from "@/lib/dates";

/**
 * §7 écran 3 — the vue Jour, « cœur de l'app ».
 *
 * Two responses: `GET /api/days/{date}` is the programmation and `GET /api/journal/{date}`
 * is the cahier journal. They are two things (`CONTEXT.md`) and the page keeps them so:
 * the cahier journal is the page, the programmation is what it was copied from and what it
 * still says more than a ligne does.
 *
 * What prints is this page with everything that is not the cahier journal taken off
 * (ADR-0030) — which is why the header below is the model's header rather than a screen
 * header with a printed one somewhere else.
 */

/** The class this cahier journal belongs to, as its printed header names it. */
const CLASS_LABEL = "CM1-CM2 – Cycle 3";

/** `2026-09-07`. A date that is not one never reaches the API. */
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export default function DayPage() {
	const { date } = useParams({ from: "/jour/$date" });
	const isDate = ISO_DATE.test(date);

	const today = useQuery({ queryKey: ["today"], queryFn: getToday });
	const day = useQuery({
		queryKey: ["day", date],
		queryFn: () => getDay(date),
		enabled: isDate,
	});
	const journal = useQuery({
		queryKey: ["journal", date],
		queryFn: () => getJournal(date),
		enabled: isDate,
	});

	if (!isDate) {
		return (
			<LoadFailure
				error={new Error(`« ${date} » n'est pas une date.`)}
				what="ce jour"
			/>
		);
	}
	if (
		day.isError &&
		day.error instanceof ApiError &&
		day.error.status === 404
	) {
		return <NotASchoolDay date={date} />;
	}
	if (day.isPending || journal.isPending) {
		return <Loading label="Chargement du jour…" />;
	}
	if (day.isError) {
		return <LoadFailure error={day.error} what="ce jour" />;
	}
	if (journal.isError) {
		return <LoadFailure error={journal.error} what="le cahier journal" />;
	}

	return (
		<div className="mx-auto max-w-5xl p-6 print:max-w-none print:p-0">
			<header className="mb-4">
				<div className="flex flex-wrap items-center justify-between gap-3">
					<p className="text-sm">
						{day.data.period.label} – Semaine {day.data.number_in_period}
						<span className="text-slate-500 print:hidden">
							{" "}
							·{" "}
							<Link
								to="/semaine/$number"
								params={{ number: String(day.data.week_number) }}
								className="underline-offset-2 hover:underline"
							>
								S{day.data.week_number}
							</Link>
						</span>
					</p>
					<div className="flex items-center gap-2 print:hidden">
						<DayStep date={day.data.previous_day} direction="previous" />
						<DayStep date={day.data.next_day} direction="next" />
						<button
							type="button"
							onClick={() => window.print()}
							className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100"
						>
							<Printer className="size-4" aria-hidden="true" />
							Imprimer
						</button>
					</div>
				</div>

				<div className="mt-2 flex flex-wrap items-baseline justify-between gap-3">
					<h1 className="text-2xl font-semibold first-letter:uppercase">
						{formatLongDate(day.data.date)}
					</h1>
					<p className="text-sm text-slate-600">{CLASS_LABEL}</p>
				</div>

				<div className="mt-1 flex flex-wrap items-center gap-2 print:hidden">
					<WhenChip
						date={date}
						todayDate={today.data?.date}
						nextTaughtDate={today.data?.next_taught_day?.date}
					/>
					{day.data.is_off && day.data.off_reason !== null && (
						<span className="inline-flex items-center gap-1 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
							<CalendarOff className="size-3" aria-hidden="true" />
							{day.data.off_reason}
						</span>
					)}
				</div>
			</header>

			<JournalPanel
				day={day.data}
				journal={journal.data}
				todayDate={today.data?.date}
			/>

			{day.data.sessions.length > 0 && (
				<section className="mt-10 print:hidden">
					<h2 className="mb-2 text-lg font-semibold">Programmation du jour</h2>
					<p className="mb-3 text-sm text-slate-500">
						Ce qu'une ligne de cahier journal ne copie pas : la séquence, les
						items de programme, le matériel.
					</p>
					<DayProgramme sessions={day.data.sessions} />
				</section>
			)}
		</div>
	);
}

interface WhenChipProps {
	date: string;
	todayDate: string | undefined;
	nextTaughtDate: string | undefined;
}

/** Where this jour sits relative to today — the one thing the date alone does not say. */
function WhenChip({ date, todayDate, nextTaughtDate }: WhenChipProps) {
	if (date === todayDate) {
		return (
			<span className="rounded bg-slate-900 px-2 py-0.5 text-xs font-medium text-white">
				Aujourd'hui
			</span>
		);
	}
	if (date === nextTaughtDate) {
		return (
			<span className="rounded bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-700">
				Prochain jour de classe
			</span>
		);
	}
	return null;
}

/**
 * A date the year has no jour de classe for: a mercredi, a week-end, des vacances.
 *
 * The API answers 404, and so it should — but a 404 is not a failure the teacher caused,
 * so this says what is true rather than « impossible de charger ».
 */
function NotASchoolDay({ date }: { date: string }) {
	return (
		<div className="m-6 max-w-xl rounded-lg border border-slate-200 bg-white p-6">
			<h1 className="text-lg font-semibold first-letter:uppercase">
				{formatLongDate(date)}
			</h1>
			<p className="mt-2 text-sm text-slate-600">
				Ce n'est pas un jour de classe : la classe a lieu les lundi, mardi,
				jeudi et vendredi des périodes, hors vacances.
			</p>
			{/*
			 * Nowhere to link this date to: a mercredi belongs to no jour de classe and the
			 * API has no date-to-semaine for one. So both ways out are offered — the semaine
			 * courante, and the next jour there is class on.
			 */}
			<p className="mt-4 flex gap-4 text-sm">
				<Link to="/aujourdhui" className="underline underline-offset-2">
					Aller au prochain jour de classe
				</Link>
				<Link to="/semaine" className="underline underline-offset-2">
					Voir la semaine
				</Link>
			</p>
		</div>
	);
}

interface DayStepProps {
	date: string | null;
	direction: "previous" | "next";
}

function DayStep({ date, direction }: DayStepProps) {
	const isPrevious = direction === "previous";
	const label = isPrevious ? "Jour précédent" : "Jour suivant";
	const Icon = isPrevious ? ChevronLeft : ChevronRight;

	if (date === null) {
		return (
			<span
				aria-disabled="true"
				className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-300"
			>
				{isPrevious && <Icon className="size-4" aria-hidden="true" />}
				{label}
				{!isPrevious && <Icon className="size-4" aria-hidden="true" />}
			</span>
		);
	}

	return (
		<Link
			to="/jour/$date"
			params={{ date }}
			aria-label={`${label} (${formatLongDate(date)})`}
			className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100"
		>
			{isPrevious && <Icon className="size-4" aria-hidden="true" />}
			{label}
			{!isPrevious && <Icon className="size-4" aria-hidden="true" />}
		</Link>
	);
}
