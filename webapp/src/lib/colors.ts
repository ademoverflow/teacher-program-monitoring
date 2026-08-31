import type { CSSProperties } from "react";
import type { SubjectRef } from "@/lib/api/shared";

/**
 * The colour a matière is drawn in.
 *
 * `subjects.color` is the pastel the seed carries, used straight as a background. The
 * accent is the same hue darkened by `color-mix`, so nothing here does colour arithmetic
 * in JavaScript, and a matière whose colour changes in `core/seed/subjects.json` changes
 * everywhere at once.
 *
 * A null matière is the neutral: l'accueil du matin has none (ADR-0015), and neither has a
 * cellule whose créneau alternates and whose séance is missing.
 */

const NEUTRAL_FILL = "#F8FAFC";
const NEUTRAL_ACCENT = "#CBD5E1";
const NEUTRAL_DOT_BORDER = "#94A3B8";

/** The matière's own colour, darkened — an accent that needs no second value in the seed. */
function accent(color: string): string {
	return `color-mix(in srgb, ${color} 55%, #0F172A)`;
}

export function subjectStyle(subject: SubjectRef | null): CSSProperties {
	if (subject === null) {
		return {
			backgroundColor: NEUTRAL_FILL,
			borderInlineStartColor: NEUTRAL_ACCENT,
		};
	}
	return {
		backgroundColor: subject.color,
		borderInlineStartColor: accent(subject.color),
	};
}

/** A small filled dot in a matière's colour, for lists and fiches. */
export function subjectDotStyle(subject: SubjectRef | null): CSSProperties {
	if (subject === null) {
		return {
			backgroundColor: NEUTRAL_ACCENT,
			borderColor: NEUTRAL_DOT_BORDER,
		};
	}
	return {
		backgroundColor: subject.color,
		borderColor: accent(subject.color),
	};
}
