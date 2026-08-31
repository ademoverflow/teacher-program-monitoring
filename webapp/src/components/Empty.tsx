interface EmptyProps {
	children: React.ReactNode;
}

/** A list that came back with nothing in it — a true answer, not a failure. */
export function Empty({ children }: EmptyProps) {
	return (
		<p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
			{children}
		</p>
	);
}
