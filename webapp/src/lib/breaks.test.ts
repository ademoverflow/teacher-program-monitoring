import { describe, expect, it } from "vitest";
import type { DayDetail } from "@/lib/api/days";
import { findBreaks } from "@/lib/breaks";
import dayFixture from "@/test/fixtures/day-2026-09-07.json";

const slots = (dayFixture as DayDetail).sessions.map((session) => session.slot);

describe("les coupures d'une journée", () => {
	it("trouve la récréation et la pause méridienne, que le gabarit ne déclare pas", () => {
		expect(findBreaks(slots)).toEqual([
			{ startsAt: "10:15:00", endsAt: "10:45:00", label: "Récréation" },
			{ startsAt: "12:30:00", endsAt: "14:00:00", label: "Pause méridienne" },
		]);
	});

	it("n'invente pas de trou entre deux créneaux qui se chevauchent", () => {
		// Mardi 11h30 holds two créneaux at once; jeudi holds a 45' and a 30' one.
		expect(
			findBreaks([
				{ starts_at: "11:30:00", ends_at: "12:15:00" },
				{ starts_at: "11:30:00", ends_at: "12:00:00" },
				{ starts_at: "12:15:00", ends_at: "12:30:00" },
			]),
		).toEqual([]);
	});

	it("garde un trou que §4.1 ne nomme pas, sans nom", () => {
		expect(
			findBreaks([
				{ starts_at: "09:00:00", ends_at: "09:10:00" },
				{ starts_at: "09:30:00", ends_at: "10:00:00" },
			]),
		).toEqual([{ startsAt: "09:10:00", endsAt: "09:30:00", label: null }]);
	});

	it("ne trouve rien là où il n'y a pas de créneau", () => {
		expect(findBreaks([])).toEqual([]);
	});
});
