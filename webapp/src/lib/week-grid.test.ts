import { describe, expect, it } from "vitest";
import { weekDetailSchema } from "@/lib/api/weeks";
import { buildWeekGrid, cellSubject, type GridColumn } from "@/lib/week-grid";
import week01 from "@/test/fixtures/week-01.json";
import week25 from "@/test/fixtures/week-25.json";

/**
 * The assembly of §4.1's grid, against two responses frozen from a seeded stack. No
 * network, no database: the three traps of the phase are structural, and they are all
 * present in these two semaines.
 */

const S1 = weekDetailSchema.parse(week01);
const S25 = weekDetailSchema.parse(week25);

function column(grid: { columns: GridColumn[] }, date: string): GridColumn {
	const found = grid.columns.find((candidate) => candidate.day.date === date);
	if (found === undefined) {
		throw new Error(`Aucun jour au ${date}`);
	}
	return found;
}

function cellAt(
	grid: { columns: GridColumn[] },
	date: string,
	startsAt: string,
) {
	return column(grid, date).cells.filter(
		(placed) => placed.cell.slot.starts_at === startsAt,
	);
}

describe("les réponses figées", () => {
	it("valident les schémas écrits à la main", () => {
		expect(S1.number).toBe(1);
		expect(S25.number).toBe(25);
	});
});

describe("la S1, qui n'a pas de lundi", () => {
	const grid = buildWeekGrid(S1);

	it("dessine trois colonnes et pas quatre", () => {
		expect(grid.columns.map((one) => one.day.day_of_week)).toEqual([2, 4, 5]);
	});

	it("porte les 38 séances de la semaine", () => {
		const total = grid.columns.reduce(
			(count, one) =>
				count +
				one.cells.reduce(
					(inner, placed) => inner + placed.cell.sessions.length,
					0,
				),
			0,
		);
		expect(total).toBe(38);
	});
});

describe("les bandes horaires", () => {
	const grid = buildWeekGrid(S1);

	it("sortent des bornes des créneaux, pas d'une liste écrite d'avance", () => {
		expect(grid.bands).toHaveLength(13);
		expect(grid.bands[0].startsAt).toBe("09:00:00");
		expect(grid.bands.at(-1)?.endsAt).toBe("16:30:00");
	});

	it("nomment la récréation et la pause méridienne, qui ne sont pas des créneaux", () => {
		const breaks = grid.bands.filter((band) => band.isBreak);
		expect(
			breaks.map((band) => [band.startsAt, band.endsAt, band.breakLabel]),
		).toEqual([
			["10:15:00", "10:45:00", "Récréation"],
			["12:30:00", "14:00:00", "Pause méridienne"],
		]);
	});

	it("ne laissent aucun trou : chaque bande de chaque jour est couverte", () => {
		for (const one of grid.columns) {
			for (const [index, band] of grid.bands.entries()) {
				if (band.isBreak) {
					continue;
				}
				const width = one.cells
					.filter(
						(placed) => placed.bandStart <= index && placed.bandEnd > index,
					)
					.reduce((total, placed) => total + placed.laneSpan, 0);
				expect(width, `${one.day.date} ${band.startsAt} n'est pas rempli`).toBe(
					one.laneCount,
				);
			}
		}
	});
});

describe("le vendredi, qui ne tombe pas sur la grille des autres jours", () => {
	const grid = buildWeekGrid(S1);

	it("place ses deux cellules de 30' sur leurs propres bornes (ADR-0003)", () => {
		const fluence = cellAt(grid, "2026-09-04", "11:30:00");
		const dictee = cellAt(grid, "2026-09-04", "12:00:00");
		expect(fluence).toHaveLength(1);
		expect(dictee).toHaveLength(1);
		expect(fluence[0].cell.slot.duration_minutes).toBe(30);
		expect(dictee[0].cell.slot.duration_minutes).toBe(30);
		expect(fluence[0].bandEnd).toBe(dictee[0].bandStart);
	});

	it("garde 15 minutes de calcul mental dans une bande de 20 (ADR-0003)", () => {
		const [mental] = cellAt(grid, "2026-09-04", "09:55:00");
		expect(mental.cell.slot.duration_minutes).toBe(15);
		expect(grid.bands[mental.bandStart].minutes).toBe(20);
	});

	it("n'a qu'une voie : rien n'y est dédoublé par l'EDT", () => {
		expect(column(grid, "2026-09-04").laneCount).toBe(1);
	});
});

describe("les deux façons dont un horaire se dédouble", () => {
	const grid = buildWeekGrid(S1);

	it("mardi 9h10 : une cellule, deux séances empilées (ADR-0010)", () => {
		const placed = cellAt(grid, "2026-09-01", "09:10:00");
		expect(placed).toHaveLength(1);
		expect(placed[0].laneSpan).toBe(column(grid, "2026-09-01").laneCount);
		expect(placed[0].cell.sessions.map((one) => one.level)).toEqual([
			"CM1",
			"CM2",
		]);
	});

	it("mardi 11h30 : deux cellules côte à côte, CM1 d'abord", () => {
		const placed = cellAt(grid, "2026-09-01", "11:30:00");
		expect(placed).toHaveLength(2);
		expect(placed.map((one) => one.cell.slot.level)).toEqual(["CM1", "CM2"]);
		expect(placed.map((one) => one.lane)).toEqual([0, 1]);
		expect(placed.map((one) => one.laneSpan)).toEqual([1, 1]);
	});
});

describe("un jour chômé", () => {
	const grid = buildWeekGrid(S25);

	it("garde sa colonne, ses cellules et son motif (ADR-0001)", () => {
		const monday = column(grid, "2027-03-29");
		expect(grid.columns).toHaveLength(4);
		expect(monday.day.is_off).toBe(true);
		expect(monday.day.off_reason).toBe("Lundi de Pâques");
		expect(monday.cells).toHaveLength(10);
		expect(
			monday.cells.every((placed) => placed.cell.sessions.length === 0),
		).toBe(true);
	});
});

describe("la couleur d'une cellule", () => {
	const grid = buildWeekGrid(S1);

	it("vient de la séance quand le créneau alterne (ADR-0002)", () => {
		const [histoireOuGeo] = cellAt(grid, "2026-09-01", "14:15:00").filter(
			(placed) => placed.cell.slot.is_alternating,
		);
		expect(histoireOuGeo.cell.slot.subject).toBeNull();
		// The alternance opens the year on histoire (ADR-0013).
		expect(cellSubject(histoireOuGeo.cell)?.code).toBe("histoire");
	});

	it("vient du créneau quand la cellule est vide", () => {
		const [maths] = cellAt(buildWeekGrid(S25), "2027-03-29", "10:45:00");
		expect(maths.cell.sessions).toHaveLength(0);
		expect(cellSubject(maths.cell)?.code).toBe("mathematiques");
	});

	it("n'existe pas pour l'accueil du matin (ADR-0015)", () => {
		const [accueil] = cellAt(grid, "2026-09-01", "09:00:00");
		expect(accueil.cell.sessions).toHaveLength(1);
		expect(cellSubject(accueil.cell)).toBeNull();
	});
});
