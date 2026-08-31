import type { DomainRef, SubjectRef } from "@/lib/api/shared";
import { subjectDotStyle } from "@/lib/colors";

interface SubjectLineProps {
	subject: SubjectRef | null;
	domain: DomainRef | null;
	className?: string;
	dotClassName?: string;
}

/** « ● Mathématiques · Nombres » — how a matière and its domaine are named in a list. */
export function SubjectLine({
	subject,
	domain,
	className = "text-xs text-slate-500",
	dotClassName = "size-2.5",
}: SubjectLineProps) {
	return (
		<p className={`flex items-center gap-1.5 ${className}`}>
			<span
				style={subjectDotStyle(subject)}
				className={`inline-block shrink-0 rounded-full border ${dotClassName}`}
				aria-hidden="true"
			/>
			{subject?.label ?? "Sans matière"}
			{domain !== null && <> · {domain.label}</>}
		</p>
	);
}
