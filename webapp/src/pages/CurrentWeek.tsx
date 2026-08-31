import { useQuery } from "@tanstack/react-query";
import { Navigate } from "@tanstack/react-router";
import { LoadFailure, Loading } from "@/components/QueryState";
import { getToday, getYear } from "@/lib/api";
import { resolveCurrentWeek } from "@/lib/current-week";

/**
 * `/semaine` — « semaine courante par défaut » (§8 Phase 5).
 *
 * `current_week_number` answers it while the year is running; once it is over the fallback
 * is the semaine of `next_taught_day`.
 */
export default function CurrentWeekPage() {
	const year = useQuery({ queryKey: ["calendar"], queryFn: getYear });
	const today = useQuery({ queryKey: ["today"], queryFn: getToday });

	if (year.isPending || today.isPending) {
		return <Loading label="Recherche de la semaine courante…" />;
	}
	if (year.isError) {
		return <LoadFailure error={year.error} what="l'année scolaire" />;
	}

	const number = resolveCurrentWeek(year.data, today.data);
	return (
		<Navigate
			to="/semaine/$number"
			params={{ number: String(number) }}
			replace
		/>
	);
}
