import { useQuery } from "@tanstack/react-query";
import { Navigate } from "@tanstack/react-router";
import { Empty } from "@/components/Empty";
import { LoadFailure } from "@/components/LoadFailure";
import { Loading } from "@/components/Loading";
import { getToday } from "@/lib/api/calendar";

/**
 * `/aujourdhui` — the home page (§8 Phase 6).
 *
 * « redirige vers le prochain jour de classe si férié/week-end », which is exactly what
 * `next_taught_day` means: today when today is taught, the next jour de classe otherwise.
 * A jour chômé is a jour de classe with no class, so it is skipped here too — its own vue
 * Jour is still reachable by its date.
 *
 * On 2026-08-31, the day before the pupils come back, that is mardi 01/09: the fallback is
 * the only path the year currently exercises.
 */
export default function TodayPage() {
	const today = useQuery({ queryKey: ["today"], queryFn: getToday });

	if (today.isPending) {
		return <Loading label="Recherche du jour de classe…" />;
	}
	if (today.isError) {
		return <LoadFailure error={today.error} what="la date du jour" />;
	}

	const next = today.data.next_taught_day;
	if (next === null) {
		return (
			<div className="p-6">
				<Empty>
					L'année scolaire est terminée : il n'y a plus de jour de classe à
					ouvrir.
				</Empty>
			</div>
		);
	}

	return <Navigate to="/jour/$date" params={{ date: next.date }} replace />;
}
