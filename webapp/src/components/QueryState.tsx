import { CircleAlert, Loader } from "lucide-react";

interface LoadingProps {
	label?: string;
}

export function Loading({ label = "Chargement…" }: LoadingProps) {
	return (
		<p className="flex items-center gap-2 p-6 text-sm text-slate-500">
			<Loader className="size-4 animate-spin" aria-hidden="true" />
			{label}
		</p>
	);
}

interface LoadFailureProps {
	error: Error;
	what: string;
}

export function LoadFailure({ error, what }: LoadFailureProps) {
	return (
		<div
			role="alert"
			className="m-6 flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800"
		>
			<CircleAlert className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
			<span>
				<strong className="font-medium">Impossible de charger {what}.</strong>{" "}
				{error.message}
			</span>
		</div>
	);
}

interface EmptyProps {
	children: React.ReactNode;
}

export function Empty({ children }: EmptyProps) {
	return (
		<p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
			{children}
		</p>
	);
}
