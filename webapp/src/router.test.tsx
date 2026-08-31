import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, stubApi } from "@/test/app";
import calendar from "@/test/fixtures/calendar.json";
import dayRentree from "@/test/fixtures/day-2026-09-01.json";
import journalRentree from "@/test/fixtures/journal-2026-09-01.json";
import TODAY from "@/test/fixtures/today.json";
import week01 from "@/test/fixtures/week-01.json";

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("les routes", () => {
	it("ouvre « Aujourd'hui » depuis la racine, replié sur le prochain jour de classe", async () => {
		// On 2026-08-31 the pupils have not come back: `school_day` is null and
		// `next_taught_day` is mardi 01/09, so the home page is always the fallback.
		stubApi({
			"/api/calendar/today": TODAY,
			"/api/days/2026-09-01": dayRentree,
			"/api/journal/2026-09-01": journalRentree,
		});
		const { router } = renderApp("/");

		await waitFor(() => {
			expect(router.state.location.pathname).toBe("/jour/2026-09-01");
		});
		expect(await screen.findByText("mardi 1 septembre 2026")).toBeTruthy();
	});

	it("ouvre l'année sur /annee", async () => {
		stubApi({ "/api/calendar": calendar });
		renderApp("/annee");

		expect(await screen.findByText("Année scolaire 2026-2027")).toBeTruthy();
	});

	it("ouvre la semaine courante sur /semaine", async () => {
		stubApi({
			"/api/calendar": calendar,
			"/api/calendar/today": TODAY,
			"/api/weeks/1": week01,
		});
		const { router } = renderApp("/semaine");

		await waitFor(() => {
			expect(router.state.location.pathname).toBe("/semaine/1");
		});
		expect(await screen.findByText("Semaine 1")).toBeTruthy();
	});

	it("garde la sidebar sur chaque écran", async () => {
		stubApi({
			"/api/calendar": calendar,
			"/api/health": { status: "ok", uptime: 1, version: "0.0.0" },
		});
		renderApp("/annee");

		const nav = await screen.findByRole("navigation", {
			name: "Navigation principale",
		});
		expect(nav.textContent).toContain("Aujourd'hui");
		expect(nav.textContent).toContain("Année");
		expect(nav.textContent).toContain("Semaine");
		expect(nav.textContent).toContain("Programmes");
		expect(await screen.findByText("API v0.0.0")).toBeTruthy();
	});

	it("signale une API injoignable sans casser l'écran", async () => {
		stubApi({ "/api/calendar": calendar });
		renderApp("/annee");

		const alerts = await screen.findAllByRole("alert");
		expect(
			alerts.some((one) => one.textContent?.includes("API injoignable")),
		).toBe(true);
	});
});
