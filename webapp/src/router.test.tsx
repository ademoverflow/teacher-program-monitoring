import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderApp, stubApi } from "@/test/app";
import calendar from "@/test/fixtures/calendar.json";
import week01 from "@/test/fixtures/week-01.json";

const TODAY = {
	date: "2026-08-31",
	school_day: null,
	next_taught_day: {
		id: "d",
		date: "2026-09-01",
		day_of_week: 2,
		is_off: false,
		off_reason: null,
		week_number: 1,
		number_in_period: 1,
		period_code: "P1",
	},
};

afterEach(() => {
	vi.unstubAllGlobals();
});

describe("les routes", () => {
	it("ouvre l'année depuis la racine", async () => {
		stubApi({ "/api/calendar": calendar });
		const { router } = renderApp("/");

		await waitFor(() => {
			expect(router.state.location.pathname).toBe("/annee");
		});
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
