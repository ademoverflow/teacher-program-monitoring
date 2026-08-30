import { useQuery } from "@tanstack/react-query";
import { Activity, CircleAlert, CircleCheck, RefreshCw } from "lucide-react";
import { getHealth } from "@/lib/api";

function formatUptime(seconds: number): string {
	if (seconds < 60) {
		return `${Math.round(seconds)} s`;
	}
	const minutes = Math.floor(seconds / 60);
	if (minutes < 60) {
		return `${minutes} min`;
	}
	const hours = Math.floor(minutes / 60);
	return `${hours} h ${minutes % 60} min`;
}

function App() {
	const health = useQuery({ queryKey: ["health"], queryFn: getHealth });

	return (
		<main className="flex min-h-screen items-center justify-center bg-slate-50 p-8 text-slate-900">
			<section className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
				<h1 className="text-2xl font-semibold">Suivi de programme CM1-CM2</h1>
				<p className="mt-1 text-sm text-slate-500">
					Année scolaire 2026-2027 · zone C
				</p>

				<div className="mt-6 rounded-lg border border-slate-200 p-4">
					<h2 className="flex items-center gap-2 text-sm font-medium text-slate-600">
						<Activity className="size-4" aria-hidden="true" />
						État de l'API
					</h2>

					{health.isPending && (
						<p className="mt-2 text-sm text-slate-500">Connexion à l'API…</p>
					)}

					{health.isError && (
						<p
							role="alert"
							className="mt-2 flex items-center gap-2 text-sm text-red-700"
						>
							<CircleAlert className="size-4 shrink-0" aria-hidden="true" />
							API injoignable : {health.error.message}
						</p>
					)}

					{health.isSuccess && (
						<dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
							<dt className="text-slate-500">Statut</dt>
							<dd className="flex items-center gap-1 font-medium text-emerald-700">
								<CircleCheck className="size-4" aria-hidden="true" />
								{health.data.status}
							</dd>
							<dt className="text-slate-500">Version</dt>
							<dd>{health.data.version}</dd>
							<dt className="text-slate-500">Démarrée depuis</dt>
							<dd>{formatUptime(health.data.uptime)}</dd>
						</dl>
					)}
				</div>

				<button
					type="button"
					onClick={() => health.refetch()}
					className="mt-4 inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
				>
					<RefreshCw className="size-4" aria-hidden="true" />
					Actualiser
				</button>
			</section>
		</main>
	);
}

export default App;
