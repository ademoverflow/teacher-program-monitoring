import { useEffect, useRef, useState } from "react";

/**
 * A field that saves what it holds when it is left (ADR-0029).
 *
 * Blur, not keystroke: a `PATCH` per character is wrong, and a debounce loses the last
 * edit when the teacher closes the tab. Échap puts back what the server has; Entrée
 * commits, except in a field whose value may hold newlines. A field that has not changed
 * saves nothing.
 *
 * The value comes back from the server after every commit, and the draft is re-seeded from
 * it — but never while the field has the focus, so a refetch can never land under the
 * cursor.
 *
 * Both growing shapes use `.autogrow` (`styles.css`): what the teacher reads is what
 * prints, and a bilan written on four lines is not clipped to two (ADR-0030).
 */

/**
 * How much room a field takes.
 *
 * - `line` — one line that does not wrap: the durée.
 * - `wrapped` — one value, wrapped over as many lines as it needs: the discipline, which
 *   is a créneau's label and is regularly wider than its column.
 * - `block` — a value that may itself hold newlines: the objectifs, the bilan.
 */
export type FieldShape = "line" | "wrapped" | "block";

interface EditableTextProps {
	value: string;
	/**
	 * Called with the new text when the field is left and the text changed.
	 *
	 * Return a promise and the field waits on it: a rejection puts back what the server
	 * has. That is what an emptied discipline needs — the API refuses it, and a field left
	 * blank while the server still holds « Calcul mental » would be a lie on the screen.
	 * A handler that returns nothing is committed and forgotten, as before.
	 */
	onCommit: (next: string) => unknown;
	/** What this field is, for the teacher and for a screen reader. */
	label: string;
	shape?: FieldShape;
	placeholder?: string;
	className?: string;
	inputMode?: "text" | "numeric";
}

export function EditableText({
	value,
	onCommit,
	label,
	shape = "line",
	placeholder,
	className = "",
	inputMode = "text",
}: EditableTextProps) {
	const [draft, setDraft] = useState(value);
	const focused = useRef(false);
	// The draft is also kept in a ref, and that is the one `commit` reads. A change and a
	// blur landing in the same task — a paste followed by a click, a script driving the
	// page — would otherwise commit the draft of the *previous* render, which is the value
	// that was just replaced.
	const latest = useRef(value);

	useEffect(() => {
		if (!focused.current) {
			latest.current = value;
			setDraft(value);
		}
	}, [value]);

	function change(next: string) {
		latest.current = next;
		setDraft(next);
	}

	function commit() {
		focused.current = false;
		if (latest.current === value) {
			return;
		}
		try {
			Promise.resolve(onCommit(latest.current)).catch(revert);
		} catch {
			revert();
		}
	}

	/** Put back what the server has. The caller says why; this only undoes. */
	function revert() {
		if (!focused.current) {
			change(value);
		}
	}

	function onKeyDown(event: React.KeyboardEvent) {
		if (event.key === "Escape") {
			change(value);
			focused.current = false;
			(event.target as HTMLElement).blur();
		}
		if (event.key === "Enter" && shape !== "block") {
			event.preventDefault();
			(event.target as HTMLElement).blur();
		}
	}

	const shared = {
		"aria-label": label,
		placeholder,
		value: draft,
		onFocus: () => {
			focused.current = true;
		},
		onBlur: commit,
		onKeyDown,
	};

	const fieldClass =
		"w-full rounded-sm bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-slate-400";

	if (shape === "line") {
		return (
			<input
				{...shared}
				inputMode={inputMode}
				onChange={(event) => change(event.target.value)}
				className={`${fieldClass} ${className}`}
			/>
		);
	}

	return (
		<div className={`autogrow ${className}`} data-value={draft}>
			<textarea
				{...shared}
				rows={1}
				onChange={(event) => change(event.target.value)}
				className={fieldClass}
			/>
		</div>
	);
}
