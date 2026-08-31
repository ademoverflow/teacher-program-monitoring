import type { CSSProperties } from "react";
import type { SubjectRef } from "@/lib/api/shared";

/**
 * The colour a matière is drawn in.
 *
 * `subjects.color` is the pastel the seed carries, used straight as a background. The
 * accent is the same hue darkened by `color-mix`, so nothing here has to do colour
 * arithmetic in JavaScript, and a matière whose colour is changed in the seed changes
 * everywhere at once.
 *
 * A null matière is the neutral: l'accueil du matin has none (ADR-0015), and neither has
 * an empty cellule of a jour chômé.
 */
export function subjectStyle(subject: SubjectRef | null): CSSProperties {
	if (subject === null) {
		return {
			backgroundColor: "#F8FAFC",
			borderInlineStartColor: "#CBD5E1",
		};
	}
	return {
		backgroundColor: subject.color,
		borderInlineStartColor: `color-mix(in srgb, ${subject.color} 55%, #0F172A)`,
	};
}

/** A small filled dot in a matière's colour, for legends and lists. */
export function subjectDotStyle(subject: SubjectRef | null): CSSProperties {
	return {
		backgroundColor: subject?.color ?? "#CBD5E1",
		borderColor: subject
			? `color-mix(in srgb, ${subject.color} 55%, #0F172A)`
			: "#94A3B8",
	};
}
