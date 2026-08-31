import { screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, stubApi } from "@/test/app";
import week01 from "@/test/fixtures/week-01.json";
import week25 from "@/test/fixtures/week-25.json";

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("la vue Semaine", () => {
	it("dessine la S1 avec ses trois jours, la rentrée étant un mardi", async () => {
		stubApi({ "/api/weeks/1": week01 });
		renderApp("/semaine/1");

		expect(await screen.findByText("mardi 1 sept.")).toBeTruthy();
		expect(screen.getByText("jeudi 3 sept.")).toBeTruthy();
		expect(screen.getByText("vendredi 4 sept.")).toBeTruthy();
		expect(screen.queryByText(/lundi/)).toBeNull();
	});

	it("nomme la récréation et la pause méridienne, qui n'ont pas de créneau", async () => {
		stubApi({ "/api/weeks/1": week01 });
		renderApp("/semaine/1");

		// One band per jour column.
		expect(await screen.findAllByText("Récréation")).toHaveLength(3);
		expect(screen.getAllByText("Pause méridienne")).toHaveLength(3);
	});

	it("empile deux séances dans une cellule, badgées CM1 et CM2 (ADR-0010)", async () => {
		stubApi({ "/api/weeks/1": week01 });
		renderApp("/semaine/1");

		const mardi = await screen.findByRole("list", {
			name: "Créneaux du mardi 1 sept.",
		});
		const conjugaison = within(mardi).getByRole("listitem", {
			name: "9h10 · Étude de la langue — Conjugaison",
		});
		expect(within(conjugaison).getByText("CM1")).toBeTruthy();
		expect(within(conjugaison).getByText("CM2")).toBeTruthy();
	});

	it("dessine deux cellules côte à côte là où l'EDT a deux créneaux", async () => {
		stubApi({ "/api/weeks/1": week01 });
		renderApp("/semaine/1");

		const mardi = await screen.findByRole("list", {
			name: "Créneaux du mardi 1 sept.",
		});
		expect(
			within(mardi).getByRole("listitem", {
				name: "11h30 · Lecture, compréhension de textes",
			}),
		).toBeTruthy();
		expect(
			within(mardi).getByRole("listitem", {
				name: "11h30 · Histoire ou Géographie",
			}),
		).toBeTruthy();
	});

	it("imprime la durée du créneau, pas l'écart de ses bornes (ADR-0003)", async () => {
		stubApi({ "/api/weeks/1": week01 });
		renderApp("/semaine/1");

		// Vendredi's calcul mental sits in the grid's 9h55-10h15 band and lasts 15'.
		const vendredi = await screen.findByRole("list", {
			name: "Créneaux du vendredi 4 sept.",
		});
		const mental = within(vendredi).getByRole("listitem", {
			name: "9h55 · Calcul mental",
		});
		expect(within(mental).getByText("15 min")).toBeTruthy();

		const mardi = screen.getByRole("list", {
			name: "Créneaux du mardi 1 sept.",
		});
		expect(
			within(
				within(mardi).getByRole("listitem", { name: "9h55 · Calcul mental" }),
			).getByText("20 min"),
		).toBeTruthy();
	});

	it("montre le trou du lundi de Pâques plutôt que de l'omettre", async () => {
		stubApi({ "/api/weeks/25": week25 });
		renderApp("/semaine/25");

		expect(await screen.findByText("Lundi de Pâques")).toBeTruthy();
		expect(screen.getByText("lundi 29 mars")).toBeTruthy();
		// The chômé jour keeps its ten cellules, each naming its créneau and holding
		// no séance.
		expect(screen.getAllByText("Anglais").length).toBeGreaterThan(0);
	});

	it("navigue de semaine en semaine", async () => {
		stubApi({ "/api/weeks/1": week01 });
		renderApp("/semaine/1");

		expect(await screen.findByText("Semaine 1")).toBeTruthy();
		const next = screen.getByLabelText("Semaine suivante (S2)");
		expect(next.getAttribute("href")).toBe("/semaine/2");
		expect(
			screen.getByText("Semaine précédente").getAttribute("href"),
		).toBeNull();
	});
});
