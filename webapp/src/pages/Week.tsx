import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { LoadFailure, Loading } from "@/components/QueryState";
import { WeekGrid } from "@/components/WeekGrid";
import { getWeek } from "@/lib/api";
import { formatDateRange } from "@/lib/dates";

/** §7 écran 2 — the semaine as §4.1 prints it, from one `GET /api/weeks/{n}`. */
export default function WeekPage() {
	const { number } = useParams({ from: "/semaine/$number" });
	const weekNumber = Number(number);
	const week = useQuery({
		queryKey: ["week", weekNumber],
		queryFn: () => getWeek(weekNumber),
	});

	if (week.isPending) {
		return <Loading label={`Chargement de la semaine ${weekNumber}…`} />;
	}
	if (week.isError) {
		return <LoadFailure error={week.error} what={`la semaine ${weekNumber}`} />;
	}

	const data = week.data;

	return (
		<div className="p-6">
			<header className="mb-4 flex flex-wrap items-center justify-between gap-3">
				<div>
					<h1 className="text-2xl font-semibold">
						Semaine {data.number}
						<span className="ml-2 text-base font-normal text-slate-500">
							{data.period.code}-S{data.number_in_period}
						</span>
					</h1>
					<p className="mt-1 text-sm text-slate-500">
						{data.period.label} ·{" "}
						{formatDateRange(data.starts_on, data.ends_on)}
					</p>
				</div>

				<nav aria-label="Navigation des semaines" className="flex gap-2">
					<WeekStep number={data.previous_week_number} direction="previous" />
					<WeekStep number={data.next_week_number} direction="next" />
				</nav>
			</header>

			<WeekGrid week={data} />
		</div>
	);
}

interface WeekStepProps {
	number: number | null;
	direction: "previous" | "next";
}

function WeekStep({ number, direction }: WeekStepProps) {
	const isPrevious = direction === "previous";
	const label = isPrevious ? "Semaine précédente" : "Semaine suivante";
	const Icon = isPrevious ? ChevronLeft : ChevronRight;

	if (number === null) {
		return (
			<span
				className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-300"
				aria-disabled="true"
			>
				{isPrevious && <Icon className="size-4" aria-hidden="true" />}
				{label}
				{!isPrevious && <Icon className="size-4" aria-hidden="true" />}
			</span>
		);
	}

	return (
		<Link
			to="/semaine/$number"
			params={{ number: String(number) }}
			aria-label={`${label} (S${number})`}
			className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100"
		>
			{isPrevious && <Icon className="size-4" aria-hidden="true" />}
			{label}
			{!isPrevious && <Icon className="size-4" aria-hidden="true" />}
		</Link>
	);
}
