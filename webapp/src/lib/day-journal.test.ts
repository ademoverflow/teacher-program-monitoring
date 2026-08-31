import { describe, expect, it } from "vitest";
import type { DayDetail } from "@/lib/api/days";
import type { JournalDay } from "@/lib/api/journal";
import { buildJournalRows, moveEntry } from "@/lib/day-journal";
import dayFixture from "@/test/fixtures/day-2026-09-07.json";
import dayOff from "@/test/fixtures/day-2027-03-29.json";
import journalFixture from "@/test/fixtures/journal-2026-09-07.json";

const day = dayFixture as DayDetail;
const journal = journalFixture as JournalDay;

/** The disciplines and the break labels, in the order they are drawn. */
function labels(rows: ReturnType<typeof buildJournalRows>): string[] {
	return rows.map((row) =>
		row.kind === "break" ? `— ${row.break.label} —` : row.entry.discipline,
	);
}

describe("les lignes du cahier journal", () => {
	it("intercale la récréation et la pause méridienne entre les lignes", () => {
		const rows = buildJournalRows(journal.entries, day.sessions);

		expect(labels(rows)).toEqual([
			"Accueil · rituel de langue · plan de travail",
			"Étude de la langue — Grammaire (CM1)",
			"Étude de la langue — Grammaire (CM2)",
			"Calcul mental",
			"— Récréation —",
			"Mathématiques — Nombres (CM1)",
			"Mathématiques — Nombres (CM2)",
			"Lecture — Œuvre suivie",
			"Dictée du jour",
			"— Pause méridienne —",
			"Lecture offerte / lecture personnelle",
			"Sciences et technologie",
			"Anglais",
			"Arts plastiques",
		]);
	});

	it("rattache chaque ligne à la séance dont elle a été copiée", () => {
		const rows = buildJournalRows(journal.entries, day.sessions);
		const first = rows[0];

		expect(first.kind).toBe("entry");
		if (first.kind === "entry") {
			expect(first.session?.slot.starts_at).toBe("09:00:00");
			// The créneau's teaching time, not `ends_at - starts_at` (ADR-0003).
			expect(first.entry.duration_minutes).toBe(10);
		}
	});

	it("laisse une ligne écrite à la main sans séance, et sans déplacer de coupure", () => {
		const hand = {
			...journal.entries[0],
			id: "hand-written",
			planned_session_id: null,
			discipline: "Conseil de classe",
		};
		const rows = buildJournalRows([hand, ...journal.entries], day.sessions);

		expect(rows[0].kind).toBe("entry");
		if (rows[0].kind === "entry") {
			expect(rows[0].session).toBeNull();
		}
		// The two breaks still fall where the séances put them, one row later.
		expect(labels(rows)[5]).toBe("— Récréation —");
	});

	it("n'imprime pas une coupure qu'aucune ligne ne suit", () => {
		const morning = journal.entries.slice(0, 4);
		const rows = buildJournalRows(morning, day.sessions);

		expect(labels(rows).some((label) => label.startsWith("—"))).toBe(false);
	});

	it("ne trouve aucune coupure un jour chômé, qui n'a aucune séance", () => {
		expect(buildJournalRows([], (dayOff as DayDetail).sessions)).toEqual([]);
	});
});

describe("le déplacement d'une ligne", () => {
	const ids = ["a", "b", "c"];

	it("renvoie l'ordre complet, jamais le seul déplacement", () => {
		expect(moveEntry(ids, "b", -1)).toEqual(["b", "a", "c"]);
		expect(moveEntry(ids, "b", 1)).toEqual(["a", "c", "b"]);
	});

	it("ne fait rien au-delà des deux bouts", () => {
		expect(moveEntry(ids, "a", -1)).toEqual(ids);
		expect(moveEntry(ids, "c", 1)).toEqual(ids);
		expect(moveEntry(ids, "inconnue", 1)).toEqual(ids);
	});
});
