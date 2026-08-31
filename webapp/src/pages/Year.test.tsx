import { screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, stubApi } from "@/test/app";
import calendar from "@/test/fixtures/calendar.json";

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("la vue Année", () => {
	it("répartit les 36 semaines sur les cinq périodes", async () => {
		stubApi({ "/api/calendar": calendar });
		renderApp("/annee");

		expect(await screen.findByText("Année scolaire 2026-2027")).toBeTruthy();
		const cards = screen.getAllByRole("region");
		expect(
			cards.map((card) => within(card).getAllByRole("link").length),
		).toEqual([7, 7, 5, 6, 11]);
	});

	it("annonce les vacances qui ferment chaque période", async () => {
		stubApi({ "/api/calendar": calendar });
		renderApp("/annee");

		expect(await screen.findByText(/Vacances de la Toussaint/)).toBeTruthy();
		expect(
			screen.getByText(/Vacances d'été · à partir du 3 juil./),
		).toBeTruthy();
	});

	it("marque la semaine courante et mène à sa grille", async () => {
		stubApi({ "/api/calendar": calendar });
		renderApp("/annee");

		const first = await screen.findByRole("link", {
			name: "Semaine 1, 31 août – 4 sept.",
		});
		expect(first.getAttribute("aria-current")).toBe("page");
		expect(first.getAttribute("href")).toBe("/semaine/1");

		const second = screen.getByRole("link", {
			name: "Semaine 2, 7 sept. – 11 sept.",
		});
		expect(second.getAttribute("aria-current")).toBeNull();
	});

	it("signale les semaines amputées d'un jour chômé", async () => {
		stubApi({ "/api/calendar": calendar });
		renderApp("/annee");

		// 29/03 (P4-S6), 06-07/05 (P5-S3) and 17/05 (P5-S5).
		const marks = await screen.findAllByText(/jours? chômés?/);
		expect(marks.map((mark) => mark.textContent)).toEqual([
			"1 jour chômé",
			"2 jours chômés",
			"1 jour chômé",
		]);
	});
});
