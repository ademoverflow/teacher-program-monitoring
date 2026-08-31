import { screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, stubApi } from "@/test/app";
import fractionsCm1 from "@/test/fixtures/program-items-fractions-cm1.json";

const ITEM = fractionsCm1.items[0];

const LINKED = {
	total: 2,
	limit: 20,
	offset: 0,
	sessions: [
		{
			id: "s1",
			date: "2026-09-07",
			timetable_slot_id: "t1",
			level: "CM1",
			title: "Séquence 2 — Fractions-1 (séance 1/4)",
			status: "planifiée",
			position: 5,
			subject: null,
			domain: null,
			sequence: null,
		},
		{
			id: "s2",
			date: "2026-09-08",
			timetable_slot_id: "t2",
			level: "CM1",
			title: "Séquence 2 — Fractions-1 (séance 2/4)",
			status: "planifiée",
			position: 5,
			subject: null,
			domain: null,
			sequence: null,
		},
	],
};

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("la fiche d'un item de programme", () => {
	it("cite le fichier et la page dont l'item a été lu", async () => {
		stubApi({
			[`/api/program-items/${ITEM.id}`]: ITEM,
			[`/api/planned-sessions?program_item_id=${ITEM.id}&limit=20&offset=0`]:
				LINKED,
		});
		renderApp(`/programmes/${ITEM.id}`);

		expect(
			await screen.findByRole("heading", { name: ITEM.title }),
		).toBeTruthy();
		expect(
			screen.getByText(
				(_, node) =>
					node?.textContent ===
					`${ITEM.source_file} · page ${ITEM.source_page}`,
			),
		).toBeTruthy();
	});

	it("liste les séances qui travaillent l'item", async () => {
		stubApi({
			[`/api/program-items/${ITEM.id}`]: ITEM,
			[`/api/planned-sessions?program_item_id=${ITEM.id}&limit=20&offset=0`]:
				LINKED,
		});
		renderApp(`/programmes/${ITEM.id}`);

		const list = await screen.findByRole("list", { name: "Séances liées" });
		expect(
			within(list).getByText("Séquence 2 — Fractions-1 (séance 1/4)"),
		).toBeTruthy();
		expect(within(list).getByText("lundi 7 septembre 2026")).toBeTruthy();
	});
});
