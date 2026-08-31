import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { CalendarOff, Palmtree } from "lucide-react";
import { LoadFailure } from "@/components/LoadFailure";
import { Loading } from "@/components/Loading";
import type { Holiday, PeriodSummary, WeekSummary } from "@/lib/api";
import { getYear } from "@/lib/api";
import {
	formatCompactDate,
	formatCompactRange,
	formatLongDate,
} from "@/lib/dates";
import { plural } from "@/lib/plural";

/**
 * §7 écran 1 — the year in one request.
 *
 * `GET /api/calendar` carries the five périodes with their semaines, the five vacances and
 * the semaine courante, so this view never walks the semaines itself.
 */
export default function YearPage() {
	const year = useQuery({ queryKey: ["calendar"], queryFn: getYear });

	if (year.isPending) {
		return <Loading label="Chargement de l'année…" />;
	}
	if (year.isError) {
		return <LoadFailure error={year.error} what="l'année scolaire" />;
	}

	const { periods, holidays, current_week_number: currentWeek } = year.data;
	const weekCount = periods.reduce(
		(total, period) => total + period.weeks.length,
		0,
	);

	return (
		<div className="p-6">
			<header className="mb-6">
				<h1 className="text-2xl font-semibold">
					Année scolaire {year.data.label}
				</h1>
				<p className="mt-1 text-sm text-slate-500">
					{weekCount} semaines de classe · {formatLongDate(year.data.starts_on)}{" "}
					→ {formatLongDate(year.data.ends_on)}
				</p>
			</header>

			<div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
				{periods.map((period) => (
					<PeriodCard
						key={period.code}
						period={period}
						holiday={holidayAfter(period, holidays)}
						currentWeek={currentWeek}
					/>
				))}
			</div>
		</div>
	);
}

/** The vacances that close a période: the first stretch beginning after its last jour. */
function holidayAfter(
	period: PeriodSummary,
	holidays: Holiday[],
): Holiday | undefined {
	return holidays.find((holiday) => holiday.starts_on > period.ends_on);
}

interface PeriodCardProps {
	period: PeriodSummary;
	holiday: Holiday | undefined;
	currentWeek: number | null;
}

function PeriodCard({ period, holiday, currentWeek }: PeriodCardProps) {
	return (
		<section
			aria-label={period.label}
			className="rounded-xl border border-slate-200 bg-white shadow-sm"
		>
			<header className="border-b border-slate-100 px-4 py-3">
				<h2 className="font-semibold">{period.label}</h2>
				<p className="text-xs text-slate-500">
					{period.weeks.length} semaines ·{" "}
					{formatCompactRange(period.starts_on, period.ends_on)}
				</p>
			</header>

			<ul className="grid grid-cols-2 gap-2 p-3 sm:grid-cols-3">
				{period.weeks.map((week) => (
					<li key={week.number}>
						<WeekChip week={week} isCurrent={week.number === currentWeek} />
					</li>
				))}
			</ul>

			{holiday !== undefined && (
				<p className="flex items-center gap-2 border-t border-slate-100 px-4 py-2 text-xs text-amber-700">
					<Palmtree className="size-3.5 shrink-0" aria-hidden="true" />
					{holiday.label} ·{" "}
					{holiday.ends_on === null
						? `à partir du ${formatCompactDate(holiday.starts_on)}`
						: formatCompactRange(holiday.starts_on, holiday.ends_on)}
				</p>
			)}
		</section>
	);
}

interface WeekChipProps {
	week: WeekSummary;
	isCurrent: boolean;
}

function WeekChip({ week, isCurrent }: WeekChipProps) {
	const daysOff = week.days_off === 0 ? "" : `, ${daysOffLabel(week.days_off)}`;

	return (
		<Link
			to="/semaine/$number"
			params={{ number: String(week.number) }}
			aria-label={`Semaine ${week.number}, ${formatCompactRange(week.starts_on, week.ends_on)}${daysOff}`}
			aria-current={isCurrent ? "page" : undefined}
			className={`block rounded-lg border px-2.5 py-2 text-left transition hover:border-slate-400 hover:bg-slate-50 ${
				isCurrent
					? "border-slate-900 bg-slate-900 text-white hover:border-slate-900 hover:bg-slate-800"
					: "border-slate-200"
			}`}
		>
			<span className="block text-sm font-semibold">S{week.number}</span>
			<span
				className={`block text-[0.6875rem] ${isCurrent ? "text-slate-300" : "text-slate-500"}`}
			>
				{formatCompactRange(week.starts_on, week.ends_on)}
			</span>
			{week.days_off > 0 && (
				<span
					className={`mt-1 flex items-center gap-1 text-[0.6875rem] ${
						isCurrent ? "text-amber-200" : "text-amber-700"
					}`}
				>
					<CalendarOff className="size-3 shrink-0" aria-hidden="true" />
					{daysOffLabel(week.days_off)}
				</span>
			)}
		</Link>
	);
}

/** « 2 jours chômés » — said the same way in the chip and in its accessible name. */
function daysOffLabel(count: number): string {
	return `${count} ${plural(count, "jour")} ${plural(count, "chômé")}`;
}
