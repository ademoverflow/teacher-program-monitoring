import { describe, expect, it } from "vitest";
import type { DayRef } from "@/lib/api/calendar";
import { resolveCurrentWeek } from "@/lib/current-week";

const DAY: DayRef = {
	id: "d",
	date: "2026-09-01",
	day_of_week: 2,
	is_off: false,
	off_reason: null,
	week_number: 1,
	number_in_period: 1,
	period_code: "P1",
};

describe("la semaine courante", () => {
	it("est celle que le calendrier annonce", () => {
		expect(
			resolveCurrentWeek({ current_week_number: 12 }, { next_taught_day: DAY }),
		).toBe(12);
	});

	it("se replie sur le prochain jour de classe hors année", () => {
		expect(
			resolveCurrentWeek(
				{ current_week_number: null },
				{ next_taught_day: DAY },
			),
		).toBe(1);
	});

	it("ouvre la rentrée quand plus rien n'est à venir", () => {
		expect(
			resolveCurrentWeek(
				{ current_week_number: null },
				{ next_taught_day: null },
			),
		).toBe(1);
		expect(resolveCurrentWeek({ current_week_number: null }, undefined)).toBe(
			1,
		);
	});
});
