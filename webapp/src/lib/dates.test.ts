import { describe, expect, it } from "vitest";
import {
	formatCompactDate,
	formatCompactRange,
	formatDateRange,
	formatDuration,
	formatLongDate,
	formatShortDate,
	formatTime,
	parseIsoDate,
	timeToMinutes,
} from "@/lib/dates";

describe("les dates", () => {
	it("lit une date ISO comme une date locale, jamais UTC", () => {
		const date = parseIsoDate("2026-09-07");
		expect(date.getFullYear()).toBe(2026);
		expect(date.getMonth()).toBe(8);
		expect(date.getDate()).toBe(7);
	});

	it("écrit le jour en toutes lettres", () => {
		expect(formatLongDate("2026-09-07")).toBe("lundi 7 septembre 2026");
		expect(formatShortDate("2026-09-01")).toBe("mardi 1 sept.");
		expect(formatCompactDate("2026-08-31")).toBe("31 août");
	});

	it("écrit une semaine comme une plage", () => {
		expect(formatDateRange("2026-08-31", "2026-09-04")).toBe(
			"du 31 août au 4 septembre 2026",
		);
		expect(formatCompactRange("2026-08-31", "2026-09-04")).toBe(
			"31 août – 4 sept.",
		);
	});

	it("écrit une heure comme l'EDT l'imprime", () => {
		expect(formatTime("09:10:00")).toBe("9h10");
		expect(formatTime("16:30:00")).toBe("16h30");
		expect(formatTime("09:00:00")).toBe("9h00");
	});

	it("compte les minutes depuis minuit", () => {
		expect(timeToMinutes("09:10:00")).toBe(550);
		expect(timeToMinutes("00:00:00")).toBe(0);
	});

	it("écrit une durée", () => {
		expect(formatDuration(45)).toBe("45 min");
	});
});
