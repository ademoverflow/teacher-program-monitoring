import { useQuery } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, Loader } from "lucide-react";
import { getHealth } from "@/lib/api";

/**
 * The one diagnostic worth having on every page of a local app: whether the containers
 * that hold the year are answering. This is the Phase 0 smoke test, kept.
 */
export function ApiStatus() {
	const health = useQuery({
		queryKey: ["health"],
		queryFn: getHealth,
		refetchInterval: 60_000,
	});

	if (health.isPending) {
		return (
			<p className="flex items-center gap-1.5 text-xs text-slate-400">
				<Loader className="size-3.5 animate-spin" aria-hidden="true" />
				Connexion à l'API…
			</p>
		);
	}

	if (health.isError) {
		return (
			<p
				role="alert"
				className="flex items-start gap-1.5 text-xs font-medium text-red-700"
			>
				<CircleAlert className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
				API injoignable
			</p>
		);
	}

	return (
		<p className="flex items-center gap-1.5 text-xs text-slate-400">
			<CircleCheck className="size-3.5 text-emerald-600" aria-hidden="true" />
			API v{health.data.version}
		</p>
	);
}
