import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, stubApi } from "@/test/app";
import fractionsCm1 from "@/test/fixtures/program-items-fractions-cm1.json";
import subjects from "@/test/fixtures/subjects.json";

const EMPTY = { total: 0, limit: 50, offset: 0, items: [] };

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("le navigateur de programmes", () => {
	it("rend la recherche « fractions » en CM1 telle que l'API la classe", async () => {
		stubApi({
			"/api/subjects": subjects,
			"/api/program-items?level=CM1&q=fractions&limit=50&offset=0":
				fractionsCm1,
		});
		renderApp("/programmes?q=fractions&niveau=CM1");

		const list = await screen.findByRole("list", {
			name: "Items de programme",
		});
		const titles = within(list)
			.getAllByRole("heading")
			.map((heading) => heading.textContent);
		// The order is the server's rank, never re-sorted here.
		expect(titles).toEqual([
			"Les fractions",
			"Les nombres décimaux",
			"Mémoriser des faits numériques",
		]);
	});

	it("écrit les filtres dans l'URL et les envoie à l'API", async () => {
		const fetchMock = stubApi({
			"/api/subjects": subjects,
			"/api/program-items?limit=50&offset=0": EMPTY,
			"/api/program-items?subject=mathematiques&limit=50&offset=0": EMPTY,
		});
		const { router } = renderApp("/programmes");

		await screen.findByRole("option", { name: "Mathématiques" });
		fireEvent.change(screen.getByLabelText("Matière"), {
			target: { value: "mathematiques" },
		});

		await waitFor(() => {
			expect(router.state.location.search).toEqual({
				matiere: "mathematiques",
				page: 1,
			});
		});
		await waitFor(() => {
			expect(
				fetchMock.mock.calls.some((call) =>
					String(call[0]).includes("subject=mathematiques"),
				),
			).toBe(true);
		});
	});

	it("restreint les domaines à la matière choisie", async () => {
		stubApi({
			"/api/subjects": subjects,
			"/api/program-items?subject=mathematiques&limit=50&offset=0": EMPTY,
		});
		renderApp("/programmes?matiere=mathematiques");

		await screen.findByRole("option", { name: "Nombres" });
		const domaine = screen.getByLabelText("Domaine");
		const options = within(domaine).getAllByRole("option");
		// « Tous » plus the nine domaines de maths, and none of the other 36.
		expect(options).toHaveLength(10);
		expect(options.map((option) => option.textContent)).toContain("Nombres");
		expect(options.map((option) => option.textContent)).not.toContain(
			"Lecture",
		);
	});

	it("dit clairement qu'un filtre ne renvoie rien", async () => {
		stubApi({
			"/api/subjects": subjects,
			"/api/program-items?subject=poesie&limit=50&offset=0": EMPTY,
		});
		renderApp("/programmes?matiere=poesie");

		expect(
			await screen.findByText(
				"Aucun item de programme ne correspond à ces filtres.",
			),
		).toBeTruthy();
	});
});
