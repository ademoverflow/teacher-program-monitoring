import { Loader } from "lucide-react";

interface LoadingProps {
	/** What is being loaded, in French: « Chargement de la semaine 12… ». */
	label: string;
}

export function Loading({ label }: LoadingProps) {
	return (
		<p className="flex items-center gap-2 p-6 text-sm text-slate-500">
			<Loader className="size-4 animate-spin" aria-hidden="true" />
			{label}
		</p>
	);
}
