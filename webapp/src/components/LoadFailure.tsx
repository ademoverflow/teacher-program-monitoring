import { CircleAlert } from "lucide-react";

interface LoadFailureProps {
	error: Error;
	/** What could not be loaded: « la semaine 12 ». */
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
