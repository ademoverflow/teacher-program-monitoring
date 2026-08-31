import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, type StubbedRequest, stubApi } from "@/test/app";
import dayFixture from "@/test/fixtures/day-2026-09-07.json";
import dayOff from "@/test/fixtures/day-2027-03-29.json";
import journalFixture from "@/test/fixtures/journal-2026-09-07.json";
import emptyJournal from "@/test/fixtures/journal-2026-09-07-vide.json";
import journalOff from "@/test/fixtures/journal-2027-03-29.json";
import today from "@/test/fixtures/today.json";

afterEach(() => {
	vi.unstubAllGlobals();
});

/** `GET /api/calendar/today` as it answers once the 7th is behind us. */
const AFTER = { ...today, date: "2026-09-30" };

/** The sidebar polls this; an unstubbed one raises « API injoignable » over the screen. */
const HEALTH = { "/api/health": { status: "ok", uptime: 1, version: "0.0.0" } };

/** The day and its cahier journal, already filled — the ordinary case. */
function filledDay(extra: Record<string, unknown> = {}) {
	return {
		...HEALTH,
		"/api/calendar/today": today,
		"/api/days/2026-09-07": dayFixture,
		"/api/journal/2026-09-07": journalFixture,
		...extra,
	};
}

describe("la vue Jour", () => {
	it("porte l'en-tête du modèle imprimé", async () => {
		stubApi(filledDay());
		renderApp("/jour/2026-09-07");

		expect(await screen.findByText("lundi 7 septembre 2026")).toBeTruthy();
		expect(screen.getByText(/Période 1 – Semaine 2/)).toBeTruthy();
		expect(screen.getByText("CM1-CM2 – Cycle 3")).toBeTruthy();
	});

	it("dessine les douze lignes, la récréation et la pause méridienne en travers", async () => {
		stubApi(filledDay());
		renderApp("/jour/2026-09-07");

		const table = await screen.findByRole("table");
		// 1 en-tête + 12 lignes + 2 coupures.
		expect(within(table).getAllByRole("row")).toHaveLength(15);
		expect(within(table).getByText(/Récréation 10h15 – 10h45/)).toBeTruthy();
		expect(
			within(table).getByText(/Pause méridienne 12h30 – 14h00/),
		).toBeTruthy();
	});

	it("nomme la matière résolue sur un créneau alternant (ADR-0021)", async () => {
		stubApi(filledDay());
		renderApp("/jour/2026-09-07");

		// The 15h45 créneau is « Arts plastiques / Éducation musicale »; the ligne carries
		// the matière the génération resolved, not the pair.
		const field = await screen.findByLabelText(
			"Discipline de la ligne « Arts plastiques »",
		);
		expect((field as HTMLInputElement).value).toBe("Arts plastiques");
	});

	it("imprime la durée du créneau, pas l'écart de ses bornes (ADR-0003)", async () => {
		stubApi(filledDay());
		renderApp("/jour/2026-09-07");

		const duration = await screen.findByLabelText(
			"Durée de la ligne « Accueil · rituel de langue · plan de travail », en minutes",
		);
		expect((duration as HTMLInputElement).value).toBe("10");
	});

	it("n'initialise pas un jour que l'enseignante ne fait que regarder (ADR-0028)", async () => {
		const fetchMock = stubApi(
			filledDay({ "/api/journal/2026-09-07": emptyJournal }),
		);
		renderApp("/jour/2026-09-07");

		expect(
			await screen.findByRole("button", {
				name: "Initialiser depuis la programmation",
			}),
		).toBeTruthy();
		expect(screen.getByText(/12 séances/)).toBeTruthy();
		expect(
			fetchMock.mock.calls.some(([, init]) => init?.method === "POST"),
		).toBe(false);
	});

	it("remplit le cahier journal quand on le lui demande", async () => {
		stubApi(
			filledDay({
				"/api/journal/2026-09-07": emptyJournal,
				"POST /api/journal/2026-09-07/initialise": {
					status: 201,
					body: journalFixture,
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		fireEvent.click(
			await screen.findByRole("button", {
				name: "Initialiser depuis la programmation",
			}),
		);

		const table = await screen.findByRole("table");
		expect(within(table).getAllByRole("row")).toHaveLength(15);
	});

	it("initialise de lui-même le jour qui est en train de se vivre (ADR-0028)", async () => {
		stubApi({
			...HEALTH,
			"/api/calendar/today": AFTER,
			"/api/days/2026-09-07": dayFixture,
			"/api/journal/2026-09-07": emptyJournal,
			"POST /api/journal/2026-09-07/initialise": {
				status: 201,
				body: journalFixture,
			},
		});
		renderApp("/jour/2026-09-07");

		const table = await screen.findByRole("table");
		expect(within(table).getAllByRole("row")).toHaveLength(15);
	});

	it("dit pourquoi un jour chômé n'a pas de cahier journal", async () => {
		stubApi({
			...HEALTH,
			"/api/calendar/today": today,
			"/api/days/2027-03-29": dayOff,
			"/api/journal/2027-03-29": journalOff,
		});
		renderApp("/jour/2027-03-29");

		expect(
			await screen.findByText(/Pas de classe ce jour-là : Lundi de Pâques/),
		).toBeTruthy();
		expect(screen.queryByRole("table")).toBeNull();
	});

	it("dit qu'un mercredi n'est pas un jour de classe, sans crier à l'erreur", async () => {
		stubApi({ ...HEALTH, "/api/calendar/today": today });
		renderApp("/jour/2026-09-02");

		expect(
			await screen.findByText(/Ce n'est pas un jour de classe/),
		).toBeTruthy();
		expect(screen.queryByRole("alert")).toBeNull();
	});

	it("refuse une date qui n'en est pas une sans rien demander à l'API", async () => {
		const fetchMock = stubApi({ ...HEALTH, "/api/calendar/today": today });
		renderApp("/jour/lundi");

		const alert = await screen.findByRole("alert");
		expect(alert.textContent).toContain("« lundi » n'est pas une date.");
		expect(
			fetchMock.mock.calls.some(([url]) => String(url).includes("/api/days/")),
		).toBe(false);
	});
});

describe("l'édition d'une ligne", () => {
	it("enregistre un bilan quand le champ est quitté, et garde la réponse", async () => {
		const written: unknown[] = [];
		const target = journalFixture.entries[3];
		stubApi(
			filledDay({
				[`PATCH /api/journal/entries/${target.id}`]: (
					request: StubbedRequest,
				) => {
					written.push(request.body);
					return { ...target, ...(request.body as object) };
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		const bilan = await screen.findByLabelText(
			"Bilan de la ligne « Calcul mental »",
		);
		fireEvent.change(bilan, {
			target: { value: "Travail sur toute la semaine" },
		});
		fireEvent.blur(bilan);

		await waitFor(() => {
			expect(written).toEqual([{ bilan: "Travail sur toute la semaine" }]);
		});
		expect((bilan as HTMLTextAreaElement).value).toBe(
			"Travail sur toute la semaine",
		);
	});

	it("enregistre une saisie que le blur suit dans le même tour de boucle", async () => {
		// A paste followed by a click, or a script driving the page: the change and the
		// blur land in one task, so `commit` must read the draft it was just given rather
		// than the one the last render closed over.
		const written: unknown[] = [];
		const target = journalFixture.entries[3];
		stubApi(
			filledDay({
				[`PATCH /api/journal/entries/${target.id}`]: (
					request: StubbedRequest,
				) => {
					written.push(request.body);
					return { ...target, ...(request.body as object) };
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		const discipline = await screen.findByLabelText(
			"Discipline de la ligne « Calcul mental »",
		);
		fireEvent.focus(discipline);
		fireEvent.change(discipline, {
			target: { value: "Calcul mental (rituel)" },
		});
		fireEvent.blur(discipline);

		await waitFor(() => {
			expect(written).toEqual([{ discipline: "Calcul mental (rituel)" }]);
		});
	});

	it("n'écrit rien quand le champ est quitté sans avoir changé", async () => {
		const fetchMock = stubApi(filledDay());
		renderApp("/jour/2026-09-07");

		const bilan = await screen.findByLabelText(
			"Bilan de la ligne « Calcul mental »",
		);
		fireEvent.focus(bilan);
		fireEvent.blur(bilan);

		expect(
			fetchMock.mock.calls.some(([, init]) => init?.method === "PATCH"),
		).toBe(false);
	});

	it("rend une durée vidée comme une durée non notée", async () => {
		const written: unknown[] = [];
		const target = journalFixture.entries[3];
		stubApi(
			filledDay({
				[`PATCH /api/journal/entries/${target.id}`]: (
					request: StubbedRequest,
				) => {
					written.push(request.body);
					return { ...target, ...(request.body as object) };
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		const duration = await screen.findByLabelText(
			"Durée de la ligne « Calcul mental », en minutes",
		);
		fireEvent.change(duration, { target: { value: "" } });
		fireEvent.blur(duration);

		await waitFor(() => {
			expect(written).toEqual([{ duration_minutes: null }]);
		});
	});

	it("montre la phrase du serveur quand une écriture est refusée", async () => {
		const target = journalFixture.entries[3];
		stubApi(
			filledDay({
				[`PATCH /api/journal/entries/${target.id}`]: {
					status: 422,
					body: { detail: "La discipline ne peut pas être vide" },
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		const discipline = await screen.findByLabelText(
			"Discipline de la ligne « Calcul mental »",
		);
		fireEvent.change(discipline, { target: { value: "" } });
		fireEvent.blur(discipline);

		const alert = await screen.findByRole("alert");
		expect(alert.textContent).toContain("La discipline ne peut pas être vide");
	});
});

describe("l'ajout et la suppression d'une ligne", () => {
	it("ajoute une ligne à la fin, que l'enseignante nomme ensuite", async () => {
		const added = {
			...journalFixture.entries[0],
			id: "added",
			planned_session_id: null,
			discipline: "Nouvelle ligne",
			duration_minutes: null,
			objectives: null,
			position: 13,
		};
		stubApi(filledDay({ "POST /api/journal/2026-09-07/entries": added }));
		renderApp("/jour/2026-09-07");

		fireEvent.click(
			await screen.findByRole("button", { name: "Ajouter une ligne" }),
		);

		expect(
			await screen.findByLabelText("Discipline de la ligne « Nouvelle ligne »"),
		).toBeTruthy();
	});

	it("retire une ligne, sans rien remettre à sa place", async () => {
		const target = journalFixture.entries[3];
		stubApi(
			filledDay({
				[`DELETE /api/journal/entries/${target.id}`]: { status: 204 },
			}),
		);
		renderApp("/jour/2026-09-07");

		fireEvent.click(
			await screen.findByRole("button", {
				name: "Supprimer la ligne « Calcul mental »",
			}),
		);

		await waitFor(() => {
			expect(
				screen.queryByLabelText("Bilan de la ligne « Calcul mental »"),
			).toBeNull();
		});
		// The récréation followed « Calcul mental »; with it gone it follows the ligne
		// before, and the table has lost exactly one row.
		expect(within(screen.getByRole("table")).getAllByRole("row")).toHaveLength(
			14,
		);
	});
});

describe("l'ordre des lignes", () => {
	it("envoie l'ordre complet du jour, pas le seul déplacement (ADR-0029)", async () => {
		let sent: { entry_ids: string[] } | null = null;
		stubApi(
			filledDay({
				"PUT /api/journal/2026-09-07/order": (request: StubbedRequest) => {
					sent = request.body as { entry_ids: string[] };
					return journalFixture;
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		fireEvent.click(
			await screen.findByRole("button", {
				name: "Monter la ligne « Calcul mental »",
			}),
		);

		await waitFor(() => {
			expect(sent).not.toBeNull();
		});
		const order = sent as unknown as { entry_ids: string[] };
		expect(order.entry_ids).toHaveLength(12);
		// The 4th ligne swapped with the 3rd; every other id kept its rank.
		expect(order.entry_ids[2]).toBe(journalFixture.entries[3].id);
		expect(order.entry_ids[3]).toBe(journalFixture.entries[2].id);
	});

	it("ne propose pas de monter la première ligne ni de descendre la dernière", async () => {
		stubApi(filledDay());
		renderApp("/jour/2026-09-07");

		const first = await screen.findByRole("button", {
			name: "Monter la ligne « Accueil · rituel de langue · plan de travail »",
		});
		expect((first as HTMLButtonElement).disabled).toBe(true);
		expect(
			(
				screen.getByRole("button", {
					name: "Descendre la ligne « Arts plastiques »",
				}) as HTMLButtonElement
			).disabled,
		).toBe(true);
	});

	it("montre le refus du serveur si l'ordre ne lui convient pas", async () => {
		stubApi(
			filledDay({
				"PUT /api/journal/2026-09-07/order": {
					status: 400,
					body: {
						detail:
							"L'ordre doit nommer exactement les lignes du cahier journal de ce jour, une fois chacune",
					},
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		fireEvent.click(
			await screen.findByRole("button", {
				name: "Monter la ligne « Calcul mental »",
			}),
		);

		const alert = await screen.findByRole("alert");
		expect(alert.textContent).toContain("L'ordre doit nommer exactement");
	});
});

describe("le statut d'une séance", () => {
	it("s'écrit sur la séance, depuis la ligne qui en vient (ADR-0031)", async () => {
		let sent: unknown = null;
		const session = dayFixture.sessions[3];
		stubApi(
			filledDay({
				[`PATCH /api/planned-sessions/${session.id}`]: (
					request: StubbedRequest,
				) => {
					sent = request.body;
					return { ...session, status: "faite" };
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		const select = await screen.findByLabelText(
			`Statut de la séance « ${session.title} »`,
		);
		fireEvent.change(select, { target: { value: "faite" } });

		await waitFor(() => {
			expect(sent).toEqual({ status: "faite" });
		});
	});

	it("n'en propose pas sur une ligne écrite à la main", async () => {
		const hand = {
			...journalFixture.entries[0],
			id: "hand",
			planned_session_id: null,
			discipline: "Conseil de classe",
		};
		stubApi(
			filledDay({
				"/api/journal/2026-09-07": {
					...journalFixture,
					entries: [...journalFixture.entries, hand],
				},
			}),
		);
		renderApp("/jour/2026-09-07");

		await screen.findByLabelText(
			"Discipline de la ligne « Conseil de classe »",
		);
		// One select per ligne that came from a séance, and none for the hand-written one.
		expect(screen.getAllByRole("combobox")).toHaveLength(12);
	});
});
